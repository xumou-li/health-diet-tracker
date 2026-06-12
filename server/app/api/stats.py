"""营养统计API"""
from datetime import date, timedelta
from flask import Blueprint, request, g
from sqlalchemy import func
from app.extensions import db
from app.models import MealRecord, BodyRecord
from app.utils.response import success, error
from app.utils.auth import login_required
from app.services.nutrition import NutritionService

stats_bp = Blueprint('stats', __name__)


def get_daily_stats(user_id, target_date):
    """获取某日的营养统计"""
    meals = MealRecord.query.filter_by(
        user_id=user_id,
        date=target_date
    ).all()
    
    total = {
        'calorie': sum(m.calorie for m in meals),
        'protein': sum(float(m.protein) for m in meals),
        'carb': sum(float(m.carb) for m in meals),
        'fat': sum(float(m.fat) for m in meals)
    }
    
    # 按餐次统计
    by_meal = {1: 0, 2: 0, 3: 0, 4: 0}
    for meal in meals:
        by_meal[meal.meal_type] += meal.calorie
    
    return {
        'date': target_date.isoformat(),
        'total': total,
        'by_meal_type': {
            'breakfast': by_meal[1],
            'lunch': by_meal[2],
            'dinner': by_meal[3],
            'snack': by_meal[4]
        },
        'meal_count': len(meals)
    }


@stats_bp.route('/today', methods=['GET'])
@login_required
def get_today_stats():
    """今日汇总（热量、营养素、评分）"""
    user = g.current_user
    today = date.today()
    
    # 获取今日统计
    stats = get_daily_stats(user.id, today)
    
    # 获取目标值（使用用户自定义比例）
    targets = NutritionService.calculate_nutrient_targets(
        user.daily_calorie_goal,
        float(user.protein_ratio) if user.protein_ratio else 0.15,
        float(user.fat_ratio) if user.fat_ratio else 0.25,
        float(user.carb_ratio) if user.carb_ratio else 0.55
    )
    
    # 计算评分
    score = NutritionService.calculate_diet_score(stats['total'], targets)
    
    # 计算摄入状态
    intake_status = {
        'calorie': NutritionService.get_intake_status(stats['total']['calorie'], targets['calorie']),
        'protein': NutritionService.get_intake_status(stats['total']['protein'], targets['protein']),
        'carb': NutritionService.get_intake_status(stats['total']['carb'], targets['carb']),
        'fat': NutritionService.get_intake_status(stats['total']['fat'], targets['fat'])
    }
    
    # 计算剩余可摄入
    remaining = {
        'calorie': max(0, targets['calorie'] - stats['total']['calorie']),
        'protein': max(0, targets['protein'] - stats['total']['protein']),
        'carb': max(0, targets['carb'] - stats['total']['carb']),
        'fat': max(0, targets['fat'] - stats['total']['fat'])
    }
    
    return success({
        'date': today.isoformat(),
        'actual': stats['total'],
        'target': targets,
        'remaining': remaining,
        'by_meal_type': stats['by_meal_type'],
        'meal_count': stats['meal_count'],
        'score': score,
        'intake_status': intake_status,
        'bmi': float(user.bmi),
        'bmi_status': NutritionService.get_bmi_status(float(user.bmi))
    })


@stats_bp.route('/week', methods=['GET'])
@login_required
def get_week_stats():
    """最近7天统计"""
    user = g.current_user
    today = date.today()
    
    # 获取每日统计
    daily_stats = []
    targets = NutritionService.calculate_nutrient_targets(
        user.daily_calorie_goal,
        float(user.protein_ratio) if user.protein_ratio else 0.15,
        float(user.fat_ratio) if user.fat_ratio else 0.25,
        float(user.carb_ratio) if user.carb_ratio else 0.55
    )
    
    for i in range(7):
        target_date = today - timedelta(days=6-i)
        stats = get_daily_stats(user.id, target_date)
        score = NutritionService.calculate_diet_score(stats['total'], targets)
        daily_stats.append({
            'date': target_date.isoformat(),
            'calorie': stats['total']['calorie'],
            'protein': round(stats['total']['protein'], 1),
            'carb': round(stats['total']['carb'], 1),
            'fat': round(stats['total']['fat'], 1),
            'score': score,
            'is_target_met': 0.8 <= stats['total']['calorie'] / targets['calorie'] <= 1.2 if targets['calorie'] > 0 else False
        })
    
    # 汇总统计
    total_calorie = sum(d['calorie'] for d in daily_stats)
    avg_calorie = total_calorie / 7
    target_met_days = sum(1 for d in daily_stats if d['is_target_met'])
    avg_score = sum(d['score'] for d in daily_stats) / 7
    avg_protein = sum(d['protein'] for d in daily_stats) / 7
    avg_carb = sum(d['carb'] for d in daily_stats) / 7
    avg_fat = sum(d['fat'] for d in daily_stats) / 7
    
    return success({
        'period': f"{(today - timedelta(days=6)).isoformat()} ~ {today.isoformat()}",
        'daily': daily_stats,
        'summary': {
            'total_calorie': total_calorie,
            'avg_calorie': round(avg_calorie),
            'avg_protein': round(avg_protein, 1),
            'avg_carb': round(avg_carb, 1),
            'avg_fat': round(avg_fat, 1),
            'target_met_days': target_met_days,
            'avg_score': round(avg_score, 1)
        },
        'target': targets
    })


@stats_bp.route('/month', methods=['GET'])
@login_required
def get_month_stats():
    """最近30天统计"""
    user = g.current_user
    today = date.today()
    start_date = today - timedelta(days=29)
    
    targets = NutritionService.calculate_nutrient_targets(
        user.daily_calorie_goal,
        float(user.protein_ratio) if user.protein_ratio else 0.15,
        float(user.fat_ratio) if user.fat_ratio else 0.25,
        float(user.carb_ratio) if user.carb_ratio else 0.55
    )
    
    # 聚合查询
    daily_data = db.session.query(
        MealRecord.date,
        func.sum(MealRecord.calorie).label('calorie'),
        func.sum(MealRecord.protein).label('protein'),
        func.sum(MealRecord.carb).label('carb'),
        func.sum(MealRecord.fat).label('fat'),
        func.count(MealRecord.id).label('count')
    ).filter(
        MealRecord.user_id == user.id,
        MealRecord.date >= start_date,
        MealRecord.date <= today
    ).group_by(MealRecord.date).all()
    
    # 转换为字典
    data_map = {d.date: d for d in daily_data}
    
    # 填充所有日期
    daily_stats = []
    total_calorie = 0
    total_score = 0
    recorded_days = 0
    target_met_days = 0
    total_protein = 0.0
    total_carb = 0.0
    total_fat = 0.0
    
    for i in range(30):
        target_date = start_date + timedelta(days=i)
        if target_date in data_map:
            d = data_map[target_date]
            calorie = int(d.calorie or 0)
            protein = round(float(d.protein or 0), 1)
            carb = round(float(d.carb or 0), 1)
            fat = round(float(d.fat or 0), 1)
            day_total = {
                'calorie': calorie,
                'protein': protein,
                'carb': carb,
                'fat': fat
            }
            score = NutritionService.calculate_diet_score(day_total, targets)
            is_target_met = 0.8 <= calorie / targets['calorie'] <= 1.2 if targets['calorie'] > 0 else False

            total_calorie += calorie
            total_score += score
            recorded_days += 1
            total_protein += protein
            total_carb += carb
            total_fat += fat
            if is_target_met:
                target_met_days += 1
            daily_stats.append({
                'date': target_date.isoformat(),
                'calorie': calorie,
                'protein': protein,
                'carb': carb,
                'fat': fat,
                'score': score,
                'is_target_met': is_target_met,
                'has_record': True
            })
        else:
            day_total = {
                'calorie': 0,
                'protein': 0,
                'carb': 0,
                'fat': 0
            }
            score = NutritionService.calculate_diet_score(day_total, targets)
            total_score += score

            daily_stats.append({
                'date': target_date.isoformat(),
                'calorie': 0,
                'protein': 0,
                'carb': 0,
                'fat': 0,
                'score': score,
                'is_target_met': False,
                'has_record': False
            })

    avg_calorie = total_calorie / recorded_days if recorded_days > 0 else 0
    avg_score = total_score / 30
    avg_protein = round(total_protein / recorded_days, 1) if recorded_days > 0 else 0.0
    avg_carb = round(total_carb / recorded_days, 1) if recorded_days > 0 else 0.0
    avg_fat = round(total_fat / recorded_days, 1) if recorded_days > 0 else 0.0
    
    return success({
        'period': f"{start_date.isoformat()} ~ {today.isoformat()}",
        'daily': daily_stats,
        'summary': {
            'total_calorie': total_calorie,
            'avg_calorie': round(avg_calorie),
            'avg_protein': avg_protein,
            'avg_carb': avg_carb,
            'avg_fat': avg_fat,
            'recorded_days': recorded_days,
            'target_met_days': target_met_days,
            'avg_score': round(avg_score, 1)
        },
        'target': targets
    })


@stats_bp.route('/nutrients-radar', methods=['GET'])
@login_required
def get_nutrients_radar():
    """营养素雷达图数据"""
    user = g.current_user
    target_date = request.args.get('date', date.today().isoformat())
    
    try:
        target_date = date.fromisoformat(target_date)
    except ValueError:
        target_date = date.today()
    
    stats = get_daily_stats(user.id, target_date)
    targets = NutritionService.calculate_nutrient_targets(
        user.daily_calorie_goal,
        float(user.protein_ratio) if user.protein_ratio else 0.15,
        float(user.fat_ratio) if user.fat_ratio else 0.25,
        float(user.carb_ratio) if user.carb_ratio else 0.55
    )
    
    # 计算各营养素完成百分比（0-100，超过100按100计）
    def calc_percent(actual, target):
        if target <= 0:
            return 0
        return min(100, round(actual / target * 100))
    
    radar_data = [
        {'name': '热量', 'value': calc_percent(stats['total']['calorie'], targets['calorie'])},
        {'name': '蛋白质', 'value': calc_percent(stats['total']['protein'], targets['protein'])},
        {'name': '碳水', 'value': calc_percent(stats['total']['carb'], targets['carb'])},
        {'name': '脂肪', 'value': calc_percent(stats['total']['fat'], targets['fat'])}
    ]
    
    return success({
        'date': target_date.isoformat(),
        'radar': radar_data,
        'actual': stats['total'],
        'target': targets
    })


@stats_bp.route('/weight-trend', methods=['GET'])
@login_required
def get_weight_trend():
    """体重变化趋势"""
    user = g.current_user
    days = request.args.get('days', 30, type=int)
    
    start_date = date.today() - timedelta(days=days-1)
    
    # 查询身体记录
    records = BodyRecord.query.filter(
        BodyRecord.user_id == user.id,
        db.func.date(BodyRecord.recorded_at) >= start_date
    ).order_by(BodyRecord.recorded_at).all()
    
    trend = []
    for record in records:
        trend.append({
            'date': record.recorded_at.date().isoformat(),
            'weight': float(record.weight_kg),
            'bmi': float(record.bmi)
        })
    
    # 计算变化
    if len(trend) >= 2:
        weight_change = trend[-1]['weight'] - trend[0]['weight']
        bmi_change = trend[-1]['bmi'] - trend[0]['bmi']
    else:
        weight_change = 0
        bmi_change = 0
    
    return success({
        'period': f"{start_date.isoformat()} ~ {date.today().isoformat()}",
        'trend': trend,
        'summary': {
            'start_weight': trend[0]['weight'] if trend else float(user.weight_kg),
            'current_weight': float(user.weight_kg),
            'weight_change': round(weight_change, 2),
            'bmi_change': round(bmi_change, 2)
        }
    })


@stats_bp.route('/analysis', methods=['GET'])
@login_required
def get_analysis():
    """
    热量分析与反馈（核心模块）
    返回：超标分析、食物来源排行、饮食建议、推荐食物
    """
    user = g.current_user
    target_date = request.args.get('date', date.today().isoformat())
    
    try:
        target_date = date.fromisoformat(target_date)
    except ValueError:
        target_date = date.today()
    
    # 获取当日饮食记录（包含食物详情）
    meals = MealRecord.query.filter_by(
        user_id=user.id,
        date=target_date
    ).all()
    
    # 获取目标值（使用用户自定义比例）
    targets = NutritionService.calculate_nutrient_targets(
        user.daily_calorie_goal,
        float(user.protein_ratio) if user.protein_ratio else 0.15,
        float(user.fat_ratio) if user.fat_ratio else 0.25,
        float(user.carb_ratio) if user.carb_ratio else 0.55
    )
    
    # 计算实际摄入
    actual = {
        'calorie': sum(m.calorie for m in meals),
        'protein': sum(float(m.protein) for m in meals),
        'carb': sum(float(m.carb) for m in meals),
        'fat': sum(float(m.fat) for m in meals)
    }
    
    # 1. 各营养素超标百分比
    excess_percent = {
        'calorie': NutritionService.calculate_excess_percent(actual['calorie'], targets['calorie']),
        'protein': NutritionService.calculate_excess_percent(actual['protein'], targets['protein']),
        'carb': NutritionService.calculate_excess_percent(actual['carb'], targets['carb']),
        'fat': NutritionService.calculate_excess_percent(actual['fat'], targets['fat'])
    }
    
    # 判断超标营养素
    excess_nutrients = []
    is_calorie_excess = actual['calorie'] > targets['calorie']
    for nutrient in ['protein', 'carb', 'fat']:
        if actual[nutrient] > targets[nutrient]:
            excess_nutrients.append(nutrient)
    
    # 2. 超标食物来源排行（按各营养素贡献排序）
    food_sources = []
    for meal in meals:
        name = meal.food.name if meal.food else (meal.custom_name or '自定义食物')
        food_sources.append({
            'name': name,
            'meal_type': meal.meal_type,
            'weight_g': meal.weight_g,
            'calorie': meal.calorie,
            'protein': float(meal.protein),
            'carb': float(meal.carb),
            'fat': float(meal.fat)
        })
    
    # 按各营养素排序取TOP贡献食物
    top_protein_sources = sorted(food_sources, key=lambda x: x['protein'], reverse=True)[:5]
    top_fat_sources = sorted(food_sources, key=lambda x: x['fat'], reverse=True)[:5]
    top_carb_sources = sorted(food_sources, key=lambda x: x['carb'], reverse=True)[:5]
    top_calorie_sources = sorted(food_sources, key=lambda x: x['calorie'], reverse=True)[:5]
    
    # 3. 基于BMI和超标类型的建议
    bmi_status = NutritionService.get_bmi_status(float(user.bmi))
    suggestions = NutritionService.get_diet_suggestions(bmi_status, excess_nutrients, is_calorie_excess)
    
    # 4. 推荐食物列表
    recommended_foods = NutritionService.get_recommended_foods(excess_nutrients, is_calorie_excess, bmi_status)
    
    return success({
        'date': target_date.isoformat(),
        'summary': {
            'actual': actual,
            'target': targets,
            'is_calorie_excess': is_calorie_excess,
            'bmi': float(user.bmi),
            'bmi_status': bmi_status
        },
        'excess_analysis': {
            'excess_percent': excess_percent,
            'excess_nutrients': excess_nutrients
        },
        'food_sources': {
            'top_calorie': [{'name': f['name'], 'value': f['calorie'], 'meal_type': f['meal_type']} for f in top_calorie_sources],
            'top_protein': [{'name': f['name'], 'value': round(f['protein'], 2), 'meal_type': f['meal_type']} for f in top_protein_sources],
            'top_fat': [{'name': f['name'], 'value': round(f['fat'], 2), 'meal_type': f['meal_type']} for f in top_fat_sources],
            'top_carb': [{'name': f['name'], 'value': round(f['carb'], 2), 'meal_type': f['meal_type']} for f in top_carb_sources]
        },
        'suggestions': suggestions,
        'recommended_foods': recommended_foods
    })


@stats_bp.route('/metabolism-insight', methods=['GET'])
@login_required
def get_metabolism_insight():
    """个人代谢分析

    返回基于身体快照和饮食记录反推的个人代谢系数，
    以及与公式预测的对比。
    """
    user = g.current_user
    from app.services.metabolism import MetabolismService

    result = MetabolismService.calibrate_coefficient(user.id)

    confidence_map = {
        'high': '高（3组以上快照数据）',
        'medium': '中（2组快照数据）',
        'low': '低（仅1组数据或数据不足）',
        'none': '暂无（需要≥2条身体快照且≥7天间隔）'
    }

    data = {
        'coefficient': result['coefficient'],
        'confidence': result['confidence'],
        'confidence_desc': confidence_map.get(result['confidence'], ''),
        'formula_tdee': result['formula_tdee'],
        'actual_tdee': result['actual_tdee'],
        'sample_pairs': result['sample_pairs'],
        'latest_calibrated_at': result['latest_calibrated_at'],
        'deviation_percent': round((result['coefficient'] - 1.0) * 100, 1),
        'is_calibrated': result['coefficient'] != 1.0 and result['sample_pairs'] > 0
    }

    # 获取最新 body_record 中存储的系数
    latest_body = BodyRecord.query.filter_by(user_id=user.id).order_by(
        BodyRecord.recorded_at.desc()
    ).first()
    if latest_body and latest_body.metabolic_coefficient:
        data['stored_coefficient'] = float(latest_body.metabolic_coefficient)

    # 公式预测消耗
    activity_factor = NutritionService.ACTIVITY_FACTORS.get(
        user.activity_level, 1.2
    )
    data['current_formula_tdee'] = round(user.bmr * activity_factor)

    # 校准后推荐热量
    if data['is_calibrated']:
        coef = data.get('stored_coefficient', data['coefficient'])
        calibrated_tdee = round(user.bmr * activity_factor * coef)
        calibrated_goal = round(calibrated_tdee * float(user.goal_factor))
        data['calibrated_tdee'] = calibrated_tdee
        data['calibrated_daily_goal'] = calibrated_goal
        data['original_daily_goal'] = user.daily_calorie_goal

    return success(data)

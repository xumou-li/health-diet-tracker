"""饮食记录API"""
from datetime import date, datetime
from flask import Blueprint, request, g
from app.extensions import db
from app.models import MealRecord, Food, BodyRecord
from app.utils.response import success, error
from app.utils.auth import login_required
from app.utils.validators import validate_meal_type, validate_date

meal_bp = Blueprint('meal', __name__)


def get_or_create_body_record(user):
    """获取或创建今日身体记录快照"""
    today = date.today()
    
    # 查找今日的身体记录
    body_record = BodyRecord.query.filter(
        BodyRecord.user_id == user.id,
        db.func.date(BodyRecord.recorded_at) == today
    ).first()
    
    if not body_record:
        # 创建今日快照
        body_record = BodyRecord(
            user_id=user.id,
            height_cm=user.height_cm,
            weight_kg=user.weight_kg,
            age=user.age,
            gender=user.gender,
            activity_level=user.activity_level,
            bmi=user.bmi,
            bmr=user.bmr,
            daily_calorie_goal=user.daily_calorie_goal,
            protein_ratio=user.protein_ratio,
            fat_ratio=user.fat_ratio,
            carb_ratio=user.carb_ratio
        )
        db.session.add(body_record)
        db.session.flush()
    
    return body_record


def calculate_nutrition(food, weight_g):
    """根据食物和重量计算营养数据"""
    ratio = float(weight_g) / 100
    return {
        'calorie': int(food.calorie_per_100g * ratio),
        'protein': round(float(food.protein_per_100g) * ratio, 2),
        'carb': round(float(food.carb_per_100g) * ratio, 2),
        'fat': round(float(food.fat_per_100g) * ratio, 2)
    }


@meal_bp.route('/meals', methods=['POST'])
@login_required
def add_meal():
    """新增饮食记录"""
    user = g.current_user
    data = request.get_json() or {}
    
    food_id = data.get('food_id')
    meal_date = data.get('date', date.today().isoformat())
    meal_type = data.get('meal_type')
    weight_g = data.get('weight_g')
    
    # 校验
    if not food_id:
        return error('请选择食物')
    
    if not validate_meal_type(meal_type):
        return error('餐次类型错误（1=早餐, 2=午餐, 3=晚餐, 4=加餐）')
    
    if not weight_g or weight_g <= 0:
        return error('请输入有效的重量')
    
    # 检查食物是否存在
    food = Food.query.get(food_id)
    if not food or not food.is_approved:
        return error('食物不存在')
    
    try:
        # 解析日期
        record_date = date.fromisoformat(meal_date)
        
        # 获取身体记录快照
        body_record = get_or_create_body_record(user)
        
        # 计算营养数据
        nutrition = calculate_nutrition(food, weight_g)
        
        # 创建饮食记录
        meal = MealRecord(
            user_id=user.id,
            food_id=food_id,
            body_record_id=body_record.id,
            date=record_date,
            meal_type=meal_type,
            weight_g=weight_g,
            calorie=nutrition['calorie'],
            protein=nutrition['protein'],
            carb=nutrition['carb'],
            fat=nutrition['fat']
        )
        db.session.add(meal)
        db.session.commit()
        
        return success(meal.to_dict(), '添加成功')
        
    except ValueError as e:
        return error(f'日期格式错误: {str(e)}')
    except Exception as e:
        db.session.rollback()
        return error(f'添加失败: {str(e)}')


@meal_bp.route('/meals/batch', methods=['POST'])
@login_required
def add_meals_batch():
    """批量新增饮食记录（食谱一键添加）"""
    user = g.current_user
    data = request.get_json() or {}
    
    items = data.get('items', [])  # [{food_id, weight_g}, ...]
    meal_date = data.get('date', date.today().isoformat())
    meal_type = data.get('meal_type')
    
    if not items:
        return error('请选择食物')
    
    if not validate_meal_type(meal_type):
        return error('餐次类型错误')
    
    try:
        record_date = date.fromisoformat(meal_date)
        body_record = get_or_create_body_record(user)
        
        meals = []
        for item in items:
            item_type = item.get('type', 'food')
            
            if item_type == 'custom':
                # 自定义食物：直接使用提供的数据
                name = (item.get('name') or '').strip()
                if not name:
                    continue
                meal = MealRecord(
                    user_id=user.id,
                    food_id=None,
                    body_record_id=body_record.id,
                    date=record_date,
                    meal_type=meal_type,
                    weight_g=None,
                    calorie=int(item.get('calorie', 0)),
                    protein=round(float(item.get('protein', 0)), 2),
                    carb=round(float(item.get('carb', 0)), 2),
                    fat=round(float(item.get('fat', 0)), 2),
                    custom_name=name
                )
                db.session.add(meal)
                meals.append(meal)
            else:
                food_id = item.get('food_id')
                weight_g = item.get('weight_g', 100)
                
                food = Food.query.get(food_id)
                if not food or not food.is_approved:
                    continue
                
                nutrition = calculate_nutrition(food, weight_g)
                
                meal = MealRecord(
                    user_id=user.id,
                    food_id=food_id,
                    body_record_id=body_record.id,
                    date=record_date,
                    meal_type=meal_type,
                    weight_g=weight_g,
                    calorie=nutrition['calorie'],
                    protein=nutrition['protein'],
                    carb=nutrition['carb'],
                    fat=nutrition['fat']
                )
                db.session.add(meal)
                meals.append(meal)
        
        db.session.commit()
        
        return success({
            'count': len(meals),
            'items': [m.to_dict() for m in meals]
        }, f'成功添加{len(meals)}条记录')
        
    except Exception as e:
        db.session.rollback()
        return error(f'添加失败: {str(e)}')


@meal_bp.route('/meals', methods=['GET'])
@login_required
def get_meals():
    """获取指定日期记录"""
    user = g.current_user
    
    meal_date = request.args.get('date', date.today().isoformat())
    meal_type = request.args.get('meal_type', type=int)
    
    try:
        record_date = date.fromisoformat(meal_date)
    except ValueError:
        return error('日期格式错误')
    
    # 构建查询
    query = MealRecord.query.filter_by(user_id=user.id, date=record_date)
    
    if meal_type:
        query = query.filter_by(meal_type=meal_type)
    
    meals = query.order_by(MealRecord.meal_type, MealRecord.created_at).all()
    
    # 按餐次分组
    grouped = {1: [], 2: [], 3: [], 4: []}
    for meal in meals:
        grouped[meal.meal_type].append(meal.to_dict())
    
    # 计算汇总
    total_calorie = sum(m.calorie for m in meals)
    total_protein = sum(float(m.protein) for m in meals)
    total_carb = sum(float(m.carb) for m in meals)
    total_fat = sum(float(m.fat) for m in meals)
    
    return success({
        'date': meal_date,
        'meals': grouped,
        'summary': {
            'calorie': total_calorie,
            'protein': round(total_protein, 2),
            'carb': round(total_carb, 2),
            'fat': round(total_fat, 2),
            'count': len(meals)
        }
    })


@meal_bp.route('/meals/<int:meal_id>', methods=['PUT'])
@login_required
def update_meal(meal_id):
    """修改记录"""
    user = g.current_user
    data = request.get_json() or {}
    
    meal = MealRecord.query.filter_by(id=meal_id, user_id=user.id).first()
    
    if not meal:
        return error('记录不存在', 404)
    
    weight_g = data.get('weight_g')
    meal_type = data.get('meal_type')
    
    try:
        if weight_g and weight_g > 0:
            if not meal.food:
                return error('自定义食物不支持修改重量')
            # 重新计算营养数据
            nutrition = calculate_nutrition(meal.food, weight_g)
            meal.weight_g = weight_g
            meal.calorie = nutrition['calorie']
            meal.protein = nutrition['protein']
            meal.carb = nutrition['carb']
            meal.fat = nutrition['fat']
        
        if meal_type and validate_meal_type(meal_type):
            meal.meal_type = meal_type
        
        db.session.commit()
        
        return success(meal.to_dict(), '更新成功')
        
    except Exception as e:
        db.session.rollback()
        return error(f'更新失败: {str(e)}')


@meal_bp.route('/meals/<int:meal_id>', methods=['DELETE'])
@login_required
def delete_meal(meal_id):
    """删除记录"""
    user = g.current_user
    
    meal = MealRecord.query.filter_by(id=meal_id, user_id=user.id).first()
    
    if not meal:
        return error('记录不存在', 404)
    
    try:
        db.session.delete(meal)
        db.session.commit()
        
        return success(message='删除成功')
        
    except Exception as e:
        db.session.rollback()
        return error(f'删除失败: {str(e)}')


@meal_bp.route('/meals/copy', methods=['POST'])
@login_required
def copy_meals():
    """复制某天某餐到今天"""
    user = g.current_user
    data = request.get_json() or {}
    
    source_date = data.get('source_date')
    source_meal_type = data.get('source_meal_type')
    target_date = data.get('target_date', date.today().isoformat())
    target_meal_type = data.get('target_meal_type')
    
    if not source_date:
        return error('请指定源日期')
    
    if not validate_meal_type(source_meal_type):
        return error('源餐次类型错误')
    
    if not validate_meal_type(target_meal_type):
        target_meal_type = source_meal_type
    
    try:
        src_date = date.fromisoformat(source_date)
        tgt_date = date.fromisoformat(target_date)
        
        # 获取源记录
        source_meals = MealRecord.query.filter_by(
            user_id=user.id,
            date=src_date,
            meal_type=source_meal_type
        ).all()
        
        if not source_meals:
            return error('源日期无相关记录')
        
        # 获取身体记录
        body_record = get_or_create_body_record(user)
        
        # 复制记录
        new_meals = []
        for src in source_meals:
            new_meal = MealRecord(
                user_id=user.id,
                food_id=src.food_id,
                body_record_id=body_record.id,
                date=tgt_date,
                meal_type=target_meal_type,
                weight_g=src.weight_g,
                calorie=src.calorie,
                protein=src.protein,
                carb=src.carb,
                fat=src.fat
            )
            db.session.add(new_meal)
            new_meals.append(new_meal)
        
        db.session.commit()
        
        return success({
            'count': len(new_meals),
            'items': [m.to_dict() for m in new_meals]
        }, f'成功复制{len(new_meals)}条记录')
        
    except ValueError as e:
        return error(f'日期格式错误: {str(e)}')
    except Exception as e:
        db.session.rollback()
        return error(f'复制失败: {str(e)}')

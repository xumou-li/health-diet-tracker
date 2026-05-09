"""个性化代谢系数校准服务

基于身体快照（体重变化）和饮食记录（热量摄入）的历史数据，
反推用户的真实代谢水平，修正 Mifflin-St Jeor 通用公式的个体偏差。

核心原理：能量平衡公式
  体重变化(kg) × 7700 = 累计摄入(kcal) - 累计消耗(kcal)
  → 日均真实消耗 = 日均摄入 - (体重变化 × 7700 / 天数)
  → 个人代谢系数 = 日均真实消耗 / (BMR × 活动系数)
"""

from datetime import date, timedelta
from sqlalchemy import func
from app.extensions import db
from app.models import BodyRecord, MealRecord
from app.services.nutrition import NutritionService


class MetabolismService:
    """个人代谢系数校准服务"""

    # 每公斤体重变化对应热量（kcal）—— 营养学公认系数
    KCAL_PER_KG = 7700

    # 最少快照间隔天数（避免日体重波动噪声）
    MIN_INTERVAL_DAYS = 7

    # 系数合理范围（超出视为异常数据）
    COEFF_MIN = 0.70
    COEFF_MAX = 1.50

    # 时间衰减半衰期（天）—— 越近的快照对权重越高
    DECAY_HALF_LIFE = 30

    @classmethod
    def calibrate_coefficient(cls, user_id):
        """基于身体快照和饮食记录校准个人代谢系数

        返回 {
            'coefficient': float,       # 校准后的代谢系数（1.0=与公式一致）
            'confidence': str,          # 'high'/'medium'/'low'/'none'
            'formula_tdee': int,        # 公式预测的TDEE
            'actual_tdee': int,         # 推算的实际TDEE
            'sample_pairs': int,        # 有效快照对数
            'latest_calibrated_at': str # 最近校准日期
        }
        """
        # 1. 获取所有身体快照，按时间排序
        body_records = BodyRecord.query.filter_by(
            user_id=user_id
        ).order_by(BodyRecord.recorded_at.asc()).all()

        if len(body_records) < 2:
            return cls._empty_result('none', '身体快照数据不足（至少需要2条）')

        # 2. 获取所有饮食记录，按日期聚合
        daily_calories = cls._get_daily_calories(user_id)

        if not daily_calories:
            return cls._empty_result('none', '饮食记录数据不足')

        # 3. 计算每对快照的代谢系数
        pairs = []

        for i in range(len(body_records)):
            for j in range(i + 1, len(body_records)):
                record_a = body_records[i]
                record_b = body_records[j]

                days = (record_b.recorded_at.date() - record_a.recorded_at.date()).days

                if days < cls.MIN_INTERVAL_DAYS:
                    continue

                delta_weight = float(record_b.weight_kg) - float(record_a.weight_kg)

                # 计算 A→B 期间日均热量摄入
                total_calories = 0
                days_with_data = 0
                current = record_a.recorded_at.date()
                while current < record_b.recorded_at.date():
                    cal = daily_calories.get(current, 0)
                    total_calories += cal
                    if cal > 0:
                        days_with_data += 1
                    current += timedelta(days=1)

                actual_days = max(days, 1)

                # 如果大多数天没有记录，跳过这个配对
                if days_with_data < max(3, actual_days * 0.5):
                    continue

                avg_daily_calorie = total_calories / actual_days

                # 核心公式：日均真实消耗
                daily_surplus = delta_weight * cls.KCAL_PER_KG / days
                actual_tdee = avg_daily_calorie - daily_surplus

                if actual_tdee <= 0:
                    continue

                # 公式预测的 TDEE（使用快照 B 的参数）
                formula_tdee = cls._calc_formula_tdee(record_b)

                if formula_tdee <= 0:
                    continue

                coef = actual_tdee / formula_tdee

                # 过滤异常值
                if coef < cls.COEFF_MIN or coef > cls.COEFF_MAX:
                    continue

                pairs.append({
                    'coefficient': round(coef, 4),
                    'actual_tdee': round(actual_tdee),
                    'formula_tdee': formula_tdee,
                    'days': days,
                    'delta_weight': round(delta_weight, 2),
                    'avg_calorie': round(avg_daily_calorie),
                    'ref_date': record_b.recorded_at.date()
                })

        if not pairs:
            return cls._empty_result('low', '暂无满足条件的快照配对（需间隔≥7天且有完整饮食记录）')

        # 4. 时间加权融合
        today = date.today()
        total_weight = 0.0
        weighted_sum = 0.0
        actual_tdee_sum = 0.0

        for pair in pairs:
            days_ago = (today - pair['ref_date']).days
            weight = 0.5 ** (days_ago / cls.DECAY_HALF_LIFE)
            weighted_sum += pair['coefficient'] * weight
            actual_tdee_sum += pair['actual_tdee'] * weight
            total_weight += weight

        final_coefficient = round(weighted_sum / total_weight, 3)
        avg_actual_tdee = round(actual_tdee_sum / total_weight)

        sample_pairs_count = len(pairs)

        # 置信度
        if sample_pairs_count >= 3:
            confidence = 'high'
        elif sample_pairs_count >= 2:
            confidence = 'medium'
        else:
            confidence = 'low'

        return {
            'coefficient': final_coefficient,
            'confidence': confidence,
            'formula_tdee': cls._calc_formula_tdee(body_records[-1]),
            'actual_tdee': avg_actual_tdee,
            'sample_pairs': sample_pairs_count,
            'pairs': pairs,
            'latest_calibrated_at': body_records[-1].recorded_at.isoformat() if body_records else None
        }

    @classmethod
    def apply_calibration(cls, user):
        """将校准系数应用到用户的热量目标

        在 user 更新档案时调用。
        更新 body_record.metabolic_coefficient 和 user.daily_calorie_goal。
        """
        result = cls.calibrate_coefficient(user.id)
        coefficient = result['coefficient']

        # 只有高/中置信度且偏差 >2% 才自动应用
        if result['confidence'] in ('high', 'medium') and abs(coefficient - 1.0) > 0.02:
            # 更新用户缓存
            user.metabolic_coefficient = coefficient

            # 重算并更新每日热量目标
            activity_factor = NutritionService.ACTIVITY_FACTORS.get(
                user.activity_level, 1.2
            )
            calibrated_tdee = int(user.bmr * activity_factor * coefficient)
            user.daily_calorie_goal = int(calibrated_tdee * float(user.calorie_coefficient))

            # 更新最新 BodyRecord
            latest = BodyRecord.query.filter_by(
                user_id=user.id
            ).order_by(BodyRecord.recorded_at.desc()).first()
            if latest:
                latest.metabolic_coefficient = coefficient
                latest.daily_calorie_goal = user.daily_calorie_goal

            db.session.commit()

        return result

    @staticmethod
    def _get_daily_calories(user_id):
        """获取用户每日总热量摄入字典 {date: calories}"""
        results = db.session.query(
            MealRecord.date,
            func.sum(MealRecord.calorie).label('total')
        ).filter(
            MealRecord.user_id == user_id
        ).group_by(MealRecord.date).all()

        return {row.date: int(row.total or 0) for row in results}

    @staticmethod
    def _calc_formula_tdee(body_record):
        """根据 body_record 中的参数计算公式 TDEE"""
        activity_factor = NutritionService.ACTIVITY_FACTORS.get(
            body_record.activity_level, 1.2
        )
        return int(body_record.bmr * activity_factor)

    @classmethod
    def _empty_result(cls, confidence, reason):
        """返回默认结果（系数=1.0，完全信任公式）"""
        return {
            'coefficient': 1.0,
            'confidence': confidence,
            'formula_tdee': 0,
            'actual_tdee': 0,
            'sample_pairs': 0,
            'pairs': [],
            'reason': reason,
            'latest_calibrated_at': None
        }

"""参数校验工具"""
import re


def validate_phone(phone):
    """校验手机号"""
    if not phone:
        return False
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))


def validate_email(email):
    """校验邮箱"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password):
    """校验密码（至少6位）"""
    if not password:
        return False
    return len(password) >= 6


def validate_gender(gender):
    """校验性别"""
    return gender in [0, 1, 2]


def validate_activity_level(level):
    """校验活动水平"""
    return level in [1, 2, 3, 4]


def validate_health_goal(goal):
    """校验健康目标"""
    return goal in [1, 2, 3]


def validate_calorie_coefficient(coefficient):
    """校验热量系数"""
    try:
        return float(coefficient) > 0
    except (TypeError, ValueError):
        return False


def validate_meal_type(meal_type):
    """校验餐次类型"""
    return meal_type in [1, 2, 3, 4]


def validate_date(date_str):
    """校验日期格式 YYYY-MM-DD"""
    if not date_str:
        return False
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    return bool(re.match(pattern, date_str))

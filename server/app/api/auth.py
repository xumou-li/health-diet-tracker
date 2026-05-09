"""用户认证API"""
import json
from datetime import date
from flask import Blueprint, request
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models import User, BodyRecord, SystemConfig
from app.utils.response import success, error
from app.services.email_service import send_verification_code, verify_code
from app.utils.validators import (
    validate_phone,
    validate_email,
    validate_password,
    validate_gender,
    validate_activity_level,
    validate_health_goal,
    validate_goal_factor,
)
from app.services.nutrition import NutritionService

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json() or {}
    
    # 获取参数
    phone = data.get('phone')
    email = data.get('email')
    password = data.get('password')
    code = data.get('code')  # 验证码（邮箱注册时必填）
    gender = data.get('gender')
    birthday = data.get('birthday')
    height_cm = data.get('height_cm')
    weight_kg = data.get('weight_kg')
    activity_level = data.get('activity_level')
    health_goal = data.get('health_goal', 1)
    calorie_coefficient = data.get('calorie_coefficient')
    
    # 获取自定义营养素比例（可选）
    protein_ratio = data.get('protein_ratio')
    fat_ratio = data.get('fat_ratio')
    carb_ratio = data.get('carb_ratio')

    if not validate_health_goal(health_goal):
        return error('健康目标参数错误（1=维持, 2=减脂, 3=增肌）')

    health_goal = int(health_goal)

    if calorie_coefficient is None:
        goal_factor = NutritionService.get_default_goal_factor(health_goal)
    elif not validate_goal_factor(calorie_coefficient):
        return error('热量系数参数错误')
    else:
        goal_factor = round(float(calorie_coefficient), 2)

    # 如果没有提供比例，根据健康目标使用默认值
    if protein_ratio is None or fat_ratio is None or carb_ratio is None:
        default_ratios = NutritionService.get_default_nutrient_ratios(health_goal)
        protein_ratio = protein_ratio if protein_ratio is not None else default_ratios['protein']
        fat_ratio = fat_ratio if fat_ratio is not None else default_ratios['fat']
        carb_ratio = carb_ratio if carb_ratio is not None else default_ratios['carb']
    
    # 校验必填参数
    if not phone and not email:
        return error('手机号或邮箱至少填写一个')
    
    if phone and not validate_phone(phone):
        return error('手机号格式不正确')
    
    if email and not validate_email(email):
        return error('邮箱格式不正确')

    # 邮箱注册需要验证码
    if email:
        if not code:
            return error('请输入验证码')
        valid, msg = verify_code(email, code)
        if not valid:
            return error(msg)

    if not validate_password(password):
        return error('密码至少6位')

    password = str(password)
    
    if not validate_gender(gender):
        return error('性别参数错误')

    if not isinstance(gender, int):
        return error('性别参数错误')
    
    if not birthday:
        return error('请填写出生日期')
    
    if not height_cm or height_cm < 50 or height_cm > 250:
        return error('身高应在50-250cm之间')

    height_cm = int(height_cm)
    
    if not weight_kg or weight_kg < 20 or weight_kg > 300:
        return error('体重应在20-300kg之间')

    weight_kg = float(weight_kg)
    
    if not validate_activity_level(activity_level):
        return error('活动水平参数错误')

    if not isinstance(activity_level, int):
        return error('活动水平参数错误')
    
    # 检查手机号/邮箱是否已存在
    if phone and User.query.filter_by(phone=phone, is_deleted=False).first():
        return error('该手机号已注册')
    
    if email and User.query.filter_by(email=email, is_deleted=False).first():
        return error('该邮箱已注册')
    
    try:
        # 解析生日
        birthday_date = date.fromisoformat(birthday)
        
        # 计算年龄
        today = date.today()
        age = today.year - birthday_date.year - (
            (today.month, today.day) < (birthday_date.month, birthday_date.day)
        )
        
        # 计算健康指标
        metrics = NutritionService.calculate_user_metrics(
            weight_kg,
            height_cm,
            age,
            gender,
            activity_level,
            health_goal,
            goal_factor
        )
        
        # 创建用户
        user = User()
        user.phone = phone
        user.email = email
        user.password_hash = generate_password_hash(password)
        user.gender = gender
        user.birthday = birthday_date
        user.height_cm = height_cm
        user.weight_kg = weight_kg
        user.activity_level = activity_level
        user.health_goal = health_goal
        user.goal_factor = metrics['calorie_coefficient']
        user.bmi = metrics['bmi']
        user.bmr = metrics['bmr']
        user.daily_calorie_goal = metrics['daily_calorie_goal']
        user.protein_ratio = protein_ratio
        user.fat_ratio = fat_ratio
        user.carb_ratio = carb_ratio
        user.last_weight_update = today
        db.session.add(user)
        db.session.flush()  # 获取user.id
        
        # 创建身体记录快照
        body_record = BodyRecord()
        body_record.user_id = user.id
        body_record.height_cm = height_cm
        body_record.weight_kg = weight_kg
        body_record.age = age
        body_record.gender = gender
        body_record.activity_level = activity_level
        body_record.bmi = metrics['bmi']
        body_record.bmr = metrics['bmr']
        body_record.daily_calorie_goal = metrics['daily_calorie_goal']
        body_record.goal_factor = metrics['calorie_coefficient']
        body_record.protein_ratio = protein_ratio
        body_record.fat_ratio = fat_ratio
        body_record.carb_ratio = carb_ratio
        db.session.add(body_record)
        db.session.commit()
        
        # 生成JWT
        access_token = create_access_token(
            identity=json.dumps({'type': 'user', 'id': user.id})
        )
        
        return success({
            'token': access_token,
            'user': user.to_dict()
        }, '注册成功')
        
    except ValueError as e:
        return error(f'日期格式错误: {str(e)}')
    except Exception as e:
        db.session.rollback()
        return error(f'注册失败: {str(e)}')


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json() or {}
    
    account = data.get('account')  # 手机号或邮箱
    password = data.get('password')
    
    if not account:
        return error('请输入手机号或邮箱')
    
    if not password:
        return error('请输入密码')
    
    # 查找用户
    user = None
    if validate_phone(account):
        user = User.query.filter_by(phone=account, is_deleted=False).first()
    elif validate_email(account):
        user = User.query.filter_by(email=account, is_deleted=False).first()
    else:
        # 尝试两种方式查找
        user = User.query.filter(
            (User.phone == account) | (User.email == account),
            User.is_deleted == False
        ).first()
    
    if not user:
        return error('账号不存在')
    
    if user.is_frozen:
        return error('账号已被冻结，请联系管理员')
    
    if not check_password_hash(user.password_hash, password):
        return error('密码错误')
    
    # 生成JWT
    access_token = create_access_token(
        identity=json.dumps({'type': 'user', 'id': user.id})
    )
    
    return success({
        'token': access_token,
        'user': user.to_dict()
    }, '登录成功')


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """重置密码（简化版，实际需要验证码）"""
    data = request.get_json() or {}
    
    account = data.get('account')
    new_password = data.get('new_password')
    # 实际应有验证码校验: code = data.get('code')
    
    if not account:
        return error('请输入手机号或邮箱')
    
    if not validate_password(new_password):
        return error('新密码至少6位')

    new_password = str(new_password)
    
    # 查找用户
    user = User.query.filter(
        (User.phone == account) | (User.email == account),
        User.is_deleted == False
    ).first()
    
    if not user:
        return error('账号不存在')
    
    try:
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        return success(message='密码重置成功')
    except Exception as e:
        db.session.rollback()
        return error(f'重置失败: {str(e)}')


@auth_bp.route('/announcement', methods=['GET'])
def get_announcement():
    """获取系统公告（公开接口）"""
    config = SystemConfig.query.first()
    announcement = config.announcement if config else None
    return success({'announcement': announcement or ''})


@auth_bp.route('/send-code', methods=['POST'])
def send_code():
    """发送邮箱验证码"""
    data = request.get_json() or {}
    email = data.get('email', '').strip()

    if not email:
        return error('请输入邮箱')
    if not validate_email(email):
        return error('邮箱格式不正确')

    # 检查邮箱是否已注册
    if User.query.filter_by(email=email, is_deleted=False).first():
        return error('该邮箱已注册')

    success_flag, msg = send_verification_code(email)
    if not success_flag:
        return error(msg)

    return success(message=msg)

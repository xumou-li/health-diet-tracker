"""用户与身体档案API"""
import os
import uuid
from datetime import date, timedelta
from flask import Blueprint, request, g, current_app
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import BodyRecord
from app.utils.response import success, error
from app.utils.auth import login_required
from app.utils.validators import validate_activity_level, validate_health_goal, validate_calorie_coefficient, validate_password
from app.services.nutrition import NutritionService
from app.services.email_service import send_verification_code, verify_code

user_bp = Blueprint('user', __name__)


@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """获取用户信息+当前身体档案"""
    user = g.current_user
    
    # 获取最新的身体记录
    latest_body = BodyRecord.query.filter_by(user_id=user.id).order_by(
        BodyRecord.recorded_at.desc()
    ).first()
    
    default_ratios = NutritionService.get_default_nutrient_ratios(user.health_goal)

    # 计算营养目标（使用用户自定义比例）
    nutrient_targets = NutritionService.calculate_nutrient_targets(
        user.daily_calorie_goal,
        float(user.protein_ratio) if user.protein_ratio is not None else default_ratios['protein'],
        float(user.fat_ratio) if user.fat_ratio is not None else default_ratios['fat'],
        float(user.carb_ratio) if user.carb_ratio is not None else default_ratios['carb']
    )
    
    data = user.to_dict()
    data['bmi_status'] = NutritionService.get_bmi_status(float(user.bmi))
    data['nutrient_targets'] = nutrient_targets
    data['latest_body_record'] = latest_body.to_dict() if latest_body else None
    
    return success(data)


@user_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """更新身体档案（触发BMI/BMR重算）"""
    user = g.current_user
    data = request.get_json() or {}
    
    # 可更新的字段
    height_cm = data.get('height_cm', user.height_cm)
    weight_kg = data.get('weight_kg', float(user.weight_kg))
    activity_level = data.get('activity_level', user.activity_level)
    health_goal = data.get('health_goal', user.health_goal)
    diet_preference = data.get('diet_preference', user.diet_preference)
    nickname = data.get('nickname')

    provided_calorie_coefficient = data.get('calorie_coefficient')
    health_goal_changed = health_goal != user.health_goal

    if health_goal_changed and provided_calorie_coefficient is None:
        calorie_coefficient = NutritionService.get_default_calorie_coefficient(health_goal)
    elif provided_calorie_coefficient is None:
        calorie_coefficient = (
            float(user.calorie_coefficient)
            if user.calorie_coefficient is not None
            else NutritionService.get_default_calorie_coefficient(user.health_goal)
        )
    elif not validate_calorie_coefficient(provided_calorie_coefficient):
        return error('热量系数参数错误')
    else:
        calorie_coefficient = round(float(provided_calorie_coefficient), 2)
    
    # 营养素比例（可选更新）
    protein_ratio = data.get('protein_ratio')
    fat_ratio = data.get('fat_ratio')
    carb_ratio = data.get('carb_ratio')
    
    # 如果提供了比例，更新用户比例
    if protein_ratio is not None:
        user.protein_ratio = max(0.05, min(0.50, float(protein_ratio)))  # 限制5%-50%
    if fat_ratio is not None:
        user.fat_ratio = max(0.10, min(0.45, float(fat_ratio)))  # 限制10%-45%
    if carb_ratio is not None:
        user.carb_ratio = max(0.20, min(0.70, float(carb_ratio)))  # 限制20%-70%
    
    # 校验
    if height_cm < 50 or height_cm > 250:
        return error('身高应在50-250cm之间')
    
    if weight_kg < 20 or weight_kg > 300:
        return error('体重应在20-300kg之间')
    
    if not validate_activity_level(activity_level):
        return error('活动水平参数错误')

    if not validate_health_goal(health_goal):
        return error('健康目标参数错误（1=维持, 2=减脂, 3=增肌）')

    height_cm = int(height_cm)
    weight_kg = float(weight_kg)
    activity_level = int(activity_level)
    health_goal = int(health_goal)

    try:
        current_calorie_coefficient = (
            float(user.calorie_coefficient)
            if user.calorie_coefficient is not None
            else NutritionService.get_default_calorie_coefficient(user.health_goal)
        )

        # 检查是否需要重新计算指标
        need_recalc = (
            height_cm != user.height_cm or
            float(weight_kg) != float(user.weight_kg) or
            activity_level != user.activity_level or
            health_goal_changed or
            float(calorie_coefficient) != current_calorie_coefficient
        )
        
        # 更新用户信息
        user.height_cm = height_cm
        user.weight_kg = weight_kg
        user.activity_level = activity_level
        user.health_goal = health_goal
        user.calorie_coefficient = calorie_coefficient
        user.diet_preference = diet_preference

        # 昵称（可选更新）
        if nickname is not None:
            nickname = str(nickname).strip()
            if len(nickname) > 50:
                return error('昵称不能超过50个字符')
            user.nickname = nickname

        if need_recalc:
            # 重新计算健康指标
            metrics = NutritionService.calculate_user_metrics(
                weight_kg,
                height_cm,
                user.age,
                user.gender,
                activity_level,
                health_goal,
                calorie_coefficient
            )
            user.bmi = metrics['bmi']
            user.bmr = metrics['bmr']
            user.daily_calorie_goal = metrics['daily_calorie_goal']
            user.calorie_coefficient = metrics['calorie_coefficient']
            user.last_weight_update = date.today()
            
            # 创建新的身体记录快照
            body_record = BodyRecord()
            body_record.user_id = user.id
            body_record.height_cm = height_cm
            body_record.weight_kg = weight_kg
            body_record.age = user.age
            body_record.gender = user.gender
            body_record.activity_level = activity_level
            body_record.bmi = metrics['bmi']
            body_record.bmr = metrics['bmr']
            body_record.daily_calorie_goal = metrics['daily_calorie_goal']
            body_record.calorie_coefficient = metrics['calorie_coefficient']
            body_record.protein_ratio = user.protein_ratio
            body_record.fat_ratio = user.fat_ratio
            body_record.carb_ratio = user.carb_ratio
            db.session.add(body_record)
        
        db.session.commit()

        # 异步校准个人代谢系数（不影响主流程）
        try:
            from app.services.metabolism import MetabolismService
            MetabolismService.apply_calibration(user)
        except Exception:
            pass  # 校准失败不影响档案更新

        return success(user.to_dict(), '更新成功')
        
    except Exception as e:
        db.session.rollback()
        return error(f'更新失败: {str(e)}')


@user_bp.route('/health-goal', methods=['PUT'])
@login_required
def update_health_goal():
    """更新健康目标"""
    user = g.current_user
    data = request.get_json() or {}
    
    health_goal = data.get('health_goal')
    
    if not validate_health_goal(health_goal):
        return error('健康目标参数错误（1=维持, 2=减脂, 3=增肌）')

    if not isinstance(health_goal, int):
        return error('健康目标参数错误（1=维持, 2=减脂, 3=增肌）')
    
    try:
        user.health_goal = health_goal
        user.calorie_coefficient = NutritionService.get_default_calorie_coefficient(health_goal)
        
        # 重新计算每日热量目标
        daily_calorie = NutritionService.calculate_daily_calorie(
            user.bmr,
            user.activity_level,
            health_goal,
            user.calorie_coefficient
        )
        user.daily_calorie_goal = daily_calorie
        
        # 根据新的健康目标更新默认营养素比例（如果用户没有自定义过）
        default_ratios = NutritionService.get_default_nutrient_ratios(health_goal)
        user.protein_ratio = default_ratios['protein']
        user.fat_ratio = default_ratios['fat']
        user.carb_ratio = default_ratios['carb']

        body_record = BodyRecord()
        body_record.user_id = user.id
        body_record.height_cm = user.height_cm
        body_record.weight_kg = user.weight_kg
        body_record.age = user.age
        body_record.gender = user.gender
        body_record.activity_level = user.activity_level
        body_record.bmi = user.bmi
        body_record.bmr = user.bmr
        body_record.daily_calorie_goal = daily_calorie
        body_record.calorie_coefficient = user.calorie_coefficient
        body_record.protein_ratio = user.protein_ratio
        body_record.fat_ratio = user.fat_ratio
        body_record.carb_ratio = user.carb_ratio
        db.session.add(body_record)

        db.session.commit()

        # 校准个人代谢系数
        try:
            from app.services.metabolism import MetabolismService
            MetabolismService.apply_calibration(user)
        except Exception:
            pass

        return success({
            'health_goal': health_goal,
            'calorie_coefficient': float(user.calorie_coefficient),
            'daily_calorie_goal': daily_calorie,
            'nutrient_targets': NutritionService.calculate_nutrient_targets(
                daily_calorie, user.protein_ratio, user.fat_ratio, user.carb_ratio
            ),
            'nutrient_ratios': {
                'protein': float(user.protein_ratio),
                'fat': float(user.fat_ratio),
                'carb': float(user.carb_ratio)
            }
        }, '更新成功')
        
    except Exception as e:
        db.session.rollback()
        return error(f'更新失败: {str(e)}')


@user_bp.route('/diet-preference', methods=['PUT'])
@login_required
def update_diet_preference():
    """更新饮食偏好"""
    user = g.current_user
    data = request.get_json() or {}
    
    diet_preference = data.get('diet_preference', '')
    
    try:
        user.diet_preference = diet_preference
        db.session.commit()
        
        return success({
            'diet_preference': diet_preference
        }, '更新成功')
        
    except Exception as e:
        db.session.rollback()
        return error(f'更新失败: {str(e)}')


@user_bp.route('/body-history', methods=['GET'])
@login_required
def get_body_history():
    """获取身体记录历史"""
    user = g.current_user
    
    # 日期范围参数（可选，如 days=7 表示只查近7天）
    days = request.args.get('days', type=int)
    
    query = BodyRecord.query.filter_by(user_id=user.id)
    
    if days:
        start_date = date.today() - timedelta(days=days - 1)
        query = query.filter(BodyRecord.recorded_at >= start_date)
    
    query = query.order_by(BodyRecord.recorded_at.desc())
    
    # 有日期过滤时不分页，直接返回全部
    if days:
        records = query.all()
        return success({
            'items': [record.to_dict() for record in records],
            'total': len(records)
        })
    
    # 无日期过滤时保持分页
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return success({
        'items': [record.to_dict() for record in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@user_bp.route('/avatar', methods=['POST'])
@login_required
def upload_avatar():
    """上传用户头像"""
    user = g.current_user

    if 'file' not in request.files:
        return error('请选择头像文件')

    file = request.files['file']
    if not file.filename:
        return error('请选择头像文件')

    # 校验文件类型
    allowed_exts = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_exts:
        return error('头像仅支持 png/jpg/jpeg/gif/webp 格式')

    # 校验文件大小（不超过 2MB）
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > 2 * 1024 * 1024:
        return error('头像大小不能超过 2MB')

    try:
        # 生成唯一文件名
        filename = f"user_{user.id}_{uuid.uuid4().hex[:8]}.{ext}"

        # 保存到 Flask static 目录
        upload_dir = os.path.join(current_app.static_folder, 'uploads', 'avatars')
        os.makedirs(upload_dir, exist_ok=True)

        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

        # 更新用户头像字段（存相对路径）
        avatar_url = f'/static/uploads/avatars/{filename}'
        user.avatar = avatar_url
        db.session.commit()

        return success({'avatar': avatar_url}, '头像上传成功')

    except Exception as e:
        db.session.rollback()
        return error(f'头像上传失败: {str(e)}')


@user_bp.route('/send-change-password-code', methods=['POST'])
@login_required
def send_change_password_code():
    """发送修改密码验证码到用户邮箱"""
    user = g.current_user

    if not user.email:
        return error('您的账号未绑定邮箱，无法修改密码')

    success_flag, msg = send_verification_code(user.email, purpose='change_password')
    if not success_flag:
        return error(msg)

    return success(message=msg)


@user_bp.route('/change-password', methods=['PUT'])
@login_required
def change_password():
    """通过邮箱验证码修改密码"""
    user = g.current_user
    data = request.get_json() or {}

    code = data.get('code', '').strip()
    new_password = data.get('new_password', '')

    if not user.email:
        return error('您的账号未绑定邮箱，无法修改密码')

    if not code:
        return error('请输入验证码')

    if not validate_password(new_password):
        return error('新密码至少6位')

    new_password = str(new_password)

    # 校验验证码
    valid, msg = verify_code(user.email, code)
    if not valid:
        return error(msg)

    try:
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        return success(message='密码修改成功')
    except Exception as e:
        db.session.rollback()
        return error(f'修改密码失败: {str(e)}')

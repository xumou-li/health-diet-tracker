"""用户管理API"""
import json
from datetime import date
from flask import Blueprint, request, g
from sqlalchemy import func
from app.extensions import db
from app.models import User, MealRecord, AdminLog
from app.utils.response import success, error
from app.utils.auth import admin_required

admin_users_bp = Blueprint('admin_users', __name__)


def log_action(action, target_type, target_id, details=None):
    """记录管理员操作"""
    log = AdminLog(
        admin_id=g.current_admin.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=json.dumps(details) if details else None,
        ip_address=request.remote_addr
    )
    db.session.add(log)


@admin_users_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard():
    """数据概览面板"""
    today = date.today()
    
    # 用户统计
    total_users = User.query.filter_by(is_deleted=False).count()
    today_new_users = User.query.filter(
        User.is_deleted == False,
        func.date(User.created_at) == today
    ).count()
    
    # 活跃用户（今日有记录）
    active_users = db.session.query(func.count(func.distinct(MealRecord.user_id))).filter(
        MealRecord.date == today
    ).scalar() or 0
    
    # 今日记录数
    today_records = MealRecord.query.filter_by(date=today).count()
    
    # BMI分布
    bmi_stats = {
        'underweight': User.query.filter(User.is_deleted == False, User.bmi < 18.5).count(),
        'normal': User.query.filter(User.is_deleted == False, User.bmi >= 18.5, User.bmi < 24).count(),
        'overweight': User.query.filter(User.is_deleted == False, User.bmi >= 24, User.bmi < 28).count(),
        'obese': User.query.filter(User.is_deleted == False, User.bmi >= 28).count()
    }
    
    return success({
        'users': {
            'total': total_users,
            'today_new': today_new_users,
            'today_active': active_users
        },
        'records': {
            'today': today_records
        },
        'bmi_distribution': bmi_stats
    })


@admin_users_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """用户列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '')
    status = request.args.get('status')  # frozen / active
    
    query = User.query.filter_by(is_deleted=False)
    
    if keyword:
        query = query.filter(
            (User.phone.like(f'%{keyword}%')) | (User.email.like(f'%{keyword}%'))
        )
    
    if status == 'frozen':
        query = query.filter_by(is_frozen=True)
    elif status == 'active':
        query = query.filter_by(is_frozen=False)
    
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    users = []
    for user in pagination.items:
        user_dict = user.to_dict()
        user_dict['is_frozen'] = user.is_frozen
        users.append(user_dict)
    
    return success({
        'items': users,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@admin_users_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user_detail(user_id):
    """用户详情"""
    user = User.query.filter_by(id=user_id, is_deleted=False).first()
    
    if not user:
        return error('用户不存在', 404)
    
    # 脱敏处理
    user_dict = user.to_dict()
    if user_dict.get('phone'):
        phone = user_dict['phone']
        user_dict['phone'] = phone[:3] + '****' + phone[-4:]
    if user_dict.get('email'):
        email = user_dict['email']
        at_idx = email.find('@')
        if at_idx > 2:
            user_dict['email'] = email[:2] + '***' + email[at_idx:]
    
    user_dict['is_frozen'] = user.is_frozen
    
    # 统计
    record_count = MealRecord.query.filter_by(user_id=user_id).count()
    user_dict['record_count'] = record_count
    
    return success(user_dict)


@admin_users_bp.route('/users/<int:user_id>/freeze', methods=['PUT'])
@admin_required
def toggle_freeze_user(user_id):
    """冻结/解冻用户"""
    user = User.query.filter_by(id=user_id, is_deleted=False).first()
    
    if not user:
        return error('用户不存在', 404)
    
    try:
        user.is_frozen = not user.is_frozen
        action = 'freeze_user' if user.is_frozen else 'unfreeze_user'
        log_action(action, 'user', user_id, {'user_id': user_id, 'phone': user.phone})
        db.session.commit()
        
        status = '已冻结' if user.is_frozen else '已解冻'
        return success({'is_frozen': user.is_frozen}, f'用户{status}')
        
    except Exception as e:
        db.session.rollback()
        return error(f'操作失败: {str(e)}')


@admin_users_bp.route('/logs', methods=['GET'])
@admin_required
def get_admin_logs():
    """操作日志"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    action = request.args.get('action')
    
    query = AdminLog.query
    
    if action:
        query = query.filter_by(action=action)
    
    pagination = query.order_by(AdminLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return success({
        'items': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

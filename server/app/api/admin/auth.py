"""管理员认证API"""
import json
from datetime import datetime
from flask import Blueprint, request
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.models import Admin
from app.utils.response import success, error

admin_auth_bp = Blueprint('admin_auth', __name__)


@admin_auth_bp.route('/auth/login', methods=['POST'])
def admin_login():
    """管理员登录"""
    data = request.get_json() or {}
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return error('请输入用户名和密码')
    
    admin = Admin.query.filter_by(username=username).first()
    
    if not admin:
        return error('用户名或密码错误')
    
    if not admin.is_active:
        return error('账号已被禁用')
    
    if not check_password_hash(admin.password_hash, password):
        return error('用户名或密码错误')
    
    # 更新最后登录时间
    admin.last_login_at = datetime.now()
    db.session.commit()
    
    # 生成JWT
    access_token = create_access_token(
        identity=json.dumps({'type': 'admin', 'id': admin.id})
    )
    
    return success({
        'token': access_token,
        'admin': admin.to_dict()
    }, '登录成功')


@admin_auth_bp.route('/auth/init', methods=['POST'])
def init_admin():
    """初始化超级管理员（仅当无管理员时可用）"""
    # 检查是否已有管理员
    if Admin.query.first():
        return error('管理员已存在，无法初始化')
    
    data = request.get_json() or {}
    
    username = data.get('username', 'admin')
    password = data.get('password', 'admin123')
    
    try:
        admin = Admin(
            username=username,
            password_hash=generate_password_hash(password),
            role=2  # 超级管理员
        )
        db.session.add(admin)
        db.session.commit()
        
        return success({
            'username': username,
            'message': '超级管理员创建成功，请及时修改默认密码'
        })
        
    except Exception as e:
        db.session.rollback()
        return error(f'创建失败: {str(e)}')

"""认证工具"""
import json
from functools import wraps
from flask import g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request, jwt_required
from app.models import User, Admin
from .response import error


def parse_identity(identity_str):
    """解析JWT identity（JSON字符串转字典）"""
    if not identity_str:
        return None
    try:
        if isinstance(identity_str, dict):
            return identity_str
        return json.loads(identity_str)
    except (json.JSONDecodeError, TypeError):
        return None


def get_current_user():
    """获取当前登录用户"""
    try:
        verify_jwt_in_request()
        identity = parse_identity(get_jwt_identity())
        if identity and identity.get('type') == 'user':
            user = User.query.get(identity.get('id'))
            if user and not user.is_deleted and not user.is_frozen:
                return user
    except Exception as e:
        print(f"JWT验证失败: {e}")
    return None


def get_current_admin():
    """获取当前登录管理员"""
    try:
        verify_jwt_in_request()
        identity = parse_identity(get_jwt_identity())
        if identity and identity.get('type') == 'admin':
            admin = Admin.query.get(identity.get('id'))
            if admin and admin.is_active:
                return admin
    except Exception as e:
        print(f"Admin JWT验证失败: {e}")
    return None


def login_required(f):
    """用户登录装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            identity = parse_identity(get_jwt_identity())
            
            if not identity:
                return error('无效的token', 401)
            
            if identity.get('type') != 'user':
                return error('请使用用户账号登录', 401)
            
            user = User.query.get(identity.get('id'))
            if not user:
                return error('用户不存在', 401)
            if user.is_deleted:
                return error('用户已注销', 401)
            if user.is_frozen:
                return error('账号已被冻结', 401)
            
            g.current_user = user
            return f(*args, **kwargs)
        except Exception as e:
            print(f"login_required异常: {e}")
            return error('请先登录', 401)
    return decorated


def admin_required(f):
    """管理员登录装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            identity = parse_identity(get_jwt_identity())
            
            if not identity or identity.get('type') != 'admin':
                return error('请先登录管理后台', 401)
            
            admin = Admin.query.get(identity.get('id'))
            if not admin or not admin.is_active:
                return error('请先登录管理后台', 401)
            
            g.current_admin = admin
            return f(*args, **kwargs)
        except Exception as e:
            print(f"admin_required异常: {e}")
            return error('请先登录管理后台', 401)
    return decorated


def super_admin_required(f):
    """超级管理员装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            identity = parse_identity(get_jwt_identity())
            
            if not identity or identity.get('type') != 'admin':
                return error('请先登录管理后台', 401)
            
            admin = Admin.query.get(identity.get('id'))
            if not admin or not admin.is_active:
                return error('请先登录管理后台', 401)
            if admin.role != 2:
                return error('需要超级管理员权限', 403)
            
            g.current_admin = admin
            return f(*args, **kwargs)
        except Exception as e:
            print(f"super_admin_required异常: {e}")
            return error('请先登录管理后台', 401)
    return decorated

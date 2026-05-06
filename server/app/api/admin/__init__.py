"""管理端API包"""
from flask import Blueprint
from .auth import admin_auth_bp
from .users import admin_users_bp
from .foods import admin_foods_bp
from .config import admin_config_bp
from .logs import admin_logs_bp

admin_bp = Blueprint('admin', __name__)

# 注册子蓝图
admin_bp.register_blueprint(admin_auth_bp)
admin_bp.register_blueprint(admin_users_bp)
admin_bp.register_blueprint(admin_foods_bp)
admin_bp.register_blueprint(admin_config_bp)
admin_bp.register_blueprint(admin_logs_bp)

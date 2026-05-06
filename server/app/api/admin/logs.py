"""管理员操作日志API"""
from flask import Blueprint, request
from app.extensions import db
from app.models import AdminLog
from app.utils.response import success, error
from app.utils.auth import admin_required

admin_logs_bp = Blueprint('admin_logs', __name__)


@admin_logs_bp.route('/logs', methods=['GET'])
@admin_required
def get_logs():
    """获取操作日志（分页 + action 精确筛选）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    action = request.args.get('action', type=str)

    query = AdminLog.query.order_by(AdminLog.created_at.desc())

    if action:
        query = query.filter_by(action=action)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success({
        'items': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

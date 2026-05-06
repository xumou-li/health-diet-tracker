"""系统配置API"""
import json
from datetime import date
from flask import Blueprint, request, g
from sqlalchemy import func
from app.extensions import db
from app.models import SystemConfig, AISuggestion, AdminLog
from app.utils.response import success, error
from app.utils.auth import admin_required, super_admin_required

admin_config_bp = Blueprint('admin_config', __name__)


def log_action(action, target_type, target_id, details=None):
    """记录管理员操作"""
    log = AdminLog()
    log.admin_id = g.current_admin.id
    log.action = action
    log.target_type = target_type
    log.target_id = target_id
    log.details = json.dumps(details) if details else None
    log.ip_address = request.remote_addr
    db.session.add(log)


@admin_config_bp.route('/config', methods=['GET'])
@admin_required
def get_config():
    """获取系统配置"""
    config = SystemConfig.query.first()
    
    if not config:
        config = SystemConfig()
        db.session.add(config)
        db.session.commit()
    
    # 普通管理员不显示API Key
    include_key = g.current_admin.role == 2
    
    return success(config.to_dict(include_key=include_key))


@admin_config_bp.route('/config', methods=['PUT'])
@super_admin_required
def update_config():
    """更新系统配置（仅超级管理员）"""
    data = request.get_json() or {}
    
    config = SystemConfig.query.first()
    if not config:
        config = SystemConfig()
        db.session.add(config)
    
    try:
        if 'ai_enabled' in data:
            config.ai_enabled = bool(data['ai_enabled'])
        if 'ai_daily_limit' in data:
            config.ai_daily_limit = max(1, int(data['ai_daily_limit']))
        if 'ai_model' in data:
            config.ai_model = data['ai_model']
        if 'ai_api_key' in data:
            config.ai_api_key = data['ai_api_key']
        if 'ai_api_base_url' in data:
            config.ai_api_base_url = (data['ai_api_base_url'] or '').strip() or None
        if 'ai_prompt_template' in data:
            config.ai_prompt_template = data['ai_prompt_template']
        if 'announcement' in data:
            config.announcement = data['announcement']
        
        log_action('update_config', 'config', config.id, {'changed_fields': list(data.keys())})
        db.session.commit()
        
        return success(config.to_dict(include_key=True), '配置更新成功')
        
    except Exception as e:
        db.session.rollback()
        return error(f'更新失败: {str(e)}')


@admin_config_bp.route('/stats/ai', methods=['GET'])
@admin_required
def get_ai_stats():
    """AI调用统计"""
    today = date.today()
    
    # 今日统计
    today_count = AISuggestion.query.filter(
        func.date(AISuggestion.created_at) == today
    ).count()
    
    # 今日调用人数
    today_users = db.session.query(
        func.count(func.distinct(AISuggestion.user_id))
    ).filter(
        func.date(AISuggestion.created_at) == today
    ).scalar() or 0
    
    # 今日Token消耗
    today_tokens = db.session.query(
        func.sum(AISuggestion.tokens_used)
    ).filter(
        func.date(AISuggestion.created_at) == today
    ).scalar() or 0
    
    # 平均响应时间
    avg_response_time = db.session.query(
        func.avg(AISuggestion.response_time_ms)
    ).filter(
        func.date(AISuggestion.created_at) == today
    ).scalar() or 0
    
    # 总统计
    total_count = AISuggestion.query.count()
    total_tokens = db.session.query(func.sum(AISuggestion.tokens_used)).scalar() or 0
    
    return success({
        'today': {
            'total_calls': today_count,
            'today_users': today_users,
            'tokens_used': today_tokens,
            'avg_response_ms': round(avg_response_time)
        },
        'all_time': {
            'total_calls': total_count,
            'total_tokens': total_tokens
        }
    })

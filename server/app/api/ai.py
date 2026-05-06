"""AI问答API"""
import json
from datetime import date
from flask import Blueprint, request, g, Response, stream_with_context
from app.extensions import db
from app.models import MealRecord, AISuggestion
from app.utils.response import success, error
from app.utils.auth import login_required
from app.services.ai_service import AIService
from app.services.nutrition import NutritionService

ai_bp = Blueprint('ai', __name__)


def get_today_stats(user_id):
    """获取今日摄入统计"""
    today = date.today()
    meals = MealRecord.query.filter_by(user_id=user_id, date=today).all()
    
    return {
        'calorie': sum(m.calorie for m in meals),
        'protein': sum(float(m.protein) for m in meals),
        'carb': sum(float(m.carb) for m in meals),
        'fat': sum(float(m.fat) for m in meals)
    }


@ai_bp.route('/status', methods=['GET'])
@login_required
def get_ai_status():
    """AI功能状态（开关、剩余次数）"""
    user = g.current_user
    
    enabled = AIService.is_enabled()
    remaining = AIService.get_remaining_calls(user.id) if enabled else 0
    config = AIService.get_config()
    
    return success({
        'enabled': enabled,
        'daily_limit': config.ai_daily_limit,
        'remaining_calls': remaining,
        'disclaimer': '仅供参考，不替代专业医疗建议'
    })


@ai_bp.route('/chat', methods=['POST'])
@login_required
def ai_chat():
    """AI问答"""
    user = g.current_user
    data = request.get_json() or {}
    
    question = data.get('question', '').strip()
    
    if not question:
        return error('请输入问题')
    
    if len(question) > 500:
        return error('问题过长，请精简')
    
    if not AIService.is_enabled():
        return error('AI功能暂未开启')
    
    if AIService.get_remaining_calls(user.id) <= 0:
        return error('今日AI调用次数已用完')
    
    # 获取今日统计
    daily_stats = get_today_stats(user.id)
    targets = NutritionService.calculate_nutrient_targets(user.daily_calorie_goal)
    
    # 调用AI
    content, err = AIService.chat(user, daily_stats, targets, question)
    
    if err:
        return error(err)
    
    return success({
        'question': question,
        'answer': content,
        'remaining_calls': AIService.get_remaining_calls(user.id),
        'disclaimer': '仅供参考，不替代专业医疗建议'
    })


@ai_bp.route('/chat/stream', methods=['POST'])
@login_required
def ai_chat_stream():
    """AI问答（流式 SSE）"""
    user = g.current_user
    data = request.get_json() or {}

    question = data.get('question', '').strip()

    if not question:
        return error('请输入问题')

    if len(question) > 500:
        return error('问题过长，请精简')

    if not AIService.is_enabled():
        return error('AI功能暂未开启')

    if AIService.get_remaining_calls(user.id) <= 0:
        return error('今日AI调用次数已用完')

    daily_stats = get_today_stats(user.id)
    targets = NutritionService.calculate_nutrient_targets(user.daily_calorie_goal)

    def generate():
        for chunk, err in AIService.chat_stream(user, daily_stats, targets, question):
            if err:
                yield f"data: {json.dumps({'error': err}, ensure_ascii=False)}\n\n"
                return
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@ai_bp.route('/history', methods=['GET'])
@login_required
def get_ai_history():
    """AI建议历史记录"""
    user = g.current_user
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    suggestion_type = request.args.get('type')  # 可选过滤
    
    query = AISuggestion.query.filter_by(user_id=user.id, is_deleted=False)
    
    if suggestion_type:
        query = query.filter_by(suggestion_type=suggestion_type)
    
    pagination = query.order_by(AISuggestion.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return success({
        'items': [s.to_dict() for s in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@ai_bp.route('/history', methods=['DELETE'])
@login_required
def clear_ai_history():
    """清空AI历史记录（软删除，不影响管理端统计）"""
    user = g.current_user
    suggestion_type = request.args.get('type')
    
    query = AISuggestion.query.filter_by(user_id=user.id, is_deleted=False)
    
    if suggestion_type:
        query = query.filter_by(suggestion_type=suggestion_type)
    
    updated_count = query.update({'is_deleted': True}, synchronize_session=False)
    db.session.commit()
    
    return success({'deleted_count': updated_count})

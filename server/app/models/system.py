"""系统相关模型"""
from datetime import datetime
from app.config import DEFAULT_AI_API_BASE_URL
from app.extensions import db


class SystemConfig(db.Model):
    """系统配置表"""
    __tablename__ = 'system_configs'
    
    id = db.Column(db.Integer, primary_key=True, default=1)
    ai_enabled = db.Column(db.Boolean, default=True, comment='AI功能开关')
    ai_daily_limit = db.Column(db.Integer, default=10, comment='每用户每日AI调用限额')
    ai_model = db.Column(db.String(50), default='deepseek-chat', comment='默认AI模型')
    ai_api_key = db.Column(db.String(255), comment='AI API密钥(加密存储)')
    ai_api_base_url = db.Column(db.String(255), default=DEFAULT_AI_API_BASE_URL, comment='AI API基础地址')
    ai_prompt_template = db.Column(db.Text, comment='AI提示词模板')
    announcement = db.Column(db.Text, comment='系统公告')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self, include_key=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'ai_enabled': self.ai_enabled,
            'ai_daily_limit': self.ai_daily_limit,
            'ai_model': self.ai_model,
            'ai_api_base_url': self.ai_api_base_url or '',
            'ai_prompt_template': self.ai_prompt_template,
            'announcement': self.announcement,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_key:
            data['ai_api_key'] = self.ai_api_key
        return data


class AISuggestion(db.Model):
    """AI建议记录表"""
    __tablename__ = 'ai_suggestions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')
    suggestion_type = db.Column(db.String(20), nullable=False, comment='建议类型: suggestion/evaluate/recommend/chat')
    prompt = db.Column(db.Text, comment='发送给LLM的Prompt')
    content = db.Column(db.Text, nullable=False, comment='AI生成的建议文本')
    model = db.Column(db.String(50), comment='使用的模型名称')
    tokens_used = db.Column(db.Integer, comment='Token消耗量')
    response_time_ms = db.Column(db.Integer, comment='响应时间(毫秒)')
    is_deleted = db.Column(db.Boolean, default=False, comment='软删除标记')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (
        db.Index('idx_ai_user_date', 'user_id', db.func.date('created_at')),
    )
    
    def to_dict(self):
        """转换为字典"""
        import re, json
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'suggestion_type': self.suggestion_type,
            'content': self.content,
            'model': self.model,
            'tokens_used': self.tokens_used,
            'response_time_ms': self.response_time_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        # 对chat类型，从prompt中提取用户原始问题
        if self.suggestion_type == 'chat' and self.prompt:
            prompt_str = self.prompt.strip()
            if prompt_str.startswith('['):
                # 新格式：JSON messages 数组，取最后一条 user 消息
                try:
                    msgs = json.loads(prompt_str)
                    for msg in reversed(msgs):
                        if msg.get('role') == 'user' and msg.get('content'):
                            data['question'] = msg['content']
                            break
                except (json.JSONDecodeError, TypeError):
                    pass
            else:
                # 旧格式：单个 prompt 字符串
                match = re.search(r'用户问题[：:]\s*(.+?)(?:\n\s*\n|$)', prompt_str, re.DOTALL)
                if match:
                    data['question'] = match.group(1).strip()
        return data

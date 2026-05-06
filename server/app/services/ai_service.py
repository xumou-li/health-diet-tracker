"""AI服务封装"""
import json
import time
import requests
from datetime import date
from flask import current_app
from app.config import DEFAULT_AI_API_BASE_URL
from app.extensions import db
from app.models import AISuggestion, SystemConfig


class AIService:
    """AI服务 - 封装LLM调用"""

    UPSTREAM_ERROR_LOG_LIMIT = 1000
    UPSTREAM_ERROR_MESSAGE_LIMIT = 120
    
    # 通用聊天系统提示（当 ai_prompt_template 未配置时使用）
    DEFAULT_CHAT_SYSTEM = """你是一个专业的营养师助手，名叫"小营"。
用户信息：性别{gender}，年龄{age}岁，BMI={bmi}({bmi_status})，健康目标={goal}
今日摄入：热量{calorie}kcal（目标{target_calorie}kcal），蛋白质{protein}g，脂肪{fat}g，碳水{carb}g

请根据用户的问题提供专业的饮食建议和解答。简洁友好，150字以内。非饮食话题礼貌引导回饮食。"""

    @staticmethod
    def get_api_base_url(config):
        """获取AI API基础地址"""
        api_base_url = (
            (config.ai_api_base_url or '').strip()
            or (current_app.config.get('AI_API_BASE_URL', '') or '').strip()
            or DEFAULT_AI_API_BASE_URL
        )
        return api_base_url.rstrip('/')
    
    @staticmethod
    def get_config():
        """获取AI配置"""
        config = SystemConfig.query.first()
        if not config:
            config = SystemConfig()
            db.session.add(config)
            db.session.commit()
        return config

    @classmethod
    def _trim_text(cls, text, limit):
        """裁剪文本长度，避免返回超长错误"""
        if not text:
            return ''

        text = ' '.join(str(text).split())
        if len(text) <= limit:
            return text

        return f"{text[:limit].rstrip()}..."

    @classmethod
    def _extract_upstream_error_text(cls, response):
        """提取上游错误信息摘要"""
        try:
            payload = response.json()
        except ValueError:
            payload = None

        candidates = []
        if isinstance(payload, dict):
            for key in ('message', 'error', 'detail'):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    candidates.append(value)
                elif isinstance(value, dict):
                    nested_message = value.get('message') or value.get('detail')
                    if isinstance(nested_message, str) and nested_message.strip():
                        candidates.append(nested_message)

            if not candidates and payload:
                candidates.append(json.dumps(payload, ensure_ascii=False))

        if not candidates:
            raw_text = (response.text or '').strip()
            if raw_text:
                candidates.append(raw_text)

        if not candidates:
            return '', ''

        full_text = cls._trim_text(candidates[0], cls.UPSTREAM_ERROR_LOG_LIMIT)
        short_text = cls._trim_text(candidates[0], cls.UPSTREAM_ERROR_MESSAGE_LIMIT)
        return short_text, full_text
    
    @classmethod
    def is_enabled(cls):
        """AI功能是否开启"""
        config = cls.get_config()
        return config.ai_enabled
    
    @classmethod
    def get_remaining_calls(cls, user_id):
        """获取用户今日剩余调用次数"""
        from app.models import User
        config = cls.get_config()
        user = User.query.get(user_id)
        if not user:
            return 0
        
        today = date.today()
        # 如果今天还没调用过（或日期不匹配），剩余次数 = 每日限额
        if user.last_ai_call_date != today:
            return config.ai_daily_limit
        
        return max(0, config.ai_daily_limit - user.daily_ai_calls)
    
    @classmethod
    def call_llm(cls, prompt, user_id, suggestion_type, messages=None):
        """调用LLM API
        
        Args:
            prompt: 单个prompt字符串（向后兼容，当messages为None时使用）
            messages: 完整的消息数组，如 [{"role":"system",...}, {"role":"user",...}]
        """
        config = cls.get_config()
        
        # 获取API配置
        api_key = config.ai_api_key or current_app.config.get('AI_API_KEY', '')
        api_base = cls.get_api_base_url(config)
        model = config.ai_model or 'deepseek-chat'
        
        if not api_key:
            return None, "AI服务未配置API密钥"
        
        start_time = time.time()
        
        # 构建消息
        if messages:
            api_messages = messages
        else:
            api_messages = [{"role": "user", "content": prompt}]
        
        # 用于存储记录时保留原始prompt
        stored_prompt = prompt if not messages else json.dumps(messages, ensure_ascii=False)
        
        try:
            response = requests.post(
                f"{api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": api_messages,
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=30
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code != 200:
                short_error, full_error = cls._extract_upstream_error_text(response)
                current_app.logger.error(
                    'AI upstream request failed: status=%s model=%s user_id=%s response=%s',
                    response.status_code,
                    model,
                    user_id,
                    full_error or '[empty response body]'
                )

                message = f"AI服务调用失败: {response.status_code}"
                if short_error:
                    message = f"{message} - {short_error}"

                return None, message
            
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            tokens = result.get('usage', {}).get('total_tokens', 0)
            
            if not content:
                return None, "AI服务返回内容为空"
            
            # 记录调用
            suggestion = AISuggestion()
            suggestion.user_id = user_id
            suggestion.suggestion_type = suggestion_type
            suggestion.prompt = stored_prompt
            suggestion.content = content
            suggestion.model = model
            suggestion.tokens_used = tokens
            suggestion.response_time_ms = response_time
            db.session.add(suggestion)
            
            # 更新用户今日AI调用计数（与历史记录解耦，避免清空历史时重置次数）
            from app.models import User
            user = User.query.get(user_id)
            today = date.today()
            if user.last_ai_call_date != today:
                user.daily_ai_calls = 1
                user.last_ai_call_date = today
            else:
                user.daily_ai_calls += 1
            
            db.session.commit()
            
            return content, None
            
        except requests.exceptions.Timeout:
            return None, "AI服务响应超时"
        except requests.exceptions.RequestException as e:
            return None, f"AI服务请求失败: {str(e)}"
        except Exception as e:
            return None, f"AI服务异常: {str(e)}"
    
    @classmethod
    def _get_chat_history(cls, user_id, limit=5):
        """获取最近N条聊天记录，返回 [{"role":"user","content":...}, {"role":"assistant","content":...}]"""
        import re
        records = AISuggestion.query.filter_by(
            user_id=user_id,
            suggestion_type='chat',
            is_deleted=False
        ).order_by(AISuggestion.created_at.desc()).limit(limit).all()
        
        records = list(reversed(records))  # 旧→新
        
        history = []
        for record in records:
            question = ''
            answers = []
            
            if record.prompt:
                prompt_str = record.prompt.strip()
                # 新格式：JSON messages 数组
                if prompt_str.startswith('['):
                    try:
                        msgs = json.loads(prompt_str)
                        for msg in msgs:
                            if msg.get('role') == 'user' and msg.get('content'):
                                question = msg['content']
                            elif msg.get('role') == 'assistant' and msg.get('content'):
                                answers.append(msg['content'])
                    except (json.JSONDecodeError, TypeError):
                        pass
                else:
                    # 旧格式：单个 prompt 字符串
                    match = re.search(r'用户问题[：:]\s*(.+?)(?:\n\s*\n|$)', prompt_str, re.DOTALL)
                    if match:
                        question = match.group(1).strip()
            
            if not question:
                continue
            
            answer = record.content
            if not answer and answers:
                answer = answers[-1]  # 新格式：取最后一条 assistant 回复
            
            if question and answer:
                history.append({"role": "user", "content": question})
                history.append({"role": "assistant", "content": answer})
        
        return history

    @classmethod
    def chat(cls, user, daily_stats, targets, question):
        """AI问答（带上下文历史，使用可配提示词模板）"""
        gender_map = {0: '男', 1: '女', 2: '其他'}
        goal_map = {1: '维持体重', 2: '减脂', 3: '增肌'}
        
        from app.services.nutrition import NutritionService
        
        config = cls.get_config()
        template = (config.ai_prompt_template or '').strip() or cls.DEFAULT_CHAT_SYSTEM
        
        system_msg = template.format(
            gender=gender_map.get(user.gender, '未知'),
            age=user.age,
            bmi=float(user.bmi),
            bmi_status=NutritionService.get_bmi_status(float(user.bmi)),
            goal=goal_map.get(user.health_goal, '维持体重'),
            calorie=round(daily_stats['calorie']),
            target_calorie=targets['calorie'],
            protein=round(daily_stats['protein'], 1),
            fat=round(daily_stats['fat'], 1),
            carb=round(daily_stats['carb'], 1)
        )
        
        history = cls._get_chat_history(user.id, limit=5)
        messages = [{"role": "system", "content": system_msg}]
        messages.extend(history)
        messages.append({"role": "user", "content": question})
        
        return cls.call_llm(system_msg, user.id, 'chat', messages=messages)
    
    @classmethod
    def chat_stream(cls, user, daily_stats, targets, question):
        """AI问答（流式生成器，使用可配提示词模板）— yield (content_chunk, error_string)"""
        gender_map = {0: '男', 1: '女', 2: '其他'}
        goal_map = {1: '维持体重', 2: '减脂', 3: '增肌'}
        
        from app.services.nutrition import NutritionService
        
        config = cls.get_config()
        template = (config.ai_prompt_template or '').strip() or cls.DEFAULT_CHAT_SYSTEM
        
        system_msg = template.format(
            gender=gender_map.get(user.gender, '未知'),
            age=user.age,
            bmi=float(user.bmi),
            bmi_status=NutritionService.get_bmi_status(float(user.bmi)),
            goal=goal_map.get(user.health_goal, '维持体重'),
            calorie=round(daily_stats['calorie']),
            target_calorie=targets['calorie'],
            protein=round(daily_stats['protein'], 1),
            fat=round(daily_stats['fat'], 1),
            carb=round(daily_stats['carb'], 1)
        )
        
        history = cls._get_chat_history(user.id, limit=5)
        api_messages = [{"role": "system", "content": system_msg}]
        api_messages.extend(history)
        api_messages.append({"role": "user", "content": question})
        
        config = cls.get_config()
        api_key = config.ai_api_key or current_app.config.get('AI_API_KEY', '')
        api_base = cls.get_api_base_url(config)
        model = config.ai_model or 'deepseek-chat'
        
        if not api_key:
            yield '', 'AI服务未配置API密钥'
            return
        
        start_time = time.time()
        full_content = ''
        
        try:
            response = requests.post(
                f"{api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": api_messages,
                    "max_tokens": 500,
                    "temperature": 0.7,
                    "stream": True
                },
                timeout=30,
                stream=True
            )
            
            if response.status_code != 200:
                short_error, full_error = cls._extract_upstream_error_text(response)
                msg = f"AI服务调用失败: {response.status_code}"
                if short_error:
                    msg = f"{msg} - {short_error}"
                yield '', msg
                return
            
            for line in response.iter_lines():
                if not line:
                    continue
                line_text = line.decode('utf-8').strip()
                if not line_text.startswith('data: '):
                    continue
                data_str = line_text[6:]
                if data_str == '[DONE]':
                    break
                try:
                    chunk_data = json.loads(data_str)
                    delta = chunk_data.get('choices', [{}])[0].get('delta', {})
                    content = delta.get('content', '')
                    if content:
                        full_content += content
                        yield content, None
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
            
            response_time = int((time.time() - start_time) * 1000)
            
            if not full_content:
                yield '', 'AI服务返回内容为空'
                return
            
            # 保存记录 + 更新计数
            suggestion = AISuggestion()
            suggestion.user_id = user.id
            suggestion.suggestion_type = 'chat'
            suggestion.prompt = json.dumps(api_messages, ensure_ascii=False)
            suggestion.content = full_content
            suggestion.model = model
            suggestion.response_time_ms = response_time
            # 流式API不返回usage，按字符估算token（中英混合约2字符/1token）
            prompt_chars = len(suggestion.prompt or '')
            content_chars = len(full_content)
            suggestion.tokens_used = max(1, int((prompt_chars + content_chars) / 2))
            db.session.add(suggestion)
            
            today = date.today()
            if user.last_ai_call_date != today:
                user.daily_ai_calls = 1
                user.last_ai_call_date = today
            else:
                user.daily_ai_calls += 1
            
            db.session.commit()
            
        except requests.exceptions.Timeout:
            yield '', 'AI服务响应超时'
        except requests.exceptions.RequestException as e:
            yield '', f'AI服务请求失败: {str(e)}'
        except Exception as e:
            yield '', f'AI服务异常: {str(e)}'

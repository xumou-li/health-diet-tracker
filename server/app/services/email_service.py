"""邮件服务 —— 验证码发送与校验"""
import random
import time
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# SMTP 配置（QQ邮箱）
SMTP_SERVER = 'smtp.qq.com'
SMTP_PORT = 587
SENDER_EMAIL = '1146782462@qq.com'
SENDER_AUTH_CODE = 'cvwryzxbsrgjbaed'
SENDER_NICKNAME = '有何不可'

# 验证码有效期（秒）
CODE_EXPIRE_SECONDS = 300  # 5分钟
# 同一邮箱发送间隔（秒）
CODE_COOLDOWN_SECONDS = 60

# 内存存储: {email: {'code': str, 'expires_at': float, 'last_sent_at': float}}
_codes = {}


def _clean_expired():
    """清理过期验证码"""
    now = time.time()
    expired = [e for e, v in _codes.items() if v['expires_at'] < now]
    for e in expired:
        del _codes[e]


def send_verification_code(to_email: str, purpose: str = 'register') -> tuple:
    """
    发送验证码到指定邮箱
    purpose: 'register'（注册）或 'change_password'（修改密码）
    返回: (success: bool, message: str)
    """
    _clean_expired()
    now = time.time()

    # 检查发送间隔
    existing = _codes.get(to_email)
    if existing and (now - existing.get('last_sent_at', 0)) < CODE_COOLDOWN_SECONDS:
        remaining = int(CODE_COOLDOWN_SECONDS - (now - existing['last_sent_at']))
        return False, f'请{remaining}秒后再试'

    # 生成6位数字验证码
    code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

    # 根据用途选择邮件主题和正文
    if purpose == 'change_password':
        subject = '修改密码验证码 - 健康饮食记录'
        title_text = '修改密码验证码'
    else:
        subject = '注册验证码 - 健康饮食记录'
        title_text = '您的注册验证码'

    body = f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5;">
  <div style="max-width: 480px; margin: 0 auto; background: #fff; border-radius: 12px; padding: 32px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);">
    <h2 style="color: #2e7d32; margin: 0 0 16px;">🧑‍🍳 健康饮食记录</h2>
    <p style="color: #333; font-size: 15px; margin: 0 0 8px;">{title_text}：</p>
    <div style="background: #e8f5e9; border-radius: 8px; padding: 16px; text-align: center; margin: 16px 0;">
      <span style="font-size: 32px; font-weight: bold; color: #2e7d32; letter-spacing: 6px;">{code}</span>
    </div>
    <p style="color: #888; font-size: 13px; margin: 0;">验证码 5 分钟内有效，请勿泄露给他人。</p>
    <p style="color: #bbb; font-size: 12px; margin: 24px 0 0;">此邮件由系统自动发送，请勿回复。</p>
  </div>
</body>
</html>'''

    try:
        message = MIMEMultipart()
        byte_nickname = SENDER_NICKNAME.encode('utf-8')
        encoded_nickname = base64.b64encode(byte_nickname).decode('ascii')
        formatted_nickname = f'=?utf-8?B?{encoded_nickname}?='
        message['From'] = f'"{formatted_nickname}" <{SENDER_EMAIL}>'
        message['To'] = to_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'html', 'utf-8'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_AUTH_CODE)
        server.sendmail(SENDER_EMAIL, [to_email], message.as_string())
        server.quit()

        # 存储验证码
        _codes[to_email] = {
            'code': code,
            'expires_at': now + CODE_EXPIRE_SECONDS,
            'last_sent_at': now
        }

        return True, '验证码已发送'
    except smtplib.SMTPException as e:
        return False, f'邮件发送失败: {str(e)}'


def verify_code(email: str, code: str) -> tuple:
    """
    校验验证码
    返回: (valid: bool, message: str)
    """
    _clean_expired()

    existing = _codes.get(email)
    if not existing:
        return False, '请先获取验证码'

    if existing['expires_at'] < time.time():
        del _codes[email]
        return False, '验证码已过期，请重新获取'

    if existing['code'] != str(code).strip():
        return False, '验证码错误'

    # 验证通过，删除已使用的验证码
    del _codes[email]
    return True, '验证通过'

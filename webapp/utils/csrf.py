"""
CSRF保护模块

功能：
- 生成CSRF令牌
- 验证CSRF令牌
- 提供Flask模板上下文处理器

使用说明：
- 在需要保护的表单中添加 {% csrf_token %}
- 使用 generate_csrf_token() 生成令牌
- 使用 validate_csrf_token() 验证令牌
"""
import secrets
import time
from flask import session, request


CSRF_TOKEN_LENGTH = 32
CSRF_TOKEN_EXPIRE = 10800


def generate_csrf_token():
    """
    生成CSRF令牌

    返回:
        str: 唯一的CSRF令牌
    """
    if 'csrf_token' not in session or is_csrf_token_expired():
        token = secrets.token_hex(CSRF_TOKEN_LENGTH)
        session['csrf_token'] = token
        session['csrf_token_time'] = time.time()
    return session.get('csrf_token')


def is_csrf_token_expired():
    """
    检查CSRF令牌是否过期

    返回:
        bool: 令牌过期返回True，否则返回False
    """
    token_time = session.get('csrf_token_time', 0)
    return (time.time() - token_time) > CSRF_TOKEN_EXPIRE


def validate_csrf_token(token):
    """
    验证CSRF令牌是否有效

    参数:
        token: 待验证的令牌

    返回:
        bool: 令牌有效返回True，否则返回False
    """
    if not token:
        return False
    
    session_token = session.get('csrf_token')
    if not session_token:
        return False
    
    return secrets.compare_digest(token, session_token)


def get_csrf_token_from_request():
    """
    从请求中获取CSRF令牌

    优先从请求头获取，其次从表单获取

    返回:
        str or None: CSRF令牌，如果不存在返回None
    """
    token = request.headers.get('X-CSRF-Token')
    if token:
        return token
    
    if request.form:
        token = request.form.get('csrf_token')
        if token:
            return token
    
    if request.get_json(silent=True):
        token = request.json.get('csrf_token') if request.json else None
        if token:
            return token
    
    return None


def require_csrf_protection():
    """
    验证请求中的CSRF令牌

    用于需要CSRF保护的装饰器

    返回:
        tuple: (是否有效, 错误消息)
    """
    if request.method in ['GET', 'HEAD', 'OPTIONS']:
        return True, None
    
    token = get_csrf_token_from_request()
    if not token:
        return False, "缺少CSRF令牌"
    
    if not validate_csrf_token(token):
        return False, "CSRF令牌验证失败"
    
    return True, None

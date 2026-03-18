"""
请求限流模块

功能：
- 基于IP的请求限流
- 基于用户的请求限流
- 防止API滥用和暴力破解

配置说明（在config.py中设置）：
- RATE_LIMIT_ENABLED: 是否启用限流，默认True
- RATE_LIMIT_PER_MINUTE: 每分钟允许的请求数，默认60
- RATE_LIMIT_PER_HOUR: 每小时允许的请求数，默认1000
"""
import time
from collections import defaultdict
from flask import request, jsonify
from functools import wraps
from webapp.utils.login_security import get_client_ip

request_counts = defaultdict(list)
RATE_LIMIT_PER_MINUTE = 60
RATE_LIMIT_PER_HOUR = 1000
CLEANUP_INTERVAL = 3600
last_cleanup = time.time()


def cleanup_old_requests():
    """清理过期的请求记录"""
    global request_counts, last_cleanup
    
    current_time = time.time()
    if current_time - last_cleanup > CLEANUP_INTERVAL:
        cutoff_time = current_time - 3600
        for key in list(request_counts.keys()):
            request_counts[key] = [t for t in request_counts[key] if t > cutoff_time]
            if not request_counts[key]:
                del request_counts[key]
        last_cleanup = current_time


def check_rate_limit(key, limit, window):
    """
    检查请求是否超过限流限制

    参数:
        key: 限流键（可以是IP或用户ID）
        limit: 允许的最大请求数
        window: 时间窗口（秒）

    返回:
        bool: 是否允许请求
    """
    cleanup_old_requests()
    
    current_time = time.time()
    cutoff_time = current_time - window
    
    request_times = request_counts[key]
    request_times = [t for t in request_times if t > cutoff_time]
    request_counts[key] = request_times
    
    if len(request_times) >= limit:
        return False
    
    request_times.append(current_time)
    request_counts[key] = request_times
    return True


def get_rate_limit_key():
    """获取限流键（优先用户ID，其次IP"""
    from flask import session
    
    user_id = session.get('user_id')
    if user_id:
        return f"user:{user_id}"
    
    ip = get_client_ip()
    return f"ip:{ip}"


def rate_limit(limit=60, window=60, message=None):
    """
    请求限流装饰器

    参数:
        limit: 允许的最大请求数
        window: 时间窗口（秒）
        message: 超限时的错误消息

    使用示例:
        @rate_limit(limit=10, window=60)
        def my_api():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            key = get_rate_limit_key()
            if not check_rate_limit(key, limit, window):
                msg = message or f"请求过于频繁，请{window}秒后再试"
                return jsonify({'code': 429, 'message': msg}), 429
            return f(*args, **kwargs)
        return wrapped
    return decorator


def ip_rate_limit(limit=100, window=60):
    """
    基于IP的限流装饰器

    参数:
        limit: 每IP允许的最大请求数
        window: 时间窗口（秒）
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip = get_client_ip()
            key = f"ip:{ip}"
            if not check_rate_limit(key, limit, window):
                return jsonify({'code': 429, 'message': f'IP请求过于频繁，请{window}秒后再试'}), 429
            return f(*args, **kwargs)
        return wrapped
    return decorator

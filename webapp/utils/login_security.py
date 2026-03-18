"""
登录安全模块

功能：
- 登录失败次数限制
- 账户锁定机制
- 登录时间间隔控制
- IP登录尝试跟踪

配置说明（在config.py中设置）：
- MAX_LOGIN_ATTEMPTS: 最大登录失败次数，默认5次
- LOCKOUT_DURATION: 账户锁定时长（秒），默认1800秒（30分钟）
- LOGIN_TIME_WINDOW: 登录尝试时间窗口（秒），默认300秒（5分钟）
"""
import time
import logging
from functools import wraps
from flask import session, request, jsonify
from database import get_db

logger = logging.getLogger(__name__)


MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 1800
LOGIN_TIME_WINDOW = 300


def record_login_attempt(username, success, ip_address):
    """
    记录登录尝试

    参数:
        username: 用户名
        success: 是否成功
        ip_address: 客户端IP地址
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO login_attempts (username, success, ip_address, attempt_time)
                   VALUES (%s, %s, %s, NOW())""",
                (username, success, ip_address)
            )


def get_recent_login_attempts(username):
    """
    获取用户最近的登录尝试次数

    参数:
        username: 用户名

    返回:
        int: 失败次数
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT COUNT(*) as count FROM login_attempts
                   WHERE username = %s AND success = 0
                   AND attempt_time > DATE_SUB(NOW(), INTERVAL %s SECOND)""",
                (username, LOGIN_TIME_WINDOW)
            )
            result = cursor.fetchone()
            return result['count'] if result else 0


def is_account_locked(username):
    """
    检查账户是否被锁定

    参数:
        username: 用户名

    返回:
        tuple: (是否锁定, 剩余解锁时间秒数)
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT locked_until FROM users
                   WHERE username = %s AND locked_until > NOW()""",
                (username,)
            )
            result = cursor.fetchone()
            if result:
                cursor.execute(
                    """SELECT TIMESTAMPDIFF(SECOND, NOW(), %s) as remaining""",
                    (result['locked_until'],)
                )
                remaining = cursor.fetchone()
                return True, remaining['remaining'] if remaining else LOCKOUT_DURATION
            return False, 0


def lock_account(username, duration=LOCKOUT_DURATION):
    """
    锁定账户

    参数:
        username: 用户名
        duration: 锁定时长（秒）
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """UPDATE users SET locked_until = DATE_ADD(NOW(), INTERVAL %s SECOND)
                   WHERE username = %s""",
                (duration, username)
            )
            logger.warning(f"账户 {username} 已被锁定 {duration} 秒")


def unlock_expired_accounts():
    """解锁已过期的锁定账户"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """UPDATE users SET locked_until = NULL
                   WHERE locked_until IS NOT NULL AND locked_until <= NOW()"""
            )


def check_ip_login_attempts(ip_address):
    """
    检查IP的登录尝试次数

    参数:
        ip_address: 客户端IP地址

    返回:
        bool: 是否超过限制
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT COUNT(*) as count FROM login_attempts
                   WHERE ip_address = %s AND success = 0
                   AND attempt_time > DATE_SUB(NOW(), INTERVAL %s SECOND)""",
                (ip_address, LOGIN_TIME_WINDOW * 3)
            )
            result = cursor.fetchone()
            return (result['count'] if result else 0) >= MAX_LOGIN_ATTEMPTS * 3


def get_client_ip():
    """获取客户端真实IP地址"""
    if request.headers.get('X-Forwarded-For'):
        xff = request.headers.get('X-Forwarded-For')
        if xff:
            return xff.split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        xri = request.headers.get('X-Real-IP')
        if xri:
            return xri
    return request.remote_addr or '127.0.0.1'


def handle_login_attempt(username, success):
    """
    处理登录尝试

    参数:
        username: 用户名
        success: 是否成功

    返回:
        tuple: (是否允许继续, 错误消息)
    """
    ip_address = get_client_ip()
    
    if not success:
        record_login_attempt(username, False, ip_address)
        
        if check_ip_login_attempts(ip_address):
            return False, "登录尝试过于频繁，请稍后再试"
        
        attempts = get_recent_login_attempts(username)
        
        if attempts >= MAX_LOGIN_ATTEMPTS:
            lock_account(username)
            return False, f"登录失败次数过多，账户已被锁定，请在{ LOCKOUT_DURATION // 60 }分钟后重试"
        
        remaining = MAX_LOGIN_ATTEMPTS - attempts
        return False, f"用户名或密码错误，还剩{remaining}次尝试机会"
    else:
        record_login_attempt(username, True, ip_address)
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """UPDATE users SET failed_login_attempts = 0, locked_until = NULL
                       WHERE username = %s""",
                    (username,)
                )
        
        return True, None

"""
认证路由模块

功能：
- 用户登录（需输入算术验证码）
- 用户注册
- 用户登出
- 获取当前用户信息
- 检查登录状态
- 生成算术验证码
"""
import random
import time
from flask import Blueprint, request, jsonify, session
from webapp.utils.auth import (
    create_user, get_user_by_username, get_user_by_id,
    verify_password
)
from webapp.utils.security import validate_username, validate_password
from webapp.utils.stats import record_visit
from webapp.utils.login_security import handle_login_attempt, is_account_locked, get_client_ip
from webapp.utils.operation_log import log_operation

auth_bp = Blueprint('auth', __name__)


def generate_captcha():
    """生成算术验证码"""
    operators = ['+', '-', '*']
    op = random.choice(operators)
    
    if op == '+':
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        answer = a + b
        expression = f"{a} + {b} = ?"
    elif op == '-':
        a = random.randint(10, 30)
        b = random.randint(1, a)
        answer = a - b
        expression = f"{a} - {b} = ?"
    else:
        a = random.randint(2, 9)
        b = random.randint(2, 9)
        answer = a * b
        expression = f"{a} × {b} = ?"
    
    return expression, str(answer)


@auth_bp.route('/api/auth/captcha', methods=['GET'])
def get_captcha():
    """获取算术验证码"""
    expression, answer = generate_captcha()
    session['captcha_answer'] = answer
    session['captcha_ts'] = int(__import__('time').time())
    return jsonify({'code': 200, 'data': {'expression': expression}})


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.json if request.json else {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    captcha = data.get('captcha', '').strip()

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400

    valid, msg = validate_username(username)
    if not valid:
        return jsonify({'code': 400, 'message': msg}), 400

    if not captcha:
        return jsonify({'code': 400, 'message': '请输入验证码'}), 400

    stored_answer = session.get('captcha_answer')
    if not stored_answer:
        return jsonify({'code': 400, 'message': '验证码已过期，请刷新后重试'}), 400

    if captcha != stored_answer:
        return jsonify({'code': 400, 'message': '验证码错误'}), 400

    import time
    captcha_ts = session.get('captcha_ts', 0)
    if time.time() - captcha_ts > 300:
        return jsonify({'code': 400, 'message': '验证码已过期，请刷新后重试'}), 400

    session.pop('captcha_answer', None)
    session.pop('captcha_ts', None)

    locked, remaining = is_account_locked(username)
    if locked:
        minutes = remaining // 60
        seconds = remaining % 60
        if minutes > 0:
            return jsonify({'code': 403, 'message': f'账户已被锁定，请{minutes}分{seconds}秒后再试'}), 403
        else:
            return jsonify({'code': 403, 'message': f'账户已被锁定，请{seconds}秒后再试'}), 403

    user = get_user_by_username(username)
    if not user:
        handle_login_attempt(username, False)
        log_operation('login_failed', {'username': username, 'reason': 'user_not_found'}, None, username)
        return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401

    if not verify_password(password, user['password_hash']):
        handle_login_attempt(username, False)
        log_operation('login_failed', {'username': username, 'reason': 'wrong_password'}, None, username)
        return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401

    allowed, msg = handle_login_attempt(username, True)
    if not allowed:
        return jsonify({'code': 403, 'message': msg}), 403

    session['user_id'] = user['id']
    session['user'] = {
        'id': user['id'],
        'username': user['username'],
        'role': user['role']
    }
    session['last_activity'] = int(time.time())

    from webapp.utils.operation_log import log_operation
    from webapp.utils.login_security import get_client_ip
    log_operation('login_success', {'username': username}, user['id'], user['username'])

    return jsonify({
        'code': 200,
        'message': '登录成功',
        'data': {
            'id': user['id'],
            'username': user['username'],
            'role': user['role']
        }
    })


@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """用户登出"""
    user_id = session.get('user_id')
    username = session.get('user', {}).get('username', 'unknown')
    log_operation('logout', {'username': username}, user_id, username)
    session.clear()
    return jsonify({'code': 200, 'message': '登出成功'})


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.json if request.json else {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400

    # 验证用户名
    valid, msg = validate_username(username)
    if not valid:
        return jsonify({'code': 400, 'message': msg}), 400

    # 验证密码
    valid, msg = validate_password(password)
    if not valid:
        return jsonify({'code': 400, 'message': msg}), 400

    # 检查用户名是否已存在
    if get_user_by_username(username):
        return jsonify({'code': 400, 'message': '用户名已存在'}), 400

    # 创建用户
    user_id = create_user(username, password, 'user')

    # 自动登录
    session['user_id'] = user_id
    session['user'] = {
        'id': user_id,
        'username': username,
        'role': 'user'
    }

    return jsonify({
        'code': 200,
        'message': '注册成功',
        'data': {
            'id': user_id,
            'username': username,
            'role': 'user'
        }
    })


@auth_bp.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """获取当前登录用户信息"""
    user = session.get('user')
    if not user:
        return jsonify({'code': 401, 'message': '未登录'}), 401

    return jsonify({'code': 200, 'data': user})


@auth_bp.route('/api/auth/check', methods=['GET'])
def check_auth():
    """检查登录状态"""
    user = session.get('user')
    if user:
        return jsonify({'code': 200, 'logged_in': True, 'user': user})
    return jsonify({'code': 200, 'logged_in': False})

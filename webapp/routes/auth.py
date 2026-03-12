"""
认证路由模块
"""
from flask import Blueprint, request, jsonify, session
from webapp.utils.auth import (
    create_user, get_user_by_username, get_user_by_id,
    verify_password
)
from webapp.utils.security import validate_username, validate_password
from webapp.utils.stats import record_visit

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.json if request.json else {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400

    # 验证用户名格式
    valid, msg = validate_username(username)
    if not valid:
        return jsonify({'code': 400, 'message': msg}), 400

    # 获取用户
    user = get_user_by_username(username)
    if not user:
        return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401

    # 验证密码
    if not verify_password(password, user['password_hash']):
        return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401

    # 创建会话
    session['user_id'] = user['id']
    session['user'] = {
        'id': user['id'],
        'username': user['username'],
        'role': user['role']
    }

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

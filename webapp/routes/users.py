"""
用户管理路由模块
"""
from flask import Blueprint, request, jsonify, session
from app.utils.auth import (
    create_user, get_all_users, get_user_by_id,
    delete_user, get_user_by_username
)
from app.utils.security import validate_username, validate_password

users_bp = Blueprint('users', __name__)


def require_admin():
    """检查是否是管理员"""
    user = session.get('user')
    if not user:
        return False, jsonify({'code': 401, 'message': '请先登录'}), 401
    if user.get('role') != 'admin':
        return False, jsonify({'code': 403, 'message': '权限不足'}), 403
    return True, None, None


@users_bp.route('/api/users', methods=['GET'])
def get_users():
    """获取用户列表"""
    # 检查管理员权限
    ok, error_resp, status = require_admin()
    if not ok:
        return error_resp, status

    users = get_all_users()
    return jsonify({'code': 200, 'data': users})


@users_bp.route('/api/users', methods=['POST'])
def create_new_user():
    """创建新用户（管理员操作）"""
    # 检查管理员权限
    ok, error_resp, status = require_admin()
    if not ok:
        return error_resp, status

    data = request.json if request.json else {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'user')

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

    # 验证角色
    if role not in ('user', 'admin'):
        return jsonify({'code': 400, 'message': '无效的角色'}), 400

    # 检查用户名是否已存在
    if get_user_by_username(username):
        return jsonify({'code': 400, 'message': '用户名已存在'}), 400

    # 创建用户
    user_id = create_user(username, password, role)

    return jsonify({
        'code': 200,
        'message': '创建成功',
        'data': {'id': user_id, 'username': username, 'role': role}
    })


@users_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user_by_id(user_id):
    """删除用户（管理员操作）"""
    # 检查管理员权限
    ok, error_resp, status = require_admin()
    if not ok:
        return error_resp, status

    # 不能删除自己
    current_user = session.get('user')
    if user_id == current_user.get('id'):
        return jsonify({'code': 400, 'message': '不能删除自己的账号'}), 400

    # 获取用户信息确认
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404

    # 不能删除管理员
    if user.get('role') == 'admin':
        return jsonify({'code': 400, 'message': '不能删除管理员账号'}), 400

    # 删除用户
    if delete_user(user_id):
        return jsonify({'code': 200, 'message': '删除成功'})
    else:
        return jsonify({'code': 500, 'message': '删除失败'}), 500

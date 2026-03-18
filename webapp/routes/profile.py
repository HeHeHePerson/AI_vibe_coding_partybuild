"""
用户资料路由模块

功能：
- 获取当前用户资料
- 更新用户资料
- 上传用户头像
- 修改密码
"""
import os
import time
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from database import get_db
from webapp.utils.security import validate_username, validate_password
from webapp.utils.operation_log import log_operation

profile_bp = Blueprint('profile', __name__)

ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_avatar_file(filename):
    """检查是否为允许的头像文件类型"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_AVATAR_EXTENSIONS


@profile_bp.route('/api/profile', methods=['GET'])
def get_profile():
    """获取当前用户资料"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '请先登录'}), 401

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT id, username, role, avatar, bio, email, phone, created_at, last_login_at
                   FROM users WHERE id = %s""",
                (user_id,)
            )
            user = cursor.fetchone()

            if not user:
                return jsonify({'code': 404, 'message': '用户不存在'}), 404

            return jsonify({'code': 200, 'data': user})


@profile_bp.route('/api/profile', methods=['PUT'])
def update_profile():
    """更新用户资料"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '请先登录'}), 401

    data = request.json if request.json else {}
    bio = data.get('bio', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()

    if bio and len(bio) > 500:
        return jsonify({'code': 400, 'message': '个人简介不能超过500个字符'}), 400

    if email:
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'code': 400, 'message': '邮箱格式不正确'}), 400

    if phone:
        import re
        if not re.match(r'^1[3-9]\d{9}$', phone):
            return jsonify({'code': 400, 'message': '手机号格式不正确'}), 400

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """UPDATE users SET bio = %s, email = %s, phone = %s WHERE id = %s""",
                (bio, email, phone, user_id)
            )

    log_operation('update_profile', {'bio': bool(bio), 'email': bool(email), 'phone': bool(phone)})

    return jsonify({'code': 200, 'message': '资料更新成功'})


@profile_bp.route('/api/profile/avatar', methods=['POST'])
def upload_avatar():
    """上传用户头像"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '请先登录'}), 401

    if 'avatar' not in request.files:
        return jsonify({'code': 400, 'message': '请选择头像文件'}), 400

    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'code': 400, 'message': '请选择头像文件'}), 400

    if not allowed_avatar_file(file.filename):
        return jsonify({'code': 400, 'message': '不支持的图片格式，请上传 png、jpg、jpeg、gif 或 webp 格式'}), 400

    filename = secure_filename(file.filename)
    timestamp = int(time.time())
    filename = f"avatar_{user_id}_{timestamp}.{filename.rsplit('.', 1)[1].lower()}"
    
    avatar_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
    os.makedirs(avatar_folder, exist_ok=True)
    filepath = os.path.join(avatar_folder, filename)

    file.save(filepath)

    avatar_url = f'/uploads/avatars/{filename}'

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET avatar = %s WHERE id = %s",
                (avatar_url, user_id)
            )

    log_operation('upload_avatar', {'filename': filename})

    return jsonify({
        'code': 200,
        'message': '头像上传成功',
        'data': {'avatar': avatar_url}
    })


@profile_bp.route('/api/profile/password', methods=['PUT'])
def change_password():
    """修改密码"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '请先登录'}), 401

    data = request.json if request.json else {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return jsonify({'code': 400, 'message': '请填写完整'}), 400

    valid, msg = validate_password(new_password)
    if not valid:
        return jsonify({'code': 400, 'message': msg}), 400

    from webapp.utils.auth import verify_password, hash_password

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                return jsonify({'code': 404, 'message': '用户不存在'}), 404

            if not verify_password(old_password, user['password_hash']):
                return jsonify({'code': 400, 'message': '原密码错误'}), 400

            new_hash = hash_password(new_password)
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (new_hash, user_id)
            )

    log_operation('change_password')

    return jsonify({'code': 200, 'message': '密码修改成功'})

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
import struct
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from database import get_db
from webapp.utils.security import validate_username, validate_password
from webapp.utils.operation_log import log_operation

profile_bp = Blueprint('profile', __name__)

ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_AVATAR_MIME_TYPES = {
    'png': ['image/png'],
    'jpg': ['image/jpeg', 'image/jpg'],
    'jpeg': ['image/jpeg'],
    'gif': ['image/gif'],
    'webp': ['image/webp']
}
MAGIC_NUMBERS = {
    'png': b'\x89PNG\r\n\x1a\n',
    'jpg': b'\xff\xd8\xff',
    'jpeg': b'\xff\xd8\xff',
    'gif': b'GIF87a',
    'gif89a': b'GIF89a',
    'webp': b'RIFF'
}
MAX_AVATAR_SIZE = 2 * 1024 * 1024
MAX_AVATAR_DIMENSION = 1024


def get_file_extension(filename):
    """安全获取文件扩展名"""
    if '.' not in filename:
        return None
    return filename.rsplit('.', 1)[1].lower()


def allowed_avatar_file(filename):
    """检查是否为允许的头像文件类型（仅检查扩展名）"""
    ext = get_file_extension(filename)
    return ext in ALLOWED_AVATAR_EXTENSIONS if ext else False


def verify_image_magic_number(file_stream):
    """通过读取文件头部魔术数字验证图片真实格式"""
    file_stream.seek(0)
    header = file_stream.read(16)
    file_stream.seek(0)

    if header.startswith(MAGIC_NUMBERS['png']):
        return 'png'
    elif header.startswith(MAGIC_NUMBERS['jpg']) or header.startswith(MAGIC_NUMBERS['jpeg']):
        return 'jpg'
    elif header.startswith(MAGIC_NUMBERS['gif87a']) or header.startswith(MAGIC_NUMBERS['gif89a']):
        return 'gif'
    elif header.startswith(MAGIC_NUMBERS['webp']):
        file_stream.seek(0)
        riff = file_stream.read(12)
        if len(riff) >= 12 and riff[8:12] == b'WEBP':
            return 'webp'
    return None


def verify_image_dimensions(filepath, max_dimension):
    """验证图片尺寸不超过限制"""
    try:
        with open(filepath, 'rb') as f:
            header = f.read(16)
            f.seek(0)

            width, height = 0, 0

            if header.startswith(MAGIC_NUMBERS['png']):
                f.seek(16)
                width = struct.unpack('>I', f.read(4))[0]
                height = struct.unpack('>I', f.read(4))[0]
            elif header.startswith(MAGIC_NUMBERS['jpg']) or header.startswith(MAGIC_NUMBERS['jpeg']):
                f.seek(0)
                while True:
                    marker = f.read(2)
                    if marker != b'\xff':
                        break
                    length = struct.unpack('>H', f.read(2))[0]
                    if marker in (b'\xc0', b'\xc2'):
                        f.read(1)
                        height = struct.unpack('>H', f.read(2))[0]
                        width = struct.unpack('>H', f.read(2))[0]
                        break
                    f.seek(length - 2, 1)
            elif header.startswith(MAGIC_NUMBERS['gif87a']) or header.startswith(MAGIC_NUMBERS['gif89a']):
                width = struct.unpack('<H', f.read(2))[0]
                height = struct.unpack('<H', f.read(2))[0]
            else:
                return True

            if width > max_dimension or height > max_dimension:
                return False
            return True
    except Exception:
        return False


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
    """上传用户头像

    安全检查：
    - 文件扩展名验证
    - MIME 类型验证
    - Magic Number (文件头) 验证
    - 文件大小限制 (2MB)
    - 图片尺寸限制 (1024x1024)
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '请先登录'}), 401

    if 'avatar' not in request.files:
        return jsonify({'code': 400, 'message': '请选择头像文件'}), 400

    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'code': 400, 'message': '请选择头像文件'}), 400

    ext = get_file_extension(file.filename)
    if not ext or ext not in ALLOWED_AVATAR_EXTENSIONS:
        return jsonify({'code': 400, 'message': '不支持的图片格式，请上传 png、jpg、jpeg、gif 或 webp 格式'}), 400

    content = file.read()
    file.seek(0)

    if len(content) > MAX_AVATAR_SIZE:
        return jsonify({'code': 400, 'message': '图片文件大小不能超过 2MB'}), 400

    if len(content) < 16:
        return jsonify({'code': 400, 'message': '文件损坏或不是有效的图片文件'}), 400

    import io
    file_stream = io.BytesIO(content)
    magic_ext = verify_image_magic_number(file_stream)
    if not magic_ext or magic_ext != ext:
        return jsonify({'code': 400, 'message': '文件类型与扩展名不匹配或文件已损坏'}), 400

    mime_type = file.content_type if file.content_type else ''
    allowed_mimes = ALLOWED_AVATAR_MIME_TYPES.get(ext, [])
    if mime_type and mime_type not in allowed_mimes:
        return jsonify({'code': 400, 'message': '不支持的图片 MIME 类型'}), 400

    timestamp = int(time.time())
    filename = f"avatar_{user_id}_{timestamp}.{ext}"

    avatar_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
    os.makedirs(avatar_folder, exist_ok=True)
    filepath = os.path.join(avatar_folder, filename)

    try:
        file.save(filepath)

        if not verify_image_dimensions(filepath, MAX_AVATAR_DIMENSION):
            os.remove(filepath)
            return jsonify({'code': 400, 'message': f'图片尺寸不能超过 {MAX_AVATAR_DIMENSION}x{MAX_AVATAR_DIMENSION} 像素'}), 400

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
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'code': 500, 'message': '头像上传失败'}), 500


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


@profile_bp.route('/api/users/<int:user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    """获取指定用户的公开资料（任意登录用户可查看）"""
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({'code': 401, 'message': '请先登录'}), 401

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT id, username, avatar, bio, created_at
                   FROM users WHERE id = %s""",
                (user_id,)
            )
            user = cursor.fetchone()

            if not user:
                return jsonify({'code': 404, 'message': '用户不存在'}), 404

            return jsonify({'code': 200, 'data': user})

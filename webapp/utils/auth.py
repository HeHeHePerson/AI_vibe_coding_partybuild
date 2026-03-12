"""
认证工具模块
"""
import bcrypt
from database import get_db


def hash_password(password):
    """对密码进行bcrypt加密"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password, password_hash):
    """验证密码是否正确"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def create_user(username, password, role='user'):
    """创建新用户"""
    password_hash = hash_password(password)
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (username, password_hash, role)
            )
            return cursor.lastrowid


def get_user_by_username(username):
    """根据用户名获取用户"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            return cursor.fetchone()


def get_user_by_id(user_id):
    """根据用户ID获取用户"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, role, DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') as created_at FROM users WHERE id = %s", (user_id,))
            return cursor.fetchone()


def get_all_users():
    """获取所有用户列表"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, role, DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') as created_at FROM users ORDER BY created_at DESC")
            return cursor.fetchall()


def delete_user(user_id):
    """删除用户"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s AND role = 'user'", (user_id,))
            return cursor.rowcount > 0


def update_user_password(user_id, new_password):
    """更新用户密码"""
    password_hash = hash_password(new_password)
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (password_hash, user_id)
            )
            return cursor.rowcount > 0

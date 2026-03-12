"""
公告管理路由模块
"""
from flask import Blueprint, request, jsonify, session
from database import get_db
from webapp.utils.security import escape_html

notices_bp = Blueprint('notices', __name__)


@notices_bp.route('/api/notices', methods=['GET'])
def get_notices():
    """获取公告列表"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT n.id, n.title, n.content, n.created_at,
                       u.username as author_name
                FROM notices n
                JOIN users u ON n.author_id = u.id
                ORDER BY n.created_at DESC
            """)
            notices = cursor.fetchall()

            # 转义HTML
            for notice in notices:
                notice['title'] = escape_html(notice['title'])

            return jsonify({'code': 200, 'data': notices})


@notices_bp.route('/api/notices/<int:notice_id>', methods=['GET'])
def get_notice(notice_id):
    """获取公告详情"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT n.id, n.title, n.content, n.created_at,
                       u.username as author_name
                FROM notices n
                JOIN users u ON n.author_id = u.id
                WHERE n.id = %s
            """, (notice_id,))
            notice = cursor.fetchone()

            if not notice:
                return jsonify({'code': 404, 'message': '公告不存在'}), 404

            # 转义HTML
            notice['title'] = escape_html(notice['title'])
            notice['content'] = escape_html(notice['content'])

            return jsonify({'code': 200, 'data': notice})


@notices_bp.route('/api/notices', methods=['POST'])
def create_notice():
    """创建公告"""
    # 检查登录
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '请先登录'}), 401

    # 检查是否是管理员
    user_info = session.get('user')
    if not user_info or user_info.get('role') != 'admin':
        return jsonify({'code': 403, 'message': '权限不足，只有管理员可以发布公告'}), 403

    # 获取数据
    title = request.json.get('title', '').strip() if request.json else ''
    content = request.json.get('content', '').strip() if request.json else ''

    # 验证
    if not title:
        return jsonify({'code': 400, 'message': '标题不能为空'}), 400

    if not content:
        return jsonify({'code': 400, 'message': '内容不能为空'}), 400

    if len(title) > 200:
        return jsonify({'code': 400, 'message': '标题不能超过200个字符'}), 400

    if len(content) > 5000:
        return jsonify({'code': 400, 'message': '内容不能超过5000个字符'}), 400

    # 保存到数据库
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO notices (title, content, author_id) VALUES (%s, %s, %s)",
                (title, content, user_id)
            )
            notice_id = cursor.lastrowid

    return jsonify({'code': 200, 'message': '公告发布成功', 'data': {'id': notice_id}})


@notices_bp.route('/api/notices/<int:notice_id>', methods=['DELETE'])
def delete_notice(notice_id):
    """删除公告"""
    # 检查登录
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '请先登录'}), 401

    # 检查是否是管理员
    user_info = session.get('user')
    if not user_info or user_info.get('role') != 'admin':
        return jsonify({'code': 403, 'message': '权限不足'}), 403

    # 获取公告信息
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM notices WHERE id = %s", (notice_id,))
            notice = cursor.fetchone()

            if not notice:
                return jsonify({'code': 404, 'message': '公告不存在'}), 404

            cursor.execute("DELETE FROM notices WHERE id = %s", (notice_id,))

    return jsonify({'code': 200, 'message': '删除成功'})

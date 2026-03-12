"""
内容管理路由模块
"""
import json
import os
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from database import get_db
from webapp.utils.security import escape_html, validate_title, validate_content

contents_bp = Blueprint('contents', __name__)


def allowed_file(filename):
    """检查文件类型是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@contents_bp.route('/api/contents', methods=['GET'])
def get_contents():
    """获取内容列表"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.title, c.images, c.created_at, u.username as author_name
                FROM contents c
                JOIN users u ON c.author_id = u.id
                ORDER BY c.created_at DESC
            """)
            contents = cursor.fetchall()

            # 处理图片JSON
            for content in contents:
                if content['images']:
                    if isinstance(content['images'], str):
                        content['images'] = json.loads(content['images'])
                else:
                    content['images'] = []

                # 转义HTML
                content['title'] = escape_html(content['title'])

            return jsonify({'code': 200, 'data': contents})


@contents_bp.route('/api/contents/<int:content_id>', methods=['GET'])
def get_content(content_id):
    """获取内容详情"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.*, u.username as author_name
                FROM contents c
                JOIN users u ON c.author_id = u.id
                WHERE c.id = %s
            """, (content_id,))
            content = cursor.fetchone()

            if not content:
                return jsonify({'code': 404, 'message': '内容不存在'}), 404

            # 处理图片JSON
            if content['images']:
                if isinstance(content['images'], str):
                    content['images'] = json.loads(content['images'])
            else:
                content['images'] = []

            # 获取评论
            cursor.execute("""
                SELECT cm.*, u.username as user_name
                FROM comments cm
                JOIN users u ON cm.user_id = u.id
                WHERE cm.content_id = %s
                ORDER BY cm.created_at DESC
            """, (content_id,))
            comments = cursor.fetchall()

            # 获取点赞数
            cursor.execute(
                "SELECT COUNT(*) as count FROM likes WHERE content_id = %s",
                (content_id,)
            )
            like_result = cursor.fetchone()
            like_count = like_result['count'] if like_result else 0

            # 检查当前用户是否已点赞
            user_liked = False
            user_id = session.get('user_id')
            if user_id:
                from webapp.utils.stats import check_user_liked_today
                user_liked = check_user_liked_today(content_id, user_id)

            # 转义HTML
            content['title'] = escape_html(content['title'])
            content['body'] = escape_html(content['body'])

            return jsonify({
                'code': 200,
                'data': {
                    'content': content,
                    'comments': comments,
                    'like_count': like_count,
                    'user_liked': user_liked
                }
            })


@contents_bp.route('/api/contents', methods=['POST'])
def create_content():
    """创建内容"""
    # 检查登录
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '请先登录'}), 401

    # 获取表单数据
    title = request.form.get('title', '').strip()
    body = request.form.get('body', '').strip()

    # 验证
    valid, msg = validate_title(title)
    if not valid:
        return jsonify({'code': 400, 'message': msg}), 400

    valid, msg = validate_content(body)
    if not valid:
        return jsonify({'code': 400, 'message': msg}), 400

    # 处理上传的图片
    images = []
    if 'images' in request.files:
        files = request.files.getlist('images')
        upload_folder = current_app.config['UPLOAD_FOLDER']

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # 添加时间戳避免文件名冲突
                import time
                timestamp = int(time.time())
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                images.append(f'/uploads/{filename}')

    # 保存到数据库
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO contents (title, body, images, author_id) VALUES (%s, %s, %s, %s)",
                (title, body, json.dumps(images), user_id)
            )
            content_id = cursor.lastrowid

    return jsonify({'code': 200, 'message': '创建成功', 'data': {'id': content_id}})


@contents_bp.route('/api/contents/<int:content_id>', methods=['DELETE'])
def delete_content(content_id):
    """删除内容"""
    # 检查登录
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '请先登录'}), 401

    # 获取内容信息
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT author_id FROM contents WHERE id = %s", (content_id,))
            content = cursor.fetchone()

            if not content:
                return jsonify({'code': 404, 'message': '内容不存在'}), 404

            # 检查权限：只能删除自己的内容
            user_info = session.get('user')
            if content['author_id'] != user_id and user_info.get('role') != 'admin':
                return jsonify({'code': 403, 'message': '权限不足'}), 403

            # 删除内容（连同评论和点赞一起删除）
            cursor.execute("DELETE FROM contents WHERE id = %s", (content_id,))

    return jsonify({'code': 200, 'message': '删除成功'})


# 评论路由
@contents_bp.route('/api/contents/<int:content_id>/comments', methods=['GET'])
def get_comments(content_id):
    """获取内容的评论"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT cm.*, u.username as user_name
                FROM comments cm
                JOIN users u ON cm.user_id = u.id
                WHERE cm.content_id = %s
                ORDER BY cm.created_at DESC
            """, (content_id,))
            comments = cursor.fetchall()
            return jsonify({'code': 200, 'data': comments})


@contents_bp.route('/api/contents/<int:content_id>/comments', methods=['POST'])
def add_comment(content_id):
    """添加评论"""
    # 检查登录
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '请先登录'}), 401

    # 获取评论内容
    body = request.json.get('body', '').strip() if request.json else ''
    if not body:
        return jsonify({'code': 400, 'message': '评论内容不能为空'}), 400

    # 保存评论
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 检查内容是否存在
            cursor.execute("SELECT id FROM contents WHERE id = %s", (content_id,))
            if not cursor.fetchone():
                return jsonify({'code': 404, 'message': '内容不存在'}), 404

            cursor.execute(
                "INSERT INTO comments (content_id, user_id, body) VALUES (%s, %s, %s)",
                (content_id, user_id, body)
            )
            comment_id = cursor.lastrowid

    return jsonify({'code': 200, 'message': '评论成功', 'data': {'id': comment_id}})


@contents_bp.route('/api/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    """删除评论"""
    # 检查登录
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '请先登录'}), 401

    with get_db() as conn:
        with conn.cursor() as cursor:
            # 获取评论信息
            cursor.execute("SELECT user_id FROM comments WHERE id = %s", (comment_id,))
            comment = cursor.fetchone()

            if not comment:
                return jsonify({'code': 404, 'message': '评论不存在'}), 404

            # 检查权限：只能删除自己的评论
            user_info = session.get('user')
            if comment['user_id'] != user_id and user_info.get('role') != 'admin':
                return jsonify({'code': 403, 'message': '权限不足'}), 403

            cursor.execute("DELETE FROM comments WHERE id = %s", (comment_id,))

    return jsonify({'code': 200, 'message': '删除成功'})


# 点赞路由
@contents_bp.route('/api/contents/<int:content_id>/like', methods=['POST'])
def like_content(content_id):
    """点赞内容"""
    # 检查登录
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '请先登录'}), 401

    with get_db() as conn:
        with conn.cursor() as cursor:
            # 检查内容是否存在
            cursor.execute("SELECT id FROM contents WHERE id = %s", (content_id,))
            if not cursor.fetchone():
                return jsonify({'code': 404, 'message': '内容不存在'}), 404

            # 检查今天是否已点赞
            from webapp.utils.stats import check_user_liked_today
            if check_user_liked_today(content_id, user_id):
                return jsonify({'code': 400, 'message': '今天已经点赞过了'}), 400

            # 添加点赞
            from webapp.utils.stats import add_like
            if add_like(content_id, user_id):
                return jsonify({'code': 200, 'message': '点赞成功'})
            else:
                return jsonify({'code': 500, 'message': '点赞失败'}), 500


@contents_bp.route('/api/contents/<int:content_id>/like', methods=['DELETE'])
def unlike_content(content_id):
    """取消点赞"""
    # 检查登录
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '请先登录'}), 401

    from webapp.utils.stats import remove_like
    if remove_like(content_id, user_id):
        return jsonify({'code': 200, 'message': '取消点赞成功'})
    else:
        return jsonify({'code': 400, 'message': '取消点赞失败'}), 400

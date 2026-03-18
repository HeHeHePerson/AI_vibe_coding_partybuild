"""
内容管理路由模块

功能：
- 获取内容列表和详情
- 创建、删除内容
- 评论管理
- 内容点赞和评论点赞
- 文件上传（带安全检查）
"""
import json
import os
import time
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from database import get_db
from webapp.utils.security import escape_html, validate_title, validate_content
from webapp.utils.operation_log import log_operation

contents_bp = Blueprint('contents', __name__)


def allowed_file(filename):
    """
    检查文件类型是否允许

    安全说明：仅允许白名单中的文件扩展名，防止上传恶意文件
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def is_safe_path(base_path, user_path):
    """
    检查文件路径是否在允许的目录内（防止目录穿越攻击）

    参数:
        base_path: 基础目录（上传目录的绝对路径）
        user_path: 用户提供的文件路径

    返回:
        bool: 路径安全返回True，否则返回False

    安全说明：
        使用os.path.realpath解析符号链接和../
        确保最终路径仍然在base_path内
    """
    # 获取绝对路径并解析../
    real_base = os.path.realpath(base_path)
    real_path = os.path.realpath(os.path.join(base_path, user_path))

    # 检查最终路径是否在基础目录内
    return real_path.startswith(real_base)


@contents_bp.route('/api/contents', methods=['GET'])
def get_contents():
    """获取内容列表"""
    keyword = request.args.get('keyword', '').strip()
    category_id = request.args.get('category_id', type=int)
    tag_id = request.args.get('tag_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    per_page = min(per_page, 100)
    offset = (page - 1) * per_page
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            where_conditions = []
            params = []
            
            if keyword:
                where_conditions.append("(c.title LIKE %s OR c.body LIKE %s)")
                params.extend([f'%{keyword}%', f'%{keyword}%'])
            
            if category_id:
                where_conditions.append("c.category_id = %s")
                params.append(category_id)
            
            if tag_id:
                where_conditions.append("EXISTS (SELECT 1 FROM content_tags ct WHERE ct.content_id = c.id AND ct.tag_id = %s)")
                params.append(tag_id)
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            count_sql = f"SELECT COUNT(*) as total FROM contents c WHERE {where_clause}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']
            
            sql = f"""
                SELECT c.id, c.title, c.images, c.category_id,
                       c.created_at as created_at,
                       u.username as author_name
                FROM contents c
                JOIN users u ON c.author_id = u.id
                WHERE {where_clause}
                ORDER BY c.created_at DESC
                LIMIT %s OFFSET %s
            """
            params.extend([per_page, offset])
            cursor.execute(sql, params)
            contents = cursor.fetchall()

            for content in contents:
                if content['images']:
                    if isinstance(content['images'], str):
                        content['images'] = json.loads(content['images'])
                else:
                    content['images'] = []

                content['title'] = escape_html(content['title'])

            return jsonify({
                'code': 200,
                'data': contents,
                'pagination': {
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'pages': (total + per_page - 1) // per_page
                }
            })


@contents_bp.route('/api/contents/<int:content_id>', methods=['GET'])
def get_content(content_id):
    """获取内容详情"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.title, c.body, c.images,
                       c.created_at as created_at,
                       c.author_id as author_id,
                       u.username as author_name
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
                SELECT cm.id, cm.content_id, cm.user_id, cm.body, cm.parent_id,
                       cm.created_at as created_at,
                       u.username as user_name,
                       p.user_id as parent_user_id, pu.username as parent_user_name,
                       p.body as parent_body
                FROM comments cm
                JOIN users u ON cm.user_id = u.id
                LEFT JOIN comments p ON cm.parent_id = p.id
                LEFT JOIN users pu ON p.user_id = pu.id
                WHERE cm.content_id = %s
                ORDER BY cm.created_at DESC
            """, (content_id,))
            comments = cursor.fetchall()

            # 获取每条评论的点赞数和用户是否已点赞
            user_id = session.get('user_id')
            for comment in comments:
                # 评论点赞数
                cursor.execute(
                    "SELECT COUNT(*) as count FROM comment_likes WHERE comment_id = %s",
                    (comment['id'],)
                )
                like_result = cursor.fetchone()
                comment['like_count'] = like_result['count'] if like_result else 0

                # 用户是否已点赞
                comment['user_liked'] = False
                if user_id:
                    from webapp.utils.stats import check_user_comment_liked_today
                    comment['user_liked'] = check_user_comment_liked_today(comment['id'], user_id)

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
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '请先登录'}), 401

    title = request.form.get('title', '').strip()
    body = request.form.get('body', '').strip()
    category_id = request.form.get('category_id', type=int)
    tag_ids = request.form.getlist('tag_ids')

    valid, msg = validate_title(title)
    if not valid:
        return jsonify({'code': 400, 'message': msg}), 400

    valid, msg = validate_content(body)
    if not valid:
        return jsonify({'code': 400, 'message': msg}), 400

    images = []
    if 'images' in request.files:
        files = request.files.getlist('images')
        upload_folder = current_app.config['UPLOAD_FOLDER']

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename) if file.filename else ''
                if not filename:
                    continue
                timestamp = int(time.time())
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(upload_folder, filename)

                if not is_safe_path(upload_folder, filename):
                    continue

                file.save(filepath)
                images.append(f'/uploads/{filename}')

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO contents (title, body, images, author_id, category_id) VALUES (%s, %s, %s, %s, %s)",
                (title, body, json.dumps(images), user_id, category_id)
            )
            content_id = cursor.lastrowid

            if tag_ids:
                for tag_id in tag_ids:
                    try:
                        tag_id = int(tag_id)
                        cursor.execute(
                            "INSERT INTO content_tags (content_id, tag_id) VALUES (%s, %s)",
                            (content_id, tag_id)
                        )
                    except (ValueError, TypeError):
                        pass

    log_operation('create_content', {'content_id': content_id, 'title': title})

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
                SELECT cm.*, u.username as user_name,
                       p.user_id as parent_user_id, pu.username as parent_user_name,
                       p.body as parent_body
                FROM comments cm
                JOIN users u ON cm.user_id = u.id
                LEFT JOIN comments p ON cm.parent_id = p.id
                LEFT JOIN users pu ON p.user_id = pu.id
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

    # 验证评论长度（防止大文本攻击）
    if len(body) > 5000:
        return jsonify({'code': 400, 'message': '评论内容过长，请精简后再提交'}), 400

    # 获取父评论ID（用于回复功能）
    parent_id = request.json.get('parent_id') if request.json else None
    # 验证parent_id有效性
    if parent_id:
        with get_db() as conn:
            with conn.cursor() as cursor:
                # 检查父评论是否存在且属于同一内容
                cursor.execute(
                    "SELECT id, content_id FROM comments WHERE id = %s",
                    (parent_id,)
                )
                parent_comment = cursor.fetchone()
                if not parent_comment:
                    return jsonify({'code': 400, 'message': '回复的评论不存在'}), 400
                if parent_comment['content_id'] != content_id:
                    return jsonify({'code': 400, 'message': '不能回复其他内容的评论'}), 400

    # 保存评论
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 检查内容是否存在
            cursor.execute("SELECT id FROM contents WHERE id = %s", (content_id,))
            if not cursor.fetchone():
                return jsonify({'code': 404, 'message': '内容不存在'}), 404

            cursor.execute(
                "INSERT INTO comments (content_id, user_id, body, parent_id) VALUES (%s, %s, %s, %s)",
                (content_id, user_id, body, parent_id)
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


# 评论点赞路由
@contents_bp.route('/api/comments/<int:comment_id>/like', methods=['POST'])
def like_comment(comment_id):
    """点赞评论"""
    # 检查登录
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '请先登录'}), 401

    with get_db() as conn:
        with conn.cursor() as cursor:
            # 检查评论是否存在
            cursor.execute("SELECT id FROM comments WHERE id = %s", (comment_id,))
            if not cursor.fetchone():
                return jsonify({'code': 404, 'message': '评论不存在'}), 404

            # 检查今天是否已点赞
            from webapp.utils.stats import check_user_comment_liked_today
            if check_user_comment_liked_today(comment_id, user_id):
                return jsonify({'code': 400, 'message': '今天已经点赞过了'}), 400

            # 添加点赞
            from webapp.utils.stats import add_comment_like
            if add_comment_like(comment_id, user_id):
                return jsonify({'code': 200, 'message': '点赞成功'})
            else:
                return jsonify({'code': 500, 'message': '点赞失败'}), 500


@contents_bp.route('/api/comments/<int:comment_id>/like', methods=['DELETE'])
def unlike_comment(comment_id):
    """取消点赞评论"""
    # 检查登录
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '请先登录'}), 401

    from webapp.utils.stats import remove_comment_like
    if remove_comment_like(comment_id, user_id):
        return jsonify({'code': 200, 'message': '取消点赞成功'})
    else:
        return jsonify({'code': 400, 'message': '取消点赞失败'}), 400

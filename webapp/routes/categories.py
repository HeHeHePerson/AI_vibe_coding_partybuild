"""
分类和标签管理路由模块

功能：
- 分类管理（增删改查）
- 标签管理（增删改查）
- 内容分类/标签设置
"""
from flask import Blueprint, request, jsonify, session
from database import get_db
from webapp.utils.security import escape_html
from webapp.utils.operation_log import log_operation

categories_bp = Blueprint('categories', __name__)


def require_admin():
    """检查是否是管理员"""
    user = session.get('user')
    if not user:
        return False, jsonify({'code': 401, 'message': '请先登录'}), 401
    if user.get('role') != 'admin':
        return False, jsonify({'code': 403, 'message': '权限不足'}), 403
    return True, None, None


@categories_bp.route('/api/categories', methods=['GET'])
def get_categories():
    """获取分类列表"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.name, c.description, c.sort_order,
                       (SELECT COUNT(*) FROM contents WHERE category_id = c.id) as content_count,
                       c.created_at
                FROM categories c
                ORDER BY c.sort_order ASC, c.id ASC
            """)
            categories = cursor.fetchall()
            return jsonify({'code': 200, 'data': categories})


@categories_bp.route('/api/categories', methods=['POST'])
def create_category():
    """创建分类"""
    ok, error_resp, status = require_admin()
    if not ok:
        return error_resp, status

    data = request.json if request.json else {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    sort_order = data.get('sort_order', 0)

    if not name:
        return jsonify({'code': 400, 'message': '分类名称不能为空'}), 400

    if len(name) > 50:
        return jsonify({'code': 400, 'message': '分类名称不能超过50个字符'}), 400

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name, description, sort_order) VALUES (%s, %s, %s)",
                (name, description, sort_order)
            )
            category_id = cursor.lastrowid

    log_operation('create_category', {'name': name})

    return jsonify({'code': 200, 'message': '创建成功', 'data': {'id': category_id}})


@categories_bp.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """更新分类"""
    ok, error_resp, status = require_admin()
    if not ok:
        return error_resp, status

    data = request.json if request.json else {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    sort_order = data.get('sort_order', 0)

    if not name:
        return jsonify({'code': 400, 'message': '分类名称不能为空'}), 400

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE categories SET name = %s, description = %s, sort_order = %s WHERE id = %s",
                (name, description, sort_order, category_id)
            )

    log_operation('update_category', {'category_id': category_id, 'name': name})

    return jsonify({'code': 200, 'message': '更新成功'})


@categories_bp.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """删除分类"""
    ok, error_resp, status = require_admin()
    if not ok:
        return error_resp, status

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM categories WHERE id = %s", (category_id,))
            if not cursor.fetchone():
                return jsonify({'code': 404, 'message': '分类不存在'}), 404

            cursor.execute("SELECT COUNT(*) as count FROM contents WHERE category_id = %s", (category_id,))
            if cursor.fetchone()['count'] > 0:
                return jsonify({'code': 400, 'message': '该分类下存在内容，无法删除'}), 400

            cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))

    log_operation('delete_category', {'category_id': category_id})

    return jsonify({'code': 200, 'message': '删除成功'})


@categories_bp.route('/api/tags', methods=['GET'])
def get_tags():
    """获取标签列表"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT t.id, t.name, t.color,
                       (SELECT COUNT(*) FROM content_tags WHERE tag_id = t.id) as content_count,
                       t.created_at
                FROM tags t
                ORDER BY t.id ASC
            """)
            tags = cursor.fetchall()
            return jsonify({'code': 200, 'data': tags})


@categories_bp.route('/api/tags', methods=['POST'])
def create_tag():
    """创建标签"""
    ok, error_resp, status = require_admin()
    if not ok:
        return error_resp, status

    data = request.json if request.json else {}
    name = data.get('name', '').strip()
    color = data.get('color', '#1890ff').strip()

    if not name:
        return jsonify({'code': 400, 'message': '标签名称不能为空'}), 400

    if len(name) > 20:
        return jsonify({'code': 400, 'message': '标签名称不能超过20个字符'}), 400

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM tags WHERE name = %s", (name,))
            if cursor.fetchone():
                return jsonify({'code': 400, 'message': '标签名称已存在'}), 400

            cursor.execute(
                "INSERT INTO tags (name, color) VALUES (%s, %s)",
                (name, color)
            )
            tag_id = cursor.lastrowid

    log_operation('create_tag', {'name': name})

    return jsonify({'code': 200, 'message': '创建成功', 'data': {'id': tag_id}})


@categories_bp.route('/api/tags/<int:tag_id>', methods=['PUT'])
def update_tag(tag_id):
    """更新标签"""
    ok, error_resp, status = require_admin()
    if not ok:
        return error_resp, status

    data = request.json if request.json else {}
    name = data.get('name', '').strip()
    color = data.get('color', '').strip()

    if not name:
        return jsonify({'code': 400, 'message': '标签名称不能为空'}), 400

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE tags SET name = %s, color = %s WHERE id = %s",
                (name, color, tag_id)
            )

    log_operation('update_tag', {'tag_id': tag_id, 'name': name})

    return jsonify({'code': 200, 'message': '更新成功'})


@categories_bp.route('/api/tags/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    """删除标签"""
    ok, error_resp, status = require_admin()
    if not ok:
        return error_resp, status

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM tags WHERE id = %s", (tag_id,))
            if not cursor.fetchone():
                return jsonify({'code': 404, 'message': '标签不存在'}), 404

            cursor.execute("DELETE FROM content_tags WHERE tag_id = %s", (tag_id,))
            cursor.execute("DELETE FROM tags WHERE id = %s", (tag_id,))

    log_operation('delete_tag', {'tag_id': tag_id})

    return jsonify({'code': 200, 'message': '删除成功'})

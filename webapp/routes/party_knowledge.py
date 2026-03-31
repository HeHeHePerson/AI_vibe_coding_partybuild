"""
党建知识学习模块路由

功能：
- 获取党建知识列表
- 获取党建知识详情
- 创建党建知识（管理员）
- 更新党建知识（管理员）
- 删除党建知识（管理员）
- 记录学习进度
"""
from flask import Blueprint, request, jsonify, session
from database import get_db
from webapp.utils.security import escape_html, validate_title, validate_content
from webapp.utils.operation_log import log_operation

party_knowledge_bp = Blueprint('party_knowledge', __name__)


@party_knowledge_bp.route('/api/party/knowledge', methods=['GET'])
def get_knowledge_list():
    """获取党建知识列表"""
    category = request.args.get('category', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    offset = (page - 1) * per_page
    is_admin = request.args.get('admin', 'false').lower() == 'true'
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 构建查询条件
            where_conditions = []
            params = []
            
            if not is_admin:
                where_conditions.append("pk.status = 'approved'")
            
            if category:
                where_conditions.append("pk.category = %s")
                params.append(category)
            
            where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # 查询总数
            cursor.execute(f"SELECT COUNT(*) as total FROM party_knowledge pk {where_clause}", params)
            total = cursor.fetchone()['total']
            
            # 查询列表
            cursor.execute(f"""
                SELECT pk.id, pk.title, pk.category, pk.view_count, pk.created_at, pk.status,
                       u.username as author_name
                FROM party_knowledge pk
                LEFT JOIN users u ON pk.author_id = u.id
                {where_clause}
                ORDER BY pk.created_at DESC
                LIMIT %s OFFSET %s
            """, params + [per_page, offset])
            knowledge_list = cursor.fetchall()
    
    return jsonify({
        'code': 200,
        'data': {
            'list': knowledge_list,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
        }
    })


@party_knowledge_bp.route('/api/party/knowledge/<int:knowledge_id>', methods=['GET'])
def get_knowledge_detail(knowledge_id):
    """获取党建知识详情"""
    user_id = session.get('user_id')
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 更新浏览量
            cursor.execute("UPDATE party_knowledge SET view_count = view_count + 1 WHERE id = %s", (knowledge_id,))
            
            # 查询详情
            cursor.execute("""
                SELECT pk.*, u.username as author_name
                FROM party_knowledge pk
                LEFT JOIN users u ON pk.author_id = u.id
                WHERE pk.id = %s
            """, (knowledge_id,))
            knowledge = cursor.fetchone()
            
            if not knowledge:
                return jsonify({'code': 404, 'message': '党建知识不存在'}), 404
            
            # 检查学习记录
            study_record = None
            if user_id:
                cursor.execute("""
                    SELECT study_time, completed
                    FROM party_study_records
                    WHERE user_id = %s AND knowledge_id = %s
                """, (user_id, knowledge_id))
                study_record = cursor.fetchone()
    
    return jsonify({
        'code': 200,
        'data': {
            'knowledge': knowledge,
            'study_record': study_record
        }
    })


@party_knowledge_bp.route('/api/party/knowledge', methods=['POST'])
def create_knowledge():
    """创建党建知识"""
    user = session.get('user')
    if not user:
        return jsonify({'code': 401, 'message': '未登录'}), 401
    
    data = request.json or {}
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    category = data.get('category', '').strip()
    
    # 验证输入
    if not title or not content or not category:
        return jsonify({'code': 400, 'message': '标题、内容和分类不能为空'}), 400
    
    valid, msg = validate_title(title)
    if not valid:
        return jsonify({'code': 400, 'message': msg}), 400
    
    valid, msg = validate_content(content)
    if not valid:
        return jsonify({'code': 400, 'message': msg}), 400
    
    # 转义HTML
    title = escape_html(title)
    content = escape_html(content)
    category = escape_html(category)
    
    # 确定审核状态
    status = 'approved' if user.get('role') == 'admin' else 'pending'
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO party_knowledge (title, content, category, author_id, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (title, content, category, user['id'], status))
            knowledge_id = cursor.lastrowid
    
    log_operation('create_knowledge', {'title': title, 'category': category}, user['id'], user['username'])
    
    return jsonify({
        'code': 200,
        'message': '创建成功',
        'data': {'id': knowledge_id}
    })


@party_knowledge_bp.route('/api/party/knowledge/<int:knowledge_id>', methods=['PUT'])
def update_knowledge(knowledge_id):
    """更新党建知识（管理员）"""
    user = session.get('user')
    if not user or user.get('role') != 'admin':
        return jsonify({'code': 403, 'message': '权限不足'}), 403
    
    data = request.json or {}
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    category = data.get('category', '').strip()
    
    # 验证输入
    if not title or not content or not category:
        return jsonify({'code': 400, 'message': '标题、内容和分类不能为空'}), 400
    
    valid, msg = validate_title(title)
    if not valid:
        return jsonify({'code': 400, 'message': msg}), 400
    
    valid, msg = validate_content(content)
    if not valid:
        return jsonify({'code': 400, 'message': msg}), 400
    
    # 转义HTML
    title = escape_html(title)
    content = escape_html(content)
    category = escape_html(category)
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 检查是否存在
            cursor.execute("SELECT id FROM party_knowledge WHERE id = %s", (knowledge_id,))
            if not cursor.fetchone():
                return jsonify({'code': 404, 'message': '党建知识不存在'}), 404
            
            # 更新
            cursor.execute("""
                UPDATE party_knowledge
                SET title = %s, content = %s, category = %s
                WHERE id = %s
            """, (title, content, category, knowledge_id))
    
    log_operation('update_knowledge', {'id': knowledge_id, 'title': title}, user['id'], user['username'])
    
    return jsonify({'code': 200, 'message': '更新成功'})


@party_knowledge_bp.route('/api/party/knowledge/<int:knowledge_id>', methods=['DELETE'])
def delete_knowledge(knowledge_id):
    """删除党建知识（管理员）"""
    user = session.get('user')
    if not user or user.get('role') != 'admin':
        return jsonify({'code': 403, 'message': '权限不足'}), 403
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 检查是否存在
            cursor.execute("SELECT id FROM party_knowledge WHERE id = %s", (knowledge_id,))
            if not cursor.fetchone():
                return jsonify({'code': 404, 'message': '党建知识不存在'}), 404
            
            # 删除
            cursor.execute("DELETE FROM party_knowledge WHERE id = %s", (knowledge_id,))
    
    log_operation('delete_knowledge', {'id': knowledge_id}, user['id'], user['username'])
    
    return jsonify({'code': 200, 'message': '删除成功'})


@party_knowledge_bp.route('/api/party/knowledge/<int:knowledge_id>/study', methods=['POST'])
def record_study(knowledge_id):
    """记录学习进度"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '未登录'}), 401
    
    data = request.json or {}
    study_time = int(data.get('study_time', 0))
    completed = data.get('completed', False)
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 检查党建知识是否存在
            cursor.execute("SELECT id FROM party_knowledge WHERE id = %s", (knowledge_id,))
            if not cursor.fetchone():
                return jsonify({'code': 404, 'message': '党建知识不存在'}), 404
            
            # 检查是否已有学习记录
            cursor.execute("""
                SELECT id FROM party_study_records
                WHERE user_id = %s AND knowledge_id = %s
            """, (user_id, knowledge_id))
            record = cursor.fetchone()
            
            if record:
                # 更新现有记录
                cursor.execute("""
                    UPDATE party_study_records
                    SET study_time = study_time + %s, completed = %s
                    WHERE id = %s
                """, (study_time, completed, record['id']))
            else:
                # 创建新记录
                cursor.execute("""
                    INSERT INTO party_study_records (user_id, knowledge_id, study_time, completed)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, knowledge_id, study_time, completed))
            
            # 如果完成学习，添加积分
            if completed:
                cursor.execute("""
                    INSERT INTO party_integral (user_id, points, reason, type)
                    VALUES (%s, 5, '完成党建知识学习', 'add')
                """, (user_id,))
    
    return jsonify({'code': 200, 'message': '学习记录更新成功'})


@party_knowledge_bp.route('/api/party/knowledge/categories', methods=['GET'])
def get_categories():
    """获取党建知识分类列表"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT category FROM party_knowledge ORDER BY category")
            categories = [row['category'] for row in cursor.fetchall()]
    
    return jsonify({'code': 200, 'data': categories})


@party_knowledge_bp.route('/api/party/knowledge/<int:knowledge_id>/review', methods=['PUT'])
def review_knowledge(knowledge_id):
    """审核党建知识（管理员）"""
    user = session.get('user')
    if not user or user.get('role') != 'admin':
        return jsonify({'code': 403, 'message': '权限不足'}), 403
    
    data = request.json or {}
    status = data.get('status', '').strip()
    
    if status not in ['approved', 'rejected']:
        return jsonify({'code': 400, 'message': '无效的审核状态'}), 400
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 检查党建知识是否存在
            cursor.execute("SELECT id FROM party_knowledge WHERE id = %s", (knowledge_id,))
            if not cursor.fetchone():
                return jsonify({'code': 404, 'message': '党建知识不存在'}), 404
            
            # 更新审核状态
            cursor.execute("""
                UPDATE party_knowledge
                SET status = %s
                WHERE id = %s
            """, (status, knowledge_id))
    
    log_operation('review_knowledge', {'id': knowledge_id, 'status': status}, user['id'], user['username'])
    
    return jsonify({'code': 200, 'message': '审核成功'})

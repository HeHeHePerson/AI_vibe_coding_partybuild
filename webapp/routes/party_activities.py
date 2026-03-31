"""
组织活动模块路由

功能：
- 获取活动列表
- 获取活动详情
- 创建活动（管理员）
- 更新活动（管理员）
- 删除活动（管理员）
- 报名参加活动
- 取消报名
- 更新参与状态（管理员）
"""
from flask import Blueprint, request, jsonify, session
from database import get_db
from webapp.utils.security import escape_html, validate_title, validate_content
from webapp.utils.operation_log import log_operation
from datetime import datetime

party_activities_bp = Blueprint('party_activities', __name__)


@party_activities_bp.route('/api/party/activities', methods=['GET'])
def get_activities():
    """获取活动列表"""
    status = request.args.get('status', '')
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
                where_conditions.append("pa.review_status = 'approved'")
            
            if status:
                where_conditions.append("pa.status = %s")
                params.append(status)
            
            where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # 查询总数
            cursor.execute(f"SELECT COUNT(*) as total FROM party_activities pa {where_clause}", params)
            total = cursor.fetchone()['total']
            
            # 查询列表
            cursor.execute(f"""
                SELECT pa.id, pa.title, pa.content as description, pa.start_time as activity_time, pa.location, 
                       pa.max_participants, pa.current_participants as participant_count, pa.status, pa.review_status,
                       pa.created_at, u.username as author_name
                FROM party_activities pa
                LEFT JOIN users u ON pa.author_id = u.id
                {where_clause}
                ORDER BY pa.created_at DESC
                LIMIT %s OFFSET %s
            """, params + [per_page, offset])
            activities = cursor.fetchall()
    
    return jsonify({
        'code': 200,
        'data': {
            'list': activities,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
        }
    })


@party_activities_bp.route('/api/party/activities/<int:activity_id>', methods=['GET'])
def get_activity_detail(activity_id):
    """获取活动详情"""
    user_id = session.get('user_id')
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 查询活动详情
            cursor.execute("""
                SELECT pa.*, u.username as author_name
                FROM party_activities pa
                LEFT JOIN users u ON pa.author_id = u.id
                WHERE pa.id = %s
            """, (activity_id,))
            activity = cursor.fetchone()
            
            if not activity:
                return jsonify({'code': 404, 'message': '活动不存在'}), 404
            
            # 检查用户是否已报名
            is_registered = False
            registration_status = None
            if user_id:
                cursor.execute("""
                    SELECT status FROM activity_participants
                    WHERE activity_id = %s AND user_id = %s
                """, (activity_id, user_id))
                registration = cursor.fetchone()
                if registration:
                    is_registered = True
                    registration_status = registration['status']
            
            # 获取参与列表
            cursor.execute("""
                SELECT ap.user_id, u.username, ap.status, ap.created_at
                FROM activity_participants ap
                LEFT JOIN users u ON ap.user_id = u.id
                WHERE ap.activity_id = %s
                ORDER BY ap.created_at DESC
            """, (activity_id,))
            participants = cursor.fetchall()
    
    return jsonify({
        'code': 200,
        'data': {
            'activity': activity,
            'is_registered': is_registered,
            'registration_status': registration_status,
            'participants': participants
        }
    })


@party_activities_bp.route('/api/party/activities', methods=['POST'])
def create_activity():
    """创建活动"""
    user = session.get('user')
    if not user:
        return jsonify({'code': 401, 'message': '未登录'}), 401
    
    data = request.json or {}
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    location = data.get('location', '').strip()
    organizer = data.get('organizer', '').strip()
    max_participants = data.get('max_participants')
    
    # 验证输入
    if not title or not content or not start_time or not end_time or not location or not organizer:
        return jsonify({'code': 400, 'message': '标题、内容、时间、地点和组织者不能为空'}), 400
    
    valid, msg = validate_title(title)
    if not valid:
        return jsonify({'code': 400, 'message': msg}), 400
    
    valid, msg = validate_content(content)
    if not valid:
        return jsonify({'code': 400, 'message': msg}), 400
    
    # 验证时间
    try:
        start_datetime = datetime.fromisoformat(start_time)
        end_datetime = datetime.fromisoformat(end_time)
        if start_datetime >= end_datetime:
            return jsonify({'code': 400, 'message': '开始时间必须早于结束时间'}), 400
    except ValueError:
        return jsonify({'code': 400, 'message': '时间格式错误'}), 400
    
    # 转义HTML
    title = escape_html(title)
    content = escape_html(content)
    location = escape_html(location)
    organizer = escape_html(organizer)
    
    # 确定审核状态
    review_status = 'approved' if user.get('role') == 'admin' else 'pending'
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO party_activities (
                    title, content, start_time, end_time, location, 
                    organizer, max_participants, author_id, review_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                title, content, start_datetime, end_datetime, 
                location, organizer, max_participants, user['id'], review_status
            ))
            activity_id = cursor.lastrowid
    
    log_operation('create_activity', {'title': title}, user['id'], user['username'])
    
    return jsonify({
        'code': 200,
        'message': '创建成功',
        'data': {'id': activity_id}
    })


@party_activities_bp.route('/api/party/activities/<int:activity_id>', methods=['PUT'])
def update_activity(activity_id):
    """更新活动（管理员）"""
    user = session.get('user')
    if not user or user.get('role') != 'admin':
        return jsonify({'code': 403, 'message': '权限不足'}), 403
    
    data = request.json or {}
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    location = data.get('location', '').strip()
    organizer = data.get('organizer', '').strip()
    max_participants = data.get('max_participants')
    
    # 验证输入
    if not title or not content or not start_time or not end_time or not location or not organizer:
        return jsonify({'code': 400, 'message': '标题、内容、时间、地点和组织者不能为空'}), 400
    
    valid, msg = validate_title(title)
    if not valid:
        return jsonify({'code': 400, 'message': msg}), 400
    
    valid, msg = validate_content(content)
    if not valid:
        return jsonify({'code': 400, 'message': msg}), 400
    
    # 验证时间
    try:
        start_datetime = datetime.fromisoformat(start_time)
        end_datetime = datetime.fromisoformat(end_time)
        if start_datetime >= end_datetime:
            return jsonify({'code': 400, 'message': '开始时间必须早于结束时间'}), 400
    except ValueError:
        return jsonify({'code': 400, 'message': '时间格式错误'}), 400
    
    # 转义HTML
    title = escape_html(title)
    content = escape_html(content)
    location = escape_html(location)
    organizer = escape_html(organizer)
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 检查是否存在
            cursor.execute("SELECT id FROM party_activities WHERE id = %s", (activity_id,))
            if not cursor.fetchone():
                return jsonify({'code': 404, 'message': '活动不存在'}), 404
            
            # 更新
            cursor.execute("""
                UPDATE party_activities
                SET title = %s, content = %s, start_time = %s, end_time = %s, 
                    location = %s, organizer = %s, max_participants = %s
                WHERE id = %s
            """, (
                title, content, start_datetime, end_datetime, 
                location, organizer, max_participants, activity_id
            ))
    
    log_operation('update_activity', {'id': activity_id, 'title': title}, user['id'], user['username'])
    
    return jsonify({'code': 200, 'message': '更新成功'})


@party_activities_bp.route('/api/party/activities/<int:activity_id>', methods=['DELETE'])
def delete_activity(activity_id):
    """删除活动（管理员）"""
    user = session.get('user')
    if not user or user.get('role') != 'admin':
        return jsonify({'code': 403, 'message': '权限不足'}), 403
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 检查是否存在
            cursor.execute("SELECT id FROM party_activities WHERE id = %s", (activity_id,))
            if not cursor.fetchone():
                return jsonify({'code': 404, 'message': '活动不存在'}), 404
            
            # 删除
            cursor.execute("DELETE FROM party_activities WHERE id = %s", (activity_id,))
    
    log_operation('delete_activity', {'id': activity_id}, user['id'], user['username'])
    
    return jsonify({'code': 200, 'message': '删除成功'})


@party_activities_bp.route('/api/party/activities/<int:activity_id>/register', methods=['POST'])
def register_activity(activity_id):
    """报名参加活动"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '未登录'}), 401
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 检查活动是否存在
            cursor.execute("SELECT id, max_participants, current_participants, status FROM party_activities WHERE id = %s", (activity_id,))
            activity = cursor.fetchone()
            if not activity:
                return jsonify({'code': 404, 'message': '活动不存在'}), 404
            
            # 检查活动状态
            if activity['status'] == 'completed':
                return jsonify({'code': 400, 'message': '活动已结束，无法报名'}), 400
            
            # 检查是否已报名
            cursor.execute("""
                SELECT id FROM activity_participants
                WHERE activity_id = %s AND user_id = %s
            """, (activity_id, user_id))
            if cursor.fetchone():
                return jsonify({'code': 400, 'message': '您已报名此活动'}), 400
            
            # 检查名额是否已满
            if activity['max_participants'] and activity['current_participants'] >= activity['max_participants']:
                return jsonify({'code': 400, 'message': '活动名额已满'}), 400
            
            # 开始事务
            try:
                # 插入报名记录
                cursor.execute("""
                    INSERT INTO activity_participants (activity_id, user_id, status)
                    VALUES (%s, %s, 'registered')
                """, (activity_id, user_id))
                
                # 更新活动参与人数
                cursor.execute("""
                    UPDATE party_activities
                    SET current_participants = current_participants + 1
                    WHERE id = %s
                """, (activity_id,))
                
                # 添加积分
                cursor.execute("""
                    INSERT INTO party_integral (user_id, points, reason, type)
                    VALUES (%s, 10, '报名参加组织活动', 'add')
                """, (user_id,))
                
                conn.commit()
            except Exception as e:
                conn.rollback()
                return jsonify({'code': 500, 'message': '报名失败'}), 500
    
    return jsonify({'code': 200, 'message': '报名成功'})


@party_activities_bp.route('/api/party/activities/<int:activity_id>/unregister', methods=['POST'])
def unregister_activity(activity_id):
    """取消报名"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '未登录'}), 401
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 检查是否已报名
            cursor.execute("""
                SELECT id FROM activity_participants
                WHERE activity_id = %s AND user_id = %s
            """, (activity_id, user_id))
            registration = cursor.fetchone()
            if not registration:
                return jsonify({'code': 400, 'message': '您未报名此活动'}), 400
            
            # 开始事务
            try:
                # 删除报名记录
                cursor.execute("""
                    DELETE FROM activity_participants
                    WHERE id = %s
                """, (registration['id'],))
                
                # 更新活动参与人数
                cursor.execute("""
                    UPDATE party_activities
                    SET current_participants = current_participants - 1
                    WHERE id = %s
                """, (activity_id,))
                
                conn.commit()
            except Exception as e:
                conn.rollback()
                return jsonify({'code': 500, 'message': '取消报名失败'}), 500
    
    return jsonify({'code': 200, 'message': '取消报名成功'})


@party_activities_bp.route('/api/party/activities/<int:activity_id>/participants/<int:user_id>/status', methods=['PUT'])
def update_participant_status(activity_id, user_id):
    """更新参与状态（管理员）"""
    user = session.get('user')
    if not user or user.get('role') != 'admin':
        return jsonify({'code': 403, 'message': '权限不足'}), 403
    
    data = request.json or {}
    status = data.get('status', '').strip()
    
    if status not in ['registered', 'attended', 'absent']:
        return jsonify({'code': 400, 'message': '无效的状态值'}), 400
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 检查报名记录是否存在
            cursor.execute("""
                SELECT id FROM activity_participants
                WHERE activity_id = %s AND user_id = %s
            """, (activity_id, user_id))
            if not cursor.fetchone():
                return jsonify({'code': 404, 'message': '报名记录不存在'}), 404
            
            # 更新状态
            cursor.execute("""
                UPDATE activity_participants
                SET status = %s
                WHERE activity_id = %s AND user_id = %s
            """, (status, activity_id, user_id))
            
            # 如果状态为attended，添加积分
            if status == 'attended':
                cursor.execute("""
                    INSERT INTO party_integral (user_id, points, reason, type)
                    VALUES (%s, 15, '参加组织活动', 'add')
                """, (user_id,))
    
    return jsonify({'code': 200, 'message': '状态更新成功'})


@party_activities_bp.route('/api/party/activities/<int:activity_id>/review', methods=['PUT'])
def review_activity(activity_id):
    """审核组织活动（管理员）"""
    user = session.get('user')
    if not user or user.get('role') != 'admin':
        return jsonify({'code': 403, 'message': '权限不足'}), 403
    
    data = request.json or {}
    status = data.get('status', '').strip()
    
    if status not in ['approved', 'rejected']:
        return jsonify({'code': 400, 'message': '无效的审核状态'}), 400
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 检查活动是否存在
            cursor.execute("SELECT id FROM party_activities WHERE id = %s", (activity_id,))
            if not cursor.fetchone():
                return jsonify({'code': 404, 'message': '活动不存在'}), 404
            
            # 更新审核状态
            cursor.execute("""
                UPDATE party_activities
                SET review_status = %s
                WHERE id = %s
            """, (status, activity_id))
    
    log_operation('review_activity', {'id': activity_id, 'status': status}, user['id'], user['username'])
    
    return jsonify({'code': 200, 'message': '审核成功'})

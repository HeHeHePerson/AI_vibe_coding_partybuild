"""
党员积分模块路由

功能：
- 获取积分记录列表
- 获取用户积分统计
- 管理员添加/扣除积分
- 积分排行榜
"""
from flask import Blueprint, request, jsonify, session
from database import get_db
from webapp.utils.security import escape_html
from webapp.utils.operation_log import log_operation

party_integral_bp = Blueprint('party_integral', __name__)


@party_integral_bp.route('/api/party/integral/records', methods=['GET'])
def get_integral_records():
    """获取积分记录列表"""
    user = session.get('user')
    user_id = session.get('user_id')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    offset = (page - 1) * per_page
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 构建查询条件
            if user and user.get('role') == 'admin':
                # 管理员可以查看所有记录
                where_clause = "" if not user_id else "WHERE user_id = %s"
                params = [user_id] if user_id else []
            else:
                # 普通用户只能查看自己的记录
                where_clause = "WHERE user_id = %s"
                params = [user_id]
            
            # 查询总数
            cursor.execute(f"SELECT COUNT(*) as total FROM party_integral {where_clause}", params)
            total = cursor.fetchone()['total']
            
            # 查询列表
            cursor.execute(f"""
                SELECT pi.*, u.username
                FROM party_integral pi
                LEFT JOIN users u ON pi.user_id = u.id
                {where_clause}
                ORDER BY pi.created_at DESC
                LIMIT %s OFFSET %s
            """, params + [per_page, offset])
            records = cursor.fetchall()
    
    return jsonify({
        'code': 200,
        'data': {
            'list': records,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
        }
    })


@party_integral_bp.route('/api/party/integral/stats', methods=['GET'])
def get_integral_stats():
    """获取用户积分统计"""
    user = session.get('user')
    user_id = session.get('user_id')
    target_user_id = request.args.get('user_id')
    
    # 权限检查
    if target_user_id and not (user and user.get('role') == 'admin'):
        return jsonify({'code': 403, 'message': '权限不足'}), 403
    
    query_user_id = target_user_id if (user and user.get('role') == 'admin' and target_user_id) else user_id
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 查询总积分
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN type = 'add' THEN points ELSE -points END) as total_points,
                    SUM(CASE WHEN type = 'add' THEN points ELSE 0 END) as total_add,
                    SUM(CASE WHEN type = 'deduct' THEN points ELSE 0 END) as total_deduct
                FROM party_integral
                WHERE user_id = %s
            """, (query_user_id,))
            stats = cursor.fetchone()
            
            # 确保返回的数据不为None
            stats = {
                'total_points': stats['total_points'] or 0,
                'total_add': stats['total_add'] or 0,
                'total_deduct': stats['total_deduct'] or 0
            }
    
    return jsonify({'code': 200, 'data': stats})


@party_integral_bp.route('/api/party/integral', methods=['POST'])
def manage_integral():
    """管理员添加/扣除积分"""
    user = session.get('user')
    if not user or user.get('role') != 'admin':
        return jsonify({'code': 403, 'message': '权限不足'}), 403
    
    data = request.json or {}
    user_id = data.get('user_id')
    points = data.get('points')
    reason = data.get('reason', '').strip()
    type_ = data.get('type', 'add')
    
    # 验证输入
    if not user_id or not points or not reason:
        return jsonify({'code': 400, 'message': '用户ID、积分和原因不能为空'}), 400
    
    # 验证积分
    try:
        points = int(points)
        if points <= 0:
            return jsonify({'code': 400, 'message': '积分必须大于0'}), 400
    except ValueError:
        return jsonify({'code': 400, 'message': '积分格式错误'}), 400
    
    # 验证类型
    if type_ not in ['add', 'deduct']:
        return jsonify({'code': 400, 'message': '无效的积分类型'}), 400
    
    # 转义HTML
    reason = escape_html(reason)
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                return jsonify({'code': 404, 'message': '用户不存在'}), 404
            
            # 添加积分记录
            cursor.execute("""
                INSERT INTO party_integral (user_id, points, reason, type)
                VALUES (%s, %s, %s, %s)
            """, (user_id, points, reason, type_))
    
    log_operation('manage_integral', {'user_id': user_id, 'points': points, 'type': type_}, user['id'], user['username'])
    
    return jsonify({'code': 200, 'message': '操作成功'})


@party_integral_bp.route('/api/party/integral/ranking', methods=['GET'])
def get_integral_ranking():
    """积分排行榜"""
    limit = int(request.args.get('limit', 10))
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    u.id, u.username, 
                    SUM(CASE WHEN pi.type = 'add' THEN pi.points ELSE -pi.points END) as total_points
                FROM users u
                LEFT JOIN party_integral pi ON u.id = pi.user_id
                GROUP BY u.id, u.username
                ORDER BY total_points DESC
                LIMIT %s
            """, (limit,))
            ranking = cursor.fetchall()
    
    return jsonify({'code': 200, 'data': ranking})


@party_integral_bp.route('/api/party/integral/overview', methods=['GET'])
def get_integral_overview():
    """获取积分概览"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '未登录'}), 401
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 查询总积分
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN type = 'add' THEN points ELSE -points END) as total_integral
                FROM party_integral
                WHERE user_id = %s
            """, (user_id,))
            total_result = cursor.fetchone()
            total_integral = total_result['total_integral'] or 0
            
            # 查询本月积分
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN type = 'add' THEN points ELSE -points END) as monthly_integral
                FROM party_integral
                WHERE user_id = %s AND DATE_FORMAT(created_at, '%%Y-%%m') = DATE_FORMAT(NOW(), '%%Y-%%m')
            """, (user_id,))
            monthly_result = cursor.fetchone()
            monthly_integral = monthly_result['monthly_integral'] or 0
            
            # 查询积分排名
            cursor.execute("""
                SELECT COUNT(*) + 1 as user_rank
                FROM (
                    SELECT 
                        SUM(CASE WHEN type = 'add' THEN points ELSE -points END) as total_points
                    FROM party_integral
                    GROUP BY user_id
                    HAVING total_points > %s
                ) as ranks
            """, (total_integral,))
            rank_result = cursor.fetchone()
            rank = rank_result['user_rank'] if rank_result else 1
    
    return jsonify({
        'code': 200,
        'data': {
            'total_integral': total_integral,
            'monthly_integral': monthly_integral,
            'rank': rank
        }
    })


@party_integral_bp.route('/api/party/integral/rules', methods=['GET'])
def get_integral_rules():
    """获取积分规则"""
    rules = [
        {
            'category': '学习教育',
            'items': [
                {'action': '完成党建知识学习', 'points': 5, 'limit': '每篇文章一次'},
                {'action': '参加在线考试', 'points': 15, 'limit': '每次考试一次'}
            ]
        },
        {
            'category': '组织活动',
            'items': [
                {'action': '报名参加组织活动', 'points': 10, 'limit': '每次活动一次'},
                {'action': '实际参加组织活动', 'points': 15, 'limit': '每次活动一次'}
            ]
        },
        {
            'category': '党费缴纳',
            'items': [
                {'action': '按时缴纳党费', 'points': 20, 'limit': '每月一次'}
            ]
        },
        {
            'category': '志愿服务',
            'items': [
                {'action': '参加志愿服务活动', 'points': 25, 'limit': '每次活动一次'}
            ]
        }
    ]
    
    return jsonify({'code': 200, 'data': rules})


@party_integral_bp.route('/api/party/integral/details', methods=['GET'])
def get_integral_details():
    """获取积分明细"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '未登录'}), 401
    
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    offset = (page - 1) * per_page
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 查询总数
            cursor.execute("SELECT COUNT(*) as total FROM party_integral WHERE user_id = %s", (user_id,))
            total = cursor.fetchone()['total']
            
            # 查询列表
            cursor.execute("""
                SELECT id, points, reason, type as category, created_at
                FROM party_integral
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (user_id, per_page, offset))
            details = cursor.fetchall()
    
    return jsonify({
        'code': 200,
        'data': {
            'list': details,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
        }
    })

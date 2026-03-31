"""
党费缴纳模块路由

功能：
- 获取党费缴纳记录列表
- 获取党费缴纳详情
- 创建党费缴纳记录（管理员）
- 更新党费缴纳状态
- 批量导入党费记录（管理员）
"""
from flask import Blueprint, request, jsonify, session
from database import get_db
from webapp.utils.security import escape_html
from webapp.utils.operation_log import log_operation
from datetime import datetime

party_fees_bp = Blueprint('party_fees', __name__)


@party_fees_bp.route('/api/party/fees', methods=['GET'])
def get_fee_records():
    """获取党费缴纳记录列表"""
    user = session.get('user')
    user_id = session.get('user_id')
    status = request.args.get('status', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    offset = (page - 1) * per_page
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 构建查询条件
            if user and user.get('role') == 'admin':
                # 管理员可以查看所有记录
                where_clause = "" if not status else "WHERE status = %s"
                params = [status] if status else []
            else:
                # 普通用户只能查看自己的记录
                where_clause = "WHERE user_id = %s" + (" AND status = %s" if status else "")
                params = [user_id] + ([status] if status else [])
            
            # 查询总数
            cursor.execute(f"SELECT COUNT(*) as total FROM party_fees {where_clause}", params)
            total = cursor.fetchone()['total']
            
            # 查询列表
            cursor.execute(f"""
                SELECT pf.*, u.username
                FROM party_fees pf
                LEFT JOIN users u ON pf.user_id = u.id
                {where_clause}
                ORDER BY pf.payment_date DESC
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


@party_fees_bp.route('/api/party/fees/<int:fee_id>', methods=['GET'])
def get_fee_detail(fee_id):
    """获取党费缴纳详情"""
    user = session.get('user')
    user_id = session.get('user_id')
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 查询详情
            cursor.execute("""
                SELECT pf.*, u.username
                FROM party_fees pf
                LEFT JOIN users u ON pf.user_id = u.id
                WHERE pf.id = %s
            """, (fee_id,))
            fee = cursor.fetchone()
            
            if not fee:
                return jsonify({'code': 404, 'message': '缴费记录不存在'}), 404
            
            # 权限检查
            if not (user and (user.get('role') == 'admin' or fee['user_id'] == user_id)):
                return jsonify({'code': 403, 'message': '权限不足'}), 403
    
    return jsonify({'code': 200, 'data': fee})


@party_fees_bp.route('/api/party/fees', methods=['POST'])
def create_fee_record():
    """创建党费缴纳记录（管理员）"""
    user = session.get('user')
    if not user or user.get('role') != 'admin':
        return jsonify({'code': 403, 'message': '权限不足'}), 403
    
    data = request.json or {}
    user_id = data.get('user_id')
    amount = data.get('amount')
    payment_date = data.get('payment_date')
    payment_period = data.get('payment_period', '').strip()
    status = data.get('status', 'pending')
    payment_method = data.get('payment_method', '').strip()
    
    # 验证输入
    if not user_id or not amount or not payment_date or not payment_period:
        return jsonify({'code': 400, 'message': '用户ID、金额、缴费日期和缴费周期不能为空'}), 400
    
    # 验证金额
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'code': 400, 'message': '金额必须大于0'}), 400
    except ValueError:
        return jsonify({'code': 400, 'message': '金额格式错误'}), 400
    
    # 验证日期
    try:
        payment_date_obj = datetime.fromisoformat(payment_date)
    except ValueError:
        return jsonify({'code': 400, 'message': '日期格式错误'}), 400
    
    # 验证状态
    if status not in ['pending', 'paid', 'overdue', 'completed']:
        return jsonify({'code': 400, 'message': '无效的状态值'}), 400
    
    # 转义HTML
    payment_period = escape_html(payment_period)
    payment_method = escape_html(payment_method)
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                return jsonify({'code': 404, 'message': '用户不存在'}), 404
            
            # 创建记录
            cursor.execute("""
                INSERT INTO party_fees (
                    user_id, amount, payment_date, payment_period, 
                    status, payment_method
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id, amount, payment_date_obj, payment_period, 
                status, payment_method
            ))
            fee_id = cursor.lastrowid
            
            # 如果状态为paid，添加积分
            if status == 'paid':
                cursor.execute("""
                    INSERT INTO party_integral (user_id, points, reason, type)
                    VALUES (%s, 20, '按时缴纳党费', 'add')
                """, (user_id,))
    
    log_operation('create_fee', {'user_id': user_id, 'amount': amount}, user['id'], user['username'])
    
    return jsonify({
        'code': 200,
        'message': '创建成功',
        'data': {'id': fee_id}
    })


@party_fees_bp.route('/api/party/fees/<int:fee_id>', methods=['PUT'])
def update_fee_status(fee_id):
    """更新党费缴纳状态"""
    user = session.get('user')
    user_id = session.get('user_id')
    
    data = request.json or {}
    status = data.get('status', '').strip()
    
    if status not in ['pending', 'paid', 'overdue', 'completed']:
        return jsonify({'code': 400, 'message': '无效的状态值'}), 400
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 查询记录
            cursor.execute("SELECT user_id, status FROM party_fees WHERE id = %s", (fee_id,))
            fee = cursor.fetchone()
            if not fee:
                return jsonify({'code': 404, 'message': '缴费记录不存在'}), 404
            
            # 权限检查
            if not (user and (user.get('role') == 'admin' or fee['user_id'] == user_id)):
                return jsonify({'code': 403, 'message': '权限不足'}), 403
            
            # 更新状态
            cursor.execute("UPDATE party_fees SET status = %s WHERE id = %s", (status, fee_id))
            
            # 如果状态从非paid变为paid，添加积分
            if fee['status'] != 'paid' and status == 'paid':
                cursor.execute("""
                    INSERT INTO party_integral (user_id, points, reason, type)
                    VALUES (%s, 20, '按时缴纳党费', 'add')
                """, (fee['user_id'],))
    
    log_operation('update_fee_status', {'id': fee_id, 'status': status}, user['id'], user['username'])
    
    return jsonify({'code': 200, 'message': '状态更新成功'})


@party_fees_bp.route('/api/party/fees/<int:fee_id>', methods=['DELETE'])
def delete_fee_record(fee_id):
    """删除党费缴纳记录（管理员）"""
    user = session.get('user')
    if not user or user.get('role') != 'admin':
        return jsonify({'code': 403, 'message': '权限不足'}), 403
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 检查记录是否存在
            cursor.execute("SELECT id FROM party_fees WHERE id = %s", (fee_id,))
            if not cursor.fetchone():
                return jsonify({'code': 404, 'message': '缴费记录不存在'}), 404
            
            # 删除记录
            cursor.execute("DELETE FROM party_fees WHERE id = %s", (fee_id,))
    
    log_operation('delete_fee', {'id': fee_id}, user['id'], user['username'])
    
    return jsonify({'code': 200, 'message': '删除成功'})


@party_fees_bp.route('/api/party/fees/batch', methods=['POST'])
def batch_import_fees():
    """批量导入党费记录（管理员）"""
    user = session.get('user')
    if not user or user.get('role') != 'admin':
        return jsonify({'code': 403, 'message': '权限不足'}), 403
    
    data = request.json or {}
    records = data.get('records', [])
    
    if not records:
        return jsonify({'code': 400, 'message': '请提供导入数据'}), 400
    
    success_count = 0
    failed_records = []
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            for record in records:
                try:
                    user_id = record.get('user_id')
                    amount = record.get('amount')
                    payment_date = record.get('payment_date')
                    payment_period = record.get('payment_period', '').strip()
                    status = record.get('status', 'pending')
                    payment_method = record.get('payment_method', '').strip()
                    
                    # 验证输入
                    if not user_id or not amount or not payment_date or not payment_period:
                        failed_records.append({'record': record, 'error': '缺少必要字段'})
                        continue
                    
                    # 验证金额
                    amount = float(amount)
                    if amount <= 0:
                        failed_records.append({'record': record, 'error': '金额必须大于0'})
                        continue
                    
                    # 验证日期
                    payment_date_obj = datetime.fromisoformat(payment_date)
                    
                    # 验证状态
                    if status not in ['pending', 'paid', 'overdue', 'completed']:
                        failed_records.append({'record': record, 'error': '无效的状态值'})
                        continue
                    
                    # 转义HTML
                    payment_period = escape_html(payment_period)
                    payment_method = escape_html(payment_method)
                    
                    # 检查用户是否存在
                    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                    if not cursor.fetchone():
                        failed_records.append({'record': record, 'error': '用户不存在'})
                        continue
                    
                    # 插入记录
                    cursor.execute("""
                        INSERT INTO party_fees (
                            user_id, amount, payment_date, payment_period, 
                            status, payment_method
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        user_id, amount, payment_date_obj, payment_period, 
                        status, payment_method
                    ))
                    
                    # 如果状态为paid，添加积分
                    if status == 'paid':
                        cursor.execute("""
                            INSERT INTO party_integral (user_id, points, reason, type)
                            VALUES (%s, 20, '按时缴纳党费', 'add')
                        """, (user_id,))
                    
                    success_count += 1
                except Exception as e:
                    failed_records.append({'record': record, 'error': str(e)})
            
            conn.commit()
    
    log_operation('batch_import_fees', {'success': success_count, 'failed': len(failed_records)}, user['id'], user['username'])
    
    return jsonify({
        'code': 200,
        'message': f'批量导入完成，成功{success_count}条，失败{len(failed_records)}条',
        'data': {
            'success_count': success_count,
            'failed_count': len(failed_records),
            'failed_records': failed_records
        }
    })


@party_fees_bp.route('/api/party/fees/stats', methods=['GET'])
def get_fee_stats():
    """获取党费缴纳统计"""
    user = session.get('user')
    user_id = session.get('user_id')
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            if user and user.get('role') == 'admin':
                # 管理员查看所有统计
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_records,
                        SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) as total_paid,
                        SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as total_pending,
                        SUM(CASE WHEN status = 'overdue' THEN amount ELSE 0 END) as total_overdue
                    FROM party_fees
                """)
            else:
                # 普通用户查看自己的统计
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_records,
                        SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) as total_paid,
                        SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as total_pending,
                        SUM(CASE WHEN status = 'overdue' THEN amount ELSE 0 END) as total_overdue
                    FROM party_fees
                    WHERE user_id = %s
                """, (user_id,))
            
            stats = cursor.fetchone()
    
    return jsonify({'code': 200, 'data': stats})


@party_fees_bp.route('/api/party/fees/user-info', methods=['GET'])
def get_user_fee_info():
    """获取用户缴费信息"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '未登录'}), 401
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            # 查询用户基本信息
            cursor.execute("""
                SELECT username as name
                FROM users
                WHERE id = %s
            """, (user_id,))
            user_info = cursor.fetchone()
            
            # 查询缴费统计
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) as total_paid,
                    SUM(CASE WHEN status = 'pending' OR status = 'overdue' THEN amount ELSE 0 END) as overdue_amount
                FROM party_fees
                WHERE user_id = %s
            """, (user_id,))
            fee_stats = cursor.fetchone()
            
            # 构建返回数据
            result = {
                'name': user_info.get('name', '') if user_info else '',
                'party_id': '',  # 假设党员编号存储在users表中，这里需要根据实际情况调整
                'monthly_fee': 50,  # 假设月缴费标准为50元，实际应从数据库获取
                'total_paid': fee_stats.get('total_paid', 0) if fee_stats else 0,
                'overdue_amount': fee_stats.get('overdue_amount', 0) if fee_stats else 0
            }
    
    return jsonify({'code': 200, 'data': result})


@party_fees_bp.route('/api/party/fees/pay', methods=['POST'])
def pay_fee():
    """在线缴费"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'code': 401, 'message': '未登录'}), 401
        
        data = request.json or {}
        amount = data.get('amount')
        payment_method = data.get('payment_method')
        remark = data.get('remark', '').strip()
        
        # 验证输入
        if not amount or not payment_method:
            return jsonify({'code': 400, 'message': '金额和缴费方式不能为空'}), 400
        
        # 验证金额
        try:
            amount = float(amount)
            if amount <= 0:
                return jsonify({'code': 400, 'message': '金额必须大于0'}), 400
        except ValueError:
            return jsonify({'code': 400, 'message': '金额格式错误'}), 400
        
        # 转义HTML
        remark = escape_html(remark)
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                # 创建缴费记录
                cursor.execute("""
                    INSERT INTO party_fees (user_id, amount, payment_date, payment_period, status, payment_method, remark)
                    VALUES (%s, %s, NOW(), CONCAT(YEAR(NOW()), '-', MONTH(NOW())), 'paid', %s, %s)
                """, (user_id, amount, payment_method, remark))
                
                # 添加积分
                cursor.execute("""
                    INSERT INTO party_integral (user_id, points, reason, type)
                    VALUES (%s, 20, '按时缴纳党费', 'add')
                """, (user_id,))
        
        return jsonify({'code': 200, 'message': '缴费成功'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500

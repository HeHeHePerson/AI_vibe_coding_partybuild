"""
操作日志模块

功能：
- 记录用户敏感操作（登录、登出、创建、修改、删除等）
- 提供操作日志查询接口（仅管理员）
- 记录操作IP和User-Agent

使用说明：
- 导入 log_operation 函数
- 在需要记录的操作中调用 log_operation
"""
import json
from flask import request, session
from database import get_db
from webapp.utils.login_security import get_client_ip


def log_operation(operation, detail=None, user_id=None, username=None):
    """
    记录操作日志

    参数:
        operation: 操作类型（如 'login', 'create_content', 'delete_user' 等）
        detail: 操作详情（可选）
        user_id: 用户ID（可选，默认从session获取）
        username: 用户名（可选，默认从session获取）
    """
    if user_id is None:
        user_id = session.get('user_id')
    
    if username is None:
        user_info = session.get('user')
        if user_info:
            username = user_info.get('username', 'unknown')
        else:
            username = 'anonymous'
    
    ip_address = get_client_ip()
    user_agent = request.headers.get('User-Agent', '')[:255] if request else ''
    
    if detail and isinstance(detail, (dict, list)):
        try:
            detail = json.dumps(detail, ensure_ascii=False)
        except:
            pass
    
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO operation_logs 
                   (user_id, username, operation, detail, ip_address, user_agent)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (user_id, username, operation, detail, ip_address, user_agent)
            )


def get_operation_logs(limit=100, offset=0, operation=None, user_id=None, start_date=None, end_date=None):
    """
    获取操作日志列表

    参数:
        limit: 返回数量限制
        offset: 偏移量
        operation: 按操作类型过滤
        user_id: 按用户ID过滤
        start_date: 开始日期
        end_date: 结束日期

    返回:
        list: 日志列表
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            where_conditions = []
            params = []
            
            if operation:
                where_conditions.append("operation = %s")
                params.append(operation)
            
            if user_id:
                where_conditions.append("user_id = %s")
                params.append(user_id)
            
            if start_date:
                where_conditions.append("created_at >= %s")
                params.append(start_date)
            
            if end_date:
                where_conditions.append("created_at <= %s")
                params.append(end_date)
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            sql = f"""
                SELECT id, user_id, username, operation, detail, 
                       ip_address, user_agent, created_at
                FROM operation_logs
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            
            cursor.execute(sql, params)
            return cursor.fetchall()


def get_log_count(operation=None, user_id=None, start_date=None, end_date=None):
    """
    获取操作日志总数

    参数:
        operation: 按操作类型过滤
        user_id: 按用户ID过滤
        start_date: 开始日期
        end_date: 结束日期

    返回:
        int: 日志总数
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            where_conditions = []
            params = []
            
            if operation:
                where_conditions.append("operation = %s")
                params.append(operation)
            
            if user_id:
                where_conditions.append("user_id = %s")
                params.append(user_id)
            
            if start_date:
                where_conditions.append("created_at >= %s")
                params.append(start_date)
            
            if end_date:
                where_conditions.append("created_at <= %s")
                params.append(end_date)
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            sql = f"SELECT COUNT(*) as count FROM operation_logs WHERE {where_clause}"
            cursor.execute(sql, params)
            result = cursor.fetchone()
            return result['count'] if result else 0


def get_operation_logs_for_export(operation=None, user_id=None, start_date=None, end_date=None):
    """
    获取所有操作日志（用于导出）

    参数:
        operation: 按操作类型过滤
        user_id: 按用户ID过滤
        start_date: 开始日期
        end_date: 结束日期

    返回:
        list: 日志列表
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            where_conditions = []
            params = []
            
            if operation:
                where_conditions.append("operation = %s")
                params.append(operation)
            
            if user_id:
                where_conditions.append("user_id = %s")
                params.append(user_id)
            
            if start_date:
                where_conditions.append("created_at >= %s")
                params.append(start_date)
            
            if end_date:
                where_conditions.append("created_at <= %s")
                params.append(end_date)
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            sql = f"""
                SELECT id, user_id, username, operation, detail, 
                       ip_address, user_agent, created_at
                FROM operation_logs
                WHERE {where_clause}
                ORDER BY created_at DESC
            """
            
            cursor.execute(sql, params)
            return cursor.fetchall()

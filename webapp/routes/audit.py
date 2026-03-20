"""
用户审计日志路由模块

功能：
- 记录用户登录、登出、发布内容、发布评论等操作
- 提供管理员查看审计日志的接口
- 支持审计日志下载（CSV格式）
"""
import csv
import io
from flask import Blueprint, request, jsonify, session, make_response
from webapp.utils.operation_log import get_operation_logs, get_log_count, get_operation_logs_for_export

audit_bp = Blueprint('audit', __name__)


def require_admin():
    """检查是否是管理员"""
    user = session.get('user')
    if not user:
        return False, jsonify({'code': 401, 'message': '请先登录'}), 401
    if user.get('role') != 'admin':
        return False, jsonify({'code': 403, 'message': '权限不足'}), 403
    return True, None, None


@audit_bp.route('/api/audit/logs', methods=['GET'])
def get_audit_logs():
    """获取审计日志列表（仅管理员）"""
    ok, error_resp, status = require_admin()
    if not ok:
        return error_resp, status

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = min(per_page, 200)
    offset = (page - 1) * per_page

    operation = request.args.get('operation', '').strip()
    user_id = request.args.get('user_id', type=int)
    username = request.args.get('username', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()

    logs = get_operation_logs(
        limit=per_page,
        offset=offset,
        operation=operation if operation else None,
        user_id=user_id if user_id else None,
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None
    )

    count = get_log_count(
        operation=operation if operation else None,
        user_id=user_id if user_id else None,
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None
    )

    return jsonify({
        'code': 200,
        'data': {
            'logs': logs,
            'pagination': {
                'total': count,
                'page': page,
                'per_page': per_page,
                'pages': (count + per_page - 1) // per_page if per_page > 0 else 0
            }
        }
    })


@audit_bp.route('/api/audit/operations', methods=['GET'])
def get_operation_types():
    """获取审计日志支持的操作类型列表（仅管理员）"""
    ok, error_resp, status = require_admin()
    if not ok:
        return error_resp, status

    operations = [
        {'value': 'login_success', 'label': '登录成功'},
        {'value': 'login_failed', 'label': '登录失败'},
        {'value': 'logout', 'label': '登出'},
        {'value': 'create_content', 'label': '发布内容'},
        {'value': 'create_comment', 'label': '发布评论'},
        {'value': 'update_profile', 'label': '更新资料'},
        {'value': 'upload_avatar', 'label': '上传头像'},
        {'value': 'change_password', 'label': '修改密码'},
        {'value': 'delete_content', 'label': '删除内容'},
        {'value': 'delete_comment', 'label': '删除评论'},
    ]

    return jsonify({'code': 200, 'data': operations})


OPERATION_LABELS = {
    'login_success': '登录成功',
    'login_failed': '登录失败',
    'logout': '登出',
    'create_content': '发布内容',
    'create_comment': '发布评论',
    'update_profile': '更新资料',
    'upload_avatar': '上传头像',
    'change_password': '修改密码',
    'delete_content': '删除内容',
    'delete_comment': '删除评论',
}


@audit_bp.route('/api/audit/logs/export', methods=['GET'])
def export_audit_logs():
    """导出审计日志为CSV（仅管理员）"""
    ok, error_resp, status = require_admin()
    if not ok:
        return error_resp, status

    operation = request.args.get('operation', '').strip()
    user_id = request.args.get('user_id', type=int)
    username = request.args.get('username', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()

    logs = get_operation_logs_for_export(
        operation=operation if operation else None,
        user_id=user_id if user_id else None,
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None
    )

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)
    
    writer.writerow(['ID', '时间', '用户名', '用户ID', '操作类型', '详情', 'IP地址', 'User-Agent'])
    
    for log in logs:
        detail = log.get('detail', '')
        if detail:
            try:
                import json
                detail_obj = json.loads(detail) if isinstance(detail, str) else detail
                detail = json.dumps(detail_obj, ensure_ascii=False)
            except:
                pass
        
        writer.writerow([
            log.get('id', ''),
            log.get('created_at', ''),
            log.get('username', ''),
            log.get('user_id', ''),
            OPERATION_LABELS.get(log.get('operation', ''), log.get('operation', '')),
            detail,
            log.get('ip_address', ''),
            log.get('user_agent', '')
        ])
    
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=audit_logs_{start_date or "all"}_{end_date or "all"}.csv'
    
    return response

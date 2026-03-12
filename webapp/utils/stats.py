"""
统计工具模块
"""
from datetime import datetime, date
from database import get_db


def record_visit():
    """记录访问次数"""
    today = date.today()
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO visits (visit_date, visit_count) VALUES (%s, 1) "
                "ON DUPLICATE KEY UPDATE visit_count = visit_count + 1",
                (today,)
            )


def get_visit_stats():
    """获取访问统计"""
    today = date.today()
    # 获取本月第一天
    first_day_of_month = today.replace(day=1)

    with get_db() as conn:
        with conn.cursor() as cursor:
            # 今日访问
            cursor.execute(
                "SELECT visit_count FROM visits WHERE visit_date = %s",
                (today,)
            )
            today_result = cursor.fetchone()
            today_count = today_result['visit_count'] if today_result else 0

            # 本月访问
            cursor.execute(
                "SELECT SUM(visit_count) as month_count FROM visits WHERE visit_date >= %s",
                (first_day_of_month,)
            )
            month_result = cursor.fetchone()
            month_count = month_result['month_count'] if month_result and month_result['month_count'] else 0

            # 总访问
            cursor.execute("SELECT SUM(visit_count) as total_count FROM visits")
            total_result = cursor.fetchone()
            total_count = total_result['total_count'] if total_result and total_result['total_count'] else 0

            return {
                'today': today_count,
                'month': month_count,
                'total': total_count
            }


def get_content_like_count(content_id):
    """获取内容的点赞总数"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) as count FROM likes WHERE content_id = %s",
                (content_id,)
            )
            result = cursor.fetchone()
            return result['count'] if result else 0


def check_user_liked_today(content_id, user_id):
    """检查用户今天是否已点赞"""
    today = date.today()
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM likes WHERE content_id = %s AND user_id = %s AND created_at = %s",
                (content_id, user_id, today)
            )
            return cursor.fetchone() is not None


def add_like(content_id, user_id):
    """添加点赞"""
    today = date.today()
    with get_db() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    "INSERT INTO likes (content_id, user_id, created_at) VALUES (%s, %s, %s)",
                    (content_id, user_id, today)
                )
                return True
            except Exception:
                return False


def remove_like(content_id, user_id):
    """移除点赞"""
    today = date.today()
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM likes WHERE content_id = %s AND user_id = %s AND created_at = %s",
                (content_id, user_id, today)
            )
            return cursor.rowcount > 0

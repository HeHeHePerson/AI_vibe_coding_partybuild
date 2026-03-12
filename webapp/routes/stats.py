"""
统计路由模块
"""
from flask import Blueprint, jsonify
from webapp.utils.stats import record_visit, get_visit_stats, get_content_like_count

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/api/stats/visits', methods=['GET'])
def get_visits():
    """获取访问统计"""
    stats = get_visit_stats()
    return jsonify({'code': 200, 'data': stats})


@stats_bp.route('/api/stats/record', methods=['POST'])
def record_visit_count():
    """记录访问"""
    record_visit()
    return jsonify({'code': 200})


@stats_bp.route('/api/stats/content/<int:content_id>/likes', methods=['GET'])
def get_content_likes(content_id):
    """获取内容的点赞数"""
    count = get_content_like_count(content_id)
    return jsonify({'code': 200, 'data': {'count': count}})

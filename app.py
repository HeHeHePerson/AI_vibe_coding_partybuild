"""
智慧党建系统 - Flask应用主入口

功能：
- 用户认证与会话管理（3小时无操作超时）
- 页面路由
- 请求日志记录
- 蓝图注册
"""
import os
import time
import logging
from datetime import datetime
from flask import Flask, render_template, session, redirect, url_for, request, g, current_app
from config import (
    SECRET_KEY, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME,
    UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH
)
from database import init_db, get_db
from webapp.utils.stats import record_visit
from webapp.utils.csrf import generate_csrf_token, validate_csrf_token, get_csrf_token_from_request

SESSION_TIMEOUT = 3 * 60 * 60  # 3小时（秒）

# 创建Flask应用
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
application = Flask(__name__,
    template_folder=os.path.join(BASE_DIR, 'webapp', 'templates'),
    static_folder=os.path.join(BASE_DIR, 'webapp', 'static')
)
app = application
app.secret_key = SECRET_KEY

# 配置日志
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'access.log')

# 配置日志记录器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 注册蓝图
from webapp.routes.auth import auth_bp
from webapp.routes.users import users_bp
from webapp.routes.contents import contents_bp
from webapp.routes.stats import stats_bp
from webapp.routes.notices import notices_bp
from webapp.routes.profile import profile_bp
from webapp.routes.categories import categories_bp
from webapp.routes.audit import audit_bp
from webapp.routes.party_knowledge import party_knowledge_bp
from webapp.routes.party_activities import party_activities_bp
from webapp.routes.party_fees import party_fees_bp
from webapp.routes.party_integral import party_integral_bp

app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(contents_bp)
app.register_blueprint(stats_bp)
app.register_blueprint(notices_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(audit_bp)
app.register_blueprint(party_knowledge_bp)
app.register_blueprint(party_activities_bp)
app.register_blueprint(party_fees_bp)
app.register_blueprint(party_integral_bp)


# 请求日志记录中间件
@app.before_request
def check_session_timeout():
    """检查session超时，3小时无操作则清除session"""
    if session.get('user_id'):
        last_activity = session.get('last_activity')
        if last_activity:
            if time.time() - last_activity > SESSION_TIMEOUT:
                session.clear()
                return redirect(url_for('login_page'))
        session['last_activity'] = time.time()


@app.before_request
def log_request_info():
    """记录请求开始时间"""
    g.request_start_time = datetime.now()


@app.after_request
def log_response_info(response):
    """记录请求日志"""
    # 排除静态文件请求
    if request.path.startswith('/static'):
        return response

    # 获取请求信息
    method = request.method
    path = request.path
    remote_addr = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')

    # 获取请求体（仅记录非敏感信息）
    request_data = ""
    if method in ['POST', 'PUT', 'DELETE']:
        # 记录请求参数，但隐藏敏感字段
        form = request.form.to_dict()
        json_data = request.get_json(silent=True)
        if json_data:
            # 隐藏密码等敏感信息
            sanitized = {}
            for k, v in json_data.items():
                if k.lower() in ['password', 'token', 'secret', 'key']:
                    sanitized[k] = '***'
                else:
                    sanitized[k] = str(v)[:200]  # 限制长度
            request_data = f" | Body: {sanitized}"
        elif form:
            sanitized = {}
            for k, v in form.items():
                if k.lower() in ['password', 'token', 'secret', 'key']:
                    sanitized[k] = '***'
                else:
                    sanitized[k] = str(v)[:200]
            request_data = f" | Form: {sanitized}"

    # 获取用户信息
    user_id = session.get('user_id')
    username = session.get('user', {}).get('username', 'Anonymous')
    user_info = f" | User: {username}(ID:{user_id})" if user_id else ""

    # 计算请求处理时间
    if hasattr(g, 'request_start_time'):
        duration = (datetime.now() - g.request_start_time).total_seconds()
        duration_info = f" | Duration: {duration:.3f}s"
    else:
        duration_info = ""

    # 记录日志
    log_message = f"{remote_addr} - {method} {path}{user_info}{request_data} | Status: {response.status_code}{duration_info}"
    logger.info(log_message)

    return response


# 路由：首页（党建之声）
@app.route('/')
def index():
    """首页：党建之声内容列表"""
    # 记录访问
    try:
        record_visit()
    except Exception:
        pass  # 忽略访问记录错误

    return render_template('index.html')


# 路由：登录页面
@app.route('/login')
def login_page():
    """登录页面"""
    if session.get('user'):
        return redirect(url_for('index'))
    return render_template('login.html')


# 路由：注册页面
@app.route('/register')
def register_page():
    """注册页面"""
    if session.get('user'):
        return redirect(url_for('index'))
    return render_template('register.html')


# 路由：创建内容页面
@app.route('/create')
def create_page():
    """创建内容页面"""
    if not session.get('user'):
        return redirect(url_for('login_page'))
    return render_template('create.html')


# 路由：内容详情页面
@app.route('/content/<int:content_id>')
def content_page(content_id):
    """内容详情页面"""
    return render_template('content.html', content_id=content_id, current_user=session.get('user'))


# 路由：用户管理页面（管理员）
@app.route('/manage')
def manage_page():
    """用户管理页面"""
    user = session.get('user')
    if not user:
        return redirect(url_for('login_page'))
    if user.get('role') != 'admin':
        return redirect(url_for('index'))
    return render_template('manage.html')


# 路由：公告管理页面（管理员）
@app.route('/notices')
def notices_page():
    """公告管理页面"""
    user = session.get('user')
    if not user:
        return redirect(url_for('login_page'))
    if user.get('role') != 'admin':
        return redirect(url_for('index'))
    return render_template('notices.html')


# 路由：用户审计日志页面（管理员）
@app.route('/audit')
def audit_page():
    """用户审计日志页面"""
    user = session.get('user')
    if not user:
        return redirect(url_for('login_page'))
    if user.get('role') != 'admin':
        return redirect(url_for('index'))
    return render_template('audit.html')


# 路由：个人资料页面
@app.route('/profile')
def profile_page():
    """个人资料页面"""
    user = session.get('user')
    if not user:
        return redirect(url_for('login_page'))
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT id, username, role, avatar, bio, email, phone, created_at, last_login_at
                   FROM users WHERE id = %s""",
                (user_id,)
            )
            db_user = cursor.fetchone()
            if not db_user:
                return redirect(url_for('login_page'))
            current_user_with_avatar = {
                'id': db_user['id'],
                'username': db_user['username'],
                'role': db_user['role'],
                'avatar': db_user['avatar'],
                'bio': db_user['bio'],
                'email': db_user['email'],
                'phone': db_user['phone'],
                'created_at': db_user['created_at'],
                'last_login_at': db_user['last_login_at']
            }
    return render_template('profile.html', current_user=current_user_with_avatar)


# 路由：党建知识页面
@app.route('/party/knowledge')
def party_knowledge_page():
    """党建知识页面"""
    return render_template('party_knowledge.html')


# 路由：党建知识详情页面
@app.route('/party/knowledge/<int:knowledge_id>')
def party_knowledge_detail_page(knowledge_id):
    """党建知识详情页面"""
    return render_template('party_knowledge_detail.html', knowledge_id=knowledge_id)


# 路由：组织活动页面
@app.route('/party/activities')
def party_activities_page():
    """组织活动页面"""
    return render_template('party_activities.html')


# 路由：党费缴纳页面
@app.route('/party/fees')
def party_fees_page():
    """党费缴纳页面"""
    return render_template('party_fees.html')


# 路由：党员积分页面
@app.route('/party/integral')
def party_integral_page():
    """党员积分页面"""
    return render_template('party_integral.html')


@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """提供上传文件的访问服务"""
    from flask import send_from_directory
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filename)


# 错误处理
@app.errorhandler(404)
def not_found(e):
    """404错误处理"""
    return render_template('error.html', error_code=404, message='页面不存在'), 404


@app.errorhandler(500)
def server_error(e):
    """500错误处理"""
    return render_template('error.html', error_code=500, message='服务器内部错误'), 500


# 初始化数据库连接测试
def init_app():
    """初始化应用"""
    try:
        init_db()
        print("数据库连接成功!")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        print("请确保MySQL已启动并配置正确!")


@app.context_processor
def inject_csrf_token():
    """向模板注入CSRF令牌"""
    return dict(csrf_token=generate_csrf_token())


CSRF_PROTECTED_METHODS = ['POST', 'PUT', 'DELETE', 'PATCH']


@app.before_request
def csrf_protect():
    """CSRF保护中间件"""
    if request.method in CSRF_PROTECTED_METHODS:
        token = get_csrf_token_from_request()
        if not token or not validate_csrf_token(token):
            from flask import jsonify
            return jsonify({'code': 403, 'message': 'CSRF令牌验证失败，请刷新页面后重试'}), 403


if __name__ == '__main__':
    init_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

"""
智慧党建系统 - Flask应用主入口
"""
import os
from flask import Flask, render_template, session, redirect, url_for
from config import (
    SECRET_KEY, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME,
    UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH
)
from database import init_db
from webapp.utils.stats import record_visit

# 创建Flask应用
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
application = Flask(__name__,
    template_folder=os.path.join(BASE_DIR, 'webapp', 'templates'),
    static_folder=os.path.join(BASE_DIR, 'webapp', 'static')
)
app = application
app.secret_key = SECRET_KEY

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

app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(contents_bp)
app.register_blueprint(stats_bp)


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


if __name__ == '__main__':
    init_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

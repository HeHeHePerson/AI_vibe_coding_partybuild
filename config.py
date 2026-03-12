"""
智慧党建系统配置文件

配置项说明：
- 数据库配置：通过环境变量或默认值配置，支持MySQL连接参数
- 文件上传：允许的图片和文档格式白名单，防止上传恶意文件
- Session：安全相关的Cookie配置，防止XSS和CSRF攻击

环境变量说明：
- SECRET_KEY: Session加密密钥
- DB_HOST: 数据库主机地址
- DB_PORT: 数据库端口
- DB_USER: 数据库用户名
- DB_PASSWORD: 数据库密码
- DB_NAME: 数据库名称
"""
import os

# =============================================================================
# 基础配置
# =============================================================================

# Session密钥，用于加密Session数据
# 生产环境建议使用随机字符串，可通过环境变量 SECRET_KEY 设置
SECRET_KEY = os.environ.get('SECRET_KEY', 'party-building-secret-key-2024')

# =============================================================================
# 数据库配置
# =============================================================================

# 数据库主机地址，默认localhost，可通过环境变量 DB_HOST 设置
DB_HOST = os.environ.get('DB_HOST', 'localhost')

# 数据库端口，默认3306（MySQL默认端口），可通过环境变量 DB_PORT 设置
DB_PORT = int(os.environ.get('DB_PORT', 3306))

# 数据库用户名，默认root，可通过环境变量 DB_USER 设置
DB_USER = os.environ.get('DB_USER', 'root')

# 数据库密码，默认root，可通过环境变量 DB_PASSWORD 设置
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'root')

# 数据库名称，默认party_building，可通过环境变量 DB_NAME 设置
DB_NAME = os.environ.get('DB_NAME', 'party_building')

# =============================================================================
# 文件上传配置
# =============================================================================

# 项目根目录（自动获取当前文件所在目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 上传文件保存目录（相对于项目根目录的webapp/uploads目录）
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'webapp', 'uploads')

# 允许上传的文件扩展名白名单
# 安全说明：只允许常见的图片和文档格式，禁止可执行脚本（如jsp, py, asp, php等）
# 这样做可以防止恶意用户上传webshell等危险文件
ALLOWED_EXTENSIONS = {
    # 图片格式
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp',
    # Word文档
    'doc', 'docx',
    # Excel表格
    'xls', 'xlsx',
    # PowerPoint演示文稿
    'ppt', 'pptx',
    # PDF
    'pdf',
    # 文本文件
    'txt'
}

# 上传文件大小限制，默认16MB
# 超过此大小的文件上传请求将被拒绝
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# =============================================================================
# Session配置（安全相关）
# =============================================================================

# 防止XSS攻击：设置Cookie为HttpOnly，客户端JavaScript无法读取
# 这可以防止攻击者通过XSS窃取用户的Session ID
SESSION_COOKIE_HTTPONLY = True

# 防止CSRF攻击：设置Cookie的SameSite属性为Lax
# 这可以防止跨站请求伪造攻击
SESSION_COOKIE_SAMESITE = 'Lax'

# Session有效期，默认24小时（单位：秒）
# 用户登录后24小时内无需重新登录
PERMANENT_SESSION_LIFETIME = 3600 * 24  # 24小时

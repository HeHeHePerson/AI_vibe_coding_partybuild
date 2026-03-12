"""
安全工具模块
提供SQL注入防护、XSS防护等功能
"""
import html
import re


def escape_html(text):
    """对文本进行HTML转义，防止XSS攻击"""
    if text is None:
        return ''
    return html.escape(str(text))


def sanitize_filename(filename):
    """清理文件名，移除危险字符"""
    # 移除路径分隔符和危险字符
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    return filename


def validate_username(username):
    """验证用户名格式"""
    if not username or len(username) < 2 or len(username) > 50:
        return False, "用户名长度需在2-50个字符之间"
    if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', username):
        return False, "用户名只能包含字母、数字、下划线和中文"
    return True, None


def validate_password(password):
    """验证密码强度"""
    if not password or len(password) < 6:
        return False, "密码长度需至少6个字符"
    return True, None


def validate_title(title):
    """验证标题"""
    if not title or len(title.strip()) == 0:
        return False, "标题不能为空"
    if len(title) > 255:
        return False, "标题长度不能超过255个字符"
    return True, None


def validate_content(content):
    """验证内容"""
    if not content or len(content.strip()) == 0:
        return False, "内容不能为空"
    return True, None

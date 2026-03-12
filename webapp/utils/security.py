"""
安全工具模块

功能：
- SQL注入防护（通过参数化查询）
- XSS防护（HTML转义）
- 输入验证（用户名、密码、标题、内容）

使用说明：
- 所有用户输入都应该先经过验证函数验证
- 所有输出到HTML的内容都应该使用escape_html转义
- 数据库查询使用参数化查询（已在各路由模块中实现）
"""
import html
import re


def escape_html(text):
    """
    对文本进行HTML转义，防止XSS攻击

    参数:
        text: 要转义的文本

    返回:
        str: 转义后的文本，特殊字符会被转换为HTML实体
    """
    if text is None:
        return ''
    return html.escape(str(text))


def sanitize_filename(filename):
    """
    清理文件名，移除危险字符

    安全说明：移除路径分隔符等可能导致目录穿越的字符

    参数:
        filename: 原始文件名

    返回:
        str: 清理后的文件名
    """
    # 移除路径分隔符和危险字符，只保留字母、数字、下划线、连字符和点
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    return filename


def validate_username(username):
    """
    验证用户名格式

    规则：
    - 长度：2-50个字符
    - 字符：只能包含字母、数字、下划线和中文

    参数:
        username: 用户名

    返回:
        tuple: (是否有效, 错误消息)
    """
    if not username or len(username) < 2 or len(username) > 50:
        return False, "用户名长度需在2-50个字符之间"
    if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', username):
        return False, "用户名只能包含字母、数字、下划线和中文"
    return True, None


def validate_password(password):
    """
    验证密码强度

    规则：至少6个字符

    参数:
        password: 密码

    返回:
        tuple: (是否有效, 错误消息)
    """
    if not password or len(password) < 6:
        return False, "密码长度需至少6个字符"
    return True, None


def validate_title(title):
    """
    验证标题

    规则：
    - 不能为空
    - 长度不能超过255个字符

    参数:
        title: 标题

    返回:
        tuple: (是否有效, 错误消息)
    """
    if not title or len(title.strip()) == 0:
        return False, "标题不能为空"
    if len(title) > 255:
        return False, "标题长度不能超过255个字符"
    return True, None


def validate_content(content):
    """
    验证内容

    规则：
    - 不能为空
    - 长度不能超过100000个字符（防止大文本攻击）

    参数:
        content: 内容

    返回:
        tuple: (是否有效, 错误消息)
    """
    if not content or len(content.strip()) == 0:
        return False, "内容不能为空"
    if len(content) > 100000:
        return False, "内容过长，请精简后再提交"
    return True, None

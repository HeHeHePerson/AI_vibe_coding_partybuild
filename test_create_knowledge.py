import requests
import re

# 测试党建知识新建功能
session = requests.Session()

# 1. 获取登录页面，提取CSRF令牌
login_page = session.get('http://localhost:5001/login')
csrf_token = re.search(r'value="([0-9a-f]{64})"', login_page.text).group(1)
print(f"CSRF Token: {csrf_token}")

# 2. 获取验证码
captcha_response = session.get('http://localhost:5001/api/auth/captcha')
captcha_data = captcha_response.json()
captcha_expression = captcha_data['data']['expression']
print(f"Captcha Expression: {captcha_expression}")

# 3. 计算验证码结果
try:
    # 移除可能的特殊字符，只保留数字和运算符
    captcha_expression = captcha_expression.replace('×', '*')
    # 移除 "= ?" 部分
    captcha_expression = captcha_expression.split('=')[0].strip()
    captcha_result = eval(captcha_expression)
    print(f"Captcha Result: {captcha_result}")
except Exception as e:
    print(f"Error calculating captcha: {e}")
    captcha_result = 0

# 4. 登录（使用普通用户）
login_data = {
    'username': 'test002',
    'password': 'Test002!',
    'captcha': str(captcha_result)
}

login_headers = {
    'Content-Type': 'application/json',
    'X-CSRF-Token': csrf_token
}

login_response = session.post('http://localhost:5001/api/auth/login', json=login_data, headers=login_headers)
print(f"Login Response: {login_response.json()}")

# 5. 测试创建党建知识
knowledge_data = {
    'title': '测试党建知识',
    'category': '测试分类',
    'content': '这是测试党建知识的内容'
}

knowledge_response = session.post('http://localhost:5001/api/party/knowledge', json=knowledge_data, headers=login_headers)
print(f"Create Knowledge Response: {knowledge_response.json()}")

# 6. 测试获取党建知识列表（普通用户）
list_response = session.get('http://localhost:5001/api/party/knowledge')
print(f"Knowledge List Response: {list_response.json()}")

# 7. 登出
session.get('http://localhost:5001/api/auth/logout')

# 8. 管理员登录
login_data_admin = {
    'username': 'aqjsb',
    'password': 'Icbc1234!',
    'captcha': str(captcha_result)
}

login_response_admin = session.post('http://localhost:5001/api/auth/login', json=login_data_admin, headers=login_headers)
print(f"Admin Login Response: {login_response_admin.json()}")

# 9. 测试获取党建知识列表（管理员，包含待审核内容）
list_admin_response = session.get('http://localhost:5001/api/party/knowledge?admin=true')
print(f"Admin Knowledge List Response: {list_admin_response.json()}")

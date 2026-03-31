import requests
import re
from datetime import datetime, timedelta

# 测试组织活动新建功能
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

# 5. 测试创建组织活动
# 设置活动时间
start_time = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
end_time = (datetime.now() + timedelta(days=1, hours=2)).strftime('%Y-%m-%dT%H:%M')

activity_data = {
    'title': '测试组织活动',
    'content': '这是测试组织活动的内容',
    'start_time': start_time,
    'end_time': end_time,
    'location': '测试地点',
    'organizer': '测试组织者',
    'max_participants': 50
}

activity_response = session.post('http://localhost:5001/api/party/activities', json=activity_data, headers=login_headers)
print(f"Create Activity Response: {activity_response.json()}")

# 6. 测试获取组织活动列表（普通用户）
list_response = session.get('http://localhost:5001/api/party/activities')
print(f"Activity List Response: {list_response.json()}")

# 7. 登出
session.get('http://localhost:5001/api/auth/logout')

# 8. 管理员登录
# 获取新的验证码
captcha_response = session.get('http://localhost:5001/api/auth/captcha')
captcha_data = captcha_response.json()
captcha_expression = captcha_data['data']['expression']
print(f"New Captcha Expression: {captcha_expression}")

# 计算新的验证码结果
try:
    captcha_expression = captcha_expression.replace('×', '*')
    captcha_expression = captcha_expression.split('=')[0].strip()
    captcha_result = eval(captcha_expression)
    print(f"New Captcha Result: {captcha_result}")
except Exception as e:
    print(f"Error calculating captcha: {e}")
    captcha_result = 0

login_data_admin = {
    'username': 'aqjsb',
    'password': 'Icbc1234!',
    'captcha': str(captcha_result)
}

login_response_admin = session.post('http://localhost:5001/api/auth/login', json=login_data_admin, headers=login_headers)
print(f"Admin Login Response: {login_response_admin.json()}")

# 9. 测试获取组织活动列表（管理员，包含待审核内容）
list_admin_response = session.get('http://localhost:5001/api/party/activities?admin=true')
print(f"Admin Activity List Response: {list_admin_response.json()}")

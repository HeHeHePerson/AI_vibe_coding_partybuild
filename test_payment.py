import requests
import re

# 测试党费缴纳功能
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

# 4. 登录
login_data = {
    'username': 'admin',
    'password': 'Admin123!',
    'captcha': str(captcha_result)
}

login_headers = {
    'Content-Type': 'application/json',
    'X-CSRF-Token': csrf_token
}

login_response = session.post('http://localhost:5001/api/auth/login', json=login_data, headers=login_headers)
print(f"Login Response: {login_response.json()}")

# 5. 测试缴费功能
payment_data = {
    'amount': 100,
    'payment_method': 'alipay',
    'remark': '测试缴费'
}

payment_headers = {
    'Content-Type': 'application/json',
    'X-CSRF-Token': csrf_token
}

payment_response = session.post('http://localhost:5001/api/party/fees/pay', json=payment_data, headers=payment_headers)
print(f"Payment Response: {payment_response.json()}")

import requests

# 测试党费缴纳API
session = requests.Session()

# 1. 直接测试缴费API，使用用户ID 1
payment_data = {
    'amount': 100,
    'payment_method': 'alipay',
    'remark': '测试缴费'
}

# 设置用户ID到session中（模拟登录）
session.cookies.set('user_id', '1')
session.cookies.set('user', '{}')

payment_response = session.post('http://localhost:5001/api/party/fees/pay', json=payment_data)
print(f"Payment Response: {payment_response.json()}")
print(f"Status Code: {payment_response.status_code}")

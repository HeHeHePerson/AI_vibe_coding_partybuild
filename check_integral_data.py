import pymysql
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

# 连接数据库
conn = pymysql.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)

# 创建游标
cursor = conn.cursor()

# 查询积分记录数据
try:
    cursor.execute("SELECT id, points, reason, type, created_at FROM party_integral LIMIT 10")
    result = cursor.fetchall()
    print("积分记录数据:")
    for row in result:
        print(row)
except Exception as e:
    print(f"Error: {e}")
finally:
    # 关闭连接
    cursor.close()
    conn.close()

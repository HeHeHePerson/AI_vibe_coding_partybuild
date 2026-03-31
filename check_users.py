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

# 查询用户表
try:
    cursor.execute("SELECT id, username, password FROM users")
    result = cursor.fetchall()
    print("Users:")
    for row in result:
        print(f"ID: {row[0]}, Username: {row[1]}, Password: {row[2]}")
except Exception as e:
    print(f"Error: {e}")
finally:
    # 关闭连接
    cursor.close()
    conn.close()

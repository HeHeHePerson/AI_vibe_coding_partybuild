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

# 检查用户表结构
try:
    cursor.execute("SHOW CREATE TABLE users")
    result = cursor.fetchone()
    print(result[1])
    
    # 查询用户数据
    cursor.execute("SELECT * FROM users")
    result = cursor.fetchall()
    print("\nUsers data:")
    for row in result:
        print(row)
except Exception as e:
    print(f"Error: {e}")
finally:
    # 关闭连接
    cursor.close()
    conn.close()

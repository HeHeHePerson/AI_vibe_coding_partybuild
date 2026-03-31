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

try:
    # 为党建知识表添加审核状态字段
    cursor.execute("ALTER TABLE party_knowledge ADD COLUMN `status` enum('pending','approved','rejected') DEFAULT 'approved' COMMENT '审核状态'")
    print("党建知识表添加审核状态字段成功")
    
    # 为组织活动表添加审核状态字段
    cursor.execute("ALTER TABLE party_activities ADD COLUMN `review_status` enum('pending','approved','rejected') DEFAULT 'approved' COMMENT '审核状态'")
    print("组织活动表添加审核状态字段成功")
    
    # 提交事务
    conn.commit()
    print("所有操作执行成功")
except Exception as e:
    print(f"错误: {e}")
    conn.rollback()
finally:
    # 关闭连接
    cursor.close()
    conn.close()

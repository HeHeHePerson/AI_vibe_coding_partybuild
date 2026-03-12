"""
数据库连接模块
使用PyMySQL实现数据库操作
"""
import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


def get_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',
        cursorclass=DictCursor
    )


@contextmanager
def get_db():
    """数据库上下文管理器，自动管理连接和事务"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_db():
    """初始化数据库连接池（测试连接）"""
    conn = get_connection()
    conn.close()
    return True

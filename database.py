"""
数据库连接模块

功能说明：
- 提供MySQL数据库连接管理
- 使用PyMySQL作为数据库驱动
- 支持上下文管理器自动管理事务

使用方法：
    from database import get_db

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            result = cursor.fetchall()
    # 事务自动提交，连接自动关闭

注意事项：
- 所有数据库操作必须使用参数化查询，防止SQL注入
- 连接使用完成后会自动关闭，无需手动关闭
- 事务会自动提交，异常会自动回滚
"""
import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


def get_connection():
    """
    获取数据库连接

    返回:
        pymysql.Connection: 数据库连接对象

    配置说明:
        - charset='utf8mb4': 支持完整的中文字符和emoji
        - cursorclass=DictCursor: 查询结果以字典形式返回，键为字段名
        - init_command="SET time_zone = '+8:00'": 设置时区为东八区，确保时间正确
    """
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',
        cursorclass=DictCursor,
        init_command="SET time_zone = '+8:00'"  # 设置时区为东八区
    )


@contextmanager
def get_db():
    """
    数据库上下文管理器

    功能:
    - 自动获取数据库连接
    - 自动提交事务（正常情况下）
    - 自动回滚事务（异常情况下）
    - 自动关闭连接

    使用示例:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()

    异常处理:
        - 如果代码块中发生异常，事务会自动回滚
        - 连接会在finally块中确保关闭
    """
    # 获取数据库连接
    conn = get_connection()
    try:
        # yield将控制权交给调用者
        yield conn
        # 如果没有异常，提交事务
        conn.commit()
    except Exception as e:
        # 如果发生异常，回滚事务，保证数据一致性
        conn.rollback()
        # 重新抛出异常，让调用者知道发生了错误
        raise e
    finally:
        # 确保连接被关闭，释放资源
        conn.close()


def init_db():
    """
    初始化数据库连接（测试连接）

    用于:
    - 应用启动时测试数据库连接是否正常
    - 验证数据库配置是否正确

    返回:
        bool: 连接成功返回True，失败会抛出异常

    异常:
        如果连接失败，会抛出pymysql相关异常
    """
    conn = get_connection()
    conn.close()
    return True

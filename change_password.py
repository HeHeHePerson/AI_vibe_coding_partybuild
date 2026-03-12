"""
修改用户密码脚本

用途：
- 创建管理员账号
- 重置用户密码

使用方法：
    python change_password.py <username> <password>

示例：
    python change_password.py admin admin123    # 修改admin密码为admin123
    python change_password.py newadmin pass123 # 创建新用户newadmin（如果不存在）
"""
import sys
import os
import argparse

# 添加项目根目录到Python路径，确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webapp.utils.auth import update_user_password, get_user_by_username


def change_password(username, new_password):
    """
    修改指定用户的密码

    参数:
        username: 用户名
        new_password: 新密码（明文，会自动加密存储）

    返回:
        bool: 密码修改成功返回True，否则返回False
    """
    # 根据用户名查询用户是否存在
    user = get_user_by_username(username)
    if not user:
        print(f"错误: 用户 '{username}' 不存在")
        return False

    # 调用auth模块更新密码（密码会以bcrypt加密后存储）
    if update_user_password(user['id'], new_password):
        print(f"成功: 用户 '{username}' 的密码已更新")
        return True
    else:
        print(f"错误: 密码更新失败")
        return False


if __name__ == '__main__':
    # 命令行参数解析
    parser = argparse.ArgumentParser(
        description='修改用户密码',
        epilog='示例: python change_password.py admin admin123'
    )
    # 用户名参数
    parser.add_argument(
        'username',
        help='要修改密码的用户名'
    )
    # 新密码参数
    parser.add_argument(
        'password',
        help='新密码（明文，会自动加密存储）'
    )

    # 解析命令行参数
    args = parser.parse_args()

    # 执行密码修改
    success = change_password(args.username, args.password)

    # 根据执行结果返回退出码
    # 0表示成功，1表示失败
    sys.exit(0 if success else 1)

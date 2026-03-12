"""
修改用户密码脚本
"""
import sys
sys.path.insert(0, '/workspace')

import argparse
from webapp.utils.auth import update_user_password, get_user_by_id, get_user_by_username


def change_password(username, new_password):
    """修改用户密码"""
    # 获取用户
    user = get_user_by_username(username)
    if not user:
        print(f"错误: 用户 '{username}' 不存在")
        return False

    # 更新密码
    if update_user_password(user['id'], new_password):
        print(f"成功: 用户 '{username}' 的密码已更新")
        return True
    else:
        print(f"错误: 密码更新失败")
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='修改用户密码')
    parser.add_argument('username', help='用户名')
    parser.add_argument('password', help='新密码')

    args = parser.parse_args()

    success = change_password(args.username, args.password)
    sys.exit(0 if success else 1)

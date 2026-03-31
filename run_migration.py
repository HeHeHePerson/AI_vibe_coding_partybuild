#!/usr/bin/env python3
"""
数据库迁移脚本

功能：执行党建园地模块的数据库迁移
使用：python run_migration.py
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db

def run_migration():
    """
    执行数据库迁移
    """
    print("开始执行数据库迁移...")
    
    # 读取迁移脚本
    migration_file = os.path.join(os.path.dirname(__file__), 'docs', 'migration_party_garden.sql')
    
    if not os.path.exists(migration_file):
        print(f"错误：迁移脚本文件不存在: {migration_file}")
        return False
    
    print(f"读取迁移脚本: {migration_file}")
    
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
    except Exception as e:
        print(f"错误：读取迁移脚本失败: {e}")
        return False
    
    # 执行SQL脚本
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                # 分割SQL语句并执行
                sql_statements = sql_script.split(';')
                
                for stmt in sql_statements:
                    stmt = stmt.strip()
                    if stmt:
                        try:
                            cursor.execute(stmt)
                            print(f"执行SQL: {stmt[:100]}...")
                        except Exception as e:
                            print(f"警告：执行SQL失败: {e}")
                            print(f"SQL语句: {stmt}")
                            # 继续执行其他语句
                            continue
        
        print("数据库迁移执行完成！")
        return True
    except Exception as e:
        print(f"错误：数据库迁移失败: {e}")
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)

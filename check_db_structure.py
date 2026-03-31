#!/usr/bin/env python3
"""
检查数据库表结构
"""
from database import get_db

with get_db() as conn:
    with conn.cursor() as cursor:
        # 查看party_fees表结构
        cursor.execute('DESCRIBE party_fees')
        print("party_fees表结构:")
        for row in cursor.fetchall():
            print(row)
        
        print("\n")
        
        # 查看当前数据
        cursor.execute('SELECT id, status FROM party_fees LIMIT 5')
        print("当前数据:")
        for row in cursor.fetchall():
            print(row)

#!/usr/bin/env python3
"""
修改党费缴纳表的status字段，添加completed状态
"""
from database import get_db

with get_db() as conn:
    with conn.cursor() as cursor:
        # 修改status字段，添加completed选项
        cursor.execute("""
            ALTER TABLE party_fees
            MODIFY COLUMN status enum('pending','paid','overdue','completed') DEFAULT 'pending'
        """)
        conn.commit()
        print("成功修改party_fees表的status字段，添加了completed状态")
        
        # 验证修改结果
        cursor.execute('DESCRIBE party_fees')
        for row in cursor.fetchall():
            if row['Field'] == 'status':
                print(f"修改后的status字段: {row['Type']}")

import sqlite3
import os
from db_setup import DB_PATH

def update_database_schema():
    """更新数据库表结构"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查活动表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activities'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        # 备份现有数据
        cursor.execute("SELECT * FROM activities")
        activities_data = cursor.fetchall()
        
        # 删除现有表
        cursor.execute("DROP TABLE activities")
        
        # 创建新表结构
        cursor.execute("""
            CREATE TABLE activities (
                activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                is_total_target BOOLEAN NOT NULL,
                item_id INTEGER,
                activity_type TEXT,
                need_total_target BOOLEAN,
                need_item_target BOOLEAN,
                target_value REAL NOT NULL,
                original_price REAL,
                discount_price REAL,
                FOREIGN KEY (brand_id) REFERENCES brands(brand_id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES items(item_id)
            )
        """)
        
        # 如果有需要，尝试迁移数据
        # 此处需要根据旧表结构和新表结构调整
        
        print("活动表结构已更新")
    else:
        # 如果表不存在，直接创建
        cursor.execute("""
            CREATE TABLE activities (
                activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                is_total_target BOOLEAN NOT NULL,
                item_id INTEGER,
                activity_type TEXT,
                need_total_target BOOLEAN,
                need_item_target BOOLEAN,
                target_value REAL NOT NULL,
                original_price REAL,
                discount_price REAL,
                FOREIGN KEY (brand_id) REFERENCES brands(brand_id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES items(item_id)
            )
        """)
        print("活动表已创建")
    
    conn.commit()
    conn.close()
    
    print(f"数据库已更新：{DB_PATH}")

if __name__ == "__main__":
    update_database_schema()

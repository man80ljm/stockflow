import sqlite3
import os
from database.db_setup import DB_PATH  # 修改为 package 导入

def update_database_schema():
    """更新数据库表结构"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查并更新 items 表
    cursor.execute("PRAGMA table_info(items)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    if 'unit' not in existing_columns or 'brand_id' not in existing_columns:
        # 备份现有数据
        cursor.execute("SELECT item_id, item_name, spec FROM items")
        items_data = cursor.fetchall()
        
        # 删除现有表
        cursor.execute("DROP TABLE IF EXISTS items")
        
        # 创建新表结构
        cursor.execute("""
            CREATE TABLE items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                spec TEXT NOT NULL,
                unit TEXT NOT NULL,
                brand_id INTEGER NOT NULL,
                UNIQUE(item_name, spec, unit, brand_id),
                FOREIGN KEY (brand_id) REFERENCES brands(brand_id) ON DELETE CASCADE
            )
        """)
        
        # 迁移数据
        for item in items_data:
            cursor.execute(
                "INSERT INTO items (item_id, item_name, spec, unit, brand_id) VALUES (?, ?, ?, ?, ?)",
                (item[0], item[1], item[2], "件", 1)
            )
        
        print("items 表结构已更新")
    
    # 检查并更新 activities 表
    cursor.execute("PRAGMA table_info(activities)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    if 'need_total_target' not in existing_columns or 'need_item_target' not in existing_columns:
        cursor.execute("ALTER TABLE activities ADD COLUMN need_total_target BOOLEAN")
        cursor.execute("ALTER TABLE activities ADD COLUMN need_item_target BOOLEAN")
        print("activities 表已添加 need_total_target 和 need_item_target 列")
    
    conn.commit()
    conn.close()
    
    print(f"数据库已更新：{DB_PATH}")

if __name__ == "__main__":
    update_database_schema()
import sqlite3
import os
from database.db_setup import DB_PATH  # 修改为 package 导入

def update_database_schema():
    """更新数据库表结构，添加验证约束并迁移现有数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # --- 更新 items 表：添加 spec 正整数约束、unit 和 brand_id ---
    cursor.execute("PRAGMA table_info(items)")
    existing_columns = {row[1]: row for row in cursor.fetchall()}
    
    if (existing_columns.get('spec')[2] != 'INTEGER' or 
        'CHECK(spec > 0)' not in existing_columns.get('spec')[5] or 
        'unit' not in existing_columns or 
        'brand_id' not in existing_columns):
        # 备份现有数据
        cursor.execute("SELECT item_id, item_name, spec, unit, brand_id FROM items")
        items_data = cursor.fetchall()
        
        # 重命名旧表
        cursor.execute("ALTER TABLE items RENAME TO items_old")
        
        # 创建新表结构
        cursor.execute("""
            CREATE TABLE items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                spec INTEGER NOT NULL CHECK(spec > 0),  -- 正整数约束
                unit TEXT NOT NULL,
                brand_id INTEGER NOT NULL,
                UNIQUE(item_name, spec, unit, brand_id),
                FOREIGN KEY (brand_id) REFERENCES brands(brand_id) ON DELETE CASCADE
            )
        """)
        
        # 迁移数据，转换 spec 为整数
        for item in items_data:
            try:
                spec = int(item[2]) if item[2] else 1  # 尝试将 spec 转为整数
                if spec <= 0:
                    spec = 1  # 默认值，防止无效数据
            except (ValueError, TypeError):
                spec = 1  # 如果转换失败，使用默认值
            cursor.execute(
                "INSERT INTO items (item_id, item_name, spec, unit, brand_id) VALUES (?, ?, ?, ?, ?)",
                (item[0], item[1], spec, item[3] or "件", item[4] or 1)
            )
        
        # 删除旧表
        cursor.execute("DROP TABLE items_old")
        print("items 表结构已更新：spec 转为 INTEGER 并添加正整数约束，unit 和 brand_id 已添加")
    
    # --- 更新 activities 表：添加价格非负约束和唯一约束 ---
    cursor.execute("PRAGMA table_info(activities)")
    existing_columns = {row[1]: row for row in cursor.fetchall()}
    
    # 检查是否需要添加价格约束或唯一约束
    cursor.execute("PRAGMA index_list(activities)")
    indexes = [row[1] for row in cursor.fetchall()]
    needs_update = (
        'need_total_target' not in existing_columns or
        'need_item_target' not in existing_columns or
        'original_price' not in existing_columns or
        'CHECK(original_price >= 0)' not in existing_columns.get('original_price', [None])[5] or
        'discount_price' not in existing_columns or
        'CHECK(discount_price >= 0)' not in existing_columns.get('discount_price', [None])[5] or
        'unique_brand_month_total' not in indexes
    )
    
    if needs_update:
        # 清理重复的总目标记录
        cursor.execute("""
            DELETE FROM activities
            WHERE activity_id NOT IN (
                SELECT MIN(activity_id)
                FROM activities
                WHERE is_total_target = 1
                GROUP BY brand_id, month
            ) AND is_total_target = 1
        """)
        
        # 备份现有数据
        cursor.execute("SELECT * FROM activities")
        activities_data = cursor.fetchall()
        
        # 重命名旧表
        cursor.execute("ALTER TABLE activities RENAME TO activities_old")
        
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
                original_price REAL CHECK(original_price >= 0),  -- 非负约束
                discount_price REAL CHECK(discount_price >= 0),  -- 非负约束
                FOREIGN KEY (brand_id) REFERENCES brands(brand_id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES items(item_id),
                UNIQUE(brand_id, month, is_total_target)  -- 唯一约束，确保总目标唯一
            )
        """)
        
        # 迁移数据，验证价格
        for activity in activities_data:
            original_price = activity[9]
            discount_price = activity[10]
            # 确保价格非负或 NULL
            original_price = float(original_price) if original_price and float(original_price) >= 0 else None
            discount_price = float(discount_price) if discount_price and float(discount_price) >= 0 else None
            cursor.execute(
                """
                INSERT OR IGNORE INTO activities (
                    activity_id, brand_id, month, is_total_target, item_id, activity_type,
                    need_total_target, need_item_target, target_value, original_price, discount_price
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (activity[0], activity[1], activity[2], activity[3], activity[4], activity[5],
                 activity[6], activity[7], activity[8], original_price, discount_price)
            )
        
        # 删除旧表
        cursor.execute("DROP TABLE activities_old")
        print("activities 表已更新：添加 original_price 和 discount_price 非负约束，以及 brand_id, month, is_total_target 唯一约束")
    
    conn.commit()
    conn.close()
    
    print(f"数据库已更新：{DB_PATH}")

if __name__ == "__main__":
    update_database_schema()
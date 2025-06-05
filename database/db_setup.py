import sqlite3
import os

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "stockflow.db")

def create_database():
    """创建 SQLite 数据库和表结构"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 创建品牌表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS brands (
            brand_id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        )
    """)

    # 创建商品表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            spec TEXT NOT NULL,
            UNIQUE(item_name, spec)
        )
    """)

    # 创建进货表（添加 ON DELETE CASCADE）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            brand_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit TEXT NOT NULL,
            unit_price REAL NOT NULL,
            total_amount REAL NOT NULL,
            date TEXT NOT NULL,
            remarks TEXT,
            FOREIGN KEY (item_id) REFERENCES items(item_id),
            FOREIGN KEY (brand_id) REFERENCES brands(brand_id) ON DELETE CASCADE
        )
    """)

    # 创建活动表（添加 ON DELETE CASCADE）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_item TEXT,
            target_value REAL NOT NULL,
            rebate_rule TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (brand_id) REFERENCES brands(brand_id) ON DELETE CASCADE
        )
    """)

    # 创建索引以优化查询
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_purchases_date ON purchases(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_purchases_brand ON purchases(brand_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_month ON activities(month)")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
    print(f"数据库已创建：{DB_PATH}")
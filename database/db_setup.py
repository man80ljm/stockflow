import sqlite3
import os
from pathlib import Path

# 基于项目根目录定义数据目录
BASE_DIR = Path(__file__).parent.parent  # 指向 stockflow/ 目录
DB_DIR = BASE_DIR / "data"
DB_PATH = DB_DIR / "stockflow.db"

def create_database():
    """创建 SQLite 数据库和表结构"""
    DB_DIR.mkdir(parents=True, exist_ok=True)  # 自动创建 data 目录
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

    # 创建进货表
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

    # 创建活动表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
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

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_purchases_date ON purchases(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_purchases_brand ON purchases(brand_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_month ON activities(month)")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
    print(f"数据库已创建：{DB_PATH}")
import sqlite3
from datetime import datetime
from database.db_setup import DB_PATH

def get_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_PATH)

def add_brand(brand_name):
    """添加品牌"""
    conn = get_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute(
            "INSERT INTO brands (brand_name, created_at) VALUES (?, ?)",
            (brand_name, created_at)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_all_brands():
    """获取所有品牌"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT brand_id, brand_name FROM brands")
    brands = cursor.fetchall()
    conn.close()
    return brands

def delete_brand(brand_id):
    """删除品牌及其相关数据"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM brands WHERE brand_id = ?", (brand_id,))
    conn.commit()
    conn.close()

def add_item(item_name, spec):
    """添加商品"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO items (item_name, spec) VALUES (?, ?)",
            (item_name, spec)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        cursor.execute(
            "SELECT item_id FROM items WHERE item_name = ? AND spec = ?",
            (item_name, spec)
        )
        item_id = cursor.fetchone()[0]
        return item_id
    finally:
        conn.close()

def get_all_items():
    """获取所有商品"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT item_id, item_name, spec FROM items")
    items = cursor.fetchall()
    conn.close()
    return items

def add_purchase(item_id, brand_id, quantity, unit, unit_price, total_amount, date, remarks=None):
    """添加进货记录"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO purchases (item_id, brand_id, quantity, unit, unit_price, total_amount, date, remarks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (item_id, brand_id, quantity, unit, unit_price, total_amount, date, remarks)
    )
    conn.commit()
    purchase_id = cursor.lastrowid
    conn.close()
    return purchase_id

def get_purchases_by_brand(brand_id, page=1, per_page=20):
    """按品牌分页查询进货记录"""
    conn = get_connection()
    cursor = conn.cursor()
    offset = (page - 1) * per_page
    cursor.execute(
        """
        SELECT p.purchase_id, p.item_id, p.brand_id, p.quantity, p.unit, p.unit_price, 
               p.total_amount, p.date, p.remarks, i.item_name, i.spec
        FROM purchases p
        JOIN items i ON p.item_id = i.item_id
        WHERE p.brand_id = ?
        ORDER BY p.date DESC
        LIMIT ? OFFSET ?
        """,
        (brand_id, per_page, offset)
    )
    purchases = cursor.fetchall()
    # 查询总记录数
    cursor.execute("SELECT COUNT(*) FROM purchases WHERE brand_id = ?", (brand_id,))
    total_records = cursor.fetchone()[0]
    conn.close()
    return purchases, total_records

def get_earliest_year():
    """获取最早的进货年份"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MIN(date) FROM purchases")
    earliest_date = cursor.fetchone()[0]
    conn.close()
    if earliest_date:
        return int(earliest_date[:4])
    return datetime.now().year
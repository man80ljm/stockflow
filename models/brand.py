import sqlite3
from datetime import datetime
from database.db_setup import get_db_path
DB_PATH = get_db_path()  # 动态获取路径

class Brand:
    def __init__(self, brand_id, brand_name, created_at):
        self.brand_id = brand_id
        self.brand_name = brand_name
        self.created_at = created_at

    def save(self):
        """保存品牌到数据库"""
        if self.brand_id is None:  # 如果 brand_id 为 None，说明是新增品牌
            return add_brand(self.brand_name)
        return None  # 如果已经有 brand_id，说明是更新操作（当前无需实现）

    def delete(self):
        """删除品牌及其相关数据"""
        if self.brand_id is not None:
            delete_brand(self.brand_id)

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
    """获取所有品牌，包括创建时间"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT brand_id, brand_name, created_at FROM brands")
    brands = cursor.fetchall()
    conn.close()
    return brands

def delete_brand(brand_id):
    """删除品牌及其相关数据"""
    conn = get_connection()
    cursor = conn.cursor()
    # 先删除相关的进货记录
    cursor.execute("DELETE FROM purchases WHERE brand_id = ?", (brand_id,))
    # 再删除品牌
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
    # 检查 item_id 是否已经被其他品牌使用
    cursor.execute(
        """
        SELECT brand_id FROM purchases WHERE item_id = ?
        """,
        (item_id,)
    )
    existing_brand = cursor.fetchone()
    if existing_brand and existing_brand[0] != brand_id:
        conn.close()
        raise ValueError(f"商品 (item_id: {item_id}) 已被品牌 (brand_id: {existing_brand[0]}) 使用，不能重复关联！")
    
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
import sqlite3
import logging
from datetime import datetime
from database.db_setup import DB_PATH
import os
from pathlib import Path

# 获取当前文件所在目录的父目录
ROOT_DIR = Path(__file__).parent.parent
# 数据库文件路径
DB_PATH = os.path.join(ROOT_DIR, "data", "stockflow.db")

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

def get_purchases_by_brand(brand_id, page=1, per_page=20, year=None, month=None):
    """按品牌分页查询进货记录，可按年月过滤"""
    conn = get_connection()
    cursor = conn.cursor()
    offset = (page - 1) * per_page
    query = """
        SELECT p.purchase_id, p.item_id, p.brand_id, p.quantity, p.unit, p.unit_price, 
               p.total_amount, p.date, p.remarks, i.item_name, i.spec
        FROM purchases p
        JOIN items i ON p.item_id = i.item_id
        WHERE p.brand_id = ?
    """
    params = [brand_id]
    
    if year and month:
        query += " AND strftime('%Y', p.date) = ? AND strftime('%m', p.date) = ?"
        params.extend([str(year), f"{month:02d}"])
    
    query += " ORDER BY p.date ASC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    cursor.execute(query, params)
    purchases = cursor.fetchall()
    
    count_query = "SELECT COUNT(*) FROM purchases WHERE brand_id = ?"
    count_params = [brand_id]
    if year and month:
        count_query += " AND strftime('%Y', date) = ? AND strftime('%m', date) = ?"
        count_params.extend([str(year), f"{month:02d}"])
    
    cursor.execute(count_query, count_params)
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

def get_monthly_activities(brand_id, year, month):
    """获取指定月份的所有活动"""
    conn = get_connection()
    cursor = conn.cursor()
    month_str = f"{year}-{month:02d}"
    
    cursor.execute("""
        SELECT a.activity_id, a.is_total_target, a.item_id, a.activity_type,
               a.need_total_target, a.need_item_target, a.target_value,
               a.original_price, a.discount_price, i.item_name, i.spec
        FROM activities a
        LEFT JOIN items i ON a.item_id = i.item_id
        WHERE a.brand_id = ? AND a.month = ?
        ORDER BY a.is_total_target DESC, a.activity_id
    """, (brand_id, month_str))
    
    activities = cursor.fetchall()
    conn.close()
    return activities

def add_activity(brand_id, month, is_total_target, item_id, activity_type=None, 
               need_total_target=None, need_item_target=None, target_value=0,
               original_price=None, discount_price=None):
    """添加活动记录"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO activities (
            brand_id, month, is_total_target, item_id, activity_type,
            need_total_target, need_item_target, target_value,
            original_price, discount_price
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (brand_id, month, is_total_target, item_id, activity_type,
          need_total_target, need_item_target, target_value,
          original_price, discount_price))
    
    activity_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return activity_id


def delete_activity(activity_id):
    """删除活动"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM activities WHERE activity_id = ?", (activity_id,))
    conn.commit()
    conn.close()
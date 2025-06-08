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

# 配置日志
logging.basicConfig(
    filename=os.path.join(os.path.dirname(DB_PATH), 'debug.log'),
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
    except sqlite3.IntegrityError as e:
        logging.error(f"添加品牌失败: {e}")
        return None
    finally:
        conn.close()

def get_all_brands():
    """获取所有品牌"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT brand_id, brand_name FROM brands")
        brands = cursor.fetchall()
        return brands
    except sqlite3.Error as e:
        logging.error(f"获取品牌列表失败: {e}")
        return []
    finally:
        conn.close()

def delete_brand(brand_id):
    """删除品牌及其相关数据"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM brands WHERE brand_id = ?", (brand_id,))
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"删除品牌失败: {e}")
    finally:
        conn.close()

def add_item(item_name, spec, unit, brand_id):
    """添加商品，关联品牌"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO items (item_name, spec, unit, brand_id) VALUES (?, ?, ?, ?)",
            (item_name, spec, unit, brand_id)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        logging.error(f"添加商品失败: {e}")
        cursor.execute(
            "SELECT item_id FROM items WHERE item_name = ? AND spec = ? AND unit = ? AND brand_id = ?",
            (item_name, spec, unit, brand_id)
        )
        item_id = cursor.fetchone()[0]
        return item_id
    finally:
        conn.close()

def get_all_items(brand_id=None):
    """获取所有商品，带品牌过滤"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT item_id, item_name, spec, unit FROM items"
        params = []
        if brand_id:
            query += " WHERE brand_id = ?"
            params.append(brand_id)
        cursor.execute(query, params)
        items = cursor.fetchall()
        return items
    except sqlite3.Error as e:
        logging.error(f"获取商品列表失败: {e}")
        return []
    finally:
        conn.close()

def add_purchase(item_id, brand_id, quantity, unit, unit_price, total_amount, date, remarks=None):
    """添加进货记录"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
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
        return cursor.lastrowid
    except (sqlite3.Error, ValueError) as e:
        logging.error(f"添加进货记录失败: {e}")
        raise
    finally:
        conn.close()

def get_purchases_by_brand(brand_id, page=1, per_page=20, year=None, month=None):
    """按品牌分页查询进货记录，可按年月过滤"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
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
        return purchases, total_records
    except sqlite3.Error as e:
        logging.error(f"查询进货记录失败: {e}")
        return [], 0
    finally:
        conn.close()

def get_earliest_year():
    """获取最早的进货年份"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MIN(date) FROM purchases")
        earliest_date = cursor.fetchone()[0]
        return int(earliest_date[:4]) if earliest_date else datetime.now().year
    except sqlite3.Error as e:
        logging.error(f"获取最早年份失败: {e}")
        return datetime.now().year
    finally:
        conn.close()

def get_monthly_activities(brand_id, year, month):
    """获取指定月份的所有活动"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        month_str = f"{year}-{month:02d}"
        
        cursor.execute("""
            SELECT a.activity_id, a.is_total_target, a.item_id, a.activity_type,
                   a.need_total_target, a.need_item_target, a.target_value,
                   a.original_price, a.discount_price, i.item_name, i.spec, i.unit
            FROM activities a
            LEFT JOIN items i ON a.item_id = i.item_id
            WHERE a.brand_id = ? AND a.month = ?
            ORDER BY a.is_total_target DESC, a.activity_id
        """, (brand_id, month_str))
        
        activities = cursor.fetchall()
        return activities
    except sqlite3.Error as e:
        logging.error(f"获取月度活动失败: {e}")
        return []
    finally:
        conn.close()

def add_activity(brand_id, month, is_total_target, item_id, activity_type=None, 
               need_total_target=None, need_item_target=None, target_value=0,
               original_price=None, discount_price=None):
    """添加活动记录"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
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
        
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"添加活动失败: {e}")
        raise
    finally:
        conn.close()

def delete_activity(activity_id):
    """删除活动并清理未引用的商品"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 获取活动关联的 item_id
        cursor.execute("SELECT item_id FROM activities WHERE activity_id = ?", (activity_id,))
        item_id = cursor.fetchone()
        
        # 删除活动记录
        cursor.execute("DELETE FROM activities WHERE activity_id = ?", (activity_id,))
        
        # 如果活动关联了商品，检查是否需要删除该商品
        if item_id and item_id[0]:
            item_id = item_id[0]
            # 检查该商品是否仍被其他活动或进货记录引用
            cursor.execute("SELECT COUNT(*) FROM activities WHERE item_id = ?", (item_id,))
            activity_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM purchases WHERE item_id = ?", (item_id,))
            purchase_count = cursor.fetchone()[0]
            
            # 如果商品未被任何记录引用，删除该商品
            if activity_count == 0 and purchase_count == 0:
                cursor.execute("DELETE FROM items WHERE item_id = ?", (item_id,))
        
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"删除活动失败: {e}")
    finally:
        conn.close()

def delete_purchase(purchase_id):
    """删除进货记录并清理未引用的商品"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 获取进货记录关联的 item_id
        cursor.execute("SELECT item_id FROM purchases WHERE purchase_id = ?", (purchase_id,))
        item_id = cursor.fetchone()
        
        # 删除进货记录
        cursor.execute("DELETE FROM purchases WHERE purchase_id = ?", (purchase_id,))
        
        # 如果进货记录关联了商品，检查是否需要删除该商品
        if item_id and item_id[0]:
            item_id = item_id[0]
            # 检查该商品是否仍被其他活动或进货记录引用
            cursor.execute("SELECT COUNT(*) FROM activities WHERE item_id = ?", (item_id,))
            activity_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM purchases WHERE item_id = ?", (item_id,))
            purchase_count = cursor.fetchone()[0]
            
            # 如果商品未被任何记录引用，删除该商品
            if activity_count == 0 and purchase_count == 0:
                cursor.execute("DELETE FROM items WHERE item_id = ?", (item_id,))
        
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"删除进货记录失败: {e}")
    finally:
        conn.close()
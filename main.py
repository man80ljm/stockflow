import sys
import os
import sqlite3
from PyQt5.QtWidgets import QApplication
from ui.add_brand import AddBrandWindow
from database.db_setup import create_database, DB_PATH
from database.update_db import update_database_schema

def get_base_path():
    """获取应用程序的基路径（打包后为 main.exe 所在目录）"""
    if getattr(sys, 'frozen', False):  # PyInstaller 打包环境
        # 打包后，sys.executable 是 main.exe 的路径
        base_path = os.path.dirname(sys.executable)
    else:
        # 开发环境，获取 main.py 所在目录
        base_path = os.path.dirname(os.path.abspath(__file__))
    return base_path

def ensure_data_directory():
    """确保 data 目录存在，并返回动态的 DB_PATH"""
    base_path = get_base_path()
    data_dir = os.path.join(base_path, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return os.path.join(data_dir, "stockflow.db")

def check_database_schema(db_path):
    """检查数据库表结构是否与预期一致"""
    expected_columns = {
        'activities': ['activity_id', 'brand_id', 'month', 'is_total_target', 'item_id',
                      'activity_type', 'need_total_target', 'need_item_target', 'target_value',
                      'original_price', 'discount_price'],
        'brands': ['brand_id', 'brand_name', 'created_at'],
        'items': ['item_id', 'item_name', 'spec', 'unit', 'brand_id'],
        'purchases': ['purchase_id', 'item_id', 'brand_id', 'quantity', 'unit', 'unit_price',
                     'total_amount', 'date', 'remarks']
    }
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for table, columns in expected_columns.items():
        cursor.execute(f"PRAGMA table_info({table})")
        existing_columns = [row[1] for row in cursor.fetchall()]
        missing_columns = [col for col in columns if col not in existing_columns]
        
        if missing_columns:
            conn.close()
            update_database_schema()
            break
    
    conn.close()

if __name__ == "__main__":
    try:
        # 动态获取 data 目录和数据库路径
        DB_PATH = ensure_data_directory()
        
        # 确保数据库文件存在并创建
        if not os.path.exists(DB_PATH):
            create_database()
        else:
            check_database_schema(DB_PATH)
        
        app = QApplication(sys.argv)
        window = AddBrandWindow()
        window.show()
        sys.exit(app.exec_())
    except RuntimeError as e:
        print(f"启动失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"未知错误: {e}")
        sys.exit(1)
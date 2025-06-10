import os
import sys

def ensure_data_dir():
    if hasattr(sys, '_MEIPASS'):
        data_dir = os.path.join(sys._MEIPASS, "data")
        os.makedirs(data_dir, exist_ok=True)
        # 更新 queries.py 的 DB_DIR
        import database.queries
        database.queries.DB_DIR = data_dir
        database.queries.DB_PATH = os.path.join(data_dir, "stockflow.db")

ensure_data_dir()
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
                             QTableWidgetItem, QPushButton, QMessageBox, QApplication, QHeaderView)
from PyQt5.QtCore import Qt
import datetime
import traceback
import os
from database.queries import get_connection

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug.log")

def log_debug(message):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {message}\n")

class ExpenseInfoWindow(QWidget):
    def __init__(self, brand, year, month, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.brand = brand
        self.year = year
        self.month = month
        self.setWindowTitle(f"{self.brand.brand_name} - 支出情况")
        self.setGeometry(100, 100, 800, 400)
        self.init_ui()
        self.load_expense_data()
        self.center_on_screen()
        log_debug(f"初始化 ExpenseInfoWindow for brand: {brand.brand_name}, 年: {year}, 月: {month}")

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        window_size = self.geometry()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        self.move(x, y)

    def init_ui(self):
        layout = QVBoxLayout()
        title_label = QLabel(f"{self.brand.brand_name} - {self.year}年{self.month}月支出情况")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(title_label)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["原始支出", "优惠返点", "实际支出"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.load_expense_data)
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_expense_data(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 原始支出
            log_debug(f"Querying original expense for brand_id: {self.brand.brand_id}, year: {self.year}, month: {self.month}")
            cursor.execute("""
                SELECT SUM(total_amount)
                FROM purchases
                WHERE brand_id = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
            """, (self.brand.brand_id, str(self.year), f"{self.month:02d}"))
            result = cursor.fetchone()
            original_expense = float(result[0]) if result and result[0] is not None else 0.0
            log_debug(f"Original expense retrieved: {original_expense}")

            # 获取总销量目标
            log_debug(f"Querying total target for brand_id: {self.brand.brand_id}, month: {self.year}-{self.month:02d}")
            cursor.execute("""
                SELECT target_value
                FROM activities
                WHERE brand_id = ? AND month = ? AND is_total_target = 1
            """, (self.brand.brand_id, f"{self.year}-{self.month:02d}"))
            total_target = cursor.fetchone()
            total_target_value = float(total_target[0]) if total_target and total_target[0] is not None else 0.0
            log_debug(f"Total target value: {total_target_value}")

            # 获取单品活动数据
            log_debug(f"Querying activities for brand_id: {self.brand.brand_id}, month: {self.year}-{self.month:02d}")
            cursor.execute("""
                SELECT a.activity_id, a.activity_type, a.original_price, a.discount_price,
                    a.target_value, a.need_total_target, a.need_item_target, a.item_id
                FROM activities a
                WHERE a.brand_id = ? AND a.month = ? AND a.is_total_target = 0
            """, (self.brand.brand_id, f"{self.year}-{self.month:02d}"))
            activities = cursor.fetchall()
            log_debug(f"Activities retrieved: {len(activities)} records")

            # 计算实际总销量
            log_debug(f"Querying actual total sales for brand_id: {self.brand.brand_id}")
            cursor.execute("""
                SELECT SUM(total_amount)
                FROM purchases
                WHERE brand_id = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
            """, (self.brand.brand_id, str(self.year), f"{self.month:02d}"))
            result = cursor.fetchone()
            actual_total_sales = float(result[0]) if result and result[0] is not None else 0.0
            log_debug(f"Actual total sales: {actual_total_sales}")

            discount_total = 0.0
            for activity in activities:
                activity_id, activity_type, original_price, discount_price, target_value, \
                need_total_target, need_item_target, item_id = activity

                is_completed = True
                if need_total_target and actual_total_sales < total_target_value:
                    is_completed = False
                if need_item_target and item_id:
                    log_debug(f"Querying actual item sales for item_id: {item_id}")
                    cursor.execute("""
                        SELECT SUM(quantity)
                        FROM purchases
                        WHERE brand_id = ? AND item_id = ? AND 
                            strftime('%Y', date) = ? AND strftime('%m', date) = ?
                    """, (self.brand.brand_id, item_id, str(self.year), f"{self.month:02d}"))
                    result = cursor.fetchone()
                    actual_item_sales = float(result[0]) if result and result[0] is not None else 0.0
                    log_debug(f"Actual item sales for item_id {item_id}: {actual_item_sales}")
                    if actual_item_sales < target_value:
                        is_completed = False

                if is_completed and original_price and discount_price:
                    if need_total_target:
                        discount = (original_price - discount_price) * (actual_total_sales / total_target_value if total_target_value > 0 else 0)
                    elif need_item_target and item_id:
                        discount = (original_price - discount_price) * actual_item_sales
                    discount_total += discount
                    log_debug(f"Discount calculated for activity {activity_id}: {discount}")

            actual_expense = original_expense - discount_total
            log_debug(f"Final actual expense: {actual_expense}")

            self.table.setRowCount(1)
            items_to_set = [
                f"{original_expense:.2f}",
                f"{discount_total:.2f}",
                f"{actual_expense:.2f}"
            ]

            for col, text in enumerate(items_to_set):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(0, col, item)

            self.table.resizeColumnsToContents()
            font_metrics = self.table.fontMetrics()
            padding = font_metrics.horizontalAdvance('M') * 4
            for col in range(self.table.columnCount()):
                current_width = self.table.columnWidth(col)
                self.table.setColumnWidth(col, current_width + padding)

            conn.close()

        except Exception as e:
            log_debug(f"加载支出数据时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"加载支出数据失败: {str(e)}")

    def closeEvent(self, event):
        try:
            log_debug("ExpenseInfoWindow 关闭事件触发")
            parent = self.parent()
            if parent and hasattr(parent, 'expense_windows'):
                key = (self.brand.brand_id, self.year, self.month)
                if key in parent.expense_windows:
                    del parent.expense_windows[key]
            super().closeEvent(event)
        except Exception as e:
            log_debug(f"关闭窗口时发生错误: {e}")
            event.accept()
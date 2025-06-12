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

class ActivityCompletionWindow(QWidget):
    def __init__(self, brand, year, month, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.brand = brand
        self.year = year
        self.month = month
        self.setWindowTitle(f"{self.brand.brand_name} - 活动完成情况")
        self.setGeometry(100, 100, 1800, 500)  # 增加宽度以适应新列
        self.init_ui()
        self.load_completion_data()
        self.center_on_screen()
        log_debug(f"初始化 ActivityCompletionWindow for brand: {brand.brand_name}, 年: {year}, 月: {month}")

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        window_size = self.geometry()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        self.move(x, y)

    def init_ui(self):
        layout = QVBoxLayout()
        title_label = QLabel(f"{self.brand.brand_name} - {self.year}年{self.month}月活动完成情况")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(title_label)

        self.table = QTableWidget()
        self.table.setColumnCount(10)  # 修改：增加到10列
        self.table.setHorizontalHeaderLabels([
            "品名", "活动类型", "设定总销量", "实际总销量",
            "设定单品销量", "实际单品销量", "是否完成",
            "单品初始支出", "单品返点", "单品实际支出"  # 新增三列
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.load_completion_data)
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_completion_data(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 获取总销量目标
            cursor.execute("""
                SELECT target_value
                FROM activities
                WHERE brand_id = ? AND month = ? AND is_total_target = 1
            """, (self.brand.brand_id, f"{self.year}-{self.month:02d}"))
            total_target = cursor.fetchone()
            total_target_value = total_target[0] if total_target else 0

            # 获取单品活动数据，包含原价和优惠价
            cursor.execute("""
                SELECT a.activity_id, a.activity_type, a.need_total_target, a.need_item_target,
                    a.target_value, a.original_price, a.discount_price, i.item_id, i.item_name, i.spec, i.unit
                FROM activities a
                LEFT JOIN items i ON a.item_id = i.item_id
                WHERE a.brand_id = ? AND a.month = ? AND a.is_total_target = 0
            """, (self.brand.brand_id, f"{self.year}-{self.month:02d}"))
            activities = cursor.fetchall()

            self.table.setRowCount(0)
            if not activities and total_target_value == 0:
                QMessageBox.information(self, "提示", f"未找到 {self.year}年{self.month}月 的活动数据")
                conn.close()
                return

            # 计算实际总销量
            cursor.execute("""
                SELECT SUM(total_amount)
                FROM purchases
                WHERE brand_id = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
            """, (self.brand.brand_id, str(self.year), f"{self.month:02d}"))
            result = cursor.fetchone()
            actual_total_sales = result[0] if result[0] else 0

            for row, activity in enumerate(activities):
                activity_id, activity_type, need_total_target, need_item_target, target_value, \
                original_price, discount_price, item_id, item_name, spec, unit = activity

                # 获取单品实际销量
                actual_item_sales = 0
                if item_id:
                    cursor.execute("""
                        SELECT SUM(quantity)
                        FROM purchases
                        WHERE brand_id = ? AND item_id = ? AND 
                            strftime('%Y', date) = ? AND strftime('%m', date) = ?
                    """, (self.brand.brand_id, item_id, str(self.year), f"{self.month:02d}"))
                    result = cursor.fetchone()
                    actual_item_sales = result[0] if result[0] else 0

                # 判断是否完成
                is_completed = True
                if need_total_target and actual_total_sales < total_target_value:
                    is_completed = False
                if need_item_target and actual_item_sales < target_value:
                    is_completed = False
                completion_status = "是" if is_completed else "否"

                # 计算单品支出相关数据
                # --- 修改后代码 ---
                cursor.execute("""
                    SELECT SUM(total_amount)
                    FROM purchases
                    WHERE brand_id = ? AND item_id = ? AND 
                        strftime('%Y', date) = ? AND strftime('%m', date) = ?
                """, (self.brand.brand_id, item_id, str(self.year), f"{self.month:02d}"))
                result = cursor.fetchone()
                item_original_expense = float(result[0]) if result and result[0] is not None else 0.0
                log_debug(f"Calculated item_original_expense for item_id {item_id}: {item_original_expense}")

                # --- 新增代码：在循环开始处获取 spec ---
                cursor.execute("""
                    SELECT spec
                    FROM items
                    WHERE item_id = ?
                """, (item_id,))
                spec_result = cursor.fetchone()
                spec = float(spec_result[0]) if spec_result and spec_result[0] is not None else 1.0  # 默认 spec 为 1
                log_debug(f"Retrieved spec for item_id {item_id}: {spec}")

                # --- 修改后代码 ---
                item_discount = 0
                if is_completed and original_price and discount_price:
                    item_discount = (original_price - discount_price) * spec * actual_item_sales  # 单品返点
                    log_debug(f"Calculated item_discount for item_id {item_id}: {item_discount}")
                    
                item_actual_expense = item_original_expense - item_discount  # 单品实际支出

                self.table.insertRow(row)
                item_display = item_name or "未知品名"
                items_to_set = [
                    item_display, activity_type,
                    str(total_target_value) if need_total_target else "无需",
                    str(actual_total_sales),
                    str(target_value) if need_item_target else "无需",
                    str(actual_item_sales),
                    completion_status,
                    f"{item_original_expense:.2f}",  # 新增：单品初始支出
                    f"{item_discount:.2f}",          # 新增：单品返点
                    f"{item_actual_expense:.2f}"     # 新增：单品实际支出
                ]

                for col, text in enumerate(items_to_set):
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignCenter)
                    if col == 6:
                        item.setBackground(Qt.green if text == "是" else Qt.red)
                    self.table.setItem(row, col, item)

            self.table.resizeColumnsToContents()
            font_metrics = self.table.fontMetrics()
            padding = font_metrics.horizontalAdvance('M') * 4
            for col in range(self.table.columnCount()):
                current_width = self.table.columnWidth(col)
                self.table.setColumnWidth(col, current_width + padding)

            conn.close()

        except Exception as e:
            log_debug(f"加载活动完成情况时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"加载活动完成情况失败: {str(e)}")

    def closeEvent(self, event):
        key = (self.brand.brand_id, self.year, self.month)
        parent = self.parent()
        if parent and hasattr(parent, 'completion_windows') and key in parent.completion_windows:
            del parent.completion_windows[key]
        super().closeEvent(event)
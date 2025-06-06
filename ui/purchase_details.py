from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox, QDateEdit, QApplication, QStackedWidget, QDoubleSpinBox, QHeaderView, QMenu
from PyQt5.QtCore import QDate, Qt, QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from database.queries import get_purchases_by_brand, get_connection
from database.db_setup import DB_PATH
from models.purchase import Purchase
import datetime
import traceback
import os
import sqlite3  # 导入 sqlite3 以处理 IntegrityError

# 调试日志文件路径
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug.log")

def log_debug(message):
    """记录调试信息到文件"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {message}\n")

class PurchaseDetailsWindow(QWidget):
    def __init__(self, brand):
        super().__init__()
        self.brand = brand
        self.current_page = 1
        self.per_page = 20
        self.total_pages = 1
        self.purchases = []
        self.year = QDate.currentDate().year()
        self.month = QDate.currentDate().month()
        self.setWindowTitle(f"{self.brand.brand_name} - 进货详情")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()
        self.load_purchases()
        self.center_on_screen()

    def center_on_screen(self):
        """将窗口移动到屏幕中央"""
        screen = QApplication.primaryScreen().geometry()
        window_size = self.geometry()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        self.move(x, y)

    def init_ui(self):
        layout = QVBoxLayout()

        # 标题
        title_label = QLabel(f"{self.brand.brand_name} - 进货详情")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(title_label)

        # 时间筛选
        layout.addLayout(self.setup_date_filter())

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["日期", "品名", "规格", "单位", "数量", "单价", "金额", "备注"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # 禁止双击编辑
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        column_widths = {0: 120, 1: 150, 2: 100, 3: 80, 4: 80, 5: 100, 6: 120, 7: 150}
        for col, width in column_widths.items():
            self.table.setColumnWidth(col, width)
        self.setup_context_menu()
        layout.addWidget(self.table)

        # 分页控件
        page_layout = QHBoxLayout()
        self.page_label = QLabel("第 1 页 / 共 1 页")
        prev_button = QPushButton("上一页")
        prev_button.clicked.connect(self.prev_page)
        next_button = QPushButton("下一页")
        next_button.clicked.connect(self.next_page)
        page_layout.addWidget(self.page_label)
        page_layout.addWidget(prev_button)
        page_layout.addWidget(next_button)
        layout.addLayout(page_layout)

        # 操作按钮
        button_layout = QHBoxLayout()
        activity_button = QPushButton("当月活动")
        activity_button.clicked.connect(self.open_activity_screen)
        add_button = QPushButton("增加")
        add_button.clicked.connect(self.add_purchase)
        export_button = QPushButton("导出")
        calculate_button = QPushButton("计算")
        bill_button = QPushButton("账单")
        button_layout.addWidget(activity_button)
        button_layout.addWidget(add_button)
        button_layout.addWidget(export_button)
        button_layout.addWidget(calculate_button)
        button_layout.addWidget(bill_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def setup_date_filter(self):
        date_layout = QHBoxLayout()
        self.date_selector = QDateEdit()
        self.date_selector.setDisplayFormat("yyyy年MM月")
        self.date_selector.setCalendarPopup(True)
        self.date_selector.setDate(QDate.currentDate())
        self.date_selector.dateChanged.connect(self.filter_by_date)
        date_layout.addWidget(QLabel("选择月份："))
        date_layout.addWidget(self.date_selector)
        date_layout.addStretch()
        return date_layout

    def filter_by_date(self):
        selected_date = self.date_selector.date()
        self.year = selected_date.year()
        self.month = selected_date.month()
        self.current_page = 1
        self.load_purchases()

    def setup_context_menu(self):
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row >= 0:
            menu = QMenu(self)
            edit_action = menu.addAction("修改")
            delete_action = menu.addAction("删除")
            action = menu.exec_(self.table.viewport().mapToGlobal(pos))
            if action == delete_action:
                self.delete_purchase(row)
            elif action == edit_action:
                self.edit_purchase(row)

    def load_purchases(self):
        try:
            self.purchases = []
            purchase_data, total_records = get_purchases_by_brand(
                self.brand.brand_id, self.current_page, self.per_page, self.year, self.month
            )
            self.total_pages = (total_records + self.per_page - 1) // self.per_page
            self.page_label.setText(f"第 {self.current_page} 页 / 共 {self.total_pages} 页")

            for data in purchase_data:
                purchase = Purchase(
                    purchase_id=data[0], item_id=data[1], brand_id=data[2], quantity=data[3],
                    unit=data[4], unit_price=data[5], total_amount=data[6], date=data[7],
                    remarks=data[8], item_name=data[9], spec=data[10]
                )
                self.purchases.append(purchase)

            self.table.setRowCount(len(self.purchases))
            for row, purchase in enumerate(self.purchases):
                date_str = datetime.datetime.strptime(purchase.date, "%Y-%m-%d").strftime("%Y年%m月%d日")
                self.table.setItem(row, 0, QTableWidgetItem(date_str))
                self.table.setItem(row, 1, QTableWidgetItem(purchase.item_name))
                self.table.setItem(row, 2, QTableWidgetItem(purchase.spec))
                self.table.setItem(row, 3, QTableWidgetItem(purchase.unit))
                self.table.setItem(row, 4, QTableWidgetItem(str(purchase.quantity)))
                self.table.setItem(row, 5, QTableWidgetItem(str(purchase.unit_price)))
                self.table.setItem(row, 6, QTableWidgetItem(str(purchase.total_amount)))
                self.table.setItem(row, 7, QTableWidgetItem(purchase.remarks or ""))
        except Exception as e:
            log_debug(f"加载进货记录时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"加载进货记录失败: {str(e)}")

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_purchases()

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_purchases()

    def open_activity_screen(self):
        QMessageBox.information(self, "提示", "活动信息界面尚未实现！")

    def add_purchase(self):
        try:
            dialog = AddPurchaseDialog(self.brand.brand_id, self)
            if dialog.exec_():
                self.load_purchases()
        except Exception as e:
            log_debug(f"新增进货记录时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"新增进货记录失败: {str(e)}")

    def edit_purchase(self, row):
        purchase = self.purchases[row]
        dialog = AddPurchaseDialog(self.brand.brand_id, self, purchase)
        if dialog.exec_():
            self.load_purchases()

    def delete_purchase(self, row):
        purchase = self.purchases[row]
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定删除进货记录 '{purchase.item_name} ({purchase.spec})' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM purchases WHERE purchase_id = ?", (purchase.purchase_id,))
            conn.commit()
            conn.close()
            self.load_purchases()

    def on_cell_double_clicked(self, row, column):
        if column == 7:  # 仅允许编辑备注
            self.table.setEditTriggers(QTableWidget.DoubleClicked)
            self.table.editItem(self.table.item(row, column))
            self.table.cellChanged.connect(self.on_cell_changed)
            self.table.setEditTriggers(QTableWidget.NoEditTriggers)

    def on_cell_changed(self, row, column):
        try:
            if column == 7:
                purchase = self.purchases[row]
                new_remarks = self.table.item(row, column).text().strip() or None
                if new_remarks != purchase.remarks:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE purchases SET remarks = ? WHERE purchase_id = ?",
                        (new_remarks, purchase.purchase_id)
                    )
                    conn.commit()
                    conn.close()
                    purchase.remarks = new_remarks
                    QMessageBox.information(self, "成功", "备注已更新！")
        except Exception as e:
            log_debug(f"更新备注时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"更新备注失败: {str(e)}")

class AddPurchaseDialog(QDialog):
    def __init__(self, brand_id, parent=None, purchase=None):
        super().__init__(parent)
        self.brand_id = brand_id
        self.purchase = purchase
        self.items = self.get_items_for_brand()
        self.current_step = 0
        self.item_id = None
        self.selected_item = None
        self.last_search_time = 0
        self.search_delay = 200
        self.setWindowTitle("新增进货记录" if not purchase else "修改进货记录")
        self.init_ui()
        if purchase:
            self.populate_purchase_data()

    def populate_purchase_data(self):
        self.new_or_existing_combo.setCurrentIndex(1)
        self.current_step = 1
        self.stack.setCurrentIndex(self.current_step)
        for i in range(self.existing_item_model.rowCount()):
            item = self.existing_item_model.item(i)
            if item.data(Qt.UserRole) == self.purchase.item_id:
                self.existing_item_combo.setCurrentIndex(i)
                self.on_item_selected(i)
                break
        self.quantity_input.setValue(self.purchase.quantity)
        self.unit_price_input.setValue(self.purchase.unit_price)
        date = QDate.fromString(self.purchase.date, "yyyy-MM-dd")
        self.date_input.setDate(date)
        self.remarks_input.setText(self.purchase.remarks or "")

    def get_items_for_brand(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT i.item_id, i.item_name, i.spec
            FROM items i
            JOIN purchases p ON i.item_id = p.item_id
            WHERE p.brand_id = ?
            AND i.item_id NOT IN (
                SELECT item_id FROM purchases WHERE brand_id != ?
            )
            """,
            (self.brand_id, self.brand_id)
        )
        items = cursor.fetchall()
        conn.close()
        return items

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        # 步骤 1：选择是否新增商品
        self.step1_widget = QWidget()
        step1_layout = QFormLayout()
        self.new_or_existing_combo = QComboBox()
        self.new_or_existing_combo.addItems(["新增品类", "已有品类"])
        self.new_or_existing_combo.currentIndexChanged.connect(self.on_new_or_existing_changed)
        step1_layout.addRow("品类选择：", self.new_or_existing_combo)
        self.step1_widget.setLayout(step1_layout)
        self.stack.addWidget(self.step1_widget)

        # 步骤 1.5：已有品类模糊搜索
        self.step1_5_widget = QWidget()
        step1_5_layout = QFormLayout()
        self.existing_item_combo = QComboBox()
        self.existing_item_combo.setEditable(True)
        self.existing_item_combo.setInsertPolicy(QComboBox.NoInsert)
        self.existing_item_combo.clearEditText()
        self.existing_item_model = QStandardItemModel()
        for item in self.items:
            display_text = f"{item[1]} ({item[2]})"
            model_item = QStandardItem(display_text)
            model_item.setData(item[0], Qt.UserRole)
            model_item.setData(item[1], Qt.UserRole + 1)
            model_item.setData(item[2], Qt.UserRole + 2)
            self.existing_item_model.appendRow(model_item)
            self.existing_item_combo.addItem(display_text)
        self.existing_item_combo.setModel(self.existing_item_model)
        self.existing_item_combo.editTextChanged.connect(self.on_search_text_changed)
        self.existing_item_combo.currentIndexChanged.connect(self.on_item_selected)
        self.existing_item_combo.setMaxVisibleItems(10)
        self.existing_item_combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.existing_item_combo.setStyleSheet("""
            QComboBox QAbstractItemView {
                selection-background-color: #0078D7;
                selection-color: white;
            }
        """)
        step1_5_layout.addRow("选择已有品类：", self.existing_item_combo)
        self.step1_5_widget.setLayout(step1_5_layout)
        self.stack.addWidget(self.step1_5_widget)

        # 步骤 2：输入新商品名称
        self.step2_widget = QWidget()
        step2_layout = QFormLayout()
        self.new_item_name = QLineEdit()
        self.new_item_name.setPlaceholderText("请输入商品名称")
        step2_layout.addRow("新商品名称：", self.new_item_name)
        self.step2_widget.setLayout(step2_layout)
        self.stack.addWidget(self.step2_widget)

        # 步骤 3：输入新商品规格
        self.step3_widget = QWidget()
        step3_layout = QFormLayout()
        self.new_item_spec = QLineEdit()
        self.new_item_spec.setPlaceholderText("请输入规格")
        step3_layout.addRow("新商品规格：", self.new_item_spec)
        self.step3_widget.setLayout(step3_layout)
        self.stack.addWidget(self.step3_widget)

        # 步骤 4：选择单位
        self.step4_widget = QWidget()
        step4_layout = QFormLayout()
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["件", "箱", "桶", "瓶"])
        step4_layout.addRow("单位：", self.unit_combo)
        self.step4_widget.setLayout(step4_layout)
        self.stack.addWidget(self.step4_widget)

        # 步骤 5：输入数量
        self.step5_widget = QWidget()
        step5_layout = QFormLayout()
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setDecimals(0)
        self.quantity_input.setMinimum(1)
        self.quantity_input.setMaximum(999999)
        step5_layout.addRow("数量：", self.quantity_input)
        self.step5_widget.setLayout(step5_layout)
        self.stack.addWidget(self.step5_widget)

        # 步骤 6：输入单价
        self.step6_widget = QWidget()
        step6_layout = QFormLayout()
        self.unit_price_input = QDoubleSpinBox()
        self.unit_price_input.setDecimals(2)
        self.unit_price_input.setMinimum(0.01)
        self.unit_price_input.setMaximum(999999)
        step6_layout.addRow("单价：", self.unit_price_input)
        self.step6_widget.setLayout(step6_layout)
        self.stack.addWidget(self.step6_widget)

        # 步骤 7：选择日期和输入备注
        self.step7_widget = QWidget()
        step7_layout = QFormLayout()
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        step7_layout.addRow("日期：", self.date_input)
        self.remarks_input = QLineEdit()
        self.remarks_input.setPlaceholderText("请输入备注（可选）")
        step7_layout.addRow("备注：", self.remarks_input)
        self.step7_widget.setLayout(step7_layout)
        self.stack.addWidget(self.step7_widget)

        # 按钮布局
        self.button_layout = QHBoxLayout()
        self.prev_button = QPushButton("上一步")
        self.prev_button.clicked.connect(self.prev_step)
        self.prev_button.setEnabled(False)
        self.next_button = QPushButton("下一步")
        self.next_button.clicked.connect(self.next_step)
        self.button_layout.addWidget(self.prev_button)
        self.button_layout.addWidget(self.next_button)
        self.main_layout.addLayout(self.button_layout)

        self.setLayout(self.main_layout)

        self.new_or_existing_combo.installEventFilter(self)
        self.existing_item_combo.installEventFilter(self)
        self.new_item_name.installEventFilter(self)
        self.new_item_spec.installEventFilter(self)
        self.unit_combo.installEventFilter(self)
        self.quantity_input.installEventFilter(self)
        self.unit_price_input.installEventFilter(self)
        self.date_input.installEventFilter(self)
        self.remarks_input.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == event.KeyPress and event.key() in (Qt.Key_Enter, Qt.Key_Return):
            if self.current_step < 6:
                self.next_step()
            return True
        return super().eventFilter(obj, event)

    def on_new_or_existing_changed(self, index):
        try:
            log_debug(f"用户选择: 新增/已有选项 = {index}")
            self.existing_item_combo.editTextChanged.disconnect(self.on_search_text_changed)
            self.existing_item_combo.currentIndexChanged.disconnect(self.on_item_selected)

            if index == 1:
                self.current_step = 1
                self.existing_item_combo.clearEditText()
                if not self.items:
                    QMessageBox.information(self, "提示", "当前品牌没有可用品类，请先添加品类！")
                    self.next_button.setEnabled(False)
                else:
                    self.next_button.setEnabled(False)
                    QTimer.singleShot(100, self.existing_item_combo.setFocus)
            else:
                self.current_step = 2
                self.next_button.setEnabled(True)
            self.stack.setCurrentIndex(self.current_step)
            self.prev_button.setEnabled(self.current_step > 0)

            self.existing_item_combo.editTextChanged.connect(self.on_search_text_changed)
            self.existing_item_combo.currentIndexChanged.connect(self.on_item_selected)
        except Exception as e:
            log_debug(f"处理品类选择变化时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"切换品类选择失败: {str(e)}")

    def on_search_text_changed(self, text):
        try:
            current_time = datetime.datetime.now().timestamp() * 1000
            if current_time - self.last_search_time < self.search_delay:
                return
            self.last_search_time = current_time

            text = text.lower().strip()
            self.existing_item_model.clear()

            if not text:
                for item in self.items:
                    display_text = f"{item[1]} ({item[2]})"
                    model_item = QStandardItem(display_text)
                    model_item.setData(item[0], Qt.UserRole)
                    model_item.setData(item[1], Qt.UserRole + 1)
                    model_item.setData(item[2], Qt.UserRole + 2)
                    self.existing_item_model.appendRow(model_item)
                self.next_button.setEnabled(False)
                return

            matched_items = False
            for item in self.items:
                display_text = f"{item[1]} ({item[2]})"
                if text in display_text.lower():
                    model_item = QStandardItem(display_text)
                    model_item.setData(item[0], Qt.UserRole)
                    model_item.setData(item[1], Qt.UserRole + 1)
                    model_item.setData(item[2], Qt.UserRole + 2)
                    self.existing_item_model.appendRow(model_item)
                    matched_items = True

            self.next_button.setEnabled(False)
            if not matched_items:
                self.existing_item_combo.setCurrentText("")
        except Exception as e:
            log_debug(f"搜索品类时发生错误: {e}\n{traceback.format_exc()}")
            self.next_button.setEnabled(False)

    def on_item_selected(self, index):
        try:
            if index >= 0 and self.existing_item_combo.currentText():
                item = self.existing_item_model.item(index)
                if item:
                    self.selected_item = {
                        "item_id": item.data(Qt.UserRole),
                        "item_name": item.data(Qt.UserRole + 1),
                        "spec": item.data(Qt.UserRole + 2)
                    }
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT unit FROM purchases WHERE item_id = ? ORDER BY date DESC LIMIT 1",
                        (self.selected_item["item_id"],)
                    )
                    result = cursor.fetchone()
                    unit = result[0] if result else "件"
                    self.unit_combo.setCurrentText(unit)
                    self.unit_combo.setEnabled(False)
                    conn.close()
                    self.next_button.setEnabled(True)
                else:
                    self.next_button.setEnabled(False)
            else:
                self.next_button.setEnabled(False)
        except Exception as e:
            log_debug(f"处理品类选择时发生错误: {e}\n{traceback.format_exc()}")
            self.next_button.setEnabled(False)

    def next_step(self):
        try:
            if self.current_step == 0:
                if self.new_or_existing_combo.currentIndex() == 0:
                    self.current_step = 2
                else:
                    self.current_step = 1
            elif self.current_step == 1:
                if not self.items:
                    QMessageBox.warning(self, "错误", "当前品牌没有可用品类！")
                    return
                if not hasattr(self, 'selected_item') or not self.selected_item:
                    QMessageBox.warning(self, "错误", "请选择一个有效的品类！")
                    return
                self.item_id = self.selected_item["item_id"]
                self.current_step = 4
            elif self.current_step == 2:
                if not self.new_item_name.text().strip():
                    QMessageBox.warning(self, "错误", "新商品名称不能为空！")
                    return
                self.current_step += 1
            elif self.current_step == 3:
                if not self.new_item_spec.text().strip():
                    QMessageBox.warning(self, "错误", "新商品规格不能为空！")
                    return
                self.current_step += 1
            elif self.current_step == 4:
                if self.quantity_input.value() <= 0:
                    QMessageBox.warning(self, "错误", "数量必须大于 0！")
                    return
                self.current_step += 1
            elif self.current_step == 5:
                if self.unit_price_input.value() <= 0:
                    QMessageBox.warning(self, "错误", "单价必须大于 0！")
                    return
                self.current_step += 1
            elif self.current_step == 6:
                self.save_purchase()
                return

            self.stack.setCurrentIndex(self.current_step)
            self.prev_button.setEnabled(True)
            self.next_button.setText("确定" if self.current_step == 6 else "下一步")
        except Exception as e:
            log_debug(f"点击‘下一步’时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"操作失败: {str(e)}")

    def prev_step(self):
        try:
            if self.current_step > 0:
                if self.current_step in [2, 3]:
                    self.current_step = 0
                elif self.current_step == 4 and self.new_or_existing_combo.currentIndex() == 1:
                    self.current_step = 1
                    self.unit_combo.setEnabled(True)  # 恢复单位选择
                else:
                    self.current_step -= 1
                self.stack.setCurrentIndex(self.current_step)
                self.prev_button.setEnabled(self.current_step > 0)
                self.next_button.setText("下一步")
                self.next_button.setEnabled(True)
        except Exception as e:
            log_debug(f"点击‘上一步’时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"操作失败: {str(e)}")

    def save_purchase(self):
        try:
            if not os.path.exists(DB_PATH):
                log_debug(f"数据库文件不存在: {DB_PATH}")
                raise FileNotFoundError(f"数据库文件不存在: {DB_PATH}")

            conn = get_connection()
            cursor = conn.cursor()

            if self.new_or_existing_combo.currentIndex() == 0:
                item_name = self.new_item_name.text().strip()
                spec = self.new_item_spec.text().strip()
                try:
                    cursor.execute(
                        "INSERT INTO items (item_name, spec) VALUES (?, ?)",
                        (item_name, spec)
                    )
                    conn.commit()
                    self.item_id = cursor.lastrowid
                except sqlite3.IntegrityError:
                    cursor.execute(
                        "SELECT item_id FROM items WHERE item_name = ? AND spec = ?",
                        (item_name, spec)
                    )
                    result = cursor.fetchone()
                    if result:
                        self.item_id = result[0]
                    else:
                        raise Exception("无法创建或找到商品")
            else:
                self.item_id = self.selected_item["item_id"]

            date = self.date_input.date().toString("yyyy-MM-dd")
            unit = self.unit_combo.currentText()
            quantity = int(self.quantity_input.value())
            unit_price = float(self.unit_price_input.value())
            total_amount = quantity * unit_price
            remarks = self.remarks_input.text().strip() or None

            if self.purchase:  # 修改记录
                cursor.execute(
                    """
                    UPDATE purchases SET item_id = ?, brand_id = ?, quantity = ?, unit = ?,
                    unit_price = ?, total_amount = ?, date = ?, remarks = ?
                    WHERE purchase_id = ?
                    """,
                    (self.item_id, self.brand_id, quantity, unit, unit_price, total_amount,
                     date, remarks, self.purchase.purchase_id)
                )
            else:  # 新增记录
                cursor.execute(
                    """
                    INSERT INTO purchases (item_id, brand_id, quantity, unit, unit_price,
                    total_amount, date, remarks)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (self.item_id, self.brand_id, quantity, unit, unit_price, total_amount,
                     date, remarks)
                )
            conn.commit()
            conn.close()
            QMessageBox.information(self, "成功", "进货记录保存成功！")
            self.accept()
        except Exception as e:
            log_debug(f"保存进货记录时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
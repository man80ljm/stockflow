from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
                             QTableWidgetItem, QPushButton, QMessageBox, QDialog,
                             QFormLayout, QLineEdit, QComboBox, QDateEdit, QApplication,
                             QStackedWidget, QDoubleSpinBox, QHeaderView, QMenu, QCompleter)
from PyQt5.QtCore import QDate, Qt, QTimer, QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIntValidator
from database.queries import get_purchases_by_brand, get_connection, add_item, get_all_items
from database.db_setup import DB_PATH
from models.purchase import Purchase
import datetime
import traceback
import os
import sqlite3
from database.queries import (
    get_purchases_by_brand, get_connection, add_item, get_all_items, delete_purchase
)
import pandas as pd

# 调试日志文件路径
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug.log")

def log_debug(message):
    """记录调试信息到文件"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {message}\n")

class PurchaseDetailsWindow(QWidget):
    def __init__(self, brand, parent=None):
        super().__init__(parent)
        log_debug(f"初始化 PurchaseDetailsWindow for brand: {brand.brand_name}")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.brand = brand
        self.current_page = 1
        self.per_page = 20
        self.total_pages = 1
        self.purchases = []
        self.year = QDate.currentDate().year()
        self.month = QDate.currentDate().month()
        self.activity_windows = {}  # 新增：跟踪已打开的 ActivityInfoWindow 实例
        self.completion_windows = {}  # 跟踪 ActivityCompletionWindow 实例
        self.expense_windows = {}   # 跟踪 ExpenseInfoWindow 实例
        self.setWindowTitle(f"{self.brand.brand_name} - 进货详情")
        self.setGeometry(100, 100, 1400, 600)
        self.init_ui()
        self.load_purchases()
        self.center_on_screen()
        log_debug(f"完成 PurchaseDetailsWindow 初始化 for brand: {brand.brand_name}")
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
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        
        # 列宽自适应并支持手动拖动
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # 启用右键菜单
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
        # 操作按钮
        button_layout = QHBoxLayout()
        activity_button = QPushButton("当月活动")
        activity_button.clicked.connect(self.open_activity_screen)
        add_button = QPushButton("增加")
        add_button.clicked.connect(self.add_purchase)
        completion_button = QPushButton("活动完成情况")
        completion_button.clicked.connect(self.open_completion_screen)
        expense_button = QPushButton("支出情况")
        expense_button.clicked.connect(self.open_expense_screen)
        bill_button = QPushButton("账单导出")
        bill_button.clicked.connect(self.export_bill)
        button_layout.addWidget(activity_button)
        button_layout.addWidget(add_button)
        button_layout.addWidget(completion_button)
        button_layout.addWidget(expense_button)
        button_layout.addWidget(bill_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def open_activity_screen(self):
        from ui.activity_completion import ActivityCompletionWindow  # 改为新文件名
        key = (self.brand.brand_id, self.year, self.month)
        if key in self.activity_windows and self.activity_windows[key].isVisible():
            self.activity_windows[key].activateWindow()
            self.activity_windows[key].raise_()
        else:
            self.activity_windows[key] = ActivityCompletionWindow(self.brand, self.year, self.month, parent=self)
            self.activity_windows[key].show()

    def open_expense_screen(self):
        # 新增：支出情况窗口
        try:
            log_debug("尝试打开支出情况窗口")
            from ui.expense_info import ExpenseInfoWindow
            key = (self.brand.brand_id, self.year, self.month)
            
            # 清理无效引用
            if key in self.expense_windows:
                try:
                    if not self.expense_windows[key].isVisible():
                        del self.expense_windows[key]
                except (RuntimeError, ReferenceError):
                    del self.expense_windows[key]  # 强制移除可能已销毁的对象
                
            # 创建新窗口或激活现有窗口
            if key not in self.expense_windows:
                self.expense_windows[key] = ExpenseInfoWindow(self.brand, self.year, self.month, parent=None)
                self.expense_windows[key].setWindowModality(Qt.ApplicationModal)  # 设置为模态窗口
                self.expense_windows[key].show()
            else:
                self.expense_windows[key].activateWindow()
                self.expense_windows[key].raise_()
                
            log_debug(f"支出情况窗口状态: {self.expense_windows[key].isVisible()}")
            
        except Exception as e:
            log_debug(f"打开支出情况窗口时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"打开支出情况窗口失败: {str(e)}")


    def export_bill(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.date, i.item_name, i.spec, p.unit, p.quantity, p.unit_price, p.total_amount, p.remarks
                FROM purchases p
                JOIN items i ON p.item_id = i.item_id
                WHERE p.brand_id = ? AND strftime('%Y', p.date) = ? AND strftime('%m', p.date) = ?
                ORDER BY p.date
            """, (self.brand.brand_id, str(self.year), f"{self.month:02d}"))
            records = cursor.fetchall()
            conn.close()

            if not records:
                QMessageBox.warning(self, "警告", "没有找到符合条件的记录！")
                return

            df = pd.DataFrame(records, columns=["日期", "品名", "规格", "单位", "数量", "单价", "金额", "备注"])
            file_name = f"{self.brand.brand_name}_{self.year}年{self.month}月_进货详情.xlsx"
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", file_name)
            df.to_excel(file_path, index=False, engine='openpyxl')
            QMessageBox.information(self, "成功", f"账单已导出到：{file_path}")
        except Exception as e:
            log_debug(f"导出账单时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"导出账单失败: {str(e)}")

    def setup_date_filter(self):
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("选择月份："))

        # 创建年份选择框
        self.year_combo = QComboBox()
        current_year = QDate.currentDate().year()
        for year in range(current_year - 5, current_year + 5):
            self.year_combo.addItem(str(year))
        self.year_combo.setCurrentText(str(self.year)) # 设置当前年份
        self.year_combo.currentIndexChanged.connect(self.filter_by_date)

        # 创建月份选择框
        self.month_combo = QComboBox()
        for month in range(1, 13):
            self.month_combo.addItem(f"{month:02d}") # 格式化为 01, 02 ...
        self.month_combo.setCurrentIndex(self.month - 1) # 设置当前月份
        self.month_combo.currentIndexChanged.connect(self.filter_by_date)

        date_layout.addWidget(self.year_combo)
        date_layout.addWidget(QLabel("年"))
        date_layout.addWidget(self.month_combo)
        date_layout.addWidget(QLabel("月"))
        date_layout.addStretch()
        return date_layout

    def filter_by_date(self):
        # 从下拉框获取新的年月
        self.year = int(self.year_combo.currentText())
        self.month = int(self.month_combo.currentText())
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
                
                items_to_set = [
                    date_str, purchase.item_name, str(purchase.spec) if purchase.spec is not None else "", purchase.unit,
                    str(purchase.quantity), str(purchase.unit_price),
                    str(purchase.total_amount), purchase.remarks or ""
                ]

                for col, text in enumerate(items_to_set):
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, col, item)
            
            self.table.resizeColumnsToContents()
            font_metrics = self.table.fontMetrics()
            padding = font_metrics.horizontalAdvance('M') * 4 
            for col in range(self.table.columnCount()):
                current_width = self.table.columnWidth(col)
                self.table.setColumnWidth(col, current_width + padding)

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
        from ui.activity_info import ActivityInfoWindow
        key = (self.brand.brand_id, self.year, self.month)  # 使用 (brand_id, year, month) 作为键
        if key in self.activity_windows and self.activity_windows[key].isVisible():
            # 如果窗口已存在且可见，激活窗口
            self.activity_windows[key].activateWindow()
            self.activity_windows[key].raise_()
        else:
            # 创建新窗口并存储
            self.activity_windows[key] = ActivityInfoWindow(self.brand, self.year, self.month, parent=self)
            self.activity_windows[key].show()

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
            try:
                delete_purchase(purchase.purchase_id)  # 调用 queries.py 的函数
                self.load_purchases()
            except Exception as e:
                log_debug(f"删除进货记录时发生错误: {e}\n{traceback.format_exc()}")
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")

    def on_cell_double_clicked(self, row, column):
        if column == 7:
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

    def closeEvent(self, event):
        """从 AddBrandWindow 的跟踪列表中移除自身"""
        parent = self.parent()
        if parent and hasattr(parent, 'purchase_windows'):
            if self in parent.purchase_windows:
                parent.purchase_windows.remove(self)
        super().closeEvent(event)

    def open_completion_screen(self):
        from ui.activity_completion import ActivityCompletionWindow
        key = (self.brand.brand_id, self.year, self.month)
        if key in self.completion_windows:
            try:
                if self.completion_windows[key].isVisible():
                    self.completion_windows[key].activateWindow()
                    self.completion_windows[key].raise_()
                    return
            except RuntimeError:
                del self.completion_windows[key]  # 移除已删除的无效引用
        self.completion_windows[key] = ActivityCompletionWindow(self.brand, self.year, self.month, parent=None)
        self.completion_windows[key].setWindowModality(Qt.ApplicationModal)
        self.completion_windows[key].show()


class AddPurchaseDialog(QDialog):
    def __init__(self, brand_id, parent=None, purchase=None):
        super().__init__(parent)
        self.brand_id = brand_id
        self.purchase = purchase
        self.items = self.get_items_for_brand()
        self.current_step = 0
        self.item_id = None
        self.selected_item = None
        
        self.proxy_model = QSortFilterProxyModel(self)
        
        self.setWindowTitle("新增进货记录" if not purchase else "修改进货记录")
        self.init_ui()
        if purchase:
            self.populate_purchase_data()

    def populate_purchase_data(self):
        self.new_or_existing_combo.setCurrentIndex(1)
        self.current_step = 1
        self.stack.setCurrentIndex(self.current_step)
        
        for row in range(self.existing_item_model.rowCount()):
            source_index = self.existing_item_model.index(row, 0)
            item_id = self.existing_item_model.data(source_index, Qt.UserRole)
            if item_id == self.purchase.item_id:
                proxy_index = self.proxy_model.mapFromSource(source_index)
                if proxy_index.isValid():
                    self.existing_item_combo.setCurrentIndex(proxy_index.row())
                    self.on_item_selected(proxy_index.row())
                break

        self.quantity_input.setValue(self.purchase.quantity)
        self.unit_price_input.setValue(self.purchase.unit_price)
        date = QDate.fromString(self.purchase.date, "yyyy-MM-dd")
        self.date_input.setDate(date)
        self.remarks_input.setText(self.purchase.remarks or "")

    def get_items_for_brand(self):
        try:
            if not os.path.exists(DB_PATH):
                log_debug(f"数据库文件不存在: {DB_PATH}")
                raise FileNotFoundError(f"数据库文件不存在: {DB_PATH}")
            
            with get_connection() as conn:  # 使用 with 语句自动管理连接
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT i.item_id, i.item_name, i.spec, i.unit
                    FROM items i
                    WHERE i.brand_id = ?
                    """,
                    (self.brand_id,)
                )
                items = cursor.fetchall()
                log_debug(f"获取品牌 {self.brand_id} 的相关品类: {items}")
                return items
        except Exception as e:
            log_debug(f"获取品牌相关品类时发生错误: {e}\n{traceback.format_exc()}")
            return []

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
        self.existing_item_combo.lineEdit().setPlaceholderText("输入关键字进行搜索...")

        self.existing_item_model = QStandardItemModel()
        for item_id, item_name, spec, unit in self.items:
            display_text = f"{item_name} ({spec}, {unit})"
            model_item = QStandardItem(display_text)
            model_item.setData(item_id, Qt.UserRole)
            model_item.setData(item_name, Qt.UserRole + 1)
            model_item.setData(spec, Qt.UserRole + 2)
            model_item.setData(unit, Qt.UserRole + 3)
            self.existing_item_model.appendRow(model_item)

        self.proxy_model.setSourceModel(self.existing_item_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(0)

        self.existing_item_combo.setModel(self.proxy_model)
        self.existing_item_combo.setCurrentIndex(-1) # 默认不选中
        
        completer = self.existing_item_combo.completer()
        completer.setCompletionMode(QCompleter.PopupCompletion)
        self.existing_item_combo.lineEdit().textChanged.connect(self.on_search_text_changed)
        self.existing_item_combo.activated.connect(self.on_item_selected)

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
        step2_layout.addRow("品类名称:", self.new_item_name)
        self.step2_widget.setLayout(step2_layout)
        self.stack.addWidget(self.step2_widget)

        # 步骤 3：输入新商品规格
        self.step3_widget = QWidget()
        step3_layout = QFormLayout()
        self.new_item_spec = QLineEdit()
        self.new_item_spec.setPlaceholderText("请输入规格 (纯数字, 如: 12)") # 优化提示文本
        # 创建一个整数验证器，允许输入的范围是 1 到 99999
        validator = QIntValidator(1, 99999, self)
        self.new_item_spec.setValidator(validator)
        step3_layout.addRow("规格:", self.new_item_spec)
        self.step3_widget.setLayout(step3_layout)
        self.stack.addWidget(self.step3_widget)

        # 步骤 4：选择单位
        self.step4_widget = QWidget()
        step4_layout = QFormLayout()
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["件", "箱", "桶", "瓶", "盒", "杯", "组", "排"])
        step4_layout.addRow("单位:", self.unit_combo)
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

        # 设置回车键触发“下一步”
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
            if isinstance(obj, QComboBox) and obj.view().isVisible():
                return False
            if self.next_button.isEnabled():
                self.next_step()
                return True
        return super().eventFilter(obj, event)

    def on_new_or_existing_changed(self, index):
        try:
            log_debug(f"用户选择: 新增/已有选项 = {index}")
            if index == 1:  # 已有品类
                self.current_step = 1
                self.proxy_model.setFilterFixedString("")
                self.existing_item_combo.lineEdit().clear()
                if not self.items:
                    QMessageBox.information(self, "提示", "当前品牌没有可用品类，请先添加品类！")
                    self.next_button.setEnabled(False)
                else:
                    self.next_button.setEnabled(False)
                    QTimer.singleShot(100, self.existing_item_combo.setFocus)
            else:  # 新增品类
                self.current_step = 2
                self.next_button.setEnabled(True)
            self.stack.setCurrentIndex(self.current_step)
            self.prev_button.setEnabled(self.current_step > 0)
        except Exception as e:
            log_debug(f"处理品类选择变化时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"切换品类选择失败: {str(e)}")

    def on_search_text_changed(self, text):
        """处理搜索文本变化，确保不自动填充（借鉴自activity_info.py的稳定实现）"""
        try:
            log_debug(f"搜索文本变化: {text}")
            
            current_text = self.existing_item_combo.lineEdit().text()
            cursor_pos = self.existing_item_combo.lineEdit().cursorPosition()

            # 过滤模型并重置状态
            self.proxy_model.setFilterFixedString(text)
            self.next_button.setEnabled(False)
            self.selected_item = None 

            # 根据搜索结果显示或隐藏下拉列表
            if text and self.proxy_model.rowCount() > 0:
                self.existing_item_combo.showPopup()
            else:
                self.existing_item_combo.hidePopup()
            
            # --- 核心修正：使用信号阻断，防止递归调用导致闪退 ---
            self.existing_item_combo.lineEdit().blockSignals(True)
            # 如果自动补全器修改了文本，则强制恢复用户输入的文本和光标位置
            if self.existing_item_combo.lineEdit().text() != current_text:
                self.existing_item_combo.lineEdit().setText(current_text)
                self.existing_item_combo.lineEdit().setCursorPosition(cursor_pos)
            self.existing_item_combo.lineEdit().blockSignals(False)
            # --- 修正结束 ---
                
        except Exception as e:
            log_debug(f"on_search_text_changed 错误: {str(e)}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"搜索时发生错误: {str(e)}")


    def on_item_selected(self, index):
        """处理用户选择品类后的操作"""
        try:
            log_debug(f"用户选择索引: {index}")
            
            if index < 0:
                self.next_button.setEnabled(False)
                return
            
            proxy_index = self.proxy_model.index(index, 0)
            if not proxy_index.isValid(): return # 增加有效性检查

            source_index = self.proxy_model.mapToSource(proxy_index)
            item = self.existing_item_model.itemFromIndex(source_index)

            if item:
                display_text = f"{item.data(Qt.UserRole + 1)} ({item.data(Qt.UserRole + 2)}, {item.data(Qt.UserRole + 3)})"
                
                # 同样使用信号阻断来设置文本，确保万无一失
                self.existing_item_combo.lineEdit().blockSignals(True)
                self.existing_item_combo.lineEdit().setText(display_text)
                self.existing_item_combo.lineEdit().blockSignals(False)
                
                log_debug(f"用户选择了: {display_text}")
                
                self.selected_item = {
                    "item_id": item.data(Qt.UserRole),
                    "item_name": item.data(Qt.UserRole + 1),
                    "spec": item.data(Qt.UserRole + 2),
                    "unit": item.data(Qt.UserRole + 3)
                }
                
                self.unit_combo.setCurrentText(self.selected_item["unit"])
                self.unit_combo.setEnabled(False)
                
                self.next_button.setEnabled(True)
                self.existing_item_combo.hidePopup() # 增加：选择后主动隐藏下拉列表
            else:
                self.next_button.setEnabled(False)

                
        except Exception as e:
            log_debug(f"on_item_selected 错误: {str(e)}\n{traceback.format_exc()}")
            self.next_button.setEnabled(False)

    def next_step(self):
        try:
            if self.current_step == 0:
                if self.new_or_existing_combo.currentIndex() == 0:
                    self.current_step = 2
                else:
                    self.current_step = 1
                    self.existing_item_combo.lineEdit().clear()
                    self.selected_item = None
            elif self.current_step == 1:
                if not self.items:
                    QMessageBox.warning(self, "错误", "当前品牌没有可用品类！")
                    return
                if not self.selected_item:
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
                if self.new_or_existing_combo.currentIndex() == 1:
                    self.current_step += 1
                else:
                    self.current_step += 1
            elif self.current_step == 5:
                if self.quantity_input.value() <= 0:
                    QMessageBox.warning(self, "错误", "数量必须大于 0！")
                    return
                self.current_step += 1
            elif self.current_step == 6:
                if self.unit_price_input.value() <= 0:
                    QMessageBox.warning(self, "错误", "单价必须大于 0！")
                    return
                self.current_step += 1
            elif self.current_step == 7:
                self.save_purchase()
                return

            if self.new_or_existing_combo.currentIndex() == 1 and self.current_step == 4:
                self.stack.setCurrentIndex(5)
                self.current_step = 5
            else:
                self.stack.setCurrentIndex(self.current_step)

            self.prev_button.setEnabled(True)
            self.next_button.setText("确定" if self.current_step == 7 else "下一步")
        except Exception as e:
            log_debug(f"点击‘下一步’时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"操作失败: {str(e)}")

    def prev_step(self):
        try:
            if self.current_step > 0:
                if self.current_step in [2, 3]:
                    self.current_step = 0
                elif self.current_step == 5 and self.new_or_existing_combo.currentIndex() == 1:
                    self.current_step = 1
                    self.unit_combo.setEnabled(True)
                elif self.current_step == 4 and self.new_or_existing_combo.currentIndex() == 1:
                    self.current_step = 1
                    self.unit_combo.setEnabled(True)
                else:
                    self.current_step -= 1
                
                self.stack.setCurrentIndex(self.current_step)
                self.prev_button.setEnabled(self.current_step > 0)
                self.next_button.setText("下一步")
                self.next_button.setEnabled(True)
                if self.current_step == 1:
                    self.next_button.setEnabled(False)

        except Exception as e:
            log_debug(f"点击‘上一步’时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"操作失败: {str(e)}")

    def save_purchase(self):
        try:
            if not os.path.exists(DB_PATH):
                log_debug(f"数据库文件不存在: {DB_PATH}")
                raise FileNotFoundError(f"数据库文件不存在: {DB_PATH}")

            with get_connection() as conn:  # 使用 with 语句
                cursor = conn.cursor()

                if self.new_or_existing_combo.currentIndex() == 0:
                    item_name = self.new_item_name.text().strip()
                    spec = self.new_item_spec.text().strip()
                    unit = self.unit_combo.currentText()
                    try:
                        cursor.execute(
                            "SELECT item_id FROM items WHERE item_name = ? AND spec = ? AND unit = ? AND brand_id = ?",
                            (item_name, spec, unit, self.brand_id)
                        )
                        existing_item = cursor.fetchone()
                        if existing_item:
                            self.item_id = existing_item[0]
                        else:
                            cursor.execute(
                                "INSERT INTO items (item_name, spec, unit, brand_id) VALUES (?, ?, ?, ?)",
                                (item_name, spec, unit, self.brand_id)
                            )
                            self.item_id = cursor.lastrowid
                    except sqlite3.IntegrityError:
                        raise Exception("无法创建或找到商品")
                else:
                    self.item_id = self.selected_item["item_id"]

                date = self.date_input.date().toString("yyyy-MM-dd")
                unit = self.unit_combo.currentText()
                quantity = int(self.quantity_input.value())
                unit_price = float(self.unit_price_input.value())
                total_amount = quantity * unit_price
                remarks = self.remarks_input.text().strip() or None

                if self.purchase:
                    cursor.execute(
                        """
                        UPDATE purchases SET item_id = ?, brand_id = ?, quantity = ?, unit = ?,
                        unit_price = ?, total_amount = ?, date = ?, remarks = ?
                        WHERE purchase_id = ?
                        """,
                        (self.item_id, self.brand_id, quantity, unit, unit_price, total_amount,
                        date, remarks, self.purchase.purchase_id)
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO purchases (item_id, brand_id, quantity, unit, unit_price,
                        total_amount, date, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (self.item_id, self.brand_id, quantity, unit, unit_price, total_amount,
                        date, remarks)
                    )
                # 提交事务由 with 语句自动处理
            QMessageBox.information(self, "成功", "进货记录保存成功！")
            self.accept()
        except Exception as e:
            log_debug(f"保存进货记录时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox, QDateEdit, QApplication, QStackedWidget, QDoubleSpinBox, QHeaderView
from PyQt5.QtCore import QDate, Qt, QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from database.queries import get_purchases_by_brand, get_connection
from database.db_setup import DB_PATH
from models.purchase import Purchase
import datetime
import traceback
import os

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
        self.setWindowTitle(f"{self.brand.brand_name} - 进货详情")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()
        self.load_purchases()
        # 将窗口移动到屏幕中央
        self.center_on_screen()

    def center_on_screen(self):
        """将窗口移动到屏幕中央"""
        screen = QApplication.primaryScreen().geometry()
        window_size = self.geometry()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        self.move(x, y)

    def init_ui(self):
        # 主布局：垂直布局
        layout = QVBoxLayout()

        # 标题
        title_label = QLabel(f"{self.brand.brand_name} - 进货详情")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(title_label)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["序号", "日期", "品名", "规格", "单位", "数量", "单价", "金额", "备注"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        self.table.cellChanged.connect(self.on_cell_changed)
        # 允许用户调整列宽并自适应页面宽度
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionsMovable(True)  # 允许拖动列
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

    def load_purchases(self):
        """加载进货记录"""
        try:
            self.purchases = []
            purchase_data, total_records = get_purchases_by_brand(self.brand.brand_id, self.current_page, self.per_page)
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
                # 序号
                self.table.setItem(row, 0, QTableWidgetItem(str((self.current_page - 1) * self.per_page + row + 1)))
                # 日期：格式化为“YYYY年MM月DD日”
                date_str = datetime.datetime.strptime(purchase.date, "%Y-%m-%d").strftime("%Y年%m月%d日")
                self.table.setItem(row, 1, QTableWidgetItem(date_str))
                self.table.setItem(row, 2, QTableWidgetItem(purchase.item_name))
                self.table.setItem(row, 3, QTableWidgetItem(purchase.spec))
                self.table.setItem(row, 4, QTableWidgetItem(purchase.unit))
                self.table.setItem(row, 5, QTableWidgetItem(str(purchase.quantity)))
                self.table.setItem(row, 6, QTableWidgetItem(str(purchase.unit_price)))
                self.table.setItem(row, 7, QTableWidgetItem(str(purchase.total_amount)))
                self.table.setItem(row, 8, QTableWidgetItem(purchase.remarks or ""))
            self.table.resizeColumnsToContents()
        except Exception as e:
            log_debug(f"加载进货记录时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"加载进货记录失败: {str(e)}")

    def prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_purchases()

    def next_page(self):
        """下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_purchases()

    def open_activity_screen(self):
        """打开活动信息界面"""
        QMessageBox.information(self, "提示", "活动信息界面尚未实现！")

    def add_purchase(self):
        """新增进货记录"""
        try:
            log_debug(f"开始添加进货记录, brand_id: {self.brand.brand_id}")
            dialog = AddPurchaseDialog(self.brand.brand_id, self)
            if dialog.exec_():
                self.load_purchases()
        except Exception as e:
            log_debug(f"新增进货记录时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"新增进货记录失败: {str(e)}")

    def on_cell_changed(self, row, column):
        """处理单元格内容变化，更新备注"""
        try:
            if column == 8:  # 备注列
                purchase = self.purchases[row]
                new_remarks = self.table.item(row, column).text().strip() or None
                if new_remarks != purchase.remarks:
                    # 更新数据库
                    conn = None
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE purchases SET remarks = ? WHERE purchase_id = ?",
                            (new_remarks, purchase.purchase_id)
                        )
                        conn.commit()
                    finally:
                        if conn:
                            conn.close()
                    # 更新对象
                    purchase.remarks = new_remarks
                    QMessageBox.information(self, "成功", "备注已更新！")
        except Exception as e:
            log_debug(f"更新备注时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"更新备注失败: {str(e)}")

class AddPurchaseDialog(QDialog):
    def __init__(self, brand_id, parent=None):
        super().__init__(parent)
        self.brand_id = brand_id
        self.items = self.get_items_for_brand()
        self.current_step = 0
        self.item_id = None
        self.selected_item = None
        self.last_search_time = 0  # 用于防抖
        self.search_delay = 200  # 防抖延迟（毫秒）
        self.setWindowTitle("新增进货记录")
        log_debug(f"初始化 AddPurchaseDialog, brand_id: {brand_id}, items: {self.items}")
        self.init_ui()

    def get_items_for_brand(self):
        """获取当前品牌相关的品类"""
        conn = None
        try:
            # 检查数据库文件是否存在
            if not os.path.exists(DB_PATH):
                log_debug(f"数据库文件不存在: {DB_PATH}")
                raise FileNotFoundError(f"数据库文件不存在: {DB_PATH}")
            
            conn = get_connection()
            cursor = conn.cursor()
            # 确保一个 item_id 只与当前 brand_id 关联
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
            log_debug(f"获取品牌 {self.brand_id} 的相关品类: {items}")
            return items
        except Exception as e:
            log_debug(f"获取品牌相关品类时发生错误: {e}\n{traceback.format_exc()}")
            return []
        finally:
            if conn:
                conn.close()

    def init_ui(self):
        try:
            self.main_layout = QVBoxLayout()
            
            # 使用 QStackedWidget 管理多个步骤页面
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

            # 步骤 1.5：已有品类模糊搜索（仅在选择“已有品类”时显示）
            self.step1_5_widget = QWidget()
            step1_5_layout = QFormLayout()
            self.existing_item_combo = QComboBox()
            self.existing_item_combo.setEditable(True)
            self.existing_item_combo.setInsertPolicy(QComboBox.NoInsert)
            self.existing_item_combo.clearEditText()  # 确保初始为空
            self.existing_item_model = QStandardItemModel()
            for item in self.items:
                display_text = f"{item[1]} ({item[2]})"
                model_item = QStandardItem(display_text)
                model_item.setData(item[0], Qt.UserRole)  # 存储 item_id
                model_item.setData(item[1], Qt.UserRole + 1)  # 存储 item_name
                model_item.setData(item[2], Qt.UserRole + 2)  # 存储 spec
                self.existing_item_model.appendRow(model_item)
                self.existing_item_combo.addItem(display_text)
            self.existing_item_combo.setModel(self.existing_item_model)
            self.existing_item_combo.editTextChanged.connect(self.on_search_text_changed)
            self.existing_item_combo.currentIndexChanged.connect(self.on_item_selected)
            step1_5_layout.addRow("选择已有品类：", self.existing_item_combo)
            self.step1_5_widget.setLayout(step1_5_layout)
            self.stack.addWidget(self.step1_5_widget)

            # 步骤 2：输入新商品名称（仅在选择“新增品类”时显示）
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

            # 步骤 5：输入数量（仅数字）
            self.step5_widget = QWidget()
            step5_layout = QFormLayout()
            self.quantity_input = QDoubleSpinBox()
            self.quantity_input.setDecimals(0)  # 仅整数
            self.quantity_input.setMinimum(1)
            self.quantity_input.setMaximum(999999)
            step5_layout.addRow("数量：", self.quantity_input)
            self.step5_widget.setLayout(step5_layout)
            self.stack.addWidget(self.step5_widget)

            # 步骤 6：输入单价（仅数字）
            self.step6_widget = QWidget()
            step6_layout = QFormLayout()
            self.unit_price_input = QDoubleSpinBox()
            self.unit_price_input.setDecimals(2)  # 保留两位小数
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
            self.next_button.setEnabled(True)  # 初始状态始终启用“下一步”
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
        except Exception as e:
            log_debug(f"初始化 UI 时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"初始化界面失败: {str(e)}")

    def eventFilter(self, obj, event):
        try:
            if event.type() == event.KeyPress and event.key() in (Qt.Key_Enter, Qt.Key_Return):
                if self.current_step < 6:  # 最后一步不触发“下一步”
                    self.next_step()
                return True
            return super().eventFilter(obj, event)
        except Exception as e:
            log_debug(f"处理事件过滤器时发生错误: {e}\n{traceback.format_exc()}")
            return False

    def on_new_or_existing_changed(self, index):
        """处理新增品类或已有品类的选择"""
        try:
            log_debug(f"用户选择: 新增/已有选项 = {index}")
            # 断开信号槽，避免切换页面时触发
            self.existing_item_combo.editTextChanged.disconnect(self.on_search_text_changed)
            self.existing_item_combo.currentIndexChanged.disconnect(self.on_item_selected)

            if index == 1:  # 选择了“已有品类”
                self.current_step = 1  # 跳转到步骤 1.5
                self.existing_item_combo.clearEditText()  # 清空输入框
                # 如果没有可用品类，禁用“下一步”并提示
                if not self.items:
                    QMessageBox.information(self, "提示", "当前品牌没有可用品类，请先添加品类！")
                    self.next_button.setEnabled(False)
                else:
                    self.next_button.setEnabled(False)  # 等待用户选择品类
                    # 延迟设置焦点，避免立即触发信号
                    QTimer.singleShot(100, self.existing_item_combo.setFocus)
            else:
                self.current_step = 2  # 直接跳转到输入新商品名称
                self.next_button.setEnabled(True)
            self.stack.setCurrentIndex(self.current_step)
            self.prev_button.setEnabled(self.current_step > 0)

            # 重新连接信号槽
            self.existing_item_combo.editTextChanged.connect(self.on_search_text_changed)
            self.existing_item_combo.currentIndexChanged.connect(self.on_item_selected)
        except Exception as e:
            log_debug(f"处理品类选择变化时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"切换品类选择失败: {str(e)}")

    def on_search_text_changed(self, text):
        """模糊搜索已有品类"""
        try:
            # 防抖：限制触发频率
            current_time = datetime.datetime.now().timestamp() * 1000  # 毫秒
            if current_time - self.last_search_time < self.search_delay:
                return
            self.last_search_time = current_time

            if not self.items:  # 如果品类列表为空，直接返回
                self.next_button.setEnabled(False)
                return
            
            text = text.lower().strip()
            # 保存当前选择的项目ID（如果有）
            current_id = None
            if self.existing_item_combo.currentIndex() >= 0:
                current_item = self.existing_item_model.item(self.existing_item_combo.currentIndex())
                if current_item:
                    current_id = current_item.data(Qt.UserRole)
            
            self.existing_item_model.clear()
            matched_items = False
            selected_index = -1
            
            for idx, item in enumerate(self.items):
                display_text = f"{item[1]} ({item[2]})"
                if not text or text in display_text.lower():
                    model_item = QStandardItem(display_text)
                    model_item.setData(item[0], Qt.UserRole)  # 存储 item_id
                    model_item.setData(item[1], Qt.UserRole + 1)  # 存储 item_name
                    model_item.setData(item[2], Qt.UserRole + 2)  # 存储 spec
                    self.existing_item_model.appendRow(model_item)
                    matched_items = True
                    
                    # 如果是之前选中的项目，记录新索引
                    if current_id and item[0] == current_id:
                        selected_index = self.existing_item_model.rowCount() - 1
            
            # 如果找到之前选中的项目，重新选中它
            if selected_index >= 0:
                self.existing_item_combo.setCurrentIndex(selected_index)
                self.next_button.setEnabled(True)
            else:
                self.next_button.setEnabled(False)
                
            log_debug(f"搜索文本变化: {text}, 匹配项: {matched_items}")
        except Exception as e:
            log_debug(f"搜索品类时发生错误: {e}\n{traceback.format_exc()}")
            self.next_button.setEnabled(False)

    def on_item_selected(self, index):
        """当用户选择一个品类时，启用‘下一步’按钮"""
        try:
            if index >= 0 and self.existing_item_combo.currentText():
                item = self.existing_item_model.item(index)
                if item:  # 确保选中的项存在
                    self.next_button.setEnabled(True)
                    # 立即存储选中的品类信息，避免后续步骤重新查询
                    self.selected_item = {
                        "item_id": item.data(Qt.UserRole),
                        "item_name": item.data(Qt.UserRole + 1),
                        "spec": item.data(Qt.UserRole + 2)
                    }
                    log_debug(f"已选择品类: {self.selected_item}")
                else:
                    self.next_button.setEnabled(False)
            else:
                self.next_button.setEnabled(False)
            log_debug(f"品类选择索引: {index}")
        except Exception as e:
            log_debug(f"处理品类选择时发生错误: {e}\n{traceback.format_exc()}")
            self.next_button.setEnabled(False)

    def next_step(self):
        try:
            log_debug(f"当前步骤: {self.current_step}")
            # 验证当前步骤的输入
            if self.current_step == 0:
                if self.new_or_existing_combo.currentIndex() == 0:  # 选择了“新增品类”
                    self.current_step = 2  # 直接跳转到输入新商品名称
                else:
                    self.current_step = 1  # 跳转到步骤 1.5（已有品类）
            elif self.current_step == 1:
                if not self.items:
                    QMessageBox.warning(self, "错误", "当前品牌没有可用品类！")
                    return
                
                # 使用已存储的选择信息，而不是重新查询
                if not hasattr(self, 'selected_item') or not self.selected_item:
                    QMessageBox.warning(self, "错误", "请选择一个有效的品类！")
                    return
                
                self.item_id = self.selected_item["item_id"]
                if self.item_id is None:
                    log_debug("品类 item_id 为空")
                    QMessageBox.warning(self, "错误", "品类数据无效！")
                    return
                
                # 自动选择最近一次使用的单位（如果没有历史记录，默认为“件”）
                conn = None
                try:
                    if not os.path.exists(DB_PATH):
                        log_debug(f"数据库文件不存在: {DB_PATH}")
                        raise FileNotFoundError(f"数据库文件不存在: {DB_PATH}")
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT unit FROM purchases WHERE item_id = ? ORDER BY date DESC LIMIT 1",
                        (self.item_id,)
                    )
                    result = cursor.fetchone()
                    unit = result[0] if result else "件"
                    self.unit_combo.setCurrentText(unit)
                    log_debug(f"查询到的单位: {unit}")
                except Exception as e:
                    log_debug(f"查询单位时发生错误: {e}\n{traceback.format_exc()}")
                    unit = "件"
                    self.unit_combo.setCurrentText(unit)
                finally:
                    if conn:
                        conn.close()
                self.current_step = 4  # 跳到输入数量
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
            if self.current_step == 6:
                self.next_button.setText("确定")
            else:
                self.next_button.setText("下一步")
        except Exception as e:
            log_debug(f"点击‘下一步’时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"操作失败: {str(e)}")

    def prev_step(self):
        try:
            if self.current_step > 0:
                # 如果是从“新增品类”路径（步骤 2 或 3），直接返回到品类选择（步骤 0）
                if self.current_step in [2, 3] and self.new_or_existing_combo.currentIndex() == 0:
                    self.current_step = 0
                # 如果是从数量输入（步骤 4）且是“已有品类”路径，返回到选择品类（步骤 1）
                elif self.current_step == 4 and self.new_or_existing_combo.currentIndex() == 1:
                    self.current_step = 1
                else:
                    self.current_step -= 1
                if self.current_step == 0:
                    self.new_or_existing_combo.setCurrentIndex(0)
                self.stack.setCurrentIndex(self.current_step)
                self.prev_button.setEnabled(self.current_step > 0)
                self.next_button.setText("下一步")
                self.next_button.setEnabled(True)
        except Exception as e:
            log_debug(f"点击‘上一步’时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"操作失败: {str(e)}")

    def save_purchase(self):
        try:
            # 保存商品（如果是新增商品）
            if self.new_or_existing_combo.currentIndex() == 0:
                if not os.path.exists(DB_PATH):
                    log_debug(f"数据库文件不存在: {DB_PATH}")
                    raise FileNotFoundError(f"数据库文件不存在: {DB_PATH}")
                conn = None
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    item_name = self.new_item_name.text().strip()
                    spec = self.new_item_spec.text().strip()
                    try:
                        cursor.execute(
                            "INSERT INTO items (item_name, spec) VALUES (?, ?)",
                            (item_name, spec)
                        )
                        conn.commit()
                        self.item_id = cursor.lastrowid
                    except Exception as e:
                        cursor.execute(
                            "SELECT item_id FROM items WHERE item_name = ? AND spec = ?",
                            (item_name, spec)
                        )
                        result = cursor.fetchone()
                        if result:
                            self.item_id = result[0]
                        else:
                            raise Exception("无法创建或找到商品")
                finally:
                    if conn:
                        conn.close()
            else:
                self.item_id = self.selected_item["item_id"]

            date = self.date_input.date().toString("yyyy-MM-dd")
            unit = self.unit_combo.currentText()
            quantity = int(self.quantity_input.value())
            unit_price = float(self.unit_price_input.value())
            total_amount = quantity * unit_price
            remarks = self.remarks_input.text().strip() or None

            purchase = Purchase(
                purchase_id=None, item_id=self.item_id, brand_id=self.brand_id,
                quantity=quantity, unit=unit, unit_price=unit_price,
                total_amount=total_amount, date=date, remarks=remarks,
                item_name=None, spec=None
            )
            purchase_id = purchase.save()
            if purchase_id:
                QMessageBox.information(self, "成功", "进货记录添加成功！")
                self.accept()
            else:
                QMessageBox.warning(self, "错误", "添加进货记录失败！")
        except Exception as e:
            log_debug(f"保存进货记录时发生错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
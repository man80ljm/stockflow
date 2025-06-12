import sys
import traceback
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QDialog, QFormLayout, QComboBox, QCheckBox, 
                            QMessageBox, QStackedWidget, QRadioButton, QCompleter,QAbstractItemView)
from PyQt5.QtGui import QDoubleValidator, QStandardItemModel, QStandardItem,QIntValidator
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from database.queries import (get_monthly_activities, add_activity, delete_activity, 
                             get_all_items, add_item)
import os
import datetime
from database.queries import (
    get_monthly_activities, add_activity, delete_activity, 
    get_all_items, add_item, get_connection
)

# 建议也为这个文件添加日志功能，方便调试
def log_activity_debug(message):
    try:
        with open("activity_debug.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now()}] {message}\n")
    except:
        pass # 日志失败不应影响主程序

# 定义 log_debug 函数，复用 purchase_details.py 的逻辑
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug.log")
def log_debug(message):
    """记录调试信息到文件"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {message}\n")

from ui.base_window import CenteredMainWindow  # 导入基类
class ActivityInfoWindow(CenteredMainWindow):
    """活动信息管理窗口"""
    
    def __init__(self, brand, year, month,parent=None):
        super().__init__(parent)
        self.brand = brand
        self.year = year
        self.month = month
        self.setWindowTitle(f"{brand.brand_name} - {year}年{month}月活动")
        self.resize(1600, 600)
        self.center_on_screen()  # 确保在调整大小后居中
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 总销量目标区域
        total_group = QWidget()
        total_layout = QHBoxLayout(total_group)
        self.total_target_input = QLineEdit()
        self.total_target_input.setValidator(QDoubleValidator(0, 9999999, 2))
        self.total_target_input.setPlaceholderText("输入总销售额目标")
        total_layout.addWidget(QLabel("总销售额目标 (元):"))
        total_layout.addWidget(self.total_target_input)
        save_total_btn = QPushButton("保存")
        save_total_btn.clicked.connect(self.save_total_target)
        total_layout.addWidget(save_total_btn)
        layout.addWidget(total_group)
        
        # 单品活动区域
        item_group = QWidget()
        item_layout = QVBoxLayout(item_group)
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(9)
        self.activity_table.setHorizontalHeaderLabels([
            "商品名称", "规格", "活动类型", "需总销量", "需单品销量", 
            "目标值", "原价", "优惠价", "操作"
        ])
        self.activity_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        add_btn = QPushButton("添加单品活动")
        add_btn.clicked.connect(self.open_add_dialog)
        item_layout.addWidget(self.activity_table)
        item_layout.addWidget(add_btn)
        layout.addWidget(item_group)
        
        self.load_activities()

    def load_activities(self):
        self.activity_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        """加载活动数据，防止重复和空行"""
        activities = get_monthly_activities(self.brand.brand_id, self.year, self.month)
        self.activity_table.setRowCount(0)
        seen_items = set()  # 跟踪已添加的 item_id
        if not activities:
            self.activity_table.insertRow(0)
            self.activity_table.setItem(0, 0, QTableWidgetItem("无数据"))
            log_activity_debug(f"无活动数据 for brand: {self.brand.brand_name}, year: {self.year}, month: {self.month}")
            return
        
        for activity in activities:
            row = self.activity_table.rowCount()
            activity_id, is_total, item_id, activity_type, need_total, need_item, target_value, \
            original_price, discount_price, item_name, spec, unit = activity
            
            if is_total:
                self.total_target_input.setText(str(target_value))
                continue
                
            # 防止重复添加
            if item_id and item_id in seen_items:
                continue
            seen_items.add(item_id)
            
            self.activity_table.insertRow(row)

            # 第0列: 商品名称
            item0 = QTableWidgetItem(item_name or "")
            item0.setTextAlignment(Qt.AlignCenter)
            self.activity_table.setItem(row, 0, item0)

            # 第1列: 规格
            item1 = QTableWidgetItem(str(spec) if spec is not None else "")
            item1.setTextAlignment(Qt.AlignCenter)
            self.activity_table.setItem(row, 1, item1)

            # 第2列: 活动类型
            item2 = QTableWidgetItem(activity_type or "")
            item2.setTextAlignment(Qt.AlignCenter)
            self.activity_table.setItem(row, 2, item2)

            # 第3列: 需总销量
            item3 = QTableWidgetItem("是" if need_total else "否")
            item3.setTextAlignment(Qt.AlignCenter)
            self.activity_table.setItem(row, 3, item3)

            # 第4列: 需单品销量
            item4 = QTableWidgetItem("是" if need_item else "否")
            item4.setTextAlignment(Qt.AlignCenter)
            self.activity_table.setItem(row, 4, item4)

            # 第5列: 目标值
            item5 = QTableWidgetItem(str(target_value))
            item5.setTextAlignment(Qt.AlignCenter)
            self.activity_table.setItem(row, 5, item5)

            # 第6列: 原价
            item6 = QTableWidgetItem(str(original_price or ""))
            item6.setTextAlignment(Qt.AlignCenter)
            self.activity_table.setItem(row, 6, item6)

            # 第7列: 优惠价
            item7 = QTableWidgetItem(str(discount_price or ""))
            item7.setTextAlignment(Qt.AlignCenter)
            self.activity_table.setItem(row, 7, item7)
            
            # 第8列: 操作按钮
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda checked, aid=activity_id: self.delete_activity(aid))
            self.activity_table.setCellWidget(row, 8, delete_btn)

            # 列宽自适应
            self.activity_table.resizeColumnsToContents()
            font_metrics = self.activity_table.fontMetrics()
            padding = font_metrics.horizontalAdvance('M') * 4
            for col in range(self.activity_table.columnCount()):
                current_width = self.activity_table.columnWidth(col)
                self.activity_table.setColumnWidth(col, current_width + padding)


    def save_total_target(self):
        """保存总销量目标"""
        try:
            target_value = float(self.total_target_input.text())
            if target_value <= 0:
                raise ValueError("目标值必须大于0")
            add_activity(self.brand.brand_id, f"{self.year}-{self.month:02d}", True, None,
                        None, False, False, target_value, None, None)
            QMessageBox.information(self, "成功", "总销量目标已保存")
            # --- 修改代码：增强自动刷新 ---
            # 通知父窗口中的 ActivityCompletionWindow 和 ExpenseInfoWindow 刷新
            parent = self.parent()
            if parent and hasattr(parent, 'completion_windows'):
                key = (self.brand.brand_id, self.year, self.month)
                if key in parent.completion_windows:
                    try:
                        parent.completion_windows[key].load_completion_data()
                        log_activity_debug(f"自动刷新 ActivityCompletionWindow for brand: {self.brand.brand_name}, year: {self.year}, month: {self.month}")
                    except Exception as e:
                        log_activity_debug(f"自动刷新 ActivityCompletionWindow 失败: {e}")
            if parent and hasattr(parent, 'expense_windows'):
                if key in parent.expense_windows:
                    try:
                        parent.expense_windows[key].load_expense_data()
                        log_activity_debug(f"自动刷新 ExpenseInfoWindow for brand: {self.brand.brand_name}, year: {self.year}, month: {self.month}")
                    except Exception as e:
                        log_activity_debug(f"自动刷新 ExpenseInfoWindow 失败: {e}")
            # --- 结束修改代码 ---
        except ValueError as e:
            QMessageBox.warning(self, "错误", f"请输入有效的金额: {str(e)}")

    def open_add_dialog(self):
        """打开添加单品活动对话框"""
        dialog = AddItemActivityDialog(self.brand.brand_id, self.year, self.month)
        if dialog.exec_() == QDialog.Accepted:
            self.load_activities()

    def delete_activity(self, activity_id):
        """删除指定活动"""
        reply = QMessageBox.question(self, "确认", "确定删除此活动?", 
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            delete_activity(activity_id)
            self.load_activities()

    def closeEvent(self, event):
        """在窗口关闭时从父窗口的 activity_windows 字典中移除自身"""
        parent = self.parent()
        if parent and hasattr(parent, 'activity_windows'):
            key = (self.brand.brand_id, self.year, self.month)
            if key in parent.activity_windows:
                del parent.activity_windows[key]
        super().closeEvent(event)

from ui.base_window import CenteredDialog  # 导入基类
class AddItemActivityDialog(CenteredDialog):
    """添加单品活动对话框"""
    
    def __init__(self, brand_id, year, month):
        super().__init__()
        self.brand_id = brand_id
        self.year = year
        self.month = month
        self.selected_item = None
        self.setWindowTitle("添加单品活动")
        self.resize(450, 350)
        self.center_on_screen()  # 确保在调整大小后居中
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        self.stack = QStackedWidget()

        # 步骤1: 选择新增或已有品类
        step1 = QWidget()
        step1_layout = QVBoxLayout(step1)
        self.new_item_radio = QRadioButton("新增品类")
        self.existing_item_radio = QRadioButton("已有品类")
        self.new_item_radio.setChecked(True)
        step1_layout.addWidget(QLabel("请选择品类类型:"))
        step1_layout.addWidget(self.new_item_radio)
        step1_layout.addWidget(self.existing_item_radio)
        self.stack.addWidget(step1)

        # 步骤2: 输入品类详情
        step2 = QWidget()
        step2_layout = QFormLayout(step2)
        self.new_item_name = QLineEdit(placeholderText="请输入品类名称")
        self.new_item_spec = QLineEdit()
        self.new_item_spec.setPlaceholderText("请输入规格 (纯数字, 如: 12)") # 优化提示文本
        # 创建一个整数验证器，允许输入的范围是 1 到 99999
        validator = QIntValidator(1, 99999, self)
        self.new_item_spec.setValidator(validator)
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["件", "箱", "桶", "瓶", "盒", "杯", "组", "排"])
        self.existing_item_combo = QComboBox()
        self.existing_item_combo.setEditable(True)
        self.existing_item_combo.setInsertPolicy(QComboBox.NoInsert)
        self.existing_item_combo.lineEdit().setPlaceholderText("输入关键字进行搜索...")

        self.existing_item_model = QStandardItemModel()
        items = get_all_items(self.brand_id)
        for item_id, item_name, spec, unit in items:
            display_text = f"{item_name} ({spec}, {unit})"
            model_item = QStandardItem(display_text)
            model_item.setData(item_id, Qt.UserRole)
            model_item.setData(item_name, Qt.UserRole + 1)
            model_item.setData(spec, Qt.UserRole + 2)
            model_item.setData(unit, Qt.UserRole + 3)
            self.existing_item_model.appendRow(model_item)

        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.existing_item_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(0)

        self.existing_item_combo.setModel(self.proxy_model)

        self.existing_item_combo.setCurrentIndex(-1)
        
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
        step2_layout.addRow("品类名称:", self.new_item_name)
        step2_layout.addRow("规格:", self.new_item_spec)
        step2_layout.addRow("单位:", self.unit_combo)
        step2_layout.addRow("选择已有品类:", self.existing_item_combo)
        self.stack.addWidget(step2)

        # 步骤3: 选择活动类型和配置
        step3 = QWidget()
        # ... (步骤3的代码保持不变) ...
        step3_layout = QFormLayout(step3)
        self.activity_type = QComboBox()
        self.activity_type.addItems(["案后结", "案后结(不与总指标挂钩)", "特价", "随货搭"])
        self.need_total = QCheckBox("需完成总销量")
        self.need_item = QCheckBox("需完成单品销量")
        self.target_value = QLineEdit()
        self.target_value.setValidator(QDoubleValidator(0, 999999, 2))
        self.target_value.setPlaceholderText("输入目标值")
        self.original_price = QLineEdit()
        self.original_price.setValidator(QDoubleValidator(0.01, 9999, 2))
        self.original_price.setPlaceholderText("输入原价")
        self.discount_price = QLineEdit()
        self.discount_price.setValidator(QDoubleValidator(0.01, 9999, 2))
        self.discount_price.setPlaceholderText("输入优惠价")
        step3_layout.addRow("活动类型:", self.activity_type)
        step3_layout.addRow("", self.need_total)
        step3_layout.addRow("", self.need_item)
        step3_layout.addRow("目标值:", self.target_value)
        step3_layout.addRow("原价:", self.original_price)
        step3_layout.addRow("优惠价:", self.discount_price)
        self.stack.addWidget(step3)

        layout.addWidget(self.stack)
        nav_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("上一步")
        self.next_button = QPushButton("下一步")
        self.finish_button = QPushButton("完成")
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        nav_layout.addWidget(self.finish_button)

        layout.addLayout(nav_layout)

        self.prev_button.clicked.connect(self.prev_step)
        self.next_button.clicked.connect(self.next_step)
        self.finish_button.clicked.connect(self.save_activity)

        # 添加 need_item 的状态变化监听
        self.need_item.toggled.connect(self.update_target_value_state)

        # --- 新增代码：监听活动类型变化 ---
        self.activity_type.currentIndexChanged.connect(self.update_need_total_state)
        # 初始化 need_total 状态
        self.update_need_total_state()

        # 初始化目标值输入框状态（默认未勾选，禁用）
        self.update_target_value_state(False)

        # 注意：这里只连接信号，不做任何按钮状态的判断
        self.new_item_radio.toggled.connect(self.toggle_item_view)
        self.current_step = 0
        
        self.toggle_item_view() # 初始化时调用一次，确保界面正确
        self.update_buttons()   # 初始化时调用一次，确保按钮状态正确

    def update_need_total_state(self):
        """根据活动类型更新 '需完成总销量' 复选框状态"""
        is_no_total_target = self.activity_type.currentText() == "案后结(不与总指标挂钩)"
        if is_no_total_target:
            self.need_total.setEnabled(False)
            self.need_total.setChecked(False)  # 强制取消勾选
            log_activity_debug("Disabled need_total for activity type: 案后结(不与总指标挂钩)")
        else:
            self.need_total.setEnabled(True)
            log_activity_debug(f"Enabled need_total for activity type: {self.activity_type.currentText()}")

    # 添加 update_target_value_state 方法
    def update_target_value_state(self, checked):
        """根据 '需完成单品销量' 复选框状态更新 '目标值' 输入框"""
        if checked:
            self.target_value.setEnabled(True)
            self.target_value.clear()  # 清空内容，允许用户输入
        else:
            self.target_value.setEnabled(False)
            self.target_value.setText("0")  # 设置为默认值 0

    def toggle_item_view(self):
        """
        核心修改点 1: 此函数现在只负责切换界面元素的显示/隐藏
        不再处理任何按钮的启用/禁用逻辑
        """
        is_new = self.new_item_radio.isChecked()
        self.new_item_name.setVisible(is_new)
        self.new_item_spec.setVisible(is_new)
        self.unit_combo.setVisible(is_new)
        self.existing_item_combo.setVisible(not is_new)

    def prev_step(self):
        """返回上一步"""
        if self.current_step > 0:
            if self.current_step == 1:
                self.existing_item_combo.lineEdit().clear()
                self.selected_item = None

            self.current_step -= 1
            self.stack.setCurrentIndex(self.current_step)
            self.update_buttons()

    def next_step(self):
        """前往下一步"""
        if self.current_step == 1 and self.new_item_radio.isChecked():
            if not self.new_item_name.text().strip() or not self.new_item_spec.text().strip():
                QMessageBox.warning(self, "输入错误", "品类名称和规格不能为空！")
                return

        if self.current_step < 2:
            self.current_step += 1
            self.stack.setCurrentIndex(self.current_step)
            self.toggle_item_view() # 切换页面后，确保控件显示正确
            self.update_buttons()   # 切换页面后，更新按钮状态

    def update_buttons(self):
        """
        核心修改点 2: 此函数成为按钮状态管理的唯一中心
        """
        self.prev_button.setEnabled(self.current_step > 0)
        self.next_button.setVisible(self.current_step < 2)
        self.finish_button.setVisible(self.current_step == 2)
        
        # 根据当前在哪一步，来决定“下一步”按钮是否可用
        if self.current_step == 0:
            # 在第一步，无论如何“下一步”都可用
            self.next_button.setEnabled(True)
        elif self.current_step == 1:
            # 在第二步，需要分情况讨论
            if self.new_item_radio.isChecked():
                # 新增品类模式，下一步可用
                self.next_button.setEnabled(True)
            else:
                # 已有品类模式，必须选择了品类后，下一步才可用
                self.next_button.setEnabled(self.selected_item is not None)

    def on_search_text_changed(self, text):
        """处理搜索文本变化，禁止自动填充，并增加错误处理"""
        try:
            current_text = self.existing_item_combo.lineEdit().text()
            cursor_pos = self.existing_item_combo.lineEdit().cursorPosition()

            self.proxy_model.setFilterFixedString(text)
            
            self.selected_item = None
            self.update_buttons()

            # 恢复用户输入的文本和光标，防止QCompleter自动填充
            if self.existing_item_combo.lineEdit().text() != current_text:
                self.existing_item_combo.lineEdit().setText(current_text)
                self.existing_item_combo.lineEdit().setCursorPosition(cursor_pos)

            if text and self.proxy_model.rowCount() > 0:
                self.existing_item_combo.showPopup()
            else:
                self.existing_item_combo.hidePopup()
        except Exception as e:
            log_activity_debug(f"搜索时发生严重错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "严重错误", f"搜索功能出现异常: {e}")

    def on_item_selected(self, index):
        """处理用户从下拉列表选择品类后的操作，并增加错误处理"""
        try:
            if index < 0:
                return
            
            proxy_index = self.proxy_model.index(index, 0)
            source_index = self.proxy_model.mapToSource(proxy_index)
            item = self.existing_item_model.itemFromIndex(source_index)

            if item:
                self.existing_item_combo.lineEdit().blockSignals(True)
                self.existing_item_combo.lineEdit().setText(item.text())
                self.existing_item_combo.lineEdit().blockSignals(False)
                
                self.selected_item = {
                    "item_id": item.data(Qt.UserRole),
                    "item_name": item.data(Qt.UserRole + 1),
                    "spec": item.data(Qt.UserRole + 2),
                    "unit": item.data(Qt.UserRole + 3)
                }
                self.update_buttons()
                self.existing_item_combo.hidePopup()
        except Exception as e:
            log_activity_debug(f"选择项目时发生严重错误: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "严重错误", f"选择项目时出现异常: {e}")
            self.selected_item = None
            self.update_buttons()

    def save_activity(self):
        """保存活动到数据库"""
        if not self.validate_inputs():
            return
        
        item_id = None
        item_name = None
        
        with get_connection() as conn:  # 使用 with 语句自动管理连接
            cursor = conn.cursor()
            try:
                if self.new_item_radio.isChecked():
                    item_name = self.new_item_name.text().strip()
                    spec = self.new_item_spec.text().strip()
                    unit = self.unit_combo.currentText()
                    
                    # 检查 items 表中是否已存在相同商品
                    cursor.execute(
                        "SELECT item_id FROM items WHERE item_name = ? AND spec = ? AND unit = ? AND brand_id = ?",
                        (item_name, spec, unit, self.brand_id)
                    )
                    existing_item = cursor.fetchone()
                    if existing_item:
                        QMessageBox.warning(self, "错误", f"商品 '{item_name} ({spec}, {unit})' 已存在，无法重复添加！")
                        return
                    item_id = add_item(item_name, spec, unit, self.brand_id)
                else:
                    if self.selected_item:
                        item_id = self.selected_item['item_id']
                        item_name = self.selected_item['item_name']
                    else:
                        QMessageBox.warning(self, "错误", "请选择一个有效的已有品类。")
                        return
                
                # 检查当月活动中是否已存在该商品的活动
                month_str = f"{self.year}-{self.month:02d}"
                cursor.execute(
                    "SELECT COUNT(*) FROM activities WHERE brand_id = ? AND month = ? AND item_id = ?",
                    (self.brand_id, month_str, item_id)
                )
                if cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "错误", f"当月活动中已存在商品 '{item_name}' 的活动，无法重复添加！")
                    return
                
                activity_type = self.activity_type.currentText()
                need_total = self.need_total.isChecked()
                need_item = self.need_item.isChecked()
                target_value = float(self.target_value.text()) if self.target_value.text() else 0
                original_price = float(self.original_price.text()) if self.original_price.text() else 0
                discount_price = float(self.discount_price.text()) if self.discount_price.text() else 0
                
                if activity_type == "案后结(不与总指标挂钩)":
                    need_total = False
                
                add_activity(self.brand_id, f"{self.year}-{self.month:02d}", False, item_id,
                            activity_type, need_total, need_item, target_value,
                            original_price, discount_price)
                self.accept()
            except Exception as e:
                log_activity_debug(f"保存活动时发生错误: {e}\n{traceback.format_exc()}")
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")

    def validate_inputs(self):
        """验证输入数据"""
        if self.current_step == 2:
            try:
                if not self.target_value.text() or not self.original_price.text() or not self.discount_price.text():
                    QMessageBox.warning(self, "错误", "请输入目标值、原价和优惠价")
                    return False
                if float(self.discount_price.text()) >= float(self.original_price.text()):
                    QMessageBox.warning(self, "错误", "优惠价必须低于原价")
                    return False
                # 如果 '需完成单品销量' 未勾选，验证目标值是否为 0
                if not self.need_item.isChecked() and float(self.target_value.text()) != 0:
                    QMessageBox.warning(self, "错误", "当 '需完成单品销量' 未勾选时，目标值必须为 0")
                    return False
            except ValueError:
                QMessageBox.warning(self, "错误", "价格和目标值必须是有效的数字")
                return False
        return True



if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    # 示例用法（需提供 brand 对象）
    # window = ActivityInfoWindow(brand, 2025, 6)
    # window.show()
    # sys.exit(app.exec_())
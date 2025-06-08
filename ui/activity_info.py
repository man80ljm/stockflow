import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QDialog, QFormLayout, QComboBox, QCheckBox, 
                            QMessageBox,QStackedWidget,QRadioButton)
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import Qt
from database.queries import (get_monthly_activities, add_activity, delete_activity, 
                             get_all_items, add_item)

class ActivityInfoWindow(QMainWindow):
    """活动信息管理窗口"""
    
    def __init__(self, brand, year, month):
        super().__init__()
        self.brand = brand
        self.year = year
        self.month = month
        self.setWindowTitle(f"{brand.brand_name} - {year}年{month}月活动")
        self.setGeometry(100, 100, 900, 600)
        
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
        self.activity_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        add_btn = QPushButton("添加单品活动")
        add_btn.clicked.connect(self.open_add_dialog)
        item_layout.addWidget(self.activity_table)
        item_layout.addWidget(add_btn)
        layout.addWidget(item_group)
        
        self.load_activities()

    def load_activities(self):
        """加载活动数据"""
        activities = get_monthly_activities(self.brand.brand_id, self.year, self.month)
        self.activity_table.setRowCount(0)
        for activity in activities:
            row = self.activity_table.rowCount()
            self.activity_table.insertRow(row)
            activity_id, is_total, item_id, activity_type, need_total, need_item, target_value, \
            original_price, discount_price, item_name, spec = activity
            
            if is_total:
                self.total_target_input.setText(str(target_value))
                continue
                
            self.activity_table.setItem(row, 0, QTableWidgetItem(item_name or ""))
            self.activity_table.setItem(row, 1, QTableWidgetItem(spec or ""))
            self.activity_table.setItem(row, 2, QTableWidgetItem(activity_type or ""))
            self.activity_table.setItem(row, 3, QTableWidgetItem("是" if need_total else "否"))
            self.activity_table.setItem(row, 4, QTableWidgetItem("是" if need_item else "否"))
            self.activity_table.setItem(row, 5, QTableWidgetItem(str(target_value)))
            self.activity_table.setItem(row, 6, QTableWidgetItem(str(original_price or "")))
            self.activity_table.setItem(row, 7, QTableWidgetItem(str(discount_price or "")))
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda checked, aid=activity_id: self.delete_activity(aid))
            self.activity_table.setCellWidget(row, 8, delete_btn)

    def save_total_target(self):
        """保存总销量目标"""
        try:
            target_value = float(self.total_target_input.text())
            if target_value <= 0:
                raise ValueError("目标值必须大于0")
            add_activity(self.brand.brand_id, f"{self.year}-{self.month:02d}", True, None,
                        None, False, False, target_value, None, None)
            QMessageBox.information(self, "成功", "总销量目标已保存")
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

class AddItemActivityDialog(QDialog):
    """添加单品活动对话框"""
    
    def __init__(self, brand_id, year, month):
        super().__init__()
        self.brand_id = brand_id
        self.year = year
        self.month = month
        self.setWindowTitle("添加单品活动")
        self.setGeometry(200, 200, 400, 300)
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
        self.new_item_spec = QLineEdit(placeholderText="请输入规格")
        self.existing_combo = QComboBox()
        items = get_all_items()
        for item in items:
            self.existing_combo.addItem(f"{item[1]} ({item[2]})", item[0])
        step2_layout.addRow("品类名称:", self.new_item_name)
        step2_layout.addRow("规格:", self.new_item_spec)
        step2_layout.addRow("选择已有品类:", self.existing_combo)
        self.existing_combo.hide()
        self.stack.addWidget(step2)

        # 步骤3: 选择活动类型和配置
        step3 = QWidget()
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
        self.prev_btn = QPushButton("上一步")
        self.next_btn = QPushButton("下一步")
        self.finish_btn = QPushButton("完成")
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.finish_btn)
        layout.addLayout(nav_layout)

        self.prev_btn.clicked.connect(self.prev_step)
        self.next_btn.clicked.connect(self.next_step)
        self.finish_btn.clicked.connect(self.save_activity)
        self.prev_btn.setEnabled(False)
        self.finish_btn.hide()

        self.new_item_radio.toggled.connect(lambda checked: self.toggle_item_view(checked))
        self.current_step = 0

    def toggle_item_view(self, checked):
        """切换品类输入方式"""
        if checked:
            self.new_item_name.show()
            self.new_item_spec.show()
            self.existing_combo.hide()
        else:
            self.new_item_name.hide()
            self.new_item_spec.hide()
            self.existing_combo.show()

    def prev_step(self):
        """返回上一步"""
        if self.current_step > 0:
            self.current_step -= 1
            self.stack.setCurrentIndex(self.current_step)
            self.update_buttons()

    def next_step(self):
        """前往下一步"""
        if self.current_step < 2:
            self.current_step += 1
            self.stack.setCurrentIndex(self.current_step)
            self.update_buttons()

    def update_buttons(self):
        """更新导航按钮状态"""
        self.prev_btn.setEnabled(self.current_step > 0)
        self.next_btn.setVisible(self.current_step < 2)
        self.finish_btn.setVisible(self.current_step == 2)

    def save_activity(self):
        """保存活动到数据库"""
        if not self.validate_inputs():
            return
        item_id = self.existing_combo.currentData() if not self.new_item_radio.isChecked() else \
                  add_item(self.new_item_name.text(), self.new_item_spec.text())
        activity_type = self.activity_type.currentText()
        need_total = self.need_total.isChecked()
        need_item = self.need_item.isChecked()
        target_value = float(self.target_value.text())
        original_price = float(self.original_price.text())
        discount_price = float(self.discount_price.text())
        
        # 根据活动类型设置默认条件
        if activity_type == "案后结(不与总指标挂钩)":
            need_total = False
        
        add_activity(self.brand_id, f"{self.year}-{self.month:02d}", False, item_id,
                     activity_type, need_total, need_item, target_value,
                     original_price, discount_price)
        self.accept()

    def validate_inputs(self):
        """验证输入数据"""
        if self.current_step == 1 and self.new_item_radio.isChecked():
            if not self.new_item_name.text() or not self.new_item_spec.text():
                QMessageBox.warning(self, "错误", "请输入品类名称和规格")
                return False
        elif self.current_step == 2:
            if not self.target_value.text() or not self.original_price.text() or not self.discount_price.text():
                QMessageBox.warning(self, "错误", "请输入目标值、原价和优惠价")
                return False
            if float(self.discount_price.text()) >= float(self.original_price.text()):
                QMessageBox.warning(self, "错误", "优惠价必须低于原价")
                return False
        return True

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    # 示例用法（需提供 brand 对象）
    # window = ActivityInfoWindow(brand, 2025, 6)
    # window.show()
    # sys.exit(app.exec_())
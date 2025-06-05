from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox, QDateEdit
from PyQt5.QtCore import QDate
from database.queries import get_purchases_by_brand, get_all_items, add_item
from models.purchase import Purchase
import datetime

class PurchaseDetailsWindow(QWidget):
    def __init__(self, brand):
        super().__init__()
        self.brand = brand  # 传入的 Brand 对象
        self.current_page = 1
        self.per_page = 20
        self.total_pages = 1
        self.purchases = []
        self.setWindowTitle(f"{self.brand.brand_name} - 进货详情")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()
        self.load_purchases()

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
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
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
        dialog = AddPurchaseDialog(self.brand.brand_id, self)
        if dialog.exec_():
            self.load_purchases()

class AddPurchaseDialog(QDialog):
    def __init__(self, brand_id, parent=None):
        super().__init__(parent)
        self.brand_id = brand_id
        self.items = get_all_items()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("新增进货记录")
        layout = QFormLayout()

        # 商品选择（下拉框）
        self.item_combo = QComboBox()
        self.item_combo.addItem("新增商品...")
        for item in self.items:
            self.item_combo.addItem(f"{item[1]} ({item[2]})", userData=item[0])
        self.item_combo.currentIndexChanged.connect(self.on_item_changed)
        layout.addRow("商品：", self.item_combo)

        # 新商品输入（隐藏，动态显示）
        self.new_item_name = QLineEdit()
        self.new_item_name.setPlaceholderText("请输入商品名称")
        self.new_item_spec = QLineEdit()
        self.new_item_spec.setPlaceholderText("请输入规格")
        self.new_item_name.setVisible(False)
        self.new_item_spec.setVisible(False)
        layout.addRow("新商品名称：", self.new_item_name)
        layout.addRow("新商品规格：", self.new_item_spec)

        # 日期
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        layout.addRow("日期：", self.date_input)

        # 单位
        self.unit_input = QLineEdit()
        self.unit_input.setText("件")
        layout.addRow("单位：", self.unit_input)

        # 数量
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("请输入数量")
        layout.addRow("数量：", self.quantity_input)

        # 单价
        self.unit_price_input = QLineEdit()
        self.unit_price_input.setPlaceholderText("请输入单价")
        layout.addRow("单价：", self.unit_price_input)

        # 备注
        self.remarks_input = QLineEdit()
        self.remarks_input.setPlaceholderText("请输入备注（可选）")
        layout.addRow("备注：", self.remarks_input)

        # 按钮
        button_layout = QHBoxLayout()
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_purchase)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)

        self.setLayout(layout)

    def on_item_changed(self, index):
        """商品选择变化时动态显示新商品输入框"""
        if index == 0:  # 选择了“新增商品...”
            self.new_item_name.setVisible(True)
            self.new_item_spec.setVisible(True)
        else:
            self.new_item_name.setVisible(False)
            self.new_item_spec.setVisible(False)

    def save_purchase(self):
        """保存进货记录"""
        # 获取商品 ID
        if self.item_combo.currentIndex() == 0:  # 新增商品
            item_name = self.new_item_name.text().strip()
            spec = self.new_item_spec.text().strip()
            if not item_name or not spec:
                QMessageBox.warning(self, "错误", "新商品名称和规格不能为空！")
                return
            item_id = add_item(item_name, spec)
        else:
            item_id = self.item_combo.currentData()

        # 获取其他输入
        date = self.date_input.date().toString("yyyy-MM-dd")
        unit = self.unit_input.text().strip()
        quantity_text = self.quantity_input.text().strip()
        unit_price_text = self.unit_price_input.text().strip()
        remarks = self.remarks_input.text().strip() or None

        # 验证输入
        try:
            quantity = int(quantity_text)
            if quantity <= 0:
                raise ValueError("数量必须大于 0")
            unit_price = float(unit_price_text)
            if unit_price <= 0:
                raise ValueError("单价必须大于 0")
        except ValueError as e:
            QMessageBox.warning(self, "错误", str(e))
            return

        # 计算总金额
        total_amount = quantity * unit_price

        # 保存进货记录
        purchase = Purchase(
            purchase_id=None, item_id=item_id, brand_id=self.brand_id,
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
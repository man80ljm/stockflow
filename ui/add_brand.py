from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget, QGridLayout, QDialog, QLineEdit, QFormLayout, QMessageBox, QMenu
from PyQt5.QtCore import Qt
from database.queries import add_brand, get_all_brands
from models.brand import Brand
from ui.purchase_details import PurchaseDetailsWindow

class AddBrandWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("品牌管理")
        self.setGeometry(100, 100, 600, 400)
        self.brands = []
        self.init_ui()
        self.load_brands()

    def init_ui(self):
        # 主布局：垂直布局
        layout = QVBoxLayout()

        # 标题
        title_label = QLabel("品牌管理")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(title_label)

        # 品牌按钮区域（带滚动条）
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.button_container = QWidget()
        self.button_layout = QGridLayout()
        self.button_container.setLayout(self.button_layout)
        self.scroll_area.setWidget(self.button_container)
        layout.addWidget(self.scroll_area)

        # 操作按钮
        button_layout = QHBoxLayout()
        add_button = QPushButton("增加")
        add_button.clicked.connect(self.add_brand_dialog)
        filter_button = QPushButton("筛选")
        filter_button.clicked.connect(self.open_filter_screen)
        export_button = QPushButton("导出")
        calculate_button = QPushButton("计算")
        bill_button = QPushButton("账单")
        button_layout.addWidget(add_button)
        button_layout.addWidget(filter_button)
        button_layout.addWidget(export_button)
        button_layout.addWidget(calculate_button)
        button_layout.addWidget(bill_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_brands(self):
        """加载品牌列表并创建按钮"""
        # 清空现有按钮
        for i in reversed(range(self.button_layout.count())):
            widget = self.button_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        self.brands = []
        brand_data = get_all_brands()
        for brand_id, brand_name in brand_data:
            created_at = self.get_created_at(brand_id)
            brand = Brand(brand_id, brand_name, created_at)
            self.brands.append(brand)

        # 创建品牌按钮（一行四个）
        for index, brand in enumerate(self.brands):
            row = index // 4
            col = index % 4
            button = QPushButton(brand.brand_name)
            button.setMinimumHeight(50)
            button.setStyleSheet("font-size: 12pt;")
            button.clicked.connect(lambda checked, b=brand: self.open_purchase_details(b))
            button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda pos, b=brand: self.show_context_menu(pos, b))
            self.button_layout.addWidget(button, row, col)

    def get_created_at(self, brand_id):
        """获取品牌的创建时间"""
        from database.queries import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT created_at FROM brands WHERE brand_id = ?", (brand_id,))
        created_at = cursor.fetchone()[0]
        conn.close()
        return created_at

    def add_brand_dialog(self):
        """显示添加品牌的弹窗"""
        dialog = AddBrandDialog(self)
        if dialog.exec_():
            self.load_brands()

    def open_purchase_details(self, brand):
        """打开进货详情界面"""
        self.purchase_window = PurchaseDetailsWindow(brand)
        self.purchase_window.show()

    def show_context_menu(self, pos, brand):
        """显示右键菜单"""
        menu = QMenu(self)
        delete_action = menu.addAction("删除")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == delete_action:
            self.confirm_delete(brand)

    def confirm_delete(self, brand):
        """确认删除品牌"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"删除后整个品牌 '{brand.brand_name}' 的数据将清除，确定删除吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            brand.delete()
            self.load_brands()

    def open_filter_screen(self):
        """打开筛选界面"""
        QMessageBox.information(self, "提示", "筛选界面尚未实现！")

class AddBrandDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加品牌")
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText("请输入品牌名称")
        layout.addRow("品牌名称：", self.brand_input)

        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.save_brand)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)

        self.setLayout(layout)

    def save_brand(self):
        """保存品牌"""
        brand_name = self.brand_input.text().strip()
        if not brand_name:
            QMessageBox.warning(self, "错误", "品牌名称不能为空！")
            return

        brand = Brand(None, brand_name, None)
        brand_id = brand.save()
        if brand_id:
            QMessageBox.information(self, "成功", f"品牌 '{brand_name}' 添加成功！")
            self.accept()
        else:
            QMessageBox.warning(self, "错误", f"品牌 '{brand_name}' 已存在！")
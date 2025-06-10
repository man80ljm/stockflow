import os
import datetime
import traceback  # 添加导入
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget, QGridLayout, QDialog, QLineEdit, QFormLayout, QMessageBox, QMenu
from PyQt5.QtCore import Qt
from models.brand import add_brand, get_all_brands, Brand
from ui.purchase_details import PurchaseDetailsWindow
from PyQt5 import  sip
from PyQt5.QtCore import Qt, QTimer  # 添加 QTimer

# 定义 log_debug 函数
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug.log")
def log_debug(message):
    """记录调试信息到文件"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {message}\n")

class AddBrandWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("品牌管理")
        self.setGeometry(100, 100, 600, 400)
        self.brands = []
        self.purchase_windows = []  # 添加列表以跟踪打开的 PurchaseDetailsWindow
        self.init_ui()
        self.load_brands()
        # 将窗口移动到屏幕中央
        self.center_on_screen()
    
    def center_on_screen(self):
        """将窗口移动到屏幕中央"""
        # 获取屏幕几何信息
        screen = QApplication.primaryScreen().geometry()
        window_size = self.geometry()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        self.move(x, y)

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
        filter_button = QPushButton("筛选（未实现）")
        filter_button.setEnabled(False)  # 禁用未实现功能
        export_button = QPushButton("导出（未实现）")
        export_button.setEnabled(False)
        calculate_button = QPushButton("计算（未实现）")
        calculate_button.setEnabled(False)
        bill_button = QPushButton("账单（未实现）")
        bill_button.setEnabled(False)
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
        for brand_id, brand_name, created_at in brand_data:
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
            button.customContextMenuRequested.connect(lambda pos, btn=button, b=brand: self.show_context_menu(btn, pos, b))
            self.button_layout.addWidget(button, row, col)

    def add_brand_dialog(self):
        """显示添加品牌的弹窗"""
        dialog = AddBrandDialog(self)
        if dialog.exec_():
            self.load_brands()

    def open_purchase_details(self, brand):
        """打开进货详情界面，确保只有一个 PurchaseDetailsWindow 打开"""
        log_debug(f"调用 open_purchase_details for brand: {brand.brand_name}")
        
        # 先关闭所有当前打开的窗口
        for window in self.purchase_windows[:]:  # 使用列表副本进行迭代
            try:
                if window is not None:
                    window.close()
                    log_debug(f"关闭现有 PurchaseDetailsWindow")
            except Exception as e:
                log_debug(f"关闭窗口时发生错误: {str(e)}")
        
        # 清空列表
        self.purchase_windows.clear()
        log_debug("清空 purchase_windows 列表")
        
        # 创建并显示新窗口
        try:
            purchase_window = PurchaseDetailsWindow(brand)
            self.purchase_windows.append(purchase_window)
            log_debug(f"创建 PurchaseDetailsWindow for brand: {brand.brand_name}")
            purchase_window.show()
            log_debug("调用 purchase_window.show()")
        except Exception as e:
            log_debug(f"创建 PurchaseDetailsWindow 失败: {str(e)}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "错误", f"打开进货详情失败: {str(e)}")



    def show_context_menu(self, button, pos, brand):
        """显示右键菜单"""
        menu = QMenu(self)
        delete_action = menu.addAction("删除")
        action = menu.exec_(button.mapToGlobal(pos))
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

    def closeEvent(self, event):
        """关闭窗口时关闭所有相关的 PurchaseDetailsWindow"""
        for window in self.purchase_windows[:]:  # 使用列表副本
            try:
                if window is not None:
                    window.close()
            except Exception as e:
                log_debug(f"关闭窗口时发生错误: {str(e)}")
        
        self.purchase_windows.clear()  # 清空列表
        super().closeEvent(event)


class AddBrandDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加品牌")
        self.init_ui()
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
        try:
            brand_id = brand.save()
            if brand_id:
                QMessageBox.information(self, "成功", f"品牌 '{brand_name}' 添加成功！")
                self.accept()
            else:
                QMessageBox.warning(self, "错误", f"品牌 '{brand_name}' 已存在！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存品牌时发生错误：{str(e)}")
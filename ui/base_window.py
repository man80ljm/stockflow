from PyQt5.QtWidgets import QMainWindow, QDialog, QApplication

class CenteredWindowMixin:
    def center_on_screen(self):
        """将窗口移动到屏幕中央"""
        screen = QApplication.primaryScreen().geometry()
        window_size = self.geometry()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        self.move(x, y)

class CenteredMainWindow(QMainWindow, CenteredWindowMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.center_on_screen()  # 默认居中

class CenteredDialog(QDialog, CenteredWindowMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.center_on_screen()  # 默认居中
from ui.add_brand import AddBrandWindow
from PyQt5.QtWidgets import QApplication
import sys
from database.db_setup import create_database

if __name__ == "__main__":
    create_database()  # 确保数据库已创建
    app = QApplication(sys.argv)
    window = AddBrandWindow()
    window.show()
    sys.exit(app.exec_())
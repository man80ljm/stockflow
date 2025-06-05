import sys
from PyQt5.QtWidgets import QApplication
from ui.add_brand import AddBrandWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AddBrandWindow()
    window.show()
    sys.exit(app.exec_())
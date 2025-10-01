from PyQt6.QtWidgets import QApplication
from core.loader import BootLoader
import sys

def main():
    app = QApplication(sys.argv)
    window = BootLoader()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

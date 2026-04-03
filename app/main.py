import sys
from PyQt6.QtWidgets import QApplication
from app.gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    # Применяем стиль (опционально)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
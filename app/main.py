import sys
import logging
from PyQt6.QtWidgets import QApplication
from app.gui.main_window import MainWindow

def main():

    logging.basicConfig(level=logging.DEBUG, filename='C:\\temp\\scanner_debug.log', filemode='w')
    logging.debug(f"sys.frozen={getattr(sys, 'frozen', False)}")
    logging.debug(f"sys._MEIPASS={getattr(sys, '_MEIPASS', 'NOT SET')}")
    logging.debug(f"sys.path={sys.path}")
    logging.debug(f"__file__={__file__ if '__file__' in dir() else 'NOT DEFINED'}")

    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scanner.log', encoding='utf-8'),
            logging.StreamHandler()  # дублирует в консоль
        ]
    )
    
    app = QApplication(sys.argv)
    # Применяем стиль (опционально)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
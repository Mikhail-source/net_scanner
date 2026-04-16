import sys
import logging
from PyQt6.QtWidgets import QApplication
from app.gui.main_window import MainWindow

def main():
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
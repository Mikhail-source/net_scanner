import sys
import os
import logging
from pathlib import Path

# 🔥 Настройка логирования ДО импортов приложения
if getattr(sys, 'frozen', False):
    # Режим EXE: пишем лог в %TEMP% или рядом с exe
    log_dir = Path(os.getenv('TEMP', os.getenv('TMP', '.')))
    log_file = log_dir / "NetScanner.log"
else:
    # Режим разработки
    log_file = Path("scanner.log")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w', encoding='utf-8', delay=False),
        logging.StreamHandler(sys.stderr)  # Дублируем в консоль для отладки
    ],
    force=True  # Перезаписать существующие конфигурации
)

logger = logging.getLogger(__name__)
logger.info(f"=== Запуск NetScanner ===")
logger.info(f"frozen={getattr(sys, 'frozen', False)}")
logger.info(f"_MEIPASS={getattr(sys, '_MEIPASS', 'NOT SET')}")
logger.info(f"sys.path={sys.path[:3]}...")  # Первые 3 пути

# 🔥 ФИКС ПУТЕЙ ДЛЯ ИМПОРТОВ
if getattr(sys, 'frozen', False):
    # В режиме EXE добавляем временную папку в начало пути
    if hasattr(sys, '_MEIPASS') and sys._MEIPASS not in sys.path:
        sys.path.insert(0, sys._MEIPASS)
        logger.debug(f"Added _MEIPASS to sys.path: {sys._MEIPASS}")

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
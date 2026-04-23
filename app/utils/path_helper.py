import sys
from pathlib import Path

def get_resource_path(relative_path: str) -> Path:
    """
    Возвращает абсолютный путь к ресурсу, работая как в режиме разработки,
    так и в скомпилированном EXE.
    
    Args:
        relative_path: Путь относительно корня приложения (например, "data/service.json")
    
    Returns:
        Path: Абсолютный путь к файлу
    """
    if hasattr(sys, '_MEIPASS'):
        # Режим PyInstaller: файлы распакованы во временную папку
        base_path = Path(sys._MEIPASS)
    else:
        # Режим разработки: обычный запуск
        base_path = Path(__file__).resolve().parent.parent.parent  # net_scanner/
    
    return base_path / relative_path
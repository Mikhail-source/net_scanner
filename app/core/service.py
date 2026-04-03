# app/core/service.py
import json
from pathlib import Path
from typing import Dict

# 1. Глобальная переменная для кэширования данных (загружается 1 раз при импорте)
_services_cache: Dict[str, str] = {}
_is_loaded = False

def _load_services():
    """Загружает базу сервисов в память"""
    global _services_cache, _is_loaded
    
    if _is_loaded:
        return

    # 2. Надежное построение пути (работает на Windows, Linux, Mac)
    # Ищем файл data/service.json относительно текущей папки core
    base_dir = Path(__file__).resolve().parent.parent
    json_path = base_dir / "data" / "service.json"

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            _services_cache = json.load(f)
            _is_loaded = True
    except FileNotFoundError:
        print(f"Warning: {json_path} not found. Services will be 'unknown'.")
        _services_cache = {}
        _is_loaded = True # Помечаем как загружено, чтобы не пытаться снова
    except json.JSONDecodeError:
        print(f"Error: {json_path} is not valid JSON.")
        _services_cache = {}
        _is_loaded = True

def check_service(port: int) -> str:
    """Возвращает имя сервиса по номеру порта"""
    _load_services() # Убеждаемся, что данные загружены
    return _services_cache.get(str(port), "unknown")
import json
from pathlib import Path
from typing import Dict
from app.utils.path_helper import get_resource_path

_services_cache: Dict[str, str] = {}
_banners_cache: list = []
_is_loaded = False

def _load_services():
    """
    Загружает базу сервисов в память
    """
    global _services_cache, _is_loaded
    global _banners_cache
    
    if _is_loaded:
        return

    """
    Надежное построение пути (работает на Windows, Linux, Mac)
    Ищем файл data/service.json относительно текущей папки core
    """
    json_path = get_resource_path("app/data/service.json")

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _services_cache = data
            _banners_cache = [item.lower() for item in list(data.values())]
            _is_loaded = True
    except FileNotFoundError:
        alt_path = Path(__file__).parent.parent / "data" / "service.json"
        if alt_path.exists():
            with open(alt_path, 'r', encoding='utf-8') as f:
                _services_cache = json.load(f)
        _is_loaded = True
    except json.JSONDecodeError:
        _services_cache = {}
        _is_loaded = True

def check_service(port: int) -> str:
    """Возвращает имя сервиса по номеру порта"""
    _load_services() # Убеждаемся, что данные загружены
    return _services_cache.get(str(port), "unknown")

def detect_service_from_banner(banner: str) -> str:
    """Определяет сервис по баннеру"""
    for banner_cache in _banners_cache:
        if banner_cache in banner.lower():
            return banner_cache
    
    return "unknown"
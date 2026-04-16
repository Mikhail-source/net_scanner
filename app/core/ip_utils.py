import ipaddress
from typing import Iterator

def parse_ip_range(input_str: str) -> Iterator[str]:
    """
    Генерирует список IP-адресов из строки с поддержкой форматов:
    - Одиночный: "192.168.1.1"
    - Диапазон: "192.168.1.1-192.168.1.50"
    - Вайлдкард: "192.168.1.*"
    - Список: "192.168.1.1, 192.168.1.5"
    
    Возвращает генератор (экономит память при больших диапазонах).
    """
    input_str = input_str.strip()
    
    # 1. Обработка списка (запятые)
    if ',' in input_str:
        for part in input_str.split(','):
            yield from parse_ip_range(part.strip())
        return
    
    # 2. Обработка вайлдкарда: 192.168.1.* -> 192.168.1.0/24
    if '*' in input_str:
        # Заменяем * на 0 и добавляем маску /24 (для одной звезды)
        # Заменяем * на 0 и добавляем маску /16 (для двух звезд)
        count = input_str.count("*")
        suffix = ""
        match count:
            case 1: suffix = "/24"
            case 2: suffix = "/16"
        network_str = input_str.replace('*', '0') + suffix
        try:
            yield from iter([f"{input_str.replace('*', '0')}"])
            network = ipaddress.ip_network(network_str, strict=False)
            yield from (str(host) for host in network.hosts())
            yield from iter([f"{input_str.replace('*', '255')}"])
        except ValueError:
            pass  # Игнорируем невалидные
        return
    
    # 3. Обработка диапазона: 192.168.1.1-192.168.1.50
    if '-' in input_str and '/' not in input_str:
        try:
            start_str, end_str = input_str.split('-')
            start_ip = ipaddress.ip_address(start_str.strip())
            end_ip = ipaddress.ip_address(end_str.strip())
            
            # Итерируемся от start до end включительно
            current = start_ip
            while current <= end_ip:
                yield str(current)
                current += 1
            return
        except ValueError:
            pass  # Если не диапазон, пробуем дальше
    
    # 4. Одиночный IP
    try:
        ip = ipaddress.ip_address(input_str)
        yield str(ip)
    except ValueError:
        # Невалидный ввод — пропускаем
        pass
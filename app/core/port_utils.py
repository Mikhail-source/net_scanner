def parse_ports(text: str) -> list:
    """
    Генерирует список портов из строки с поддержкой форматов:
    - Одиночный: "80"
    - Диапазон: "1-1000"
    - Вайлдкард: "*"
    - Список: "80, 1000"
    """
    ports = []
    
    for part in text.split(','):
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                ports.extend(range(start, end + 1))
            except ValueError:
                raise ValueError
        elif '*' in text:
            ports.extend(range(1, 65536))
        elif text == '':
            return []
        else:
            try:
                ports.append(int(part))
            except ValueError:
                raise ValueError

    return sorted(set(ports))
from app.core.port_utils import parse_ports

def test_list():
    port_list = ", ".join([f"{port}" for port in range(100)])
    result = parse_ports(port_list)
    assert result == [port for port in range(100)]

def test_range():
    port_range = "1-100, 201-300"
    ports = []
    result = parse_ports(port_range)
    for part in port_range.split(','):
        part = part.strip()
        if '-' in part:
            start, end = map(int, part.split('-'))
            ports.extend(range(start, end + 1))
    assert result == ports
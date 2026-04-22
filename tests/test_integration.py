from app.core.ip_utils import parse_ip
from app.core.port_utils import parse_ports
from app.core.input_parser import InputParser

def test_full_parse_scenario():
    """Тест полного сценария: ввод пользователя → парсинг → запрос"""
    parser = InputParser()
    
    # Сценарий: "хочу просканировать подсеть 192.168.1.0/30 на портах 80,443"
    request = parser.parse(
        host_input="192.168.1.0 - 192.168.1.10",
        ports_input="80,443"
    )
    
    assert request.ping_mode is False
    assert len(request.hosts) == 11
    assert request.ports == [80, 443]
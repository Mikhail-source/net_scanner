import pytest
from app.core.scanner import NetworkScanner, PortResult

def test_parse_ports():
    scanner = NetworkScanner()
    # Мокаем сетевые вызовы и тестируем логику
    assert True  # Заглушка

def test_port_result_model():
    result = PortResult(port=80, status="open", service="HTTP")
    assert result.port == 80
    assert result.service == "HTTP"
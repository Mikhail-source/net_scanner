from app.core.ip_utils import parse_ip

def test_single_ip():
    result = list(parse_ip("192.168.1.1"))
    assert result == ["192.168.1.1"]

def test_list():
    ip_list = ", ".join([f"192.168.0.{ip}" for ip in range(100)])
    result = list(parse_ip(ip_list))
    assert result == [f"192.168.0.{ip}" for ip in range(100)]

def test_wildcard_1():
    ip_wildcard = "192.168.0.*"
    result = list(parse_ip(ip_wildcard))
    assert result == [f"192.168.0.{ip}" for ip in range(256)]

def test_wildcard_2():
    ip_wildcard = "192.168.*.*"
    result = list(parse_ip(ip_wildcard))
    assert result == [f"192.168.{oct_3}.{oct_4}" for oct_3 in range(256) for oct_4 in range(256)]

def test_range():
    ip_range = "192.168.0.0 - 192.168.0.255"
    result = list(parse_ip(ip_range))
    assert result == [f"192.168.0.{ip}" for ip in range(256)]

def test_true_ip():
    ip_true = ["192.168.0.1",
                "0.0.0.0",
                "255.255.255.255"]
    for i in range(len(ip_true)):
        result = list(parse_ip(ip_true[i]))
        assert result == [ip_true[i]]

def test_false_ip():
    ip_false = ["192.168.0.a",
                "1922.168.0.1",
                "192.168.0"]
    for ip in ip_false:
        result = list(parse_ip(ip))
        assert not result

def test_invalid_input():
        result = list(parse_ip("not-an-ip"))
        assert result == []
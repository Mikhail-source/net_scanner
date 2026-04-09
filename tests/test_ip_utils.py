from app.core.ip_utils import parse_ip_range

def test_list():
    text = ["192.168.0." + str(x) for x in range(100)]
    result = parse_ip_range(text)

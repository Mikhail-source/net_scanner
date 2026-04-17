from dataclasses import dataclass
from app.core.ip_utils import parse_ip
from app.core.port_utils import parse_ports
from app.core.export import export_data

@dataclass
class ScanRequest:
    hosts: list[str]
    ports: list[int]
    ping_mode: bool  # "ping_only" или "port_scan"

class InputParser:
    @staticmethod
    def parse(host_input: str, ports_input: str) -> ScanRequest:
        scan = ScanRequest
        scan.hosts = list(parse_ip(host_input.strip()))
        scan.ports = parse_ports(ports_input.strip())
        scan.ping_mode = False if scan.ports else True

        return scan
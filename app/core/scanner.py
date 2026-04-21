import asyncio
from typing import Callable, Optional
from pydantic import BaseModel
from app.core.service import check_service, detect_service_from_banner
from app.core.ping_utils import async_ping

class PortResult(BaseModel):
    port: int
    status: str
    service: str = "unknown"
    banner: Optional[str] = None

class ScanTarget(BaseModel):
    hosts: list[str]
    ports: list[int]
    force_scan: bool = False

class NetworkScanner:
    def __init__(self, timeout: float = 1.0):
        self.timeout = timeout
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    async def ping_host(self, host: str) -> dict:
        """Пинг хоста"""
        is_alive = await async_ping(host, timeout=self.timeout)
        return {
            "host": host,
            "port": 0,
            "status": "alive" if is_alive else "dead",
            "service": "ICMP",
            "banner": "Host reachable" if is_alive else "No response"
        }

    async def scan_port(self, host: str, port: int) -> PortResult:
        """Сканирование одного порта"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=self.timeout
            )
            banner = ""
            try:
                data = await asyncio.wait_for(reader.read(1024), timeout=0.5)
                if data:
                    banner = data.decode('utf-8', errors='ignore').strip()
            except:
                pass
            writer.close()
            await writer.wait_closed()
            
            service = check_service(port)
            if service == "unknown" and banner:
                service = detect_service_from_banner(banner)
            
            return PortResult(port=port, status="open", service=service, banner=banner or None)
        except asyncio.TimeoutError:
            return PortResult(port=port, status="filtered")
        except ConnectionRefusedError:
            return PortResult(port=port, status="closed")
        except Exception:
            return PortResult(port=port, status="filtered")

    async def _process_ping(self, host: str, callback: Callable):
        """Обработчик пинга"""
        result = await self.ping_host(host)
        callback(result)

    async def _process_port(self, host: str, port: int, callback: Callable):
        """Обработчик порта"""
        result = await self.scan_port(host, port)
        callback({
            "host": host,
            "port": result.port,
            "status": result.status,
            "service": result.service,
            "banner": result.banner
        })

    async def scan(self, target: ScanTarget, progress_callback: Callable):
        """Единый метод сканирования: порты ИЛИ пинг"""
        self._is_cancelled = False
        
        # 🔥 РЕЖИМ ТОЛЬКО ПИНГ
        if not target.ports:
            ping_tasks  = [self._process_ping(
                host, progress_callback) for host in target.hosts]
            for i in range(0, len(ping_tasks), 100):
                if self._is_cancelled:
                    break
                batch = ping_tasks[i:i+100]
                if batch:
                    await asyncio.gather(*batch)
                    await asyncio.sleep(0)
            return
        
        # 🔥 РЕЖИМ СКАНИРОВАНИЯ ПОРТОВ
        for host in target.hosts:
            if self._is_cancelled:
                break

            if not target.force_scan:
                ping_result = await self.ping_host(host)
                if ping_result["status"] == "dead":
                    # Хост мёртв и force_scan выключен → пропускаем сканирование портов
                    progress_callback({
                        "host": host,
                        "port": 0,
                        "status": "dead",
                        "service": "ICMP",
                        "banner": "Host unreachable, port scan skipped"
                    })
                    continue
            else:        
                port_tasks = [self._process_port(
                    host, port, progress_callback) for port in target.ports]
                for i in range(0, len(port_tasks), 100):
                    if self._is_cancelled:
                        break
                    batch = port_tasks[i:i+100]
                    if batch:
                        await asyncio.gather(*batch)
                        await asyncio.sleep(0)
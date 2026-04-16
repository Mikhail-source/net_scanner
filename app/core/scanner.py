import asyncio
from typing import Callable, Optional
from pydantic import BaseModel
from app.core.service import check_service, detect_service_from_banner
from app.core.ping_utils import async_ping

class PortResult(BaseModel):
    port: int
    status: str  # open, closed, filtered
    service: str = "unknown"
    banner: Optional[str] = None

class ScanTarget(BaseModel):
    hosts: list[str]  # ← было host: str, теперь список
    ports: list[int]

class NetworkScanner:
    def __init__(self, timeout: float = 1.0):
        self.timeout = timeout
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    async def ping_host(self, host: str) -> dict:
        """Пинг хоста, возвращает результат в формате для GUI"""
        is_alive = await async_ping(host, timeout=self.timeout)
        return {
            "host": host,
            "port": 0,  # 0 = специальный порт для "хост жив"
            "status": "alive" if is_alive else "dead",
            "service": "ICMP",
            "banner": "Host is reachable via ping" if is_alive else "No response"
        }

    async def scan(self, target: ScanTarget, progress_callback: Callable):
        """Сканирование: порты ИЛИ пинг, если портов нет"""
        self._is_cancelled = False
        
        if not target.ports:
            tasks = []
            for host in target.hosts:
                if self._is_cancelled:
                    break
                tasks.append(self._ping_single(host, progress_callback))
            
            # Выполняем пинги батчами
            for i in range(0, len(tasks), 100):
                batch = tasks[i:i+100]
                if batch:
                    await asyncio.gather(*batch)
                    await asyncio.sleep(0)
            return

    async def _ping_single(self, host: str, callback: Callable):
        """Внутренний метод для пинга одного хоста"""
        result = await self.ping_host(host)
        callback(result)

    async def _scan_single(self, host: str, port: int, callback: Callable):
        """Внутренний метод для сканирования одного хост:порт"""
        result = await self.scan_port(host, port)
        result_with_host = {
            "host": host,
            "port": result.port,
            "status": result.status,
            "service": result.service,
            "banner": result.banner
        }
        callback(result_with_host)

    async def scan_port(self, host: str, port: int) -> PortResult:
        """Проверка одного порта"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=self.timeout
            )
            
            # Попытка получить баннер (первый байт)
            banner = ""
            try:
                data = await asyncio.wait_for(reader.read(1024), timeout=0.5)
                if data:
                    banner = data.decode('utf-8', errors='ignore').strip()
            except:
                pass
            
            writer.close()
            await writer.wait_closed()
            
            return PortResult(port=port, status="open",
                              service=check_service(port),
                              banner=detect_service_from_banner(banner))
        except asyncio.TimeoutError:
            return PortResult(port=port, status="filtered")
        except ConnectionRefusedError:
            return PortResult(port=port, status="closed")
        except Exception:
            return PortResult(port=port, status="filtered")

    async def scan(self, target: ScanTarget, progress_callback: Callable):
        """Сканирование множества хостов и портов"""
        self._is_cancelled = False
        
        for host in target.hosts:
            if self._is_cancelled:
                break
                
            # Сканируем порты для текущего хоста
            tasks = []
            for port in target.ports:
                if self._is_cancelled:
                    break
                tasks.append(self._scan_single(host, port, progress_callback))
                
                # Батчинг: выполняем пачками по 100 задач, чтобы не забить память
                if len(tasks) >= 100:
                    await asyncio.gather(*tasks)
                    tasks = []
                    await asyncio.sleep(0)  # Yield control to event loop
            
            # Добиваем остаток задач для этого хоста
            if tasks and not self._is_cancelled:
                await asyncio.gather(*tasks)

    async def _scan_single(self, host: str, port: int, callback: Callable):
        """Внутренний метод для сканирования одного хост:порт"""
        result = await self.scan_port(host, port)
        # Добавляем хост в результат для отображения
        result_with_host = {
            "host": host,
            "port": result.port,
            "status": result.status,
            "service": result.service,
            "banner": result.banner
        }
        callback(result_with_host)
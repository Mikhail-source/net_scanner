import asyncio
from typing import Callable, Optional
from pydantic import BaseModel
from app.core.service import check_service, detect_service_from_banner

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
        
        # Счётчик для прогресса (опционально)
        total = len(target.hosts) * len(target.ports)
        current = 0
        
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
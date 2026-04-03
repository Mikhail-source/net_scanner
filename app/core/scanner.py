import asyncio
import socket
from typing import Callable, Optional
from datetime import datetime
from pydantic import BaseModel
from .service import check_service

class PortResult(BaseModel):
    port: int
    status: str  # open, closed, filtered
    service: str = "unknown"
    banner: Optional[str] = None

class ScanTarget(BaseModel):
    host: str
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
            
            return PortResult(port=port, status="open", service=check_service(port), banner=banner or None)
        except asyncio.TimeoutError:
            return PortResult(port=port, status="filtered")
        except ConnectionRefusedError:
            return PortResult(port=port, status="closed")
        except Exception:
            return PortResult(port=port, status="filtered")

    async def scan(self, target: ScanTarget, progress_callback: Callable):
        """Основной метод сканирования"""
        self._is_cancelled = False
        tasks = []
        
        for port in target.ports:
            if self._is_cancelled:
                break
            tasks.append(self.scan_port(target.host, port))
            
            # Ограничиваем количество одновременных соединений (чтобы не убить сеть)
            if len(tasks) >= 100:
                results = await asyncio.gather(*tasks)
                for res in results:
                    progress_callback(res)
                tasks = []
                
                # Даем отрисоваться GUI
                await asyncio.sleep(0)
        
        # Добиваем остатки
        if tasks and not self._is_cancelled:
            results = await asyncio.gather(*tasks)
            for res in results:
                progress_callback(res)
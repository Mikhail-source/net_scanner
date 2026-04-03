from PyQt6.QtCore import QThread, pyqtSignal
from app.core.scanner import NetworkScanner, ScanTarget, PortResult
import asyncio

class ScannerWorker(QThread):
    # Сигналы для общения с GUI
    progress = pyqtSignal(PortResult)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, host: str, ports: list[int]):
        super().__init__()
        self.host = host
        self.ports = ports
        self.scanner = NetworkScanner(timeout=1.0)

    def run(self):
        """Точка входа потока"""
        try:
            target = ScanTarget(host=self.host, ports=self.ports)
            
            # Запускаем asyncio цикл внутри потока
            asyncio.run(self._scan_async(target))
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    async def _scan_async(self, target: ScanTarget):
        def on_result(result: PortResult):
            # Отправляем результат в GUI
            self.progress.emit(result)
        
        await self.scanner.scan(target, on_result)

    def stop(self):
        self.scanner.cancel()
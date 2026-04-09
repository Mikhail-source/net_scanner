from PyQt6.QtCore import QThread, pyqtSignal
from app.core.scanner import NetworkScanner, ScanTarget
import asyncio

class ScannerWorker(QThread):
    progress = pyqtSignal(dict)  # ← Теперь передаём dict
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, hosts: list[str], ports: list[int]):  # ← hosts вместо host
        super().__init__()
        self.hosts = hosts
        self.ports = ports
        self.scanner = NetworkScanner(timeout=1.0)

    def run(self):
        try:
            # Создаём target со списком хостов
            from app.core.scanner import ScanTarget
            target = ScanTarget(hosts=self.hosts, ports=self.ports)
            asyncio.run(self._scan_async(target))
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    async def _scan_async(self, target: ScanTarget):
        def on_result(result: dict):
            self.progress.emit(result)  # Эмитим словарь
        
        await self.scanner.scan(target, on_result)

    def stop(self):
        self.scanner.cancel()
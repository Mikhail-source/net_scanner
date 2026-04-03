from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
                             QProgressBar, QLabel, QMessageBox, QHeaderView)
from PyQt6.QtWidgets import QFileDialog
from app.gui.worker import ScannerWorker
from app.core.export import export_data

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker: ScannerWorker | None = None
        self.init_ui()
        self._progres_data: list[dict] = []

    def init_ui(self):
        self.setWindowTitle("Python Network Scanner")
        self.setGeometry(100, 100, 900, 600)

        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)

        # --- Ввод данных ---
        input_layout = QHBoxLayout()
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("IP адрес (например, 127.0.0.1)")
        self.host_input.setText("127.0.0.1")
        
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Порты (например, 1-1000 или 80,443,8080)")
        self.port_input.setText("1-1000")
        
        self.scan_btn = QPushButton("Старт")
        self.scan_btn.clicked.connect(self.start_scan)
        
        self.stop_btn = QPushButton("Стоп")
        self.stop_btn.clicked.connect(self.stop_scan)
        self.stop_btn.setEnabled(False)

        self.exp_btn = QPushButton("Экспорт")
        self.exp_btn.clicked.connect(self.exp_scan)
        self.exp_btn.setEnabled(False)

        input_layout.addWidget(QLabel("Хост:"))
        input_layout.addWidget(self.host_input, 2)
        input_layout.addWidget(QLabel("Порты:"))
        input_layout.addWidget(self.port_input, 2)
        input_layout.addWidget(self.scan_btn)
        input_layout.addWidget(self.stop_btn)
        input_layout.addWidget(self.exp_btn)
        
        layout.addLayout(input_layout)

        # --- Прогресс и статус ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Готов к работе")
        layout.addWidget(self.status_label)

        # --- Таблица ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Порт", "Статус", "Сервис", "Баннер"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def parse_ports(self, text: str) -> list[int]:
        ports = []
        for part in text.split(','):
            part = part.strip()
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    ports.extend(range(start, end + 1))
                except ValueError:
                    raise ValueError
            else:
                try:
                    ports.append(int(part))
                except ValueError:
                    raise ValueError
        return sorted(set(ports))

    def start_scan(self):
        host = self.host_input.text().strip()
        try:
            ports = self.parse_ports(self.port_input.text())
        except ValueError:
            QMessageBox.critical(self, "Ошибка", "Неверный формат портов")
            return

        if not host or not ports:
            return

        # Сброс UI
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.show()
        self.status_label.setText(f"Сканирование {host}...")
        self.table.setRowCount(0)
        self._results_count = 0

        # Запуск воркера
        self.worker = ScannerWorker(host, ports)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def exp_scan(self):
        if not self._progres_data:
            QMessageBox.information(self, "Нет данных", "Нечего экспортировать")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить результаты", "scan_results.csv", "CSV Files (*.csv)")
        
        if filename:
            from app.core.export import export_data
            if export_data(self._progres_data, filename):
                QMessageBox.information(self, "Успех", f"Данные сохранены в {filename}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить файл")

    def stop_scan(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.status_label.setText("Остановка...")

    def on_progress(self, result):
        if result.status == "open":
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(result.port)))
            self.table.setItem(row, 1, QTableWidgetItem(result.status))
            self.table.setItem(row, 2, QTableWidgetItem(result.service))
            self.table.setItem(row, 3, QTableWidgetItem(result.banner or "-"))
            self._results_count += 1
            self.status_label.setText(f"Найдено открытых: {self._results_count}")
            self._progres_data.append({
                "Port": result.port,
                "Status": result.status,
                "Service": result.service,
                "Banner": result.banner})

    def on_finished(self):
        """Вызывается, когда поток завершил работу сам"""
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.hide()
        if not self.status_label.text().startswith("Остановка"):
            self.status_label.setText("Сканирование завершено")
            self.exp_btn.setEnabled(True)
        # Не обнуляем self.worker здесь, это сделает closeEvent или новый старт

    def on_error(self, msg):
        QMessageBox.critical(self, "Ошибка", msg)
        self.on_finished()

    def closeEvent(self, event):
        """
        КРИТИЧЕСКИ ВАЖНО: Корректное завершение потока при закрытии окна.
        Без этого метода будет 'QThread: Destroyed while thread is still running'.
        """
        if self.worker and self.worker.isRunning():
            # 1. Сигнализируем потоку остановиться
            self.worker.stop()
            
            # 2. Ждем завершения потока (блокируем закрытие GUI на короткое время)
            # timeout=3000ms защита от зависания навсегда
            if not self.worker.wait(3000):
                # Если поток не ответил за 3 секунды
                QMessageBox.warning(self, "Предупреждение", 
                                    "Сканирование не удалось завершить корректно.")
            
            # 3. Очищаем ссылку
            self.worker = None

        # Разрешаем закрытие приложения
        event.accept()
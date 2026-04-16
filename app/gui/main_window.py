from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QTableWidget,
                             QTableWidgetItem, QProgressBar, QLabel,
                             QMessageBox, QHeaderView, QFileDialog, QTabWidget)
from app.gui.worker import ScannerWorker
from app.core.export import export_data
from app.db.repository import ScanHistory
from app.core.ip_utils import parse_ip_range
from app.core.port_utils import parse_ports

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker: ScannerWorker | None = None
        self.history: ScanHistory | None = None
        self.init_ui()
        self._progress_data: list[dict] = []

    def _save_to_db(self):
        # --- Сохраняет текущие результаты в БД ---
        if not self.get_progress_data():
            QMessageBox.information(self, "Нет данных", "Нечего сохранять")
            return
        host = self.ip_range_input.text().strip()
        self.history.save_results(host, self.get_progress_data())
        QMessageBox.information(self, "Успех", "Данные сохранены в БД") 

    def _load_from_db(self):
        # --- Загружает историю из БД в таблицу ---
        records = self.history.get_history(limit=100)
        self.history_table.setRowCount(0)
        for row_idx, rec in enumerate(records):
            # rec — это кортеж из SQLite: (id, host, port, status, service, banner, scanned_at)
            self.history_table.insertRow(row_idx)
            for col_idx, value in enumerate(rec[1:6]):  # Пропускаем id, берём 5 полей
                self.history_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value or "-")))

    def init_ui(self):
        self.setWindowTitle("Python Network Scanner")
        self.setGeometry(100, 100, 900, 600)
        self.history = ScanHistory()

        """ """ """ Scanner """ """ """
        scaner_tab = QWidget()
        scaner_layout = QVBoxLayout(scaner_tab)

        # --- Ввод данных ---
        input_scanner_layout = QHBoxLayout()

        self.ip_range_input = QLineEdit()
        self.ip_range_input.setPlaceholderText("192.168.1.* или 192.168.1.1-100")

        # Добавляем в layout
        input_scanner_layout.addWidget(QLabel("IP/Диапазон:"))
        input_scanner_layout.addWidget(self.ip_range_input, 2)  # Диапазон
        
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Порты (например, 1-1000 или 80,443,8080)")
        self.port_input.setText("1-1000")
        
        self.scan_btn = QPushButton("▶️ Старт")
        self.scan_btn.clicked.connect(self.start_scan)
        
        self.stop_btn = QPushButton("⏹️ Стоп")
        self.stop_btn.clicked.connect(self.stop_scan)
        self.stop_btn.setEnabled(False)

        self.exp_btn = QPushButton("💾 Экспорт")
        self.exp_btn.clicked.connect(self.exp_scan)
        self.exp_btn.setEnabled(False)

        input_scanner_layout.addWidget(QLabel("Порты:"))
        input_scanner_layout.addWidget(self.port_input, 2)
        input_scanner_layout.addWidget(self.scan_btn)
        input_scanner_layout.addWidget(self.stop_btn)
        input_scanner_layout.addWidget(self.exp_btn)
        
        scaner_layout.addLayout(input_scanner_layout)

        # --- Прогресс и статус ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        scaner_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Готов к работе")
        scaner_layout.addWidget(self.status_label)

        # --- Таблица ---
        self.scanner_table = QTableWidget()
        self.scanner_table.setColumnCount(5)
        self.scanner_table.setHorizontalHeaderLabels(["Хост", "Порт", "Статус", "Обычно использует", "Баннер"])
        self.scanner_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        scaner_layout.addWidget(self.scanner_table)

        """ """ """ History """ """ """
        history_tab = QWidget()

        history_layout = QVBoxLayout(history_tab)
        control_history_layout = QHBoxLayout()

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(lambda: self._save_to_db())
        control_history_layout.addWidget(self.save_btn)

        self.get_btn = QPushButton("Загрузить")
        self.get_btn.clicked.connect(lambda: self._load_from_db())
        control_history_layout.addWidget(self.get_btn)
        
        # --- Таблица ---
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Хост", "Порт", "Статус", "Обычно использует", "Баннер"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        history_layout.addLayout(control_history_layout)
        history_layout.addWidget(self.history_table)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tabs.addTab(scaner_tab, "Сканер")
        self.tabs.addTab(history_tab, "История")
        self.tabs.currentChanged.connect(self.contain_history)

    def start_scan(self):
        # Собираем список хостов
        hosts = []
        
        # Приоритет: если заполнен диапазон — используем его
        if self.ip_range_input.text().strip():
            hosts = list(parse_ip_range(self.ip_range_input.text()))
            if not hosts:
                QMessageBox.critical(self, "Ошибка", "Введите корректный IP или диапазон")
                return
        
        # Парсим порты
        try:
            ports = parse_ports(self.port_input.text())
        except ValueError:
            QMessageBox.critical(self, "Ошибка", "Неверный формат портов")
            return

        # Подготовка UI
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.show()

        if not ports:
            # Режим только пинг: 1 проверка на хост
            total_targets = len(hosts)
            self.status_label.setText(f"Режим: только ping, {len(hosts)} хостов")
        else:
            # Режим сканирования портов
            total_targets = len(hosts) * len(ports)
            self.status_label.setText(f"План: {len(hosts)} хостов × {len(ports)} портов = {total_targets}")

        self.status_label.setText(f"План: {len(hosts)} хостов × {len(ports)} портов = {total_targets} проверок")
        
        self.scanner_table.setRowCount(0)
        self._progress_data = []  # Сброс данных

        # Запуск воркера
        # Передаём список хостов вместо одного
        self.worker = ScannerWorker(hosts, ports)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

        self._total_planned = total_targets
        self._progress_count = 0
        self.progress_bar.setRange(0, max(1, self._total_planned))  # Защита от 0
        self.progress_bar.setValue(0)

    def exp_scan(self):
        if not self.get_progress_data():
            QMessageBox.information(self, "Нет данных", "Нечего экспортировать")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить результаты", "scan_results.csv", "CSV Files (*.csv)")
        
        if filename:
            if export_data(self.get_progress_data(), filename):
                QMessageBox.information(self, "Успех", f"Данные сохранены в {filename}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить файл")

    def stop_scan(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.status_label.setText("Остановка...")

    def on_progress(self, result: dict):
        # Показываем и "alive", и открытые порты
        if result["status"] in ("open", "alive"):
            row = self.scanner_table.rowCount()
            self.scanner_table.insertRow(row)
            
            self.scanner_table.setItem(row, 0, QTableWidgetItem(result["host"]))
            
            # Для пинга порт = 0, отображаем как "ICMP"
            port_display = "ICMP" if result["port"] == 0 else str(result["port"])
            self.scanner_table.setItem(row, 1, QTableWidgetItem(port_display))
            
            self.scanner_table.setItem(row, 2, QTableWidgetItem(result["status"]))
            self.scanner_table.setItem(row, 3, QTableWidgetItem(result["service"]))
            self.scanner_table.setItem(row, 4, QTableWidgetItem(result["banner"] or "-"))
            
            # Сохраняем для экспорта
            self._progress_data.append({
                "Host": result["host"],
                "Port": port_display,
                "Status": result["status"],
                "Service": result["service"],
                "Banner": result["banner"] or ""
            })
            
            self._progress_count += 1
            self.progress_bar.setValue(self._progress_count)

    def on_finished(self):
        # Вызывается, когда поток завершил работу сам
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
            # Сигнализируем потоку остановиться
            self.worker.stop()
            
            # Ждем завершения потока (блокируем закрытие GUI на короткое время)
            # timeout=3000ms защита от зависания навсегда
            if not self.worker.wait(3000):
                # Если поток не ответил за 3 секунды
                QMessageBox.warning(self, "Предупреждение", 
                                    "Сканирование не удалось завершить корректно.")
            
            # Очищаем ссылку
            self.worker = None

        # Разрешаем закрытие приложения
        event.accept()

    def get_progress_data(self):
        return self._progress_data

    def set_progress_data(self, port, status, service, banner):
        self._progress_data.append({
                "Port": port, "Status": status, "Service": service, "Banner": banner})
        
    def contain_history(self, index):
    # Заполняет вкладку 'История' при переключении
        if index != 1:  # 1 — индекс вкладки "История"
            return
        
        data = self.get_progress_data()
        if not data:
            return
        
        self.history_table.setRowCount(0)  # Очистка
        self.history_table.setColumnCount(5)  # Согласуем со сканером
        self.history_table.setHorizontalHeaderLabels(["Host", "Port", "Status", "Service", "Banner"])
        
        for row_idx, row in enumerate(data):
            self.history_table.insertRow(row_idx)
            # Сопоставляем ключи словаря с индексами колонок
            columns = ["Host", "Port", "Status", "Service", "Banner"]
            for col_idx, key in enumerate(columns):
                value = row.get(key, "")
                self.history_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
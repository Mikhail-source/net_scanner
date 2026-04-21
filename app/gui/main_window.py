from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QTableWidget,
                             QTableWidgetItem, QProgressBar, QLabel,
                             QMessageBox, QHeaderView, QFileDialog, QTabWidget,
                             QMenu, QApplication, QCheckBox)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
from app.gui.worker import ScannerWorker
from app.db.repository import ScanHistory
from app.core.input_parser import InputParser, ScanRequest

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker: ScannerWorker | None = None
        self.history: ScanHistory | None = None
        self.scan: InputParser
        self.scan_request: ScanRequest
        self.init_ui()
        self._progress_data: list[dict] = []
        self._summary: dict
        self._start_time: datetime
        self._status_colors = {
                "open": "#d4edda",    # светло-зелёный
                "alive": "#cce5ff",   # светло-голубой
                "closed": "#f8f9fa",  # светло-серый
                "filtered": "#fff3cd",# светло-жёлтый
                "dead": "#f8d7da",    # светло-красный
                }

    def _save_to_db(self):
        # --- Сохраняет текущие результаты в БД ---
        if not self.get_progress_data():
            QMessageBox.information(self,
                                    "Нет данных", "Нечего сохранять")
            return
        host = self.ip_range_input.text().strip()
        self.history.save_results(host, self.get_progress_data())
        QMessageBox.information(self, "Успех", "Данные сохранены в БД")

    def _load_from_db(self):
        # --- Загружает историю из БД в таблицу ---
        records = self.history.get_history(limit=100)
        self.history_table.setRowCount(0)
        for row_idx, rec in enumerate(records):
            # rec — это кортеж из SQLite:
            # (id, host, port, status, service, banner, scanned_at)
            self.history_table.insertRow(row_idx)
            # Пропускаем id, берём 5 полей
            for col_idx, value in enumerate(rec[1:6]):
                self.history_table.setItem(row_idx, col_idx,
                                           QTableWidgetItem(str(value or "-")))

    def _show_table_menu(self, position):
        menu = QMenu()
        copy_action = menu.addAction("📋 Копировать строку")
        
        action = menu.exec(self.scanner_table.viewport().mapToGlobal(position))
        
        if action == copy_action:
            row = self.scanner_table.currentRow()
            if row >= 0:
                row_data = [
                    self.scanner_table.item(row, col).text()
                    for col in range(self.scanner_table.columnCount())
                    if self.scanner_table.item(row, col)
                ]
                QApplication.clipboard().setText("\t".join(row_data))

    def _clear_results(self):
        # Если сканирование идёт — блокируем очистку или сначала останавливаем
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Внимание", "Остановите сканирование перед очисткой")
            return

        self.scanner_table.setRowCount(0)
        self._progress_data = []
        self._progress_count = 0
        self.progress_bar.setValue(0)
        self.status_label.setText("Результаты очищены")

    def _show_summary(self):
        """Показывает статистику после сканирования"""
        alive_count = len(self._summary["hosts_alive"])  # Уникальные живые хосты
        
        # Формируем топ сервисов
        services = self._summary["services"]
        top_services = sorted(services.items(), key=lambda x: x[1], reverse=True)[:5]
        services_str = "\n".join(f"   ├── {svc}: {cnt}" for svc, cnt in top_services)
        if not services_str:
            services_str = "   └── (нет данных)"
        
        summary = (
            f"✅ Сканирование завершено!\n"
            f"├── Хостов проверено: {self._summary['hosts_checked']}\n"
            f"├── Живых хостов: {alive_count}\n"
            f"├── Открытых портов: {self._summary['ports_open']}\n"
            f"├── Зафильтровано: {self._summary['ports_filtered']}\n"
            f"└── Топ сервисов:\n{services_str}\n"
            f"Время: {self._summary["time"]}"
        )
        
        QMessageBox.information(self, "📊 Статистика", summary)

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
        self.ip_range_input.setPlaceholderText(
            "192.168.1.* или 192.168.1.1-100")

        # Добавляем в layout
        input_scanner_layout.addWidget(QLabel("IP/Диапазон:"))
        input_scanner_layout.addWidget(self.ip_range_input, 2)
        
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText(
            "Порты (например, 1-1000 или 80,443,8080)")
        self.port_input.setText("1-1000")
        input_scanner_layout.addWidget(QLabel("Порты:"))
        input_scanner_layout.addWidget(self.port_input, 2)

        self.force_scan_checkbox = QCheckBox("🔍")
        self.force_scan_checkbox.setChecked(False)
        self.force_scan_checkbox.setToolTip(
        "Если включено: порты сканируются "
        "даже если хост не отвечает на ping.\n"
        "Полезно, когда ICMP заблокирован фаерволом, но сервисы доступны."
)
        input_scanner_layout.addWidget(self.force_scan_checkbox)
        
        self.scan_btn = QPushButton("▶️ Старт")
        self.scan_btn.clicked.connect(self.start_scan)
        input_scanner_layout.addWidget(self.scan_btn)
        
        self.stop_btn = QPushButton("⏹️ Стоп")
        self.stop_btn.clicked.connect(self.stop_scan)
        self.stop_btn.setEnabled(False)
        input_scanner_layout.addWidget(self.stop_btn)

        self.clear_btn = QPushButton("🗑️ Очистить")
        self.clear_btn.clicked.connect(self._clear_results)
        input_scanner_layout.addWidget(self.clear_btn)

        self.exp_btn = QPushButton("💾 Экспорт")
        self.exp_btn.clicked.connect(self.exp_scan)
        self.exp_btn.setEnabled(False)
        input_scanner_layout.addWidget(self.exp_btn)
        
        scaner_layout.addLayout(input_scanner_layout)

        # --- Прогресс и статус ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        scaner_layout.addWidget(self.progress_bar)

        # --- Таблица ---
        self.scanner_table = QTableWidget()
        self.scanner_table.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.scanner_table.customContextMenuRequested.connect(
            self._show_table_menu)
        self.scanner_table.setColumnCount(5)
        self.scanner_table.setHorizontalHeaderLabels(
            ["Хост", "Порт", "Статус", "Обычно использует", "Баннер"])
        self.scanner_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        scaner_layout.addWidget(self.scanner_table)

        self.status_label = QLabel("Готов к работе")
        scaner_layout.addWidget(self.status_label)

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
        self.history_table.setHorizontalHeaderLabels(
            ["Хост", "Порт", "Статус", "Обычно использует", "Баннер"])
        self.history_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)

        history_layout.addLayout(control_history_layout)
        history_layout.addWidget(self.history_table)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tabs.addTab(scaner_tab, "Сканер")
        self.tabs.addTab(history_tab, "История")
        self.tabs.currentChanged.connect(self.contain_history)

    def start_scan(self):
        self._start_time = datetime.now()
        self.scan = InputParser()
        try:
            self.scan_request = self.scan.parse(self.ip_range_input.text(),
                                                self.port_input.text())
            if not self.scan_request.hosts:
                QMessageBox.critical(
                    self, "Ошибка", "Введите корректный IP или диапазон")
                return
        except:
            QMessageBox.critical(self, "Ошибка", "Неверный формат портов")
            return
        
        self._summary = {"hosts_checked": len(self.scan_request.hosts),
                         "hosts_alive": set(),
                         "ports_open": 0,
                         "ports_closeed": 0,
                         "ports_filtered": 0,
                         "services": {},
                         "time": ""}

        # Подготовка UI
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.show()

        total_targets = (len(self.scan_request.hosts) *
                         max(1, len(self.scan_request.ports)))
        if self.scan_request.ping_mode:
            # Режим только пинг: 1 проверка на хост
            self.status_label.setText(
                f"Режим: только ping, {len(self.scan_request.hosts)} хостов")
        else:
            # Режим сканирования портов
            self.status_label.setText(
                f"План: {len(self.scan_request.hosts)} хостов × "
                f"{len(self.scan_request.ports)} портов = {total_targets}")

        self.status_label.setText(
            f"План: {len(self.scan_request.hosts)} хостов × "
            f"{len(self.scan_request.ports)} портов = "
            f"{total_targets} проверок")
        self.scanner_table.setRowCount(0)
        self._progress_data = []  # Сброс данных

        # Запуск воркера
        # Передаём список хостов вместо одного
        self.worker = ScannerWorker(
            self.scan_request.hosts,
            self.scan_request.ports,
            force_scan=self.force_scan_checkbox.isChecked()
        )       
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

        self._progress_count = 0
        self.progress_bar.setRange(0, max(1, total_targets))  # Защита от 0
        self.progress_bar.setValue(0)

    def exp_scan(self):
        if not self.get_progress_data():
            QMessageBox.information(self,
                                    "Нет данных", "Нечего экспортировать")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить результаты", "scan_results.csv",
            "CSV Files (*.csv)")
        
        if filename:
            if self.parser.export(self.get_progress_data(), filename):
                QMessageBox.information(self, "Успех",
                                        f"Данные сохранены в {filename}")
            else:
                QMessageBox.critical(self, "Ошибка",
                                     "Не удалось сохранить файл")

    def stop_scan(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.status_label.setText("Остановка...")

    def on_progress(self, result: dict):
        host = result["host"]
        status = result["status"]
        color = self._status_colors.get(result["status"], QColor("#ffffff"))

        if status == "alive":
            self._summary["hosts_alive"].add(host)  # Хост жив по ping
        elif status == "open":
            self._summary["hosts_alive"].add(host)  # Хост жив, т.к. порт открыт!
            self._summary["ports_open"] += 1
        # Статистика сервисов
            service = result.get("service", "unknown")
            self._summary["services"][service] = self._summary["services"].get(service, 0) + 1
        elif status == "filtered":
            self._summary["ports_filtered"] += 1
        elif status == "dead":
            pass  # Хост мёртв, ничего не считаем

        if status not in ["dead", "closed"]:
            row = self.scanner_table.rowCount()
            self.scanner_table.insertRow(row)
            
            self.scanner_table.setItem(row, 0,
                                       QTableWidgetItem(result["host"]))
            
            # Для пинга порт = 0, отображаем как "ICMP"
            if result["port"] == 0:
                port_display = "ICMP"
            else:
                port_display = str(result["port"])
                
            self.scanner_table.setItem(
                row, 1, QTableWidgetItem(port_display))
            self.scanner_table.setItem(
                row, 2, QTableWidgetItem(result["status"]))
            self.scanner_table.setItem(
                row, 3, QTableWidgetItem(result["service"]))
            self.scanner_table.setItem(
                row, 4, QTableWidgetItem(result["banner"] or "-"))

            for col in range(self.scanner_table.columnCount()):
                item = self.scanner_table.item(row, col)
                if item:
                    item.setBackground(QColor(color))
                    item.setForeground(QColor("#000000"))
            
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
        time = datetime.now() - self._start_time
        self._summary["time"] = str(time).split('.')[0]
        # Вызывается, когда поток завершил работу сам
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.hide()
        if not self.status_label.text().startswith("Остановка"):
            self.status_label.setText("Сканирование завершено")
            self.exp_btn.setEnabled(True)
        # Не обнуляем self.worker здесь,
        # это сделает closeEvent или новый старт
        self._show_summary()

    def on_error(self, msg):
        QMessageBox.critical(self, "Ошибка", msg)
        self.on_finished()

    def closeEvent(self, event):
        """
        КРИТИЧЕСКИ ВАЖНО: Корректное завершение потока при закрытии окна.
        Без этого будет 'QThread: Destroyed while thread is still running'.
        """
        if self.worker and self.worker.isRunning():
            # Сигнализируем потоку остановиться
            self.worker.stop()
            
            # Ждем завершения потока (блокируем закрытие GUI на короткое время)
            # timeout=3000ms защита от зависания навсегда
            if not self.worker.wait(3000):
                # Если поток не ответил за 3 секунды
                QMessageBox.warning(
                    self, "Предупреждение",
                    "Сканирование не удалось завершить корректно.")
            
            # Очищаем ссылку
            self.worker = None

        # Разрешаем закрытие приложения
        event.accept()

    def get_progress_data(self):
        return self._progress_data

    def set_progress_data(self, port, status, service, banner):
        self._progress_data.append({
                "Port": port, "Status": status,
                "Service": service, "Banner": banner})
        
    def contain_history(self, index):
    # Заполняет вкладку 'История' при переключении
        if index != 1:  # 1 — индекс вкладки "История"
            return
        
        data = self.get_progress_data()
        if not data:
            return
        
        self.history_table.setRowCount(0)  # Очистка
        self.history_table.setColumnCount(5)  # Согласуем со сканером
        self.history_table.setHorizontalHeaderLabels(
            ["Host", "Port", "Status", "Service", "Banner"])
        
        for row_idx, row in enumerate(data):
            self.history_table.insertRow(row_idx)
            # Сопоставляем ключи словаря с индексами колонок
            columns = ["Host", "Port", "Status", "Service", "Banner"]
            for col_idx, key in enumerate(columns):
                value = row.get(key, "")
                self.history_table.setItem(
                    row_idx, col_idx, QTableWidgetItem(str(value)))
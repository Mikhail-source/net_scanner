from PyQt6.QtWidgets import QFileDialog, QApplication
import sys

app = QApplication(sys.argv)
path, _ = QFileDialog.getSaveFileName(
    caption="Сохранить Excel",
    directory="отчёт.xlsx",
    filter="Excel (*.xlsx)"
)
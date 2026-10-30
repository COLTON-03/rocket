from __future__ import annotations

from dataclasses import asdict, is_dataclass

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class TelemetryTable(QWidget):
	def __init__(self) -> None:
		super().__init__()
		layout = QVBoxLayout(self)
		self.table = QTableWidget(self)
		self.table.setColumnCount(2)
		self.table.setHorizontalHeaderLabels(["Field", "Value"])
		self.table.horizontalHeader().setStretchLastSection(True)
		layout.addWidget(self.table)

	def update_record(self, record: object) -> None:
		if not is_dataclass(record):
			return
		payload = asdict(record)
		self.table.setRowCount(len(payload))
		for row, (key, value) in enumerate(payload.items()):
			self.table.setItem(row, 0, QTableWidgetItem(key))
			self.table.setItem(row, 1, QTableWidgetItem(f"{value}"))

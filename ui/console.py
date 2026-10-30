from __future__ import annotations

from PyQt6.QtWidgets import (
	QCheckBox,
	QHBoxLayout,
	QLineEdit,
	QPlainTextEdit,
	QVBoxLayout,
	QWidget,
)


class ConsolePane(QWidget):
	def __init__(self) -> None:
		super().__init__()
		self._all_lines: list[str] = []

		layout = QVBoxLayout(self)
		controls = QHBoxLayout()

		self.filter_edit = QLineEdit(self)
		self.filter_edit.setPlaceholderText("Filter text")
		self.filter_edit.textChanged.connect(self._rebuild_view)

		self.autoscroll_checkbox = QCheckBox("Autoscroll", self)
		self.autoscroll_checkbox.setChecked(True)

		controls.addWidget(self.filter_edit)
		controls.addWidget(self.autoscroll_checkbox)

		self.text = QPlainTextEdit(self)
		self.text.setReadOnly(True)

		layout.addLayout(controls)
		layout.addWidget(self.text)

	def append_line(self, line: str) -> None:
		self._all_lines.append(line)
		if self._matches_filter(line):
			self.text.appendPlainText(line)
			if self.autoscroll_checkbox.isChecked():
				scrollbar = self.text.verticalScrollBar()
				scrollbar.setValue(scrollbar.maximum())

	def clear(self) -> None:
		self._all_lines.clear()
		self.text.clear()

	def _matches_filter(self, line: str) -> bool:
		needle = self.filter_edit.text().strip().lower()
		return not needle or needle in line.lower()

	def _rebuild_view(self) -> None:
		self.text.clear()
		for line in self._all_lines:
			if self._matches_filter(line):
				self.text.appendPlainText(line)

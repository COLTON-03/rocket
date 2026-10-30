from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget


class StateBar(QWidget):
	STATES = ["PAD", "FLIGHT", "DESCENT", "LANDED"]

	def __init__(self) -> None:
		super().__init__()
		self._state = 0
		self._deploy_text = ""

		layout = QHBoxLayout(self)
		self._label = QLabel("PAD", self)
		self._deploy = QLabel("", self)
		layout.addWidget(self._label)
		layout.addWidget(self._deploy)
		layout.addStretch(1)
		self.setMinimumHeight(42)

	def update_state(self, state: int, deploy_text: str = "") -> None:
		self._state = max(0, min(3, state))
		self._deploy_text = deploy_text
		self._label.setText(self.STATES[self._state])
		self._deploy.setText(deploy_text)
		self.update()

	def paintEvent(self, event) -> None:  # type: ignore[override]
		super().paintEvent(event)
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)

		start_x = 200
		center_y = self.height() // 2
		step = 120
		radius = 10

		for i, name in enumerate(self.STATES):
			x = start_x + i * step
			color = QColor(80, 180, 120) if i == self._state else QColor(90, 90, 90)
			painter.setBrush(color)
			painter.setPen(QColor(180, 180, 180))
			painter.drawEllipse(x - radius, center_y - radius, radius * 2, radius * 2)
			painter.drawText(x - 35, center_y + 28, name)

		if self._deploy_text:
			painter.setPen(Qt.GlobalColor.yellow)
			painter.drawText(start_x + step * 4, center_y + 5, self._deploy_text)

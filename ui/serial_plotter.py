from __future__ import annotations

from typing import Sequence

import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (
	QComboBox,
	QHBoxLayout,
	QPushButton,
	QVBoxLayout,
	QWidget,
)


class SerialPlotter(QWidget):
	def __init__(self) -> None:
		super().__init__()
		self._paused = False
		self._latest_names: list[str] = []
		self._latest_data = np.empty((0, 0), dtype=np.float64)

		layout = QVBoxLayout(self)
		controls = QHBoxLayout()

		self.pause_button = QPushButton("Pause", self)
		self.pause_button.clicked.connect(self._toggle_pause)

		self.clear_button = QPushButton("Clear", self)
		self.clear_button.clicked.connect(self.clear_plot)

		self.window_selector = QComboBox(self)
		self.window_selector.addItems(["30 s", "60 s", "120 s", "all"])

		controls.addWidget(self.pause_button)
		controls.addWidget(self.clear_button)
		controls.addWidget(self.window_selector)
		controls.addStretch(1)

		self.plot_widget = pg.PlotWidget(self)
		self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
		self.plot_widget.addLegend()

		layout.addLayout(controls)
		layout.addWidget(self.plot_widget)

		self._curves: dict[str, pg.PlotDataItem] = {}

	def set_data(self, channel_names: Sequence[str], values: np.ndarray) -> None:
		if self._paused:
			return
		self._latest_names = list(channel_names)
		self._latest_data = values
		self._redraw()

	def clear_plot(self) -> None:
		self.plot_widget.clear()
		self.plot_widget.addLegend()
		self._curves.clear()

	def _toggle_pause(self) -> None:
		self._paused = not self._paused
		self.pause_button.setText("Resume" if self._paused else "Pause")
		if not self._paused:
			self._redraw()

	def _window_seconds(self) -> float | None:
		text = self.window_selector.currentText()
		if text == "all":
			return None
		return float(text.split()[0])

	def _redraw(self) -> None:
		if len(self._latest_names) < 2 or self._latest_data.size == 0:
			return

		x = self._latest_data[:, 0]
		window_s = self._window_seconds()
		if window_s is not None and x.size > 0:
			cutoff = x[-1] - window_s
			mask = x >= cutoff
			x = x[mask]
			y_data = self._latest_data[mask]
		else:
			y_data = self._latest_data

		for idx, name in enumerate(self._latest_names[1:], start=1):
			if name not in self._curves:
				self._curves[name] = self.plot_widget.plot(name=name)
			self._curves[name].setData(x, y_data[:, idx])

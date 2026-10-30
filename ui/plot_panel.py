from __future__ import annotations

from typing import Sequence

import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QLabel, QStackedLayout, QVBoxLayout, QWidget


class PlotPanel(QWidget):
	def __init__(self, title: str) -> None:
		super().__init__()
		layout = QVBoxLayout(self)

		self._title = QLabel(title, self)
		self._title.setStyleSheet("font-weight: bold;")

		self._stack = QStackedLayout()
		self._plot = pg.PlotWidget(self)
		self._plot.showGrid(x=True, y=True, alpha=0.2)
		self._plot.addLegend()
		self._nodata = QLabel("no data from this source", self)
		self._nodata.setStyleSheet("color: #9aa0a6;")

		plot_container = QWidget(self)
		plot_layout = QVBoxLayout(plot_container)
		plot_layout.setContentsMargins(0, 0, 0, 0)
		plot_layout.addWidget(self._plot)

		empty_container = QWidget(self)
		empty_layout = QVBoxLayout(empty_container)
		empty_layout.addWidget(self._nodata)

		self._stack.addWidget(plot_container)
		self._stack.addWidget(empty_container)

		layout.addWidget(self._title)
		layout.addLayout(self._stack)

		self._curves: dict[str, pg.PlotDataItem] = {}
		self._markers: list[pg.InfiniteLine] = []

	def set_series(self, t_s: np.ndarray, names: Sequence[str], values: Sequence[np.ndarray]) -> None:
		if t_s.size == 0:
			self._stack.setCurrentIndex(1)
			return
		self._stack.setCurrentIndex(0)
		for name, series in zip(names, values, strict=True):
			if name not in self._curves:
				self._curves[name] = self._plot.plot(name=name)
			self._curves[name].setData(t_s, series)

	def set_event_markers(self, event_times_s: list[float]) -> None:
		for marker in self._markers:
			self._plot.removeItem(marker)
		self._markers.clear()
		for t_s in event_times_s:
			line = pg.InfiniteLine(pos=t_s, angle=90, pen=pg.mkPen((160, 160, 160), style=pg.QtCore.Qt.PenStyle.DashLine))
			self._plot.addItem(line)
			self._markers.append(line)

from __future__ import annotations

import math

from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class GpsPanel(QWidget):
	def __init__(self) -> None:
		super().__init__()
		self._lat0: float | None = None
		self._lon0: float | None = None

		layout = QVBoxLayout(self)
		self.latlon_label = QLabel("lat/lon: -", self)
		self.metric_label = QLabel("dE/dN: -", self)
		self.copy_button = QPushButton("Copy lat/lon", self)
		self.copy_button.clicked.connect(self._copy)
		layout.addWidget(self.latlon_label)
		layout.addWidget(self.metric_label)
		layout.addWidget(self.copy_button)

	def update_fix(self, fix: int, lat: float, lon: float) -> None:
		if fix == 0 or (lat == 0.0 and lon == 0.0):
			return
		if self._lat0 is None:
			self._lat0 = lat
			self._lon0 = lon
		self.latlon_label.setText(f"lat/lon: {lat:.6f}, {lon:.6f}")

		lat0_rad = math.radians(self._lat0)
		dlon = math.radians(lon - self._lon0)
		dlat = math.radians(lat - self._lat0)
		r = 6_371_000.0
		d_e = r * math.cos(lat0_rad) * dlon
		d_n = r * dlat
		distance = math.hypot(d_e, d_n)
		bearing = (math.degrees(math.atan2(d_e, d_n)) + 360.0) % 360.0
		self.metric_label.setText(
			f"dE {d_e:.1f} m, dN {d_n:.1f} m, dist {distance:.1f} m, brg {bearing:.1f}°"
		)

	def _copy(self) -> None:
		QGuiApplication.clipboard().setText(self.latlon_label.text().replace("lat/lon: ", ""))

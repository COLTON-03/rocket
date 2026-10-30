from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters
from PyQt6.QtWidgets import QDialog, QFileDialog, QLabel, QPushButton, QVBoxLayout


@dataclass(slots=True)
class FlightStats:
	apogee_m: float
	max_velocity_ms: float
	max_accel_g: float
	flight_duration_s: float


def compute_flight_stats(channel_names: list[str], data: np.ndarray) -> FlightStats:
	if data.size == 0:
		return FlightStats(0.0, 0.0, 0.0, 0.0)
	idx = {name: i for i, name in enumerate(channel_names)}
	t = data[:, 0]
	alt = data[:, idx["alt_m"]] if "alt_m" in idx else np.array([0.0])
	vel = data[:, idx["vel_ms"]] if "vel_ms" in idx else np.array([0.0])
	if "apk" in idx:
		acc = data[:, idx["apk"]]
	elif "amag" in idx:
		acc = data[:, idx["amag"]]
	else:
		acc = np.array([0.0])
	return FlightStats(
		apogee_m=float(np.nanmax(alt)),
		max_velocity_ms=float(np.nanmax(np.abs(vel))),
		max_accel_g=float(np.nanmax(np.abs(acc))),
		flight_duration_s=float(t[-1] - t[0]) if t.size > 1 else 0.0,
	)


class AnalysisDialog(QDialog):
	def __init__(self, stats: FlightStats, plot_widget: pg.PlotWidget | None = None) -> None:
		super().__init__()
		self.setWindowTitle("Post-Flight Analysis")
		self._stats = stats
		self._plot_widget = plot_widget

		layout = QVBoxLayout(self)
		self.summary_label = QLabel(self._summary_text(), self)
		self.export_csv_button = QPushButton("Export CSV", self)
		self.export_png_button = QPushButton("Export PNG", self)
		self.export_csv_button.clicked.connect(self._export_csv)
		self.export_png_button.clicked.connect(self._export_png)
		layout.addWidget(self.summary_label)
		layout.addWidget(self.export_csv_button)
		layout.addWidget(self.export_png_button)

	def _summary_text(self) -> str:
		return (
			f"Apogee: {self._stats.apogee_m:.1f} m\n"
			f"Max velocity: {self._stats.max_velocity_ms:.1f} m/s\n"
			f"Max |a|: {self._stats.max_accel_g:.2f} g\n"
			f"Flight duration: {self._stats.flight_duration_s:.1f} s"
		)

	def _export_csv(self) -> None:
		path, _ = QFileDialog.getSaveFileName(self, "Save Stats CSV", "stats.csv", "CSV Files (*.csv)")
		if not path:
			return
		with Path(path).open("w", encoding="utf-8", newline="") as f:
			writer = csv.writer(f)
			writer.writerow(["metric", "value"])
			writer.writerow(["apogee_m", self._stats.apogee_m])
			writer.writerow(["max_velocity_ms", self._stats.max_velocity_ms])
			writer.writerow(["max_accel_g", self._stats.max_accel_g])
			writer.writerow(["flight_duration_s", self._stats.flight_duration_s])

	def _export_png(self) -> None:
		if self._plot_widget is None:
			return
		path, _ = QFileDialog.getSaveFileName(self, "Save Dashboard PNG", "dashboard.png", "PNG Files (*.png)")
		if not path:
			return
		exporter = pyqtgraph.exporters.ImageExporter(self._plot_widget.plotItem)
		exporter.export(path)

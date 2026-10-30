from __future__ import annotations

from dataclasses import asdict
from math import isnan

import numpy as np
from PyQt6.QtWidgets import QGridLayout, QLabel, QWidget

from model.link_stats import LinkSnapshot
from ui.gps_panel import GpsPanel
from ui.plot_panel import PlotPanel
from ui.state_bar import StateBar
from ui.status_panel import StatusPanel
from ui.telemetry_table import TelemetryTable


class Dashboard(QWidget):
	def __init__(self) -> None:
		super().__init__()
		grid = QGridLayout(self)

		self.accel_panel = PlotPanel("Acceleration (g)")
		self.gyro_panel = PlotPanel("Gyro (dps)")
		self.battery_panel = PlotPanel("Battery (V)")
		self.link_panel = PlotPanel("RSSI/SNR")
		self.alt_panel = PlotPanel("Altitude (m)")
		self.velocity_panel = PlotPanel("Vertical Velocity (m/s)")
		self.gps_alt_panel = PlotPanel("GPS vs Baro Altitude")
		self.pt_panel = PlotPanel("Pressure/Temperature")

		self.status_panel = StatusPanel()
		self.telemetry_table = TelemetryTable()
		self.gps_panel = GpsPanel()
		self.state_bar = StateBar()
		self.alarm_banner = QLabel("", self)

		grid.addWidget(self.accel_panel, 0, 0)
		grid.addWidget(self.gyro_panel, 0, 1)
		grid.addWidget(self.battery_panel, 0, 2)
		grid.addWidget(self.link_panel, 0, 3)

		grid.addWidget(self.alt_panel, 1, 0)
		grid.addWidget(self.status_panel, 1, 1, 1, 2)
		grid.addWidget(self.telemetry_table, 1, 3)

		grid.addWidget(self.velocity_panel, 2, 0)
		grid.addWidget(self.gps_alt_panel, 2, 1)
		grid.addWidget(self.gps_panel, 2, 2)
		grid.addWidget(self.pt_panel, 2, 3)

		grid.addWidget(self.alarm_banner, 3, 0, 1, 4)
		grid.addWidget(self.state_bar, 4, 0, 1, 4)

		self._event_times: list[float] = []

	def add_event_time(self, t_s: float) -> None:
		self._event_times.append(t_s)

	def set_alarm(self, text: str) -> None:
		self.alarm_banner.setText(text)

	def update_from_record(self, record: object, channel_names: list[str], data: np.ndarray, source: str) -> None:
		if data.size == 0 or len(channel_names) == 0:
			return

		index = {name: i for i, name in enumerate(channel_names)}
		t_s = data[:, 0]

		def draw(panel: PlotPanel, fields: list[str]) -> None:
			present = [name for name in fields if name in index]
			if not present:
				return
			series = [data[:, index[name]] for name in present]
			panel.set_series(t_s, present, series)
			panel.set_event_markers(self._event_times)

		draw(self.accel_panel, ["ax", "ay", "az", "apk"])
		draw(self.gyro_panel, ["gx", "gy", "gz"])
		draw(self.battery_panel, ["batt_v"])
		draw(self.link_panel, ["rssi", "snr"])
		draw(self.alt_panel, ["alt_m", "max_m"])
		draw(self.velocity_panel, ["vel_ms"])
		draw(self.gps_alt_panel, ["gps_alt", "alt_m"])
		draw(self.pt_panel, ["press_pa", "temp_c"])

		self.telemetry_table.update_record(record)

		payload = asdict(record)
		if "state" not in payload:
			return

		state = int(payload.get("state", 0)) if not isnan(float(payload.get("state", 0))) else 0
		fire = int(payload.get("fire", 0)) if not isnan(float(payload.get("fire", 0))) else 0
		deploy_text = "BARO" if fire == 1 else "TIMER" if fire == 2 else ""
		self.state_bar.update_state(state=min(state, 3), deploy_text=deploy_text)

		if "fix" in payload and "lat" in payload and "lon" in payload:
			fix = int(payload.get("fix", 0))
			lat = float(payload.get("lat", 0.0))
			lon = float(payload.get("lon", 0.0))
			self.gps_panel.update_fix(fix=fix, lat=lat, lon=lon)

	def update_status(self, snapshot: LinkSnapshot, ok: int | None, ierr: int | None) -> None:
		self.status_panel.update_view(snapshot=snapshot, ok=ok, ierr=ierr)

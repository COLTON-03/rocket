from __future__ import annotations

import math
import queue
import random
import time

from PyQt6.QtCore import QThread

from sources.base import Source


class SimSource(QThread, Source):
	def __init__(
		self,
		output_queue: queue.Queue[tuple[float, str, str]],
		emit_mode: str = "both",
		speed: float = 1.0,
		packet_loss_pct: float = 0.0,
		reboot_time_s: float | None = None,
		pad_knock: bool = False,
	) -> None:
		super().__init__()
		self._output_queue = output_queue
		self._emit_mode = emit_mode
		self._speed = max(0.1, speed)
		self._packet_loss_pct = max(0.0, min(100.0, packet_loss_pct))
		self._reboot_time_s = reboot_time_s
		self._pad_knock = pad_knock
		self._running = False

		self._rng = random.Random(7)
		self._lora_cnt = 0
		self._rocket_t_ms = 0
		self._did_reboot = False
		self._last_lora_emit = -1.0

	def configure(
		self,
		emit_mode: str,
		speed: float,
		packet_loss_pct: float,
		reboot_time_s: float | None,
		pad_knock: bool,
	) -> None:
		self._emit_mode = emit_mode
		self._speed = max(0.1, speed)
		self._packet_loss_pct = max(0.0, min(100.0, packet_loss_pct))
		self._reboot_time_s = reboot_time_s
		self._pad_knock = pad_knock

	def start_source(self) -> None:
		self._running = True
		self._lora_cnt = 0
		self._rocket_t_ms = 0
		self._did_reboot = False
		self._last_lora_emit = -1.0
		if not self.isRunning():
			self.start()

	def stop_source(self) -> None:
		self._running = False
		self.wait(3000)

	def run(self) -> None:
		dt = 0.05
		t = 0.0
		while self._running:
			flight = self._flight_point(t)

			if self._reboot_time_s is not None and not self._did_reboot and t >= self._reboot_time_s:
				self._did_reboot = True
				self._lora_cnt = 0
				self._rocket_t_ms = 0

			host_t = time.time()

			if self._emit_mode in {"A", "both"} and self._should_emit_lora(t):
				line = self._make_lora_line(flight)
				if not self._drop_packet():
					self._output_queue.put((host_t, "sim-lora", line))

			if self._emit_mode in {"B", "both"}:
				line = self._make_rocket_line(flight)
				self._output_queue.put((host_t, "sim-rocket", line))

			t += dt
			self._rocket_t_ms += int(dt * 1000)
			time.sleep(dt / self._speed)

	def _drop_packet(self) -> bool:
		return self._rng.random() < (self._packet_loss_pct / 100.0)

	def _should_emit_lora(self, t: float) -> bool:
		if t - self._last_lora_emit >= 1.0:
			self._last_lora_emit = t
			return True
		return False

	def _flight_point(self, t: float) -> dict[str, float]:
		launch_t = 10.0
		boost_end_t = 12.0
		apogee_t = 18.0
		deploy_t = 18.7
		apogee_alt = 1460.0
		touchdown_t = deploy_t + apogee_alt / 6.0
		landed_t = touchdown_t + 10.0

		if t < launch_t:
			alt = self._rng.uniform(-0.3, 0.3)
			vel = 0.0
			state = 0
			fire = 0
			az = 1.0 + self._rng.uniform(-0.02, 0.02)
			amag = abs(az)
			if self._pad_knock and 5.0 <= t < 5.15:
				az = 4.0
				amag = 4.0
		elif t < boost_end_t:
			p = (t - launch_t) / (boost_end_t - launch_t)
			alt = 500.0 * p * p
			vel = 500.0 * 2.0 * p / (boost_end_t - launch_t)
			state = 1
			fire = 0
			az = self._rng.uniform(8.0, 10.0)
			amag = az
		elif t < apogee_t:
			p = (t - boost_end_t) / (apogee_t - boost_end_t)
			alt = 500.0 + (apogee_alt - 500.0) * (1.0 - (1.0 - p) ** 2)
			vel = max(0.0, 120.0 * (1.0 - p))
			state = 1
			fire = 0
			az = self._rng.uniform(-0.1, 0.2)
			amag = abs(az)
		elif t < touchdown_t:
			dt_descent = t - deploy_t
			alt = max(0.0, apogee_alt - 6.0 * dt_descent)
			vel = -6.0
			state = 2
			fire = 1
			az = 1.0 + self._rng.uniform(-0.2, 0.2)
			amag = abs(az)
		elif t < landed_t:
			alt = 0.0
			vel = 0.0
			state = 3
			fire = 1
			az = 1.0 + self._rng.uniform(-0.02, 0.02)
			amag = abs(az)
		else:
			alt = 0.0
			vel = 0.0
			state = 3
			fire = 1
			az = 1.0
			amag = 1.0

		max_m = max(0.0, min(apogee_alt, alt if state < 2 else apogee_alt))
		gx = self._rng.uniform(-1.0, 1.0)
		gy = self._rng.uniform(-1.0, 1.0)
		gz = self._rng.uniform(-5.0, 5.0)

		downrange = 320.0 * min(1.0, max(0.0, (t - deploy_t) / max(1.0, touchdown_t - deploy_t)))
		lat0 = 13.0700
		lon0 = 77.5571
		lat = lat0 + (downrange / 6371000.0) * (180.0 / math.pi)
		lon = lon0

		dist_scale = min(1.0, downrange / 400.0)
		rssi = int(-40 - 60 * dist_scale)
		snr = 10.0 - 15.0 * dist_scale
		batt = 12.4 - 0.004 * max(0.0, t - launch_t)

		return {
			"t": t,
			"state": float(state),
			"alt_m": alt,
			"vel_ms": vel,
			"max_m": max_m,
			"press_pa": 101325.0 * math.exp(-alt / 8400.0),
			"temp_c": 28.0,
			"ax": self._rng.uniform(-0.2, 0.2),
			"ay": self._rng.uniform(-0.2, 0.2),
			"az": az,
			"amag": amag,
			"gx": gx,
			"gy": gy,
			"gz": gz,
			"batt_v": batt,
			"fix": 1.0,
			"sats": 10.0,
			"lat": lat,
			"lon": lon,
			"gps_alt": 900.0 + alt,
			"fire": float(fire),
			"ok": 31.0,
			"apk": amag,
			"ierr": 0.0,
			"rssi": float(rssi),
			"snr": snr,
		}

	def _make_lora_line(self, flight: dict[str, float]) -> str:
		self._lora_cnt += 1
		values = [
			self._lora_cnt,
			int(flight["state"]),
			round(max(0.0, flight["t"] - 10.0), 2),
			round(flight["alt_m"], 2),
			round(flight["vel_ms"], 2),
			round(flight["max_m"], 2),
			round(flight["batt_v"], 2),
			int(flight["fix"]),
			int(flight["sats"]),
			f"{flight['lat']:.6f}",
			f"{flight['lon']:.6f}",
			int(flight["fire"]),
			int(flight["ok"]),
			f"{flight['ax']:.2f}",
			f"{flight['ay']:.2f}",
			f"{flight['az']:.2f}",
			f"{flight['gx']:.1f}",
			f"{flight['gy']:.1f}",
			f"{flight['gz']:.1f}",
			f"{flight['apk']:.2f}",
			int(flight["ierr"]),
			int(flight["rssi"]),
			f"{flight['snr']:.1f}",
		]
		return "CSV," + ",".join(map(str, values))

	def _make_rocket_line(self, flight: dict[str, float]) -> str:
		values = [
			"R",
			self._rocket_t_ms,
			int(flight["state"]),
			f"{flight['alt_m']:.2f}",
			f"{flight['vel_ms']:.2f}",
			f"{flight['max_m']:.2f}",
			f"{flight['press_pa']:.1f}",
			f"{flight['temp_c']:.2f}",
			f"{flight['ax']:.3f}",
			f"{flight['ay']:.3f}",
			f"{flight['az']:.3f}",
			f"{flight['amag']:.3f}",
			f"{flight['gx']:.2f}",
			f"{flight['gy']:.2f}",
			f"{flight['gz']:.2f}",
			f"{flight['batt_v']:.2f}",
			int(flight["sats"]),
			int(flight["fire"]),
			int(flight["ok"]),
		]
		return ",".join(map(str, values))

from __future__ import annotations

from dataclasses import dataclass
from math import isnan


@dataclass(slots=True)
class Event:
	name: str
	t_host_s: float
	detail: str = ""


class EventDetector:
	def __init__(self) -> None:
		self._launch_seen = False
		self._deploy_seen = False
		self._landing_seen = False

		self._module_fault_active = False
		self._battery_low_active = False
		self._imu_error_active = False
		self._gps_after_landing_active = False
		self._no_telemetry_active = False

	def detect_record(self, source: str, record: object, host_time_s: float) -> list[Event]:
		out: list[Event] = []
		state = getattr(record, "state", float("nan"))
		fire = getattr(record, "fire", float("nan"))
		ok = getattr(record, "ok", float("nan"))
		batt_v = getattr(record, "batt_v", float("nan"))
		ierr = getattr(record, "ierr", float("nan"))
		fix = getattr(record, "fix", float("nan"))

		if not isnan(state) and int(state) == 1 and not self._launch_seen:
			self._launch_seen = True
			out.append(Event(name="launch", t_host_s=host_time_s, detail="FLIGHT"))

		if source in {"lora", "rocket"} and not isnan(fire) and int(fire) != 0 and not self._deploy_seen:
			self._deploy_seen = True
			detail = "BARO" if int(fire) == 1 else "TIMER"
			out.append(Event(name="deploy", t_host_s=host_time_s, detail=detail))

		if source == "sd" and not isnan(fire) and int(fire) == 1 and not self._deploy_seen:
			self._deploy_seen = True
			out.append(Event(name="deploy", t_host_s=host_time_s, detail="SD FIRE"))

		if not isnan(state) and int(state) == 3 and not self._landing_seen:
			self._landing_seen = True
			out.append(Event(name="landing", t_host_s=host_time_s, detail="LANDED"))

		if source in {"lora", "rocket"} and not isnan(ok):
			fault = int(ok) != 31
			if fault and not self._module_fault_active:
				self._module_fault_active = True
				out.append(Event(name="alarm", t_host_s=host_time_s, detail="MODULE FAULT"))
			if not fault:
				self._module_fault_active = False

		if not isnan(batt_v):
			low = batt_v < 9.9
			if low and not self._battery_low_active:
				self._battery_low_active = True
				out.append(Event(name="alarm", t_host_s=host_time_s, detail="BATTERY LOW"))
			if not low:
				self._battery_low_active = False

		if source == "lora" and not isnan(ierr):
			has_imu_err = int(ierr) > 0
			if has_imu_err and not self._imu_error_active:
				self._imu_error_active = True
				out.append(Event(name="alarm", t_host_s=host_time_s, detail="IMU READ ERRORS"))
			if not has_imu_err:
				self._imu_error_active = False

		if self._landing_seen and not isnan(fix):
			no_fix = int(fix) == 0
			if no_fix and not self._gps_after_landing_active:
				self._gps_after_landing_active = True
				out.append(Event(name="alarm", t_host_s=host_time_s, detail="NO GPS FIX AFTER LANDING"))
			if not no_fix:
				self._gps_after_landing_active = False

		return out

	def detect_no_telemetry(self, seconds_since_packet: float, host_time_s: float) -> list[Event]:
		if seconds_since_packet > 5.0 and not self._no_telemetry_active:
			self._no_telemetry_active = True
			return [Event(name="alarm", t_host_s=host_time_s, detail=f"NO TELEMETRY {seconds_since_packet:.1f} s")]
		if seconds_since_packet <= 5.0:
			self._no_telemetry_active = False
		return []

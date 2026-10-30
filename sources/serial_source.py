from __future__ import annotations

import queue
import time

from PyQt6.QtCore import QThread

from sources.base import Source

try:
	import serial
	from serial.tools import list_ports
except ImportError:  # pragma: no cover - environment dependent
	serial = None
	list_ports = None


class SerialSource(QThread, Source):
	def __init__(
		self,
		output_queue: queue.Queue[tuple[float, str, str]],
		source_id: str = "serial",
		reconnect_interval_s: float = 2.0,
	) -> None:
		super().__init__()
		self._output_queue = output_queue
		self._source_id = source_id
		self._reconnect_interval_s = reconnect_interval_s
		self._port: str | None = None
		self._baud: int = 115200
		self._running = False

	@staticmethod
	def list_available_ports() -> list[str]:
		if list_ports is None:
			return []
		return [info.device for info in list_ports.comports()]

	@staticmethod
	def _port_score(port_info) -> int:
		description = (port_info.description or "").lower()
		hwid = (port_info.hwid or "").lower()
		vid = getattr(port_info, "vid", None)
		pid = getattr(port_info, "pid", None)

		score = 0
		if vid == 0x2E8A:
			score += 100
		if pid == 0x0005:
			score += 20
		if "pico" in description or "rp2040" in description:
			score += 40
		if "usb serial" in description:
			score += 10
		if "2e8a" in hwid:
			score += 20
		return score

	@staticmethod
	def suggest_default_port() -> str | None:
		if list_ports is None:
			return None
		ports = list(list_ports.comports())
		if not ports:
			return None

		sorted_ports = sorted(ports, key=SerialSource._port_score, reverse=True)
		best = sorted_ports[0]
		if SerialSource._port_score(best) <= 0:
			return ports[0].device
		return best.device

	@staticmethod
	def supported_baud_rates() -> list[int]:
		return [9600, 38400, 57600, 115200]

	def configure(self, port: str, baud: int) -> None:
		self._port = port
		self._baud = baud

	def start_source(self) -> None:
		self._running = True
		if not self.isRunning():
			self.start()

	def stop_source(self) -> None:
		self._running = False
		self.wait(3000)

	def run(self) -> None:
		if serial is None:
			return

		while self._running:
			if not self._port:
				time.sleep(0.2)
				continue

			try:
				with serial.Serial(self._port, self._baud, timeout=0.5) as port_handle:
					self._read_loop(port_handle)
			except Exception:
				time.sleep(self._reconnect_interval_s)

	def _read_loop(self, port_handle: serial.Serial) -> None:
		while self._running and port_handle.is_open:
			line_bytes = port_handle.readline()
			if not line_bytes:
				continue
			line = line_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
			self._output_queue.put((time.time(), self._source_id, line))

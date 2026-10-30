from __future__ import annotations

import queue
import time
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QThread

from sources.base import Source
from parsers.sd_log import SD_HEADER_LINE


class ReplaySource(QThread, Source):
	def __init__(self, output_queue: queue.Queue[tuple[float, str, str]]) -> None:
		super().__init__()
		self._output_queue = output_queue
		self._lines: list[tuple[float, str]] = []
		self._running = False
		self._paused = False
		self._speed = 1.0
		self._index = 0

	@property
	def line_count(self) -> int:
		return len(self._lines)

	def load(self, path: str | Path) -> None:
		source_path = Path(path)
		self._lines.clear()
		self._index = 0

		if source_path.is_dir():
			source_path = source_path / "raw.log"

		rows = source_path.read_text(encoding="utf-8", errors="replace").splitlines()
		if self._looks_like_raw_log(rows):
			self._load_raw_log_rows(rows)
		elif self._looks_like_sd_csv(rows):
			self._load_sd_csv_rows(rows)
		else:
			raise ValueError("Unsupported replay file format")

	def set_speed(self, speed: float) -> None:
		self._speed = max(0.1, speed)

	def pause(self, paused: bool) -> None:
		self._paused = paused

	def seek(self, index: int) -> None:
		self._index = max(0, min(index, len(self._lines) - 1))

	def start_source(self) -> None:
		self._running = True
		if not self.isRunning():
			self.start()

	def stop_source(self) -> None:
		self._running = False
		self.wait(3000)

	def run(self) -> None:
		while self._running and self._index < len(self._lines):
			if self._paused:
				time.sleep(0.05)
				continue

			t_ref, line = self._lines[self._index]
			self._output_queue.put((time.time(), "replay", line))

			self._index += 1
			if self._index >= len(self._lines):
				break
			t_next, _ = self._lines[self._index]
			delta = max(0.0, (t_next - t_ref) / self._speed)
			time.sleep(min(delta, 0.5))

	def _looks_like_raw_log(self, rows: list[str]) -> bool:
		for line in rows:
			text = line.strip()
			if not text:
				continue
			if "\t" not in text:
				return False
			host_iso = text.split("\t", 1)[0]
			try:
				datetime.fromisoformat(host_iso)
			except ValueError:
				return False
			return True
		return False

	def _looks_like_sd_csv(self, rows: list[str]) -> bool:
		if not rows:
			return False
		return rows[0].strip() == SD_HEADER_LINE

	def _load_raw_log_rows(self, rows: list[str]) -> None:
		for line in rows:
			if "\t" not in line:
				continue
			host_iso, payload = line.split("\t", 1)
			ts = datetime.fromisoformat(host_iso).timestamp()
			self._lines.append((ts, payload))

	def _load_sd_csv_rows(self, rows: list[str]) -> None:
		if not rows:
			return
		if rows[0].strip() != SD_HEADER_LINE:
			raise ValueError("SD log missing expected header")
		self._lines.append((0.0, SD_HEADER_LINE))

		first_t_ms = None
		for row in rows[1:]:
			cols = row.split(",")
			if len(cols) < 1:
				continue
			t_ms = float(cols[0])
			if first_t_ms is None:
				first_t_ms = t_ms
			rel_s = (t_ms - first_t_ms) / 1000.0
			self._lines.append((rel_s, row))

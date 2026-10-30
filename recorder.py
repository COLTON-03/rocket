from __future__ import annotations

import csv
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path


class SessionRecorder:
	def __init__(self, root: Path | None = None) -> None:
		self._root = root or Path("sessions")
		self._session_dir: Path | None = None
		self._raw_file = None
		self._parsed_writers: dict[str, tuple[object, csv.DictWriter]] = {}
		self._events_file = None
		self._events_writer: csv.DictWriter | None = None

	@property
	def session_dir(self) -> Path | None:
		return self._session_dir

	def start(self) -> Path:
		stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		self._session_dir = self._root / stamp
		self._session_dir.mkdir(parents=True, exist_ok=True)

		self._raw_file = (self._session_dir / "raw.log").open("w", encoding="utf-8", newline="")
		self._events_file = (self._session_dir / "events.csv").open("w", encoding="utf-8", newline="")
		self._events_writer = csv.DictWriter(self._events_file, fieldnames=["host_iso", "name", "detail"])
		self._events_writer.writeheader()
		return self._session_dir

	def stop(self) -> None:
		if self._raw_file:
			self._raw_file.close()
			self._raw_file = None
		for handle, _ in self._parsed_writers.values():
			handle.close()
		self._parsed_writers.clear()
		if self._events_file:
			self._events_file.close()
			self._events_file = None
		self._events_writer = None
		self._session_dir = None

	def record_raw_line(self, host_time_iso: str, line: str) -> None:
		if not self._raw_file:
			return
		self._raw_file.write(f"{host_time_iso}\t{line}\n")

	def record_parsed(self, source: str, record: object) -> None:
		if not self._session_dir or not is_dataclass(record):
			return

		filename = f"{source}.csv"
		if source not in self._parsed_writers:
			payload = asdict(record)
			handle = (self._session_dir / filename).open("w", encoding="utf-8", newline="")
			writer = csv.DictWriter(handle, fieldnames=list(payload.keys()))
			writer.writeheader()
			self._parsed_writers[source] = (handle, writer)

		payload = asdict(record)
		_, writer = self._parsed_writers[source]
		writer.writerow(payload)

	def record_event(self, host_time_iso: str, name: str, detail: str) -> None:
		if self._events_writer is None:
			return
		self._events_writer.writerow({"host_iso": host_time_iso, "name": name, "detail": detail})

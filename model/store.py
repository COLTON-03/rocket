from __future__ import annotations

from dataclasses import asdict
from typing import Any

import numpy as np

from model.buffers import RingBuffer
from parsers.records import GenericRecord


class ChannelStore:
	def __init__(self, capacity: int = 12000) -> None:
		self._capacity = capacity
		self._buffers: dict[str, RingBuffer] = {}
		self._channel_names: dict[str, list[str]] = {}
		self._start_time_s: float | None = None

	def clear(self) -> None:
		self._buffers.clear()
		self._channel_names.clear()
		self._start_time_s = None

	def append_record(self, stream: str, host_time_s: float, record: Any) -> None:
		if isinstance(record, GenericRecord):
			payload = record.values
		else:
			payload = asdict(record)
		self.append_values(stream=stream, host_time_s=host_time_s, values=payload)

	def append_values(self, stream: str, host_time_s: float, values: dict[str, float]) -> None:
		if self._start_time_s is None:
			self._start_time_s = host_time_s
		rel_time_s = host_time_s - self._start_time_s

		channel_names = ["host_t_s", *values.keys()]
		row = np.array([rel_time_s, *values.values()], dtype=np.float64)

		if stream not in self._buffers:
			self._buffers[stream] = RingBuffer(self._capacity, len(channel_names))
			self._channel_names[stream] = channel_names

		buffer = self._buffers[stream]
		expected = self._channel_names[stream]
		if channel_names != expected:
			raise ValueError(f"Channel schema changed for stream {stream}")
		buffer.append(row)

	def get_stream_data(self, stream: str) -> tuple[list[str], np.ndarray]:
		if stream not in self._buffers:
			return [], np.empty((0, 0), dtype=np.float64)
		return self._channel_names[stream], self._buffers[stream].view()

	def stream_names(self) -> list[str]:
		return sorted(self._buffers.keys())

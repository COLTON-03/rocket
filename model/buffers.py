from __future__ import annotations

import numpy as np


class RingBuffer:
	def __init__(self, capacity: int, channels: int) -> None:
		if capacity <= 0:
			raise ValueError("capacity must be > 0")
		if channels <= 0:
			raise ValueError("channels must be > 0")
		self.capacity = capacity
		self.channels = channels
		self._data = np.full((capacity, channels), np.nan, dtype=np.float64)
		self._size = 0
		self._head = 0

	@property
	def size(self) -> int:
		return self._size

	def append(self, values: np.ndarray | list[float]) -> None:
		arr = np.asarray(values, dtype=np.float64)
		if arr.shape != (self.channels,):
			raise ValueError(f"Expected shape {(self.channels,)}, got {arr.shape}")
		self._data[self._head] = arr
		self._head = (self._head + 1) % self.capacity
		self._size = min(self._size + 1, self.capacity)

	def view(self) -> np.ndarray:
		if self._size == 0:
			return np.empty((0, self.channels), dtype=np.float64)
		if self._size < self.capacity:
			return self._data[: self._size].copy()
		return np.vstack((self._data[self._head :], self._data[: self._head]))

	def clear(self) -> None:
		self._data.fill(np.nan)
		self._size = 0
		self._head = 0

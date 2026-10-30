from __future__ import annotations

class Source:
	def start_source(self) -> None:
		raise NotImplementedError

	def stop_source(self) -> None:
		raise NotImplementedError

from __future__ import annotations

import re

from parsers.records import GenericRecord

DELIMITER_REGEX = re.compile(r"[,;\t ]+")


def _split_tokens(line: str) -> list[str]:
	return [token for token in DELIMITER_REGEX.split(line.strip()) if token]


def _is_float(token: str) -> bool:
	try:
		float(token)
		return True
	except ValueError:
		return False


class GenericParser:
	def __init__(self) -> None:
		self._header: list[str] | None = None

	def parse_line(self, line: str) -> GenericRecord | None:
		tokens = _split_tokens(line)
		if not tokens:
			return None

		if self._maybe_capture_header(tokens):
			return None

		labels = self._parse_label_value_tokens(tokens)
		if labels is not None:
			return GenericRecord(values=labels)

		numeric_values = self._parse_numeric_tokens(tokens)
		keys = self._build_keys(len(numeric_values))
		return GenericRecord(values=dict(zip(keys, numeric_values, strict=True)))

	def _maybe_capture_header(self, tokens: list[str]) -> bool:
		if self._header is not None:
			return False
		if any(":" in token for token in tokens):
			return False
		if all(not _is_float(token) for token in tokens):
			self._header = tokens
			return True
		return False

	def _parse_label_value_tokens(self, tokens: list[str]) -> dict[str, float] | None:
		if not all(":" in token for token in tokens):
			return None
		values: dict[str, float] = {}
		for token in tokens:
			key, value_text = token.split(":", 1)
			if not key:
				raise ValueError("Generic label token has empty key")
			try:
				values[key] = float(value_text)
			except ValueError as exc:
				raise ValueError(f"Generic label token is non-numeric: {token!r}") from exc
		return values

	def _parse_numeric_tokens(self, tokens: list[str]) -> list[float]:
		values: list[float] = []
		for token in tokens:
			try:
				values.append(float(token))
			except ValueError as exc:
				raise ValueError(f"Generic token is non-numeric: {token!r}") from exc
		return values

	def _build_keys(self, count: int) -> list[str]:
		if self._header is not None and len(self._header) == count:
			return self._header
		return [f"ch{index}" for index in range(count)]

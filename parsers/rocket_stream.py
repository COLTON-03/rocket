from __future__ import annotations

import math

from parsers.records import RocketRecord

ROCKET_PREFIX = "R,"


def _to_float(value: str) -> float:
	text = value.strip()
	if text == "":
		return math.nan
	try:
		return float(text)
	except ValueError as exc:
		raise ValueError(f"Non-numeric field: {value!r}") from exc


def parse_rocket_line(line: str) -> RocketRecord | None:
	text = line.strip()
	if not text.startswith(ROCKET_PREFIX):
		return None

	fields = text.split(",")
	if len(fields) != 19:
		raise ValueError("Rocket line must have 18 fields after R")

	numbers = [_to_float(field) for field in fields[1:]]
	return RocketRecord(
		t_ms=numbers[0],
		state=numbers[1],
		alt_m=numbers[2],
		vel_ms=numbers[3],
		max_m=numbers[4],
		press_pa=numbers[5],
		temp_c=numbers[6],
		ax=numbers[7],
		ay=numbers[8],
		az=numbers[9],
		amag=numbers[10],
		gx=numbers[11],
		gy=numbers[12],
		gz=numbers[13],
		batt_v=numbers[14],
		sats=numbers[15],
		fire=numbers[16],
		ok=numbers[17],
	)

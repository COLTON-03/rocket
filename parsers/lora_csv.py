from __future__ import annotations

import math

from parsers.records import LoraRecord

LORA_HEADER = [
	"cnt",
	"state",
	"t_s",
	"alt_m",
	"vel_ms",
	"max_m",
	"batt_v",
	"fix",
	"sats",
	"lat",
	"lon",
	"fire",
	"ok",
	"ax",
	"ay",
	"az",
	"gx",
	"gy",
	"gz",
	"apk",
	"ierr",
	"rssi",
	"snr",
]


def is_lora_header_line(line: str) -> bool:
	return line.strip().startswith("CSV,cnt")


def _to_float(value: str) -> float:
	text = value.strip()
	if text == "":
		return math.nan
	try:
		return float(text)
	except ValueError as exc:
		raise ValueError(f"Non-numeric field: {value!r}") from exc


def _normalize_fields(fields: list[str]) -> list[str]:
	if len(fields) < 15:
		raise ValueError("Too few fields")

	if len(fields) == 15:
		base = fields[:13]
		middle = [""] * 8
		tail = fields[13:15]
		return base + middle + tail

	if len(fields) < 23:
		return fields + [""] * (23 - len(fields))

	return fields[:23]


def parse_lora_csv_line(line: str) -> LoraRecord | None:
	text = line.strip()
	if not text.startswith("CSV,"):
		return None
	if is_lora_header_line(text):
		return None

	fields = text.split(",")[1:]
	normalized = _normalize_fields(fields)
	numbers = [_to_float(value) for value in normalized]

	return LoraRecord(
		cnt=numbers[0],
		state=numbers[1],
		t_s=numbers[2],
		alt_m=numbers[3],
		vel_ms=numbers[4],
		max_m=numbers[5],
		batt_v=numbers[6],
		fix=numbers[7],
		sats=numbers[8],
		lat=numbers[9],
		lon=numbers[10],
		fire=numbers[11],
		ok=numbers[12],
		ax=numbers[13],
		ay=numbers[14],
		az=numbers[15],
		gx=numbers[16],
		gy=numbers[17],
		gz=numbers[18],
		apk=numbers[19],
		ierr=numbers[20],
		rssi=numbers[21],
		snr=numbers[22],
	)

from __future__ import annotations

import math

from parsers.records import SdRecord

SD_HEADER = [
	"t_ms",
	"state",
	"alt_m",
	"vel_ms",
	"max_m",
	"press_pa",
	"temp_c",
	"ax",
	"ay",
	"az",
	"amag",
	"gx",
	"gy",
	"gz",
	"batt_v",
	"fix",
	"sats",
	"lat",
	"lon",
	"gps_alt",
	"fire",
]
SD_HEADER_LINE = ",".join(SD_HEADER)


def is_sd_header_line(line: str) -> bool:
	return line.strip() == SD_HEADER_LINE


def _to_float(value: str) -> float:
	text = value.strip()
	if text == "":
		return math.nan
	try:
		return float(text)
	except ValueError as exc:
		raise ValueError(f"Non-numeric field: {value!r}") from exc


def parse_sd_row(line: str) -> SdRecord:
	fields = line.strip().split(",")
	if len(fields) != len(SD_HEADER):
		raise ValueError("SD row field count mismatch")
	numbers = [_to_float(field) for field in fields]
	return SdRecord(
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
		fix=numbers[15],
		sats=numbers[16],
		lat=numbers[17],
		lon=numbers[18],
		gps_alt=numbers[19],
		fire=numbers[20],
	)

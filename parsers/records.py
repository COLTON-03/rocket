from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class LoraRecord:
	cnt: float
	state: float
	t_s: float
	alt_m: float
	vel_ms: float
	max_m: float
	batt_v: float
	fix: float
	sats: float
	lat: float
	lon: float
	fire: float
	ok: float
	ax: float
	ay: float
	az: float
	gx: float
	gy: float
	gz: float
	apk: float
	ierr: float
	rssi: float
	snr: float


@dataclass(slots=True)
class RocketRecord:
	t_ms: float
	state: float
	alt_m: float
	vel_ms: float
	max_m: float
	press_pa: float
	temp_c: float
	ax: float
	ay: float
	az: float
	amag: float
	gx: float
	gy: float
	gz: float
	batt_v: float
	sats: float
	fire: float
	ok: float


@dataclass(slots=True)
class SdRecord:
	t_ms: float
	state: float
	alt_m: float
	vel_ms: float
	max_m: float
	press_pa: float
	temp_c: float
	ax: float
	ay: float
	az: float
	amag: float
	gx: float
	gy: float
	gz: float
	batt_v: float
	fix: float
	sats: float
	lat: float
	lon: float
	gps_alt: float
	fire: float


@dataclass(slots=True)
class GenericRecord:
	values: dict[str, float]


@dataclass(slots=True)
class LoraRcvRecord:
	addr: float
	payload_len: float
	packet_no: float
	rssi: float
	snr: float


@dataclass(slots=True)
class DispatchResult:
	source: str
	kind: str
	record: Any | None = None
	header: list[str] | None = None
	error: str | None = None

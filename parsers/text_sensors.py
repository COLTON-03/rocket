from __future__ import annotations

import re

from parsers.records import GenericRecord

TEMP_REGEX = re.compile(r"^Temperature\s*=\s*(?P<temp>-?\d+(?:\.\d+)?)\s*\*?C\s*$", re.IGNORECASE)
PRESS_REGEX = re.compile(r"^Pressure\s*=\s*(?P<press>-?\d+(?:\.\d+)?)\s*hPa\s*$", re.IGNORECASE)
ALT_REGEX = re.compile(r"^Approx\s+Altitude\s*=\s*(?P<alt>-?\d+(?:\.\d+)?)\s*m\s*$", re.IGNORECASE)
GPS_REGEX = re.compile(
    r"^Fix:\s*(?P<fix>\d+)\s*\|\s*Sats:\s*(?P<sats>\d+)\s*\|\s*"
    r"Lat:\s*(?P<lat>\d+(?:\.\d+)?)\s*(?P<lat_hemi>[NS])\s*\|\s*"
    r"Lon:\s*(?P<lon>\d+(?:\.\d+)?)\s*(?P<lon_hemi>[EW])\s*\|\s*"
    r"Alt:\s*(?P<alt>-?\d+(?:\.\d+)?)\s*m\s*$",
    re.IGNORECASE,
)
MPU_REGEX = re.compile(
    r"^Acc\s+g:\s*(?P<ax>-?\d+(?:\.\d+)?)\s+(?P<ay>-?\d+(?:\.\d+)?)\s+(?P<az>-?\d+(?:\.\d+)?)\s*\|\s*"
    r"Gyro\s+dps:\s*(?P<gx>-?\d+(?:\.\d+)?)\s+(?P<gy>-?\d+(?:\.\d+)?)\s+(?P<gz>-?\d+(?:\.\d+)?)\s*\|\s*"
    r"Temp:\s*(?P<temp>-?\d+(?:\.\d+)?)\s*C\s*$",
    re.IGNORECASE,
)


def _ddmm_to_decimal(value: float, is_lat: bool, hemi: str) -> float:
    degrees_width = 2 if is_lat else 3
    value_text = f"{value:.5f}"
    integer_text, frac = value_text.split(".")
    deg = float(integer_text[:degrees_width])
    minutes = float(integer_text[degrees_width:] + "." + frac)
    decimal = deg + minutes / 60.0
    if hemi.upper() in {"S", "W"}:
        decimal *= -1.0
    return decimal


class TextSensorParser:
    def __init__(self) -> None:
        self._pending_temp_c: float | None = None
        self._pending_press_hpa: float | None = None

    def parse_line(self, line: str) -> tuple[str, GenericRecord] | None:
        text = line.strip()
        if not text:
            return None

        temp_match = TEMP_REGEX.match(text)
        if temp_match:
            self._pending_temp_c = float(temp_match.group("temp"))
            return None

        press_match = PRESS_REGEX.match(text)
        if press_match:
            self._pending_press_hpa = float(press_match.group("press"))
            return None

        alt_match = ALT_REGEX.match(text)
        if alt_match:
            values: dict[str, float] = {
                "approx_alt_m": float(alt_match.group("alt")),
            }
            if self._pending_temp_c is not None:
                values["temp_c"] = self._pending_temp_c
            if self._pending_press_hpa is not None:
                values["press_hpa"] = self._pending_press_hpa
            return "sensor_bmp", GenericRecord(values=values)

        gps_match = GPS_REGEX.match(text)
        if gps_match:
            lat_raw = float(gps_match.group("lat"))
            lon_raw = float(gps_match.group("lon"))
            lat = _ddmm_to_decimal(lat_raw, is_lat=True, hemi=gps_match.group("lat_hemi"))
            lon = _ddmm_to_decimal(lon_raw, is_lat=False, hemi=gps_match.group("lon_hemi"))
            values = {
                "fix": float(gps_match.group("fix")),
                "sats": float(gps_match.group("sats")),
                "lat": lat,
                "lon": lon,
                "gps_alt": float(gps_match.group("alt")),
            }
            return "sensor_gps", GenericRecord(values=values)

        mpu_match = MPU_REGEX.match(text)
        if mpu_match:
            values = {
                "ax": float(mpu_match.group("ax")),
                "ay": float(mpu_match.group("ay")),
                "az": float(mpu_match.group("az")),
                "gx": float(mpu_match.group("gx")),
                "gy": float(mpu_match.group("gy")),
                "gz": float(mpu_match.group("gz")),
                "temp_c": float(mpu_match.group("temp")),
            }
            return "sensor_mpu", GenericRecord(values=values)

        return None

    @staticmethod
    def is_sensor_text_line(line: str) -> bool:
        text = line.strip()
        return (
            TEMP_REGEX.match(text) is not None
            or PRESS_REGEX.match(text) is not None
            or ALT_REGEX.match(text) is not None
            or GPS_REGEX.match(text) is not None
            or MPU_REGEX.match(text) is not None
            or text.startswith("BMP280 Test")
            or text.startswith("MPY:")
            or text.startswith("WHO_AM_I")
        )

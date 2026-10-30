from __future__ import annotations

from parsers.records import GenericRecord

TEAM_HEADER = [
    "TEAM_ID",
    "TIME",
    "PACKET_COUNT",
    "ALTITUDE",
    "PRESSURE",
    "TEMP",
    "VOLTAGE",
    "GNSS_TIME",
    "GNSS_LAT",
    "GNSS_LON",
    "GNSS_ALT",
    "GNSS_SATS",
    "ACC_X",
    "ACC_Y",
    "ACC_Z",
    "ROLL",
    "PITCH",
    "GYRO_X",
    "GYRO_Y",
    "GYRO_Z",
    "FSW_STATE",
]


class TeamCsvParser:
    def __init__(self) -> None:
        self._active = False

    def parse_line(self, line: str) -> GenericRecord | None:
        text = line.strip()
        if text == ",".join(TEAM_HEADER):
            self._active = True
            return None

        if not self._active and not text.startswith("2026"):
            return None

        fields = [field.strip() for field in text.split(",")]
        if len(fields) != len(TEAM_HEADER):
            return None

        team_id = fields[0]
        values: dict[str, float] = {}
        for index, name in enumerate(TEAM_HEADER[1:], start=1):
            try:
                values[name.lower()] = float(fields[index])
            except ValueError as exc:
                raise ValueError(f"Invalid TEAM CSV field {name}: {fields[index]!r}") from exc

        values["t_s"] = values["time"]
        values["cnt"] = values["packet_count"]
        values["alt_m"] = values["altitude"]
        values["press_pa"] = values["pressure"]
        values["temp_c"] = values["temp"]
        values["batt_v"] = values["voltage"]
        values["lat"] = values["gnss_lat"]
        values["lon"] = values["gnss_lon"]
        values["gps_alt"] = values["gnss_alt"]
        values["sats"] = values["gnss_sats"]
        values["ax"] = values["acc_x"]
        values["ay"] = values["acc_y"]
        values["az"] = values["acc_z"]
        values["gx"] = values["gyro_x"]
        values["gy"] = values["gyro_y"]
        values["gz"] = values["gyro_z"]
        values["state"] = values["fsw_state"]

        values["team_id_code"] = float(abs(hash(team_id)) % 10000)
        return GenericRecord(values=values)

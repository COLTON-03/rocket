from __future__ import annotations

from parsers.generic import GenericParser
from parsers.lora_csv import LORA_HEADER, is_lora_header_line, parse_lora_csv_line
from parsers.lora_rcv import parse_lora_rcv_line
from parsers.records import DispatchResult
from parsers.rocket_stream import parse_rocket_line
from parsers.sd_log import SD_HEADER, is_sd_header_line, parse_sd_row
from parsers.team_csv import TeamCsvParser
from parsers.text_sensors import TextSensorParser


class ParserDispatch:
	def __init__(self) -> None:
		self._generic = GenericParser()
		self._team_csv = TeamCsvParser()
		self._text = TextSensorParser()
		self._sd_mode = False

	def parse_line(self, line: str) -> DispatchResult:
		text = line.strip()
		if not text:
			return DispatchResult(source="unknown", kind="skip")

		try:
			if text.startswith("CSV,"):
				if is_lora_header_line(text):
					return DispatchResult(source="lora", kind="header", header=LORA_HEADER)
				record = parse_lora_csv_line(text)
				if record is None:
					return DispatchResult(source="lora", kind="skip")
				return DispatchResult(source="lora", kind="data", record=record)

			if text.startswith("R,"):
				record = parse_rocket_line(text)
				if record is None:
					return DispatchResult(source="rocket", kind="skip")
				return DispatchResult(source="rocket", kind="data", record=record)

			if text.startswith("+RCV="):
				record = parse_lora_rcv_line(text)
				if record is None:
					return DispatchResult(source="lora_rcv", kind="skip")
				return DispatchResult(source="lora_rcv", kind="data", record=record)

			if is_sd_header_line(text):
				self._sd_mode = True
				return DispatchResult(source="sd", kind="header", header=SD_HEADER)

			if self._sd_mode:
				record = parse_sd_row(text)
				return DispatchResult(source="sd", kind="data", record=record)

			parsed_text = self._text.parse_line(text)
			if parsed_text is not None:
				source, record = parsed_text
				return DispatchResult(source=source, kind="data", record=record)
			if self._text.is_sensor_text_line(text):
				return DispatchResult(source="sensor_text", kind="skip")

			team_record = self._team_csv.parse_line(text)
			if team_record is not None:
				return DispatchResult(source="team_csv", kind="data", record=team_record)
			if text == "TEAM_ID,TIME,PACKET_COUNT,ALTITUDE,PRESSURE,TEMP,VOLTAGE,GNSS_TIME,GNSS_LAT,GNSS_LON,GNSS_ALT,GNSS_SATS,ACC_X,ACC_Y,ACC_Z,ROLL,PITCH,GYRO_X,GYRO_Y,GYRO_Z,FSW_STATE":
				return DispatchResult(source="team_csv", kind="header")

			record = self._generic.parse_line(text)
			if record is None:
				return DispatchResult(source="generic", kind="header")
			return DispatchResult(source="generic", kind="data", record=record)
		except ValueError as exc:
			return DispatchResult(source="unknown", kind="bad", error=str(exc))

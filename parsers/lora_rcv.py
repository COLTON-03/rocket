from __future__ import annotations

import re

from parsers.records import LoraRcvRecord

RCV_REGEX = re.compile(
    r"^\+RCV=(?P<addr>-?\d+),(?P<len>-?\d+),(?P<payload>.*?),(?P<rssi>-?\d+),(?P<snr>-?\d+)\s*$"
)
PACKET_NO_REGEX = re.compile(r"#(?P<num>\d+)")


def parse_lora_rcv_line(line: str) -> LoraRcvRecord | None:
    match = RCV_REGEX.match(line.strip())
    if not match:
        return None

    payload = match.group("payload")
    packet_no = float("nan")
    packet_match = PACKET_NO_REGEX.search(payload)
    if packet_match:
        packet_no = float(packet_match.group("num"))

    return LoraRcvRecord(
        addr=float(match.group("addr")),
        payload_len=float(match.group("len")),
        packet_no=packet_no,
        rssi=float(match.group("rssi")),
        snr=float(match.group("snr")),
    )

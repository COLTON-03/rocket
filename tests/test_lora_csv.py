import math

import pytest

from parsers.dispatch import ParserDispatch
from parsers.lora_csv import is_lora_header_line, parse_lora_csv_line


def test_lora_21_field_line() -> None:
    line = "CSV,12,1,3.2,152.3,45.1,152.3,11.90,1,9,13.069977,77.557097,0,31,0.12,-0.05,8.73,4,-12,310,9.84,0,-71,9"
    record = parse_lora_csv_line(line)
    assert record is not None
    assert record.cnt == 12
    assert record.state == 1
    assert record.alt_m == pytest.approx(152.3)
    assert record.apk == pytest.approx(9.84)
    assert record.rssi == -71
    assert record.snr == 9


def test_lora_13_field_padded_line() -> None:
    line = "CSV,12,0,0.0,0.3,0.0,0.3,12.41,0,0,0.000000,0.000000,0,27,,,,,,,,,-45,11"
    record = parse_lora_csv_line(line)
    assert record is not None
    assert record.cnt == 12
    assert math.isnan(record.ax)
    assert math.isnan(record.gx)
    assert math.isnan(record.apk)
    assert record.rssi == -45
    assert record.snr == 11


def test_lora_13_field_unpadded_line() -> None:
    line = "CSV,44,0,0.0,0.2,0.0,0.3,12.30,0,0,0.0,0.0,0,31,-60,12"
    record = parse_lora_csv_line(line)
    assert record is not None
    assert record.cnt == 44
    assert math.isnan(record.ax)
    assert math.isnan(record.gy)
    assert record.rssi == -60
    assert record.snr == 12


def test_lora_header_line() -> None:
    line = "CSV,cnt,state,t_s,alt_m,vel_ms,max_m,batt_v,fix,sats,lat,lon,fire,ok,ax,ay,az,gx,gy,gz,apk,ierr,rssi,snr"
    assert is_lora_header_line(line)
    assert parse_lora_csv_line(line) is None


def test_lora_bad_numeric_field() -> None:
    line = "CSV,12,1,3.2,152.3,45.1,152.3,11.90,1,9,13.069977,oops,0,31,0.12,-0.05,8.73,4,-12,310,9.84,0,-71,9"
    with pytest.raises(ValueError):
        parse_lora_csv_line(line)


def test_lora_empty_field_to_nan() -> None:
    line = "CSV,12,1,,152.3,45.1,152.3,11.90,1,9,13.069977,77.557097,0,31,0.12,-0.05,8.73,4,-12,310,9.84,0,-71,9"
    record = parse_lora_csv_line(line)
    assert record is not None
    assert math.isnan(record.t_s)


def test_lora_dispatch_marks_bad_line() -> None:
    dispatch = ParserDispatch()
    line = "CSV,12,1,3.2,152.3,45.1,152.3,11.90,1,9,13.069977,BAD,0,31,0.12,-0.05,8.73,4,-12,310,9.84,0,-71,9"
    result = dispatch.parse_line(line)
    assert result.kind == "bad"


def test_lora_rcv_line_parsed_for_live_rssi_snr() -> None:
    dispatch = ParserDispatch()
    line = "+RCV=1,9,HELLO #75,-92,7"
    result = dispatch.parse_line(line)
    assert result.kind == "data"
    assert result.source == "lora_rcv"
    assert result.record is not None
    assert result.record.packet_no == 75
    assert result.record.rssi == -92
    assert result.record.snr == 7


def test_bmp_text_triplet_parsed() -> None:
    dispatch = ParserDispatch()
    assert dispatch.parse_line("Temperature = 25.59 *C").kind in {"header", "skip"}
    assert dispatch.parse_line("Pressure = 899.74 hPa").kind in {"header", "skip"}
    result = dispatch.parse_line("Approx Altitude = 991.06 m")
    assert result.kind == "data"
    assert result.source == "sensor_bmp"
    assert result.record is not None
    assert result.record.values["temp_c"] == pytest.approx(25.59)
    assert result.record.values["press_hpa"] == pytest.approx(899.74)
    assert result.record.values["approx_alt_m"] == pytest.approx(991.06)


def test_gps_text_line_parsed() -> None:
    dispatch = ParserDispatch()
    line = "Fix: 1 | Sats: 10 | Lat: 1304.19915 N | Lon: 07733.42386 E | Alt: 932.9 m"
    result = dispatch.parse_line(line)
    assert result.kind == "data"
    assert result.source == "sensor_gps"
    assert result.record is not None
    assert result.record.values["fix"] == 1
    assert result.record.values["sats"] == 10
    assert result.record.values["gps_alt"] == pytest.approx(932.9)


def test_mpu_text_line_parsed() -> None:
    dispatch = ParserDispatch()
    line = "Acc g: -0.12  0.04  1.00 | Gyro dps:   -0.8    2.1   -0.1 | Temp: 44.0 C"
    result = dispatch.parse_line(line)
    assert result.kind == "data"
    assert result.source == "sensor_mpu"
    assert result.record is not None
    assert result.record.values["ax"] == pytest.approx(-0.12)
    assert result.record.values["gy"] == pytest.approx(2.1)
    assert result.record.values["temp_c"] == pytest.approx(44.0)

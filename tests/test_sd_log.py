import pytest

from parsers.dispatch import ParserDispatch
from parsers.sd_log import SD_HEADER_LINE, is_sd_header_line, parse_sd_row


def test_sd_header_detection() -> None:
    assert is_sd_header_line(SD_HEADER_LINE)


def test_sd_row_parse() -> None:
    row = "183422,1,120.4,38.7,121.0,91085.2,28.41,0.012,-0.004,1.002,1.002,0.4,-0.2,0.1,12.38,1,9,13.069977,77.557097,890.4,0"
    record = parse_sd_row(row)
    assert record.t_ms == 183422
    assert record.state == 1
    assert record.alt_m == pytest.approx(120.4)
    assert record.gps_alt == pytest.approx(890.4)


def test_dispatch_sd_header_then_row() -> None:
    dispatch = ParserDispatch()
    header_result = dispatch.parse_line(SD_HEADER_LINE)
    assert header_result.kind == "header"
    assert header_result.source == "sd"

    row = "183422,1,120.4,38.7,121.0,91085.2,28.41,0.012,-0.004,1.002,1.002,0.4,-0.2,0.1,12.38,1,9,13.069977,77.557097,890.4,0"
    row_result = dispatch.parse_line(row)
    assert row_result.kind == "data"
    assert row_result.source == "sd"

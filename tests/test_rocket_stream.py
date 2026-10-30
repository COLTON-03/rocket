import pytest

from parsers.dispatch import ParserDispatch
from parsers.rocket_stream import parse_rocket_line


def test_parse_r_line() -> None:
    line = "R,183422,0,0.12,0.03,0.00,91085.2,28.41,0.012,-0.004,1.002,1.002,0.4,-0.2,0.1,12.38,9,0,31"
    record = parse_rocket_line(line)
    assert record is not None
    assert record.t_ms == 183422
    assert record.press_pa == pytest.approx(91085.2)
    assert record.batt_v == pytest.approx(12.38)
    assert record.ok == 31


def test_parse_invalid_rocket_line_raises() -> None:
    with pytest.raises(ValueError):
        parse_rocket_line("R,1,2,3")


def test_dispatch_r_line() -> None:
    dispatch = ParserDispatch()
    line = "R,183422,0,0.12,0.03,0.00,91085.2,28.41,0.012,-0.004,1.002,1.002,0.4,-0.2,0.1,12.38,9,0,31"
    result = dispatch.parse_line(line)
    assert result.source == "rocket"
    assert result.kind == "data"

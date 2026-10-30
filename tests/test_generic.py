import pytest

from parsers.generic import GenericParser


def test_generic_comma_numbers() -> None:
    parser = GenericParser()
    record = parser.parse_line("1,2,3")
    assert record is not None
    assert record.values["ch0"] == 1
    assert record.values["ch2"] == 3


def test_generic_space_numbers() -> None:
    parser = GenericParser()
    record = parser.parse_line("1 2 3")
    assert record is not None
    assert record.values["ch1"] == 2


def test_generic_label_value() -> None:
    parser = GenericParser()
    record = parser.parse_line("alt:123.4 vel:-5.2 batt:11.8")
    assert record is not None
    assert record.values["alt"] == pytest.approx(123.4)
    assert record.values["vel"] == pytest.approx(-5.2)


def test_generic_header_then_values() -> None:
    parser = GenericParser()
    assert parser.parse_line("a,b,c") is None
    record = parser.parse_line("4,5,6")
    assert record is not None
    assert record.values["a"] == 4
    assert record.values["c"] == 6

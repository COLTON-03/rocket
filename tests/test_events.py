from dataclasses import dataclass

from model.events import EventDetector


@dataclass
class FakeRecord:
    state: float
    fire: float
    ok: float
    batt_v: float
    ierr: float
    fix: float


def test_launch_deploy_landing_detected_once() -> None:
    detector = EventDetector()
    launch = detector.detect_record("lora", FakeRecord(1, 0, 31, 12.0, 0, 1), 1.0)
    deploy = detector.detect_record("lora", FakeRecord(2, 1, 31, 12.0, 0, 1), 2.0)
    landing = detector.detect_record("lora", FakeRecord(3, 1, 31, 12.0, 0, 1), 3.0)

    assert any(e.name == "launch" for e in launch)
    assert any(e.name == "deploy" for e in deploy)
    assert any(e.name == "landing" for e in landing)


def test_alarm_conditions_and_no_telemetry() -> None:
    detector = EventDetector()
    alarms = detector.detect_record("lora", FakeRecord(0, 0, 15, 9.5, 1, 0), 1.0)
    details = {e.detail for e in alarms if e.name == "alarm"}
    assert "MODULE FAULT" in details
    assert "BATTERY LOW" in details
    assert "IMU READ ERRORS" in details

    no_telemetry = detector.detect_no_telemetry(6.0, 2.0)
    assert len(no_telemetry) == 1
    assert "NO TELEMETRY" in no_telemetry[0].detail

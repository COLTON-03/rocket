from __future__ import annotations

import queue
from datetime import datetime

import numpy as np

from model.store import ChannelStore
from parsers.dispatch import ParserDispatch
from recorder import SessionRecorder
from sources.replay_source import ReplaySource
from sources.sim_source import SimSource


def test_record_and_replay_produce_identical_buffers(tmp_path) -> None:
    dispatcher_live = ParserDispatch()
    store_live = ChannelStore(capacity=2000)
    recorder = SessionRecorder(root=tmp_path)
    session_dir = recorder.start()

    sim = SimSource(queue.Queue(), emit_mode="both", speed=1.0)
    timestamps = [1730000000.0 + i * 0.1 for i in range(60)]

    for idx, host_t in enumerate(timestamps):
        t = idx * 0.1
        flight = sim._flight_point(t)
        lines: list[str] = []
        if sim._should_emit_lora(t):
            lines.append(sim._make_lora_line(flight))
        lines.append(sim._make_rocket_line(flight))

        for line in lines:
            recorder.record_raw_line(datetime.fromtimestamp(host_t).isoformat(), line)
            parsed = dispatcher_live.parse_line(line)
            if parsed.kind == "data" and parsed.record is not None:
                store_live.append_record(parsed.source, host_t, parsed.record)

    recorder.stop()

    replay = ReplaySource(queue.Queue())
    replay.load(session_dir / "raw.log")

    dispatcher_replay = ParserDispatch()
    store_replay = ChannelStore(capacity=2000)
    for host_t, line in replay._lines:
        parsed = dispatcher_replay.parse_line(line)
        if parsed.kind == "data" and parsed.record is not None:
            store_replay.append_record(parsed.source, host_t, parsed.record)

    for stream in ["lora", "rocket"]:
        names_live, data_live = store_live.get_stream_data(stream)
        names_replay, data_replay = store_replay.get_stream_data(stream)

        assert names_live == names_replay
        assert data_live.shape == data_replay.shape
        assert np.allclose(data_live, data_replay, equal_nan=True)


def test_replay_loads_arbitrary_log_filename(tmp_path) -> None:
    replay_file = tmp_path / "sample_team_replay_raw.log"
    replay_file.write_text(
        "2026-10-31T10:00:00\tTEAM_ID,TIME,PACKET_COUNT,ALTITUDE,PRESSURE,TEMP,VOLTAGE,GNSS_TIME,GNSS_LAT,GNSS_LON,GNSS_ALT,GNSS_SATS,ACC_X,ACC_Y,ACC_Z,ROLL,PITCH,GYRO_X,GYRO_Y,GYRO_Z,FSW_STATE\n"
        "2026-10-31T10:00:01\t2026 IN-SPACe-042,412.6,413,684.7,92560,29.4,7.38,18763,26.7412,83.8875,776.2,9,0.84,-0.37,-11.42,12.5,4.8,38.6,-2.1,1.7,3\n",
        encoding="utf-8",
    )

    replay = ReplaySource(queue.Queue())
    replay.load(replay_file)

    assert replay.line_count == 2

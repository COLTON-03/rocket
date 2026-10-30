from model.store import ChannelStore
from parsers.records import GenericRecord


def test_store_appends_generic_record_values() -> None:
    store = ChannelStore(capacity=10)
    record = GenericRecord(values={"altitude": 100.0, "pressure": 90000.0})
    store.append_record(stream="team_csv", host_time_s=1000.0, record=record)

    names, data = store.get_stream_data("team_csv")
    assert names == ["host_t_s", "altitude", "pressure"]
    assert data.shape == (1, 3)
    assert data[0, 1] == 100.0
    assert data[0, 2] == 90000.0

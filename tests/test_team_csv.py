from parsers.dispatch import ParserDispatch


def test_team_csv_header_and_data_line() -> None:
    dispatch = ParserDispatch()

    header = (
        "TEAM_ID,TIME,PACKET_COUNT,ALTITUDE,PRESSURE,TEMP,VOLTAGE,GNSS_TIME,"
        "GNSS_LAT,GNSS_LON,GNSS_ALT,GNSS_SATS,ACC_X,ACC_Y,ACC_Z,ROLL,PITCH,"
        "GYRO_X,GYRO_Y,GYRO_Z,FSW_STATE"
    )
    header_result = dispatch.parse_line(header)
    assert header_result.source == "team_csv"
    assert header_result.kind == "header"

    data_line = (
        "2026 IN-SPACe-042,412.6,413,684.7,92560,29.4,7.38,18763,26.7412,"
        "83.8875,776.2,9,0.84,-0.37,-11.42,12.5,4.8,38.6,-2.1,1.7,3"
    )
    data_result = dispatch.parse_line(data_line)
    assert data_result.source == "team_csv"
    assert data_result.kind == "data"
    assert data_result.record is not None
    assert data_result.record.values["time"] == 412.6
    assert data_result.record.values["packet_count"] == 413
    assert data_result.record.values["altitude"] == 684.7
    assert data_result.record.values["pressure"] == 92560
    assert data_result.record.values["acc_z"] == -11.42
    assert data_result.record.values["fsw_state"] == 3

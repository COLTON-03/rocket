from model.link_stats import LinkStats


def test_lora_loss_and_reboot() -> None:
    stats = LinkStats()
    stats.update_lora(1, 10.0)
    stats.update_lora(4, 11.0)
    assert stats.lost_packets == 2

    rebooted = stats.update_lora(2, 12.0)
    assert rebooted
    assert stats.reboot_count == 1


def test_snapshot_time_since_last_packet() -> None:
    stats = LinkStats()
    stats.update_rocket(1000, 20.0)
    snap = stats.snapshot(now_s=23.5)
    assert snap.time_since_last_packet_s == 3.5

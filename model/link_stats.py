from __future__ import annotations

from dataclasses import dataclass
from math import isnan


@dataclass(slots=True)
class LinkSnapshot:
	got_packets: int
	lost_packets: int
	reboot_count: int
	session_loss_pct: float
	time_since_last_packet_s: float


class LinkStats:
	def __init__(self) -> None:
		self.got_packets = 0
		self.lost_packets = 0
		self.reboot_count = 0
		self.last_cnt: int | None = None
		self.last_t_ms: float | None = None
		self.last_packet_host_time_s: float | None = None

	def update_lora(self, cnt: float, host_time_s: float) -> bool:
		rebooted = False
		if not isnan(cnt):
			cnt_i = int(cnt)
			if self.last_cnt is not None:
				if cnt_i < self.last_cnt:
					self.reboot_count += 1
					rebooted = True
				elif cnt_i > self.last_cnt + 1:
					self.lost_packets += cnt_i - self.last_cnt - 1
			self.last_cnt = cnt_i
		self.got_packets += 1
		self.last_packet_host_time_s = host_time_s
		return rebooted

	def update_rocket(self, t_ms: float, host_time_s: float) -> bool:
		rebooted = False
		if self.last_t_ms is not None and t_ms < self.last_t_ms:
			self.reboot_count += 1
			rebooted = True
		self.last_t_ms = t_ms
		self.got_packets += 1
		self.last_packet_host_time_s = host_time_s
		return rebooted

	def snapshot(self, now_s: float) -> LinkSnapshot:
		total = self.got_packets + self.lost_packets
		session_loss_pct = (100.0 * self.lost_packets / total) if total else 0.0
		time_since = 0.0
		if self.last_packet_host_time_s is not None:
			time_since = max(0.0, now_s - self.last_packet_host_time_s)
		return LinkSnapshot(
			got_packets=self.got_packets,
			lost_packets=self.lost_packets,
			reboot_count=self.reboot_count,
			session_loss_pct=session_loss_pct,
			time_since_last_packet_s=time_since,
		)

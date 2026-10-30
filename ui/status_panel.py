from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QGridLayout, QWidget

from model.link_stats import LinkSnapshot


class StatusPanel(QWidget):
	def __init__(self) -> None:
		super().__init__()
		layout = QGridLayout(self)

		self.last_packet_label = QLabel("0.0 s since last packet", self)
		self.ok_badges = QLabel("Baro IMU GPS SD Radio", self)
		self.loss_label = QLabel("Loss: 0.0%", self)
		self.reboot_label = QLabel("Reboots: 0", self)
		self.ierr_label = QLabel("IMU err: 0", self)

		layout.addWidget(self.last_packet_label, 0, 0, 1, 2)
		layout.addWidget(self.ok_badges, 1, 0, 1, 2)
		layout.addWidget(self.loss_label, 2, 0)
		layout.addWidget(self.reboot_label, 2, 1)
		layout.addWidget(self.ierr_label, 3, 0, 1, 2)

	def update_view(self, snapshot: LinkSnapshot, ok: int | None, ierr: int | None) -> None:
		self.last_packet_label.setText(f"{snapshot.time_since_last_packet_s:.1f} s since last packet")
		self.loss_label.setText(f"Loss: {snapshot.session_loss_pct:.1f}% ({snapshot.lost_packets} lost)")
		self.reboot_label.setText(f"Reboots: {snapshot.reboot_count}")
		self.ierr_label.setText(f"IMU err: {ierr if ierr is not None else '-'}")

		if ok is None:
			self.ok_badges.setText("Baro IMU GPS SD Radio")
			return

		names = ["Baro", "IMU", "GPS", "SD", "Radio"]
		bits = [1, 2, 4, 8, 16]
		tags = []
		for name, bit in zip(names, bits, strict=True):
			good = (ok & bit) != 0
			tags.append(f"{name}:{'OK' if good else 'FAIL'}")
		self.ok_badges.setText("  ".join(tags))

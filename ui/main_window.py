from __future__ import annotations

import queue
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from model.events import EventDetector
from model.link_stats import LinkStats
from model.store import ChannelStore
from parsers.dispatch import ParserDispatch
from parsers.records import GenericRecord
from recorder import SessionRecorder
from sources.replay_source import ReplaySource
from sources.serial_source import SerialSource
from sources.sim_source import SimSource
from ui.dashboard import Dashboard
from ui.console import ConsolePane
from ui.serial_plotter import SerialPlotter


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Rocket Ground Station Analyzer")
        self.resize(1280, 800)

        self._line_queue: queue.Queue[tuple[float, str, str]] = queue.Queue()
        self._dispatch = ParserDispatch()
        self._store = ChannelStore(capacity=24000)
        self._link_stats = LinkStats()
        self._events = EventDetector()
        self._recorder = SessionRecorder()
        self._serial_source = SerialSource(self._line_queue, source_id="serial")
        self._sim_source = SimSource(self._line_queue, emit_mode="both", speed=1.0)
        self._replay_source = ReplaySource(self._line_queue)
        self._auto_serial_capture = True

        central = QWidget(self)
        layout = QVBoxLayout(central)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Source:"))

        self.source_selector = QComboBox(self)
        self.source_selector.addItems(["Serial", "Simulator"])

        self.port_selector = QComboBox(self)
        self.refresh_ports_button = QPushButton("Refresh Ports", self)
        self.refresh_ports_button.clicked.connect(self._refresh_ports)

        self.baud_selector = QComboBox(self)
        for baud in SerialSource.supported_baud_rates():
            self.baud_selector.addItem(str(baud))
        self.baud_selector.setCurrentText("115200")

        self.connect_button = QPushButton("Connect", self)
        self.connect_button.clicked.connect(self._toggle_connection)

        self.record_button = QPushButton("Record", self)
        self.record_button.setCheckable(True)
        self.record_button.setChecked(True)
        self.replay_button = QPushButton("Open Replay", self)
        self.replay_button.clicked.connect(self._open_replay)

        self.replay_pause_button = QPushButton("Pause Replay", self)
        self.replay_pause_button.setCheckable(True)
        self.replay_pause_button.clicked.connect(self._toggle_replay_pause)

        self.replay_speed_selector = QComboBox(self)
        self.replay_speed_selector.addItems(["1x", "5x", "20x", "max"])
        self.replay_speed_selector.currentTextChanged.connect(self._set_replay_speed)

        self.replay_seek_slider = QSlider(self)
        self.replay_seek_slider.setOrientation(Qt.Orientation.Horizontal)
        self.replay_seek_slider.sliderReleased.connect(self._seek_replay)
        self.replay_seek_slider.setMinimum(0)
        self.replay_seek_slider.setMaximum(0)

        toolbar.addWidget(self.source_selector)
        toolbar.addWidget(self.port_selector)
        toolbar.addWidget(self.refresh_ports_button)
        toolbar.addWidget(self.baud_selector)
        toolbar.addWidget(self.connect_button)
        toolbar.addWidget(self.record_button)
        toolbar.addWidget(self.replay_button)
        toolbar.addWidget(self.replay_pause_button)
        toolbar.addWidget(self.replay_speed_selector)
        toolbar.addWidget(self.replay_seek_slider)
        toolbar.addStretch(1)

        self.serial_plotter = SerialPlotter()
        self.dashboard = Dashboard()
        self.console = ConsolePane()

        tabs = QTabWidget(self)
        tabs.addTab(self.dashboard, "Dashboard")
        tabs.addTab(self.serial_plotter, "Generic Plotter")

        splitter = QSplitter(self)
        splitter.addWidget(tabs)
        splitter.addWidget(self.console)
        splitter.setSizes([840, 440])

        layout.addLayout(toolbar)
        layout.addWidget(splitter)
        self.setCentralWidget(central)

        self._refresh_ports()

        self._drain_timer = QTimer(self)
        self._drain_timer.setInterval(33)
        self._drain_timer.timeout.connect(self._drain_queue)
        self._drain_timer.start()

        self._auto_connect_timer = QTimer(self)
        self._auto_connect_timer.setInterval(2000)
        self._auto_connect_timer.timeout.connect(self._attempt_auto_connect)
        self._auto_connect_timer.start()

        QTimer.singleShot(300, self._attempt_auto_connect)

    def closeEvent(self, event: Any) -> None:
        self._serial_source.stop_source()
        self._sim_source.stop_source()
        self._replay_source.stop_source()
        self._recorder.stop()
        super().closeEvent(event)

    def _refresh_ports(self) -> None:
        current = self.port_selector.currentText()
        self.port_selector.clear()
        ports = SerialSource.list_available_ports()
        self.port_selector.addItems(ports)
        suggested = SerialSource.suggest_default_port()
        if suggested:
            suggested_idx = self.port_selector.findText(suggested)
            if suggested_idx >= 0:
                self.port_selector.setCurrentIndex(suggested_idx)
        if current:
            idx = self.port_selector.findText(current)
            if idx >= 0:
                self.port_selector.setCurrentIndex(idx)

    def _connect_serial(self) -> bool:
        port = self.port_selector.currentText().strip()
        if not port:
            return False
        baud = int(self.baud_selector.currentText())
        self._serial_source.configure(port=port, baud=baud)
        self._serial_source.start_source()
        if self.record_button.isChecked() and self._recorder.session_dir is None:
            self._recorder.start()
        self.connect_button.setText("Disconnect")
        return True

    def _attempt_auto_connect(self) -> None:
        if not self._auto_serial_capture:
            return
        if self._serial_source.isRunning() or self._sim_source.isRunning() or self._replay_source.isRunning():
            return
        if self.source_selector.currentText() != "Serial":
            return
        self._refresh_ports()
        self._connect_serial()

    def _toggle_connection(self) -> None:
        if self._serial_source.isRunning() or self._sim_source.isRunning():
            self._serial_source.stop_source()
            self._sim_source.stop_source()
            self._recorder.stop()
            self.connect_button.setText("Connect")
            return

        selected_source = self.source_selector.currentText()
        if selected_source == "Serial":
            if not self._connect_serial():
                return
        else:
            self._sim_source.start_source()

        if selected_source != "Serial" and self.record_button.isChecked():
            self._recorder.start()
        self.connect_button.setText("Disconnect")

    def _drain_queue(self) -> None:
        drained = 0
        while drained < 200:
            try:
                host_time_s, source_id, line = self._line_queue.get_nowait()
            except queue.Empty:
                break

            self.console.append_line(f"{source_id}: {line}")
            self._recorder.record_raw_line(datetime.fromtimestamp(host_time_s).isoformat(), line)
            parsed = self._dispatch.parse_line(line)
            if parsed.kind == "data" and parsed.record is not None:
                self._store.append_record(parsed.source, host_time_s, parsed.record)
                self._recorder.record_parsed(parsed.source, parsed.record)
                self._update_stats_and_events(parsed.source, parsed.record, host_time_s)

                names, values = self._store.get_stream_data(parsed.source)
                self.dashboard.update_from_record(parsed.record, names, values, parsed.source)

                if isinstance(parsed.record, GenericRecord):
                    names, values = self._store.get_stream_data(parsed.source)
                    self.serial_plotter.set_data(names, values)
                elif parsed.source == "lora_rcv":
                    names, values = self._store.get_stream_data("lora_rcv")
                    self.serial_plotter.set_data(names, values)
            elif parsed.kind == "bad":
                self.dashboard.set_alarm(f"BAD LINE: {parsed.error}")

            drained += 1

        snapshot = self._link_stats.snapshot(now_s=time.time())
        no_telemetry_events = self._events.detect_no_telemetry(snapshot.time_since_last_packet_s, time.time())
        for event in no_telemetry_events:
            self.dashboard.set_alarm(event.detail)
            self.dashboard.add_event_time(event.t_host_s)

        self.dashboard.update_status(snapshot=snapshot, ok=self._latest_ok(), ierr=self._latest_ierr())

    def _latest_ok(self) -> int | None:
        for stream in ["lora", "rocket", "sd"]:
            names, data = self._store.get_stream_data(stream)
            if data.size == 0 or "ok" not in names:
                continue
            idx = names.index("ok")
            return int(data[-1, idx])
        return None

    def _latest_ierr(self) -> int | None:
        names, data = self._store.get_stream_data("lora")
        if data.size == 0 or "ierr" not in names:
            return None
        idx = names.index("ierr")
        return int(data[-1, idx])

    def _update_stats_and_events(self, source: str, record: object, host_time_s: float) -> None:
        rebooted = False
        if source == "lora":
            rebooted = self._link_stats.update_lora(getattr(record, "cnt"), host_time_s)
        elif source == "rocket":
            rebooted = self._link_stats.update_rocket(getattr(record, "t_ms"), host_time_s)
        else:
            self._link_stats.last_packet_host_time_s = host_time_s

        if rebooted:
            self.dashboard.set_alarm("ROCKET REBOOTED")
            self.dashboard.add_event_time(host_time_s)
            self._recorder.record_event(datetime.fromtimestamp(host_time_s).isoformat(), "reboot", "ROCKET REBOOTED")

        events = self._events.detect_record(source=source, record=record, host_time_s=host_time_s)
        for event in events:
            self.dashboard.add_event_time(event.t_host_s)
            self._recorder.record_event(
                datetime.fromtimestamp(event.t_host_s).isoformat(),
                event.name,
                event.detail,
            )
            if event.name == "alarm":
                self.dashboard.set_alarm(event.detail)

    def _open_replay(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Open Replay File",
            str(Path.cwd()),
            "Replay Files (*.log *.csv *.CSV);;All Files (*.*)",
        )
        if not selected:
            return

        self._serial_source.stop_source()
        self._sim_source.stop_source()
        self._replay_source.stop_source()
        try:
            self._replay_source.load(selected)
        except ValueError as exc:
            self.dashboard.set_alarm(f"REPLAY ERROR: {exc}")
            return
        self.replay_seek_slider.setMaximum(max(0, self._replay_source.line_count - 1))
        self._replay_source.start_source()

    def _toggle_replay_pause(self) -> None:
        paused = self.replay_pause_button.isChecked()
        self._replay_source.pause(paused)
        self.replay_pause_button.setText("Resume Replay" if paused else "Pause Replay")

    def _set_replay_speed(self, label: str) -> None:
        if label == "max":
            speed = 1_000_000.0
        else:
            speed = float(label.replace("x", ""))
        self._replay_source.set_speed(speed)

    def _seek_replay(self) -> None:
        self._replay_source.seek(self.replay_seek_slider.value())
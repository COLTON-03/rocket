# Copilot instructions: Rocket Ground Station Analyzer

This repo is a desktop ground station and graph analyzer for a model-rocket flight computer (Raspberry Pi Pico / RP2040, MicroPython). The full specification is in `ANALYZER_SPEC.md` at the repo root. Read it before generating code, and treat its data formats as exact.

## Stack (do not substitute)
- Python 3.11+
- PyQt6 for the UI, pyqtgraph for every live plot (never matplotlib for live plots)
- pyserial for serial ports, numpy for buffers
- pytest for tests
- PyInstaller for packaging

## Architecture rules
- The serial reader runs in its own `QThread`. It only reads lines (bytes → str, `errors="replace"`) and pushes `(t_host, source_id, line)` into a `queue.Queue`. No parsing and no UI calls in that thread.
- A single `QTimer` on the GUI thread (default 33 ms) drains the queue, parses lines, appends to ring buffers and redraws.
- All channel data lives in numpy ring buffers (`model/buffers.py`); plots read from buffers, never from parsers.
- Parsers are pure functions/classes with no Qt imports, so they are unit-testable.
- Every received raw line is written to the session recorder before parsing.
- Never crash on a bad line: count it, show it in the console pane, continue.

## Data facts that must not be "corrected"
- LoRa telemetry fields are separated by `;` inside the radio payload; the ground station re-emits them as comma-separated lines starting with `CSV,`.
- LoRa packets may have 13 fields (old firmware / test scripts) or 21 fields (with IMU). Missing fields are empty strings and must become NaN, not 0.
- State codes: 0 PAD, 1 FLIGHT, 2 DESCENT, 3 LANDED, 4 BEACON.
- Fire codes: 0 not fired, 1 barometric apogee, 2 backup timer.
- `ok` bits: 1 baro, 2 IMU, 4 GPS, 8 SD, 16 radio; 31 = all OK.
- There is no magnetometer and no second accelerometer on this rocket. Do not add panels for them.

## Style
- Type hints everywhere, dataclasses for parsed records.
- Small modules matching the tree in the spec; no file over ~400 lines.
- Units in variable names where ambiguous (`alt_m`, `vel_ms`, `t_ms`).

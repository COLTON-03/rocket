# Rocket Ground Station Analyzer: Build Specification

Self-contained spec for building the analyzer with GitHub Copilot. Section 8 holds the prompts to paste into Copilot Chat (Agent mode), one phase at a time.

## 1. System context

Rocket flight computer: Raspberry Pi Pico (RP2040) running MicroPython, 50 Hz main loop.

| Module | Data |
|---|---|
| MPU6050, ±16 g / ±2000 dps | ax, ay, az (g), gx, gy, gz (dps, bias-calibrated) |
| BMP388 | pressure (Pa), temperature (°C), filtered altitude above pad (m), vertical velocity (m/s), max altitude (m) |
| NEO-M9N GPS | fix (0/1/2), satellites, lat/lon (decimal degrees), GPS altitude MSL (m) |
| RYLR998 LoRa, 866 MHz, SF9/125 kHz | 1 Hz telemetry to a ground Pico; ground adds RSSI (dBm) and SNR (dB) |
| Battery divider | 3S Li-ion/LiPo voltage (12.6 V full, 9.9 V minimum) |
| Nichrome deployment | fire flag, fire reason |

Flight states: PAD → FLIGHT → DESCENT → LANDED. Deployment (single event) moves FLIGHT → DESCENT.

## 2. Input formats (exact)

### 2.1 Source A: ground station over USB (live LoRa, 1 Hz)

The ground Pico prints several kinds of lines. Only lines starting with `CSV,` are data; everything else goes to the console pane only.

Header line (printed once at boot; detect it by `CSV,cnt`):
```
CSV,cnt,state,t_s,alt_m,vel_ms,max_m,batt_v,fix,sats,lat,lon,fire,ok,ax,ay,az,gx,gy,gz,apk,ierr,rssi,snr
```

Data line example (21 payload fields + rssi + snr):
```
CSV,12,1,3.2,152.3,45.1,152.3,11.90,1,9,13.069977,77.557097,0,31,0.12,-0.05,8.73,4,-12,310,9.84,0,-71,9
```

Old 13-field packets arrive padded with empty strings in positions 13–20:
```
CSV,12,0,0.0,0.3,0.0,0.3,12.41,0,0,0.000000,0.000000,0,27,,,,,,,,,-45,11
```

| Index after `CSV` | Name | Type | Unit / meaning |
|---|---|---|---|
| 0 | cnt | int | Packet counter. Gap = lost packets; decrease = rocket rebooted |
| 1 | state | int | 0 PAD, 1 FLIGHT, 2 DESCENT, 3 LANDED, 4 BEACON |
| 2 | t_s | float | Seconds since launch (0 before launch) |
| 3 | alt_m | float | Baro altitude above pad |
| 4 | vel_ms | float | Vertical velocity |
| 5 | max_m | float | Max altitude so far |
| 6 | batt_v | float | Battery voltage |
| 7 | fix | int | 0 none, 1 GPS, 2 DGPS |
| 8 | sats | int | Satellites |
| 9 | lat | float | Decimal degrees |
| 10 | lon | float | Decimal degrees |
| 11 | fire | int | 0 not fired, 1 baro, 2 timer |
| 12 | ok | int | Module bitmask (1 baro, 2 IMU, 4 GPS, 8 SD, 16 radio) |
| 13–15 | ax, ay, az | float | g, snapshot |
| 16–18 | gx, gy, gz | float | dps, snapshot |
| 19 | apk | float | Peak \|a\| (g) since previous packet |
| 20 | ierr | int | Failed IMU reads since previous packet |
| 21 | rssi | int | dBm (added by ground) |
| 22 | snr | int | dB (added by ground) |

Rules: empty field → NaN; non-numeric field → whole line counted as bad; fewer than 15 fields → bad. Also handle the 13-field form *without* padding (old ground firmware): then the last two values are rssi, snr.

### 2.2 Source B: rocket over USB (bench, 20 Hz)

```
R,t_ms,state,alt_m,vel_ms,max_m,press_pa,temp_c,ax,ay,az,amag,gx,gy,gz,batt_v,sats,fire,ok
```
Example:
```
R,183422,0,0.12,0.03,0.00,91085.2,28.41,0.012,-0.004,1.002,1.002,0.4,-0.2,0.1,12.38,9,0,31
```
`t_ms` is the Pico's `ticks_ms` (wraps; treat as monotonic within a session, handle decrease as reboot). Other lines from the rocket (`>>> LAUNCH detected`, `BMP388 FAIL: ...`) go to the console and to the event log if they start with `>>>`.

### 2.3 Source C: SD card log replay (50 Hz, file FLTnnn.CSV)

Header:
```
t_ms,state,alt_m,vel_ms,max_m,press_pa,temp_c,ax,ay,az,amag,gx,gy,gz,batt_v,fix,sats,lat,lon,gps_alt,fire
```
Here `fire` is 1 while the nichrome is on (not the reason code). No RSSI/SNR/ok in this format.

### 2.4 Source D: generic serial plotter

Any line of numbers separated by commas, spaces, tabs or semicolons, optionally with `label:value` pairs (Arduino-plotter style). If the first line is all non-numeric tokens, use it as column names. Plots every numeric column.

## 3. Application structure

```
groundstation/
├── main.py                    # QApplication, MainWindow, mode selection
├── sources/
│   ├── base.py                # Source interface: start(), stop(), lines -> queue
│   ├── serial_source.py       # QThread, port + baud, auto-reconnect every 2 s
│   ├── replay_source.py       # file playback, speed 1x/5x/20x/max, pause, seek
│   └── sim_source.py          # synthetic flight emitting Source A and/or B lines
├── parsers/
│   ├── records.py             # dataclasses: LoraRecord, RocketRecord, SdRecord, GenericRecord
│   ├── lora_csv.py
│   ├── rocket_stream.py
│   ├── sd_log.py
│   ├── generic.py
│   └── dispatch.py            # picks parser by prefix / header
├── model/
│   ├── buffers.py             # RingBuffer(n, channels) with numpy, append/view/clear
│   ├── store.py               # named channels -> RingBuffer; time base handling
│   ├── link_stats.py          # lost packets, loss %, reboots, time since last packet
│   └── events.py              # launch/deploy/landing/reboot/alarm detection
├── ui/
│   ├── main_window.py         # toolbar: source, port, baud, connect, record, replay
│   ├── dashboard.py           # flight dashboard grid (section 4)
│   ├── plot_panel.py          # reusable pyqtgraph panel with event markers
│   ├── serial_plotter.py      # generic auto-plot view
│   ├── state_bar.py
│   ├── status_panel.py
│   ├── telemetry_table.py
│   ├── gps_panel.py
│   ├── console.py             # raw line view, filter, autoscroll toggle
│   └── theme.py               # dark theme, colors per axis (x red, y green, z blue)
├── recorder.py                # sessions/YYYYMMDD_HHMMSS/{raw.log, lora.csv, rocket.csv, events.csv}
├── analysis.py                # post-flight stats
└── tests/
    ├── test_lora_csv.py
    ├── test_rocket_stream.py
    ├── test_sd_log.py
    ├── test_generic.py
    ├── test_link_stats.py
    └── test_events.py
```

`requirements.txt`: PyQt6, pyqtgraph, pyserial, numpy, pytest, pyinstaller.

## 4. Dashboard layout

Dark theme, 4×3 grid plus bottom state bar.

| Row | Col 1 | Col 2 | Col 3 | Col 4 |
|---|---|---|---|---|
| 1 | Acceleration: ax, ay, az, plus apk as a thicker trace (g) | Gyro: gx, gy, gz (dps) | Battery (V), red line at 9.9 V | RSSI (dBm) and SNR (dB), two y-axes |
| 2 | Altitude: alt_m and max_m (m) | Status panel (spans col 2–3): large "N s since last packet", ok-bit badges (Baro, IMU, GPS, SD, Radio), loss %, reboot count, ierr badge | | Telemetry table: latest value of every field |
| 3 | Vertical velocity (m/s) | GPS altitude vs baro altitude (SD replay only; hidden otherwise) | GPS track: east/north metres from first valid fix, distance and bearing text, last known lat/lon in large font with copy button | Pressure and temperature (sources B/C only) |
| Bottom | State bar: PAD → FLIGHT → DESCENT → LANDED circles, current one filled; deploy badge "BARO" / "TIMER" when fire ≠ 0 | | | |

Rules:
- X axis: seconds since launch once launched (first state change to FLIGHT); seconds since session start before launch. A toggle switches to host clock.
- Vertical dashed lines on every time plot at launch, deploy and landing.
- Live window selectable: 30 s, 60 s, 120 s, all.
- Panels with no data for the current source show "no data from this source" instead of an empty axis.
- GPS east/north: `dE = R·cos(lat0)·Δlon`, `dN = R·Δlat` (radians, R = 6 371 000 m). Ignore fixes where fix = 0 or lat = lon = 0.

## 5. Link statistics and events

| Item | Rule |
|---|---|
| Lost packets | If cnt > last + 1, lost += cnt − last − 1 |
| Reboot | cnt < last (source A) or t_ms decreases (source B): increment reboots, insert event, keep plotting |
| Loss % | lost / (got + lost) over the session and over the last 60 s |
| Time since last packet | Host clock; updates every UI tick even with no data |
| Launch event | First record with state = 1 |
| Deploy event | First record with fire ≠ 0 (source A/B) or fire = 1 (source C) |
| Landing event | First record with state = 3 |

Alarms (banner + optional beep, each logged once per occurrence):

| Condition | Message |
|---|---|
| No packet for > 5 s | "NO TELEMETRY N s" (escalating red) |
| Reboot | "ROCKET REBOOTED" |
| ok ≠ 31 | "MODULE FAULT: <names>" |
| batt_v < 9.9 | "BATTERY LOW" |
| ierr > 0 | "IMU READ ERRORS" |
| State 3 and fix = 0 | "NO GPS FIX AFTER LANDING" |

## 6. Recording, replay and analysis

- Recording starts automatically on connect. `raw.log` holds `host_iso_time<TAB>line` for every line; parsed CSVs are written per record type; `events.csv` holds events and alarms.
- Replay accepts: a session folder, `raw.log`, or an SD `FLTnnn.CSV`. Replay feeds lines through the exact same dispatch/parsers/store as live data, timed by recorded timestamps (raw.log) or `t_ms` (SD log).
- Post-flight stats window (`analysis.py`): apogee (m) and time to apogee, max |a| and when, max velocity, burnout time (|a| drops below 1.5 g after launch), deploy time and delay after true apogee, mean descent rate, flight duration, landing position and distance/bearing from pad, total lost packets. Export as CSV and PNG of the dashboard.

## 7. Simulator (sim_source.py)

Generates realistic lines for testing with no hardware. Profile (matches the flight-code simulations):
- 10 s on the pad: alt noise ±0.3 m, az ≈ 1.0 g, gyro noise ±1 dps.
- Boost 2 s: |a| about 8–10 g along z; gyro small roll rate.
- Coast to apogee ≈ 1 460 m at T+18 s (tune drag to hit it); accelerometer reads near 0 g minus drag.
- Deploy 0.7 s after true apogee (fire = 1), then descent at 6 m/s to the ground; |a| ≈ 1 g with swinging noise.
- LANDED 10 s after touchdown.
- GPS: start at 13.0700, 77.5571; drift 200–400 m downrange during descent.
- Battery: 12.4 V sagging slowly; RSSI from −40 dBm falling with distance to about −100 dBm; SNR 10 → −5.
- Options: packet loss % (random and burst), one reboot at a chosen time, knock on the pad (4 g for 150 ms, no climb), speed 1×/5×/20×, emit source A, B or both.

## 8. Copilot Chat prompts (Agent mode)

Run one phase at a time. After each phase: run the app, run `pytest`, commit. Paste each prompt as-is.

**Phase 0, scaffold**
> Read ANALYZER_SPEC.md and .github/copilot-instructions.md. Create the folder structure from section 3 with empty modules, requirements.txt, a README with run instructions, and a MainWindow that opens a dark-themed empty window. Do not implement features yet.

**Phase 1, parsers and tests**
> Implement parsers/records.py, lora_csv.py, rocket_stream.py, sd_log.py, generic.py and dispatch.py exactly per section 2 of ANALYZER_SPEC.md. Write pytest tests covering: 21-field LoRa line, 13-field padded line, 13-field unpadded line, header line, bad numeric field, empty fields → NaN, R line, SD header and row, generic comma/space/label:value lines. All tests must pass.

**Phase 2, serial source, buffers, serial plotter**
> Implement sources/serial_source.py (QThread, port list refresh, baud selector 9600/38400/57600/115200, auto-reconnect), model/buffers.py and model/store.py, ui/console.py and ui/serial_plotter.py. The serial plotter auto-plots every numeric column of generic lines with a legend, pause, clear and window-length selector. Follow the threading rules in copilot-instructions.md.

**Phase 3, simulator**
> Implement sources/sim_source.py per section 7, as a Source selectable in the toolbar, with options for loss %, reboot time, pad knock and speed. It must emit lines in the exact formats of section 2.1 and 2.2.

**Phase 4, flight dashboard**
> Implement ui/dashboard.py, plot_panel.py, state_bar.py, status_panel.py, telemetry_table.py and gps_panel.py per section 4, fed from model/store.py. Implement model/link_stats.py and model/events.py per section 5, including event markers on every plot and the alarm banner. Verify with the simulator at 1× and 20×.

**Phase 5, recorder and replay**
> Implement recorder.py and sources/replay_source.py per section 6, with a replay toolbar (play/pause, speed, seek slider). Replay must go through the same dispatch and store as live data. Add a test that records a simulated session and replays it to identical buffer contents.

**Phase 6, analysis and packaging**
> Implement analysis.py and a post-flight stats dialog per section 6, with CSV and PNG export. Add a PyInstaller spec producing a single-folder Windows build. Profile the UI with the simulator at 20× and keep redraws under 15 ms per tick.

## 9. Acceptance tests (with hardware)

| Test | Pass when |
|---|---|
| Ground Pico on USB, rocket on bench (DRY_RUN, CRFOP 10) | All LoRa panels update at 1 Hz; IMU panels show az ≈ 1 g; ok badges all green |
| Tap the rocket board | apk spikes while ax/ay/az snapshots may not |
| Unplug the MPU6050 | IMU badge red, ierr alarm |
| Power-cycle the rocket | "ROCKET REBOOTED" once, plots continue |
| Unplug ground USB mid-session | Auto-reconnect; recording continues |
| Replay an SD FLTnnn.CSV | Plots and stats match the file opened in a spreadsheet |
| Field laptop with no internet | App runs, GPS panel works |

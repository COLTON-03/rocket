# Rocket Ground Station Analyzer (Rekha Flight Guide)

This application is your flight ground station for rocket telemetry.

It helps you:

- Watch live telemetry during launch.
- Monitor link quality (RSSI/SNR) from LoRa packets.
- See altitude, velocity, battery, IMU, GPS, and state changes.
- Record every session automatically for post-flight review.
- Replay logs and export analysis artifacts.

Important: the analyzer now auto-connects to the Pico serial port and starts plotting automatically when data appears (no button clicks required).

---

## 1) One-time setup (only once on this laptop)

Open PowerShell and run:

```powershell
Set-Location C:\Rekha
C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If this completes without errors, setup is done forever (unless dependencies change).

---

## 2) Start the analyzer (every launch day)

Open PowerShell and run:

```powershell
Set-Location C:\Rekha
.\.venv\Scripts\Activate.ps1
python main.py
```

The GUI opens. Keep this PowerShell window open while the app is running.

After startup, the analyzer automatically:

- Detects likely Pico/RP2040 COM port.
- Connects to serial in the background.
- Starts recording and plotting as soon as telemetry lines arrive.

---

## 3) Pre-flight checklist (inside the app)

1. Connect ground LoRa USB to laptop.
2. In app toolbar:
   - Source = `Serial`
   - Select correct COM port
   - Baud = `115200` (or your configured baud)
3. Wait 2–5 seconds for auto-connect.
4. Confirm live data appears in Console and Dashboard.
5. Confirm status indicators:
   - Packet timer updating
   - RSSI/SNR graph moving
   - Battery visible
   - GPS fix/sats valid

Recording starts automatically when connected (if `Record` toggle is on).

---

## Thonny workflow (important)

If you use Thonny for Pico coding:

1. Flash or run code from Thonny as usual.
2. Stop/close Thonny serial monitor before expecting analyzer to read telemetry.
3. Keep analyzer open; it will auto-connect and start plotting when the COM port is free.

Reason: only one app can own the Pico serial COM port at a time on Windows.

If data does not appear, close Thonny terminal pane/session and wait a few seconds.

---

## 4) During flight

Watch these key panels first:

- `State bar`: PAD → FLIGHT → DESCENT → LANDED
- `Altitude` and `Velocity`
- `RSSI/SNR` for link health
- `Status panel` for packet loss/reboots/module faults
- `Alarm banner` for critical alerts

If telemetry drops, keep app running; reconnect logic and recording continue when data returns.

---

## 5) After flight

### A) Recorded files

Session files are saved in:

- `sessions\YYYYMMDD_HHMMSS\raw.log`
- `sessions\YYYYMMDD_HHMMSS\events.csv`
- `sessions\YYYYMMDD_HHMMSS\*.csv` (parsed streams)

### B) Replay data in app

1. Click `Open Replay`
2. Select a `raw.log` or SD `FLTnnn.CSV`
3. Use:
   - `Pause Replay`
   - Speed selector (`1x`, `5x`, `20x`, `max`)
   - Seek slider

---

## 6) Your current supported input formats

The analyzer currently parses and plots:

- Team telemetry CSV with header:
  - `TEAM_ID,TIME,PACKET_COUNT,ALTITUDE,PRESSURE,TEMP,VOLTAGE,GNSS_TIME,GNSS_LAT,GNSS_LON,GNSS_ALT,GNSS_SATS,ACC_X,ACC_Y,ACC_Z,ROLL,PITCH,GYRO_X,GYRO_Y,GYRO_Z,FSW_STATE`
  - Example data row is auto-detected and plotted without manual mapping.
- `CSV,...` rocket telemetry packets
- `R,...` rocket USB stream packets
- SD log rows with SD header
- RYLR link packets: `+RCV=...,rssi,snr`
- Textual bench logs such as:
  - `Temperature = ...`
  - `Pressure = ...`
  - `Approx Altitude = ...`
  - `Fix: ... | Sats: ... | Lat: ... | Lon: ... | Alt: ...`
  - `Acc g: ... | Gyro dps: ... | Temp: ...`

---

## 7) Optional: train baseline from old logs

If you have a text file containing old BMP/GPS/MPU/LoRa logs, you can extract a launch baseline model:

```powershell
Set-Location C:\Rekha
.\.venv\Scripts\Activate.ps1
python tools\train_from_text_logs.py .\your_logs.txt
```

This prints baseline statistics (pressure, accel-Z, RSSI) for launch scoring.

---

## 8) Quick health check (before important launch)

```powershell
Set-Location C:\Rekha
.\.venv\Scripts\Activate.ps1
python -m pytest -q
```

Expected: all tests pass.

---

## 9) Build executable (optional)

If you want a packaged executable:

```powershell
Set-Location C:\Rekha
.\.venv\Scripts\Activate.ps1
pyinstaller groundstation.spec
```

Output: `dist\groundstation.exe`

---

## 10) Troubleshooting (fast)

- App doesn’t open:
  - Re-run the exact run commands from section 2.
- No COM ports shown:
  - Plug USB, click `Refresh Ports`, reselect port.
- No telemetry lines:
  - Check baud and radio wiring/power.
- Bad random values/spikes in bench logs:
  - Inspect sensor power and wiring, then compare in replay.
- Python command not found:
  - Use the full Python path from section 1 for setup.

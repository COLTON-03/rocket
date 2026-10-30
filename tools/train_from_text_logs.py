from __future__ import annotations

import re
from pathlib import Path

from model.launch_training import train_launch_model

PRESS_RE = re.compile(r"Pressure\s*=\s*(-?\d+(?:\.\d+)?)\s*hPa", re.IGNORECASE)
ACCZ_RE = re.compile(r"Acc\s+g:\s*-?\d+(?:\.\d+)?\s+-?\d+(?:\.\d+)?\s+(-?\d+(?:\.\d+)?)", re.IGNORECASE)
RSSI_RE = re.compile(r"\+RCV=\d+,\d+,.*?,(-?\d+),-?\d+", re.IGNORECASE)


def extract_samples(text: str) -> tuple[list[float], list[float], list[float]]:
    pressure = [float(m.group(1)) for m in PRESS_RE.finditer(text)]
    accz = [float(m.group(1)) for m in ACCZ_RE.finditer(text)]
    rssi = [float(m.group(1)) for m in RSSI_RE.finditer(text)]
    return pressure, accz, rssi


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Train launch baseline model from pasted text logs")
    parser.add_argument("input", help="Path to text file containing BMP/GPS/MPU/LoRa logs")
    args = parser.parse_args()

    text = Path(args.input).read_text(encoding="utf-8", errors="replace")
    pressure, accz, rssi = extract_samples(text)
    model = train_launch_model(pressure_hpa_samples=pressure, accel_z_samples_g=accz, rssi_samples_dbm=rssi)

    print("Launch baseline model:")
    print(f"  pressure_mean_hpa={model.pressure_mean_hpa:.3f}")
    print(f"  pressure_std_hpa={model.pressure_std_hpa:.3f}")
    print(f"  accel_z_mean_g={model.accel_z_mean_g:.3f}")
    print(f"  accel_z_std_g={model.accel_z_std_g:.3f}")
    print(f"  rssi_mean_dbm={model.rssi_mean_dbm:.3f}")
    print(f"  rssi_std_dbm={model.rssi_std_dbm:.3f}")


if __name__ == "__main__":
    main()

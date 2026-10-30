from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class LaunchModel:
    pressure_mean_hpa: float
    pressure_std_hpa: float
    accel_z_mean_g: float
    accel_z_std_g: float
    rssi_mean_dbm: float
    rssi_std_dbm: float

    def launch_score(self, pressure_hpa: float, accel_z_g: float, rssi_dbm: float) -> float:
        p_z = 0.0 if self.pressure_std_hpa == 0 else (self.pressure_mean_hpa - pressure_hpa) / self.pressure_std_hpa
        a_z = 0.0 if self.accel_z_std_g == 0 else (accel_z_g - self.accel_z_mean_g) / self.accel_z_std_g
        r_z = 0.0 if self.rssi_std_dbm == 0 else abs(rssi_dbm - self.rssi_mean_dbm) / self.rssi_std_dbm
        return float(0.5 * a_z + 0.3 * p_z + 0.2 * r_z)

    def predicts_launch(self, pressure_hpa: float, accel_z_g: float, rssi_dbm: float, threshold: float = 3.0) -> bool:
        return self.launch_score(pressure_hpa, accel_z_g, rssi_dbm) >= threshold


def train_launch_model(
    pressure_hpa_samples: list[float],
    accel_z_samples_g: list[float],
    rssi_samples_dbm: list[float],
) -> LaunchModel:
    pressure = np.asarray(pressure_hpa_samples, dtype=np.float64)
    accel_z = np.asarray(accel_z_samples_g, dtype=np.float64)
    rssi = np.asarray(rssi_samples_dbm, dtype=np.float64)

    if pressure.size == 0 or accel_z.size == 0 or rssi.size == 0:
        raise ValueError("All sample lists must be non-empty")

    return LaunchModel(
        pressure_mean_hpa=float(np.nanmean(pressure)),
        pressure_std_hpa=float(np.nanstd(pressure) + 1e-6),
        accel_z_mean_g=float(np.nanmean(accel_z)),
        accel_z_std_g=float(np.nanstd(accel_z) + 1e-6),
        rssi_mean_dbm=float(np.nanmean(rssi)),
        rssi_std_dbm=float(np.nanstd(rssi) + 1e-6),
    )

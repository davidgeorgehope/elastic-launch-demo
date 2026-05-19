"""Fuel System service — AWS us-east-1. Propulsion telemetry with realistic sensors."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class FuelSystemService(BaseService):
    SERVICE_NAME = "fuel-system"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._check_count = 0
        self._last_press_summary = time.time()

    # Nominal sensor ranges
    SENSORS = {
        "engine_thermal": {
            "name": "Engine Bay Temperature",
            "unit": "K",
            "nominal_min": 280.0,
            "nominal_max": 320.0,
            "metric": "fuel_system.engine_thermal",
        },
        "lox_pressure": {
            "name": "LOX Tank Pressure",
            "unit": "PSI",
            "nominal_min": 240.0,
            "nominal_max": 290.0,
            "metric": "fuel_system.lox_pressure",
        },
        "rp1_pressure": {
            "name": "RP-1 Tank Pressure",
            "unit": "PSI",
            "nominal_min": 220.0,
            "nominal_max": 270.0,
            "metric": "fuel_system.rp1_pressure",
        },
        "fuel_flow": {
            "name": "Fuel Flow Rate",
            "unit": "kg/s",
            "nominal_min": 4.2,
            "nominal_max": 5.8,
            "metric": "fuel_system.fuel_flow_rate",
        },
        "oxidizer_flow": {
            "name": "Oxidizer Flow Rate",
            "unit": "kg/s",
            "nominal_min": 10.5,
            "nominal_max": 14.5,
            "metric": "fuel_system.oxidizer_flow_rate",
        },
        "turbopump_rpm": {
            "name": "Turbopump RPM",
            "unit": "RPM",
            "nominal_min": 28000.0,
            "nominal_max": 34000.0,
            "metric": "fuel_system.turbopump_rpm",
        },
    }

    def generate_telemetry(self) -> None:
        # ── Fault injection ────────────────────────────────────
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── Normal sensor readings ─────────────────────────────
        for sensor_key, sensor in self.SENSORS.items():
            value = random.uniform(sensor["nominal_min"], sensor["nominal_max"])
            # Add realistic noise
            noise = random.gauss(
                0, (sensor["nominal_max"] - sensor["nominal_min"]) * 0.02
            )
            value = round(value + noise, 2)
            # Clamp to nominal range in normal mode
            if not active_channels:
                value = max(sensor["nominal_min"], min(sensor["nominal_max"], value))

            self.emit_metric(sensor["metric"], value, sensor["unit"])
            self.emit_log(
                "INFO",
                f"[PMS] sensor={sensor_key} reading={value}{sensor['unit']} nominal={sensor['nominal_min']}-{sensor['nominal_max']}{sensor['unit']} status=NOMINAL",
                {
                    "operation": "sensor_reading",
                    "sensor.name": sensor_key,
                    "sensor.type": (
                        sensor_key.split("_")[0] if "_" in sensor_key else sensor_key
                    ),
                    "sensor.value": value,
                    "sensor.unit": sensor["unit"],
                    "sensor.expected_min": sensor["nominal_min"],
                    "sensor.expected_max": sensor["nominal_max"],
                    "sensor.status": "NOMINAL",
                },
            )

        # Propulsion summary
        self._check_count += 1
        self.emit_metric("fuel_system.check_count", float(self._check_count), "checks")

        if time.time() - self._last_press_summary > 10:
            self.emit_log(
                "INFO",
                f"[PMS] system_check sensors={len(self.SENSORS)} failures=0 checks={self._check_count} result=PASS status=NOMINAL",
                {
                    "operation": "system_check",
                    "check.result": "PASS",
                    "check.sensor_count": len(self.SENSORS),
                    "check.total_count": self._check_count,
                },
            )
            self._last_press_summary = time.time()
        else:
            self.emit_log(
                "INFO",
                f"[PMS] system_check sensors={len(self.SENSORS)} failures=0 result=PASS status=NOMINAL",
                {
                    "operation": "system_check",
                    "check.result": "PASS",
                    "check.sensor_count": len(self.SENSORS),
                },
            )

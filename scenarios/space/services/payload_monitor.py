"""Payload Monitor service — GCP us-central1. Satellite payload health monitoring."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class PayloadMonitorService(BaseService):
    SERVICE_NAME = "payload-monitor"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._scan_count = 0
        self._last_health_report = time.time()

    PAYLOAD_SENSORS = {
        "bay_temperature": {
            "unit": "C",
            "nominal_min": -5.0,
            "nominal_max": 35.0,
        },
        "bay_humidity": {
            "unit": "%",
            "nominal_min": 10.0,
            "nominal_max": 45.0,
        },
        "vibration_x": {
            "unit": "g",
            "nominal_min": 0.0,
            "nominal_max": 0.8,
        },
        "vibration_y": {
            "unit": "g",
            "nominal_min": 0.0,
            "nominal_max": 0.8,
        },
        "vibration_z": {
            "unit": "g",
            "nominal_min": 0.0,
            "nominal_max": 1.0,
        },
        "power_draw": {
            "unit": "W",
            "nominal_min": 120.0,
            "nominal_max": 180.0,
        },
        "data_bus_utilization": {
            "unit": "%",
            "nominal_min": 15.0,
            "nominal_max": 65.0,
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

        # ── Payload sensor readings ────────────────────────────
        all_nominal = True
        for sensor_name, sensor in self.PAYLOAD_SENSORS.items():
            value = round(
                random.uniform(sensor["nominal_min"], sensor["nominal_max"]), 2
            )
            status = "NOMINAL"

            self.emit_metric(f"payload.{sensor_name}", value, sensor["unit"])
            self.emit_log(
                "INFO",
                f"[PLD] sensor={sensor_name} reading={value}{sensor['unit']} nominal={sensor['nominal_min']}-{sensor['nominal_max']}{sensor['unit']} status=NOMINAL",
                {
                    "payload.sensor": sensor_name,
                    "payload.reading": value,
                    "payload.unit": sensor["unit"],
                    "payload.status": status,
                    "operation": "payload_reading",
                },
            )

        # ── Payload health summary ─────────────────────────────
        self._scan_count += 1
        self.emit_metric("payload.scan_count", float(self._scan_count), "scans")

        if time.time() - self._last_health_report > 10:
            self.emit_log(
                "INFO",
                f"[PLD] health_check scan={self._scan_count} sensors={len(self.PAYLOAD_SENSORS)} failures=0 satellite=READY status=NOMINAL",
                {
                    "operation": "payload_health",
                    "payload.status": "NOMINAL",
                    "payload.sensor_count": len(self.PAYLOAD_SENSORS),
                    "payload.scan_count": self._scan_count,
                },
            )
            self._last_health_report = time.time()
        else:
            self.emit_log(
                "INFO",
                f"[PLD] health_check sensors={len(self.PAYLOAD_SENSORS)} failures=0 satellite=READY status=NOMINAL",
                {
                    "operation": "payload_health",
                    "payload.status": "NOMINAL",
                    "payload.sensor_count": len(self.PAYLOAD_SENSORS),
                },
            )

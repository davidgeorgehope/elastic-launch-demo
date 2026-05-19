"""Card Printing System service — AWS us-east-1a. MES for card printing, cutting, and QC."""

from __future__ import annotations

import random

from app.services.base_service import BaseService


class CardPrintingSystemService(BaseService):
    SERVICE_NAME = "card-printing-system"

    PRODUCTION_METRICS = {
        "print_throughput": {
            "name": "Print Throughput",
            "unit": "cards/min",
            "nominal_min": 120.0,
            "nominal_max": 180.0,
            "metric": "card_printing.throughput",
        },
        "print_queue_depth": {
            "name": "Print Queue Depth",
            "unit": "jobs",
            "nominal_min": 0.0,
            "nominal_max": 50.0,
            "metric": "card_printing.queue_depth",
        },
        "ink_coverage": {
            "name": "Ink Coverage Accuracy",
            "unit": "%",
            "nominal_min": 97.0,
            "nominal_max": 100.0,
            "metric": "card_printing.ink_coverage",
        },
        "substrate_temp": {
            "name": "Substrate Temperature",
            "unit": "C",
            "nominal_min": 22.0,
            "nominal_max": 28.0,
            "metric": "card_printing.substrate_temp",
        },
    }

    def generate_telemetry(self) -> None:
        # -- Fault injection --
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Normal telemetry --
        for sensor_key, sensor in self.PRODUCTION_METRICS.items():
            value = random.uniform(sensor["nominal_min"], sensor["nominal_max"])
            noise = random.gauss(
                0, (sensor["nominal_max"] - sensor["nominal_min"]) * 0.02
            )
            value = round(value + noise, 2)
            if not active_channels:
                value = max(sensor["nominal_min"], min(sensor["nominal_max"], value))

            self.emit_metric(sensor["metric"], value, sensor["unit"])
            self.emit_log(
                "INFO",
                f"[PrintController] INFO - {sensor_key}: {value} {sensor['unit']} status=NOMINAL",
                {
                    "operation": "production_reading",
                    "sensor.name": sensor_key,
                    "sensor.value": value,
                    "sensor.unit": sensor["unit"],
                    "sensor.status": "NOMINAL",
                },
            )

        self.emit_log(
            "INFO",
            "[PrintController] INFO - production_line_check: all systems nominal throughput=156cards/min",
            {"operation": "system_check", "check.result": "PASS"},
        )

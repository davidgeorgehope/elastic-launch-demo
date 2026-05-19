"""OEE Analytics service — GCP us-central1-a. Aggregates availability x performance x quality per line/shift.

This is the executive KPI emitter for the manufacturing scenario.
"""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService
from scenarios.manufacturing.executive_kpis import emit_executive_business_metrics_if_eligible


class OEEAnalyticsService(BaseService):
    SERVICE_NAME = "oee-analytics"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._calculations_total = 0
        self._last_shift_report = time.time()
        self._lines = ["LINE-01", "LINE-02", "LINE-03", "LINE-04", "LINE-05"]
        self._shifts = ["A", "B", "C"]

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_oee_calculation()
        self._emit_throughput_event()

        if time.time() - self._last_shift_report > 10:
            self._emit_shift_summary()
            self._last_shift_report = time.time()

        self._calculations_total += 1
        self.emit_metric("oee.calculations_total", float(self._calculations_total), "calcs")
        self.emit_metric("oee.cache_hit_rate_pct", round(random.uniform(82.0, 98.5), 1), "%")
        latency = (
            random.randint(40, 280)
            if not active_channels
            else random.randint(800, 6500)
        )
        self.emit_metric("oee.calc_latency_ms", float(latency), "ms")

        emit_executive_business_metrics_if_eligible(self)

    def _emit_oee_calculation(self) -> None:
        line = random.choice(self._lines)
        availability = round(random.uniform(82.0, 96.0), 1)
        performance = round(random.uniform(85.0, 98.0), 1)
        quality = round(random.uniform(94.0, 99.5), 1)
        oee = round(availability * performance * quality / 10000, 1)
        self.emit_log(
            "INFO",
            f"[OEE] oee_calc line={line} availability={availability}% performance={performance}% quality={quality}% oee={oee}%",
            {
                "operation": "oee_calc",
                "oee.line": line,
                "oee.availability_pct": availability,
                "oee.performance_pct": performance,
                "oee.quality_pct": quality,
                "oee.overall_pct": oee,
            },
        )

    def _emit_throughput_event(self) -> None:
        line = random.choice(self._lines)
        units = random.randint(40, 220)
        target = random.randint(180, 250)
        self.emit_log(
            "INFO",
            f"[OEE] throughput_window line={line} units={units} target={target} attainment_pct={round(units / target * 100, 1)}",
            {
                "operation": "throughput_window",
                "oee.line": line,
                "oee.units_produced": units,
                "oee.target_units": target,
            },
        )

    def _emit_shift_summary(self) -> None:
        shift = random.choice(self._shifts)
        line = random.choice(self._lines)
        downtime = random.randint(2, 32)
        self.emit_log(
            "INFO",
            f"[OEE] shift_summary shift={shift} line={line} downtime_min={downtime} status=ON_TARGET",
            {
                "operation": "shift_summary",
                "oee.shift": shift,
                "oee.line": line,
                "oee.unplanned_downtime_min": downtime,
            },
        )

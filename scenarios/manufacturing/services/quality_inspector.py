"""Quality Inspector service — GCP us-central1-b. SPC, vision-inspection results, defect classification, Cpk monitoring."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class QualityInspectorService(BaseService):
    SERVICE_NAME = "quality-inspector"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._inspections_total = 0
        self._last_cpk_report = time.time()
        self._stations = ["VIS-01", "VIS-02", "VIS-03", "CMM-01", "TORQUE-01"]
        self._defect_codes = ["SCRATCH", "DIMENSION_OOT", "MISSING_FEATURE", "COSMETIC", "ASSEMBLY"]

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_inspection_event()
        self._emit_spc_sample()

        if time.time() - self._last_cpk_report > 10:
            self._emit_cpk_report()
            self._last_cpk_report = time.time()

        self._inspections_total += 1
        self.emit_metric("quality.inspections_total", float(self._inspections_total), "inspections")
        defect_rate = (
            round(random.uniform(0.4, 2.5), 2)
            if not active_channels
            else round(random.uniform(8.0, 25.0), 2)
        )
        self.emit_metric("quality.defect_rate_pct", defect_rate, "%")
        self.emit_metric("quality.first_pass_yield_pct", round(random.uniform(94.0, 99.2), 2), "%")

    def _emit_inspection_event(self) -> None:
        station = random.choice(self._stations)
        part_id = f"PT-{random.randint(100000, 999999)}"
        result = random.choice(["PASS", "PASS", "PASS", "PASS", "FAIL"])
        self.emit_log(
            "INFO",
            f"[QC] inspection station={station} part={part_id} result={result} confidence={round(random.uniform(0.92, 0.999), 4)}",
            {
                "operation": "inspection",
                "quality.station": station,
                "quality.part_id": part_id,
                "quality.result": result,
            },
        )

    def _emit_spc_sample(self) -> None:
        characteristic = random.choice(["LENGTH_MM", "DIAMETER_MM", "TORQUE_NM", "WEIGHT_G"])
        value = round(random.uniform(48.0, 52.0), 4)
        target = 50.0
        self.emit_log(
            "DEBUG",
            f"[QC] spc_sample characteristic={characteristic} value={value} target={target} usl=51.0 lsl=49.0",
            {
                "operation": "spc_sample",
                "quality.characteristic": characteristic,
                "quality.measured_value": value,
                "quality.target": target,
            },
        )

    def _emit_cpk_report(self) -> None:
        characteristic = random.choice(["LENGTH_MM", "DIAMETER_MM", "TORQUE_NM"])
        cpk = round(random.uniform(1.15, 1.95), 3)
        self.emit_log(
            "INFO",
            f"[QC] cpk_report characteristic={characteristic} cpk={cpk} sample_size={random.randint(30, 200)} status=CAPABLE",
            {
                "operation": "cpk_report",
                "quality.characteristic": characteristic,
                "quality.cpk": cpk,
            },
        )

"""OT Historian service — AWS us-east-1c. Time-series tag store integration (PI/Aveva-equivalent)."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class OTHistorianService(BaseService):
    SERVICE_NAME = "ot-historian"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._writes_total = 0
        self._last_archive_report = time.time()

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_archive_write()
        self._emit_buffer_status()

        if time.time() - self._last_archive_report > 10:
            self._emit_archive_compaction()
            self._last_archive_report = time.time()

        self._writes_total += random.randint(800, 3500)
        self.emit_metric("historian.writes_total", float(self._writes_total), "writes")
        lag = (
            round(random.uniform(0.05, 0.8), 2)
            if not active_channels
            else round(random.uniform(8.0, 45.0), 2)
        )
        self.emit_metric("historian.write_lag_seconds", lag, "s")
        self.emit_metric("historian.buffer_utilization_pct", round(random.uniform(8.0, 65.0), 1), "%")

    def _emit_archive_write(self) -> None:
        archive = random.choice(["AR-CURRENT", "AR-DAILY-01", "AR-DAILY-02"])
        batch_size = random.randint(500, 5000)
        self.emit_log(
            "INFO",
            f"[HIST] archive_write archive={archive} batch_size={batch_size} compression=LZ4 status=OK",
            {
                "operation": "archive_write",
                "historian.archive": archive,
                "historian.batch_size": batch_size,
                "historian.compression": "LZ4",
            },
        )

    def _emit_buffer_status(self) -> None:
        depth = random.randint(120, 8500)
        self.emit_log(
            "DEBUG",
            f"[HIST] buffer_status depth={depth} watermark_high=50000 watermark_low=10000",
            {
                "operation": "buffer_status",
                "historian.buffer_depth": depth,
            },
        )

    def _emit_archive_compaction(self) -> None:
        archive = random.choice(["AR-DAILY-01", "AR-DAILY-02", "AR-DAILY-03"])
        ratio = round(random.uniform(3.5, 9.8), 2)
        self.emit_log(
            "INFO",
            f"[HIST] archive_compaction archive={archive} compression_ratio={ratio}x duration_s={random.randint(8, 65)}",
            {
                "operation": "archive_compaction",
                "historian.archive": archive,
                "historian.compression_ratio": ratio,
            },
        )

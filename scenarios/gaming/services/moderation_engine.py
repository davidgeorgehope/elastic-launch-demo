"""Moderation Engine service — Azure eastus-1. Auto-moderation, player reports, and trust-safety enforcement."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class ModerationEngineService(BaseService):
    SERVICE_NAME = "moderation-engine"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._actions_taken = 0
        self._last_moderation_report = time.time()
        self._categories = ["harassment", "cheating", "hate_speech", "exploits", "spam"]
        self._model_versions = [
            "automod-v5.2",
            "automod-v5.3",
            "automod-v6.0",
            "automod-v6.1",
        ]

    def generate_telemetry(self) -> None:
        # ── Fault injection ────────────────────────────────────
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── Normal telemetry ───────────────────────────────────
        self._emit_content_scanned()
        self._emit_report_processed()

        if time.time() - self._last_moderation_report > 10:
            self._emit_moderation_summary()
            self._last_moderation_report = time.time()

        # Metrics
        scan_rate = random.randint(200, 2000)
        self.emit_metric("moderation.scan_rate", float(scan_rate), "msg/s")
        fp_rate = (
            round(random.uniform(0.5, 3.0), 2)
            if not active_channels
            else round(random.uniform(15.0, 45.0), 2)
        )
        self.emit_metric("moderation.false_positive_rate", fp_rate, "%")
        queue_depth = (
            random.randint(50, 500)
            if not active_channels
            else random.randint(5000, 50000)
        )
        self.emit_metric("moderation.report_queue_depth", float(queue_depth), "reports")
        self.emit_metric(
            "moderation.actions_taken", float(self._actions_taken), "actions"
        )

    def _emit_content_scanned(self) -> None:
        model = random.choice(self._model_versions)
        confidence = round(random.uniform(0.85, 0.99), 3)
        category = random.choice(self._categories)
        latency_ms = round(random.uniform(5.0, 30.0), 1)
        verdict = random.choice(["CLEAN", "CLEAN", "CLEAN", "FLAGGED"])
        if verdict == "FLAGGED":
            self._actions_taken += 1
        self.emit_log(
            "INFO",
            f"[T&S] content_scan model={model} verdict={verdict} category={category} confidence={confidence} latency={latency_ms}ms",
            {
                "operation": "content_scanned",
                "moderation.model": model,
                "moderation.verdict": verdict,
                "moderation.category": category,
                "moderation.confidence": confidence,
                "moderation.latency_ms": latency_ms,
            },
        )

    def _emit_report_processed(self) -> None:
        category = random.choice(self._categories)
        player_id = f"PLR-{random.randint(100000, 999999)}"
        resolution = random.choice(
            ["warning_issued", "temp_ban", "cleared", "escalated"]
        )
        wait_min = random.randint(1, 120)
        self.emit_log(
            "INFO",
            f"[T&S] report_processed player={player_id} category={category} resolution={resolution} wait={wait_min}min queue_depth=142",
            {
                "operation": "report_processed",
                "report.player_id": player_id,
                "report.category": category,
                "report.resolution": resolution,
                "report.wait_minutes": wait_min,
            },
        )

    def _emit_moderation_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[T&S] summary actions_taken={self._actions_taken} active_models={len(self._model_versions)} fp_rate=1.2% queue_depth=84",
            {
                "operation": "moderation_summary",
                "summary.actions_taken": self._actions_taken,
                "summary.active_models": len(self._model_versions),
            },
        )

"""Fraud Detector service — GCP us-central1-a. Real-time transaction screening and pattern detection."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class FraudDetectorService(BaseService):
    SERVICE_NAME = "fraud-detector"

    PATTERNS = [
        "VELOCITY",
        "GEOLOC",
        "AMOUNT",
        "WASH_TRADE",
        "LAYERING",
        "SPOOFING",
        "FRONT_RUNNING",
    ]

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._scans_total = 0
        self._last_model_report = time.time()

    def generate_telemetry(self) -> None:
        # ── Fault injection ────────────────────────────────────
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── Normal telemetry ───────────────────────────────────
        self._emit_scan_result()
        self._emit_pattern_check()

        if time.time() - self._last_model_report > 12:
            self._emit_model_performance()
            self._last_model_report = time.time()

        # Metrics
        self._scans_total += 1
        self.emit_metric(
            "fraud_detector.scans_total", float(self._scans_total), "scans"
        )
        fp_rate = (
            round(random.uniform(0.5, 3.0), 2)
            if not active_channels
            else round(random.uniform(15.0, 50.0), 2)
        )
        self.emit_metric("fraud_detector.false_positive_rate", fp_rate, "%")
        self.emit_metric(
            "fraud_detector.model_latency_ms", float(random.randint(5, 50)), "ms"
        )

    def _emit_scan_result(self) -> None:
        score = round(random.uniform(0.01, 0.35), 3)
        decision = "ALLOW" if score < 0.7 else "BLOCK"
        self.emit_log(
            "INFO",
            f"[COMPL] fraud_scan score={score} decision={decision} model=v3.2.1",
            {
                "operation": "fraud_scan",
                "fraud.score": score,
                "fraud.decision": decision,
                "fraud.model_version": "3.2.1",
            },
        )

    def _emit_pattern_check(self) -> None:
        pattern = random.choice(self.PATTERNS)
        matches = random.randint(0, 2)
        self.emit_log(
            "INFO",
            f"[COMPL] pattern_check pattern={pattern} matches={matches} status={'CLEAR' if matches == 0 else 'FLAGGED'}",
            {
                "operation": "pattern_check",
                "pattern.name": pattern,
                "pattern.matches": matches,
                "pattern.status": "CLEAR" if matches == 0 else "FLAGGED",
            },
        )

    def _emit_model_performance(self) -> None:
        precision = round(random.uniform(0.92, 0.99), 3)
        recall = round(random.uniform(0.85, 0.95), 3)
        f1 = round(2 * precision * recall / (precision + recall), 3)
        self.emit_log(
            "INFO",
            f"[COMPL] model_performance precision={precision} recall={recall} f1={f1} status=WITHIN_TARGETS",
            {
                "operation": "model_performance",
                "model.precision": precision,
                "model.recall": recall,
                "model.f1_score": f1,
            },
        )

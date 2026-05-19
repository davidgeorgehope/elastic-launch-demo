"""Fraud Sentinel service — GCP us-central1-b. Real-time fraud detection & prevention."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class FraudSentinelService(BaseService):
    SERVICE_NAME = "fraud-sentinel"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._scans_completed = 0
        self._last_summary = time.time()

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_transaction_scan()
        self._emit_model_health()

        if time.time() - self._last_summary > 10:
            self._emit_fraud_summary()
            self._last_summary = time.time()

        score = (
            round(random.uniform(0, 25), 1)
            if not active_channels
            else round(random.uniform(40, 90), 1)
        )
        self.emit_metric("fraud_sentinel.avg_risk_score", score, "score")
        self.emit_metric(
            "fraud_sentinel.scans_per_sec",
            round(random.uniform(200, 800), 1),
            "scans/s",
        )
        self.emit_metric(
            "fraud_sentinel.model_latency_ms", round(random.uniform(8, 45), 1), "ms"
        )

    def _emit_transaction_scan(self) -> None:
        self._scans_completed += 1
        risk_score = random.randint(0, 20)
        decision = "ALLOW"
        self.emit_log(
            "INFO",
            f"[FRAUD] transaction_scan score={risk_score}/100 decision={decision} model=FraudNet-v5.2 latency_ms=12 status=CLEAR",
            {
                "operation": "transaction_scan",
                "fraud.score": risk_score,
                "fraud.decision": decision,
                "fraud.model": "FraudNet-v5.2",
            },
        )

    def _emit_model_health(self) -> None:
        precision = round(random.uniform(94, 99), 1)
        recall = round(random.uniform(88, 96), 1)
        self.emit_log(
            "INFO",
            f"[FRAUD] model_health precision={precision}% recall={recall}% drift=0.02 feature_count=247 status=NOMINAL",
            {
                "operation": "model_health",
                "model.precision": precision,
                "model.recall": recall,
                "model.drift": 0.02,
            },
        )

    def _emit_fraud_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[FRAUD] sentinel_summary scans={self._scans_completed} blocked=3 fp_rate=0.08% prevented=$42,800 status=NOMINAL",
            {
                "operation": "sentinel_summary",
                "sentinel.scans": self._scans_completed,
                "sentinel.blocked": 3,
            },
        )

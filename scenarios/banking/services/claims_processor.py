"""Claims Processor service — AWS us-east-1b. Insurance claims FNOL, estimation, settlement."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class ClaimsProcessorService(BaseService):
    SERVICE_NAME = "claims-processor"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._claims_processed = 0
        self._last_summary = time.time()

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_claim_intake()
        self._emit_estimation_status()

        if time.time() - self._last_summary > 10:
            self._emit_claims_summary()
            self._last_summary = time.time()

        queue_depth = (
            random.randint(5, 50) if not active_channels else random.randint(200, 2000)
        )
        self.emit_metric("claims_processor.queue_depth", float(queue_depth), "claims")
        self.emit_metric(
            "claims_processor.avg_cycle_time_days",
            round(random.uniform(3.0, 12.0), 1),
            "days",
        )
        self.emit_metric(
            "claims_processor.photo_estimates_pending",
            float(random.randint(2, 30)),
            "estimates",
        )

    def _emit_claim_intake(self) -> None:
        self._claims_processed += 1
        claim_type = random.choice(
            ["auto_collision", "auto_comp", "property", "renters"]
        )
        severity = random.choice(["LOW", "MODERATE", "HIGH", "SEVERE"])
        self.emit_log(
            "INFO",
            f"[CLAIMS] fnol_received claim_type={claim_type} severity={severity} channel=MOBILE_APP status=INTAKE",
            {
                "operation": "fnol_received",
                "claim.type": claim_type,
                "claim.severity": severity,
                "claim.channel": "MOBILE_APP",
            },
        )

    def _emit_estimation_status(self) -> None:
        method = random.choice(["AI_PHOTO", "FIELD_ADJUSTER", "VIRTUAL_INSPECT"])
        estimate = round(random.uniform(500, 15000), 2)
        self.emit_log(
            "INFO",
            f"[CLAIMS] estimate_complete method={method} amount=${estimate} confidence=87% status=APPROVED",
            {
                "operation": "estimate_complete",
                "estimate.method": method,
                "estimate.amount": estimate,
                "estimate.confidence": 87,
            },
        )

    def _emit_claims_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[CLAIMS] pipeline_summary processed={self._claims_processed} avg_cycle=7.2d satisfaction=4.6/5.0 status=NOMINAL",
            {
                "operation": "pipeline_summary",
                "pipeline.processed": self._claims_processed,
                "pipeline.avg_cycle_days": 7.2,
            },
        )

"""Billing Engine service — AWS us-east-1b. OCS (online charging), CDR mediation, fraud guard."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class BillingEngineService(BaseService):
    SERVICE_NAME = "billing-engine"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._cdr_processed = 0
        self._last_summary = time.time()

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_ocs_transaction()
        self._emit_cdr_mediation()

        if time.time() - self._last_summary > 10:
            self._emit_billing_summary()
            self._last_summary = time.time()

        latency_ms = round(random.uniform(2, 50), 1) if not active_channels else round(random.uniform(500, 8000), 1)
        self.emit_metric("billing_engine.ocs_ccr_latency_ms", latency_ms, "ms")
        self.emit_metric("billing_engine.cdr_queue_depth", float(random.randint(0, 5000)), "records")
        self.emit_metric("billing_engine.ccr_success_rate", round(random.uniform(99.5, 99.99), 3), "%")

    def _emit_ocs_transaction(self) -> None:
        ccr_type = random.choice(["I", "U", "T"])
        result = "2001"
        quota_mb = random.randint(50, 200)
        self.emit_log(
            "INFO",
            f"[OCS] ccr_transaction type={ccr_type} result={result} quota_mb={quota_mb} "
            f"latency_ms={random.randint(5,45)} subscriber=PREPAID status=GRANTED",
            {
                "operation": "ccr_transaction",
                "ocs.ccr_type": ccr_type,
                "ocs.result_code": result,
                "ocs.quota_mb": quota_mb,
            },
        )

    def _emit_cdr_mediation(self) -> None:
        self._cdr_processed += random.randint(100, 500)
        self.emit_log(
            "INFO",
            f"[CDR] mediation_cycle processed={self._cdr_processed} parse_errors=0 "
            f"revenue_captured=${random.randint(10000,50000):,} status=NOMINAL",
            {
                "operation": "mediation_cycle",
                "cdr.processed": self._cdr_processed,
                "cdr.parse_errors": 0,
            },
        )

    def _emit_billing_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[BILL] billing_summary cdrs_today={self._cdr_processed} "
            f"ocs_availability=99.98% fraud_blocks=14 status=NOMINAL",
            {
                "operation": "billing_summary",
                "billing.cdrs_today": self._cdr_processed,
            },
        )

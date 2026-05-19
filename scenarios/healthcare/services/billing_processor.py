"""Billing Processor service — Azure eastus-1. Claims submission, eligibility verification, and revenue cycle."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService
from scenarios.healthcare.executive_kpis import emit_executive_business_metrics_if_eligible


class BillingProcessorService(BaseService):
    SERVICE_NAME = "billing-processor"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._claims_processed = 0
        self._last_batch_report = time.time()
        self._payers = [
            "BCBS-001",
            "AETNA-002",
            "UHC-003",
            "CIGNA-004",
            "MDCR-005",
            "MDCD-006",
        ]

    def generate_telemetry(self) -> None:
        # -- Fault injection ------------------------------------
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Normal telemetry -----------------------------------
        self._emit_claim_submission()
        self._emit_eligibility_check()

        if time.time() - self._last_batch_report > 10:
            self._emit_batch_status()
            self._last_batch_report = time.time()

        # Metrics
        self._claims_processed += 1
        self.emit_metric(
            "billing.claims_processed", float(self._claims_processed), "claims"
        )
        denial_rate = (
            round(random.uniform(2.0, 8.0), 1)
            if not active_channels
            else round(random.uniform(15.0, 40.0), 1)
        )
        self.emit_metric("billing.denial_rate_pct", denial_rate, "%")
        self.emit_metric(
            "billing.avg_reimbursement_days", float(random.randint(14, 45)), "days"
        )

        emit_executive_business_metrics_if_eligible(self)

    def _emit_claim_submission(self) -> None:
        claim_id = f"CLM-{random.randint(100000, 999999)}"
        payer = random.choice(self._payers)
        charges = round(random.uniform(500.0, 50000.0), 2)
        dx_code = random.choice(["I10", "E11.9", "J18.1", "M54.5", "K21.0", "N39.0"])
        self.emit_log(
            "INFO",
            f"[CLAIMS] x12_837_submit claim={claim_id} payer={payer} charges=${charges:.2f} dx={dx_code} status=ACCEPTED",
            {
                "operation": "claim_submission",
                "billing.claim_id": claim_id,
                "billing.payer": payer,
                "billing.charges": charges,
                "billing.dx_code": dx_code,
                "billing.status": "SUBMITTED",
            },
        )

    def _emit_eligibility_check(self) -> None:
        payer = random.choice(self._payers)
        patient_id = f"PT-{random.randint(100000, 999999)}"
        response_ms = random.randint(200, 1500)
        status = random.choice(["ELIGIBLE", "ELIGIBLE", "ELIGIBLE", "NEEDS_AUTH"])
        self.emit_log(
            "INFO",
            f"[CLAIMS] x12_271_response patient={patient_id} payer={payer} eligibility={status} response_ms={response_ms}",
            {
                "operation": "eligibility_check",
                "billing.payer": payer,
                "billing.patient_id": patient_id,
                "billing.eligibility_status": status,
                "billing.response_ms": response_ms,
            },
        )

    def _emit_batch_status(self) -> None:
        batch_id = f"BATCH-{random.randint(1000, 9999)}"
        batch_size = random.randint(50, 300)
        accepted = int(batch_size * random.uniform(0.88, 0.98))
        self.emit_log(
            "INFO",
            f"[CLAIMS] batch_status batch={batch_id} accepted={accepted}/{batch_size} total_processed={self._claims_processed} rcm=ON_TRACK",
            {
                "operation": "batch_status",
                "billing.batch_id": batch_id,
                "billing.batch_size": batch_size,
                "billing.accepted": accepted,
                "billing.total_processed": self._claims_processed,
            },
        )

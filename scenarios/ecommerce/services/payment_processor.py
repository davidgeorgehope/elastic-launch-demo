"""Payment Processor service — Azure eastus-1. Payment authorization, capture, and fraud detection."""

from __future__ import annotations

import random

from app.services.base_service import BaseService


class PaymentProcessorService(BaseService):
    SERVICE_NAME = "payment-processor"

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        transactions_per_min = round(random.uniform(90.0, 380.0), 1)
        success_rate_pct = round(random.uniform(97.5, 99.7), 2)
        avg_processing_ms = round(random.uniform(180.0, 850.0), 1)
        fraud_block_rate_pct = round(random.uniform(0.3, 1.8), 3)

        self.emit_metric("payments.transactions_per_min", transactions_per_min, "txn/min")
        self.emit_metric("payments.success_rate_pct", success_rate_pct, "%")
        self.emit_metric("payments.avg_processing_ms", avg_processing_ms, "ms")
        self.emit_metric("payments.fraud_block_rate_pct", fraud_block_rate_pct, "%")

        self.emit_log(
            "INFO",
            f"payments.health txn_per_min={transactions_per_min} success_rate={success_rate_pct}% "
            f"avg_processing_ms={avg_processing_ms} fraud_block_rate={fraud_block_rate_pct}%",
            {
                "operation": "payments_health",
                "payments.transactions_per_min": transactions_per_min,
                "payments.success_rate_pct": success_rate_pct,
                "payments.avg_processing_ms": avg_processing_ms,
                "payments.fraud_block_rate_pct": fraud_block_rate_pct,
            },
        )

        gateway_latency_ms = round(random.uniform(120.0, 600.0), 1)
        provider = random.choice(["stripe", "adyen", "braintree"])
        self.emit_log(
            "INFO",
            f"payments.gateway_health provider={provider} latency_ms={gateway_latency_ms} status=HEALTHY",
            {
                "operation": "gateway_health",
                "payments.gateway_provider": provider,
                "payments.gateway_latency_ms": gateway_latency_ms,
                "payments.gateway_status": "HEALTHY",
            },
        )

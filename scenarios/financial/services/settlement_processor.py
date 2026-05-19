"""Settlement Processor service — GCP us-central1-b. T+2 trade settlement and netting."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class SettlementProcessorService(BaseService):
    SERVICE_NAME = "settlement-processor"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._settlements_processed = 0
        self._last_netting_run = time.time()

    def generate_telemetry(self) -> None:
        # ── Fault injection ────────────────────────────────────
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── Normal telemetry ───────────────────────────────────
        self._emit_settlement_progress()
        self._emit_obligation_status()

        if time.time() - self._last_netting_run > 15:
            self._emit_netting_run()
            self._last_netting_run = time.time()

        # Metrics
        self._settlements_processed += 1
        self.emit_metric(
            "settlement.processed_count",
            float(self._settlements_processed),
            "settlements",
        )
        pending = (
            random.randint(10, 200)
            if not active_channels
            else random.randint(200, 2000)
        )
        self.emit_metric("settlement.pending_count", float(pending), "settlements")
        self.emit_metric(
            "settlement.fail_rate",
            (
                round(random.uniform(0.1, 1.5), 2)
                if not active_channels
                else round(random.uniform(5.0, 20.0), 2)
            ),
            "%",
        )

    def _emit_settlement_progress(self) -> None:
        counterparty = random.choice(
            ["Goldman Sachs", "Morgan Stanley", "JP Morgan", "Citadel"]
        )
        instrument = random.choice(["US.AAPL", "US.GOOGL", "FUT.ES", "FX.EURUSD"])
        qty = random.randint(100, 10000)
        value = round(qty * random.uniform(50, 400), 2)
        self.emit_log(
            "INFO",
            f"[SETTLE] settlement_processed instrument={instrument} qty={qty} value=${value} counterparty={counterparty} status=SETTLED",
            {
                "operation": "settlement_process",
                "settlement.instrument": instrument,
                "settlement.quantity": qty,
                "settlement.value": value,
                "settlement.counterparty": counterparty,
                "settlement.status": "SETTLED",
            },
        )

    def _emit_obligation_status(self) -> None:
        net_payable = round(random.uniform(1000000, 50000000), 2)
        net_receivable = round(random.uniform(1000000, 50000000), 2)
        self.emit_log(
            "INFO",
            f"[SETTLE] obligation_status payable=${net_payable:,.2f} receivable=${net_receivable:,.2f} status=BALANCED",
            {
                "operation": "obligation_status",
                "obligation.net_payable": net_payable,
                "obligation.net_receivable": net_receivable,
            },
        )

    def _emit_netting_run(self) -> None:
        batches = random.randint(5, 20)
        counterparties = random.randint(10, 50)
        reduction_pct = round(random.uniform(60, 90), 1)
        self.emit_log(
            "INFO",
            f"[SETTLE] netting_run batches={batches} counterparties={counterparties} reduction_pct={reduction_pct} status=COMPLETE",
            {
                "operation": "netting_run",
                "netting.batch_count": batches,
                "netting.counterparty_count": counterparties,
                "netting.reduction_pct": reduction_pct,
            },
        )

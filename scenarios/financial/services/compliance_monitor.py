"""Compliance Monitor service — Azure eastus-1. Regulatory reporting and AML screening."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class ComplianceMonitorService(BaseService):
    SERVICE_NAME = "compliance-monitor"

    REGULATIONS = ["MiFID-II", "Dodd-Frank", "EMIR", "MAR", "SFTR", "CAT"]
    REPORT_TYPES = ["EMIR-TR", "MiFID-II-RTS25", "CAT-FINRA", "SFTR", "SEC-13F"]

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._last_reg_check = time.time()
        self._screenings_total = 0

    def generate_telemetry(self) -> None:
        # ── Fault injection ────────────────────────────────────
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── Normal telemetry ───────────────────────────────────
        self._emit_screening_result()
        self._emit_watchlist_check()

        if time.time() - self._last_reg_check > 10:
            self._emit_regulatory_status()
            self._last_reg_check = time.time()

        # Metrics
        self._screenings_total += 1
        self.emit_metric(
            "compliance.screenings_total", float(self._screenings_total), "screenings"
        )
        self.emit_metric(
            "compliance.aml_latency_ms",
            float(random.randint(50, 500)),
            "ms",
        )
        self.emit_metric(
            "compliance.pending_reports",
            float(random.randint(0, 5)),
            "reports",
        )

    def _emit_screening_result(self) -> None:
        result = random.choice(["CLEAR", "CLEAR", "CLEAR", "CLEAR", "REVIEW"])
        latency_ms = random.randint(50, 500)
        self.emit_log(
            "INFO",
            f"[COMPL] aml_screening result={result} latency_ms={latency_ms} sla_met=true",
            {
                "operation": "aml_screening",
                "screening.result": result,
                "screening.latency_ms": latency_ms,
                "screening.sla_met": True,
            },
        )

    def _emit_watchlist_check(self) -> None:
        entries_checked = random.randint(1000, 10000)
        hits = random.randint(0, 1)
        self.emit_log(
            "INFO",
            f"[COMPL] watchlist_check entries_checked={entries_checked} hits={hits} status={'REVIEW_PENDING' if hits else 'CLEAR'}",
            {
                "operation": "watchlist_check",
                "watchlist.entries_checked": entries_checked,
                "watchlist.hits": hits,
            },
        )

    def _emit_regulatory_status(self) -> None:
        regulation = random.choice(self.REGULATIONS)
        report = random.choice(self.REPORT_TYPES)
        self.emit_log(
            "INFO",
            f"[COMPL] regulatory_status regulation={regulation} report={report} status=COMPLIANT",
            {
                "operation": "regulatory_status",
                "regulation.name": regulation,
                "regulation.report": report,
                "regulation.status": "COMPLIANT",
            },
        )

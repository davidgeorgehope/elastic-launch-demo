"""Audit Logger service — Azure eastus-1. Immutable audit trail and cross-region replication."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class AuditLoggerService(BaseService):
    SERVICE_NAME = "audit-logger"

    STREAMS = ["orders", "trades", "settlements", "risk-events", "compliance-alerts"]

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._events_logged = 0
        self._last_integrity_check = time.time()
        self._sequence_counters = {
            s: random.randint(1000000, 5000000) for s in self.STREAMS
        }

    def generate_telemetry(self) -> None:
        # ── Fault injection ────────────────────────────────────
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── Normal telemetry ───────────────────────────────────
        self._emit_audit_event()
        self._emit_replication_status()

        if time.time() - self._last_integrity_check > 12:
            self._emit_integrity_check()
            self._last_integrity_check = time.time()

        # Metrics
        self._events_logged += 1
        self.emit_metric(
            "audit_logger.events_logged", float(self._events_logged), "events"
        )
        self.emit_metric(
            "audit_logger.replication_lag_ms",
            float(random.randint(50, 800)),
            "ms",
        )
        self.emit_metric(
            "audit_logger.storage_used_gb",
            round(random.uniform(100, 500), 1),
            "GB",
        )

    def _emit_audit_event(self) -> None:
        stream = random.choice(self.STREAMS)
        self._sequence_counters[stream] += 1
        seq = self._sequence_counters[stream]
        event_type = random.choice(
            [
                "ORDER_NEW",
                "ORDER_CANCEL",
                "TRADE_EXEC",
                "SETTLEMENT_INIT",
                "RISK_CHECK",
                "COMPLIANCE_ALERT",
            ]
        )
        self.emit_log(
            "INFO",
            f"[AUDIT] event_logged stream={stream} seq={seq} type={event_type} status=COMMITTED",
            {
                "operation": "audit_log",
                "audit.stream": stream,
                "audit.sequence": seq,
                "audit.event_type": event_type,
                "audit.status": "COMMITTED",
            },
        )

    def _emit_replication_status(self) -> None:
        lag_ms = random.randint(50, 800)
        dest = random.choice(["eu-west-1", "us-west-2"])
        self.emit_log(
            "INFO",
            f"[AUDIT] replication_status source=eastus dest={dest} lag_ms={lag_ms} status=SYNCED",
            {
                "operation": "replication_status",
                "replication.source": "eastus",
                "replication.destination": dest,
                "replication.lag_ms": lag_ms,
                "replication.status": "SYNCED",
            },
        )

    def _emit_integrity_check(self) -> None:
        streams_ok = len(self.STREAMS)
        total_events = sum(self._sequence_counters.values())
        self.emit_log(
            "INFO",
            f"[AUDIT] integrity_check streams_valid={streams_ok}/{streams_ok} total_events={total_events} hash_chain=VALID",
            {
                "operation": "integrity_check",
                "integrity.streams_valid": streams_ok,
                "integrity.total_events": total_events,
                "integrity.hash_chain": "VALID",
            },
        )

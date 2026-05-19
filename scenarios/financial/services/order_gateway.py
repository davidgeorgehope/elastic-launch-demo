"""Order Gateway service — AWS us-east-1a. FIX protocol order ingestion and routing."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class OrderGatewayService(BaseService):
    SERVICE_NAME = "order-gateway"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._order_count = 0
        self._last_throughput_report = time.time()
        self._fix_sessions = [
            "FIX-NYSE-01",
            "FIX-NSDQ-01",
            "FIX-CBOE-01",
            "FIX-CME-01",
            "FIX-BATS-01",
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
        self._emit_order_flow()
        self._emit_fix_session_status()

        if time.time() - self._last_throughput_report > 10:
            self._emit_throughput_report()
            self._last_throughput_report = time.time()

        # Metrics
        self.emit_metric(
            "order_gateway.orders_received",
            float(self._order_count),
            "orders",
        )
        self.emit_metric(
            "order_gateway.active_fix_sessions",
            float(len(self._fix_sessions)),
            "sessions",
        )
        reject_rate = (
            round(random.uniform(0.1, 2.5), 2)
            if not active_channels
            else round(random.uniform(8.0, 25.0), 2)
        )
        self.emit_metric(
            "order_gateway.reject_rate",
            reject_rate,
            "%",
        )

    def _emit_order_flow(self) -> None:
        self._order_count += 1
        side = random.choice(["BUY", "SELL"])
        symbol = random.choice(["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"])
        qty = random.randint(100, 5000)
        price = round(random.uniform(100.0, 400.0), 2)
        latency_us = random.randint(15, 150)
        self.emit_log(
            "INFO",
            f"[OMS] order_received side={side} qty={qty} symbol={symbol} price=${price} latency_us={latency_us} status=ROUTED",
            {
                "operation": "order_received",
                "order.side": side,
                "order.symbol": symbol,
                "order.quantity": qty,
                "order.price": price,
                "order.latency_us": latency_us,
                "order.status": "ROUTED",
            },
        )

    def _emit_fix_session_status(self) -> None:
        session = random.choice(self._fix_sessions)
        heartbeat_ms = round(random.uniform(0.5, 3.0), 1)
        self.emit_log(
            "INFO",
            f"[OMS] fix_heartbeat session={session} latency_ms={heartbeat_ms} status=ACTIVE",
            {
                "operation": "fix_heartbeat",
                "fix.session": session,
                "fix.heartbeat_ms": heartbeat_ms,
                "fix.status": "ACTIVE",
            },
        )

    def _emit_throughput_report(self) -> None:
        self.emit_log(
            "INFO",
            f"[OMS] throughput_report total_orders={self._order_count} active_sessions={len(self._fix_sessions)} status=NOMINAL",
            {
                "operation": "throughput_report",
                "throughput.total_orders": self._order_count,
                "throughput.active_sessions": len(self._fix_sessions),
            },
        )

"""Customer Portal service — Azure eastus-2. Client-facing trading UI and portfolio management."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class CustomerPortalService(BaseService):
    SERVICE_NAME = "customer-portal"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._active_sessions = random.randint(200, 500)
        self._last_session_report = time.time()

    def generate_telemetry(self) -> None:
        # ── Fault injection ────────────────────────────────────
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── Normal telemetry ───────────────────────────────────
        self._emit_client_action()
        self._emit_portfolio_update()

        if time.time() - self._last_session_report > 10:
            self._emit_session_summary()
            self._last_session_report = time.time()

        # Metrics
        self._active_sessions += random.randint(-5, 5)
        self._active_sessions = max(100, self._active_sessions)
        self.emit_metric(
            "customer_portal.active_sessions", float(self._active_sessions), "sessions"
        )
        self.emit_metric(
            "customer_portal.page_load_ms",
            float(random.randint(50, 300)),
            "ms",
        )
        self.emit_metric(
            "customer_portal.api_error_rate",
            (
                round(random.uniform(0.01, 0.5), 3)
                if not active_channels
                else round(random.uniform(2.0, 10.0), 3)
            ),
            "%",
        )

    def _emit_client_action(self) -> None:
        action = random.choice(
            [
                "view_portfolio",
                "place_order",
                "check_positions",
                "view_pnl",
                "market_data_stream",
                "download_statement",
            ]
        )
        latency_ms = random.randint(20, 200)
        self.emit_log(
            "INFO",
            f"[PORTAL] client_action action={action} latency_ms={latency_ms} http_status=200",
            {
                "operation": "client_action",
                "action.type": action,
                "action.latency_ms": latency_ms,
                "action.http_status": 200,
            },
        )

    def _emit_portfolio_update(self) -> None:
        portfolio_id = f"PF-{random.randint(10000, 99999)}"
        positions = random.randint(10, 200)
        total_value = round(random.uniform(100000, 50000000), 2)
        pnl_pct = round(random.uniform(-2.0, 5.0), 2)
        self.emit_log(
            "INFO",
            f"[PORTAL] portfolio_update portfolio={portfolio_id} positions={positions} value=${total_value:,.2f} pnl={pnl_pct:+.2f}%",
            {
                "operation": "portfolio_update",
                "portfolio.id": portfolio_id,
                "portfolio.positions": positions,
                "portfolio.total_value": total_value,
                "portfolio.pnl_pct": pnl_pct,
            },
        )

    def _emit_session_summary(self) -> None:
        expired = random.randint(0, 5)
        self.emit_log(
            "INFO",
            f"[PORTAL] session_summary active={self._active_sessions} expired={expired} status=NOMINAL",
            {
                "operation": "session_summary",
                "session.active": self._active_sessions,
                "session.expired": expired,
                "session.status": "NOMINAL",
            },
        )

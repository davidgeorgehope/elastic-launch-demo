"""Customer Portal service — GCP us-central1-a. Mi Claro self-care web and app portal."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class CustomerPortalService(BaseService):
    SERVICE_NAME = "customer-portal"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._api_calls = 0
        self._last_summary = time.time()
        self._endpoints = [
            "/api/v1/account/balance",
            "/api/v1/recharge",
            "/api/v1/plan/change",
            "/api/v1/support/ticket",
            "/api/v1/account/login",
        ]

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_api_request()
        self._emit_session_health()

        if time.time() - self._last_summary > 10:
            self._emit_portal_summary()
            self._last_summary = time.time()

        latency_ms = round(random.uniform(80, 400), 1) if not active_channels else round(random.uniform(3000, 15000), 1)
        self.emit_metric("customer_portal.api_latency_ms", latency_ms, "ms")
        self.emit_metric("customer_portal.active_sessions", float(random.randint(500000, 2000000)), "sessions")
        self.emit_metric("customer_portal.auth_success_rate", round(random.uniform(99.2, 99.9), 2), "%")

    def _emit_api_request(self) -> None:
        self._api_calls += 1
        endpoint = random.choice(self._endpoints)
        country = random.choice(["BR", "CO", "AR", "MX"])
        status = 200
        self.emit_log(
            "INFO",
            f"[PORTAL] api_request endpoint={endpoint} country={country} "
            f"status={status} latency_ms={random.randint(50,350)} platform=mobile status=OK",
            {
                "operation": "api_request",
                "portal.endpoint": endpoint,
                "portal.country": country,
                "portal.status": status,
            },
        )

    def _emit_session_health(self) -> None:
        active = random.randint(500000, 2000000)
        self.emit_log(
            "INFO",
            f"[PORTAL] session_health active={active:,} idp=OK redis=OK "
            f"sso=OK rate_limit_events=0 status=NOMINAL",
            {
                "operation": "session_health",
                "portal.active_sessions": active,
            },
        )

    def _emit_portal_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[PORTAL] portal_summary api_calls={self._api_calls} "
            f"auth_rate=99.7% recharges_today=142K plan_changes=18K status=NOMINAL",
            {
                "operation": "portal_summary",
                "portal.api_calls": self._api_calls,
            },
        )

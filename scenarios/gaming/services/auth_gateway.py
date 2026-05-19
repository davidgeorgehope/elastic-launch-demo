"""Auth Gateway service — GCP us-central1-a. OAuth token management, session validation, and fraud detection."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class AuthGatewayService(BaseService):
    SERVICE_NAME = "auth-gateway"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._auth_requests = 0
        self._last_auth_report = time.time()
        self._providers = [
            "oauth-google",
            "oauth-discord",
            "oauth-steam",
            "oauth-epic",
            "email-password",
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
        self._emit_auth_request()
        self._emit_token_validation()

        if time.time() - self._last_auth_report > 10:
            self._emit_auth_summary()
            self._last_auth_report = time.time()

        # Metrics
        auth_latency = (
            round(random.uniform(10.0, 60.0), 1)
            if not active_channels
            else round(random.uniform(200.0, 2000.0), 1)
        )
        self.emit_metric("auth.request_latency_ms", auth_latency, "ms")
        self.emit_metric("auth.total_requests", float(self._auth_requests), "requests")
        active_sessions = random.randint(20000, 150000)
        self.emit_metric("auth.active_sessions", float(active_sessions), "sessions")
        token_refresh_rate = (
            random.randint(100, 1500)
            if not active_channels
            else random.randint(5000, 50000)
        )
        self.emit_metric("auth.token_refresh_rate", float(token_refresh_rate), "req/s")

    def _emit_auth_request(self) -> None:
        self._auth_requests += 1
        provider = random.choice(self._providers)
        latency_ms = round(random.uniform(15.0, 80.0), 1)
        player_id = f"PLR-{random.randint(100000, 999999)}"
        self.emit_log(
            "INFO",
            f"[Auth] login provider={provider} player={player_id} latency={latency_ms}ms result=SUCCESS session_created=true",
            {
                "operation": "auth_request",
                "auth.provider": provider,
                "auth.player_id": player_id,
                "auth.latency_ms": latency_ms,
                "auth.result": "SUCCESS",
            },
        )

    def _emit_token_validation(self) -> None:
        token_age_min = random.randint(1, 55)
        ttl_min = 60 - token_age_min
        session_id = f"SESS-{random.randint(10000000, 99999999)}"
        self.emit_log(
            "INFO",
            f"[Auth] token_validate session={session_id} age={token_age_min}min ttl={ttl_min}min status=VALID algo=RS256",
            {
                "operation": "token_validation",
                "token.session_id": session_id,
                "token.age_min": token_age_min,
                "token.ttl_min": ttl_min,
                "token.status": "VALID",
            },
        )

    def _emit_auth_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[Auth] summary total_requests={self._auth_requests} providers={len(self._providers)} active_sessions=84201 refresh_rate=412/s",
            {
                "operation": "auth_summary",
                "summary.total_requests": self._auth_requests,
                "summary.provider_count": len(self._providers),
            },
        )

"""Auth Gateway service — GCP us-central1-c. Member auth, biometrics, MFA."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class AuthGatewayService(BaseService):
    SERVICE_NAME = "auth-gateway"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._auth_count = 0
        self._last_summary = time.time()

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_auth_event()
        self._emit_mfa_status()

        if time.time() - self._last_summary > 10:
            self._emit_auth_summary()
            self._last_summary = time.time()

        auth_rate = (
            round(random.uniform(98, 99.9), 2)
            if not active_channels
            else round(random.uniform(60, 85), 2)
        )
        self.emit_metric("auth_gateway.success_rate", auth_rate, "%")
        self.emit_metric(
            "auth_gateway.active_sessions",
            float(random.randint(40000, 120000)),
            "sessions",
        )
        self.emit_metric(
            "auth_gateway.mfa_delivery_rate", round(random.uniform(95, 99.5), 1), "%"
        )

    def _emit_auth_event(self) -> None:
        self._auth_count += 1
        method = random.choice(["FACE_ID", "FINGERPRINT", "PIN", "PASSWORD", "SSO"])
        latency_ms = round(random.uniform(50, 300), 1)
        self.emit_log(
            "INFO",
            f"[AUTH] auth_verified method={method} latency_ms={latency_ms} mfa=true device_trusted=true status=SUCCESS",
            {
                "operation": "auth_verified",
                "auth.method": method,
                "auth.latency_ms": latency_ms,
                "auth.mfa": True,
                "auth.status": "SUCCESS",
            },
        )

    def _emit_mfa_status(self) -> None:
        channel = random.choice(["SMS", "PUSH", "TOTP", "EMAIL"])
        delivery_ms = round(random.uniform(200, 2000), 1)
        self.emit_log(
            "INFO",
            f"[AUTH] mfa_delivered channel={channel} delivery_ms={delivery_ms} provider=Twilio status=DELIVERED",
            {
                "operation": "mfa_delivered",
                "mfa.channel": channel,
                "mfa.delivery_ms": delivery_ms,
                "mfa.status": "DELIVERED",
            },
        )

    def _emit_auth_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[AUTH] gateway_summary total_auths={self._auth_count} biometric_pct=72% mfa_pct=98% fraud_flags=0 status=NOMINAL",
            {
                "operation": "gateway_summary",
                "auth.total": self._auth_count,
                "auth.biometric_pct": 72,
            },
        )

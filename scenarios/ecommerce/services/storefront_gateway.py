"""Storefront Gateway service — AWS us-east-1a. Customer-facing web and mobile entry point."""

from __future__ import annotations

import random

from app.services.base_service import BaseService


class StorefrontGatewayService(BaseService):
    SERVICE_NAME = "storefront-gateway"

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        active_sessions = random.randint(8000, 45000)
        page_load_ms = round(random.uniform(180.0, 650.0), 1)
        bounce_rate = round(random.uniform(18.0, 35.0), 2)
        requests_per_sec = round(random.uniform(800.0, 3500.0), 1)

        self.emit_metric("storefront.active_sessions", float(active_sessions), "sessions")
        self.emit_metric("storefront.page_load_ms", page_load_ms, "ms")
        self.emit_metric("storefront.bounce_rate_pct", bounce_rate, "%")
        self.emit_metric("storefront.requests_per_sec", requests_per_sec, "rps")

        self.emit_log(
            "INFO",
            f"storefront.health active_sessions={active_sessions} page_load_ms={page_load_ms} "
            f"bounce_rate={bounce_rate}% rps={requests_per_sec}",
            {
                "operation": "storefront_health",
                "storefront.active_sessions": active_sessions,
                "storefront.page_load_ms": page_load_ms,
                "storefront.bounce_rate_pct": bounce_rate,
                "storefront.rps": requests_per_sec,
            },
        )

        device_split = {"mobile": random.randint(45, 60), "desktop": random.randint(30, 45), "app": random.randint(5, 15)}
        self.emit_log(
            "INFO",
            f"storefront.device_split mobile={device_split['mobile']}% desktop={device_split['desktop']}% app={device_split['app']}%",
            {"operation": "device_split", **{f"storefront.device_{k}_pct": v for k, v in device_split.items()}},
        )

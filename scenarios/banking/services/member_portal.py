"""Member Portal service — Azure eastus-2. Web portal & account management."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService
from scenarios.banking.executive_kpis import emit_executive_business_metrics_if_eligible


class MemberPortalService(BaseService):
    SERVICE_NAME = "member-portal"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._page_views = 0
        self._last_summary = time.time()

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_page_view()
        self._emit_account_activity()

        if time.time() - self._last_summary > 10:
            self._emit_portal_summary()
            self._last_summary = time.time()

        active_users = random.randint(5000, 20000)
        self.emit_metric("member_portal.active_users", float(active_users), "users")
        self.emit_metric(
            "member_portal.page_load_ms", round(random.uniform(200, 800), 1), "ms"
        )
        self.emit_metric(
            "member_portal.session_duration_min", round(random.uniform(3, 25), 1), "min"
        )

        emit_executive_business_metrics_if_eligible(self)

    def _emit_page_view(self) -> None:
        self._page_views += 1
        page = random.choice(
            [
                "/dashboard",
                "/accounts",
                "/insurance/auto",
                "/claims/status",
                "/payments/bill-pay",
                "/investments",
            ]
        )
        load_ms = round(random.uniform(150, 600), 1)
        self.emit_log(
            "INFO",
            f"[PORTAL] page_view page={page} load_ms={load_ms} cdn_hit=true render_ms=42 status=200",
            {
                "operation": "page_view",
                "portal.page": page,
                "portal.load_ms": load_ms,
                "portal.cdn_hit": True,
            },
        )

    def _emit_account_activity(self) -> None:
        action = random.choice(
            [
                "VIEW_BALANCE",
                "DOWNLOAD_STATEMENT",
                "UPDATE_PROFILE",
                "VIEW_POLICY",
                "START_CLAIM",
                "SCHEDULE_PAYMENT",
            ]
        )
        self.emit_log(
            "INFO",
            f"[PORTAL] member_action action={action} auth_level=FULL session_valid=true status=COMPLETED",
            {
                "operation": "member_action",
                "portal.action": action,
                "portal.auth_level": "FULL",
            },
        )

    def _emit_portal_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[PORTAL] summary page_views={self._page_views} avg_load_ms=340 error_rate=0.01% satisfaction=4.7/5.0 status=NOMINAL",
            {
                "operation": "portal_summary",
                "portal.page_views": self._page_views,
                "portal.avg_load_ms": 340,
            },
        )

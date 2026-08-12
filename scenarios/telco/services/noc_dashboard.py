"""NOC Dashboard service — Azure eastus-3. Alert manager, incident tracking, BGP monitoring."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class NocDashboardService(BaseService):
    SERVICE_NAME = "noc-dashboard"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._incidents_created = 0
        self._last_summary = time.time()

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_alert_health()
        self._emit_bgp_status()

        if time.time() - self._last_summary > 10:
            self._emit_noc_summary()
            self._last_summary = time.time()

        alert_rate = float(random.randint(5, 40)) if not active_channels else float(random.randint(800, 2400))
        self.emit_metric("noc_dashboard.alert_rate_per_min", alert_rate, "alerts/min")
        self.emit_metric("noc_dashboard.active_incidents", float(random.randint(0, 8)), "incidents")
        self.emit_metric("noc_dashboard.bgp_peer_count", float(random.randint(280, 320)), "peers")

    def _emit_alert_health(self) -> None:
        active_alerts = random.randint(10, 80)
        correlated_pct = round(random.uniform(88, 96), 1)
        self.emit_log(
            "INFO",
            f"[NOC] alert_health active={active_alerts} p1=0 p2=2 p3={active_alerts-2} "
            f"correlated={correlated_pct}% mtta_min=3.2 status=NOMINAL",
            {
                "operation": "alert_health",
                "noc.active_alerts": active_alerts,
                "noc.correlated_pct": correlated_pct,
            },
        )

    def _emit_bgp_status(self) -> None:
        peer_count = random.randint(290, 310)
        established = peer_count - random.randint(0, 2)
        self.emit_log(
            "INFO",
            f"[BGP] peer_status total={peer_count} established={established} "
            f"flaps_1h=0 prefixes_received=842K rpki_valid=99.8% status=NOMINAL",
            {
                "operation": "peer_status",
                "bgp.peer_count": peer_count,
                "bgp.established": established,
            },
        )

    def _emit_noc_summary(self) -> None:
        self._incidents_created += random.choice([0, 0, 0, 1])
        self.emit_log(
            "INFO",
            f"[NOC] noc_summary incidents_today={self._incidents_created} "
            f"mttr_min=12.4 p1_sla_breach=0 network_availability=99.98% status=NOMINAL",
            {
                "operation": "noc_summary",
                "noc.incidents_today": self._incidents_created,
                "noc.network_availability": 99.98,
            },
        )

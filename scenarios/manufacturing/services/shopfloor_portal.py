"""Shopfloor Portal service — Azure eastus-2. Operator HMI in a Docker container, kiosk/tablet endpoint."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class ShopfloorPortalService(BaseService):
    SERVICE_NAME = "shopfloor-portal"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._sessions_total = 0
        self._last_container_report = time.time()
        self._kiosks = ["KIOSK-LINE01-01", "KIOSK-LINE02-01", "KIOSK-LINE03-01", "TABLET-MGR-01"]

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_session_event()
        self._emit_request_event()

        if time.time() - self._last_container_report > 10:
            self._emit_container_metrics()
            self._last_container_report = time.time()

        self._sessions_total += 1
        self.emit_metric("portal.sessions_total", float(self._sessions_total), "sessions")
        self.emit_metric("portal.active_kiosks", float(len(self._kiosks)), "kiosks")
        latency = (
            random.randint(40, 220)
            if not active_channels
            else random.randint(800, 5500)
        )
        self.emit_metric("portal.request_latency_ms", float(latency), "ms")
        self.emit_metric("portal.container_memory_mb", float(random.randint(180, 750)), "MB")

    def _emit_session_event(self) -> None:
        kiosk = random.choice(self._kiosks)
        operator = f"OP-{random.randint(1000, 9999)}"
        action = random.choice(["login", "scan_part", "submit_inspection", "report_issue", "logout"])
        self.emit_log(
            "INFO",
            f"[PORTAL] session kiosk={kiosk} operator={operator} action={action}",
            {
                "operation": "session_event",
                "portal.kiosk": kiosk,
                "portal.operator": operator,
                "portal.action": action,
            },
        )

    def _emit_request_event(self) -> None:
        endpoint = random.choice(["/api/scan", "/api/work-orders", "/api/inspections", "/api/issues"])
        method = random.choice(["GET", "POST"])
        status = random.choice([200, 200, 200, 200, 201, 304])
        self.emit_log(
            "DEBUG",
            f"[PORTAL] http_request method={method} path={endpoint} status={status} latency_ms={random.randint(15, 180)}",
            {
                "operation": "http_request",
                "http.method": method,
                "http.target": endpoint,
                "http.status_code": status,
            },
        )

    def _emit_container_metrics(self) -> None:
        container = "shopfloor-portal-7c8d9f4b6-xq8jt"
        image = "registry.mfg.internal/shopfloor-portal:1.18.3"
        restarts = random.choice([0, 0, 0, 0, 1])
        self.emit_log(
            "INFO",
            f"[PORTAL-K8S] container={container} image={image} restarts={restarts} memory_mb={random.randint(180, 600)} cpu_pct={random.randint(2, 28)}",
            {
                "operation": "container_status",
                "k8s.pod.name": container,
                "container.image.name": image,
                "container.restart_count": restarts,
            },
        )

"""ERP Bridge service — Azure eastus-1. SAP/Oracle ERP integration on Windows Server. Emits Windows event log entries."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class ERPBridgeService(BaseService):
    SERVICE_NAME = "erp-bridge"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._idoc_total = 0
        self._last_health_report = time.time()
        self._win_services = ["SAPHostControl", "SAPHostExec", "MSSQLSERVER", "MSExchangeIS"]

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_idoc_transaction()
        self._emit_windows_event_log()

        if time.time() - self._last_health_report > 10:
            self._emit_service_health()
            self._last_health_report = time.time()

        self._idoc_total += 1
        self.emit_metric("erp.idocs_processed", float(self._idoc_total), "idocs")
        self.emit_metric("erp.queue_depth", float(random.randint(2, 35)), "messages")
        latency = (
            random.randint(80, 450)
            if not active_channels
            else random.randint(2_000, 18_000)
        )
        self.emit_metric("erp.transaction_latency_ms", float(latency), "ms")

    def _emit_idoc_transaction(self) -> None:
        idoc_type = random.choice(["ORDERS05", "DELVRY07", "MATMAS05", "INVOIC02"])
        idoc_id = f"IDOC-{random.randint(1000000, 9999999)}"
        status = random.choice(["53", "53", "53", "51"])
        self.emit_log(
            "INFO",
            f"[ERP] idoc_processed type={idoc_type} idoc={idoc_id} status_code={status} system=SAP-PRD",
            {
                "operation": "idoc_processed",
                "erp.idoc_type": idoc_type,
                "erp.idoc_id": idoc_id,
                "erp.status_code": status,
            },
        )

    def _emit_windows_event_log(self) -> None:
        svc = random.choice(self._win_services)
        event_id = random.choice([7036, 7036, 7036, 4672, 4624])
        self.emit_log(
            "DEBUG",
            f"[ERP-WIN] event_id={event_id} source='Service Control Manager' channel=System service={svc} message='The {svc} service entered the running state.'",
            {
                "operation": "windows_event_log",
                "winlog.event_id": event_id,
                "winlog.source": "Service Control Manager",
                "winlog.channel": "System",
                "winlog.service_name": svc,
            },
        )

    def _emit_service_health(self) -> None:
        host = "mfg-sap-bridge-01"
        self.emit_log(
            "INFO",
            f"[ERP] host_health host={host} os='Windows Server 2022' uptime_h={random.randint(120, 8500)} cpu_pct={random.randint(8, 45)} status=NOMINAL",
            {
                "operation": "host_health",
                "erp.host": host,
                "erp.os": "Windows Server 2022",
            },
        )

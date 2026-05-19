"""Firewall Gateway service — Azure eastus-2. Palo Alto PAN-OS perimeter security."""

from __future__ import annotations

import random

from app.services.base_service import BaseService


class FirewallGatewayService(BaseService):
    SERVICE_NAME = "firewall-gateway"

    ZONES = ["TRUST", "UNTRUST", "DMZ", "MANAGEMENT"]

    def generate_telemetry(self) -> None:
        # -- Fault injection --
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Session table --
        session_count = (
            random.randint(15000, 45000)
            if not active_channels
            else random.randint(55000, 64000)
        )
        max_sessions = 64000
        session_rate = random.randint(500, 2000)
        self.emit_metric("firewall.session_count", float(session_count), "sessions")
        self.emit_metric("firewall.session_rate", float(session_rate), "sessions/s")
        self.emit_metric(
            "firewall.session_utilization_pct",
            round(session_count / max_sessions * 100, 1),
            "%",
        )

        self.emit_log(
            "INFO",
            f"1,2025/01/15 14:32:01,PA-5260,SYSTEM,session,0,session-info,"
            f"sessions={session_count}/{max_sessions} "
            f"({round(session_count / max_sessions * 100, 1)}%) rate={session_rate}/s",
            {
                "operation": "session_table",
                "firewall.sessions": session_count,
                "firewall.max_sessions": max_sessions,
                "firewall.session_rate": session_rate,
            },
        )

        # -- Threat prevention --
        threats_blocked = random.randint(0, 15)
        ssl_decrypted = random.randint(200, 800)
        self.emit_metric("firewall.threats_blocked", float(threats_blocked), "threats")
        self.emit_metric("firewall.ssl_decrypted", float(ssl_decrypted), "flows")

        self.emit_log(
            "INFO",
            f"1,2025/01/15 14:32:01,PA-5260,THREAT,summary,0,threat-stats,"
            f"threats_blocked={threats_blocked} ssl_decrypted={ssl_decrypted}",
            {
                "operation": "threat_prevention",
                "firewall.threats": threats_blocked,
                "firewall.ssl_flows": ssl_decrypted,
            },
        )

        # -- CPU utilization --
        cpu_mgmt = (
            round(random.uniform(15.0, 40.0), 1)
            if not active_channels
            else round(random.uniform(75.0, 98.0), 1)
        )
        cpu_dp = (
            round(random.uniform(20.0, 50.0), 1)
            if not active_channels
            else round(random.uniform(80.0, 99.0), 1)
        )
        self.emit_metric("firewall.cpu_mgmt_pct", cpu_mgmt, "%")
        self.emit_metric("firewall.cpu_dataplane_pct", cpu_dp, "%")

        self.emit_log(
            "INFO",
            f"1,2025/01/15 14:32:01,PA-5260,SYSTEM,general,0,resource-monitor,"
            f"mgmt_cpu={cpu_mgmt}% dp_cpu={cpu_dp}%",
            {
                "operation": "cpu_check",
                "firewall.cpu_mgmt": cpu_mgmt,
                "firewall.cpu_dp": cpu_dp,
            },
        )

        # -- Certificate status --
        cert_days_remaining = (
            random.randint(30, 365) if not active_channels else random.randint(0, 5)
        )
        self.emit_metric(
            "firewall.cert_days_remaining", float(cert_days_remaining), "days"
        )
        self.emit_log(
            "INFO",
            f"1,2025/01/15 14:32:01,PA-5260,SYSTEM,general,0,cert-status,"
            f"ssl_inspect_cert days_remaining={cert_days_remaining}",
            {
                "operation": "cert_check",
                "firewall.cert_expiry_days": cert_days_remaining,
            },
        )

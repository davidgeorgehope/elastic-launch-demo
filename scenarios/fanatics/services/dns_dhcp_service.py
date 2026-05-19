"""DNS/DHCP service — Azure eastus-1. Infoblox-style DNS resolution and DHCP lease management."""

from __future__ import annotations

import random

from app.services.base_service import BaseService


class DnsDhcpService(BaseService):
    SERVICE_NAME = "dns-dhcp-service"

    DNS_ZONES = ["fanatics.internal", "collectibles.prod", "warehouse.local"]
    DHCP_SCOPES = ["10.1.0.0/24", "10.2.0.0/24", "172.16.0.0/22", "192.168.1.0/24"]

    def generate_telemetry(self) -> None:
        # -- Fault injection --
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- DNS query stats --
        queries_per_sec = round(random.uniform(500.0, 2000.0), 1)
        cache_hit_pct = round(random.uniform(85.0, 98.0), 1)
        nxdomain_pct = round(random.uniform(0.5, 3.0), 2)
        avg_latency_ms = round(random.uniform(0.5, 5.0), 2)

        self.emit_metric("dns.queries_per_sec", queries_per_sec, "qps")
        self.emit_metric("dns.cache_hit_pct", cache_hit_pct, "%")
        self.emit_metric("dns.nxdomain_pct", nxdomain_pct, "%")
        self.emit_metric("dns.avg_latency_ms", avg_latency_ms, "ms")

        zone = random.choice(self.DNS_ZONES)
        self.emit_log(
            "INFO",
            f"named[12345]: info: zone '{zone}' queries={queries_per_sec}/s "
            f"cache_hit={cache_hit_pct}% nxdomain={nxdomain_pct}% latency={avg_latency_ms}ms",
            {
                "operation": "dns_health",
                "dns.zone": zone,
                "dns.qps": queries_per_sec,
                "dns.cache_hit": cache_hit_pct,
                "dns.nxdomain": nxdomain_pct,
                "dns.latency_ms": avg_latency_ms,
            },
        )

        # -- DHCP lease pool --
        scope = random.choice(self.DHCP_SCOPES)
        total_leases = 254
        active_leases = (
            random.randint(100, 230)
            if not active_channels
            else random.randint(240, 254)
        )
        self.emit_metric("dhcp.active_leases", float(active_leases), "leases")
        self.emit_metric(
            "dhcp.utilization_pct", round(active_leases / total_leases * 100, 1), "%"
        )

        self.emit_log(
            "INFO",
            f"dhcpd[6789]: info: pool {scope} active_leases={active_leases}/{total_leases} "
            f"utilization={round(active_leases / total_leases * 100, 1)}%",
            {
                "operation": "dhcp_health",
                "dhcp.scope": scope,
                "dhcp.active_leases": active_leases,
                "dhcp.total_leases": total_leases,
            },
        )

        # DNS resolution check
        self.emit_log(
            "INFO",
            "named[12345]: info: resolver health check PASS — all upstream forwarders responding within SLA",
            {"operation": "resolver_check", "check.result": "PASS"},
        )

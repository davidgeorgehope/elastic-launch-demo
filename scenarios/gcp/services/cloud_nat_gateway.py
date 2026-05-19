"""Cloud NAT Gateway service — GCP us-east1. NAT port allocation, IP management."""

from __future__ import annotations

import random

from app.services.base_service import BaseService


class CloudNatGatewayService(BaseService):
    SERVICE_NAME = "cloud-nat-gateway"

    GATEWAYS = ["gcpnet-nat-central1", "gcpnet-nat-east1", "gcpnet-nat-europe1"]
    NAT_IPS = [
        "34.72.100.10",
        "34.72.100.11",
        "34.72.100.12",
        "34.86.50.20",
        "34.86.50.21",
    ]

    def generate_telemetry(self) -> None:
        # -- Fault injection --
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Port allocation --
        gw = random.choice(self.GATEWAYS)
        total_ports = 64512
        used_ports = (
            random.randint(20000, 45000)
            if not active_channels
            else random.randint(60000, 64000)
        )
        util_pct = round(used_ports / total_ports * 100, 1)

        self.emit_metric("nat.ports_used", float(used_ports), "ports")
        self.emit_metric("nat.ports_total", float(total_ports), "ports")
        self.emit_metric("nat.port_utilization_pct", util_pct, "%")

        self.emit_log(
            "INFO",
            f"cloudnat: gateway={gw} ports_used={used_ports}/{total_ports} "
            f"utilization={util_pct}% min_ports_per_vm=64",
            {
                "operation": "port_allocation",
                "nat.gateway": gw,
                "nat.ports_used": used_ports,
                "nat.utilization": util_pct,
            },
        )

        # -- Connection stats --
        new_conns = random.randint(1000, 10000)
        dropped_conns = (
            random.randint(0, 5) if not active_channels else random.randint(50, 500)
        )
        self.emit_metric("nat.new_connections", float(new_conns), "conn/s")
        self.emit_metric("nat.dropped_connections", float(dropped_conns), "conn/s")

        self.emit_log(
            "INFO",
            f"cloudnat: gateway={gw} new_conns={new_conns}/s "
            f"dropped={dropped_conns}/s protocol=TCP+UDP",
            {
                "operation": "connection_stats",
                "nat.new_connections": new_conns,
                "nat.dropped_connections": dropped_conns,
            },
        )

        # -- IP pool status --
        nat_ip = random.choice(self.NAT_IPS)
        allocated_ips = len(self.NAT_IPS)
        active_mappings = random.randint(5000, 30000)
        self.emit_metric("nat.allocated_ips", float(allocated_ips), "addresses")
        self.emit_metric("nat.active_mappings", float(active_mappings), "mappings")

        self.emit_log(
            "INFO",
            f"cloudnat: gateway={gw} nat_ip={nat_ip} "
            f"allocated_ips={allocated_ips} active_mappings={active_mappings}",
            {
                "operation": "ip_pool_status",
                "nat.nat_ip": nat_ip,
                "nat.allocated_ips": allocated_ips,
                "nat.active_mappings": active_mappings,
            },
        )

"""VPC Network Manager service — GCP us-central1. VPC routes, subnets, peering, firewall rules."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class VpcNetworkManagerService(BaseService):
    SERVICE_NAME = "vpc-network-manager"

    NETWORKS = ["gcpnet-vpc-prod", "gcpnet-vpc-staging", "gcpnet-vpc-shared"]
    SUBNETS = [
        "gcpnet-subnet-central1",
        "gcpnet-subnet-east1",
        "gcpnet-subnet-europe1",
        "gcpnet-subnet-services",
    ]

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._poll_idx = 0
        self._last_route_check = time.time()

    def generate_telemetry(self) -> None:
        # -- Fault injection --
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Subnet IP utilization --
        subnet = self.SUBNETS[self._poll_idx % len(self.SUBNETS)]
        self._poll_idx += 1
        total_ips = 4094
        used_ips = (
            random.randint(1500, 3200)
            if not active_channels
            else random.randint(3900, 4090)
        )
        util_pct = round(used_ips / total_ips * 100, 1)

        self.emit_metric("vpc.subnet.ip_utilization", util_pct, "%")
        self.emit_metric("vpc.subnet.used_ips", float(used_ips), "addresses")

        self.emit_log(
            "INFO",
            f"vpc-monitor: subnet={subnet} used_ips={used_ips}/{total_ips} "
            f"utilization={util_pct}% network=gcpnet-vpc-prod",
            {
                "operation": "subnet_monitor",
                "vpc.subnet": subnet,
                "vpc.used_ips": used_ips,
                "vpc.total_ips": total_ips,
                "vpc.utilization_pct": util_pct,
            },
        )

        # -- Route table check every ~10s --
        if time.time() - self._last_route_check > 10:
            network = random.choice(self.NETWORKS)
            route_count = (
                random.randint(80, 200)
                if not active_channels
                else random.randint(240, 250)
            )
            peering_count = random.randint(2, 5)
            self.emit_metric("vpc.route.count", float(route_count), "routes")
            self.emit_metric("vpc.peering.count", float(peering_count), "peerings")
            self.emit_log(
                "INFO",
                f"vpc-monitor: network={network} routes={route_count}/250 "
                f"peerings={peering_count} status=ACTIVE",
                {
                    "operation": "route_check",
                    "vpc.network": network,
                    "vpc.route_count": route_count,
                    "vpc.peering_count": peering_count,
                },
            )
            self._last_route_check = time.time()

        # -- Firewall rule evaluation --
        fw_rules_evaluated = random.randint(10000, 50000)
        fw_denied = (
            random.randint(10, 100)
            if not active_channels
            else random.randint(500, 5000)
        )
        self.emit_metric(
            "vpc.firewall.rules_evaluated", float(fw_rules_evaluated), "evaluations"
        )
        self.emit_metric("vpc.firewall.denied_packets", float(fw_denied), "packets")
        self.emit_log(
            "INFO",
            f"vpc-firewall: evaluated={fw_rules_evaluated} denied={fw_denied} "
            f"network=gcpnet-vpc-prod interval=60s",
            {
                "operation": "firewall_eval",
                "vpc.firewall.evaluated": fw_rules_evaluated,
                "vpc.firewall.denied": fw_denied,
            },
        )

        # -- VPC Flow log summary --
        flows_ingress = random.randint(50000, 200000)
        flows_egress = random.randint(30000, 150000)
        self.emit_metric("vpc.flow.ingress", float(flows_ingress), "flows")
        self.emit_metric("vpc.flow.egress", float(flows_egress), "flows")
        self.emit_log(
            "INFO",
            f"vpc-flow-summary: ingress_flows={flows_ingress} egress_flows={flows_egress} "
            f"sampling_rate=0.5 interval=60s",
            {
                "operation": "flow_summary",
                "vpc.flow.ingress": flows_ingress,
                "vpc.flow.egress": flows_egress,
            },
        )

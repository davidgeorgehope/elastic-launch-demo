"""Network Intelligence service — GCP europe-west1. Connectivity tests, flow analytics."""

from __future__ import annotations

import random

from app.services.base_service import BaseService


class NetworkIntelligenceService(BaseService):
    SERVICE_NAME = "network-intelligence"

    TEST_NAMES = [
        "test-vpc-to-onprem",
        "test-central1-to-europe1",
        "test-nat-egress",
        "test-vpn-connectivity",
        "test-interconnect-path",
        "test-dns-resolution",
    ]
    PROTOCOLS = ["TCP:80", "TCP:443", "ICMP", "UDP:53", "TCP:22"]

    def generate_telemetry(self) -> None:
        # -- Fault injection --
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Connectivity test results --
        test_name = random.choice(self.TEST_NAMES)
        protocol = random.choice(self.PROTOCOLS)
        result = (
            "REACHABLE"
            if not active_channels
            else random.choice(["UNREACHABLE", "DROPPED", "AMBIGUOUS"])
        )
        hops_total = random.randint(5, 10)
        hops_completed = (
            hops_total if not active_channels else random.randint(2, hops_total - 1)
        )
        latency_ms = (
            round(random.uniform(1.0, 15.0), 2)
            if not active_channels
            else round(random.uniform(100.0, 2000.0), 2)
        )

        self.emit_metric("ni.test_latency_ms", latency_ms, "ms")

        self.emit_log(
            "INFO",
            f"nic: test={test_name} protocol={protocol} result={result} "
            f"hops={hops_completed}/{hops_total} latency={latency_ms}ms",
            {
                "operation": "connectivity_test",
                "ni.test_name": test_name,
                "ni.protocol": protocol,
                "ni.result": result,
                "ni.hops_completed": hops_completed,
                "ni.hops_total": hops_total,
                "ni.latency_ms": latency_ms,
            },
        )

        # -- Flow analytics --
        total_flows = random.randint(100000, 1000000)
        flagged_flows = (
            random.randint(0, 50) if not active_channels else random.randint(500, 5000)
        )
        anomaly_score = (
            round(random.uniform(0.0, 0.2), 3)
            if not active_channels
            else round(random.uniform(0.6, 1.0), 3)
        )

        self.emit_metric("ni.total_flows", float(total_flows), "flows")
        self.emit_metric("ni.flagged_flows", float(flagged_flows), "flows")
        self.emit_metric("ni.anomaly_score", anomaly_score, "score")

        self.emit_log(
            "INFO",
            f"nic: flow_analytics total={total_flows} flagged={flagged_flows} "
            f"anomaly_score={anomaly_score} sampling=1/1000",
            {
                "operation": "flow_analytics",
                "ni.total_flows": total_flows,
                "ni.flagged_flows": flagged_flows,
                "ni.anomaly_score": anomaly_score,
            },
        )

        # -- Performance dashboard metrics --
        topology_nodes = random.randint(30, 60)
        topology_edges = random.randint(50, 120)
        self.emit_metric("ni.topology_nodes", float(topology_nodes), "nodes")
        self.emit_metric("ni.topology_edges", float(topology_edges), "edges")

        self.emit_log(
            "INFO",
            f"nic: topology_map nodes={topology_nodes} edges={topology_edges} "
            f"regions=3 vpcs=3 last_refresh=60s",
            {
                "operation": "topology_map",
                "ni.topology_nodes": topology_nodes,
                "ni.topology_edges": topology_edges,
            },
        )

        # -- Firewall insights --
        shadowed_rules = (
            random.randint(0, 3) if not active_channels else random.randint(5, 20)
        )
        overly_permissive = (
            random.randint(0, 2) if not active_channels else random.randint(3, 15)
        )
        self.emit_metric("ni.shadowed_rules", float(shadowed_rules), "rules")
        self.emit_metric(
            "ni.overly_permissive_rules", float(overly_permissive), "rules"
        )

        self.emit_log(
            "INFO",
            f"nic: firewall_insights shadowed_rules={shadowed_rules} "
            f"overly_permissive={overly_permissive} last_analysis=300s",
            {
                "operation": "firewall_insights",
                "ni.shadowed_rules": shadowed_rules,
                "ni.overly_permissive": overly_permissive,
            },
        )

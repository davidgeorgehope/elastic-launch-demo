"""Cloud Interconnect service — GCP europe-west1. Dedicated interconnect, BGP, VLAN attachments."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class CloudInterconnectService(BaseService):
    SERVICE_NAME = "cloud-interconnect"

    ATTACHMENTS = ["gcpnet-interconnect-primary", "gcpnet-interconnect-secondary"]
    LOCATIONS = ["iad-zone1-1", "dfw-zone1-1", "ams-zone1-1"]

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._last_bgp_check = time.time()

    def generate_telemetry(self) -> None:
        # -- Fault injection --
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Circuit status --
        attachment = random.choice(self.ATTACHMENTS)
        link_status = (
            "UP" if not active_channels else random.choice(["DOWN", "FLAPPING"])
        )
        bandwidth_gbps = random.choice([10, 100])
        utilization_pct = (
            round(random.uniform(20.0, 70.0), 1)
            if not active_channels
            else round(random.uniform(85.0, 99.0), 1)
        )

        self.emit_metric("interconnect.bandwidth_gbps", float(bandwidth_gbps), "Gbps")
        self.emit_metric("interconnect.utilization_pct", utilization_pct, "%")

        self.emit_log(
            "INFO",
            f"cloud-interconnect: attachment={attachment} link={link_status} "
            f"bandwidth={bandwidth_gbps}Gbps utilization={utilization_pct}% "
            f"location={random.choice(self.LOCATIONS)}",
            {
                "operation": "circuit_status",
                "interconnect.attachment": attachment,
                "interconnect.link_status": link_status,
                "interconnect.bandwidth": bandwidth_gbps,
                "interconnect.utilization": utilization_pct,
            },
        )

        # -- BGP session check every ~10s --
        if time.time() - self._last_bgp_check > 10:
            peer_ip = f"169.254.{random.randint(0,255)}.{random.randint(1,254)}"
            peer_asn = random.choice([16550, 64512, 64513])
            bgp_state = (
                "ESTABLISHED"
                if not active_channels
                else random.choice(["IDLE", "ACTIVE", "CONNECT"])
            )
            advertised_routes = (
                random.randint(20, 100) if not active_channels else random.randint(0, 5)
            )

            self.emit_metric(
                "interconnect.bgp_advertised_routes", float(advertised_routes), "routes"
            )

            self.emit_log(
                "INFO",
                f"cloud-router: peer={peer_ip} asn={peer_asn} "
                f"state={bgp_state} advertised={advertised_routes} "
                f"bfd=ENABLED attachment={attachment}",
                {
                    "operation": "bgp_check",
                    "interconnect.bgp_peer": peer_ip,
                    "interconnect.bgp_state": bgp_state,
                    "interconnect.advertised_routes": advertised_routes,
                },
            )
            self._last_bgp_check = time.time()

        # -- VLAN attachment health --
        vlan_tag = random.randint(100, 4094)
        packets_in = random.randint(1000000, 10000000)
        packets_out = random.randint(1000000, 10000000)
        self.emit_metric("interconnect.vlan_packets_in", float(packets_in), "packets")
        self.emit_metric("interconnect.vlan_packets_out", float(packets_out), "packets")

        self.emit_log(
            "INFO",
            f"cloud-interconnect: attachment={attachment} vlan_tag={vlan_tag} "
            f"packets_in={packets_in} packets_out={packets_out} "
            f"mtu=1500 encryption=MACsec",
            {
                "operation": "vlan_health",
                "interconnect.vlan_tag": vlan_tag,
                "interconnect.packets_in": packets_in,
                "interconnect.packets_out": packets_out,
            },
        )

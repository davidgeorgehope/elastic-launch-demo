"""Cloud VPN Gateway service — GCP europe-west1. VPN tunnels, IKE/IPsec negotiation."""

from __future__ import annotations

import random

from app.services.base_service import BaseService


class CloudVpnGatewayService(BaseService):
    SERVICE_NAME = "cloud-vpn-gateway"

    TUNNELS = ["gcpnet-vpn-tunnel-01", "gcpnet-vpn-tunnel-02", "gcpnet-vpn-tunnel-03"]
    GATEWAYS = ["gcpnet-vpn-gw-europe1", "gcpnet-vpn-gw-central1"]

    def generate_telemetry(self) -> None:
        # -- Fault injection --
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Tunnel status --
        tunnel = random.choice(self.TUNNELS)
        gateway = random.choice(self.GATEWAYS)
        tunnel_status = (
            "ESTABLISHED"
            if not active_channels
            else random.choice(["DOWN", "NEGOTIATING", "NO_INCOMING_PACKETS"])
        )
        peer_ip = f"203.0.113.{random.randint(1, 254)}"

        self.emit_log(
            "INFO",
            f"cloud-vpn: tunnel={tunnel} gateway={gateway} "
            f"status={tunnel_status} peer={peer_ip} ike_version=IKEv2",
            {
                "operation": "tunnel_status",
                "vpn.tunnel": tunnel,
                "vpn.gateway": gateway,
                "vpn.status": tunnel_status,
                "vpn.peer_ip": peer_ip,
            },
        )

        # -- Throughput --
        tx_bytes = random.randint(10000000, 500000000)
        rx_bytes = random.randint(10000000, 500000000)
        self.emit_metric("vpn.tx_bytes", float(tx_bytes), "bytes")
        self.emit_metric("vpn.rx_bytes", float(rx_bytes), "bytes")

        self.emit_log(
            "INFO",
            f"cloud-vpn: tunnel={tunnel} tx_bytes={tx_bytes} rx_bytes={rx_bytes} "
            f"max_bandwidth=3Gbps routing=DYNAMIC",
            {
                "operation": "throughput",
                "vpn.tunnel": tunnel,
                "vpn.tx_bytes": tx_bytes,
                "vpn.rx_bytes": rx_bytes,
            },
        )

        # -- IKE SA status --
        ike_sa_lifetime = random.randint(1800, 36000)
        ike_rekey_in = random.randint(0, 3600) if not active_channels else 0
        child_sa_count = random.randint(1, 4)
        self.emit_metric("vpn.ike_sa_lifetime", float(ike_sa_lifetime), "seconds")
        self.emit_metric("vpn.child_sa_count", float(child_sa_count), "SAs")

        self.emit_log(
            "INFO",
            f"cloud-vpn: tunnel={tunnel} ike_sa_lifetime={ike_sa_lifetime}s "
            f"rekey_in={ike_rekey_in}s child_sas={child_sa_count} "
            f"cipher=AES-256-GCM auth=SHA-384",
            {
                "operation": "ike_status",
                "vpn.ike_sa_lifetime": ike_sa_lifetime,
                "vpn.rekey_in": ike_rekey_in,
                "vpn.child_sa_count": child_sa_count,
            },
        )

        # -- Packet stats --
        packets_dropped = (
            random.randint(0, 5) if not active_channels else random.randint(100, 2000)
        )
        self.emit_metric("vpn.packets_dropped", float(packets_dropped), "packets")
        self.emit_log(
            "INFO",
            f"cloud-vpn: tunnel={tunnel} dropped_packets={packets_dropped} "
            f"replay_window=64 dead_peer_detection=ENABLED",
            {
                "operation": "packet_stats",
                "vpn.dropped_packets": packets_dropped,
            },
        )

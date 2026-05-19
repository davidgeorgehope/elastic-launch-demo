"""Network Controller service — Azure eastus-1. Cisco IOS-XE/NX-OS routing and switching."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class NetworkControllerService(BaseService):
    SERVICE_NAME = "network-controller"

    INTERFACES = [
        "GigabitEthernet0/0/0",
        "GigabitEthernet0/0/1",
        "TenGigabitEthernet1/0/1",
        "TenGigabitEthernet1/0/2",
        "Vlan100",
        "Vlan200",
        "Loopback0",
    ]

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._poll_idx = 0
        self._last_bgp_check = time.time()

    def generate_telemetry(self) -> None:
        # -- Fault injection --
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Interface stats (SNMP-style polling) --
        iface = self.INTERFACES[self._poll_idx % len(self.INTERFACES)]
        self._poll_idx += 1
        in_octets = random.randint(50000000, 500000000)
        out_octets = random.randint(50000000, 500000000)
        in_errors = (
            random.randint(0, 2) if not active_channels else random.randint(10, 100)
        )
        crc_errors = (
            random.randint(0, 1) if not active_channels else random.randint(5, 50)
        )

        self.emit_metric("network.interface.in_octets", float(in_octets), "bytes")
        self.emit_metric("network.interface.out_octets", float(out_octets), "bytes")
        self.emit_metric("network.interface.in_errors", float(in_errors), "errors")

        self.emit_log(
            "INFO",
            f"%LINEPROTO-5-UPDOWN: Line protocol on Interface {iface}, changed state to up "
            f"in_octets={in_octets} out_octets={out_octets} in_errors={in_errors} crc_errors={crc_errors}",
            {
                "operation": "interface_poll",
                "network.interface": iface,
                "network.in_octets": in_octets,
                "network.out_octets": out_octets,
                "network.in_errors": in_errors,
                "network.crc_errors": crc_errors,
            },
        )

        # -- BGP peer check every ~10s --
        if time.time() - self._last_bgp_check > 10:
            bgp_peers = random.randint(3, 6)
            established = (
                bgp_peers if not active_channels else random.randint(1, bgp_peers - 1)
            )
            self.emit_metric(
                "network.bgp.peers_established", float(established), "peers"
            )
            self.emit_log(
                "INFO",
                f"%BGP-5-ADJCHANGE: neighbor 10.0.0.1 Up, {established}/{bgp_peers} peers Established",
                {
                    "operation": "bgp_check",
                    "bgp.total_peers": bgp_peers,
                    "bgp.established": established,
                },
            )
            self._last_bgp_check = time.time()

        # -- STP status --
        stp_changes = (
            random.randint(0, 1) if not active_channels else random.randint(3, 15)
        )
        self.emit_metric("network.stp.topology_changes", float(stp_changes), "changes")
        self.emit_log(
            "INFO",
            f"%SPANTREE-6-PORT_STATE: VLAN0100 {iface} state -> forwarding, "
            f"{stp_changes} topology changes this interval",
            {"operation": "stp_check", "stp.topology_changes": stp_changes},
        )

        # -- MAC table utilization --
        mac_entries = random.randint(800, 2500)
        mac_table_capacity = 8192
        self.emit_metric("network.mac_table.entries", float(mac_entries), "entries")
        self.emit_log(
            "INFO",
            f"%SW_MATM-6-MACCOUNT: MAC address table entries {mac_entries}/{mac_table_capacity} "
            f"({round(mac_entries / mac_table_capacity * 100, 1)}% utilization)",
            {
                "operation": "mac_table_check",
                "mac_table.entries": mac_entries,
                "mac_table.capacity": mac_table_capacity,
            },
        )

"""Fanatics Collectibles scenario — enterprise infrastructure and network operations."""

from __future__ import annotations

import random
import time
from typing import Any

from scenarios.base import BaseScenario, CountdownConfig, UITheme



class FanaticsScenario(BaseScenario):
    """Enterprise infrastructure and network operations for Fanatics Collectibles."""

    # ── Identity ──────────────────────────────────────────────────────

    @property
    def scenario_id(self) -> str:
        return "fanatics"

    @property
    def scenario_icon(self) -> str:
        return "🏈"

    @property
    def scenario_name(self) -> str:
        return "Fanatics Collectibles"

    @property
    def scenario_description(self) -> str:
        return (
            "Enterprise infrastructure and network operations for vertically integrated "
            "trading cards and memorabilia. Recently migrated 100% out of physical DCs to "
            "50% AWS / 50% Azure with GCP edge."
        )

    @property
    def namespace(self) -> str:
        return "fanatics"

    @property
    def sort_order(self) -> int:
        return 2

    @property
    def raw_log_profile(self) -> dict[str, Any]:
        return {
            "service_name": "commerce-edge",
            "user_id_prefix": "fan",
            "tier_field": "member_tier",
            "tier_values": [("guest", 60), ("member", 30), ("allstar", 10)],
            "country_weights": {"US": 80, "CA": 8, "GB": 5, "MX": 4, "AU": 3},
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "paths": [
                "/api/v1/catalog", "/api/v1/cart", "/api/v1/checkout",
                "/api/v1/orders", "/api/v1/jerseys/{team}", "/api/v1/teams",
                "/login", "/health",
            ],
            "change_point_path": "/api/v1/checkout",
        }

    @property
    def executive_kpi_emitter_service_name(self) -> str:
        return "digital-marketplace"

    @property
    def executive_dashboard_intro(self) -> str:
        return (
            "**Fanatics executive KPIs** — sports media, streaming, fantasy, collectibles "
            "commerce, sponsorship, and regulated wagering (synthetic `business.*` from `digital-marketplace`)."
        )

    @property
    def executive_kpi_sections(self) -> list[dict]:
        return [
            {
                "header": "**Monetization & wagering** — ads, subscriptions, handle, and margin",
                "specs": [
                    ("Ad revenue (USD/min)", "metrics.business.ad_revenue_usd_per_min"),
                    ("Programmatic fill (%)", "metrics.business.programmatic_fill_rate_pct"),
                    ("Betting handle (USD/min)", "metrics.business.betting_handle_usd_per_min"),
                    ("Sportsbook hold (%)", "metrics.business.betting_hold_pct"),
                    ("Gross win (USD/min)", "metrics.business.betting_gross_win_usd_per_min"),
                    ("Subscription MRR (USD/min)", "metrics.business.subscription_mrr_usd_per_min"),
                ],
            },
            {
                "header": "**Audience & engagement** — live scale, video, traffic, sessions, fantasy",
                "specs": [
                    ("Live concurrent viewers", "metrics.business.live_concurrent_viewers"),
                    ("Video min engaged / min", "metrics.business.video_minutes_engaged_per_min"),
                    ("Page views / min", "metrics.business.page_views_per_min"),
                    ("App sessions / min", "metrics.business.app_sessions_per_min"),
                    ("Content completion (%)", "metrics.business.content_completion_rate_pct"),
                    ("Fantasy active entries", "metrics.business.fantasy_active_entries"),
                ],
            },
            {
                "header": "**Commerce & partners** — merch, tickets, sponsorship, B2B data",
                "specs": [
                    ("Merch GMV (USD/min)", "metrics.business.merch_gmv_usd_per_min"),
                    ("Live ticketing (USD/min)", "metrics.business.live_event_ticketing_usd_per_min"),
                    ("Partner sponsorship (USD/min)", "metrics.business.partner_sponsorship_usd_per_min"),
                    ("API / data partner (USD/min)", "metrics.business.api_data_partner_revenue_usd_per_min"),
                    ("Sponsored inv. (s/min)", "metrics.business.sponsored_inventory_seconds_per_min"),
                    ("Premium ARPU (USD)", "metrics.business.premium_tier_arpu_usd"),
                ],
            },
            {
                "header": "**Marketing & health** — CRM, loyalty, social, churn & satisfaction proxies",
                "specs": [
                    ("Push CTR (%)", "metrics.business.push_notification_ctr_pct"),
                    ("Newsletter open (%)", "metrics.business.newsletter_open_rate_pct"),
                    ("Loyalty redeem (pts/min)", "metrics.business.loyalty_points_redeemed_per_min"),
                    ("Social clip shares / min", "metrics.business.social_clip_shares_per_min"),
                    ("Churn risk (0–100)", "metrics.business.churn_risk_index_0_100"),
                    ("Satisfaction proxy (NPS-like)", "metrics.business.net_satisfaction_proxy_nps"),
                ],
            },
        ]

    @property
    def executive_trend_charts(self) -> list[dict]:
        return [
            {"title": "Ad revenue trend", "field": "metrics.business.ad_revenue_usd_per_min", "y_label": "USD/min"},
            {"title": "Video engagement (min/min)", "field": "metrics.business.video_minutes_engaged_per_min", "y_label": "min/min"},
            {"title": "Live concurrent viewers", "field": "metrics.business.live_concurrent_viewers", "y_label": "viewers"},
            {"title": "Betting handle trend", "field": "metrics.business.betting_handle_usd_per_min", "y_label": "USD/min"},
            {"title": "Subscription MRR trend", "field": "metrics.business.subscription_mrr_usd_per_min", "y_label": "USD/min"},
            {"title": "Merch GMV trend", "field": "metrics.business.merch_gmv_usd_per_min", "y_label": "USD/min"},
        ]

    # ── Services ──────────────────────────────────────────────────────

    @property
    def services(self) -> dict[str, dict[str, Any]]:
        return {
            "card-printing-system": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1a",
                "subsystem": "manufacturing",
                "language": "java",
            },
            "digital-marketplace": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1b",
                "subsystem": "commerce",
                "language": "python",
            },
            "auction-engine": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1c",
                "subsystem": "commerce",
                "language": "go",
            },
            "packaging-fulfillment": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "logistics",
                "language": "python",
            },
            "wifi-controller": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-b",
                "subsystem": "network_access",
                "language": "cpp",
                "generates_traces": False,
            },
            "cloud-inventory-scanner": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "cloud_ops",
                "language": "python",
            },
            "network-controller": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "network_core",
                "language": "go",
                "generates_traces": False,
            },
            "firewall-gateway": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-2",
                "subsystem": "security",
                "language": "rust",
                "generates_traces": False,
            },
            "dns-dhcp-service": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "network_services",
                "language": "java",
                "generates_traces": False,
            },
        }

    # ── Channel Registry ──────────────────────────────────────────────

    @property
    def channel_registry(self) -> dict[int, dict[str, Any]]:
        return {
            1: {
                "name": "MAC Address Flapping",
                "subsystem": "network_core",
                "vehicle_section": "switching_fabric",
                "error_type": "SW_MATM-4-MACFLAP_NOTIF",
                "sensor_type": "mac_table",
                "affected_services": ["network-controller", "dns-dhcp-service"],
                "cascade_services": ["firewall-gateway", "wifi-controller"],
                "description": "MAC address table instability causing port flapping on the switching fabric",
                "investigation_notes": (
                    "1. Run `show mac address-table notification mac-move` to identify the flapping MAC and involved ports.\n"
                    "2. Check for physical layer issues: `show interface status` on both source and destination ports for CRC errors, runts, or input errors.\n"
                    "3. Verify no switching loops exist: `show spanning-tree vlan <id> detail` — a flapping MAC often indicates an STP misconfiguration or a rogue switch.\n"
                    "4. Look for duplicate MAC from VM migration or HSRP/VRRP misconfiguration: `show mac address-table address <mac>`.\n"
                    "5. If caused by a NIC teaming misconfiguration on the host side, disable one NIC and confirm flapping stops.\n"
                    "6. As a short-term fix, apply `switchport port-security` to limit MAC addresses per port and contain the blast radius."
                ),
                "remediation_action": "clear_mac_table",
                "error_message": (
                    "%SW_MATM-4-MACFLAP_NOTIF: Host {mac_address} in vlan {vlan_id} "
                    "is flapping between port {interface_src} and port {interface_dst}, "
                    "{flap_count} moves in {flap_window}s"
                ),
                "stack_trace": (
                    "switch# show mac address-table notification mac-move\n"
                    "MAC Move Notification Feature is Enabled on the switch\n"
                    "VLAN  MAC Address       From Port          To Port            Move Count\n"
                    "----  ----------------  -----------------  -----------------  ----------\n"
                    "{vlan_id}   {mac_address}     {interface_src}         {interface_dst}         {flap_count}\n"
                    "\n"
                    "switch# show mac address-table count\n"
                    "Total MAC Addresses for this criterion: 3847\n"
                    "Multicast MAC Addresses:                12\n"
                    "Unicast MAC Addresses:                  3835\n"
                    "Total MAC Addresses in Use:             3847"
                ),
            },
            2: {
                "name": "Spanning Tree Topology Change",
                "subsystem": "network_core",
                "vehicle_section": "switching_fabric",
                "error_type": "SPANTREE-2-TOPO_CHANGE",
                "sensor_type": "stp_state",
                "affected_services": ["network-controller", "firewall-gateway"],
                "cascade_services": ["dns-dhcp-service", "wifi-controller"],
                "description": "Rapid spanning tree topology changes destabilizing Layer 2 forwarding",
                "investigation_notes": (
                    "1. Run `show spanning-tree vlan <id> detail` to identify the port generating Topology Change Notifications (TCNs).\n"
                    "2. Check `show spanning-tree detail | include ieee|from|occur` across all switches to pinpoint the originating bridge.\n"
                    "3. Verify BPDU Guard and Root Guard are enabled on access ports: `show spanning-tree inconsistentports`.\n"
                    "4. A sudden burst of TCNs often indicates a flapping uplink or a new device plugged into a trunk port — correlate with interface up/down events.\n"
                    "5. Enable `spanning-tree portfast` on all edge/access ports to prevent end-host connections from triggering topology changes.\n"
                    "6. If the root bridge is shifting, set explicit root priority: `spanning-tree vlan <id> root primary` on the designated core switch."
                ),
                "remediation_action": "reset_spanning_tree",
                "error_message": (
                    "%SPANTREE-2-TOPO_CHANGE: Topology Change received on VLAN {vlan_id} "
                    "instance {stp_instance} from bridge {bridge_id} via port {interface}, "
                    "{tc_count} TCN BPDUs in {tc_window}s"
                ),
                "stack_trace": (
                    "switch# show spanning-tree vlan {vlan_id} detail\n"
                    "VLAN{vlan_id} is executing the rstp compatible Spanning Tree protocol\n"
                    "  Bridge Identifier has priority 32768, address {bridge_id}\n"
                    "  Topology change flag set, detected flag set\n"
                    "  Number of topology changes {tc_count}\n"
                    "  Last change occurred on port {interface}\n"
                    "  Times: hello 2, max age 20, forward delay 15, topology change {tc_window}\n"
                    "  Port {interface} of VLAN{vlan_id} is designated forwarding\n"
                    "    Port cost 4, Port priority 128, Port Identifier 128.1\n"
                    "    Number of transitions to forwarding state: {tc_count}"
                ),
            },
            3: {
                "name": "BGP Peer Flapping",
                "subsystem": "network_core",
                "vehicle_section": "routing_engine",
                "error_type": "BGP-3-NOTIFICATION",
                "sensor_type": "bgp_session",
                "affected_services": ["network-controller", "firewall-gateway"],
                "cascade_services": ["dns-dhcp-service", "cloud-inventory-scanner"],
                "description": "BGP peering session repeatedly transitioning between Established and Idle states",
                "investigation_notes": (
                    "1. Run `show bgp neighbors <peer_ip>` to check the last NOTIFICATION code and hold timer status.\n"
                    "2. Examine `show bgp summary` for Established vs non-Established peers and check PfxRcd (prefix received) for anomalies.\n"
                    "3. Hold Timer Expired (code 4/0) usually means keepalives are not reaching the peer — check interface utilization and MTU with `show interface <intf>`.\n"
                    "4. Cease/Admin Reset (6/4) indicates the remote side cleared the session — coordinate with the peer AS administrator.\n"
                    "5. Check route policy: `show route-map` and `show ip prefix-list` — a misconfigured prefix filter can cause constant UPDATE/WITHDRAW cycling.\n"
                    "6. Verify TCP session health: `show tcp brief | include <peer_ip>` and check for retransmissions that indicate an underlying transport issue."
                ),
                "remediation_action": "reset_bgp_session",
                "error_message": (
                    "%BGP-3-NOTIFICATION: Neighbor {bgp_peer_ip} (AS {bgp_peer_as}) "
                    "sent NOTIFICATION {bgp_notification}, {bgp_flap_count} transitions "
                    "in {bgp_flap_window}s, last state {bgp_last_state}"
                ),
                "stack_trace": (
                    "router# show bgp neighbors {bgp_peer_ip}\n"
                    "BGP neighbor is {bgp_peer_ip}, remote AS {bgp_peer_as}, external link\n"
                    "  BGP state = {bgp_last_state}, up for 00:00:03\n"
                    "  Last read 00:00:03, Last write 00:00:08\n"
                    "  Hold time is 180, keepalive interval is 60 seconds\n"
                    "  Neighbor sessions: 1 active\n"
                    "  Notification received: {bgp_notification}\n"
                    "  Flap count: {bgp_flap_count} in {bgp_flap_window}s\n"
                    "    Opens:           Sent 12   Rcvd 9\n"
                    "    Notifications:   Sent 0    Rcvd {bgp_flap_count}\n"
                    "    Updates:         Sent 245  Rcvd 0\n"
                    "    Keepalives:      Sent 1024 Rcvd 891"
                ),
            },
            4: {
                "name": "Warehouse Scanner Desync",
                "subsystem": "logistics",
                "vehicle_section": "inventory_system",
                "error_type": "WMS-SCANNER-DESYNC",
                "sensor_type": "barcode_scanner",
                "affected_services": ["packaging-fulfillment", "cloud-inventory-scanner"],
                "cascade_services": ["digital-marketplace", "card-printing-system"],
                "description": "Barcode scanners losing synchronization with inventory management system",
                "investigation_notes": (
                    "1. Check scanner WiFi signal strength: -72 dBm is marginal — scanners need at least -67 dBm for reliable real-time sync in warehouse environments.\n"
                    "2. Verify the scanner firmware version: v3.0.x has known sync bugs with the WMS REST API — upgrade to v3.2.1 which includes the keepalive fix.\n"
                    "3. Battery at 34% can cause intermittent WiFi disconnections on Zebra MC9300 scanners — swap batteries and check if sync recovers.\n"
                    "4. Missed scans create inventory deltas — run a zone reconciliation: `wms-cli reconcile --zone <zone> --source physical-count`.\n"
                    "5. If multiple scanners in the same zone are desyncing, the issue is likely the WiFi AP in that zone — check AP health (correlate with Channel 7/8).\n"
                    "6. As a workaround, switch scanners to batch/store-and-forward mode until WiFi is stable, then bulk-upload when connectivity is restored."
                ),
                "remediation_action": "resync_scanners",
                "error_message": (
                    "wms.inventory WMS-SCANNER-DESYNC scanner={scanner_id} "
                    "zone={scanner_zone} last_sync={scanner_last_sync_sec}s "
                    "(max {scanner_sync_max_sec}s) missed_scans={scanner_missed_scans} "
                    "inventory_delta={inventory_delta} firmware=v{scanner_firmware}"
                ),
                "stack_trace": (
                    "WMS Scanner Sync Diagnostic Report\n"
                    "------------------------------------\n"
                    "Scanner ID:     {scanner_id}\n"
                    "Zone:           {scanner_zone}\n"
                    "Last Sync:      {scanner_last_sync_sec}s ago (threshold: {scanner_sync_max_sec}s)\n"
                    "Missed Scans:   {scanner_missed_scans}\n"
                    "Inventory Delta: {inventory_delta} items\n"
                    "Firmware:       v{scanner_firmware}\n"
                    "WiFi Signal:    -72 dBm (marginal)\n"
                    "Battery Level:  34%\n"
                    "Recommended Action: Reconnect scanner, verify WiFi coverage in {scanner_zone}"
                ),
            },
            5: {
                "name": "Firewall CPU Overload",
                "subsystem": "security",
                "vehicle_section": "perimeter_defense",
                "error_type": "SYSTEM-cpu-critical",
                "sensor_type": "cpu_utilization",
                "affected_services": ["firewall-gateway", "network-controller"],
                "cascade_services": ["dns-dhcp-service", "digital-marketplace"],
                "description": "Firewall data plane CPU exceeding safe operating threshold",
                "investigation_notes": (
                    "1. Run `show running resource-monitor` to see per-DP CPU, packet buffer, and session rate in real time.\n"
                    "2. Identify offending policy: `show rule-hit-count` — rules with high hit counts and complex App-ID or content inspection drive DP CPU.\n"
                    "3. Check threat prevention load: `show threat statistics` — if IPS/AV signature matching is spiking, a signature update or new attack pattern may be the cause.\n"
                    "4. Review decryption overhead: `show counter global filter aspect dp delta yes | match ssl` — SSL decryption is the #1 DP CPU consumer.\n"
                    "5. Consider bypassing decryption for trusted high-bandwidth flows (e.g., Windows Update, CDN traffic) with a no-decrypt rule.\n"
                    "6. If CPU remains critical, enable hardware offload for IPSec tunnels and reduce logging verbosity on high-traffic rules."
                ),
                "remediation_action": "restart_management_plane",
                "error_message": (
                    "1,2025/01/15 14:32:01,007200001234,SYSTEM,general,0,"
                    "SYSTEM-cpu-critical,Data plane CPU at {fw_dp_cpu_pct}% "
                    "(threshold {fw_cpu_threshold}%), management plane {fw_mgmt_cpu_pct}%, "
                    "packet buffer {fw_buffer_pct}%, active rules {fw_policy_count}"
                ),
                "stack_trace": (
                    "> show running resource-monitor\n"
                    "Resource utilization (observed over last 60 seconds):\n"
                    "  Data Plane CPU Utilization:\n"
                    "    DP-0:  {fw_dp_cpu_pct}%  (threshold: {fw_cpu_threshold}%)\n"
                    "    DP-1:  {fw_dp_cpu_pct}%\n"
                    "  Management Plane CPU: {fw_mgmt_cpu_pct}%\n"
                    "  Packet Buffer:        {fw_buffer_pct}%\n"
                    "  Active Security Rules: {fw_policy_count}\n"
                    "  Session Rate:          8,452 sessions/sec\n"
                    "  Throughput:            4.2 Gbps\n"
                    "  Packet Rate:           892,341 pps"
                ),
            },
            6: {
                "name": "Fulfillment Label Printer Failure",
                "subsystem": "logistics",
                "vehicle_section": "shipping_bay",
                "error_type": "WMS-LABEL-PRINTER-FAULT",
                "sensor_type": "label_printer",
                "affected_services": ["packaging-fulfillment", "card-printing-system"],
                "cascade_services": ["digital-marketplace"],
                "description": "Shipping label printers going offline or producing unreadable labels",
                "investigation_notes": (
                    "1. Check the Zebra printer error code: E1001 = print head overheated, E2003 = ribbon empty, E3005 = label gap detection failure, E4002 = paper out.\n"
                    "2. For OFFLINE status, verify the network connection: `ping <printer_ip>` and check the switch port: `show interface <port> status`.\n"
                    "3. HEAD_ERROR requires print head replacement — Zebra ZT411/ZT421 heads have a ~50km print life; check the odometer in the printer menu.\n"
                    "4. Unreadable labels (barcode scan failures) indicate print darkness is too low or the thermal ribbon is wrinkled — run a test label: `^XA^FO50,50^BY3^BCN,100,Y,N,N^FD1234567890^FS^XZ`.\n"
                    "5. Queue depth above 200 while the printer is offline means shipments are stacking up — redirect traffic to a backup Zebra printer immediately.\n"
                    "6. For carrier-specific label format issues (ZPL vs EPL), verify the printer firmware supports the required label format and update if needed."
                ),
                "remediation_action": "restart_label_printer",
                "error_message": (
                    "wms.shipping WMS-LABEL-PRINTER-FAULT printer={label_printer_id} "
                    "status={label_printer_status} error_code={label_error_code} "
                    "failed_labels={label_failed_count} window={label_window_min}m "
                    "carrier={label_carrier} queue_depth={label_queue_depth}"
                ),
                "stack_trace": (
                    "WMS Label Subsystem Diagnostic Report\n"
                    "--------------------------------------\n"
                    "Printer ID:     {label_printer_id}\n"
                    "Status:         {label_printer_status}\n"
                    "Error Code:     {label_error_code}\n"
                    "Failed Labels:  {label_failed_count} in last {label_window_min} minutes\n"
                    "Carrier:        {label_carrier}\n"
                    "Queue Depth:    {label_queue_depth} shipments pending\n"
                    "ZPL Version:    ZPL-II\n"
                    "Print Head:     NEEDS_REPLACEMENT\n"
                    "Last Maintenance: 45 days ago\n"
                    "Recommended Action: Replace print head, recalibrate label alignment"
                ),
            },
            7: {
                "name": "WiFi AP Disconnect Storm",
                "subsystem": "network_access",
                "vehicle_section": "wireless_lan",
                "error_type": "AP_DISCONNECTED",
                "sensor_type": "ap_status",
                "affected_services": ["wifi-controller", "network-controller"],
                "cascade_services": ["packaging-fulfillment", "card-printing-system"],
                "description": "Multiple wireless access points simultaneously losing connectivity to the controller",
                "investigation_notes": (
                    "1. Check the Mist dashboard for AP connectivity status and last-seen timestamps across the affected site.\n"
                    "2. Verify upstream switch port status: `show interface status | include AP` — a switch reboot or PoE budget exhaustion can take down multiple APs simultaneously.\n"
                    "3. Check PoE allocation: `show power inline` — if the switch PoE budget is exceeded, lower-priority APs will be shut down.\n"
                    "4. Verify CAPWAP/DTLS tunnel health between APs and the Mist cloud controller — firewall rules may be blocking UDP 2049.\n"
                    "5. If APs are on a shared VLAN, check for a broadcast storm or STP issue on that VLAN that could saturate AP management traffic.\n"
                    "6. As immediate remediation, power-cycle the affected switch stack or re-provision APs from the Mist cloud console."
                ),
                "remediation_action": "restart_access_point",
                "error_message": (
                    "AP_DISCONNECTED event_id=mist-evt-{ap_disconnect_count}: "
                    "{ap_disconnect_count} APs lost connectivity in {ap_disconnect_window}s, "
                    "including {ap_name} (site {ap_site}), "
                    "last CAPWAP heartbeat {ap_last_heartbeat}s ago"
                ),
                "stack_trace": (
                    '{{"type": "AP_DISCONNECTED", "event_id": "mist-evt-{ap_disconnect_count}", '
                    '"org_id": "fanatics-org-001", "site_id": "{ap_site}", '
                    '"ap_name": "{ap_name}", "ap_mac": "5c:5b:35:a1:b2:c3", '
                    '"timestamp": 1705329121, "duration": {ap_disconnect_window}, '
                    '"count": {ap_disconnect_count}, "last_seen": {ap_last_heartbeat}, '
                    '"reason": "CAPWAP heartbeat timeout", "firmware": "0.14.29313"}}'
                ),
            },
            8: {
                "name": "WiFi Channel Interference",
                "subsystem": "network_access",
                "vehicle_section": "wireless_lan",
                "error_type": "INTERFERENCE_DETECTED",
                "sensor_type": "rf_spectrum",
                "affected_services": ["wifi-controller", "network-controller"],
                "cascade_services": ["packaging-fulfillment"],
                "description": "Co-channel and adjacent-channel interference degrading wireless performance",
                "investigation_notes": (
                    "1. Check the Mist RRM (Radio Resource Management) dashboard for channel utilization heatmaps and neighbor AP counts.\n"
                    "2. High co-channel interference with many neighbor APs indicates over-deployment — reduce AP transmit power or disable radios on overlapping APs.\n"
                    "3. Verify channel assignments: in dense warehouse environments, use only non-overlapping 5GHz channels (36, 40, 44, 48 for UNII-1; 149, 153, 157, 161 for UNII-3).\n"
                    "4. Check for non-WiFi interference sources (microwave ovens, Bluetooth, cordless phones) using a spectrum analyzer or Mist's built-in spectrum analysis.\n"
                    "5. Enable Mist Auto-RRM to dynamically adjust channel and power assignments based on real-time RF conditions.\n"
                    "6. For persistent interference in warehouse environments, consider deploying directional antennas to reduce signal bleed between aisles."
                ),
                "remediation_action": "optimize_channels",
                "error_message": (
                    "INTERFERENCE_DETECTED event_id=mist-rf-{channel_number}: "
                    "ap_name={ap_name} channel={channel_number} "
                    "co_channel_interference={interference_pct}% "
                    "noise_floor={noise_floor_dbm}dBm "
                    "retransmit_rate={retransmit_pct}% "
                    "neighbor_aps={neighbor_ap_count}"
                ),
                "stack_trace": (
                    '{{"type": "INTERFERENCE_DETECTED", "event_id": "mist-rf-{channel_number}", '
                    '"ap_name": "{ap_name}", "band": "5GHz", "channel": {channel_number}, '
                    '"bandwidth": 40, "co_channel_interference": {interference_pct}, '
                    '"adjacent_channel_interference": 8.2, "noise_floor": {noise_floor_dbm}, '
                    '"retransmit_rate": {retransmit_pct}, "neighbor_aps": {neighbor_ap_count}, '
                    '"recommended_channel": 36, "rrm_action": "pending"}}'
                ),
            },
            9: {
                "name": "Client Authentication Storm",
                "subsystem": "network_access",
                "vehicle_section": "wireless_auth",
                "error_type": "AUTH_FAILURE_STORM",
                "sensor_type": "radius_auth",
                "affected_services": ["wifi-controller", "dns-dhcp-service"],
                "cascade_services": ["network-controller"],
                "description": "RADIUS authentication requests spiking beyond server capacity",
                "investigation_notes": (
                    "1. Check RADIUS server logs: `journalctl -u freeradius -f` or NPS Event Viewer — look for repeated Access-Reject with reason codes.\n"
                    "2. Identify the NAS (Network Access Server) generating the storm: the NAS IP in the logs points to a specific WLC or switch.\n"
                    "3. Common root cause: a certificate change on the RADIUS server breaks PEAP-MSCHAPv2 — all clients simultaneously retry authentication.\n"
                    "4. Check for a Group Policy update that changed supplicant settings: `netsh wlan show profiles` on affected Windows clients.\n"
                    "5. As immediate mitigation, enable RADIUS rate limiting on the WLC: set max auth requests per second per SSID.\n"
                    "6. If the RADIUS server is overloaded, temporarily switch the SSID to PSK or MAC-auth bypass for critical warehouse devices while investigating."
                ),
                "remediation_action": "reset_radius_service",
                "error_message": (
                    "AUTH_FAILURE_STORM event_id=mist-auth-storm: "
                    "rate={auth_requests_per_sec}/s (threshold {auth_threshold}/s), "
                    "failures={auth_failures} timeouts={auth_timeouts} "
                    "nas={radius_nas_ip} server={radius_server}"
                ),
                "stack_trace": (
                    '{{"type": "AUTH_FAILURE_STORM", "event_id": "mist-auth-storm", '
                    '"org_id": "fanatics-org-001", "nas_ip": "{radius_nas_ip}", '
                    '"radius_server": "{radius_server}", "auth_rate": {auth_requests_per_sec}, '
                    '"threshold": {auth_threshold}, "failures": {auth_failures}, '
                    '"timeouts": {auth_timeouts}, "eap_type": "PEAP-MSCHAPv2", '
                    '"ssid": "Fanatics-Corp", '
                    '"reason_codes": ["timeout", "reject", "invalid_credential"]}}'
                ),
            },
            10: {
                "name": "DNS Resolution Failure Over VPN",
                "subsystem": "network_services",
                "vehicle_section": "name_resolution",
                "error_type": "NAMED-SERVFAIL-FORWARDER",
                "sensor_type": "dns_query",
                "affected_services": ["dns-dhcp-service", "network-controller"],
                "cascade_services": ["digital-marketplace", "auction-engine", "cloud-inventory-scanner"],
                "description": "DNS queries traversing VPN tunnel failing to resolve internal records",
                "investigation_notes": (
                    "1. Verify VPN tunnel status first: if the tunnel carrying DNS traffic is down, all forwarded queries will fail — check `show vpn ike-sa` / `show vpn ipsec-sa`.\n"
                    "2. Test DNS resolution from within the tunnel: `dig @<forwarder_ip> <query_name> +tcp` — if TCP works but UDP fails, MTU/fragmentation is the issue.\n"
                    "3. Check `named.conf` forwarder configuration: ensure both primary and fallback forwarders are reachable over the VPN and DNS port 53 is permitted.\n"
                    "4. Run `rndc querylog on` to enable query logging on the DNS server, then trace the query path to identify where resolution breaks.\n"
                    "5. If the forwarder is in Azure, verify Azure Private DNS zone is linked to the correct VNet and conditional forwarding rules are configured.\n"
                    "6. As a workaround, add static host entries for critical internal services to `/etc/hosts` or Windows DNS client cache while resolving the VPN issue."
                ),
                "remediation_action": "restart_dns_forwarder",
                "error_message": (
                    "named[12345]: NAMED-SERVFAIL-FORWARDER: query '{dns_query_name}' "
                    "type {dns_query_type} via tunnel {vpn_tunnel_name}: "
                    "forwarder {dns_forwarder_ip} unreachable, fallback {dns_fallback_ip} "
                    "timeout after {dns_timeout_ms}ms, returning {dns_rcode}"
                ),
                "stack_trace": (
                    "named[12345]: debug: query '{dns_query_name}' IN {dns_query_type} +E(0)\n"
                    "named[12345]: debug: forwarding query to {dns_forwarder_ip} via {vpn_tunnel_name}\n"
                    "named[12345]: debug: send: no response from {dns_forwarder_ip}#53\n"
                    "named[12345]: debug: trying fallback forwarder {dns_fallback_ip}\n"
                    "named[12345]: debug: receive: timeout from {dns_fallback_ip}#53 after {dns_timeout_ms}ms\n"
                    "named[12345]: error: NAMED-SERVFAIL-FORWARDER: all forwarders unreachable for '{dns_query_name}'\n"
                    "named[12345]: debug: query failed (SERVFAIL) '{dns_query_name}/{dns_query_type}/IN': all forwarders failed"
                ),
            },
            11: {
                "name": "DHCP Lease Storm",
                "subsystem": "network_services",
                "vehicle_section": "address_management",
                "error_type": "DHCPD-LEASE-EXHAUSTION",
                "sensor_type": "dhcp_lease",
                "affected_services": ["dns-dhcp-service", "network-controller"],
                "cascade_services": ["wifi-controller", "packaging-fulfillment"],
                "description": "DHCP scope exhaustion from excessive DISCOVER/REQUEST rate",
                "investigation_notes": (
                    "1. Run `dhcpd -T` or check `dhcpd.leases` to list all active leases and identify which scope is exhausted.\n"
                    "2. Look for a rogue DHCP server: `show ip dhcp snooping binding` on the switch, or use a packet capture to find unauthorized DHCPOFFER packets.\n"
                    "3. High DISCOVER rate with many NAKs indicates clients are not getting leases — either the pool is truly full or lease times are too long.\n"
                    "4. Reduce lease duration from the default (24h) to 4-8h for warehouse WiFi devices that frequently roam between subnets.\n"
                    "5. Check for IP address conflicts: `arping -D <ip>` on suspected duplicate IPs — a rogue server offering overlapping ranges causes scope confusion.\n"
                    "6. Expand the DHCP scope or add a secondary scope with a DHCP relay (`ip helper-address`) if the subnet legitimately needs more addresses."
                ),
                "remediation_action": "expand_dhcp_scope",
                "error_message": (
                    "dhcpd[6789]: DHCPD-LEASE-EXHAUSTION: pool {dhcp_scope} at {dhcp_util_pct}% "
                    "({dhcp_active_leases}/{dhcp_total_leases} leases), "
                    "DISCOVER rate {dhcp_discover_rate}/s, {dhcp_nak_count} NAKs, "
                    "rogue server detected at {dhcp_rogue_ip}"
                ),
                "stack_trace": (
                    "dhcpd[6789]: info: DHCPDISCOVER from 00:11:22:33:44:55 via eth0\n"
                    "dhcpd[6789]: info: pool {dhcp_scope}: {dhcp_active_leases} of {dhcp_total_leases} leases active ({dhcp_util_pct}%)\n"
                    "dhcpd[6789]: warning: DHCPD-LEASE-EXHAUSTION: pool near capacity\n"
                    "dhcpd[6789]: warning: {dhcp_discover_rate} DHCPDISCOVER packets/sec (storm threshold: 50/s)\n"
                    "dhcpd[6789]: warning: {dhcp_nak_count} DHCPNAK sent — no available leases\n"
                    "dhcpd[6789]: alert: rogue DHCP server detected: {dhcp_rogue_ip} offering leases on {dhcp_scope}\n"
                    "dhcpd[6789]: info: lease pool statistics: free=0, backup=0, expired=3, abandoned=2"
                ),
            },
            12: {
                "name": "Auction Bid Latency Spike",
                "subsystem": "commerce",
                "vehicle_section": "bidding_platform",
                "error_type": "BID_LATENCY_SLA_BREACH",
                "sensor_type": "bid_processing",
                "affected_services": ["auction-engine", "digital-marketplace"],
                "cascade_services": ["network-controller", "firewall-gateway"],
                "description": "Real-time bid processing latency exceeding SLA thresholds",
                "investigation_notes": (
                    "1. Check the bid processing queue depth in the Go auction-engine metrics — a queue depth above 500 indicates the goroutine pool is saturated.\n"
                    "2. Examine WebSocket broadcast latency: `ws_delay_ms` above 1000ms means the hub.broadcastBidUpdate is falling behind real-time.\n"
                    "3. Profile the database: `EXPLAIN ANALYZE` on the bid INSERT and auction UPDATE queries — lock contention on the `auctions` table during high-bid periods is common.\n"
                    "4. Check Redis pub/sub for bid event fanout delays: `redis-cli --latency-history -i 1` — if Redis is slow, all downstream WebSocket clients stall.\n"
                    "5. Scale horizontally: increase the auction-engine replica count in EKS and verify the ALB is distributing WebSocket connections evenly.\n"
                    "6. For immediate relief, increase the goroutine pool size and bid queue buffer, and enable connection draining on the load balancer."
                ),
                "remediation_action": "scale_auction_service",
                "error_message": (
                    'level=error ts=2025-01-15T14:32:01.234Z caller=bid_processor.go:289 '
                    'msg="BID_LATENCY_SLA_BREACH" auction={auction_id} bid={bid_id} '
                    "latency_ms={bid_latency_ms} sla_ms={bid_sla_ms} "
                    "queue_depth={bid_queue_depth} ws_delay_ms={ws_delay_ms} "
                    "affected_bidders={affected_bidders}"
                ),
                "stack_trace": (
                    "goroutine 847 [running]:\n"
                    "runtime/debug.Stack()\n"
                    "\t/usr/local/go/src/runtime/debug/stack.go:24 +0x5e\n"
                    "github.com/fanatics/auction-engine/internal/processor.(*BidProcessor).ProcessBid(0xc000518000, "
                    "{{0xc000a12480, 0x24}}, {{0xc000a124c0, 0x26}}, 0x{bid_latency_ms})\n"
                    "\t/app/internal/processor/bid_processor.go:289 +0x3a2\n"
                    "github.com/fanatics/auction-engine/internal/processor.(*BidProcessor).handleBidQueue(0xc000518000)\n"
                    "\t/app/internal/processor/bid_processor.go:145 +0x1b8\n"
                    "github.com/fanatics/auction-engine/internal/ws.(*Hub).broadcastBidUpdate(0xc000420000, "
                    "{{0xc000a12480, 0x24}})\n"
                    "\t/app/internal/ws/hub.go:89 +0x204\n"
                    "created by github.com/fanatics/auction-engine/cmd/server.Run in goroutine 1\n"
                    "\t/app/cmd/server/main.go:67 +0x2a5"
                ),
            },
            13: {
                "name": "Payment Processing Timeout",
                "subsystem": "commerce",
                "vehicle_section": "payment_system",
                "error_type": "PAYMENT_GATEWAY_TIMEOUT",
                "sensor_type": "payment_gateway",
                "affected_services": ["digital-marketplace", "auction-engine"],
                "cascade_services": ["firewall-gateway"],
                "description": "Payment gateway requests timing out, affecting checkout and auction settlements",
                "investigation_notes": (
                    "1. Check the payment provider status page (e.g., status.stripe.com) — gateway timeouts are often caused by provider-side degradation.\n"
                    "2. Review the HTTP response codes: 504 (Gateway Timeout) and 503 (Service Unavailable) indicate the provider is overloaded; 429 means rate limiting.\n"
                    "3. Verify the firewall is not blocking or throttling outbound HTTPS to payment endpoints: `show session all filter destination <gateway_ip>`.\n"
                    "4. Check connection pool exhaustion in the marketplace service: `netstat -an | grep <gateway_ip> | wc -l` — too many TIME_WAIT connections indicate pool leak.\n"
                    "5. Implement circuit breaker pattern: after 3 consecutive timeouts to a provider, failover to the backup provider (e.g., Stripe -> Adyen).\n"
                    "6. Queue failed payment retries in SQS/SNS with exponential backoff rather than blocking the checkout flow — return a pending status to the user."
                ),
                "remediation_action": "reset_payment_gateway",
                "error_message": (
                    "[PaymentHandler] PAYMENT_GATEWAY_TIMEOUT: order={order_id} "
                    "provider={payment_provider} timeout={payment_timeout_ms}ms "
                    "gateway_code={gateway_response_code} "
                    "retry={payment_retry_count}/{payment_max_retries} "
                    "amount=${payment_amount}"
                ),
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "/app/marketplace/handlers/payment.py", line 178, in process_payment\n'
                    "    response = await self.gateway.charge(order_id, amount, provider)\n"
                    '  File "/app/marketplace/gateways/{payment_provider}.py", line 92, in charge\n'
                    "    result = await self._http.post(self.endpoint, json=payload, timeout={payment_timeout_ms}/1000)\n"
                    '  File "/app/venv/lib/python3.11/site-packages/httpx/_client.py", line 1574, in post\n'
                    '    raise ReadTimeout("Timed out while receiving data")\n'
                    "httpx.ReadTimeout: Payment gateway did not respond within {payment_timeout_ms}ms\n"
                    "PAYMENT_GATEWAY_TIMEOUT: order {order_id} via {payment_provider} — {gateway_response_code}"
                ),
            },
            14: {
                "name": "Product Catalog Sync Failure",
                "subsystem": "commerce",
                "vehicle_section": "catalog_system",
                "error_type": "CATALOG_SYNC_FAILURE",
                "sensor_type": "catalog_sync",
                "affected_services": ["digital-marketplace", "card-printing-system"],
                "cascade_services": ["auction-engine"],
                "description": "Product catalog replication between marketplace and printing system failing",
                "investigation_notes": (
                    "1. Check the catalog_replicator logs for the specific error detail — 'schema version mismatch' means a migration ran on one side but not the other.\n"
                    "2. For 'primary key conflict on sku column', identify the duplicate SKUs: `SELECT sku, COUNT(*) FROM products GROUP BY sku HAVING COUNT(*) > 1`.\n"
                    "3. 'Connection reset by peer' during sync indicates a network interruption — check if the VPN tunnel between AWS (printing) and marketplace DB is stable.\n"
                    "4. 'Timeout waiting for lock on products table' means a long-running transaction is holding a row lock — find it with `SELECT * FROM information_schema.innodb_trx`.\n"
                    "5. If sync has been broken for hours, do not attempt a full resync during business hours — schedule it for the maintenance window to avoid locking the catalog.\n"
                    "6. As a workaround, enable the read-only cache mode on the marketplace so users see stale-but-consistent data while the sync recovers."
                ),
                "remediation_action": "resync_catalog",
                "error_message": (
                    "[CatalogReplicator] CATALOG_SYNC_FAILURE: "
                    "{catalog_sync_failed}/{catalog_sync_total} records failed syncing "
                    '{catalog_source} -> {catalog_destination}, '
                    'last_sync={catalog_last_sync_min}m ago, '
                    'error="{catalog_error_detail}"'
                ),
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "/app/marketplace/sync/catalog_replicator.py", line 267, in sync_catalog\n'
                    "    result = await self.replicate_batch(source, dest, batch)\n"
                    '  File "/app/marketplace/sync/catalog_replicator.py", line 245, in replicate_batch\n'
                    "    async for record in batch:\n"
                    '  File "/app/marketplace/db/connector.py", line 134, in execute_batch\n'
                    '    raise DBSyncError("{catalog_error_detail}")\n'
                    "marketplace.exceptions.CatalogSyncError: CATALOG_SYNC_FAILURE — "
                    "{catalog_sync_failed}/{catalog_sync_total} records failed\n"
                    "  Source: {catalog_source}\n"
                    "  Destination: {catalog_destination}\n"
                    "  Last successful sync: {catalog_last_sync_min} minutes ago"
                ),
            },
            15: {
                "name": "Print Queue Overflow",
                "subsystem": "manufacturing",
                "vehicle_section": "production_line",
                "error_type": "MES-QUEUE-OVERFLOW",
                "sensor_type": "print_queue",
                "affected_services": ["card-printing-system", "packaging-fulfillment"],
                "cascade_services": ["digital-marketplace"],
                "description": "Print job queue exceeding buffer capacity, new jobs being rejected",
                "investigation_notes": (
                    "1. Check printer status on the MES console: `PAPER_JAM`, `INK_LOW`, `HEAD_CLOG`, or `OFFLINE` each require different physical intervention.\n"
                    "2. Review the oldest pending job age — jobs stuck for 30+ minutes indicate the printer is not processing, not just slow.\n"
                    "3. For HP Indigo 7K: check the BID (Binary Ink Developer) levels and impression drum status via the Indigo PrintOS dashboard.\n"
                    "4. Verify the RIP (Raster Image Processor) server is not the bottleneck: high CPU on the RIP server means complex card designs are choking the pipeline.\n"
                    "5. Redistribute queued jobs to other available printers: `mes-cli reassign-queue --from <printer> --to <available_printer> --priority high`.\n"
                    "6. If the queue is critically full, pause incoming orders from the marketplace and display a 'printing delayed' banner to prevent further queue growth."
                ),
                "remediation_action": "drain_print_queue",
                "error_message": (
                    "[PrintScheduler] MES-QUEUE-OVERFLOW: "
                    "queue={print_queue_depth}/{print_queue_max} ({print_queue_pct}%) "
                    "job={print_job_id} REJECTED, oldest_pending={print_oldest_job_min}m "
                    "printer={printer_name} status={printer_status}"
                ),
                "stack_trace": (
                    "com.fanatics.mes.exception.QueueOverflowException: "
                    "MES-QUEUE-OVERFLOW: queue capacity exceeded {print_queue_depth}/{print_queue_max}\n"
                    "\tat com.fanatics.mes.scheduler.PrintScheduler.enqueueJob(PrintScheduler.java:312)\n"
                    "\tat com.fanatics.mes.scheduler.PrintScheduler.processIncoming(PrintScheduler.java:245)\n"
                    "\tat com.fanatics.mes.queue.JobQueueManager.submit(JobQueueManager.java:189)\n"
                    "\tat com.fanatics.mes.api.PrintJobController.submitJob(PrintJobController.java:78)\n"
                    "\tat java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1136)\n"
                    "\tat java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:635)\n"
                    "\tat java.base/java.lang.Thread.run(Thread.java:842)\n"
                    "  Printer: {printer_name} Status: {printer_status}\n"
                    "  Job: {print_job_id} Oldest pending: {print_oldest_job_min}m"
                ),
            },
            16: {
                "name": "Quality Control Rejection Spike",
                "subsystem": "manufacturing",
                "vehicle_section": "quality_assurance",
                "error_type": "MES-QC-REJECT-THRESHOLD",
                "sensor_type": "qc_inspection",
                "affected_services": ["card-printing-system", "packaging-fulfillment"],
                "cascade_services": ["digital-marketplace", "auction-engine"],
                "description": "Automated quality inspection system rejecting cards above acceptable defect rate",
                "investigation_notes": (
                    "1. Identify the primary defect type: `color_registration_shift` and `die_cut_misalignment` are mechanical issues; `foil_stamp_incomplete` is heat/pressure related.\n"
                    "2. Check the QC camera calibration: if the vision system is miscalibrated, it may be rejecting good cards — run `mes-qc calibrate --line <line>`.\n"
                    "3. For `centering_off` defects, inspect the sheet feeder alignment and gripper pressure on the affected print line.\n"
                    "4. Review the defect rate trend: a gradual increase indicates wear (replace cutting dies or print heads); a sudden spike indicates a material batch problem.\n"
                    "5. Cross-reference the reject batch with the paper/cardstock lot number — a bad material lot will cause consistent defects across all printers.\n"
                    "6. If the defect rate exceeds 10%, halt the production line for mechanical inspection rather than wasting material on continued rejects."
                ),
                "remediation_action": "recalibrate_qc_sensors",
                "error_message": (
                    "[QCInspector] MES-QC-REJECT-THRESHOLD: batch={qc_batch_id} "
                    "rejected={qc_reject_count}/{qc_inspected_count} "
                    "({qc_reject_pct}% defect rate, threshold {qc_threshold_pct}%) "
                    "defect={qc_defect_type} line={qc_line_number}"
                ),
                "stack_trace": (
                    "com.fanatics.mes.exception.QCRejectException: "
                    "MES-QC-REJECT-THRESHOLD: defect rate {qc_reject_pct}% exceeds threshold {qc_threshold_pct}%\n"
                    "\tat com.fanatics.mes.quality.QCInspector.inspectBatch(QCInspector.java:234)\n"
                    "\tat com.fanatics.mes.quality.QCInspector.runInspection(QCInspector.java:178)\n"
                    "\tat com.fanatics.mes.quality.InspectionPipeline.process(InspectionPipeline.java:145)\n"
                    "\tat com.fanatics.mes.api.QCController.triggerInspection(QCController.java:56)\n"
                    "\tat java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1136)\n"
                    "\tat java.base/java.lang.Thread.run(Thread.java:842)\n"
                    "  Batch: {qc_batch_id} Line: {qc_line_number}\n"
                    "  Primary defect: {qc_defect_type}\n"
                    "  Inspected: {qc_inspected_count} Rejected: {qc_reject_count}"
                ),
            },
            17: {
                "name": "SSL Decryption Certificate Expiry",
                "subsystem": "security",
                "vehicle_section": "ssl_inspection",
                "error_type": "SYSTEM-cert-expire",
                "sensor_type": "certificate",
                "affected_services": ["firewall-gateway", "dns-dhcp-service"],
                "cascade_services": ["digital-marketplace", "auction-engine"],
                "description": "SSL decryption forward proxy certificate expiring or expired, breaking TLS inspection",
                "investigation_notes": (
                    "1. Run `show system certificate detail` to check expiration dates for all installed certificates.\n"
                    "2. Identify which decryption profile references the expiring cert: `show config running | match ssl-decrypt`.\n"
                    "3. Count affected policy rules: `show rule-hit-count vsys vsys1 rule-base decryption` — each rule referencing this profile will fail.\n"
                    "4. Generate a new CSR from PAN-OS: `request certificate generate ...` or import a renewed cert from the internal CA.\n"
                    "5. After replacement, commit and verify: `request certificate info` and test with `curl -v https://<internal-url>` from a client behind the firewall.\n"
                    "6. Set up certificate expiration monitoring: configure SNMP traps or syslog alerts for certs expiring within 30 days to prevent recurrence."
                ),
                "remediation_action": "renew_certificate",
                "error_message": (
                    "1,2025/01/15 14:32:01,007200001234,SYSTEM,general,0,"
                    "SYSTEM-cert-expire,Certificate '{cert_cn}' (serial {cert_serial}) "
                    "expires in {cert_days_remaining} days, decryption profile {cert_profile}, "
                    "affecting {cert_affected_rules} policy rules"
                ),
                "stack_trace": (
                    "> show system certificate detail\n"
                    "Certificate '{cert_cn}'\n"
                    "  Serial Number: {cert_serial}\n"
                    "  Issuer: CN=Fanatics-Internal-CA,O=Fanatics Inc\n"
                    "  Subject: CN={cert_cn}\n"
                    "  Not Before: Jan 15 00:00:00 2024 GMT\n"
                    "  Not After:  Jan 18 00:00:00 2025 GMT\n"
                    "  Days Remaining: {cert_days_remaining}\n"
                    "  Key Size: 2048\n"
                    "  Used by decryption profile: {cert_profile}\n"
                    "  Policy rules referencing: {cert_affected_rules}\n"
                    "  Status: EXPIRING"
                ),
            },
            18: {
                "name": "Firewall Session Table Exhaustion",
                "subsystem": "security",
                "vehicle_section": "perimeter_defense",
                "error_type": "SYSTEM-session-threshold",
                "sensor_type": "session_table",
                "affected_services": ["firewall-gateway", "network-controller"],
                "cascade_services": ["digital-marketplace", "auction-engine"],
                "description": "Firewall session table approaching maximum capacity, new connections being dropped",
                "investigation_notes": (
                    "1. Run `show session all filter count yes` to confirm active session count, then `show session info` for utilization percentage.\n"
                    "2. Identify top talkers: `show session all filter source <zone> count yes` — look for a single IP consuming disproportionate sessions.\n"
                    "3. Check for a DDoS or scan: `show session all filter application unknown` — unknown apps with high session counts suggest malicious traffic.\n"
                    "4. Review session timeout settings: `show running-config | match timeout` — aggressive TCP timeout defaults (3600s) may keep stale sessions alive.\n"
                    "5. Reduce TCP session timeout for non-critical zones: `set deviceconfig setting session timeout-tcp 1800`.\n"
                    "6. If a specific source is flooding, apply a DoS Protection Profile or temporarily block via `set security-rule deny-source <ip>`."
                ),
                "remediation_action": "flush_session_table",
                "error_message": (
                    "1,2025/01/15 14:32:01,007200001234,SYSTEM,session,0,"
                    "SYSTEM-session-threshold,Session table utilization critical: "
                    "{session_count}/{session_max} ({session_util_pct}%) in zone {fw_zone}, "
                    "{session_drops} new connections dropped, top source {top_source_ip}"
                ),
                "stack_trace": (
                    "> show session info\n"
                    "Number of sessions supported:    {session_max}\n"
                    "Number of active sessions:       {session_count}\n"
                    "Session table utilization:       {session_util_pct}%\n"
                    "Number of sessions dropped:      {session_drops}\n"
                    "  Zone: {fw_zone}\n"
                    "  Top source: {top_source_ip}\n"
                    "TCP sessions:    {session_count}\n"
                    "UDP sessions:    1245\n"
                    "ICMP sessions:   89\n"
                    "Session aging:   TCP default timeout 3600s"
                ),
            },
            19: {
                "name": "Orphaned Cloud Resource Alert",
                "subsystem": "cloud_ops",
                "vehicle_section": "asset_management",
                "error_type": "CLOUD-ORPHANED-RESOURCE",
                "sensor_type": "cloud_asset",
                "affected_services": ["cloud-inventory-scanner", "network-controller"],
                "cascade_services": ["firewall-gateway"],
                "description": "Cloud resources detected without owner tags or associated workloads",
                "investigation_notes": (
                    "1. Query the cloud-inventory-scanner report for full orphan details: resource type, region, age, and daily cost.\n"
                    "2. Cross-reference the resource ID with Terraform state: `terraform state list | grep <resource_id>` — if present, the tag was stripped by a manual edit.\n"
                    "3. Check CloudTrail/Activity Log/Audit Log for who created the resource: `aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceName,AttributeValue=<id>`.\n"
                    "4. If the resource has no security group rules allowing inbound traffic and no associated ENI/NIC, it is likely safe to terminate.\n"
                    "5. For resources older than 30 days with no owner, follow the governance runbook: tag as `pending-termination`, notify via Slack, terminate after 7-day grace.\n"
                    "6. Prevent recurrence by enforcing AWS SCP / Azure Policy / GCP Organization Policy that denies resource creation without required `owner` and `team` tags."
                ),
                "remediation_action": "tag_or_terminate_resource",
                "error_message": (
                    "cloud-governance CLOUD-ORPHANED-RESOURCE "
                    "resource_type={cloud_resource_type} resource_id={cloud_resource_id} "
                    "provider={cloud_resource_provider} region={cloud_resource_region} "
                    "age_days={cloud_resource_age_days} cost=${cloud_resource_cost_daily}/day "
                    "security_group={cloud_resource_sg} owner=NONE"
                ),
                "stack_trace": (
                    "Cloud Governance Scan Report\n"
                    "-----------------------------\n"
                    "Resource:       {cloud_resource_type} ({cloud_resource_id})\n"
                    "Provider:       {cloud_resource_provider}\n"
                    "Region:         {cloud_resource_region}\n"
                    "Created:        {cloud_resource_age_days} days ago\n"
                    "Daily Cost:     ${cloud_resource_cost_daily}\n"
                    "Security Group: {cloud_resource_sg}\n"
                    "Owner Tag:      MISSING\n"
                    "Team Tag:       MISSING\n"
                    "Compliance:     FAIL — no owner tag after 14-day grace period\n"
                    "Action:         Schedule for termination review"
                ),
            },
            20: {
                "name": "Cross-Cloud VPN Tunnel Flapping",
                "subsystem": "cloud_ops",
                "vehicle_section": "vpn_connectivity",
                "error_type": "VPN-TUNNEL-FLAP",
                "sensor_type": "vpn_tunnel",
                "affected_services": ["cloud-inventory-scanner", "network-controller"],
                "cascade_services": ["dns-dhcp-service", "firewall-gateway"],
                "description": "Site-to-site VPN tunnels between cloud providers repeatedly going up and down",
                "investigation_notes": (
                    "1. Check IKE Phase status: Phase 1 FAILED means pre-shared key mismatch or proposal mismatch; Phase 2 FAILED means IPSec SA negotiation issue.\n"
                    "2. Verify DPD (Dead Peer Detection) settings match on both ends — mismatched DPD intervals cause one side to tear down the tunnel while the other thinks it is up.\n"
                    "3. For AWS VPN: check `aws ec2 describe-vpn-connections --vpn-connection-id <id>` for tunnel status and CloudWatch VPN metrics.\n"
                    "4. For Azure VPN Gateway: check `az network vpn-connection show` and look for IKE SA rekey failures in the diagnostic logs.\n"
                    "5. MTU issues cause tunnel flapping under load — set TCP MSS clamping to 1360 on both VPN endpoints and test with large transfers.\n"
                    "6. If the tunnel is flapping on rekey (SA_EXPIRED), increase the IKE lifetime and IPSec SA lifetime to reduce rekey frequency during peak traffic."
                ),
                "remediation_action": "reset_vpn_tunnel",
                "error_message": (
                    "cloud-networking VPN-TUNNEL-FLAP tunnel={vpn_tunnel_name} "
                    "path={vpn_src_cloud}->{vpn_dst_cloud} flaps={vpn_flap_count} "
                    "window={vpn_flap_window}s state={vpn_current_state} "
                    "ike_phase={vpn_ike_phase} ike_status={vpn_ike_status} "
                    "last_dpd={vpn_last_dpd_sec}s"
                ),
                "stack_trace": (
                    "VPN Tunnel Diagnostic Report\n"
                    "------------------------------\n"
                    "Tunnel:         {vpn_tunnel_name}\n"
                    "Path:           {vpn_src_cloud} -> {vpn_dst_cloud}\n"
                    "Current State:  {vpn_current_state}\n"
                    "Flap Count:     {vpn_flap_count} in {vpn_flap_window}s\n"
                    "IKE Phase:      {vpn_ike_phase}\n"
                    "IKE Status:     {vpn_ike_status}\n"
                    "Last DPD:       {vpn_last_dpd_sec}s ago\n"
                    "Local Gateway:  10.0.1.1\n"
                    "Remote Gateway: 10.2.0.1\n"
                    "MTU:            1400\n"
                    "Rekey Interval: 3600s\n"
                    "Action:         Check IPSec SA, verify gateway reachability"
                ),
            },
        }

    # ── Topology ──────────────────────────────────────────────────────

    @property
    def service_topology(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "network-controller": [
                ("firewall-gateway", "/api/v1/firewall/sessions", "GET"),
                ("firewall-gateway", "/api/v1/firewall/policy-push", "POST"),
                ("dns-dhcp-service", "/api/v1/dns/zone-status", "GET"),
                ("dns-dhcp-service", "/api/v1/dhcp/scope-status", "GET"),
                ("wifi-controller", "/api/v1/wifi/ap-status", "GET"),
            ],
            "firewall-gateway": [
                ("dns-dhcp-service", "/api/v1/dns/resolve", "POST"),
                ("network-controller", "/api/v1/network/route-table", "GET"),
            ],
            "digital-marketplace": [
                ("auction-engine", "/api/v1/auction/active-listings", "GET"),
                ("auction-engine", "/api/v1/auction/place-bid", "POST"),
                ("card-printing-system", "/api/v1/printing/order-status", "GET"),
                ("card-printing-system", "/api/v1/printing/submit-job", "POST"),
                ("packaging-fulfillment", "/api/v1/fulfillment/ship-order", "POST"),
            ],
            "auction-engine": [
                ("digital-marketplace", "/api/v1/marketplace/listing-update", "POST"),
                ("digital-marketplace", "/api/v1/marketplace/payment-settle", "POST"),
            ],
            "card-printing-system": [
                ("packaging-fulfillment", "/api/v1/fulfillment/queue-package", "POST"),
                ("digital-marketplace", "/api/v1/marketplace/inventory-update", "POST"),
            ],
            "packaging-fulfillment": [
                ("cloud-inventory-scanner", "/api/v1/inventory/reconcile", "POST"),
                ("digital-marketplace", "/api/v1/marketplace/shipment-notify", "POST"),
            ],
            "cloud-inventory-scanner": [
                ("network-controller", "/api/v1/network/vpn-health", "GET"),
                ("firewall-gateway", "/api/v1/firewall/sg-audit", "GET"),
            ],
            "wifi-controller": [
                ("dns-dhcp-service", "/api/v1/dhcp/client-lease", "GET"),
                ("network-controller", "/api/v1/network/vlan-map", "GET"),
            ],
            "dns-dhcp-service": [
                ("network-controller", "/api/v1/network/interface-status", "GET"),
            ],
        }

    @property
    def entry_endpoints(self) -> dict[str, list[tuple[str, str]]]:
        return {
            "network-controller": [
                ("/api/v1/network/health", "GET"),
                ("/api/v1/network/topology", "GET"),
                ("/api/v1/network/config-push", "POST"),
            ],
            "firewall-gateway": [
                ("/api/v1/firewall/status", "GET"),
                ("/api/v1/firewall/threat-log", "GET"),
            ],
            "dns-dhcp-service": [
                ("/api/v1/dns/query", "POST"),
                ("/api/v1/dhcp/lease-report", "GET"),
                ("/api/v1/dns/health", "GET"),
            ],
            "digital-marketplace": [
                ("/api/v1/marketplace/browse", "GET"),
                ("/api/v1/marketplace/checkout", "POST"),
                ("/api/v1/marketplace/search", "GET"),
            ],
            "auction-engine": [
                ("/api/v1/auction/live", "GET"),
                ("/api/v1/auction/bid", "POST"),
            ],
            "card-printing-system": [
                ("/api/v1/printing/queue-status", "GET"),
                ("/api/v1/printing/submit", "POST"),
            ],
            "packaging-fulfillment": [
                ("/api/v1/fulfillment/status", "GET"),
                ("/api/v1/fulfillment/ship", "POST"),
            ],
            "wifi-controller": [
                ("/api/v1/wifi/dashboard", "GET"),
            ],
            "cloud-inventory-scanner": [
                ("/api/v1/inventory/scan", "POST"),
                ("/api/v1/inventory/compliance", "GET"),
            ],
        }

    @property
    def db_operations(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "digital-marketplace": [
                ("SELECT", "products", "SELECT id, name, price, stock FROM products WHERE category = ? AND status = 'active' ORDER BY listed_at DESC LIMIT 50"),
                ("INSERT", "orders", "INSERT INTO orders (user_id, product_id, quantity, total, status, created_at) VALUES (?, ?, ?, ?, 'pending', NOW())"),
                ("UPDATE", "inventory", "UPDATE inventory SET quantity = quantity - ? WHERE sku = ? AND quantity >= ?"),
            ],
            "auction-engine": [
                ("SELECT", "auctions", "SELECT id, current_bid, bid_count, end_time FROM auctions WHERE status = 'active' AND end_time > NOW()"),
                ("INSERT", "bids", "INSERT INTO bids (auction_id, bidder_id, amount, placed_at) VALUES (?, ?, ?, NOW())"),
                ("UPDATE", "auctions", "UPDATE auctions SET current_bid = ?, bid_count = bid_count + 1, last_bid_at = NOW() WHERE id = ? AND current_bid < ?"),
            ],
            "card-printing-system": [
                ("SELECT", "print_jobs", "SELECT job_id, card_design_id, quantity, priority, status FROM print_jobs WHERE status IN ('queued', 'printing') ORDER BY priority DESC"),
                ("UPDATE", "print_jobs", "UPDATE print_jobs SET status = ?, completed_at = NOW() WHERE job_id = ?"),
            ],
            "packaging-fulfillment": [
                ("SELECT", "shipments", "SELECT order_id, tracking_number, carrier, status FROM shipments WHERE created_at > NOW() - INTERVAL 24 HOUR AND status = 'pending'"),
                ("INSERT", "shipments", "INSERT INTO shipments (order_id, tracking_number, carrier, weight_oz, status) VALUES (?, ?, ?, ?, 'label_printed')"),
            ],
            "dns-dhcp-service": [
                ("SELECT", "dns_records", "SELECT fqdn, record_type, ttl, value FROM dns_records WHERE zone = ? AND record_type = ?"),
                ("SELECT", "dhcp_leases", "SELECT mac_addr, ip_addr, lease_start, lease_end, hostname FROM dhcp_leases WHERE scope = ? AND lease_end > NOW()"),
            ],
            "cloud-inventory-scanner": [
                ("SELECT", "cloud_resources", "SELECT resource_id, resource_type, provider, region, owner_tag, created_at FROM cloud_resources WHERE owner_tag IS NULL AND created_at < NOW() - INTERVAL 7 DAY"),
            ],
        }

    # ── Infrastructure ────────────────────────────────────────────────

    @property
    def hosts(self) -> list[dict[str, Any]]:
        return [
            {
                "host.name": "fanatics-aws-host-01",
                "host.id": "i-0f2a3b4c5d6e78901",
                "host.arch": "amd64",
                "host.type": "m5.xlarge",
                "host.image.id": "ami-0fedcba987654321",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8175M CPU @ 2.50GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "4",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.10.1.50", "172.16.1.10"],
                "host.mac": ["0a:2b:3c:4d:5e:6f", "0a:2b:3c:4d:5e:70"],
                "os.type": "linux",
                "os.description": "Amazon Linux 2023.6.20250115",
                "cloud.provider": "aws",
                "cloud.platform": "aws_ec2",
                "cloud.region": "us-east-1",
                "cloud.availability_zone": "us-east-1a",
                "cloud.account.id": "987654321012",
                "cloud.instance.id": "i-0f2a3b4c5d6e78901",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 200 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "fanatics-gcp-host-01",
                "host.id": "7823456789012345678",
                "host.arch": "amd64",
                "host.type": "e2-standard-4",
                "host.image.id": "projects/debian-cloud/global/images/debian-12-bookworm-v20250115",
                "host.cpu.model.name": "Intel(R) Xeon(R) CPU @ 2.20GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "7",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.128.1.20", "10.128.1.21"],
                "host.mac": ["42:01:0a:80:01:14", "42:01:0a:80:01:15"],
                "os.type": "linux",
                "os.description": "Debian GNU/Linux 12 (bookworm)",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "us-central1",
                "cloud.availability_zone": "us-central1-a",
                "cloud.account.id": "fanatics-infra-prod",
                "cloud.instance.id": "7823456789012345678",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 100 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "fanatics-azure-host-01",
                "host.id": "/subscriptions/fab-012/resourceGroups/fanatics-rg/providers/Microsoft.Compute/virtualMachines/fanatics-vm-01",
                "host.arch": "amd64",
                "host.type": "Standard_D4s_v3",
                "host.image.id": "Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "106",
                "host.cpu.stepping": "6",
                "host.cpu.cache.l2.size": 1310720,
                "host.ip": ["10.2.0.10", "10.2.0.11"],
                "host.mac": ["00:0d:3a:7e:8f:9a", "00:0d:3a:7e:8f:9b"],
                "os.type": "linux",
                "os.description": "Ubuntu 22.04.5 LTS",
                "cloud.provider": "azure",
                "cloud.platform": "azure_vm",
                "cloud.region": "eastus",
                "cloud.availability_zone": "eastus-1",
                "cloud.account.id": "fab-012-345-678",
                "cloud.instance.id": "fanatics-vm-01",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 128 * 1024 * 1024 * 1024,
            },
        ]

    @property
    def k8s_clusters(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "fanatics-eks-cluster",
                "provider": "aws",
                "platform": "aws_eks",
                "region": "us-east-1",
                "zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
                "os_description": "Amazon Linux 2",
                "services": ["card-printing-system", "digital-marketplace", "auction-engine"],
            },
            {
                "name": "fanatics-gke-cluster",
                "provider": "gcp",
                "platform": "gcp_gke",
                "region": "us-central1",
                "zones": ["us-central1-a", "us-central1-b", "us-central1-c"],
                "os_description": "Container-Optimized OS",
                "services": ["packaging-fulfillment", "wifi-controller", "cloud-inventory-scanner"],
            },
            {
                "name": "fanatics-aks-cluster",
                "provider": "azure",
                "platform": "azure_aks",
                "region": "eastus",
                "zones": ["eastus-1", "eastus-2", "eastus-3"],
                "os_description": "Ubuntu 22.04 LTS",
                "services": ["network-controller", "firewall-gateway", "dns-dhcp-service"],
            },
        ]

    # ── Theme ─────────────────────────────────────────────────────────

    @property
    def theme(self) -> UITheme:
        return UITheme(
            bg_primary="#0d1117",
            bg_secondary="#161b22",
            bg_tertiary="#21262d",
            accent_primary="#58a6ff",
            accent_secondary="#3fb950",
            text_primary="#e6edf3",
            text_secondary="#8b949e",
            text_accent="#58a6ff",
            status_nominal="#3fb950",
            status_warning="#d29922",
            status_critical="#f85149",
            status_info="#58a6ff",
            font_family="'Inter', system-ui, sans-serif",
            grid_background=True,
            chaos_title="Incident Simulator",
        )

    @property
    def countdown_config(self) -> CountdownConfig:
        return CountdownConfig(enabled=False)

    # ── Agent Config ──────────────────────────────────────────────────

    @property
    def agent_config(self) -> dict[str, Any]:
        return {
            "id": "fanatics-infra-analyst",
            "name": "Infrastructure & Network Analyst",
            "assessment_tool_name": "platform_load_assessment",
            "system_prompt": (
                "You are the Fanatics Infrastructure & Network Analyst, an expert AI assistant "
                "for enterprise network and infrastructure operations. You help NOC engineers "
                "investigate incidents, analyze telemetry data, and provide root cause analysis "
                "for fault conditions across 9 infrastructure services spanning AWS, GCP, and Azure. "
                "You have deep expertise in Cisco IOS-XE/NX-OS switching and routing, "
                "Palo Alto PAN-OS firewall management, Juniper Mist wireless LAN controllers, "
                "Infoblox DDI (DNS/DHCP/IPAM), AWS VPC networking, Azure Virtual Network, "
                "and GCP VPC. You understand BGP peering, spanning tree protocol, "
                "802.1X/RADIUS authentication, SSL inspection, and cross-cloud VPN tunneling. "
                "When investigating incidents, search for these vendor-specific identifiers in logs: "
                "Cisco syslog mnemonics (SW_MATM-4-MACFLAP_NOTIF, SPANTREE-2-TOPO_CHANGE, BGP-3-NOTIFICATION), "
                "PAN-OS system events (SYSTEM-session-threshold, SYSTEM-cpu-critical, SYSTEM-cert-expire), "
                "Juniper Mist events (AP_DISCONNECTED, INTERFERENCE_DETECTED, AUTH_FAILURE_STORM), "
                "DNS/DHCP faults (NAMED-SERVFAIL-FORWARDER, DHCPD-LEASE-EXHAUSTION), "
                "commerce errors (BID_LATENCY_SLA_BREACH, PAYMENT_GATEWAY_TIMEOUT, CATALOG_SYNC_FAILURE), "
                "manufacturing faults (MES-QUEUE-OVERFLOW, MES-QC-REJECT-THRESHOLD), "
                "warehouse faults (WMS-LABEL-PRINTER-FAULT, WMS-SCANNER-DESYNC), "
                "and cloud ops events (CLOUD-ORPHANED-RESOURCE, VPN-TUNNEL-FLAP). "
                "Log messages are in body.text — NEVER search the body field alone."
            ),
        }

    @property
    def assessment_tool_config(self) -> dict[str, Any]:
        return {
            "id": "platform_load_assessment",
            "description": (
                "Comprehensive platform load assessment. Evaluates all "
                "infrastructure services against event-day readiness criteria. "
                "Returns data for load evaluation across networking, DNS, "
                "VPN, firewall, and cloud infrastructure systems. "
                "Log message field: body.text (never use 'body' alone)."
            ),
        }

    @property
    def knowledge_base_docs(self) -> list[dict[str, Any]]:
        return []  # Populated by deployer from channel_registry

    # ── Service Classes ───────────────────────────────────────────────

    def get_service_classes(self) -> list[type]:
        from scenarios.fanatics.services.card_printing import CardPrintingSystemService
        from scenarios.fanatics.services.digital_marketplace import DigitalMarketplaceService
        from scenarios.fanatics.services.auction_engine import AuctionEngineService
        from scenarios.fanatics.services.packaging_fulfillment import PackagingFulfillmentService
        from scenarios.fanatics.services.wifi_controller import WifiControllerService
        from scenarios.fanatics.services.cloud_inventory_scanner import CloudInventoryScannerService
        from scenarios.fanatics.services.network_controller import NetworkControllerService
        from scenarios.fanatics.services.firewall_gateway import FirewallGatewayService
        from scenarios.fanatics.services.dns_dhcp_service import DnsDhcpService

        return [
            CardPrintingSystemService,
            DigitalMarketplaceService,
            AuctionEngineService,
            PackagingFulfillmentService,
            WifiControllerService,
            CloudInventoryScannerService,
            NetworkControllerService,
            FirewallGatewayService,
            DnsDhcpService,
        ]

    # ── Trace Attributes & RCA ───────────────────────────────────────

    def get_trace_attributes(self, service_name: str, rng) -> dict:
        met_s = int(time.time()) % 86400
        base = {
            "platform.region": rng.choice(["us-east-1", "us-central1", "eastus"]),
            "platform.traffic_tier": rng.choice(["normal", "normal", "elevated", "peak"]),
        }
        svc_attrs = {
            "card-printing-system": {
                "print.batch_id": f"BATCH-{rng.randint(1000, 9999)}",
                "print.card_rarity": rng.choice(["common", "uncommon", "rare", "ultra-rare", "1-of-1"]),
                "print.line_number": rng.choice(["LINE-A", "LINE-B", "LINE-C"]),
                "print.substrate": rng.choice(["standard-cardstock", "chrome-foil", "refractor-film", "acetate"]),
            },
            "digital-marketplace": {
                "marketplace.listing_type": rng.choice(["buy-now", "auction", "make-offer", "pre-order"]),
                "marketplace.price_tier": rng.choice(["budget", "mid-range", "premium", "ultra-premium"]),
                "marketplace.cart_items": rng.randint(1, 12),
                "marketplace.session_type": rng.choice(["browse", "search", "checkout", "watchlist"]),
            },
            "auction-engine": {
                "auction.state": rng.choice(["accepting_bids", "going_once", "going_twice", "closed", "extending"]),
                "auction.bid_count": rng.randint(1, 250),
                "auction.reserve_met": rng.choice([True, True, True, False]),
                "auction.time_remaining_s": rng.randint(0, 7200),
            },
            "packaging-fulfillment": {
                "warehouse.zone": rng.choice(["receiving", "storage-A", "storage-B", "packing", "shipping-dock"]),
                "warehouse.pick_velocity": rng.choice(["normal", "express", "priority", "rush"]),
                "warehouse.carrier": rng.choice(["UPS", "FedEx", "USPS", "DHL"]),
                "warehouse.package_weight_oz": round(rng.uniform(2.0, 48.0), 1),
            },
            "wifi-controller": {
                "wifi.ssid": rng.choice(["Fanatics-Corp", "Fanatics-Warehouse", "Fanatics-Guest", "Fanatics-IoT"]),
                "wifi.band": rng.choice(["2.4GHz", "5GHz", "6GHz"]),
                "wifi.ap_count": rng.randint(20, 120),
                "wifi.client_count": rng.randint(50, 800),
            },
            "cloud-inventory-scanner": {
                "cloud_scan.provider": rng.choice(["aws", "azure", "gcp"]),
                "cloud_scan.resource_count": rng.randint(200, 5000),
                "cloud_scan.compliance_pct": round(rng.uniform(75.0, 99.5), 1),
                "cloud_scan.orphan_count": rng.randint(0, 45),
            },
            "network-controller": {
                "network.switch_tier": rng.choice(["core", "distribution", "access", "spine", "leaf"]),
                "network.vlan_count": rng.randint(20, 200),
                "network.port_utilization_pct": round(rng.uniform(30.0, 95.0), 1),
                "network.protocol": rng.choice(["OSPF", "BGP", "RSTP", "LACP"]),
            },
            "firewall-gateway": {
                "firewall.zone_pair": rng.choice(["TRUST->UNTRUST", "UNTRUST->DMZ", "TRUST->DMZ", "DMZ->TRUST"]),
                "firewall.policy_count": rng.randint(400, 2500),
                "firewall.session_rate": rng.randint(2000, 12000),
                "firewall.threat_level": rng.choice(["low", "medium", "high", "critical"]),
            },
            "dns-dhcp-service": {
                "dns.query_type": rng.choice(["A", "AAAA", "CNAME", "SRV", "PTR", "MX"]),
                "dns.zone": rng.choice(["fanatics.internal", "warehouse.local", "collectibles.prod"]),
                "dhcp.scope_utilization_pct": round(rng.uniform(40.0, 98.0), 1),
                "dhcp.lease_duration_s": rng.choice([3600, 7200, 14400, 28800, 86400]),
            },
        }
        base.update(svc_attrs.get(service_name, {}))
        return base

    def get_rca_clues(self, channel: int, service_name: str, rng) -> dict:
        clues = {
            1: {  # MAC Address Flapping
                "network-controller": {"switching.flap_port": rng.choice(["Gi0/0/1", "Gi0/0/3", "Te1/0/2"]), "switching.mac_table_util_pct": round(rng.uniform(85, 98), 1)},
                "dns-dhcp-service": {"dhcp.arp_conflict_detected": True, "dhcp.stale_lease_mac": "00:11:22:33:44:55"},
                "firewall-gateway": {"firewall.arp_inspection_failures": rng.randint(20, 200), "firewall.zone_affected": "TRUST"},
                "wifi-controller": {"wifi.client_roam_storm": True, "wifi.affected_ssid": "Fanatics-Warehouse"},
            },
            2: {  # Spanning Tree Topology Change
                "network-controller": {"stp.root_bridge_change": True, "stp.tcn_source_port": rng.choice(["Gi0/0/2", "Po1", "Te1/0/1"])},
                "firewall-gateway": {"firewall.l2_loop_detected": True, "firewall.broadcast_storm_pps": rng.randint(5000, 50000)},
                "dns-dhcp-service": {"dns.resolution_flapping": True, "dns.affected_zone": "fanatics.internal"},
                "wifi-controller": {"wifi.uplink_state": "flapping", "wifi.ap_isolation_triggered": rng.randint(2, 10)},
            },
            3: {  # BGP Peer Flapping
                "network-controller": {"bgp.hold_timer_misconfig": True, "bgp.prefix_withdraw_count": rng.randint(50, 500)},
                "firewall-gateway": {"firewall.bgp_port_179_drops": rng.randint(10, 100), "firewall.policy_id_blocking": f"rule-{rng.randint(100,999)}"},
                "dns-dhcp-service": {"dns.forwarder_unreachable": True, "dns.affected_queries_pct": round(rng.uniform(30, 80), 1)},
                "cloud-inventory-scanner": {"cloud_scan.cross_cloud_route_missing": True, "cloud_scan.affected_provider": rng.choice(["aws", "azure"])},
            },
            4: {  # Warehouse Scanner Desync
                "packaging-fulfillment": {"warehouse.inventory_drift_items": rng.randint(20, 200), "warehouse.scanner_firmware": rng.choice(["3.0.5", "3.1.8"])},
                "cloud-inventory-scanner": {"cloud_scan.physical_digital_mismatch": rng.randint(10, 100), "cloud_scan.reconciliation_failures": rng.randint(5, 50)},
                "digital-marketplace": {"marketplace.phantom_stock_skus": rng.randint(5, 50), "marketplace.oversold_orders": rng.randint(1, 20)},
                "card-printing-system": {"print.reprint_triggered_by_desync": rng.randint(3, 30), "print.inventory_hold": True},
            },
            5: {  # Firewall CPU Overload
                "firewall-gateway": {"firewall.dp_cpu_offender": rng.choice(["ssl-decrypt", "threat-prevention", "url-filtering"]), "firewall.packet_buffer_pct": round(rng.uniform(80, 98), 1)},
                "network-controller": {"network.throughput_degraded": True, "network.latency_spike_ms": rng.randint(50, 500)},
                "dns-dhcp-service": {"dns.query_timeout_pct": round(rng.uniform(15, 60), 1), "dns.upstream_latency_ms": rng.randint(200, 2000)},
                "digital-marketplace": {"marketplace.page_load_ms": rng.randint(3000, 15000), "marketplace.ssl_handshake_failures": rng.randint(10, 100)},
            },
            6: {  # Fulfillment Label Printer Failure
                "packaging-fulfillment": {"warehouse.label_printer_error": rng.choice(["E1001", "E2003", "E3005"]), "warehouse.shipments_held": rng.randint(50, 500)},
                "card-printing-system": {"print.completed_no_label": rng.randint(20, 200), "print.staging_area_full": True},
                "digital-marketplace": {"marketplace.shipping_delay_orders": rng.randint(50, 500), "marketplace.tracking_unavailable_count": rng.randint(30, 300)},
            },
            7: {  # WiFi AP Disconnect Storm
                "wifi-controller": {"wifi.capwap_tunnel_down": rng.randint(5, 20), "wifi.poe_budget_exceeded": rng.choice([True, False])},
                "network-controller": {"network.switch_port_down_count": rng.randint(3, 15), "network.poe_watts_available": rng.randint(0, 50)},
                "packaging-fulfillment": {"warehouse.scanner_offline_count": rng.randint(2, 10), "warehouse.pick_rate_degraded": True},
                "card-printing-system": {"print.mes_connectivity_lost": True, "print.jobs_queued_offline": rng.randint(10, 100)},
            },
            8: {  # WiFi Channel Interference
                "wifi-controller": {"wifi.co_channel_aps": rng.randint(5, 15), "wifi.rrm_auto_channel_change": rng.choice([True, False])},
                "network-controller": {"network.wlan_vlan_util_pct": round(rng.uniform(70, 95), 1), "network.broadcast_domain_size": rng.randint(200, 800)},
                "packaging-fulfillment": {"warehouse.scanner_retry_rate_pct": round(rng.uniform(15, 50), 1), "warehouse.throughput_degraded": True},
            },
            9: {  # Client Authentication Storm
                "wifi-controller": {"wifi.radius_queue_depth": rng.randint(200, 1000), "wifi.eap_type": "PEAP-MSCHAPv2"},
                "dns-dhcp-service": {"dhcp.new_lease_failures": rng.randint(20, 200), "dhcp.auth_dependent_scope": rng.choice(["10.1.0.0/24", "10.2.0.0/24"])},
                "network-controller": {"network.dot1x_failures_per_sec": rng.randint(50, 500), "network.radius_server_load_pct": round(rng.uniform(85, 100), 1)},
            },
            10: {  # DNS Resolution Failure Over VPN
                "dns-dhcp-service": {"dns.forwarder_timeout_ms": rng.randint(3000, 10000), "dns.vpn_dependent_zones": rng.randint(3, 12)},
                "network-controller": {"network.vpn_tunnel_state": "DOWN", "network.ipsec_sa_expired": True},
                "digital-marketplace": {"marketplace.internal_api_dns_failures": rng.randint(50, 500), "marketplace.service_discovery_degraded": True},
                "auction-engine": {"auction.api_hostname_unresolvable": True, "auction.failover_to_ip": True},
                "cloud-inventory-scanner": {"cloud_scan.cross_cloud_dns_broken": True, "cloud_scan.affected_provider": rng.choice(["aws", "azure", "gcp"])},
            },
            11: {  # DHCP Lease Storm
                "dns-dhcp-service": {"dhcp.pool_exhaustion_pct": round(rng.uniform(95, 100), 1), "dhcp.rogue_server_detected": True},
                "network-controller": {"network.dhcp_snooping_violations": rng.randint(10, 200), "network.affected_vlan": rng.choice([100, 200, 300])},
                "wifi-controller": {"wifi.clients_no_ip": rng.randint(20, 200), "wifi.dhcp_relay_failures": rng.randint(10, 100)},
                "packaging-fulfillment": {"warehouse.device_offline_no_ip": rng.randint(5, 30), "warehouse.zone_affected": rng.choice(["receiving", "packing", "shipping"])},
            },
            12: {  # Auction Bid Latency Spike
                "auction-engine": {"auction.goroutine_pool_saturated": True, "auction.bid_queue_depth": rng.randint(500, 2000)},
                "digital-marketplace": {"marketplace.ws_broadcast_delay_ms": rng.randint(1000, 5000), "marketplace.stale_bid_display_count": rng.randint(10, 200)},
                "network-controller": {"network.alb_latency_ms": rng.randint(100, 1000), "network.connection_draining": False},
                "firewall-gateway": {"firewall.ws_inspection_overhead_ms": rng.randint(20, 200), "firewall.deep_packet_inspection_enabled": True},
            },
            13: {  # Payment Processing Timeout
                "digital-marketplace": {"marketplace.payment_circuit_breaker": rng.choice(["CLOSED", "HALF_OPEN", "OPEN"]), "marketplace.failed_checkout_count": rng.randint(10, 200)},
                "auction-engine": {"auction.settlement_backlog": rng.randint(5, 100), "auction.payment_retry_queue": rng.randint(3, 50)},
                "firewall-gateway": {"firewall.outbound_https_throttled": rng.choice([True, False]), "firewall.payment_gateway_sessions": rng.randint(500, 5000)},
            },
            14: {  # Product Catalog Sync Failure
                "digital-marketplace": {"marketplace.catalog_staleness_min": rng.randint(30, 360), "marketplace.sku_mismatch_count": rng.randint(20, 500)},
                "card-printing-system": {"print.catalog_version": f"v{rng.randint(1,5)}.{rng.randint(0,9)}.{rng.randint(0,9)}", "print.schema_migration_pending": True},
                "auction-engine": {"auction.listing_sync_gap": rng.randint(10, 200), "auction.phantom_listings": rng.randint(2, 30)},
            },
            15: {  # Print Queue Overflow
                "card-printing-system": {"print.printer_status": rng.choice(["PAPER_JAM", "INK_LOW", "HEAD_CLOG"]), "print.rip_server_cpu_pct": round(rng.uniform(85, 100), 1)},
                "packaging-fulfillment": {"warehouse.pending_packages_no_cards": rng.randint(20, 200), "warehouse.fulfillment_sla_breach": True},
                "digital-marketplace": {"marketplace.order_delay_notification_count": rng.randint(50, 500), "marketplace.printing_backlog_hours": rng.randint(4, 48)},
            },
            16: {  # Quality Control Rejection Spike
                "card-printing-system": {"print.defect_type": rng.choice(["color_registration_shift", "die_cut_misalignment", "foil_stamp_incomplete"]), "print.material_lot": f"LOT-{rng.randint(2024001, 2024999)}"},
                "packaging-fulfillment": {"warehouse.reprint_queue_depth": rng.randint(20, 200), "warehouse.wasted_material_sheets": rng.randint(50, 500)},
                "digital-marketplace": {"marketplace.out_of_stock_skus": rng.randint(5, 50), "marketplace.customer_refund_queue": rng.randint(3, 30)},
                "auction-engine": {"auction.delayed_shipment_auctions": rng.randint(2, 20), "auction.buyer_dispute_count": rng.randint(1, 10)},
            },
            17: {  # SSL Decryption Certificate Expiry
                "firewall-gateway": {"firewall.cert_serial": f"{rng.randint(100000,999999):X}", "firewall.decryption_bypass_count": rng.randint(100, 5000)},
                "dns-dhcp-service": {"dns.tls_dot_failures": rng.randint(10, 200), "dns.fallback_to_udp": True},
                "digital-marketplace": {"marketplace.checkout_ssl_errors": rng.randint(20, 300), "marketplace.customer_complaints": rng.randint(5, 50)},
                "auction-engine": {"auction.wss_handshake_failures": rng.randint(10, 100), "auction.bidder_disconnects": rng.randint(5, 80)},
            },
            18: {  # Firewall Session Table Exhaustion
                "firewall-gateway": {"firewall.top_session_source": f"10.{rng.randint(1,254)}.{rng.randint(1,254)}.{rng.randint(1,254)}", "firewall.tcp_timeout_config": 3600},
                "network-controller": {"network.qos_drops_increasing": True, "network.affected_queue": rng.choice(["Q1-PRIORITY", "Q3-BEST-EFFORT"])},
                "digital-marketplace": {"marketplace.connection_pool_exhausted": True, "marketplace.pending_checkouts": rng.randint(50, 500)},
                "auction-engine": {"auction.websocket_failures": rng.randint(20, 200), "auction.bid_timeouts": rng.randint(5, 50)},
            },
            19: {  # Orphaned Cloud Resource Alert
                "cloud-inventory-scanner": {"cloud_scan.orphan_daily_cost_usd": round(rng.uniform(50, 2000), 2), "cloud_scan.oldest_orphan_days": rng.randint(14, 180)},
                "network-controller": {"network.orphan_security_group_rules": rng.randint(5, 50), "network.untagged_eni_count": rng.randint(3, 30)},
                "firewall-gateway": {"firewall.orphan_nat_rules": rng.randint(2, 20), "firewall.stale_address_objects": rng.randint(10, 100)},
            },
            20: {  # Cross-Cloud VPN Tunnel Flapping
                "cloud-inventory-scanner": {"cloud_scan.vpn_dependent_services": rng.randint(3, 9), "cloud_scan.cross_cloud_latency_ms": rng.randint(200, 2000)},
                "network-controller": {"network.ike_rekey_failures": rng.randint(3, 20), "network.mtu_mismatch_detected": rng.choice([True, False])},
                "dns-dhcp-service": {"dns.cross_cloud_resolution_broken": True, "dns.conditional_forwarder_down": rng.choice(["aws-to-azure", "gcp-to-azure"])},
                "firewall-gateway": {"firewall.ipsec_esp_drops": rng.randint(100, 5000), "firewall.dpd_timeout_count": rng.randint(5, 50)},
            },
        }
        channel_clues = clues.get(channel, {})
        return channel_clues.get(service_name, {})

    def get_correlation_attribute(self, channel: int, is_error: bool, rng) -> dict:
        correlation_attrs = {
            1: ("deployment.release_train", "net-core-v2.8.1-canary"),
            2: ("infra.stp_firmware", "ios-xe-17.9.4a-prerelease"),
            3: ("network.bgp_policy_rev", "route-policy-v3.2.0-rc1"),
            4: ("deployment.scanner_firmware", "mc9300-fw-3.0.5-known-bug"),
            5: ("deployment.threat_sig_ver", "content-8845-8432-experimental"),
            6: ("infra.label_zpl_version", "zebra-zpl-ii-v6.1-patched"),
            7: ("deployment.ap_firmware", "mist-fw-0.14.29313-beta"),
            8: ("infra.rrm_algorithm", "auto-rrm-v3.1-aggressive"),
            9: ("deployment.radius_config", "nps-policy-2025q1-draft"),
            10: ("network.vpn_ike_profile", "ikev2-profile-aes256-sha512"),
            11: ("infra.dhcp_failover_mode", "dhcpd-hot-standby-v2"),
            12: ("deployment.auction_runtime", "go1.22-race-detect-enabled"),
            13: ("infra.payment_gateway_sdk", "stripe-sdk-v14.2.0-beta3"),
            14: ("deployment.catalog_schema_ver", "schema-v5.3.0-migration-pending"),
            15: ("infra.rip_server_config", "fiery-rip-v4.0.1-preview"),
            16: ("deployment.qc_vision_model", "defect-detect-v2.1.0-retrained"),
            17: ("infra.cert_chain_bundle", "internal-ca-v2-cross-signed"),
            18: ("infra.fw_session_config", "pan-os-11.1.3-hotfix2"),
            19: ("infra.cloud_policy_ver", "org-policy-v2.4.0-unenforced"),
            20: ("network.vpn_gw_firmware", "vgw-strongswan-5.9.14-rc2"),
        }
        attr_key, attr_val = correlation_attrs.get(channel, ("deployment.release_train", "unknown"))
        # 90% on errors, 5% on healthy
        if is_error:
            if rng.random() < 0.90:
                return {attr_key: attr_val}
        else:
            if rng.random() < 0.05:
                return {attr_key: attr_val}
        return {}

    # ── Fault Parameters ──────────────────────────────────────────────

    def get_fault_params(self, channel: int) -> dict[str, Any]:
        return {
            # ── Network core (channels 1-3) ──
            "mac_address": f"{random.randint(0,255):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}:{random.randint(0,255):02x}",
            "interface_src": random.choice(["Gi0/0/1", "Gi0/0/2", "Gi0/0/3", "Te1/0/1", "Te1/0/2"]),
            "interface_dst": random.choice(["Gi0/0/4", "Gi0/0/5", "Te1/0/3", "Te1/0/4"]),
            "interface": random.choice(["Gi0/0/1", "Gi0/0/2", "Te1/0/1", "Te1/0/2", "Po1"]),
            "vlan_id": random.choice([100, 200, 300, 400, 500, 1000]),
            "flap_count": random.randint(10, 50),
            "flap_window": random.randint(5, 30),
            "stp_instance": random.randint(0, 15),
            "tc_count": random.randint(15, 80),
            "tc_window": random.randint(10, 60),
            "bridge_id": f"8000.{random.randint(0,255):02x}{random.randint(0,255):02x}.{random.randint(0,255):02x}{random.randint(0,255):02x}.{random.randint(0,255):02x}{random.randint(0,255):02x}",
            "bgp_peer_ip": f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "bgp_peer_as": random.choice([64512, 64513, 64514, 65001, 65002, 65100]),
            "bgp_flap_count": random.randint(5, 25),
            "bgp_flap_window": random.randint(30, 300),
            "bgp_last_state": random.choice(["Idle", "Active", "OpenSent", "OpenConfirm"]),
            "bgp_notification": random.choice([
                "Hold Timer Expired (code 4/0)",
                "Cease/Admin Reset (code 6/4)",
                "UPDATE Message Error (code 3/1)",
                "FSM Error (code 5/0)",
            ]),

            # ── Security (channels 4-6) ──
            "session_count": random.randint(58000, 63500),
            "session_max": 64000,
            "session_util_pct": round(random.uniform(90.0, 99.5), 1),
            "session_drops": random.randint(50, 500),
            "fw_zone": random.choice(["TRUST", "UNTRUST", "DMZ"]),
            "top_source_ip": f"10.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
            "fw_dp_cpu_pct": round(random.uniform(85.0, 99.0), 1),
            "fw_mgmt_cpu_pct": round(random.uniform(60.0, 90.0), 1),
            "fw_cpu_threshold": 80,
            "fw_buffer_pct": round(random.uniform(75.0, 98.0), 1),
            "fw_policy_count": random.randint(800, 2500),
            "cert_cn": random.choice([
                "*.fanatics.internal", "forward-proxy.fanatics.com",
                "ssl-inspect.collectibles.prod", "tls-decrypt.warehouse.local",
            ]),
            "cert_serial": f"{random.randint(100000,999999):X}",
            "cert_days_remaining": random.randint(-5, 3),
            "cert_profile": random.choice(["ssl-forward-proxy", "ssl-inbound-inspection", "tls-decrypt-all"]),
            "cert_affected_rules": random.randint(15, 80),

            # ── Network access (channels 7-9) ──
            "ap_name": random.choice([
                "AP-WAREHOUSE-01", "AP-WAREHOUSE-02", "AP-PRINT-FLOOR-01",
                "AP-OFFICE-01", "AP-SHIPPING-01", "AP-DOCK-01",
            ]),
            "ap_site": random.choice(["warehouse-east", "print-facility", "office-hq", "shipping-dock"]),
            "ap_disconnect_count": random.randint(5, 20),
            "ap_disconnect_window": random.randint(10, 60),
            "ap_last_heartbeat": random.randint(30, 300),
            "channel_number": random.choice([1, 6, 11, 36, 40, 44, 48, 149, 153, 157, 161]),
            "interference_pct": round(random.uniform(25.0, 75.0), 1),
            "noise_floor_dbm": round(random.uniform(-80.0, -60.0), 1),
            "retransmit_pct": round(random.uniform(10.0, 40.0), 1),
            "neighbor_ap_count": random.randint(5, 20),
            "auth_requests_per_sec": random.randint(200, 1000),
            "auth_threshold": 100,
            "auth_failures": random.randint(50, 300),
            "auth_timeouts": random.randint(20, 150),
            "radius_nas_ip": f"10.1.{random.randint(1,10)}.{random.randint(1,254)}",
            "radius_server": random.choice(["radius-01.fanatics.internal", "radius-02.fanatics.internal"]),

            # ── Network services (channels 10-11) ──
            "dns_query_name": random.choice([
                "marketplace.fanatics.internal", "auction-api.collectibles.prod",
                "card-printer-01.warehouse.local", "inventory.cloud-ops.internal",
            ]),
            "dns_query_type": random.choice(["A", "AAAA", "CNAME", "SRV"]),
            "vpn_tunnel_name": random.choice(["aws-to-azure-01", "aws-to-gcp-01", "gcp-to-azure-01"]),
            "dns_rcode": random.choice(["SERVFAIL", "REFUSED", "NXDOMAIN"]),
            "dns_forwarder_ip": random.choice(["10.0.0.53", "10.1.0.53", "168.63.129.16"]),
            "dns_fallback_ip": random.choice(["10.0.1.53", "10.2.0.53"]),
            "dns_timeout_ms": random.randint(3000, 10000),
            "dhcp_scope": random.choice(["10.1.0.0/24", "10.2.0.0/24", "172.16.0.0/22", "192.168.1.0/24"]),
            "dhcp_util_pct": round(random.uniform(92.0, 100.0), 1),
            "dhcp_active_leases": random.randint(235, 254),
            "dhcp_total_leases": 254,
            "dhcp_discover_rate": random.randint(50, 300),
            "dhcp_nak_count": random.randint(10, 100),
            "dhcp_rogue_ip": f"192.168.{random.randint(1,254)}.{random.randint(1,254)}",

            # ── Commerce (channels 12-14) ──
            "auction_id": f"AUC-{random.randint(100000,999999)}",
            "bid_id": f"BID-{random.randint(1000000,9999999)}",
            "bid_latency_ms": random.randint(500, 5000),
            "bid_sla_ms": 200,
            "bid_queue_depth": random.randint(100, 2000),
            "ws_delay_ms": random.randint(200, 3000),
            "affected_bidders": random.randint(10, 500),
            "order_id": f"ORD-{random.randint(100000,999999)}",
            "payment_provider": random.choice(["Stripe", "PayPal", "Adyen", "Braintree"]),
            "payment_timeout_ms": random.randint(5000, 30000),
            "gateway_response_code": random.choice(["504", "408", "429", "503"]),
            "payment_retry_count": random.randint(1, 3),
            "payment_max_retries": 3,
            "payment_amount": round(random.uniform(9.99, 4999.99), 2),
            "catalog_sync_failed": random.randint(50, 500),
            "catalog_sync_total": random.randint(1000, 5000),
            "catalog_source": random.choice(["card-printing-system", "product-master"]),
            "catalog_destination": random.choice(["digital-marketplace", "auction-engine"]),
            "catalog_last_sync_min": random.randint(30, 360),
            "catalog_error_detail": random.choice([
                "connection reset by peer",
                "schema version mismatch",
                "primary key conflict on sku column",
                "timeout waiting for lock on products table",
            ]),

            # ── Manufacturing (channels 15-16) ──
            "print_queue_depth": random.randint(450, 500),
            "print_queue_max": 500,
            "print_queue_pct": round(random.uniform(90.0, 100.0), 1),
            "print_job_id": f"PJ-{random.randint(10000,99999)}",
            "print_oldest_job_min": random.randint(30, 480),
            "printer_name": random.choice(["HP-Indigo-7K-01", "HP-Indigo-7K-02", "Koenig-Bauer-01", "Heidelberg-XL-01"]),
            "printer_status": random.choice(["PAPER_JAM", "INK_LOW", "OFFLINE", "HEAD_CLOG"]),
            "qc_reject_count": random.randint(20, 150),
            "qc_inspected_count": random.randint(500, 2000),
            "qc_reject_pct": round(random.uniform(5.0, 25.0), 1),
            "qc_threshold_pct": 2.0,
            "qc_defect_type": random.choice([
                "color_registration_shift", "die_cut_misalignment",
                "foil_stamp_incomplete", "surface_scratch", "centering_off",
            ]),
            "qc_batch_id": f"BATCH-{random.randint(1000,9999)}",
            "qc_line_number": random.choice(["LINE-A", "LINE-B", "LINE-C"]),

            # ── Logistics (channels 17-18) ──
            "label_printer_id": random.choice(["ZBR-SHIP-01", "ZBR-SHIP-02", "ZBR-DOCK-01"]),
            "label_printer_status": random.choice(["OFFLINE", "PAPER_OUT", "HEAD_ERROR", "RIBBON_EMPTY"]),
            "label_error_code": random.choice(["E1001", "E2003", "E3005", "E4002"]),
            "label_failed_count": random.randint(10, 100),
            "label_window_min": random.randint(5, 30),
            "label_carrier": random.choice(["UPS", "FedEx", "USPS", "DHL"]),
            "label_queue_depth": random.randint(50, 500),
            "scanner_id": random.choice(["SCN-WH-01", "SCN-WH-02", "SCN-WH-03", "SCN-DOCK-01"]),
            "scanner_zone": random.choice(["receiving", "storage-A", "storage-B", "packing", "shipping"]),
            "scanner_last_sync_sec": random.randint(120, 600),
            "scanner_sync_max_sec": 60,
            "scanner_missed_scans": random.randint(20, 200),
            "inventory_delta": random.randint(5, 50),
            "scanner_firmware": random.choice(["3.2.1", "3.1.8", "3.0.5"]),

            # ── Cloud ops (channels 19-20) ──
            "cloud_resource_type": random.choice(["EC2 Instance", "Azure VM", "GCE Instance", "EBS Volume", "Managed Disk", "S3 Bucket"]),
            "cloud_resource_id": f"res-{random.randint(10000,99999)}",
            "cloud_resource_provider": random.choice(["aws", "azure", "gcp"]),
            "cloud_resource_region": random.choice(["us-east-1", "eastus", "us-central1"]),
            "cloud_resource_age_days": random.randint(14, 180),
            "cloud_resource_cost_daily": round(random.uniform(2.50, 85.00), 2),
            "cloud_resource_sg": random.choice(["sg-0abc1234", "nsg-fanatics-default", "fw-rule-legacy"]),
            "vpn_src_cloud": random.choice(["aws", "gcp"]),
            "vpn_dst_cloud": random.choice(["azure", "gcp"]),
            "vpn_flap_count": random.randint(5, 30),
            "vpn_flap_window": random.randint(60, 600),
            "vpn_current_state": random.choice(["DOWN", "NEGOTIATING", "REKEYING"]),
            "vpn_ike_phase": random.choice(["1", "2"]),
            "vpn_ike_status": random.choice(["FAILED", "TIMEOUT", "SA_EXPIRED"]),
            "vpn_last_dpd_sec": random.randint(30, 300),
        }


# Module-level instance for registry discovery
scenario = FanaticsScenario()

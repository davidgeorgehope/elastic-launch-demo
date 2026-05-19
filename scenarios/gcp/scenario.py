"""Google Cloud Network Operations scenario — GCP-native networking across 3 regions."""

from __future__ import annotations

import random
import time
from typing import Any

from scenarios.base import BaseScenario, CountdownConfig, UITheme


class GCPScenario(BaseScenario):
    """GCP-native network operations across us-central1, us-east1, europe-west1."""

    # ── Identity ──────────────────────────────────────────────────────

    @property
    def scenario_id(self) -> str:
        return "gcp"

    @property
    def scenario_icon(self) -> str:
        return "☁️"

    @property
    def scenario_name(self) -> str:
        return "Google Cloud Network Operations"

    @property
    def scenario_description(self) -> str:
        return (
            "GCP-native network operations across three regions: us-central1, "
            "us-east1, and europe-west1. Covers VPC, Cloud Armor, Cloud NAT, "
            "Cloud DNS, Interconnect, VPN, CDN, and Load Balancing services "
            "running on Google Kubernetes Engine."
        )

    @property
    def namespace(self) -> str:
        return "gcpnet"

    @property
    def sort_order(self) -> int:
        return 9

    @property
    def raw_log_profile(self) -> dict[str, Any]:
        return {
            "service_name": "cloud-gateway",
            "user_id_prefix": "usr",
            "tier_field": "support_tier",
            "tier_values": [("basic", 60), ("standard", 30), ("premium", 10)],
            "country_weights": {"US": 35, "GB": 12, "DE": 10, "IN": 12, "JP": 8, "BR": 8, "FR": 8, "AU": 7},
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "paths": [
                "/v1/projects/{id}/instances", "/v1/projects/{id}/buckets",
                "/v1/projects/{id}/iam", "/v1/projects/{id}/networks",
                "/v1/projects/{id}/disks", "/v1/projects/{id}/operations",
                "/login", "/health",
            ],
            "change_point_path": "/v1/projects/{id}/instances",
        }

    @property
    def executive_kpi_emitter_service_name(self) -> str:
        return "cloud-cdn-service"

    @property
    def executive_dashboard_intro(self) -> str:
        return (
            "**GCP network KPIs** — CDN delivery, capacity & security, SLO compliance, "
            "and cloud economics (synthetic `business.*` from `cloud-cdn-service`)."
        )

    @property
    def executive_kpi_sections(self) -> list[dict]:
        return [
            {
                "header": "**Delivery** — cache hit rate, requests, egress, offload, latency, and errors",
                "specs": [
                    ("CDN cache hit rate (%)", "metrics.business.cdn_cache_hit_rate_pct"),
                    ("Requests / min", "metrics.business.requests_per_min"),
                    ("Bytes egress (GiB/min)", "metrics.business.bytes_egress_gib_per_min"),
                    ("Origin offload (%)", "metrics.business.origin_offload_pct"),
                    ("Edge latency P50 (ms)", "metrics.business.edge_latency_p50_ms"),
                    ("CDN error rate (%)", "metrics.business.cdn_error_rate_pct"),
                ],
            },
            {
                "header": "**Capacity & security** — bandwidth, interconnect, Cloud Armor, VPC, NAT, LB",
                "specs": [
                    ("Peak bandwidth utilization (%)", "metrics.business.peak_bandwidth_utilization_pct"),
                    ("Interconnect utilization (%)", "metrics.business.interconnect_utilization_pct"),
                    ("Cloud Armor blocks / min", "metrics.business.cloud_armor_blocks_per_min"),
                    ("VPC flow anomalies / min", "metrics.business.vpc_flow_anomalies_per_min"),
                    ("NAT port exhaustion (%)", "metrics.business.nat_port_exhaustion_rate_pct"),
                    ("Load balancer RPS", "metrics.business.load_balancer_rps"),
                ],
            },
            {
                "header": "**SLO & reliability** — uptime, API success, SLA compliance, MTTD, MTTR",
                "specs": [
                    ("Uptime (%)", "metrics.business.uptime_pct"),
                    ("API success rate (%)", "metrics.business.api_success_rate_pct"),
                    ("Network SLA compliance (%)", "metrics.business.network_sla_compliance_pct"),
                    ("Incident MTTD (min)", "metrics.business.incident_mttd_min"),
                    ("Incident MTTR (min)", "metrics.business.incident_mttr_min"),
                    ("Availability index (0–100)", "metrics.business.availability_index_0_100"),
                ],
            },
            {
                "header": "**Commercial** — spend, committed use, cost efficiency, carbon, and SLA breaches",
                "specs": [
                    ("Cloud spend (USD/min)", "metrics.business.cloud_spend_usd_per_min"),
                    ("Committed use utilization (%)", "metrics.business.committed_use_discount_utilization_pct"),
                    ("Cost / M requests (USD)", "metrics.business.cost_per_million_requests_usd"),
                    ("Resource efficiency (%)", "metrics.business.resource_efficiency_pct"),
                    ("Carbon intensity (gCO2/TiB)", "metrics.business.carbon_intensity_gco2_per_tib"),
                    ("Customer SLA breaches", "metrics.business.customer_sla_breach_count"),
                ],
            },
        ]

    @property
    def executive_trend_charts(self) -> list[dict]:
        return [
            {"title": "CDN cache hit rate", "field": "metrics.business.cdn_cache_hit_rate_pct", "y_label": "%"},
            {"title": "Requests / min", "field": "metrics.business.requests_per_min", "y_label": "requests/min"},
            {"title": "Bytes egress (GiB/min)", "field": "metrics.business.bytes_egress_gib_per_min", "y_label": "GiB/min"},
            {"title": "Cloud Armor blocks / min", "field": "metrics.business.cloud_armor_blocks_per_min", "y_label": "blocks/min"},
            {"title": "Cloud spend (USD/min)", "field": "metrics.business.cloud_spend_usd_per_min", "y_label": "USD/min"},
            {"title": "Uptime (%)", "field": "metrics.business.uptime_pct", "y_label": "%"},
        ]

    # ── Services ──────────────────────────────────────────────────────

    @property
    def services(self) -> dict[str, dict[str, Any]]:
        return {
            # ── us-central1 — Core Network ──
            "vpc-network-manager": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "core_network",
                "language": "go",
            },
            "cloud-load-balancer": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-b",
                "subsystem": "traffic_management",
                "language": "java",
            },
            "cloud-cdn-service": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-c",
                "subsystem": "content_delivery",
                "language": "python",
            },
            # ── us-east1 — Security & Access ──
            "cloud-armor-waf": {
                "cloud_provider": "gcp",
                "cloud_region": "us-east1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-east1-b",
                "subsystem": "security",
                "language": "rust",
            },
            "cloud-nat-gateway": {
                "cloud_provider": "gcp",
                "cloud_region": "us-east1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-east1-c",
                "subsystem": "network_access",
                "language": "go",
                "generates_traces": False,
            },
            "cloud-dns-resolver": {
                "cloud_provider": "gcp",
                "cloud_region": "us-east1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-east1-d",
                "subsystem": "dns",
                "language": "cpp",
                "generates_traces": False,
            },
            # ── europe-west1 — Connectivity & Monitoring ──
            "cloud-interconnect": {
                "cloud_provider": "gcp",
                "cloud_region": "europe-west1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "europe-west1-b",
                "subsystem": "connectivity",
                "language": "java",
            },
            "cloud-vpn-gateway": {
                "cloud_provider": "gcp",
                "cloud_region": "europe-west1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "europe-west1-c",
                "subsystem": "vpn",
                "language": "rust",
                "generates_traces": False,
            },
            "network-intelligence": {
                "cloud_provider": "gcp",
                "cloud_region": "europe-west1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "europe-west1-d",
                "subsystem": "monitoring",
                "language": "python",
            },
        }

    # ── Channel Registry ──────────────────────────────────────────────

    @property
    def channel_registry(self) -> dict[int, dict[str, Any]]:
        return {
            1: {
                "name": "VPC Peering Route Limit",
                "subsystem": "core_network",
                "vehicle_section": "vpc_routing",
                "error_type": "VPC-ROUTE-LIMIT-EXCEEDED",
                "sensor_type": "route_table",
                "affected_services": ["vpc-network-manager", "cloud-load-balancer"],
                "cascade_services": ["cloud-nat-gateway"],
                "description": "VPC peering route table exceeding maximum advertised route limit",
                "investigation_notes": (
                    "Root cause: VPC peering has a hard limit of 250 advertised routes per peering connection. "
                    "When custom routes are exported across peerings, aggregate routes from all subnets and "
                    "static/dynamic routes count toward this limit. Check current usage with:\n"
                    "  gcloud compute networks peerings list-routes <peering> --network=<vpc> --region=<region> --direction=INCOMING\n"
                    "Remediation: Consolidate overlapping CIDR ranges using supernets, remove stale static routes, "
                    "or switch to a Shared VPC model which avoids peering route limits. If immediate relief is needed, "
                    "request a quota increase via gcloud compute project-info describe --project=<project> and file "
                    "a support case referencing the PEER_ROUTES_PER_PEERING quota."
                ),
                "remediation_action": "reset_vpc_peering",
                "error_message": (
                    'level=error ts={{timestamp}} caller=vpc_manager.go:312 '
                    'msg="VPC-ROUTE-LIMIT-EXCEEDED" project={gcp_project} '
                    "peering={vpc_peering_name} routes={route_count}/{route_max} "
                    "network={vpc_network} region={gcp_region} "
                    "dropped_prefixes={dropped_prefixes}"
                ),
                "stack_trace": (
                    "goroutine 234 [running]:\n"
                    "runtime/debug.Stack()\n"
                    "\t/usr/local/go/src/runtime/debug/stack.go:24 +0x5e\n"
                    "cloud.google.com/go/compute/apiv1.(*RoutesClient).AggregatedList(0xc000518000, "
                    "{{0xc000a12480}}, {{0xc000a124c0}})\n"
                    "\t/app/internal/vpc/route_manager.go:312 +0x3a2\n"
                    "  VPC Network: {vpc_network}\n"
                    "  Peering: {vpc_peering_name}\n"
                    "  Routes: {route_count}/{route_max}\n"
                    "  Dropped Prefixes: {dropped_prefixes}\n"
                    "  Action: Consolidate routes or request quota increase"
                ),
            },
            2: {
                "name": "Subnet IP Exhaustion",
                "subsystem": "core_network",
                "vehicle_section": "vpc_subnets",
                "error_type": "VPC-SUBNET-IP-EXHAUSTION",
                "sensor_type": "subnet_usage",
                "affected_services": ["vpc-network-manager", "cloud-nat-gateway"],
                "cascade_services": ["cloud-load-balancer", "cloud-cdn-service"],
                "description": "VPC subnet running out of available IP addresses",
                "investigation_notes": (
                    "Root cause: Subnet CIDR range is nearly fully allocated. GKE nodes, Cloud NAT, and internal "
                    "load balancers all consume IPs from the subnet pool. Identify top consumers with:\n"
                    "  gcloud compute addresses list --filter='subnetwork:<subnet>' --project=<project>\n"
                    "  gcloud compute instances list --filter='networkInterfaces.subnetwork:<subnet>'\n"
                    "Remediation: Expand the subnet CIDR range in-place (GCP supports non-disruptive expansion):\n"
                    "  gcloud compute networks subnets expand-ip-range <subnet> --region=<region> --prefix-length=<new_prefix>\n"
                    "Alternatively, add secondary IP ranges for GKE pods/services, or migrate workloads to a new "
                    "subnet with a larger CIDR block. Check for leaked IPs from terminated GKE pods or orphaned "
                    "internal load balancer forwarding rules."
                ),
                "remediation_action": "reconfigure_firewall_rules",
                "error_message": (
                    'level=error ts={{timestamp}} caller=subnet_monitor.go:189 '
                    'msg="VPC-SUBNET-IP-EXHAUSTION" project={gcp_project} '
                    "subnet={subnet_name} cidr={subnet_cidr} "
                    "used={subnet_used_ips}/{subnet_total_ips} "
                    "utilization={subnet_util_pct}% region={gcp_region}"
                ),
                "stack_trace": (
                    "goroutine 156 [running]:\n"
                    "cloud.google.com/go/compute/apiv1.(*SubnetworksClient).Get(0xc000420000)\n"
                    "\t/app/internal/vpc/subnet_monitor.go:189 +0x1b8\n"
                    "  Subnet: {subnet_name} ({subnet_cidr})\n"
                    "  Used IPs: {subnet_used_ips}/{subnet_total_ips} ({subnet_util_pct}%)\n"
                    "  Region: {gcp_region}\n"
                    "  Action: Expand CIDR range or create secondary range"
                ),
            },
            3: {
                "name": "Firewall Rule Conflict",
                "subsystem": "core_network",
                "vehicle_section": "vpc_firewall",
                "error_type": "VPC-FIREWALL-RULE-CONFLICT",
                "sensor_type": "firewall_policy",
                "affected_services": ["vpc-network-manager", "cloud-armor-waf"],
                "cascade_services": ["cloud-interconnect"],
                "description": "Conflicting VPC firewall rules causing unexpected traffic drops",
                "investigation_notes": (
                    "Root cause: GCP firewall rules use numeric priority where LOWER number = HIGHER priority. "
                    "A DENY rule at priority 900 overrides an ALLOW rule at priority 1000, even if the ALLOW rule "
                    "is more specific. This is the opposite of some on-prem firewalls. Diagnose with:\n"
                    "  gcloud compute firewall-rules list --filter='network:<vpc>' --sort-by=priority --format='table(name,priority,direction,action,sourceRanges,targetTags)'\n"
                    "  gcloud compute firewall-rules describe <rule_name> --format=json\n"
                    "Check VPC Flow Logs for dropped traffic: Console > VPC Network > Firewall > Firewall Insights.\n"
                    "Remediation: Adjust conflicting rule priorities so ALLOW rules have lower priority numbers than "
                    "blanket DENY rules, or merge overlapping rules. Use Firewall Policy (hierarchical) for org-wide "
                    "rules and VPC firewall rules for project-specific exceptions. Validate with:\n"
                    "  gcloud compute firewall-rules update <rule> --priority=<new_priority>"
                ),
                "remediation_action": "reconfigure_firewall_rules",
                "error_message": (
                    'level=error ts={{timestamp}} caller=fw_policy_engine.go:445 '
                    'msg="VPC-FIREWALL-RULE-CONFLICT" project={gcp_project} '
                    "rule_a={fw_rule_a} rule_b={fw_rule_b} "
                    "priority_a={fw_priority_a} priority_b={fw_priority_b} "
                    "network={vpc_network} dropped_packets={fw_dropped_packets}/s"
                ),
                "stack_trace": (
                    "goroutine 312 [running]:\n"
                    "cloud.google.com/go/compute/apiv1.(*FirewallsClient).List(0xc000518000)\n"
                    "\t/app/internal/vpc/fw_policy_engine.go:445 +0x2f1\n"
                    "  Conflicting Rules:\n"
                    "    Rule A: {fw_rule_a} (priority {fw_priority_a}, ALLOW)\n"
                    "    Rule B: {fw_rule_b} (priority {fw_priority_b}, DENY)\n"
                    "  Network: {vpc_network}\n"
                    "  Dropped: {fw_dropped_packets} packets/s\n"
                    "  Action: Adjust rule priorities or merge conflicting rules"
                ),
            },
            4: {
                "name": "DDoS Alert Triggered",
                "subsystem": "security",
                "vehicle_section": "ddos_protection",
                "error_type": "ARMOR-DDOS-ALERT",
                "sensor_type": "ddos_detector",
                "affected_services": ["cloud-armor-waf", "cloud-load-balancer"],
                "cascade_services": ["vpc-network-manager", "cloud-cdn-service"],
                "description": "Cloud Armor detecting and mitigating a volumetric DDoS attack",
                "investigation_notes": (
                    "Root cause: Volumetric DDoS attack targeting the backend service through the external load "
                    "balancer. Cloud Armor Adaptive Protection has engaged but may not be fully mitigating. Check:\n"
                    "  gcloud compute security-policies describe <policy> --format=json\n"
                    "  gcloud compute security-policies rules list <policy>\n"
                    "Review Adaptive Protection events in Console > Network Security > Cloud Armor > Events tab.\n"
                    "Remediation: Enable Adaptive Protection auto-deploy if not active:\n"
                    "  gcloud compute security-policies update <policy> --enable-layer7-ddos-defense\n"
                    "Add rate-limiting rules targeting source regions: gcloud compute security-policies rules create "
                    "<priority> --security-policy=<policy> --expression='origin.region_code==\"CN\"' --action=throttle "
                    "--rate-limit-threshold-count=100 --rate-limit-threshold-interval-sec=60. "
                    "Escalate to Google Cloud Support for L3/L4 scrubbing if volume exceeds 100Gbps."
                ),
                "remediation_action": "reset_security_policy",
                "error_message": (
                    "[CloudArmor] ARMOR-DDOS-ALERT policy={armor_policy} "
                    "attack_type={ddos_attack_type} volume={ddos_volume_gbps}Gbps "
                    "source_regions={ddos_source_regions} "
                    "mitigated={ddos_mitigated_pct}% backend={armor_backend} "
                    "rule={armor_rule_name}"
                ),
                "stack_trace": (
                    "Cloud Armor DDoS Mitigation Report\n"
                    "------------------------------------\n"
                    "Policy:         {armor_policy}\n"
                    "Attack Type:    {ddos_attack_type}\n"
                    "Volume:         {ddos_volume_gbps} Gbps\n"
                    "Source Regions: {ddos_source_regions}\n"
                    "Mitigated:      {ddos_mitigated_pct}%\n"
                    "Backend:        {armor_backend}\n"
                    "Rule Matched:   {armor_rule_name}\n"
                    "Duration:       ongoing\n"
                    "Action:         Adaptive protection engaged, monitoring escalation"
                ),
            },
            5: {
                "name": "WAF False Positive Surge",
                "subsystem": "security",
                "vehicle_section": "waf_engine",
                "error_type": "ARMOR-FALSE-POSITIVE",
                "sensor_type": "waf_rules",
                "affected_services": ["cloud-armor-waf", "cloud-cdn-service"],
                "cascade_services": ["cloud-load-balancer"],
                "description": "Cloud Armor WAF rules generating excessive false positive blocks",
                "investigation_notes": (
                    "Root cause: Preconfigured WAF rule (OWASP ModSecurity CRS) is triggering on legitimate API "
                    "traffic. Common false positives: JSON payloads matching SQLi patterns, base64-encoded data "
                    "matching XSS signatures, GraphQL queries matching RCE patterns. Diagnose with:\n"
                    "  gcloud compute security-policies rules describe <priority> --security-policy=<policy>\n"
                    "  Console > Network Security > Cloud Armor > <policy> > Logs tab (filter by DENY action)\n"
                    "Remediation: Adjust sensitivity level from 1 (high) to 2 or 3 for the specific rule:\n"
                    "  gcloud compute security-policies rules update <priority> --security-policy=<policy> "
                    "--expression='evaluatePreconfiguredWaf(\"sqli-v33-stable\", {\"sensitivity\": 2})'\n"
                    "Or add path-based exception rules at a higher priority (lower number) to ALLOW known-good paths "
                    "before the WAF rule evaluates. Monitor false positive rate via Cloud Monitoring metrics "
                    "loadbalancing.googleapis.com/https/request_count filtered by security_policy_name."
                ),
                "remediation_action": "update_waf_rules",
                "error_message": (
                    "[CloudArmor] ARMOR-FALSE-POSITIVE policy={armor_policy} "
                    "rule={waf_rule_id} blocked_requests={waf_blocked_count}/m "
                    "false_positive_rate={waf_fp_rate}% "
                    "affected_paths={waf_affected_paths} "
                    "sensitivity={waf_sensitivity_level}"
                ),
                "stack_trace": (
                    "Cloud Armor WAF Analysis\n"
                    "-------------------------\n"
                    "Policy:              {armor_policy}\n"
                    "Rule:                {waf_rule_id}\n"
                    "Blocked/min:         {waf_blocked_count}\n"
                    "False Positive Rate: {waf_fp_rate}%\n"
                    "Affected Paths:      {waf_affected_paths}\n"
                    "Sensitivity:         {waf_sensitivity_level}\n"
                    "Legitimate traffic pattern: API JSON payloads triggering SQLi detection\n"
                    "Action: Adjust rule sensitivity or add path exception"
                ),
            },
            6: {
                "name": "Security Policy Sync Failure",
                "subsystem": "security",
                "vehicle_section": "policy_management",
                "error_type": "ARMOR-POLICY-SYNC-FAILURE",
                "sensor_type": "policy_sync",
                "affected_services": ["cloud-armor-waf", "vpc-network-manager"],
                "cascade_services": ["cloud-load-balancer"],
                "description": "Cloud Armor security policy failing to sync across backend services",
                "investigation_notes": (
                    "Root cause: Cloud Armor policy updates propagate asynchronously to all backend services. "
                    "Propagation typically takes 60-90 seconds but can stall if backends are unhealthy or if there "
                    "is a version conflict from concurrent policy edits. During sync gaps, stale backends enforce "
                    "the previous policy version, creating an inconsistent security posture. Check sync status:\n"
                    "  gcloud compute backend-services describe <backend> --global --format='value(securityPolicy)'\n"
                    "  gcloud compute security-policies describe <policy> --format='value(fingerprint,creationTimestamp)'\n"
                    "Remediation: Force a policy re-attachment to lagging backends:\n"
                    "  gcloud compute backend-services update <backend> --global --security-policy=<policy>\n"
                    "If version conflict persists, export the policy, delete and recreate it:\n"
                    "  gcloud compute security-policies export <policy> --file-name=policy-backup.yaml\n"
                    "Avoid concurrent policy edits; use --fingerprint flag to prevent race conditions."
                ),
                "remediation_action": "reset_security_policy",
                "error_message": (
                    "[CloudArmor] ARMOR-POLICY-SYNC-FAILURE policy={armor_policy} "
                    "version={policy_version} backends_synced={backends_synced}/{backends_total} "
                    "last_sync={policy_last_sync_sec}s ago "
                    "error=\"{policy_sync_error}\""
                ),
                "stack_trace": (
                    "Cloud Armor Policy Sync Diagnostic\n"
                    "-------------------------------------\n"
                    "Policy:           {armor_policy}\n"
                    "Version:          {policy_version}\n"
                    "Synced Backends:  {backends_synced}/{backends_total}\n"
                    "Last Sync:        {policy_last_sync_sec}s ago\n"
                    "Error:            {policy_sync_error}\n"
                    "Stale Backends:   Running policy version {policy_version} - 1\n"
                    "Action: Force policy push or check backend health"
                ),
            },
            7: {
                "name": "NAT Port Exhaustion",
                "subsystem": "network_access",
                "vehicle_section": "nat_gateway",
                "error_type": "NAT-PORT-EXHAUSTION",
                "sensor_type": "nat_ports",
                "affected_services": ["cloud-nat-gateway", "vpc-network-manager"],
                "cascade_services": ["cloud-load-balancer", "cloud-dns-resolver"],
                "description": "Cloud NAT gateway running out of available source ports",
                "investigation_notes": (
                    "Root cause: Cloud NAT allocates a minimum of 64 source ports per VM by default. With high "
                    "connection rates (e.g., GKE pods making many external API calls), the 64-port-per-VM minimum "
                    "is quickly exhausted. Each unique (src_ip, src_port, dst_ip, dst_port, protocol) tuple "
                    "consumes one port. Check current allocation:\n"
                    "  gcloud compute routers nats describe <nat> --router=<router> --region=<region>\n"
                    "  Console > Network Services > Cloud NAT > <gateway> > Monitoring tab (port utilization)\n"
                    "Remediation: Increase minimum ports per VM:\n"
                    "  gcloud compute routers nats update <nat> --router=<router> --region=<region> "
                    "--min-ports-per-vm=2048\n"
                    "Or enable Dynamic Port Allocation (DPA) for bursty workloads:\n"
                    "  gcloud compute routers nats update <nat> --router=<router> --region=<region> "
                    "--enable-dynamic-port-allocation --min-ports-per-vm=64 --max-ports-per-vm=65536\n"
                    "Also add more NAT IPs to increase the total port pool."
                ),
                "remediation_action": "reset_nat_gateway",
                "error_message": (
                    "cloudnat: NAT-PORT-EXHAUSTION gateway={nat_gateway_name} "
                    "region={gcp_region} ports_used={nat_ports_used}/{nat_ports_total} "
                    "utilization={nat_port_util_pct}% "
                    "dropped_connections={nat_dropped_conns}/s "
                    "top_vm={nat_top_vm}"
                ),
                "stack_trace": (
                    "Cloud NAT Port Allocation Report\n"
                    "----------------------------------\n"
                    "Gateway:      {nat_gateway_name}\n"
                    "Region:       {gcp_region}\n"
                    "Ports Used:   {nat_ports_used}/{nat_ports_total} ({nat_port_util_pct}%)\n"
                    "Dropped/s:    {nat_dropped_conns}\n"
                    "Top Consumer: {nat_top_vm}\n"
                    "Min Ports/VM: 64\n"
                    "Action: Increase minPortsPerVm or add NAT IP addresses"
                ),
            },
            8: {
                "name": "NAT Endpoint Mapping Failure",
                "subsystem": "network_access",
                "vehicle_section": "nat_gateway",
                "error_type": "NAT-ENDPOINT-MAPPING-FAILURE",
                "sensor_type": "nat_mapping",
                "affected_services": ["cloud-nat-gateway", "cloud-load-balancer"],
                "cascade_services": ["cloud-cdn-service"],
                "description": "Cloud NAT endpoint-independent mapping failing for new connections",
                "investigation_notes": (
                    "Root cause: NAT mapping type determines how source ports are reused. ENDPOINT_INDEPENDENT "
                    "mapping reuses the same external IP:port for all destinations from a given VM, which is "
                    "required for protocols like STUN/TURN but consumes ports faster. ADDRESS_DEPENDENT mapping "
                    "allows port reuse per destination IP. Mapping failures occur when port pool is exhausted for "
                    "the configured mapping type. Diagnose with:\n"
                    "  gcloud compute routers nats describe <nat> --router=<router> --region=<region> "
                    "--format='value(natIpAllocateOption,sourceSubnetworkIpRangesToNat,endpointTypes)'\n"
                    "Remediation for static NAT (manual IP assignment): add more NAT IPs:\n"
                    "  gcloud compute routers nats update <nat> --router=<router> --region=<region> "
                    "--nat-external-ip-pool=<ip1>,<ip2>,<ip3>\n"
                    "For dynamic NAT (auto-allocated): switch to manual allocation with a larger pool. "
                    "If ENDPOINT_INDEPENDENT is not required, switch to ADDRESS_DEPENDENT to reduce port pressure. "
                    "Review Cloud NAT logs: Console > Logging > resource.type='nat_gateway'."
                ),
                "remediation_action": "reconfigure_nat_mapping",
                "error_message": (
                    "cloudnat: NAT-ENDPOINT-MAPPING-FAILURE gateway={nat_gateway_name} "
                    "mapping_type={nat_mapping_type} failures={nat_mapping_failures}/m "
                    "nat_ip={nat_external_ip} subnet={subnet_name} "
                    "protocol={nat_protocol}"
                ),
                "stack_trace": (
                    "Cloud NAT Mapping Diagnostic\n"
                    "------------------------------\n"
                    "Gateway:      {nat_gateway_name}\n"
                    "Mapping Type: {nat_mapping_type}\n"
                    "Failures/min: {nat_mapping_failures}\n"
                    "NAT IP:       {nat_external_ip}\n"
                    "Subnet:       {subnet_name}\n"
                    "Protocol:     {nat_protocol}\n"
                    "Action: Check NAT IP allocation and endpoint mapping config"
                ),
            },
            9: {
                "name": "NAT IP Allocation Error",
                "subsystem": "network_access",
                "vehicle_section": "nat_gateway",
                "error_type": "NAT-IP-ALLOCATION-ERROR",
                "sensor_type": "nat_ip_pool",
                "affected_services": ["cloud-nat-gateway", "vpc-network-manager"],
                "cascade_services": ["cloud-interconnect"],
                "description": "Cloud NAT unable to allocate external IP addresses for outbound traffic",
                "investigation_notes": (
                    "Root cause: Cloud NAT cannot allocate additional external IPs due to project quota limits "
                    "or IP conflicts. The EXTERNAL_IP_ADDRESS quota per region defaults to a limited number. "
                    "If another NAT gateway or resource holds the IP, allocation fails. Check quotas:\n"
                    "  gcloud compute project-info describe --project=<project> "
                    "--format='table(quotas.filter(metric=STATIC_ADDRESSES).limit,usage)'\n"
                    "  gcloud compute addresses list --filter='region:<region> AND status:RESERVED'\n"
                    "Remediation: Release unused static IPs:\n"
                    "  gcloud compute addresses delete <unused-ip> --region=<region>\n"
                    "Or request a quota increase via Console > IAM & Admin > Quotas > filter 'In-use IP addresses'. "
                    "If IPs are held by other NAT gateways, consolidate NAT configurations. For immediate relief, "
                    "switch to AUTO_ONLY allocation mode which uses GCP-managed ephemeral IPs (note: IPs will "
                    "change on gateway restart, which may break IP-allowlisted external services)."
                ),
                "remediation_action": "reset_nat_gateway",
                "error_message": (
                    "cloudnat: NAT-IP-ALLOCATION-ERROR gateway={nat_gateway_name} "
                    "region={gcp_region} allocated_ips={nat_allocated_ips}/{nat_max_ips} "
                    "pending_allocations={nat_pending_allocs} "
                    "error=\"{nat_alloc_error}\""
                ),
                "stack_trace": (
                    "Cloud NAT IP Allocation Report\n"
                    "---------------------------------\n"
                    "Gateway:     {nat_gateway_name}\n"
                    "Region:      {gcp_region}\n"
                    "Allocated:   {nat_allocated_ips}/{nat_max_ips}\n"
                    "Pending:     {nat_pending_allocs}\n"
                    "Error:       {nat_alloc_error}\n"
                    "Quota:       EXTERNAL_IP_ADDRESS — check project quota\n"
                    "Action: Release unused IPs or request quota increase"
                ),
            },
            10: {
                "name": "DNSSEC Validation Failure",
                "subsystem": "dns",
                "vehicle_section": "dns_security",
                "error_type": "DNS-DNSSEC-VALIDATION-FAILURE",
                "sensor_type": "dnssec_validator",
                "affected_services": ["cloud-dns-resolver", "vpc-network-manager"],
                "cascade_services": ["cloud-armor-waf", "network-intelligence"],
                "description": "DNSSEC signature validation failing for managed DNS zones",
                "investigation_notes": (
                    "Root cause: DNSSEC validation failures typically stem from expired RRSIG signatures, missing "
                    "or mismatched DS records at the parent zone, or key rotation failures. Cloud DNS manages "
                    "DNSSEC keys automatically, but DS records at the domain registrar must be updated manually "
                    "when key-signing keys (KSK) rotate. Diagnose with:\n"
                    "  gcloud dns managed-zones describe <zone> --format='value(dnssecConfig)'\n"
                    "  gcloud dns dns-keys list --zone=<zone> --format='table(id,type,algorithm,isActive,dsRecord)'\n"
                    "  dig +dnssec +trace <record_name> @8.8.8.8\n"
                    "Remediation: If DS record is MISSING/STALE, get the current DS record from Cloud DNS and "
                    "update at the registrar:\n"
                    "  gcloud dns dns-keys describe <key-id> --zone=<zone> --format='value(dsRecord)'\n"
                    "If RRSIG is expired, force a key rotation: Console > Cloud DNS > <zone> > DNSSEC > Rotate Keys. "
                    "Allow 24-48 hours for DNS propagation of new DS records through the global DNS hierarchy."
                ),
                "remediation_action": "reset_dns_zone",
                "error_message": (
                    "cloud-dns: DNS-DNSSEC-VALIDATION-FAILURE zone={dns_zone} "
                    "record={dns_record_name} type={dns_record_type} "
                    "rrsig_expiry={dnssec_rrsig_expiry} "
                    "ds_status={dnssec_ds_status} "
                    "validation_errors={dnssec_error_count}/m"
                ),
                "stack_trace": (
                    "Cloud DNS DNSSEC Validation Report\n"
                    "------------------------------------\n"
                    "Zone:              {dns_zone}\n"
                    "Record:            {dns_record_name} ({dns_record_type})\n"
                    "RRSIG Expiry:      {dnssec_rrsig_expiry}\n"
                    "DS Record Status:  {dnssec_ds_status}\n"
                    "Validation Errors: {dnssec_error_count}/min\n"
                    "DNSKEY Algorithm:  RSASHA256\n"
                    "Action: Rotate DNSSEC keys or update DS record at registrar"
                ),
            },
            11: {
                "name": "DNS Zone Propagation Delay",
                "subsystem": "dns",
                "vehicle_section": "dns_propagation",
                "error_type": "DNS-ZONE-PROPAGATION-DELAY",
                "sensor_type": "dns_propagation",
                "affected_services": ["cloud-dns-resolver", "cloud-load-balancer"],
                "cascade_services": ["cloud-cdn-service", "network-intelligence"],
                "description": "DNS record changes taking abnormally long to propagate across Cloud DNS servers",
                "investigation_notes": (
                    "Root cause: Cloud DNS record changes normally propagate within 60 seconds, but delays occur "
                    "when authoritative name servers are under heavy query load, when the zone has a very large "
                    "record set, or when there are pending DNSSEC re-signing operations. Check change status:\n"
                    "  gcloud dns record-sets changes describe <change-id> --zone=<zone>\n"
                    "  gcloud dns record-sets changes list --zone=<zone> --sort-by=startTime --limit=5\n"
                    "Remediation: If change is stuck in PENDING, verify the zone is not locked by another operation. "
                    "Flush local DNS caches on affected VMs:\n"
                    "  sudo systemd-resolve --flush-caches (on Container-Optimized OS)\n"
                    "For external clients, reduce TTL on the record before making changes (set TTL to 60s, wait "
                    "for old TTL to expire, then make the change). Check if Cloud DNS name servers are responding:\n"
                    "  dig <record> @ns-cloud-a1.googledomains.com\n"
                    "If servers are unresponsive, check Cloud DNS quota and zone status in Console > Network Services > Cloud DNS."
                ),
                "remediation_action": "flush_dns_cache",
                "error_message": (
                    "cloud-dns: DNS-ZONE-PROPAGATION-DELAY zone={dns_zone} "
                    "change_id={dns_change_id} record={dns_record_name} "
                    "propagation_time={dns_prop_time_sec}s (SLA {dns_prop_sla_sec}s) "
                    "servers_updated={dns_servers_updated}/{dns_servers_total}"
                ),
                "stack_trace": (
                    "Cloud DNS Propagation Report\n"
                    "------------------------------\n"
                    "Zone:               {dns_zone}\n"
                    "Change ID:          {dns_change_id}\n"
                    "Record:             {dns_record_name}\n"
                    "Propagation Time:   {dns_prop_time_sec}s (SLA: {dns_prop_sla_sec}s)\n"
                    "Servers Updated:    {dns_servers_updated}/{dns_servers_total}\n"
                    "Status:             PENDING\n"
                    "Action: Wait for propagation or flush DNS cache"
                ),
            },
            12: {
                "name": "Interconnect Circuit Down",
                "subsystem": "connectivity",
                "vehicle_section": "dedicated_interconnect",
                "error_type": "INTERCONNECT-CIRCUIT-DOWN",
                "sensor_type": "circuit_status",
                "affected_services": ["cloud-interconnect", "vpc-network-manager"],
                "cascade_services": ["cloud-vpn-gateway", "network-intelligence"],
                "description": "Dedicated Interconnect circuit losing link, failing over to backup path",
                "investigation_notes": (
                    "Root cause: Dedicated Interconnect circuit link is DOWN, indicating a physical layer issue. "
                    "LACP state DETACHED means the link aggregation group has lost member links. Common causes: "
                    "fiber cut at colocation facility, optics degradation, or cross-connect issue. Diagnose with:\n"
                    "  gcloud compute interconnects describe <interconnect> --format='value(state,operationalStatus,circuitInfos)'\n"
                    "  gcloud compute interconnects attachments describe <attachment> --region=<region>\n"
                    "  Console > Hybrid Connectivity > Interconnect > <name> > Diagnostics tab\n"
                    "Remediation: If failover is ACTIVE_ON_BACKUP, traffic is flowing via the secondary path. "
                    "Contact the colocation provider to inspect the cross-connect and verify optic light levels. "
                    "Check for maintenance notifications: gcloud compute interconnects get-macsec-config <name>. "
                    "If NO_BACKUP, immediately engage VPN as emergency backup:\n"
                    "  gcloud compute vpn-tunnels create emergency-tunnel --region=<region> --peer-address=<peer> "
                    "--shared-secret=<secret> --router=<router>"
                ),
                "remediation_action": "reset_interconnect_attachment",
                "error_message": (
                    "[Interconnect] INTERCONNECT-CIRCUIT-DOWN attachment={interconnect_name} "
                    "circuit_id={circuit_id} location={interconnect_location} "
                    "link_status=DOWN since {circuit_down_sec}s "
                    "bandwidth={interconnect_bw_gbps}Gbps failover={failover_status}"
                ),
                "stack_trace": (
                    "Cloud Interconnect Circuit Report\n"
                    "-----------------------------------\n"
                    "Attachment:   {interconnect_name}\n"
                    "Circuit ID:   {circuit_id}\n"
                    "Location:     {interconnect_location}\n"
                    "Link Status:  DOWN\n"
                    "Down Since:   {circuit_down_sec}s\n"
                    "Bandwidth:    {interconnect_bw_gbps} Gbps\n"
                    "Failover:     {failover_status}\n"
                    "LACP State:   DETACHED\n"
                    "Action: Contact colo provider, verify cross-connect"
                ),
            },
            13: {
                "name": "BGP Session Flap",
                "subsystem": "connectivity",
                "vehicle_section": "bgp_routing",
                "error_type": "INTERCONNECT-BGP-FLAP",
                "sensor_type": "bgp_session",
                "affected_services": ["cloud-interconnect", "cloud-vpn-gateway"],
                "cascade_services": ["vpc-network-manager", "cloud-nat-gateway"],
                "description": "Cloud Router BGP session repeatedly flapping on interconnect attachment",
                "investigation_notes": (
                    "Root cause: BGP session flapping indicates the Cloud Router is repeatedly establishing and "
                    "dropping the BGP peering with the on-premises router. Common causes: MTU mismatch (Interconnect "
                    "supports 1440-byte MTU for BGP), hold timer too aggressive, route advertisement exceeding "
                    "peer capacity, or unstable physical link causing BFD to trigger fast failover. Diagnose:\n"
                    "  gcloud compute routers describe <router> --region=<region> --format='value(bgpPeers)'\n"
                    "  gcloud compute routers get-status <router> --region=<region>\n"
                    "  Console > Hybrid Connectivity > Cloud Routers > <router> > BGP Sessions tab\n"
                    "Remediation: Increase BGP hold timer to reduce flap sensitivity:\n"
                    "  gcloud compute routers update-bgp-peer <router> --region=<region> --peer-name=<peer> "
                    "--advertised-route-priority=100\n"
                    "Disable BFD temporarily to confirm if physical link instability is the trigger. Verify "
                    "peer ASN and IP configuration match on both sides. Reduce advertised routes with custom "
                    "route advertisements to stay under peer import limits."
                ),
                "remediation_action": "restart_bgp_session",
                "error_message": (
                    "[CloudRouter] INTERCONNECT-BGP-FLAP router={cloud_router} "
                    "peer={bgp_peer_ip} peer_asn={bgp_peer_asn} "
                    "flaps={bgp_flap_count} window={bgp_flap_window}s "
                    "state={bgp_state} advertised_routes={bgp_advertised_routes}"
                ),
                "stack_trace": (
                    "Cloud Router BGP Session Report\n"
                    "----------------------------------\n"
                    "Router:            {cloud_router}\n"
                    "Peer IP:           {bgp_peer_ip}\n"
                    "Peer ASN:          {bgp_peer_asn}\n"
                    "Flap Count:        {bgp_flap_count} in {bgp_flap_window}s\n"
                    "Current State:     {bgp_state}\n"
                    "Advertised Routes: {bgp_advertised_routes}\n"
                    "BFD Status:        DOWN\n"
                    "Action: Check peer configuration and physical link"
                ),
            },
            14: {
                "name": "CDN Cache Miss Spike",
                "subsystem": "content_delivery",
                "vehicle_section": "cdn_cache",
                "error_type": "CDN-CACHE-MISS-SPIKE",
                "sensor_type": "cache_hit_ratio",
                "affected_services": ["cloud-cdn-service", "cloud-load-balancer"],
                "cascade_services": ["vpc-network-manager"],
                "description": "Cloud CDN cache hit ratio dropping significantly, overwhelming origin servers",
                "investigation_notes": (
                    "Root cause: Cache miss spike indicates CDN edge nodes are not serving cached content. "
                    "Common causes: cache key policy includes query strings or headers that create too many unique "
                    "keys, origin setting Cache-Control: no-store or private headers, recent cache invalidation "
                    "flushing popular content, or signed URL expiration causing cache bypass. Diagnose by path:\n"
                    "  Console > Network Services > Cloud CDN > <backend> > Cache Performance tab\n"
                    "  gcloud compute backend-services describe <backend> --global --format='value(cdnPolicy)'\n"
                    "Remediation for path-specific cache misses: invalidate stale cached content by specific path:\n"
                    "  gcloud compute url-maps invalidate-cdn-cache <url-map> --path='/api/v2/assets/*'\n"
                    "Fix cache key policy to exclude unnecessary query params:\n"
                    "  gcloud compute backend-services update <backend> --global "
                    "--cache-key-include-query-string=false\n"
                    "Increase cache TTL for static assets. Verify origin is returning proper Cache-Control headers "
                    "with max-age. Check origin health since 5xx responses are not cached."
                ),
                "remediation_action": "invalidate_cdn_cache",
                "error_message": (
                    "[CloudCDN] CDN-CACHE-MISS-SPIKE backend={cdn_backend} "
                    "hit_ratio={cdn_hit_ratio}% (SLA {cdn_hit_sla}%) "
                    "miss_rate={cdn_miss_rate}/s origin_latency={cdn_origin_latency_ms}ms "
                    "cache_fill={cdn_cache_fill_pct}%"
                ),
                "stack_trace": (
                    "Cloud CDN Cache Analysis\n"
                    "--------------------------\n"
                    "Backend:          {cdn_backend}\n"
                    "Hit Ratio:        {cdn_hit_ratio}% (SLA: {cdn_hit_sla}%)\n"
                    "Miss Rate:        {cdn_miss_rate}/s\n"
                    "Origin Latency:   {cdn_origin_latency_ms}ms\n"
                    "Cache Fill:       {cdn_cache_fill_pct}%\n"
                    "Top Missed Paths: /api/v2/assets, /media/images\n"
                    "Action: Review cache key policy and TTL configuration"
                ),
            },
            15: {
                "name": "CDN Origin Unreachable",
                "subsystem": "content_delivery",
                "vehicle_section": "cdn_origin",
                "error_type": "CDN-ORIGIN-UNREACHABLE",
                "sensor_type": "origin_health",
                "affected_services": ["cloud-cdn-service", "cloud-load-balancer"],
                "cascade_services": ["cloud-armor-waf"],
                "description": "Cloud CDN unable to reach origin backend, serving stale content",
                "investigation_notes": (
                    "Root cause: CDN edge nodes cannot reach the origin backend service. Status codes 502/503 "
                    "indicate the origin is down or overloaded; 504 indicates a timeout. A status of 0 means "
                    "the connection was refused or timed out at the TCP level. CDN is serving stale cached content "
                    "while the stale TTL has not expired. Once stale TTL expires, clients will see errors. Diagnose:\n"
                    "  gcloud compute backend-services get-health <backend> --global\n"
                    "  gcloud compute health-checks describe <health-check> --format='value(httpHealthCheck)'\n"
                    "  Console > Network Services > Load Balancing > <lb> > Backend details (health status)\n"
                    "Remediation: Check origin instance group health and scaling. If origin is a GKE service, verify "
                    "pods are running: kubectl get pods -n <namespace> -l app=<origin-app>. Reset the CDN backend "
                    "association to trigger fresh origin health checks:\n"
                    "  gcloud compute backend-services update <backend> --global --enable-cdn\n"
                    "Configure connection draining timeout and increase stale TTL as a safety net:\n"
                    "  gcloud compute backend-services update <backend> --global --serve-while-stale-max-age=3600"
                ),
                "remediation_action": "reset_cdn_backend",
                "error_message": (
                    "[CloudCDN] CDN-ORIGIN-UNREACHABLE backend={cdn_backend} "
                    "origin={cdn_origin_host} status_code={cdn_origin_status} "
                    "failures={cdn_origin_failures}/m "
                    "serving_stale={cdn_stale_pct}% ttl_remaining={cdn_stale_ttl_sec}s"
                ),
                "stack_trace": (
                    "Cloud CDN Origin Health Report\n"
                    "--------------------------------\n"
                    "Backend:       {cdn_backend}\n"
                    "Origin:        {cdn_origin_host}\n"
                    "Status Code:   {cdn_origin_status}\n"
                    "Failures/min:  {cdn_origin_failures}\n"
                    "Serving Stale: {cdn_stale_pct}%\n"
                    "Stale TTL:     {cdn_stale_ttl_sec}s remaining\n"
                    "Action: Check origin backend health and network path"
                ),
            },
            16: {
                "name": "Backend Unhealthy",
                "subsystem": "traffic_management",
                "vehicle_section": "load_balancing",
                "error_type": "LB-BACKEND-UNHEALTHY",
                "sensor_type": "health_check",
                "affected_services": ["cloud-load-balancer", "vpc-network-manager"],
                "cascade_services": ["cloud-cdn-service", "cloud-armor-waf"],
                "description": "Load balancer backend instances failing health checks",
                "investigation_notes": (
                    "Root cause: Backend instances are failing consecutive health checks, causing the LB to mark "
                    "them as unhealthy and stop sending traffic. Common causes: application crash/OOM, health check "
                    "endpoint misconfiguration (wrong port or path), firewall rules blocking health check probes "
                    "(GCP health checks come from 130.211.0.0/22 and 35.191.0.0/16). Diagnose:\n"
                    "  gcloud compute backend-services get-health <backend-service> --global\n"
                    "  gcloud compute health-checks describe <health-check>\n"
                    "  gcloud compute firewall-rules list --filter='sourceRanges:130.211.0.0/22 OR sourceRanges:35.191.0.0/16'\n"
                    "Remediation: Verify health check configuration matches the application's actual health endpoint:\n"
                    "  gcloud compute health-checks update http <hc> --port=<correct_port> --request-path=<correct_path>\n"
                    "Ensure firewall rules allow health check probes:\n"
                    "  gcloud compute firewall-rules create allow-health-checks --network=<vpc> "
                    "--source-ranges=130.211.0.0/22,35.191.0.0/16 --allow=tcp:<port>\n"
                    "Check instance logs for application crashes: Console > Compute Engine > <instance> > Serial port output."
                ),
                "remediation_action": "reconfigure_health_checks",
                "error_message": (
                    "[CloudLB] LB-BACKEND-UNHEALTHY forwarding_rule={lb_forwarding_rule} "
                    "backend_service={lb_backend_service} "
                    "unhealthy={lb_unhealthy_count}/{lb_total_backends} "
                    "health_check={lb_health_check} "
                    "failed_checks={lb_failed_checks} region={gcp_region}"
                ),
                "stack_trace": (
                    "Cloud Load Balancer Health Report\n"
                    "-----------------------------------\n"
                    "Forwarding Rule:  {lb_forwarding_rule}\n"
                    "Backend Service:  {lb_backend_service}\n"
                    "Unhealthy:        {lb_unhealthy_count}/{lb_total_backends}\n"
                    "Health Check:     {lb_health_check}\n"
                    "Failed Checks:    {lb_failed_checks} consecutive\n"
                    "Region:           {gcp_region}\n"
                    "Action: Investigate backend instance logs and health check config"
                ),
            },
            17: {
                "name": "SSL Certificate Expiry",
                "subsystem": "traffic_management",
                "vehicle_section": "ssl_termination",
                "error_type": "LB-SSL-CERT-EXPIRY",
                "sensor_type": "certificate",
                "affected_services": ["cloud-load-balancer", "cloud-cdn-service"],
                "cascade_services": ["cloud-armor-waf"],
                "description": "Google-managed SSL certificate approaching or past expiration",
                "investigation_notes": (
                    "Root cause: Google-managed SSL certificate renewal has failed. The managed status "
                    "FAILED_NOT_VISIBLE means Google's CA cannot reach the domain for DCV (Domain Control Validation), "
                    "FAILED_CAA_CHECKING means CAA DNS records do not permit Google's CA (pki.goog), and "
                    "PROVISIONING means the cert is still being issued but may be stuck. Check status:\n"
                    "  gcloud compute ssl-certificates describe <cert> --format='value(managed.status,managed.domainStatus)'\n"
                    "  gcloud compute ssl-certificates list --filter='type:MANAGED AND managed.status!=ACTIVE'\n"
                    "Remediation: Verify DNS A/AAAA record points to the LB's external IP:\n"
                    "  dig <domain> +short (must resolve to the forwarding rule IP)\n"
                    "Add or fix CAA record to allow Google's CA: add DNS CAA record 'pki.goog' for the domain. "
                    "If stuck in PROVISIONING > 24h, delete and recreate the certificate:\n"
                    "  gcloud compute ssl-certificates delete <cert>\n"
                    "  gcloud compute ssl-certificates create <cert> --domains=<domain> --global\n"
                    "Attach the new cert to the target HTTPS proxy immediately."
                ),
                "remediation_action": "reset_backend_service",
                "error_message": (
                    "[CloudLB] LB-SSL-CERT-EXPIRY certificate={ssl_cert_name} "
                    "domain={ssl_domain} expires_in={ssl_days_remaining}d "
                    "managed_status={ssl_managed_status} "
                    "forwarding_rules={ssl_affected_rules}"
                ),
                "stack_trace": (
                    "SSL Certificate Status Report\n"
                    "-------------------------------\n"
                    "Certificate:      {ssl_cert_name}\n"
                    "Domain:           {ssl_domain}\n"
                    "Days Remaining:   {ssl_days_remaining}\n"
                    "Managed Status:   {ssl_managed_status}\n"
                    "Forwarding Rules: {ssl_affected_rules}\n"
                    "Provisioning:     FAILED_NOT_VISIBLE\n"
                    "Action: Verify DNS authorization and domain ownership"
                ),
            },
            18: {
                "name": "VPN Tunnel Down",
                "subsystem": "vpn",
                "vehicle_section": "vpn_tunnels",
                "error_type": "VPN-TUNNEL-DOWN",
                "sensor_type": "tunnel_status",
                "affected_services": ["cloud-vpn-gateway", "cloud-interconnect"],
                "cascade_services": ["vpc-network-manager", "network-intelligence"],
                "description": "Cloud VPN tunnel losing connectivity to remote peer",
                "investigation_notes": (
                    "Root cause: VPN tunnel has transitioned to DOWN state, meaning IPsec SA (Security Association) "
                    "has expired or been torn down. Common causes: remote peer IP changed, pre-shared key mismatch "
                    "after rotation, IKE SA lifetime expired without successful rekey, or remote gateway is "
                    "unreachable due to internet path failure. Diagnose:\n"
                    "  gcloud compute vpn-tunnels describe <tunnel> --region=<region> --format='value(status,detailedStatus)'\n"
                    "  gcloud compute vpn-tunnels list --filter='status!=ESTABLISHED' --format='table(name,region,status,peerIp)'\n"
                    "  Console > Hybrid Connectivity > VPN > <tunnel> > Status tab (IKE logs)\n"
                    "Remediation: Reset the VPN tunnel to force IKE renegotiation:\n"
                    "  gcloud compute vpn-tunnels delete <tunnel> --region=<region>\n"
                    "  gcloud compute vpn-tunnels create <tunnel> --region=<region> --peer-address=<peer-ip> "
                    "--shared-secret=<secret> --ike-version=2 --router=<router> --vpn-gateway=<gw> --interface=0\n"
                    "Verify the remote peer is reachable: ping <peer-ip> from a VM in the same region. "
                    "Check if the remote side has rotated the pre-shared key."
                ),
                "remediation_action": "reset_vpn_tunnel",
                "error_message": (
                    "[CloudVPN] VPN-TUNNEL-DOWN tunnel={vpn_tunnel_name} "
                    "gateway={vpn_gateway_name} peer={vpn_peer_ip} "
                    "status=DOWN since {vpn_down_sec}s "
                    "ike_version={vpn_ike_version} "
                    "last_handshake={vpn_last_handshake_sec}s ago"
                ),
                "stack_trace": (
                    "Cloud VPN Tunnel Report\n"
                    "-------------------------\n"
                    "Tunnel:          {vpn_tunnel_name}\n"
                    "Gateway:         {vpn_gateway_name}\n"
                    "Peer IP:         {vpn_peer_ip}\n"
                    "Status:          DOWN\n"
                    "Down Since:      {vpn_down_sec}s\n"
                    "IKE Version:     {vpn_ike_version}\n"
                    "Last Handshake:  {vpn_last_handshake_sec}s ago\n"
                    "Action: Verify peer gateway and IKE configuration"
                ),
            },
            19: {
                "name": "IKE Negotiation Failure",
                "subsystem": "vpn",
                "vehicle_section": "ike_protocol",
                "error_type": "VPN-IKE-NEGOTIATION-FAILURE",
                "sensor_type": "ike_session",
                "affected_services": ["cloud-vpn-gateway", "cloud-interconnect"],
                "cascade_services": ["cloud-nat-gateway"],
                "description": "IKE phase negotiation failing between Cloud VPN and remote peer",
                "investigation_notes": (
                    "Root cause: IKE negotiation failure at the indicated phase. Phase 1 failures (NO_PROPOSAL_CHOSEN, "
                    "AUTHENTICATION_FAILED) indicate cipher suite or PSK mismatch. Phase 2 failures (TS_UNACCEPTABLE, "
                    "INVALID_KE_PAYLOAD) indicate traffic selector or DH group mismatch. GCP Cloud VPN supports "
                    "specific cipher combinations; the remote peer must match exactly. Diagnose:\n"
                    "  gcloud compute vpn-tunnels describe <tunnel> --region=<region> --format='value(detailedStatus)'\n"
                    "  Console > Logging > resource.type='vpn_gateway' severity>=WARNING\n"
                    "Remediation: For NO_PROPOSAL_CHOSEN, align cipher suites with GCP-supported combinations:\n"
                    "  IKEv2: AES-256-CBC + SHA-256 + DH group 14 (or AES-256-GCM for combined mode)\n"
                    "For AUTHENTICATION_FAILED, verify pre-shared key matches on both sides. Rekey the session:\n"
                    "  gcloud compute vpn-tunnels update <tunnel> --region=<region> --shared-secret=<new-secret>\n"
                    "  (then update the same secret on the remote peer)\n"
                    "For TS_UNACCEPTABLE, ensure traffic selectors (local/remote CIDR) match: Cloud VPN uses "
                    "0.0.0.0/0 by default with route-based VPN; remote peer must also use 0.0.0.0/0."
                ),
                "remediation_action": "rekey_vpn_session",
                "error_message": (
                    "[CloudVPN] VPN-IKE-NEGOTIATION-FAILURE tunnel={vpn_tunnel_name} "
                    "gateway={vpn_gateway_name} peer={vpn_peer_ip} "
                    "ike_phase={ike_phase} error=\"{ike_error}\" "
                    "retries={ike_retry_count}/{ike_max_retries}"
                ),
                "stack_trace": (
                    "Cloud VPN IKE Negotiation Report\n"
                    "----------------------------------\n"
                    "Tunnel:      {vpn_tunnel_name}\n"
                    "Gateway:     {vpn_gateway_name}\n"
                    "Peer IP:     {vpn_peer_ip}\n"
                    "IKE Phase:   {ike_phase}\n"
                    "Error:       {ike_error}\n"
                    "Retries:     {ike_retry_count}/{ike_max_retries}\n"
                    "Cipher:      AES-256-CBC\n"
                    "Auth:        SHA-256\n"
                    "Action: Verify pre-shared key and cipher suite compatibility"
                ),
            },
            20: {
                "name": "Connectivity Test Failure",
                "subsystem": "monitoring",
                "vehicle_section": "network_intelligence",
                "error_type": "NI-CONNECTIVITY-TEST-FAILURE",
                "sensor_type": "connectivity_test",
                "affected_services": ["network-intelligence", "vpc-network-manager"],
                "cascade_services": ["cloud-vpn-gateway", "cloud-interconnect"],
                "description": "Network Intelligence Center connectivity test detecting unreachable endpoints",
                "investigation_notes": (
                    "Root cause: Network Intelligence Center connectivity test is simulating the packet path and "
                    "identifying a blocking resource. UNREACHABLE means a firewall or route is explicitly blocking; "
                    "DROPPED means the packet is silently dropped; AMBIGUOUS means the analysis cannot determine "
                    "the exact drop point. The blocking_resource field identifies the specific resource. Diagnose:\n"
                    "  gcloud network-management connectivity-tests describe <test-name> --format=json\n"
                    "  gcloud network-management connectivity-tests rerun <test-name>\n"
                    "  Console > Network Intelligence Center > Connectivity Tests > <test> > Trace Details\n"
                    "Remediation: Based on the blocking resource type:\n"
                    "  - firewall-rule: Adjust or create allow rules (see channel 3 for priority semantics)\n"
                    "  - route: Add or fix routes with gcloud compute routes create <route> --network=<vpc> "
                    "--destination-range=<cidr> --next-hop-instance=<instance>\n"
                    "  - vpc-peering: Ensure custom route export/import is enabled on both sides of the peering\n"
                    "  - cloud-nat: Verify NAT configuration covers the source subnet\n"
                    "Re-run the test after each fix to validate: gcloud network-management connectivity-tests rerun <test>"
                ),
                "remediation_action": "reconfigure_firewall_rules",
                "error_message": (
                    "[NIC] NI-CONNECTIVITY-TEST-FAILURE test={ni_test_name} "
                    "src={ni_src_ip} dst={ni_dst_ip} protocol={ni_protocol} "
                    "result={ni_test_result} "
                    "hops_completed={ni_hops_completed}/{ni_hops_total} "
                    "blocking_resource={ni_blocking_resource}"
                ),
                "stack_trace": (
                    "Network Intelligence Connectivity Test\n"
                    "-----------------------------------------\n"
                    "Test Name:         {ni_test_name}\n"
                    "Source:            {ni_src_ip}\n"
                    "Destination:       {ni_dst_ip}\n"
                    "Protocol:          {ni_protocol}\n"
                    "Result:            {ni_test_result}\n"
                    "Hops Completed:    {ni_hops_completed}/{ni_hops_total}\n"
                    "Blocking Resource: {ni_blocking_resource}\n"
                    "Action: Review firewall rules and routing for blocking resource"
                ),
            },
        }

    # ── Topology ──────────────────────────────────────────────────────

    @property
    def service_topology(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "vpc-network-manager": [
                ("cloud-load-balancer", "/api/v1/lb/backend-health", "GET"),
                ("cloud-load-balancer", "/api/v1/lb/forwarding-rules", "GET"),
                ("cloud-nat-gateway", "/api/v1/nat/port-allocation", "GET"),
                ("cloud-armor-waf", "/api/v1/armor/policy-status", "GET"),
                ("cloud-dns-resolver", "/api/v1/dns/zone-health", "GET"),
            ],
            "cloud-load-balancer": [
                ("cloud-cdn-service", "/api/v1/cdn/cache-status", "GET"),
                ("cloud-cdn-service", "/api/v1/cdn/invalidate", "POST"),
                ("cloud-armor-waf", "/api/v1/armor/request-filter", "POST"),
                ("vpc-network-manager", "/api/v1/vpc/health-check-config", "GET"),
            ],
            "cloud-cdn-service": [
                ("cloud-load-balancer", "/api/v1/lb/origin-fetch", "GET"),
                ("vpc-network-manager", "/api/v1/vpc/route-to-origin", "GET"),
            ],
            "cloud-armor-waf": [
                ("cloud-load-balancer", "/api/v1/lb/block-request", "POST"),
                ("vpc-network-manager", "/api/v1/vpc/firewall-sync", "POST"),
            ],
            "cloud-nat-gateway": [
                ("vpc-network-manager", "/api/v1/vpc/subnet-info", "GET"),
                ("cloud-dns-resolver", "/api/v1/dns/external-resolve", "POST"),
            ],
            "cloud-dns-resolver": [
                ("vpc-network-manager", "/api/v1/vpc/peering-dns", "GET"),
            ],
            "cloud-interconnect": [
                ("vpc-network-manager", "/api/v1/vpc/route-advertise", "POST"),
                ("cloud-vpn-gateway", "/api/v1/vpn/failover-status", "GET"),
                ("network-intelligence", "/api/v1/ni/latency-report", "GET"),
            ],
            "cloud-vpn-gateway": [
                ("cloud-interconnect", "/api/v1/interconnect/backup-path", "GET"),
                ("vpc-network-manager", "/api/v1/vpc/tunnel-routes", "POST"),
            ],
            "network-intelligence": [
                ("vpc-network-manager", "/api/v1/vpc/topology-map", "GET"),
                ("cloud-vpn-gateway", "/api/v1/vpn/tunnel-metrics", "GET"),
                ("cloud-interconnect", "/api/v1/interconnect/circuit-status", "GET"),
            ],
        }

    @property
    def entry_endpoints(self) -> dict[str, list[tuple[str, str]]]:
        return {
            "vpc-network-manager": [
                ("/api/v1/vpc/networks", "GET"),
                ("/api/v1/vpc/subnets", "GET"),
                ("/api/v1/vpc/firewall-rules", "GET"),
            ],
            "cloud-load-balancer": [
                ("/api/v1/lb/status", "GET"),
                ("/api/v1/lb/backends", "GET"),
                ("/api/v1/lb/configure", "POST"),
            ],
            "cloud-cdn-service": [
                ("/api/v1/cdn/analytics", "GET"),
                ("/api/v1/cdn/purge", "POST"),
            ],
            "cloud-armor-waf": [
                ("/api/v1/armor/policies", "GET"),
                ("/api/v1/armor/events", "GET"),
                ("/api/v1/armor/rule-update", "POST"),
            ],
            "cloud-nat-gateway": [
                ("/api/v1/nat/status", "GET"),
                ("/api/v1/nat/mappings", "GET"),
            ],
            "cloud-dns-resolver": [
                ("/api/v1/dns/query", "POST"),
                ("/api/v1/dns/zones", "GET"),
                ("/api/v1/dns/health", "GET"),
            ],
            "cloud-interconnect": [
                ("/api/v1/interconnect/attachments", "GET"),
                ("/api/v1/interconnect/diagnostics", "GET"),
            ],
            "cloud-vpn-gateway": [
                ("/api/v1/vpn/tunnels", "GET"),
                ("/api/v1/vpn/status", "GET"),
            ],
            "network-intelligence": [
                ("/api/v1/ni/tests", "GET"),
                ("/api/v1/ni/topology", "GET"),
                ("/api/v1/ni/run-test", "POST"),
            ],
        }

    @property
    def db_operations(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "vpc-network-manager": [
                ("SELECT", "vpc_networks", "SELECT network_id, name, subnet_mode, peering_count, route_count FROM vpc_networks WHERE project = ? AND status = 'ACTIVE'"),
                ("SELECT", "firewall_rules", "SELECT rule_id, name, priority, direction, action, target_tags FROM firewall_rules WHERE network_id = ? ORDER BY priority"),
                ("UPDATE", "vpc_routes", "UPDATE vpc_routes SET status = ?, updated_at = NOW() WHERE network_id = ? AND dest_range = ?"),
            ],
            "cloud-load-balancer": [
                ("SELECT", "forwarding_rules", "SELECT rule_id, ip_address, port_range, target, region FROM forwarding_rules WHERE project = ? AND status = 'ACTIVE'"),
                ("SELECT", "backend_services", "SELECT service_id, name, protocol, health_check_id, backends FROM backend_services WHERE forwarding_rule_id = ?"),
                ("UPDATE", "health_checks", "UPDATE health_checks SET last_check = NOW(), status = ? WHERE health_check_id = ?"),
            ],
            "cloud-cdn-service": [
                ("SELECT", "cdn_backends", "SELECT backend_id, origin_host, cache_mode, ttl_sec, hit_ratio FROM cdn_backends WHERE enabled = true"),
                ("INSERT", "cache_invalidations", "INSERT INTO cache_invalidations (backend_id, path_pattern, requested_at, status) VALUES (?, ?, NOW(), 'pending')"),
            ],
            "cloud-armor-waf": [
                ("SELECT", "security_policies", "SELECT policy_id, name, rule_count, backend_count, last_updated FROM security_policies WHERE project = ?"),
                ("SELECT", "waf_events", "SELECT timestamp, rule_id, action, src_ip, request_path, matched_pattern FROM waf_events WHERE policy_id = ? AND timestamp > NOW() - INTERVAL 1 HOUR ORDER BY timestamp DESC LIMIT 100"),
            ],
            "cloud-dns-resolver": [
                ("SELECT", "dns_zones", "SELECT zone_id, dns_name, visibility, dnssec_state, record_count FROM dns_zones WHERE project = ?"),
                ("SELECT", "dns_records", "SELECT name, type, ttl, rrdatas FROM dns_records WHERE zone_id = ? AND type = ?"),
            ],
            "cloud-interconnect": [
                ("SELECT", "interconnect_attachments", "SELECT attachment_id, name, region, bandwidth, vlan_tag, state FROM interconnect_attachments WHERE interconnect_id = ?"),
            ],
            "network-intelligence": [
                ("SELECT", "connectivity_tests", "SELECT test_id, name, source, destination, protocol, result, last_run FROM connectivity_tests WHERE project = ? ORDER BY last_run DESC"),
                ("INSERT", "test_results", "INSERT INTO test_results (test_id, result, hops, blocking_resource, tested_at) VALUES (?, ?, ?, ?, NOW())"),
            ],
        }

    # ── Infrastructure ────────────────────────────────────────────────

    @property
    def hosts(self) -> list[dict[str, Any]]:
        return [
            {
                "host.name": "gcpnet-host-central1",
                "host.id": "4801234567890123456",
                "host.arch": "amd64",
                "host.type": "n2-standard-4",
                "host.image.id": "projects/cos-cloud/global/images/cos-113-18244-85-29",
                "host.cpu.model.name": "Intel(R) Xeon(R) CPU @ 2.80GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "106",
                "host.cpu.stepping": "7",
                "host.cpu.cache.l2.size": 1310720,
                "host.ip": ["10.128.0.10", "10.128.0.11"],
                "host.mac": ["42:01:0a:80:00:0a", "42:01:0a:80:00:0b"],
                "os.type": "linux",
                "os.description": "Container-Optimized OS 113",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "us-central1",
                "cloud.availability_zone": "us-central1-a",
                "cloud.account.id": "gcpnet-prod-project",
                "cloud.instance.id": "4801234567890123456",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 100 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "gcpnet-host-east1",
                "host.id": "5912345678901234567",
                "host.arch": "amd64",
                "host.type": "n2-standard-4",
                "host.image.id": "projects/cos-cloud/global/images/cos-113-18244-85-29",
                "host.cpu.model.name": "Intel(R) Xeon(R) CPU @ 2.80GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "106",
                "host.cpu.stepping": "7",
                "host.cpu.cache.l2.size": 1310720,
                "host.ip": ["10.142.0.10", "10.142.0.11"],
                "host.mac": ["42:01:0a:8e:00:0a", "42:01:0a:8e:00:0b"],
                "os.type": "linux",
                "os.description": "Container-Optimized OS 113",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "us-east1",
                "cloud.availability_zone": "us-east1-b",
                "cloud.account.id": "gcpnet-prod-project",
                "cloud.instance.id": "5912345678901234567",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 100 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "gcpnet-host-europe1",
                "host.id": "6023456789012345678",
                "host.arch": "amd64",
                "host.type": "n2-standard-4",
                "host.image.id": "projects/cos-cloud/global/images/cos-113-18244-85-29",
                "host.cpu.model.name": "Intel(R) Xeon(R) CPU @ 2.80GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "106",
                "host.cpu.stepping": "7",
                "host.cpu.cache.l2.size": 1310720,
                "host.ip": ["10.132.0.10", "10.132.0.11"],
                "host.mac": ["42:01:0a:84:00:0a", "42:01:0a:84:00:0b"],
                "os.type": "linux",
                "os.description": "Container-Optimized OS 113",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "europe-west1",
                "cloud.availability_zone": "europe-west1-b",
                "cloud.account.id": "gcpnet-prod-project",
                "cloud.instance.id": "6023456789012345678",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 100 * 1024 * 1024 * 1024,
            },
        ]

    @property
    def k8s_clusters(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "gcpnet-gke-central1",
                "provider": "gcp",
                "platform": "gcp_gke",
                "region": "us-central1",
                "zones": ["us-central1-a", "us-central1-b", "us-central1-c"],
                "os_description": "Container-Optimized OS",
                "services": ["vpc-network-manager", "cloud-load-balancer", "cloud-cdn-service"],
            },
            {
                "name": "gcpnet-gke-east1",
                "provider": "gcp",
                "platform": "gcp_gke",
                "region": "us-east1",
                "zones": ["us-east1-b", "us-east1-c", "us-east1-d"],
                "os_description": "Container-Optimized OS",
                "services": ["cloud-armor-waf", "cloud-nat-gateway", "cloud-dns-resolver"],
            },
            {
                "name": "gcpnet-gke-europe1",
                "provider": "gcp",
                "platform": "gcp_gke",
                "region": "europe-west1",
                "zones": ["europe-west1-b", "europe-west1-c", "europe-west1-d"],
                "os_description": "Container-Optimized OS",
                "services": ["cloud-interconnect", "cloud-vpn-gateway", "network-intelligence"],
            },
        ]

    # ── Dashboard Override (region-based columns) ─────────────────────

    @property
    def dashboard_cloud_groups(self) -> list[dict[str, Any]]:
        """Override to group by GCP region instead of cloud provider."""
        region_order = ["us-central1", "us-east1", "europe-west1"]
        x_starts = [0, 16, 33]
        col_widths = [15, 16, 15]
        groups = []
        for i, region in enumerate(region_order):
            svcs = [
                name for name, cfg in self.services.items()
                if cfg["cloud_region"] == region
            ]
            cluster = next(
                (c for c in self.k8s_clusters if c["region"] == region), {}
            )
            groups.append({
                "label": f"**GCP** {region}",
                "services": svcs,
                "x_start": x_starts[i],
                "col_width": col_widths[i],
                "cluster": cluster.get("name", ""),
            })
        return groups

    # ── Theme ─────────────────────────────────────────────────────────

    @property
    def theme(self) -> UITheme:
        return UITheme(
            bg_primary="#0d1117",
            bg_secondary="#161b22",
            bg_tertiary="#21262d",
            accent_primary="#4285F4",       # Google Blue
            accent_secondary="#34A853",     # Google Green
            text_primary="#e6edf3",
            text_secondary="#8b949e",
            text_accent="#4285F4",          # Google Blue
            status_nominal="#34A853",       # Google Green
            status_warning="#FBBC04",       # Google Yellow
            status_critical="#EA4335",      # Google Red
            status_info="#4285F4",          # Google Blue
            font_family="'Google Sans', 'Inter', system-ui, sans-serif",
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
            "id": "gcp-network-analyst",
            "name": "Google Cloud Network Analyst",
            "assessment_tool_name": "network_health_assessment",
            "system_prompt": (
                "You are the Google Cloud Network Analyst, an expert AI assistant "
                "for GCP network operations. You help network engineers investigate "
                "incidents, analyze telemetry data, and provide root cause analysis "
                "for fault conditions across 9 GCP networking services spanning 3 regions "
                "(us-central1, us-east1, europe-west1). "
                "You have deep expertise in Google Cloud VPC networking, Cloud Armor WAF "
                "and DDoS protection, Cloud NAT gateway management, Cloud DNS (including DNSSEC), "
                "Dedicated Interconnect and BGP routing, Cloud VPN (IKE/IPsec), "
                "Cloud CDN caching and origin management, Cloud Load Balancing (L4/L7), "
                "and Network Intelligence Center connectivity testing. "
                "When investigating incidents, search for these GCP-specific identifiers in logs: "
                "VPC errors (VPC-ROUTE-LIMIT-EXCEEDED, VPC-SUBNET-IP-EXHAUSTION, VPC-FIREWALL-RULE-CONFLICT), "
                "Cloud Armor events (ARMOR-DDOS-ALERT, ARMOR-FALSE-POSITIVE, ARMOR-POLICY-SYNC-FAILURE), "
                "NAT faults (NAT-PORT-EXHAUSTION, NAT-ENDPOINT-MAPPING-FAILURE, NAT-IP-ALLOCATION-ERROR), "
                "DNS issues (DNS-DNSSEC-VALIDATION-FAILURE, DNS-ZONE-PROPAGATION-DELAY), "
                "Interconnect faults (INTERCONNECT-CIRCUIT-DOWN, INTERCONNECT-BGP-FLAP), "
                "CDN errors (CDN-CACHE-MISS-SPIKE, CDN-ORIGIN-UNREACHABLE), "
                "LB faults (LB-BACKEND-UNHEALTHY, LB-SSL-CERT-EXPIRY), "
                "VPN errors (VPN-TUNNEL-DOWN, VPN-IKE-NEGOTIATION-FAILURE), "
                "and NIC events (NI-CONNECTIVITY-TEST-FAILURE). "
                "Log messages are in body.text — NEVER search the body field alone."
            ),
        }

    @property
    def assessment_tool_config(self) -> dict[str, Any]:
        return {
            "id": "network_health_assessment",
            "description": (
                "Comprehensive network health assessment. Evaluates all "
                "GCP networking services against operational readiness criteria. "
                "Returns data for health evaluation across VPC, Cloud Armor, "
                "NAT, DNS, Interconnect, VPN, CDN, and Load Balancing systems. "
                "Log message field: body.text (never use 'body' alone)."
            ),
        }

    @property
    def knowledge_base_docs(self) -> list[dict[str, Any]]:
        return []  # Populated by deployer from channel_registry

    # ── Service Classes ───────────────────────────────────────────────

    def get_service_classes(self) -> list[type]:
        from scenarios.gcp.services.vpc_network_manager import VpcNetworkManagerService
        from scenarios.gcp.services.cloud_load_balancer import CloudLoadBalancerService
        from scenarios.gcp.services.cloud_cdn_service import CloudCdnService
        from scenarios.gcp.services.cloud_armor_waf import CloudArmorWafService
        from scenarios.gcp.services.cloud_nat_gateway import CloudNatGatewayService
        from scenarios.gcp.services.cloud_dns_resolver import CloudDnsResolverService
        from scenarios.gcp.services.cloud_interconnect import CloudInterconnectService
        from scenarios.gcp.services.cloud_vpn_gateway import CloudVpnGatewayService
        from scenarios.gcp.services.network_intelligence import NetworkIntelligenceService

        return [
            VpcNetworkManagerService,
            CloudLoadBalancerService,
            CloudCdnService,
            CloudArmorWafService,
            CloudNatGatewayService,
            CloudDnsResolverService,
            CloudInterconnectService,
            CloudVpnGatewayService,
            NetworkIntelligenceService,
        ]

    # ── Trace Attributes & RCA ───────────────────────────────────────

    def get_trace_attributes(self, service_name: str, rng) -> dict:
        uptime_s = int(time.time()) % 86400
        base = {
            "gcp.project_id": rng.choice(["gcpnet-prod-001", "gcpnet-prod-002", "gcpnet-staging"]),
            "gcp.network_tier": rng.choice(["PREMIUM", "PREMIUM", "PREMIUM", "STANDARD"]),
        }
        svc_attrs = {
            "vpc-network-manager": {
                "vpc.network_tier": rng.choice(["PREMIUM", "STANDARD"]),
                "vpc.subnet_cidr": rng.choice(["10.128.0.0/20", "10.142.0.0/20", "10.132.0.0/20"]),
                "vpc.peering_count": rng.randint(1, 8),
                "vpc.route_table_size": rng.randint(80, 250),
                "vpc.mtu": rng.choice([1460, 1500, 8896]),
            },
            "cloud-armor-waf": {
                "armor.policy_name": rng.choice(["gcpnet-waf-policy", "gcpnet-ddos-policy", "gcpnet-edge-policy"]),
                "armor.rule_count": rng.randint(8, 45),
                "armor.adaptive_protection": rng.choice([True, True, False]),
                "armor.evaluation_mode": rng.choice(["STANDARD", "ADVANCED"]),
            },
            "cloud-nat-gateway": {
                "nat.pool_utilization": round(rng.uniform(30.0, 95.0), 1),
                "nat.port_allocation": rng.choice(["STATIC", "DYNAMIC"]),
                "nat.min_ports_per_vm": rng.choice([64, 256, 1024, 2048]),
                "nat.external_ip_count": rng.randint(1, 10),
            },
            "cloud-dns-resolver": {
                "dns.query_type": rng.choice(["A", "AAAA", "CNAME", "MX", "TXT", "SRV"]),
                "dns.zone_name": rng.choice(["gcpnet-internal", "gcpnet-prod-zone", "gcpnet-services"]),
                "dns.dnssec_enabled": rng.choice([True, True, False]),
                "dns.response_policy_count": rng.randint(0, 5),
            },
            "cloud-interconnect": {
                "interconnect.circuit_id": f"CIR-{rng.randint(100000, 999999)}",
                "interconnect.bandwidth_gbps": rng.choice([10, 10, 100]),
                "interconnect.lacp_state": rng.choice(["ACTIVE", "ACTIVE", "ACTIVE", "DETACHED"]),
                "interconnect.location": rng.choice(["iad-zone1-1", "dfw-zone1-1", "ams-zone1-1"]),
            },
            "cloud-vpn-gateway": {
                "vpn.tunnel_status": rng.choice(["ESTABLISHED", "ESTABLISHED", "ESTABLISHED", "NEGOTIATING"]),
                "vpn.ike_version": rng.choice(["IKEv2", "IKEv2", "IKEv1"]),
                "vpn.peer_ip": f"203.0.113.{rng.randint(1, 254)}",
                "vpn.ha_redundancy": rng.choice([True, True, False]),
            },
            "cloud-cdn-service": {
                "cdn.cache_mode": rng.choice(["CACHE_ALL_STATIC", "USE_ORIGIN_HEADERS", "FORCE_CACHE_ALL"]),
                "cdn.origin_region": rng.choice(["us-central1", "us-east1", "europe-west1"]),
                "cdn.signed_url_enabled": rng.choice([True, False]),
                "cdn.negative_caching": rng.choice([True, False]),
            },
            "cloud-load-balancer": {
                "lb.backend_count": rng.randint(3, 12),
                "lb.health_check_interval": rng.choice([5, 10, 30]),
                "lb.scheme": rng.choice(["EXTERNAL_MANAGED", "INTERNAL_MANAGED", "EXTERNAL"]),
                "lb.protocol": rng.choice(["HTTPS", "HTTP2", "TCP", "gRPC"]),
            },
            "network-intelligence": {
                "ni.test_count_active": rng.randint(5, 25),
                "ni.topology_nodes": rng.randint(30, 120),
                "ni.last_scan_age_sec": rng.randint(10, 300),
                "ni.firewall_insights_enabled": rng.choice([True, True, False]),
            },
        }
        base.update(svc_attrs.get(service_name, {}))
        return base

    def get_rca_clues(self, channel: int, service_name: str, rng) -> dict:
        clues = {
            1: {  # VPC Peering Route Limit
                "vpc-network-manager": {"vpc.route_utilization_pct": round(rng.uniform(96, 100), 1), "vpc.peering_name": "peer-to-shared-vpc"},
                "cloud-load-balancer": {"lb.route_advertisement_status": "stale", "lb.backend_reachability": "partial"},
                "cloud-nat-gateway": {"nat.egress_route_affected": True, "nat.fallback_route": "default-igw"},
            },
            2: {  # Subnet IP Exhaustion
                "vpc-network-manager": {"vpc.subnet_util_pct": round(rng.uniform(96, 100), 1), "vpc.secondary_range_available": False},
                "cloud-nat-gateway": {"nat.ip_allocation_failures": rng.randint(10, 50), "nat.affected_subnet": "gcpnet-subnet-central1"},
                "cloud-load-balancer": {"lb.new_backend_registration": "blocked", "lb.pending_ip_requests": rng.randint(5, 20)},
                "cloud-cdn-service": {"cdn.origin_health_check_ip": "exhausted"},
            },
            3: {  # Firewall Rule Conflict
                "vpc-network-manager": {"vpc.conflicting_priorities": "900-vs-1000", "vpc.denied_flow_spike": True},
                "cloud-armor-waf": {"armor.policy_bypass_detected": True, "armor.upstream_fw_conflict": "deny-all-ingress"},
                "cloud-interconnect": {"interconnect.onprem_traffic_blocked": True, "interconnect.affected_fw_rule": "deny-egress-default"},
            },
            4: {  # DDoS Alert Triggered
                "cloud-armor-waf": {"armor.attack_vector": rng.choice(["SYN_FLOOD", "HTTP_FLOOD"]), "armor.adaptive_protection_mode": "engaged"},
                "cloud-load-balancer": {"lb.request_spike_pct": round(rng.uniform(400, 2000), 0), "lb.backend_overload": True},
                "vpc-network-manager": {"vpc.ingress_bandwidth_spike": True, "vpc.flow_log_anomaly": "volumetric"},
                "cloud-cdn-service": {"cdn.cache_bypass_rate": round(rng.uniform(60, 95), 1)},
            },
            5: {  # WAF False Positive Surge
                "cloud-armor-waf": {"armor.false_positive_rule": "sqli-v33-stable", "armor.sensitivity_level": 1},
                "cloud-cdn-service": {"cdn.blocked_asset_paths": "/api/v2/search,/graphql", "cdn.cache_miss_from_blocks": True},
                "cloud-load-balancer": {"lb.legitimate_traffic_dropped_pct": round(rng.uniform(5, 25), 1)},
            },
            6: {  # Security Policy Sync Failure
                "cloud-armor-waf": {"armor.policy_version_mismatch": True, "armor.stale_backends_count": rng.randint(2, 5)},
                "vpc-network-manager": {"vpc.security_posture": "inconsistent", "vpc.unprotected_backends": rng.randint(1, 3)},
                "cloud-load-balancer": {"lb.policy_enforcement_gap": True, "lb.backends_without_policy": rng.randint(1, 4)},
            },
            7: {  # NAT Port Exhaustion
                "cloud-nat-gateway": {"nat.min_ports_per_vm": 64, "nat.dynamic_port_allocation": False},
                "vpc-network-manager": {"vpc.egress_failures": rng.randint(50, 300), "vpc.affected_vms": rng.randint(3, 12)},
                "cloud-load-balancer": {"lb.external_api_timeouts": rng.randint(20, 100)},
                "cloud-dns-resolver": {"dns.external_resolution_failures": rng.randint(10, 80)},
            },
            8: {  # NAT Endpoint Mapping Failure
                "cloud-nat-gateway": {"nat.mapping_type_current": "ENDPOINT_INDEPENDENT", "nat.port_reuse_blocked": True},
                "cloud-load-balancer": {"lb.nat_path_affected": True, "lb.connection_draining_stuck": rng.choice([True, False])},
                "cloud-cdn-service": {"cdn.origin_fetch_via_nat": "failing", "cdn.stale_content_served": True},
            },
            9: {  # NAT IP Allocation Error
                "cloud-nat-gateway": {"nat.quota_name": "EXTERNAL_IP_ADDRESS", "nat.quota_usage_pct": round(rng.uniform(95, 100), 1)},
                "vpc-network-manager": {"vpc.nat_ip_conflict": True, "vpc.orphaned_static_ips": rng.randint(2, 8)},
                "cloud-interconnect": {"interconnect.nat_failover_path": "unavailable"},
            },
            10: {  # DNSSEC Validation Failure
                "cloud-dns-resolver": {"dns.rrsig_status": rng.choice(["EXPIRED", "EXPIRING"]), "dns.ds_record_stale": True},
                "vpc-network-manager": {"vpc.dns_resolution_failures": rng.randint(50, 300), "vpc.affected_services": "internal"},
                "cloud-armor-waf": {"armor.dns_based_rules_stale": True},
                "network-intelligence": {"ni.dns_path_test": "FAIL", "ni.dnssec_chain_broken": True},
            },
            11: {  # DNS Zone Propagation Delay
                "cloud-dns-resolver": {"dns.propagation_lag_sec": rng.randint(120, 600), "dns.change_status": "PENDING"},
                "cloud-load-balancer": {"lb.dns_stale_ip": True, "lb.traffic_to_old_backend": round(rng.uniform(10, 40), 1)},
                "cloud-cdn-service": {"cdn.dns_cache_stale": True, "cdn.origin_resolution_mismatch": True},
                "network-intelligence": {"ni.dns_consistency_check": "INCONSISTENT"},
            },
            12: {  # Interconnect Circuit Down
                "cloud-interconnect": {"interconnect.lacp_state": "DETACHED", "interconnect.light_level_dbm": round(rng.uniform(-30, -20), 1)},
                "vpc-network-manager": {"vpc.onprem_route_withdrawn": True, "vpc.bgp_routes_lost": rng.randint(10, 50)},
                "cloud-vpn-gateway": {"vpn.failover_activated": True, "vpn.backup_tunnel_latency_ms": rng.randint(15, 80)},
                "network-intelligence": {"ni.interconnect_path_test": "UNREACHABLE", "ni.failover_status": "IN_PROGRESS"},
            },
            13: {  # BGP Session Flap
                "cloud-interconnect": {"interconnect.bgp_hold_timer": rng.choice([90, 120, 180]), "interconnect.bfd_status": "DOWN"},
                "cloud-vpn-gateway": {"vpn.route_convergence_delayed": True, "vpn.backup_route_active": rng.choice([True, False])},
                "vpc-network-manager": {"vpc.route_table_oscillating": True, "vpc.stale_routes": rng.randint(5, 20)},
                "cloud-nat-gateway": {"nat.outbound_path_flapping": True},
            },
            14: {  # CDN Cache Miss Spike
                "cloud-cdn-service": {"cdn.cache_key_policy": "includes_query_strings", "cdn.unique_cache_keys": rng.randint(50000, 200000)},
                "cloud-load-balancer": {"lb.origin_request_surge": round(rng.uniform(300, 800), 0), "lb.backend_cpu_spike": True},
                "vpc-network-manager": {"vpc.egress_bandwidth_spike": True},
            },
            15: {  # CDN Origin Unreachable
                "cloud-cdn-service": {"cdn.origin_status_code": rng.choice([502, 503, 504]), "cdn.stale_ttl_remaining_sec": rng.randint(30, 300)},
                "cloud-load-balancer": {"lb.origin_health_check": "FAILING", "lb.healthy_backends": 0},
                "cloud-armor-waf": {"armor.origin_path_blocked": rng.choice([True, False])},
            },
            16: {  # Backend Unhealthy
                "cloud-load-balancer": {"lb.health_check_port": rng.choice([8080, 443, 3000]), "lb.consecutive_failures": rng.randint(3, 10)},
                "vpc-network-manager": {"vpc.health_check_fw_rule": rng.choice(["PRESENT", "MISSING"]), "vpc.probe_source_range": "130.211.0.0/22"},
                "cloud-cdn-service": {"cdn.serving_stale_from_unhealthy": True},
                "cloud-armor-waf": {"armor.backend_protection_gap": True},
            },
            17: {  # SSL Certificate Expiry
                "cloud-load-balancer": {"lb.managed_cert_status": rng.choice(["FAILED_NOT_VISIBLE", "FAILED_CAA_CHECKING"]), "lb.cert_domain": "api.gcpnet.example.com"},
                "cloud-cdn-service": {"cdn.https_serving_degraded": True, "cdn.fallback_to_http": rng.choice([True, False])},
                "cloud-armor-waf": {"armor.ssl_policy_affected": True},
            },
            18: {  # VPN Tunnel Down
                "cloud-vpn-gateway": {"vpn.ipsec_sa_status": "EXPIRED", "vpn.last_rekey_sec_ago": rng.randint(300, 3600)},
                "cloud-interconnect": {"interconnect.vpn_backup_needed": True, "interconnect.capacity_headroom_pct": round(rng.uniform(5, 30), 1)},
                "vpc-network-manager": {"vpc.tunnel_routes_withdrawn": rng.randint(5, 20), "vpc.affected_remote_cidrs": rng.randint(2, 8)},
                "network-intelligence": {"ni.vpn_path_test": "DOWN", "ni.latency_via_backup_ms": rng.randint(20, 120)},
            },
            19: {  # IKE Negotiation Failure
                "cloud-vpn-gateway": {"vpn.ike_phase_failing": rng.choice(["1", "2"]), "vpn.cipher_mismatch": rng.choice([True, False])},
                "cloud-interconnect": {"interconnect.vpn_failback_blocked": True},
                "cloud-nat-gateway": {"nat.vpn_egress_rerouted": True},
            },
            20: {  # Connectivity Test Failure
                "network-intelligence": {"ni.blocking_resource_type": rng.choice(["firewall-rule", "route", "vpc-peering", "cloud-nat"]), "ni.packet_trace_hops": rng.randint(2, 5)},
                "vpc-network-manager": {"vpc.topology_anomaly_detected": True, "vpc.unreachable_subnets": rng.randint(1, 4)},
                "cloud-vpn-gateway": {"vpn.cross_network_test": "FAIL"},
                "cloud-interconnect": {"interconnect.hybrid_path_test": "FAIL"},
            },
        }
        channel_clues = clues.get(channel, {})
        return channel_clues.get(service_name, {})

    def get_correlation_attribute(self, channel: int, is_error: bool, rng) -> dict:
        correlation_attrs = {
            1: ("deployment.terraform_version", "tf-1.7.2-canary"),
            2: ("infra.gke_node_pool", "pool-spot-n2d-burst"),
            3: ("network.firewall_policy_rev", "fw-policy-v34-rollback"),
            4: ("infra.armor_ruleset", "owasp-crs-v4.0.0-rc2"),
            5: ("deployment.waf_config_hash", "cfg-ab3f91-untested"),
            6: ("network.policy_push_agent", "armor-sync-v2.1.0-beta"),
            7: ("infra.nat_config_rev", "nat-dpa-v1.3-experimental"),
            8: ("deployment.nat_mapping_mode", "endpoint-independent-v2"),
            9: ("infra.ip_allocation_pool", "static-pool-region-east1"),
            10: ("network.dnssec_key_id", "ksk-2024q4-rotation"),
            11: ("deployment.dns_ttl_override", "ttl-60s-migration"),
            12: ("infra.interconnect_optic", "lr4-100g-batch-2024q3"),
            13: ("network.bgp_timer_profile", "aggressive-bfd-50ms"),
            14: ("deployment.cdn_cache_key", "include-all-query-params"),
            15: ("infra.origin_health_check", "hc-tcp-8080-patched"),
            16: ("network.health_check_fw", "fw-rule-missing-35-191"),
            17: ("deployment.cert_manager", "google-managed-v2-beta"),
            18: ("infra.vpn_psk_rotation", "psk-rotate-2024q4-batch2"),
            19: ("network.ike_cipher_suite", "aes256-sha384-dh20-nonstandard"),
            20: ("deployment.ni_agent_version", "nic-agent-v3.2.0-rc1"),
        }
        attr_key, attr_val = correlation_attrs.get(channel, ("deployment.terraform_version", "unknown"))
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
            # ── VPC / Core Network (channels 1-3) ──
            "gcp_project": random.choice(["gcpnet-prod-001", "gcpnet-prod-002", "gcpnet-staging"]),
            "gcp_region": random.choice(["us-central1", "us-east1", "europe-west1"]),
            "vpc_network": random.choice(["gcpnet-vpc-prod", "gcpnet-vpc-staging", "gcpnet-vpc-shared"]),
            "vpc_peering_name": random.choice(["peer-to-shared-vpc", "peer-to-onprem", "peer-to-partner"]),
            "route_count": random.randint(240, 250),
            "route_max": 250,
            "dropped_prefixes": random.randint(5, 30),
            "subnet_name": random.choice([
                "gcpnet-subnet-central1", "gcpnet-subnet-east1",
                "gcpnet-subnet-europe1", "gcpnet-subnet-services",
            ]),
            "subnet_cidr": random.choice(["10.128.0.0/20", "10.142.0.0/20", "10.132.0.0/20"]),
            "subnet_used_ips": random.randint(3900, 4090),
            "subnet_total_ips": 4094,
            "subnet_util_pct": round(random.uniform(95.0, 100.0), 1),
            "fw_rule_a": random.choice(["allow-internal-all", "allow-health-checks", "allow-iap-ssh"]),
            "fw_rule_b": random.choice(["deny-egress-default", "deny-all-ingress", "deny-suspicious-ips"]),
            "fw_priority_a": random.choice([1000, 1100, 1200]),
            "fw_priority_b": random.choice([900, 950, 1000]),
            "fw_dropped_packets": random.randint(100, 5000),

            # ── Cloud Armor / Security (channels 4-6) ──
            "armor_policy": random.choice(["gcpnet-waf-policy", "gcpnet-ddos-policy", "gcpnet-edge-policy"]),
            "armor_backend": random.choice(["backend-lb-central1", "backend-lb-east1", "backend-lb-europe1"]),
            "armor_rule_name": random.choice(["rate-limit-global", "geo-block-sanctioned", "sqli-detection", "xss-prevention"]),
            "ddos_attack_type": random.choice(["SYN_FLOOD", "UDP_AMPLIFICATION", "HTTP_FLOOD", "DNS_AMPLIFICATION"]),
            "ddos_volume_gbps": round(random.uniform(5.0, 120.0), 1),
            "ddos_source_regions": random.choice(["CN,RU,BR", "RU,UA,KZ", "multiple (>20 countries)"]),
            "ddos_mitigated_pct": round(random.uniform(92.0, 99.9), 1),
            "waf_rule_id": random.choice(["owasp-crs-v030301-id942100", "sqli-v33-stable", "xss-v33-stable", "rce-v33-stable"]),
            "waf_blocked_count": random.randint(100, 5000),
            "waf_fp_rate": round(random.uniform(15.0, 60.0), 1),
            "waf_affected_paths": random.choice(["/api/v2/search", "/api/v1/upload", "/graphql", "/api/v1/webhook"]),
            "waf_sensitivity_level": random.choice(["1 (High)", "2 (Medium)", "3 (Low)"]),
            "policy_version": random.randint(10, 50),
            "backends_synced": random.randint(1, 3),
            "backends_total": random.randint(4, 8),
            "policy_last_sync_sec": random.randint(120, 600),
            "policy_sync_error": random.choice([
                "backend not responding to policy push",
                "version conflict with pending update",
                "timeout waiting for backend acknowledgment",
            ]),

            # ── Cloud NAT (channels 7-9) ──
            "nat_gateway_name": random.choice(["gcpnet-nat-central1", "gcpnet-nat-east1", "gcpnet-nat-europe1"]),
            "nat_ports_used": random.randint(60000, 64000),
            "nat_ports_total": 64512,
            "nat_port_util_pct": round(random.uniform(92.0, 99.5), 1),
            "nat_dropped_conns": random.randint(50, 500),
            "nat_top_vm": random.choice(["gke-node-pool-a-001", "gke-node-pool-b-002", "gke-node-pool-c-003"]),
            "nat_mapping_type": random.choice(["ENDPOINT_INDEPENDENT", "ADDRESS_DEPENDENT"]),
            "nat_mapping_failures": random.randint(100, 2000),
            "nat_external_ip": f"34.{random.randint(64,127)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "nat_protocol": random.choice(["TCP", "UDP", "TCP+UDP"]),
            "nat_allocated_ips": random.randint(8, 10),
            "nat_max_ips": 10,
            "nat_pending_allocs": random.randint(2, 8),
            "nat_alloc_error": random.choice([
                "QUOTA_EXCEEDED: EXTERNAL_IP_ADDRESS",
                "IP_ALREADY_IN_USE by another NAT",
                "REGION_QUOTA_EXCEEDED for static IPs",
            ]),

            # ── Cloud DNS (channels 10-11) ──
            "dns_zone": random.choice(["gcpnet-internal", "gcpnet-prod-zone", "gcpnet-services"]),
            "dns_record_name": random.choice([
                "api.gcpnet.internal", "lb.gcpnet.prod",
                "cdn.gcpnet.internal", "vpn.gcpnet.internal",
            ]),
            "dns_record_type": random.choice(["A", "AAAA", "CNAME", "MX"]),
            "dnssec_rrsig_expiry": random.choice(["EXPIRED", "2h remaining", "30m remaining"]),
            "dnssec_ds_status": random.choice(["MISSING", "STALE", "MISMATCHED_ALGORITHM"]),
            "dnssec_error_count": random.randint(50, 500),
            "dns_change_id": f"change-{random.randint(10000, 99999)}",
            "dns_prop_time_sec": random.randint(120, 600),
            "dns_prop_sla_sec": 60,
            "dns_servers_updated": random.randint(1, 3),
            "dns_servers_total": random.randint(4, 8),

            # ── Interconnect (channels 12-13) ──
            "interconnect_name": random.choice(["gcpnet-interconnect-primary", "gcpnet-interconnect-secondary"]),
            "circuit_id": f"CIR-{random.randint(100000, 999999)}",
            "interconnect_location": random.choice(["iad-zone1-1", "dfw-zone1-1", "ams-zone1-1"]),
            "circuit_down_sec": random.randint(10, 300),
            "interconnect_bw_gbps": random.choice([10, 100]),
            "failover_status": random.choice(["ACTIVE_ON_BACKUP", "FAILOVER_IN_PROGRESS", "NO_BACKUP"]),
            "cloud_router": random.choice(["gcpnet-router-central1", "gcpnet-router-east1", "gcpnet-router-europe1"]),
            "bgp_peer_ip": f"169.254.{random.randint(0,255)}.{random.randint(1,254)}",
            "bgp_peer_asn": random.choice([16550, 64512, 64513, 65001]),
            "bgp_flap_count": random.randint(5, 30),
            "bgp_flap_window": random.randint(60, 600),
            "bgp_state": random.choice(["IDLE", "ACTIVE", "CONNECT", "OPEN_SENT"]),
            "bgp_advertised_routes": random.randint(0, 50),

            # ── CDN (channels 14-15) ──
            "cdn_backend": random.choice(["gcpnet-cdn-backend-01", "gcpnet-cdn-backend-02", "gcpnet-cdn-backend-03"]),
            "cdn_hit_ratio": round(random.uniform(15.0, 45.0), 1),
            "cdn_hit_sla": 85,
            "cdn_miss_rate": random.randint(500, 5000),
            "cdn_origin_latency_ms": random.randint(200, 2000),
            "cdn_cache_fill_pct": round(random.uniform(30.0, 60.0), 1),
            "cdn_origin_host": random.choice(["origin-central1.gcpnet.internal", "origin-east1.gcpnet.internal"]),
            "cdn_origin_status": random.choice([502, 503, 504, 0]),
            "cdn_origin_failures": random.randint(50, 500),
            "cdn_stale_pct": round(random.uniform(20.0, 80.0), 1),
            "cdn_stale_ttl_sec": random.randint(30, 300),

            # ── Load Balancer (channels 16-17) ──
            "lb_forwarding_rule": random.choice(["gcpnet-fr-https-global", "gcpnet-fr-tcp-regional", "gcpnet-fr-udp-internal"]),
            "lb_backend_service": random.choice(["gcpnet-bs-web", "gcpnet-bs-api", "gcpnet-bs-grpc"]),
            "lb_unhealthy_count": random.randint(2, 6),
            "lb_total_backends": random.randint(6, 12),
            "lb_health_check": random.choice(["hc-http-8080", "hc-https-443", "hc-tcp-3000"]),
            "lb_failed_checks": random.randint(3, 10),
            "ssl_cert_name": random.choice(["gcpnet-managed-cert-01", "gcpnet-managed-cert-02"]),
            "ssl_domain": random.choice(["api.gcpnet.example.com", "cdn.gcpnet.example.com", "*.gcpnet.example.com"]),
            "ssl_days_remaining": random.randint(-5, 3),
            "ssl_managed_status": random.choice(["FAILED_NOT_VISIBLE", "FAILED_CAA_CHECKING", "PROVISIONING"]),
            "ssl_affected_rules": random.randint(2, 8),

            # ── VPN (channels 18-19) ──
            "vpn_tunnel_name": random.choice(["gcpnet-vpn-tunnel-01", "gcpnet-vpn-tunnel-02", "gcpnet-vpn-tunnel-03"]),
            "vpn_gateway_name": random.choice(["gcpnet-vpn-gw-europe1", "gcpnet-vpn-gw-central1"]),
            "vpn_peer_ip": f"203.0.113.{random.randint(1, 254)}",
            "vpn_down_sec": random.randint(10, 300),
            "vpn_ike_version": random.choice(["IKEv2", "IKEv1"]),
            "vpn_last_handshake_sec": random.randint(60, 600),
            "ike_phase": random.choice(["1", "2"]),
            "ike_error": random.choice([
                "NO_PROPOSAL_CHOSEN",
                "AUTHENTICATION_FAILED",
                "INVALID_KE_PAYLOAD",
                "TS_UNACCEPTABLE",
            ]),
            "ike_retry_count": random.randint(3, 10),
            "ike_max_retries": 10,

            # ── Network Intelligence (channel 20) ──
            "ni_test_name": random.choice([
                "test-vpc-to-onprem", "test-central1-to-europe1",
                "test-nat-egress", "test-vpn-connectivity",
            ]),
            "ni_src_ip": f"10.{random.randint(128, 142)}.{random.randint(0, 10)}.{random.randint(1, 254)}",
            "ni_dst_ip": f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
            "ni_protocol": random.choice(["TCP:80", "TCP:443", "ICMP", "UDP:53"]),
            "ni_test_result": random.choice(["UNREACHABLE", "DROPPED", "AMBIGUOUS"]),
            "ni_hops_completed": random.randint(2, 5),
            "ni_hops_total": random.randint(6, 10),
            "ni_blocking_resource": random.choice([
                "firewall-rule/deny-all-ingress",
                "route/default-internet-gateway",
                "vpc-peering/peer-to-shared-vpc",
                "cloud-nat/gcpnet-nat-east1",
            ]),
        }


# Module-level instance for registry discovery
scenario = GCPScenario()

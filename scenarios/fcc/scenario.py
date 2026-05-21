"""FCC Communications Resilience scenario - broadband, spectrum, emergency alerting, and public safety operations."""

from __future__ import annotations

import random
from typing import Any

from scenarios.base import BaseScenario, CountdownConfig, UITheme


_CHANNELS: list[dict[str, Any]] = [
    {
        "name": "Broadband Fabric Tile Drift",
        "subsystem": "broadband_mapping",
        "section": "broadband_fabric",
        "error": "FCC-BROADBAND-FABRIC-DRIFT",
        "sensor": "fabric_reconciliation",
        "affected": ["broadband-map", "data-exchange"],
        "cascade": ["consumer-complaints", "license-manager"],
        "description": "Broadband availability fabric tiles diverging from carrier-submitted coverage claims",
        "remediation": "rebuild_broadband_fabric_tiles",
    },
    {
        "name": "Speed Claim Validation Backlog",
        "subsystem": "broadband_mapping",
        "section": "speed_validation",
        "error": "FCC-SPEED-CLAIM-BACKLOG",
        "sensor": "speed_test_validator",
        "affected": ["broadband-map", "consumer-complaints"],
        "cascade": ["data-exchange"],
        "description": "Crowdsourced and carrier-reported broadband speed evidence queue breaching SLA",
        "remediation": "scale_speed_validation_workers",
    },
    {
        "name": "Carrier Coverage Challenge Surge",
        "subsystem": "broadband_mapping",
        "section": "coverage_challenges",
        "error": "FCC-COVERAGE-CHALLENGE-SURGE",
        "sensor": "challenge_intake",
        "affected": ["broadband-map", "consumer-complaints"],
        "cascade": ["data-exchange"],
        "description": "Consumer and state broadband challenge submissions spiking above review capacity",
        "remediation": "enable_challenge_triage_mode",
    },
    {
        "name": "Licensed Band Interference",
        "subsystem": "spectrum_enforcement",
        "section": "rf_interference",
        "error": "FCC-SPECTRUM-INTERFERENCE",
        "sensor": "rf_monitor",
        "affected": ["spectrum-monitor", "license-manager"],
        "cascade": ["outage-reporting", "eas-gateway"],
        "description": "Field RF telemetry detecting interference in a licensed public safety or commercial band",
        "remediation": "dispatch_interference_investigation",
    },
    {
        "name": "Unauthorized Transmitter Detected",
        "subsystem": "spectrum_enforcement",
        "section": "transmitter_detection",
        "error": "FCC-UNAUTHORIZED-TRANSMITTER",
        "sensor": "direction_finding",
        "affected": ["spectrum-monitor"],
        "cascade": ["license-manager", "outage-reporting"],
        "description": "Direction-finding sensors identify an unlicensed transmitter on a protected frequency",
        "remediation": "open_enforcement_case",
    },
    {
        "name": "EAS CAP Signature Failure",
        "subsystem": "emergency_alerting",
        "section": "cap_validation",
        "error": "FCC-EAS-CAP-SIGNATURE-FAIL",
        "sensor": "cap_validator",
        "affected": ["eas-gateway"],
        "cascade": ["data-exchange", "consumer-complaints"],
        "description": "Emergency Alert System CAP message signature validation failing before participant fanout",
        "remediation": "rotate_eas_signing_chain",
    },
    {
        "name": "PSAP Call-Routing Failure",
        "subsystem": "network_outage",
        "section": "psap_call_routing",
        "error": "FCC-PSAP-CALL-ROUTING-FAIL",
        "sensor": "psap_call_router",
        "affected": ["outage-reporting", "eas-gateway"],
        "cascade": ["consumer-complaints", "data-exchange"],
        "description": "Selective Router failing to deliver E911 calls to the designated primary PSAP, forcing overflow to backup PSAPs and degrading dispatch availability",
        "remediation": "reroute_psap_overflow",
    },
    {
        "name": "Wireless Carrier E911 Handoff Drop",
        "subsystem": "network_outage",
        "section": "wireless_e911_handoff",
        "error": "FCC-CARRIER-HANDOFF-DROP",
        "sensor": "e911_session_tracker",
        "affected": ["outage-reporting", "spectrum-monitor"],
        "cascade": ["consumer-complaints", "eas-gateway"],
        "description": "Wireless E911 Phase II call sessions dropping during inter-sector handoff, degrading caller location continuity and triggering PSAP call-back fallback",
        "remediation": "failover_carrier_msc_trunk",
    },
    {
        "name": "ALI Location Lookup Degradation",
        "subsystem": "network_outage",
        "section": "ali_lookup",
        "error": "FCC-ALI-LOOKUP-DEGRADED",
        "sensor": "ali_resolver",
        "affected": ["data-exchange", "outage-reporting"],
        "cascade": ["consumer-complaints", "eas-gateway"],
        "description": "Automatic Location Identification lookups returning stale or imprecise records (MSAG/ALI version drift, LIS sync lag), degrading PSAP dispatch accuracy",
        "remediation": "refresh_ali_cache",
    },
    {
        "name": "Consumer Complaint Routing Loop",
        "subsystem": "consumer_protection",
        "section": "complaint_routing",
        "error": "FCC-COMPLAINT-ROUTING-LOOP",
        "sensor": "case_router",
        "affected": ["consumer-complaints"],
        "cascade": ["robocall-analytics", "data-exchange"],
        "description": "Complaint case routing repeatedly assigns the same carrier queue without resolution",
        "remediation": "reset_complaint_router_rules",
    },
    {
        "name": "Accessibility Complaint SLA Breach",
        "subsystem": "consumer_protection",
        "section": "accessibility_cases",
        "error": "FCC-ACCESSIBILITY-SLA-BREACH",
        "sensor": "sla_monitor",
        "affected": ["consumer-complaints", "data-exchange"],
        "cascade": ["license-manager"],
        "description": "Accessibility-related consumer complaints approaching response deadline without carrier action",
        "remediation": "escalate_accessibility_cases",
    },
    {
        "name": "Robocall Traceback Graph Split",
        "subsystem": "robocall_mitigation",
        "section": "traceback_graph",
        "error": "FCC-ROBOCALL-GRAPH-SPLIT",
        "sensor": "traceback_graph",
        "affected": ["robocall-analytics"],
        "cascade": ["consumer-complaints", "data-exchange"],
        "description": "Traceback analytics cannot join originating and gateway carrier legs for a campaign",
        "remediation": "rebuild_traceback_graph",
    },
    {
        "name": "STIR/SHAKEN Attestation Anomaly",
        "subsystem": "robocall_mitigation",
        "section": "call_authentication",
        "error": "FCC-STIR-SHAKEN-ANOMALY",
        "sensor": "attestation_analyzer",
        "affected": ["robocall-analytics", "consumer-complaints"],
        "cascade": ["data-exchange"],
        "description": "Call authentication signals show abnormal attestation downgrade patterns",
        "remediation": "refresh_attestation_model",
    },
    {
        "name": "ULS License Record Lock Contention",
        "subsystem": "licensing",
        "section": "uls_records",
        "error": "FCC-ULS-LOCK-CONTENTION",
        "sensor": "license_db_lock",
        "affected": ["license-manager"],
        "cascade": ["auction-platform", "data-exchange"],
        "description": "Universal Licensing System records locked during bulk update or transfer window",
        "remediation": "drain_license_update_queue",
    },
    {
        "name": "Auction Bid Round Freeze",
        "subsystem": "spectrum_auction",
        "section": "bid_round",
        "error": "FCC-AUCTION-BID-FREEZE",
        "sensor": "bid_window_monitor",
        "affected": ["auction-platform"],
        "cascade": ["license-manager", "data-exchange"],
        "description": "Spectrum auction bid window accepting bids but not publishing round results",
        "remediation": "failover_auction_round_processor",
    },
    {
        "name": "Auction Eligibility Points Mismatch",
        "subsystem": "spectrum_auction",
        "section": "eligibility_points",
        "error": "FCC-AUCTION-ELIGIBILITY-MISMATCH",
        "sensor": "eligibility_calculator",
        "affected": ["auction-platform", "license-manager"],
        "cascade": ["data-exchange"],
        "description": "Bidder eligibility points differ between the auction platform and licensing records",
        "remediation": "recompute_bidder_eligibility",
    },
    {
        "name": "Public Data Export Lag",
        "subsystem": "public_data",
        "section": "open_data_exports",
        "error": "FCC-PUBLIC-DATA-EXPORT-LAG",
        "sensor": "open_data_exporter",
        "affected": ["data-exchange"],
        "cascade": ["broadband-map", "consumer-complaints"],
        "description": "Public datasets and dashboards lag behind regulated operational systems",
        "remediation": "replay_public_data_exports",
    },
    {
        "name": "Carrier Filing Schema Drift",
        "subsystem": "public_data",
        "section": "carrier_filings",
        "error": "FCC-CARRIER-FILING-SCHEMA-DRIFT",
        "sensor": "schema_validator",
        "affected": ["data-exchange", "license-manager"],
        "cascade": ["broadband-map", "outage-reporting"],
        "description": "Carrier-submitted filings using schema revisions ahead of the ingestion pipeline",
        "remediation": "pin_carrier_schema_version",
    },
    {
        "name": "FOIA Package Generation Failure",
        "subsystem": "public_data",
        "section": "foia_processing",
        "error": "FCC-FOIA-PACKAGE-FAIL",
        "sensor": "foia_packager",
        "affected": ["data-exchange", "consumer-complaints"],
        "cascade": ["license-manager"],
        "description": "Public records package generation failing due to redaction or attachment indexing errors",
        "remediation": "restart_foia_packager",
    },
    {
        "name": "Cross-System Identity Sync Failure",
        "subsystem": "platform_identity",
        "section": "identity_sync",
        "error": "FCC-IDENTITY-SYNC-FAILURE",
        "sensor": "iam_sync",
        "affected": ["license-manager", "auction-platform", "data-exchange"],
        "cascade": ["consumer-complaints", "outage-reporting"],
        "description": "Identity and organization records failing to synchronize across FCC operational systems",
        "remediation": "resync_organization_identity",
    },
]


class FCCScenario(BaseScenario):
    """FCC communications resilience demo with 9 services and 20 fault channels."""

    @property
    def scenario_id(self) -> str:
        return "fcc"

    @property
    def scenario_icon(self) -> str:
        return "FCC"

    @property
    def scenario_name(self) -> str:
        return "FCC Communications Resilience"

    @property
    def scenario_description(self) -> str:
        return (
            "Communications-regulator operations across broadband mapping, spectrum monitoring, "
            "emergency alerting, consumer complaints, licensing, spectrum auctions, outage reporting, "
            "robocall mitigation, and public data exchange."
        )

    @property
    def namespace(self) -> str:
        return "fcc"

    @property
    def sort_order(self) -> int:
        return 10

    @property
    def raw_log_profile(self) -> dict[str, Any]:
        return {
            "service_name": "fcc-public-api",
            "user_id_prefix": "fcc-user",
            "tier_field": "submitter_type",
            "tier_values": [("consumer", 50), ("carrier", 30), ("state", 12), ("public_safety", 8)],
            "country_weights": {"US": 96, "CA": 2, "GB": 1, "MX": 1},
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "paths": [
                "/api/v1/broadband/availability/{id}",
                "/api/v1/complaints",
                "/api/v1/outages/nors",
                "/api/v1/licenses/uls/{id}",
                "/api/v1/auctions/rounds",
                "/api/v1/robocall/traceback",
                "/api/v1/public/datasets",
                "/login",
                "/health",
            ],
            "change_point_path": "/api/v1/outages/nors",
        }

    @property
    def executive_kpi_emitter_service_name(self) -> str:
        return "data-exchange"

    @property
    def executive_dashboard_intro(self) -> str:
        return (
            "**FCC communications KPIs** - broadband access, spectrum and licensing, "
            "public safety communications, and platform operations (synthetic `business.*` from `data-exchange`)."
        )

    @property
    def executive_kpi_sections(self) -> list[dict]:
        return [
            {
                "header": "**Broadband & consumers** - availability, speeds, complaints, SLA, neutrality, and robocall protection",
                "specs": [
                    ("Broadband availability (%)", "metrics.business.broadband_availability_pct"),
                    ("Median download (Mbps)", "metrics.business.speed_test_median_down_mbps"),
                    ("Complaints / min", "metrics.business.consumer_complaints_per_min"),
                    ("Complaint SLA compliance (%)", "metrics.business.complaint_sla_compliance_pct"),
                    ("Neutrality review queue", "metrics.business.net_neutrality_review_queue"),
                    ("Robocall blocks / min", "metrics.business.robocall_blocks_per_min"),
                ],
            },
            {
                "header": "**Spectrum & licensing** - occupancy, interference, licensing, auctions, success rate, and enforcement",
                "specs": [
                    ("Spectrum occupancy (%)", "metrics.business.spectrum_occupancy_pct"),
                    ("Open interference cases", "metrics.business.interference_cases_open"),
                    ("License backlog", "metrics.business.license_processing_backlog"),
                    ("Auction volume (USD/min)", "metrics.business.auction_bid_volume_usd_per_min"),
                    ("License success rate (%)", "metrics.business.license_system_success_rate_pct"),
                    ("Enforcement actions / min", "metrics.business.enforcement_actions_per_min"),
                ],
            },
            {
                "header": "**Public safety** - EAS, WEA, 911, outage reporting, restoration, and risk",
                "specs": [
                    ("EAS delivery success (%)", "metrics.business.eas_delivery_success_pct"),
                    ("WEA latency (ms)", "metrics.business.wea_delivery_latency_ms"),
                    ("PSAP 911 availability (%)", "metrics.business.psap_911_availability_pct"),
                    ("Outage reports / min", "metrics.business.outage_reports_per_min"),
                    ("Restoration ETA (min)", "metrics.business.restoration_eta_min"),
                    ("Public safety risk", "metrics.business.public_safety_risk_index_0_100"),
                ],
            },
            {
                "header": "**Operations** - API health, data lag, productivity, precision, MTTD, and MTTR",
                "specs": [
                    ("API success rate (%)", "metrics.business.api_success_rate_pct"),
                    ("Data ingest lag (sec)", "metrics.business.data_ingest_lag_sec"),
                    ("Caseworker productivity", "metrics.business.caseworker_productivity_per_hour"),
                    ("Fraud precision (%)", "metrics.business.fraud_detection_precision_pct"),
                    ("Incident MTTD (min)", "metrics.business.incident_mttd_min"),
                    ("Incident MTTR (min)", "metrics.business.incident_mttr_min"),
                ],
            },
        ]

    @property
    def executive_trend_charts(self) -> list[dict]:
        return [
            {"title": "Broadband availability", "field": "metrics.business.broadband_availability_pct", "y_label": "%"},
            {"title": "Complaint volume", "field": "metrics.business.consumer_complaints_per_min", "y_label": "complaints/min"},
            {"title": "Spectrum occupancy", "field": "metrics.business.spectrum_occupancy_pct", "y_label": "%"},
            {"title": "WEA latency", "field": "metrics.business.wea_delivery_latency_ms", "y_label": "ms"},
            {"title": "Outage reports", "field": "metrics.business.outage_reports_per_min", "y_label": "reports/min"},
            {"title": "Data ingest lag", "field": "metrics.business.data_ingest_lag_sec", "y_label": "sec"},
        ]

    @property
    def services(self) -> dict[str, dict[str, Any]]:
        return {
            "broadband-map": {"cloud_provider": "aws", "cloud_region": "us-east-1", "cloud_platform": "aws_ec2", "cloud_availability_zone": "us-east-1a", "subsystem": "broadband_mapping", "language": "python"},
            "spectrum-monitor": {"cloud_provider": "aws", "cloud_region": "us-east-1", "cloud_platform": "aws_ec2", "cloud_availability_zone": "us-east-1b", "subsystem": "spectrum_enforcement", "language": "go"},
            "eas-gateway": {"cloud_provider": "aws", "cloud_region": "us-east-1", "cloud_platform": "aws_ec2", "cloud_availability_zone": "us-east-1c", "subsystem": "emergency_alerting", "language": "java"},
            "consumer-complaints": {"cloud_provider": "gcp", "cloud_region": "us-central1", "cloud_platform": "gcp_compute_engine", "cloud_availability_zone": "us-central1-a", "subsystem": "consumer_protection", "language": "dotnet"},
            "license-manager": {"cloud_provider": "gcp", "cloud_region": "us-central1", "cloud_platform": "gcp_compute_engine", "cloud_availability_zone": "us-central1-b", "subsystem": "licensing", "language": "java"},
            "auction-platform": {"cloud_provider": "gcp", "cloud_region": "us-central1", "cloud_platform": "gcp_compute_engine", "cloud_availability_zone": "us-central1-c", "subsystem": "spectrum_auction", "language": "go"},
            "outage-reporting": {"cloud_provider": "azure", "cloud_region": "eastus", "cloud_platform": "azure_vm", "cloud_availability_zone": "eastus-1", "subsystem": "network_outage", "language": "python"},
            "robocall-analytics": {"cloud_provider": "azure", "cloud_region": "eastus", "cloud_platform": "azure_vm", "cloud_availability_zone": "eastus-2", "subsystem": "robocall_mitigation", "language": "python"},
            "data-exchange": {"cloud_provider": "azure", "cloud_region": "eastus", "cloud_platform": "azure_vm", "cloud_availability_zone": "eastus-3", "subsystem": "public_data", "language": "java"},
        }

    @property
    def channel_registry(self) -> dict[int, dict[str, Any]]:
        registry = {}
        for idx, ch in enumerate(_CHANNELS, start=1):
            registry[idx] = {
                "name": ch["name"],
                "subsystem": ch["subsystem"],
                "vehicle_section": ch["section"],
                "error_type": ch["error"],
                "sensor_type": ch["sensor"],
                "affected_services": ch["affected"],
                "cascade_services": ch["cascade"],
                "description": ch["description"],
                "investigation_notes": (
                    f"Root cause pattern: {ch['description']}. Correlate ERROR logs with carrier_id, "
                    "region, affected county, queue depth, and data ingest lag. Validate whether the "
                    "problem is isolated to the primary service or cascading through public data, licensing, "
                    "consumer protection, or emergency communications workflows. Remediation action: "
                    f"{ch['remediation']}."
                ),
                "remediation_action": ch["remediation"],
                "error_message": (
                    "[FCC] {error_type} incident={incident_id} carrier={carrier_id} state={state} "
                    "county={county} service={service_name} section={section} queue_depth={queue_depth} "
                    "latency_ms={latency_ms} affected_records={records} error=\"{error_detail}\""
                ).replace("{error_type}", ch["error"]).replace("{section}", ch["section"]),
                "stack_trace": (
                    "FCC Incident Diagnostic\n"
                    "-----------------------\n"
                    f"Error Type: {ch['error']}\n"
                    f"Subsystem:  {ch['subsystem']}\n"
                    f"Section:    {ch['section']}\n"
                    "Incident:   {incident_id}\n"
                    "Carrier:    {carrier_id}\n"
                    "Location:   {county}, {state}\n"
                    "Queue:      {queue_depth} pending records\n"
                    "Latency:    {latency_ms} ms\n"
                    "Endpoint:   {endpoint}\n"
                    f"Action:     {ch['remediation']}"
                ),
            }
        return registry

    @property
    def service_topology(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "broadband-map": [("data-exchange", "/api/v1/public/broadband/export", "POST"), ("consumer-complaints", "/api/v1/complaints/challenges", "GET")],
            "spectrum-monitor": [("license-manager", "/api/v1/licenses/frequency-owner", "GET"), ("outage-reporting", "/api/v1/outages/interference-impact", "POST")],
            "eas-gateway": [("outage-reporting", "/api/v1/outages/public-safety", "GET"), ("data-exchange", "/api/v1/public/eas-audit", "POST")],
            "consumer-complaints": [("robocall-analytics", "/api/v1/robocall/campaign-score", "POST"), ("data-exchange", "/api/v1/public/complaint-summary", "POST")],
            "license-manager": [("auction-platform", "/api/v1/auctions/eligibility", "GET"), ("data-exchange", "/api/v1/public/license-update", "POST")],
            "auction-platform": [("license-manager", "/api/v1/licenses/auction-results", "POST"), ("data-exchange", "/api/v1/public/auction-round", "POST")],
            "outage-reporting": [("eas-gateway", "/api/v1/eas/incident-context", "GET"), ("consumer-complaints", "/api/v1/complaints/outage-notice", "POST")],
            "robocall-analytics": [("consumer-complaints", "/api/v1/complaints/robocall-link", "POST"), ("data-exchange", "/api/v1/public/robocall-stats", "POST")],
            "data-exchange": [("broadband-map", "/api/v1/broadband/tile-status", "GET"), ("license-manager", "/api/v1/licenses/open-data-delta", "GET")],
        }

    @property
    def entry_endpoints(self) -> dict[str, list[tuple[str, str]]]:
        return {
            "broadband-map": [("/api/v1/broadband/tiles", "GET"), ("/api/v1/broadband/challenges", "POST")],
            "spectrum-monitor": [("/api/v1/spectrum/scans", "POST"), ("/api/v1/spectrum/interference", "GET")],
            "eas-gateway": [("/api/v1/eas/cap", "POST"), ("/api/v1/wea/audit", "GET")],
            "consumer-complaints": [("/api/v1/complaints", "POST"), ("/api/v1/complaints/status", "GET")],
            "license-manager": [("/api/v1/licenses/applications", "POST"), ("/api/v1/licenses/uls", "GET")],
            "auction-platform": [("/api/v1/auctions/bids", "POST"), ("/api/v1/auctions/rounds", "GET")],
            "outage-reporting": [("/api/v1/outages/nors", "POST"), ("/api/v1/outages/911", "GET")],
            "robocall-analytics": [("/api/v1/robocall/traceback", "POST"), ("/api/v1/robocall/stir-shaken", "GET")],
            "data-exchange": [("/api/v1/public/datasets", "GET"), ("/api/v1/foia/packages", "POST")],
        }

    @property
    def db_operations(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "broadband-map": [("UPDATE", "broadband_tiles", "UPDATE broadband_tiles SET availability_pct = ?, updated_at = NOW() WHERE tile_id = ?")],
            "spectrum-monitor": [("INSERT", "rf_events", "INSERT INTO rf_events (band, mhz, county, state, score, ts) VALUES (?, ?, ?, ?, ?, NOW())")],
            "eas-gateway": [("INSERT", "eas_audits", "INSERT INTO eas_audits (alert_id, cap_event, delivery_status, ts) VALUES (?, ?, ?, NOW())")],
            "consumer-complaints": [("UPDATE", "complaints", "UPDATE complaints SET status = ?, carrier_id = ?, updated_at = NOW() WHERE complaint_id = ?")],
            "license-manager": [("SELECT", "licenses", "SELECT license_id, callsign, frequency_mhz FROM licenses WHERE carrier_id = ?")],
            "auction-platform": [("INSERT", "auction_bids", "INSERT INTO auction_bids (auction_id, round, bidder_id, amount, ts) VALUES (?, ?, ?, ?, NOW())")],
            "outage-reporting": [("INSERT", "outage_reports", "INSERT INTO outage_reports (outage_id, carrier_id, psap_id, state, ts) VALUES (?, ?, ?, ?, NOW())")],
            "robocall-analytics": [("UPDATE", "tracebacks", "UPDATE tracebacks SET graph_status = ?, score = ? WHERE traceback_id = ?")],
            "data-exchange": [("INSERT", "public_exports", "INSERT INTO public_exports (feed_id, records, status, ts) VALUES (?, ?, ?, NOW())")],
        }

    @property
    def hosts(self) -> list[dict[str, Any]]:
        return [
            self._host("fcc-aws-host-01", "aws", "aws_ec2", "us-east-1", "us-east-1a", "i-0fcc001a"),
            self._host("fcc-gcp-host-01", "gcp", "gcp_compute_engine", "us-central1", "us-central1-a", "fcc-gcp-001"),
            self._host("fcc-azure-host-01", "azure", "azure_vm", "eastus", "eastus-1", "fcc-az-001"),
        ]

    def _host(self, name: str, provider: str, platform: str, region: str, zone: str, instance_id: str) -> dict[str, Any]:
        return {
            "host.name": name,
            "host.id": instance_id,
            "host.arch": "amd64",
            "host.type": "c6i.2xlarge" if provider == "aws" else "standard-8",
            "host.image.id": f"{provider}-linux-2026",
            "host.cpu.model.name": "Intel(R) Xeon(R) Platinum CPU",
            "host.cpu.vendor.id": "GenuineIntel",
            "host.cpu.family": "6",
            "host.cpu.model.id": "85",
            "host.cpu.stepping": "7",
            "host.cpu.cache.l2.size": 1048576,
            "host.ip": [f"10.{random.randint(20, 40)}.{random.randint(0, 5)}.{random.randint(10, 240)}"],
            "host.mac": [f"02:42:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}"],
            "os.type": "linux",
            "os.description": "Ubuntu 22.04 LTS",
            "cloud.provider": provider,
            "cloud.platform": platform,
            "cloud.region": region,
            "cloud.availability_zone": zone,
            "cloud.account.id": "fcc-communications-prod",
            "cloud.instance.id": instance_id,
            "cpu_count": 8,
            "memory_total_bytes": 32 * 1024 * 1024 * 1024,
            "disk_total_bytes": 500 * 1024 * 1024 * 1024,
        }

    @property
    def k8s_clusters(self) -> list[dict[str, Any]]:
        return [
            {"name": "fcc-eks-cluster", "provider": "aws", "platform": "aws_eks", "region": "us-east-1", "zones": ["us-east-1a", "us-east-1b", "us-east-1c"], "os_description": "Amazon Linux 2", "services": ["broadband-map", "spectrum-monitor", "eas-gateway"]},
            {"name": "fcc-gke-cluster", "provider": "gcp", "platform": "gcp_gke", "region": "us-central1", "zones": ["us-central1-a", "us-central1-b", "us-central1-c"], "os_description": "Container-Optimized OS", "services": ["consumer-complaints", "license-manager", "auction-platform"]},
            {"name": "fcc-aks-cluster", "provider": "azure", "platform": "azure_aks", "region": "eastus", "zones": ["eastus-1", "eastus-2", "eastus-3"], "os_description": "Ubuntu 22.04 LTS", "services": ["outage-reporting", "robocall-analytics", "data-exchange"]},
        ]

    @property
    def theme(self) -> UITheme:
        return UITheme(
            bg_primary="#07111f",
            bg_secondary="#101a27",
            bg_tertiary="#172536",
            accent_primary="#1fb6a6",
            accent_secondary="#f2b84b",
            text_primary="#f4f7fb",
            text_secondary="#9eb0c3",
            text_accent="#1fb6a6",
            status_nominal="#2fbf71",
            status_warning="#f2b84b",
            status_critical="#e85d5d",
            status_info="#5aa9e6",
            chaos_title="Communications Incident Simulator",
            service_label="Platform",
            channel_label="Use Case",
        )

    @property
    def countdown_config(self) -> CountdownConfig:
        return CountdownConfig(enabled=False)

    @property
    def agent_config(self) -> dict[str, Any]:
        errors = ", ".join(ch["error"] for ch in _CHANNELS)
        return {
            "id": "fcc-communications-analyst",
            "name": "FCC Communications Operations Analyst",
            "assessment_tool_name": "communications_resilience_assessment",
            "system_prompt": (
                "You are the FCC Communications Operations Analyst, an expert AI assistant for "
                "communications-regulator operations. You investigate incidents across broadband mapping, "
                "spectrum enforcement, emergency alerting, consumer complaints, licensing, auctions, outage "
                "reporting, robocall mitigation, and public data exchange. "
                "You also have deep expertise in 911 public-safety communications: Selective Router call "
                "routing to PSAPs, MSAG/ALI databases, NG911 ESInet/ESRP/LIS architecture, wireless E911 "
                "Phase II (MPC/GMLC, E2 interface), and FCC reporting frameworks (NORS for outages, DIRS "
                "for disaster events). When 911 incidents (PSAP-CALL-ROUTING-FAIL, CARRIER-HANDOFF-DROP, "
                "ALI-LOOKUP-DEGRADED) are detected, prioritize them above non-public-safety incidents and "
                "assess FCC reportability thresholds (NORS: >30 min outage and >900k user-minutes affected). "
                "Prioritize public safety impact, consumer harm, carrier accountability, and timely restoration. "
                "Search for these error signatures: "
                f"{errors}. Log messages are in body.text - NEVER search the body field alone."
            ),
        }

    @property
    def assessment_tool_config(self) -> dict[str, Any]:
        return {
            "id": "communications_resilience_assessment",
            "description": (
                "FCC communications resilience assessment. Evaluates recent errors and warnings across "
                "broadband, spectrum, emergency alerting, consumer protection, licensing, outage, robocall, "
                "and public data services. Log message field: body.text (never use 'body' alone)."
            ),
        }

    @property
    def knowledge_base_docs(self) -> list[dict[str, Any]]:
        return []

    def get_service_classes(self) -> list[type]:
        from scenarios.fcc.services.core import (
            AuctionPlatformService,
            BroadbandMapService,
            ConsumerComplaintsService,
            DataExchangeService,
            EASGatewayService,
            LicenseManagerService,
            OutageReportingService,
            RobocallAnalyticsService,
            SpectrumMonitorService,
        )

        return [
            BroadbandMapService,
            SpectrumMonitorService,
            EASGatewayService,
            ConsumerComplaintsService,
            LicenseManagerService,
            AuctionPlatformService,
            OutageReportingService,
            RobocallAnalyticsService,
            DataExchangeService,
        ]

    def get_trace_attributes(self, service_name: str, rng) -> dict:
        return {
            "fcc.case_id": f"FCC-{rng.randint(100000, 999999)}",
            "fcc.carrier_id": rng.choice(["VZ-001", "ATT-002", "TMUS-003", "COMCAST-004", "CHARTER-005", "LUMEN-006"]),
            "fcc.jurisdiction": rng.choice(["federal", "state-coordinated", "tribal", "territorial"]),
        }

    def get_fault_params(self, channel: int) -> dict[str, Any]:
        states = ["CA", "TX", "FL", "NY", "PA", "IL", "OH", "GA", "NC", "VA", "WA", "CO"]
        counties = ["Fairfax", "Cook", "Harris", "Los Angeles", "Miami-Dade", "King", "Fulton", "Wake", "Maricopa"]
        carriers = ["VZ-001", "ATT-002", "TMUS-003", "COMCAST-004", "CHARTER-005", "LUMEN-006", "DISH-007"]
        endpoints = ["/api/v1/outages/nors", "/api/v1/eas/cap", "/api/v1/broadband/tiles", "/api/v1/licenses/uls", "/api/v1/public/datasets"]
        return {
            "incident_id": f"FCC-INC-{random.randint(100000, 999999)}",
            "carrier_id": random.choice(carriers),
            "state": random.choice(states),
            "county": random.choice(counties),
            "service_name": random.choice(list(self.services.keys())),
            "queue_depth": random.randint(250, 25_000),
            "latency_ms": random.randint(800, 12_000),
            "records": random.randint(500, 2_000_000),
            "error_detail": random.choice([
                "validation pipeline exceeded retry budget",
                "carrier submission conflicts with authoritative record",
                "public safety impact confidence below threshold",
                "schema version mismatch during ingest",
                "cross-system reconciliation timed out",
            ]),
            "endpoint": random.choice(endpoints),
            "band": random.choice(["700MHz", "850MHz", "PCS", "AWS-3", "C-Band", "CBRS", "6GHz"]),
            "mhz": round(random.uniform(617.0, 7125.0), 3),
            "alert_id": f"EAS-{random.randint(10000, 99999)}",
            "cap_event": random.choice(["TOR", "FFW", "EVI", "CAE", "CEM", "RMT"]),
            "complaint_id": f"CGB-{random.randint(100000, 999999)}",
            "license_id": f"ULS-{random.randint(1000000, 9999999)}",
            "auction_id": f"AUC-{random.randint(100, 999)}",
            "bid_round": random.randint(1, 180),
            "outage_id": f"NORS-{random.randint(100000, 999999)}",
            "psap_id": f"PSAP-{random.randint(1000, 9999)}",
            "traceback_id": f"TB-{random.randint(100000, 999999)}",
            "phone_number": f"+1{random.randint(2000000000, 9999999999)}",
            "feed_id": random.choice(["broadband-data", "uls-public", "nors-summary", "consumer-complaints", "auction-results"]),
        }


scenario = FCCScenario()

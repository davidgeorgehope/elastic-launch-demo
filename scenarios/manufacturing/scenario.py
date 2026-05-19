"""Manufacturing Operations Platform scenario — discrete manufacturing OT/IT convergence.

Covers MES, SCADA/OT gateways, OEE analytics, quality, predictive maintenance, ERP integration on
Windows, raw material inventory, and a containerized shopfloor portal across AWS/GCP/Azure.
"""

from __future__ import annotations

import random
import secrets
import time
from typing import Any

from scenarios.base import BaseScenario, CountdownConfig, UITheme


class ManufacturingScenario(BaseScenario):
    """Discrete manufacturing platform with 9 systems and 20 fault channels spanning OT and IT."""

    # -- Identity ---------------------------------------------------------------

    @property
    def scenario_id(self) -> str:
        return "manufacturing"

    @property
    def scenario_icon(self) -> str:
        return "🏭"

    @property
    def scenario_name(self) -> str:
        return "Manufacturing Operations Platform"

    @property
    def scenario_description(self) -> str:
        return (
            "Multi-site discrete manufacturing with MES, SCADA/OT, OEE analytics, "
            "quality, predictive maintenance, ERP integration on Windows Server, and a "
            "containerized shopfloor portal. Designed to demonstrate OT/IT convergence, "
            "factory automation observability, and Elastic as the single pane of glass "
            "for plant operations."
        )

    @property
    def namespace(self) -> str:
        return "mfg"

    @property
    def sort_order(self) -> int:
        return 8

    @property
    def nominal_label(self) -> str:
        return "RUNNING"

    # -- Executive Dashboard ----------------------------------------------------

    @property
    def raw_log_profile(self) -> dict[str, Any]:
        return {
            "service_name": "mes-gateway",
            "user_id_prefix": "op",
            "tier_field": "line_type",
            "tier_values": [("assembly", 50), ("packaging", 30), ("qa", 20)],
            "country_weights": {"US": 30, "DE": 25, "JP": 20, "MX": 10, "CN": 10, "BR": 5},
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "paths": [
                "/api/v1/work-orders", "/api/v1/plc/status", "/api/v1/oee",
                "/api/v1/quality", "/api/v1/inventory", "/api/v1/batches",
                "/api/v1/downtime", "/health",
            ],
            "change_point_path": "/api/v1/plc/status",
        }

    @property
    def executive_kpi_emitter_service_name(self) -> str:
        return "oee-analytics"

    @property
    def executive_dashboard_intro(self) -> str:
        return (
            "**Plant operations KPIs** — production performance (OEE), quality, maintenance & "
            "reliability, and cost & operations (synthetic `business.*` from `oee-analytics`)."
        )

    @property
    def executive_kpi_sections(self) -> list[dict]:
        return [
            {
                "header": "**Production Performance** — OEE, throughput, and cycle time",
                "specs": [
                    ("Overall OEE (%)", "metrics.business.oee_overall_pct"),
                    ("Availability (%)", "metrics.business.oee_availability_pct"),
                    ("Performance (%)", "metrics.business.oee_performance_pct"),
                    ("Quality (%)", "metrics.business.oee_quality_pct"),
                    ("Throughput (units/hr)", "metrics.business.throughput_units_per_hour"),
                    ("Cycle time (sec)", "metrics.business.cycle_time_seconds"),
                ],
            },
            {
                "header": "**Quality** — yield, scrap, defects, capability",
                "specs": [
                    ("First pass yield (%)", "metrics.business.first_pass_yield_pct"),
                    ("Scrap rate (%)", "metrics.business.scrap_rate_pct"),
                    ("Defect PPM", "metrics.business.defect_ppm"),
                    ("Rework hours/shift", "metrics.business.rework_hours_per_shift"),
                    ("Process Cpk", "metrics.business.process_cpk"),
                    ("Customer complaints/day", "metrics.business.customer_complaints_per_day"),
                ],
            },
            {
                "header": "**Maintenance & Reliability** — downtime, MTBF, MTTR, PM compliance",
                "specs": [
                    ("Unplanned downtime (min/shift)", "metrics.business.unplanned_downtime_min_per_shift"),
                    ("MTBF (hours)", "metrics.business.mtbf_hours"),
                    ("MTTR (min)", "metrics.business.mttr_minutes"),
                    ("PM compliance (%)", "metrics.business.pm_compliance_pct"),
                    ("Spare parts stockout risk (%)", "metrics.business.spare_parts_stockout_risk_pct"),
                    ("Maintenance backlog", "metrics.business.maintenance_backlog_count"),
                ],
            },
            {
                "header": "**Cost & Operations** — COPQ, energy, delivery, safety",
                "specs": [
                    ("Cost of poor quality (USD/min)", "metrics.business.cost_of_poor_quality_usd_per_min"),
                    ("Energy (kWh)", "metrics.business.energy_consumption_kwh"),
                    ("Material variance (USD)", "metrics.business.material_variance_usd"),
                    ("On-time delivery (%)", "metrics.business.on_time_delivery_pct"),
                    ("Inventory turns", "metrics.business.inventory_turns"),
                    ("Recordable safety incidents", "metrics.business.recordable_safety_incidents"),
                ],
            },
        ]

    @property
    def executive_trend_charts(self) -> list[dict]:
        return [
            {"title": "Overall OEE (%)", "field": "metrics.business.oee_overall_pct", "y_label": "%"},
            {"title": "Throughput (units/hr)", "field": "metrics.business.throughput_units_per_hour", "y_label": "units/hr"},
            {"title": "First pass yield (%)", "field": "metrics.business.first_pass_yield_pct", "y_label": "%"},
            {"title": "Unplanned downtime (min)", "field": "metrics.business.unplanned_downtime_min_per_shift", "y_label": "min"},
            {"title": "Cost of poor quality (USD/min)", "field": "metrics.business.cost_of_poor_quality_usd_per_min", "y_label": "USD/min"},
            {"title": "MTBF (hours)", "field": "metrics.business.mtbf_hours", "y_label": "hours"},
        ]

    # -- Services ---------------------------------------------------------------

    @property
    def services(self) -> dict[str, dict[str, Any]]:
        return {
            "mes-controller": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1a",
                "subsystem": "mes",
                "language": "java",
            },
            "scada-gateway": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1b",
                "subsystem": "scada",
                "language": "python",
            },
            "ot-historian": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1c",
                "subsystem": "historian",
                "language": "python",
            },
            "oee-analytics": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "oee",
                "language": "python",
            },
            "quality-inspector": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-b",
                "subsystem": "quality",
                "language": "java",
            },
            "maintenance-scheduler": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "maintenance",
                "language": "go",
            },
            "erp-bridge": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "erp",
                "language": "dotnet",
            },
            "inventory-sync": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "inventory",
                "language": "java",
            },
            "shopfloor-portal": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-2",
                "subsystem": "portal",
                "language": "nodejs",
            },
        }

    # -- Channel Registry -------------------------------------------------------

    @property
    def channel_registry(self) -> dict[int, dict[str, Any]]:
        return {
            1: {
                "name": "PLC Communication Loss",
                "subsystem": "scada",
                "vehicle_section": "opcua_gateway",
                "error_type": "PLC-COMM-LOSS",
                "sensor_type": "opcua_subscription",
                "affected_services": ["scada-gateway", "mes-controller"],
                "cascade_services": ["oee-analytics", "shopfloor-portal", "ot-historian"],
                "description": "OPC-UA subscription to a critical line PLC drops; tag updates stop flowing to MES and historian",
                "investigation_notes": (
                    "Root Cause: OPC-UA secure channel failures usually indicate either certificate trust chain "
                    "issues, network segmentation changes (VLAN/firewall) between the SCADA gateway and the PLC, "
                    "or aggressive watchdog timeouts when the PLC scan rate is at capacity. Status code 0x80AC0000 "
                    "(BadSecureChannelClosed) and 0x80820000 (BadConnectionClosed) are the most common.\n"
                    "Remediation: 1) Verify network reachability: `ping {plc_host}` and `tcptraceroute {plc_host} 4840`. "
                    "2) Check the OPC-UA endpoint discovery: `opc-ua-cli discover --endpoint opc.tcp://{plc_host}:4840`. "
                    "3) Renegotiate the secure channel: `scada-admin reconnect --plc {plc_id} --renew-channel`. "
                    "4) If certs are the issue, push a fresh app instance cert: `scada-admin push-cert --plc {plc_id}`. "
                    "5) Restart the gateway subscription manager if needed: `systemctl restart scada-opcua-gateway`. "
                    "6) Confirm tag updates resume by watching `scada.tag_update_rate_per_s` return to baseline."
                ),
                "remediation_action": "reconnect_plc",
                "error_message": "[SCADA] PLC-COMM-LOSS: plc={plc_id} endpoint=opc.tcp://{plc_host}:4840 status_code={opcua_status} subscription={subscription_id} elapsed_s={comm_loss_seconds}",
                "stack_trace": (
                    "OPC-UA Secure Channel Trace\n"
                    "  Endpoint:           opc.tcp://{plc_host}:4840\n"
                    "  PLC:                {plc_id}\n"
                    "  Subscription:       {subscription_id}\n"
                    "  Last keepalive:     {comm_loss_seconds}s ago (timeout: 10s)\n"
                    "  Status code:        {opcua_status} (BadSecureChannelClosed)\n"
                    "  Affected tags:      MotorSpeed, OvenTempC, ConveyorRPM, PartsCounter\n"
                    "  Watchdog:           CHANNEL TIMEOUT — reconnect deferred\n"
                    "PLC-COMM-LOSS: {plc_id} unreachable for {comm_loss_seconds}s; MES queue blocked"
                ),
            },
            2: {
                "name": "MES Work Order Deadlock",
                "subsystem": "mes",
                "vehicle_section": "work_order_engine",
                "error_type": "MES-WORK-ORDER-DEADLOCK",
                "sensor_type": "work_order_engine",
                "affected_services": ["mes-controller"],
                "cascade_services": ["oee-analytics", "shopfloor-portal", "scada-gateway"],
                "description": "MES routing engine deadlocks; work orders stuck in IN_PROGRESS, blocking line releases",
                "investigation_notes": (
                    "Root Cause: Routing-engine deadlocks happen when concurrent work-order state transitions take "
                    "shared row locks on the same equipment-resource record in a different order than the line-release "
                    "transaction takes them, producing a cycle in the lock graph. Common after deploying a new routing "
                    "ruleset or when the changeover transaction includes a cross-line resource swap.\n"
                    "Remediation: 1) Inspect the deadlock graph: `mes-admin deadlock-report --since 5m`. "
                    "2) Identify the offending transaction and abort the lower-priority side: `mes-admin abort-tx --tx-id {tx_id}`. "
                    "3) Restart the work-order engine to clear orphan locks: `systemctl restart mes-workorder-engine`. "
                    "4) Verify queue depth recovers: `mes-admin queue-depth --line {line_id}`. "
                    "5) If recurrence: revert the routing ruleset deploy and re-test in staging."
                ),
                "remediation_action": "restart_workorder_engine",
                "error_message": "[MES] MES-WORK-ORDER-DEADLOCK: line={line_id} wo={work_order_id} tx={tx_id} queue_depth={queue_depth} stuck_for_s={stuck_seconds}",
                "stack_trace": (
                    "=== MES DEADLOCK GRAPH ===\n"
                    "Line: {line_id} | Stuck WO: {work_order_id}\n"
                    "------------------------------------------------------------------------\n"
                    "TX-ID         | OPERATION               | LOCK MODE | RESOURCE\n"
                    "------------------------------------------------------------------------\n"
                    "{tx_id}        | wo_state_transition     | EXCL_ROW  | equipment_state[{line_id}]\n"
                    "TX-OTHER-A     | line_release            | EXCL_ROW  | work_order[{work_order_id}]\n"
                    "TX-OTHER-A     | wo_state_transition     | WAIT      | equipment_state[{line_id}]\n"
                    "{tx_id}        | line_release            | WAIT      | work_order[{work_order_id}]\n"
                    "------------------------------------------------------------------------\n"
                    "MES-WORK-ORDER-DEADLOCK: cycle detected; queue_depth={queue_depth}; stuck for {stuck_seconds}s"
                ),
            },
            3: {
                "name": "Batch Genealogy Traceability Gap",
                "subsystem": "mes",
                "vehicle_section": "genealogy_engine",
                "error_type": "MES-BATCH-GENEALOGY-BREAK",
                "sensor_type": "genealogy_engine",
                "affected_services": ["mes-controller"],
                "cascade_services": ["quality-inspector", "ot-historian"],
                "description": "Batch genealogy records lose link between raw material lots and finished goods, breaking traceability for IATF 16949 / FDA 21 CFR Part 11",
                "investigation_notes": (
                    "Root Cause: Genealogy gaps appear when the consumption event for a raw-material lot is recorded "
                    "after the finished-goods batch is closed, or when a partial-substitution swap is executed without "
                    "the operator scanning the new lot. The `parent_lot` foreign key on the consumption record ends up "
                    "NULL for some operations.\n"
                    "Remediation: 1) Identify orphan operations: `mes-admin genealogy-gaps --batch {batch_id}`. "
                    "2) Reconcile from the historian event stream: `mes-admin reconstruct-genealogy --batch {batch_id} "
                    "--from-historian`. 3) Re-link orphan operations to the correct upstream lot: `mes-admin link-lot "
                    "--operation {operation_id} --lot {raw_lot_id}`. 4) Revalidate completeness: `mes-admin verify-traceability "
                    "--batch {batch_id}`. 5) File a quality deviation if the batch has already shipped, per IATF 16949 7.5.3.2.1."
                ),
                "remediation_action": "reconstruct_genealogy",
                "error_message": "[MES] MES-BATCH-GENEALOGY-BREAK: batch={batch_id} product={product_code} missing_links={missing_link_count} compliance_risk=HIGH",
                "stack_trace": (
                    "=== BATCH GENEALOGY VERIFICATION — {batch_id} ===\n"
                    "Product: {product_code} | Operations: 14 | Linked: {linked_count} | Missing: {missing_link_count}\n"
                    "------------------------------------------------------------------------\n"
                    "OPERATION   | EQUIPMENT  | RAW LOT          | LINK STATUS\n"
                    "------------------------------------------------------------------------\n"
                    "OP-010      | LINE-03-A  | LOT-RM-447821    | OK\n"
                    "OP-020      | LINE-03-A  | LOT-RM-447821    | OK\n"
                    "OP-030      | LINE-03-B  | NULL             | MISSING\n"
                    "OP-040      | LINE-03-B  | LOT-RM-{raw_lot_id}    | OK\n"
                    "OP-050      | PACK-01    | NULL             | MISSING\n"
                    "------------------------------------------------------------------------\n"
                    "MES-BATCH-GENEALOGY-BREAK: {missing_link_count} operations missing parent lot — IATF 16949 risk"
                ),
            },
            4: {
                "name": "SCADA Tag Storm",
                "subsystem": "scada",
                "vehicle_section": "tag_subscription",
                "error_type": "SCADA-TAG-STORM",
                "sensor_type": "tag_subscription",
                "affected_services": ["scada-gateway", "ot-historian"],
                "cascade_services": ["mes-controller", "oee-analytics"],
                "description": "Runaway tag-update rate floods the historian write path, exhausting buffers",
                "investigation_notes": (
                    "Root Cause: Tag storms typically come from a sensor stuck in fast-change mode (e.g., a dead-band "
                    "value of 0 on a noisy signal) or from a PLC firmware update that reset the publishing interval to "
                    "the minimum allowed by the OPC-UA server. The downstream historian buffer fills faster than the "
                    "compaction job can drain it.\n"
                    "Remediation: 1) Identify offenders: `scada-admin top-publishers --window 60s`. "
                    "2) Apply a temporary dead-band: `scada-admin set-deadband --tag {tag_name} --pct 0.5`. "
                    "3) Reduce publishing rate: `scada-admin set-publish-interval --subscription {subscription_id} --ms 1000`. "
                    "4) Drain the historian buffer: `historian-admin flush-buffer --priority high`. "
                    "5) Open a biomed/maintenance ticket if a sensor is genuinely failing (constant noise above process limits)."
                ),
                "remediation_action": "throttle_subscription",
                "error_message": "[SCADA] SCADA-TAG-STORM: subscription={subscription_id} rate={tag_rate}/s baseline=1200/s tag={tag_name} affected_plcs={affected_plcs}",
                "stack_trace": (
                    "=== SCADA TAG PUBLISH RATE ANOMALY ===\n"
                    "Subscription: {subscription_id} | Window: 60s\n"
                    "------------------------------------------------------------------------\n"
                    "TAG NAME             | RATE/s   | BASELINE | RATIO    | DEADBAND\n"
                    "------------------------------------------------------------------------\n"
                    "{tag_name}            | {tag_rate}    | 12       | {tag_rate}x      | 0.0\n"
                    "MotorSpeed            | 8        | 8        | 1.0x     | 0.5\n"
                    "OvenTempC             | 3        | 3        | 1.0x     | 0.5\n"
                    "------------------------------------------------------------------------\n"
                    "SCADA-TAG-STORM: aggregate rate {tag_rate}/s exceeds historian buffer drain rate; backpressure imminent"
                ),
            },
            5: {
                "name": "OT Historian Backpressure",
                "subsystem": "historian",
                "vehicle_section": "write_pipeline",
                "error_type": "OT-HISTORIAN-BACKPRESSURE",
                "sensor_type": "write_pipeline",
                "affected_services": ["ot-historian"],
                "cascade_services": ["scada-gateway", "oee-analytics"],
                "description": "Historian write lag exceeds threshold; risks dropping OT tag data on the floor",
                "investigation_notes": (
                    "Root Cause: Backpressure occurs when the disk-write throughput on the historian archive volume "
                    "falls below the incoming tag rate — usually due to a stuck compaction job, a snapshot operation "
                    "blocking the write path, or a degraded RAID volume. Persistent lag risks the in-memory buffer "
                    "cycling out un-archived points.\n"
                    "Remediation: 1) Check disk I/O: `iostat -x 1 5` on `mfg-historian-host`. "
                    "2) Check compaction job status: `historian-admin compaction-status`. "
                    "3) Pause non-essential snapshots: `historian-admin pause-snapshot --duration 15m`. "
                    "4) Force a buffer flush to a secondary volume if available: `historian-admin failover-write --target AR-SECONDARY`. "
                    "5) Open an infrastructure ticket if the disk SMART status shows degraded."
                ),
                "remediation_action": "drain_historian_buffer",
                "error_message": "[HIST] OT-HISTORIAN-BACKPRESSURE: archive={archive_id} buffer_depth={buffer_depth} write_lag_s={write_lag_s} threshold=10s",
                "stack_trace": (
                    "=== HISTORIAN WRITE PIPELINE STATUS ===\n"
                    "Archive: {archive_id} | Buffer: {buffer_depth}/50000 (high watermark)\n"
                    "------------------------------------------------------------------------\n"
                    "STAGE              | STATUS    | LAG (s)  | THROUGHPUT\n"
                    "------------------------------------------------------------------------\n"
                    "ingest_queue        | OK        | 0.1      | 4200 pts/s\n"
                    "buffer_to_archive   | DEGRADED  | {write_lag_s}      | 350 pts/s\n"
                    "compaction          | STALLED   | --       | 0 pts/s\n"
                    "------------------------------------------------------------------------\n"
                    "OT-HISTORIAN-BACKPRESSURE: write lag {write_lag_s}s; buffer at {buffer_depth}/50000"
                ),
            },
            6: {
                "name": "OT Protocol Drift",
                "subsystem": "scada",
                "vehicle_section": "protocol_parser",
                "error_type": "PROTOCOL-DRIFT",
                "sensor_type": "protocol_parser",
                "affected_services": ["scada-gateway"],
                "cascade_services": ["mes-controller", "ot-historian"],
                "description": "Modbus/EtherNet-IP frame parse failures after a PLC firmware drift introduces a non-standard register layout",
                "investigation_notes": (
                    "Root Cause: After a PLC firmware update, Modbus register maps (function codes 03/04/16) or "
                    "EtherNet-IP CIP class objects can shift offsets, causing the gateway parser to misalign data words. "
                    "The result is plausibly-shaped values that pass type checks but represent the wrong physical quantity.\n"
                    "Remediation: 1) Compare current vs. expected register map: `scada-admin diff-regmap --plc {plc_id} "
                    "--baseline {firmware_baseline}`. 2) Reload the corrected register-map config: `scada-admin reload-regmap "
                    "--plc {plc_id} --version {firmware_version}`. 3) Validate sample reads against the engineering "
                    "reference: `scada-admin read-sample --plc {plc_id} --tag MotorSpeed`. 4) If firmware was unauthorized, "
                    "open an OT change-control ticket to roll back to {firmware_baseline}. "
                    "5) Add a parser-version assertion to CI on the SCADA config repo."
                ),
                "remediation_action": "reload_regmap",
                "error_message": "[SCADA] PROTOCOL-DRIFT: plc={plc_id} protocol={protocol} firmware_current={firmware_version} expected={firmware_baseline} parse_failures={parse_failure_count}",
                "stack_trace": (
                    "=== PROTOCOL PARSER DIAGNOSTIC — {plc_id} ===\n"
                    "Protocol: {protocol} | Firmware: {firmware_version} (baseline: {firmware_baseline})\n"
                    "------------------------------------------------------------------------\n"
                    "FN CODE   | EXPECTED OFFSET | ACTUAL OFFSET | TAG               | STATUS\n"
                    "------------------------------------------------------------------------\n"
                    "FC-03     | 40001           | 40001         | MotorSpeed         | OK\n"
                    "FC-03     | 40009           | 40012         | OvenTempC          | DRIFT (+3)\n"
                    "FC-04     | 30001           | 30005         | PressurePsi        | DRIFT (+4)\n"
                    "FC-16     | 41001           | 41001         | SetpointWrite      | OK\n"
                    "------------------------------------------------------------------------\n"
                    "PROTOCOL-DRIFT: {parse_failure_count} parse failures in 60s on {plc_id}"
                ),
            },
            7: {
                "name": "OPC-UA Certificate Expiry",
                "subsystem": "scada",
                "vehicle_section": "secure_channel",
                "error_type": "OPC-UA-CERT-EXPIRY",
                "sensor_type": "x509_validator",
                "affected_services": ["scada-gateway"],
                "cascade_services": ["mes-controller", "ot-historian", "shopfloor-portal"],
                "description": "TLS certificate between the OPC-UA gateway and aggregation server expired; secure channel rejected",
                "investigation_notes": (
                    "Root Cause: OPC-UA app instance certificates have a hard expiry; once the `notAfter` date passes, "
                    "the secure channel handshake is rejected by the server with status 0x80120000 (BadCertificateInvalid) "
                    "or 0x80130000 (BadCertificateTimeInvalid). Auto-renewal jobs that depend on the cert still being "
                    "valid for handshake will not renew themselves.\n"
                    "Remediation: 1) Check expiry: `openssl x509 -in /etc/scada/certs/app-instance.crt -noout -dates`. "
                    "2) Issue a fresh certificate via the OT PKI: `pki-cli issue --profile opcua-app-instance "
                    "--cn scada-gateway-{plc_id}`. 3) Push the new cert to the gateway and trust list: "
                    "`scada-admin install-cert --cert /tmp/new.crt`. 4) Also push to PLC trust list (out-of-band, "
                    "via the engineering workstation). 5) Renegotiate channels: `scada-admin reconnect --all`. "
                    "6) Add a 30-day expiry alert via Elastic Watcher."
                ),
                "remediation_action": "renew_opcua_cert",
                "error_message": "[SCADA] OPC-UA-CERT-EXPIRY: subject={cert_subject} expired_days_ago={cert_expired_days} thumbprint={cert_thumbprint} affected_plcs={affected_plcs}",
                "stack_trace": (
                    "=== OPC-UA CERTIFICATE STATUS ===\n"
                    "Subject:      {cert_subject}\n"
                    "Issuer:       CN=Manufacturing OT Root CA\n"
                    "NotBefore:    2024-08-15 00:00:00 UTC\n"
                    "NotAfter:     {cert_expiry_date} (expired {cert_expired_days} days ago)\n"
                    "Thumbprint:   {cert_thumbprint}\n"
                    "------------------------------------------------------------------------\n"
                    "Handshake:    REJECTED — status 0x80130000 (BadCertificateTimeInvalid)\n"
                    "Affected:     {affected_plcs}\n"
                    "OPC-UA-CERT-EXPIRY: secure channel cannot be established"
                ),
            },
            8: {
                "name": "OEE Availability Drop",
                "subsystem": "oee",
                "vehicle_section": "availability_calc",
                "error_type": "OEE-AVAILABILITY-DROP",
                "sensor_type": "availability_calc",
                "affected_services": ["oee-analytics"],
                "cascade_services": ["mes-controller", "shopfloor-portal"],
                "description": "Calculated OEE for a critical line falls below 75%; production guidance at risk",
                "investigation_notes": (
                    "Root Cause: An OEE availability drop is the *symptom* — the underlying cause is upstream "
                    "(unplanned downtime, micro-stops, slow cycles). Always correlate the drop window with maintenance "
                    "events, MES equipment-state transitions, and SCADA tag-quality changes for the same line.\n"
                    "Remediation: 1) Pull the equipment-state timeline: `oee-admin timeline --line {line_id} --window 60m`. "
                    "2) Cross-reference with MES work-order status: `mes-admin status --line {line_id}`. "
                    "3) Check for active maintenance: `cmms-admin active-mwo --line {line_id}`. "
                    "4) Recompute OEE with corrected planned-downtime exclusions: `oee-admin recompute --line {line_id} "
                    "--exclude-planned`. 5) Engage the line lead and shift supervisor before reporting upward — the "
                    "metric needs human context."
                ),
                "remediation_action": "recompute_oee",
                "error_message": "[OEE] OEE-AVAILABILITY-DROP: line={line_id} availability={availability_pct}% threshold=75% downtime_min={downtime_minutes} target_oee={target_oee}%",
                "stack_trace": (
                    "=== OEE AVAILABILITY DROP — {line_id} ===\n"
                    "Window: 60 minutes | Calculated: {availability_pct}% | Threshold: 75%\n"
                    "------------------------------------------------------------------------\n"
                    "INTERVAL    | STATE       | DURATION (s)  | NOTES\n"
                    "------------------------------------------------------------------------\n"
                    "00:00–02:14 | RUNNING     | 134           | nominal\n"
                    "02:14–08:30 | UNPLANNED   | {downtime_minutes}m         | trigger event\n"
                    "08:30–18:00 | RUNNING     | 570           | recovered\n"
                    "18:00–22:45 | MICROSTOP   | 285           | <2min stops\n"
                    "------------------------------------------------------------------------\n"
                    "OEE-AVAILABILITY-DROP: target {target_oee}%, actual {availability_pct}% — investigation required"
                ),
            },
            9: {
                "name": "SPC Out-of-Control Process",
                "subsystem": "quality",
                "vehicle_section": "spc_engine",
                "error_type": "SPC-OUT-OF-CONTROL",
                "sensor_type": "spc_engine",
                "affected_services": ["quality-inspector"],
                "cascade_services": ["mes-controller", "oee-analytics"],
                "description": "Process variation exceeds Cpk threshold on a critical-to-quality (CTQ) characteristic",
                "investigation_notes": (
                    "Root Cause: An out-of-control signal (Western Electric / Nelson rules) means the process mean "
                    "or variance has shifted. Common causes: tooling wear, fixture loosening, raw-material lot change, "
                    "or a temperature/humidity excursion in the work cell. A rule-2 (9 points on one side of mean) is "
                    "more diagnostic than a rule-1 (single point beyond 3σ).\n"
                    "Remediation: 1) Pull the SPC chart: `qc-admin spc-chart --characteristic {characteristic} --window 8h`. "
                    "2) Identify the rule fired and the timestamp. 3) Cross-reference with raw-material lot changes "
                    "(`mes-admin lot-history --line {line_id}`) and operator/tooling changes. "
                    "4) Pause auto-release and shift to 100% inspection until the cause is found and corrected: "
                    "`qc-admin set-inspection-mode --line {line_id} --mode FULL`. 5) Document a CAPA per IATF 16949."
                ),
                "remediation_action": "tighten_inspection",
                "error_message": "[QC] SPC-OUT-OF-CONTROL: characteristic={characteristic} rule={spc_rule} cpk={cpk} target_cpk=1.33 line={line_id}",
                "stack_trace": (
                    "=== SPC CONTROL CHART — {characteristic} ===\n"
                    "Line: {line_id} | Sample size: 30 | Cpk: {cpk} | Target: 1.33\n"
                    "------------------------------------------------------------------------\n"
                    "RULE FIRED: {spc_rule}\n"
                    "  Western Electric Rule 1: 1 point beyond 3σ\n"
                    "  Western Electric Rule 2: 9 consecutive points on one side of mean\n"
                    "  Nelson Rule 5: 2 of 3 consecutive points beyond 2σ on same side\n"
                    "------------------------------------------------------------------------\n"
                    "SAMPLE  | VALUE   | STATUS\n"
                    "------------------------------------------------------------------------\n"
                    "S-028   | 49.85   | within ±1σ\n"
                    "S-029   | 51.12   | beyond +2σ\n"
                    "S-030   | 51.48   | beyond +3σ — RULE 1 FIRED\n"
                    "------------------------------------------------------------------------\n"
                    "SPC-OUT-OF-CONTROL: process shift detected on {characteristic}"
                ),
            },
            10: {
                "name": "Vision Inspection Failure",
                "subsystem": "quality",
                "vehicle_section": "vision_pipeline",
                "error_type": "VISION-INSPECT-FAIL",
                "sensor_type": "vision_pipeline",
                "affected_services": ["quality-inspector"],
                "cascade_services": ["mes-controller", "oee-analytics"],
                "description": "Vision system camera or inference pipeline failure; defects flowing through unchecked",
                "investigation_notes": (
                    "Root Cause: Vision pipeline failures fall into three buckets: (1) hardware (camera trigger lost, "
                    "lighting drifting, lens fouled), (2) inference (model returns low confidence on every frame), "
                    "(3) network (frames arrive late or out of order). The first sign is usually a confidence-score "
                    "histogram skewing low for an entire shift.\n"
                    "Remediation: 1) Visual inspection of camera, lens, lighting at station {station_id}. "
                    "2) Run the calibration target: `vision-cli calibrate --station {station_id}`. "
                    "3) Check inference container health: `kubectl describe pod -n vision vision-inference-*`. "
                    "4) Reload the model: `vision-cli reload-model --station {station_id} --model {model_version}`. "
                    "5) If the issue persists, fall back to manual inspection and tag the lot for review per quality plan."
                ),
                "remediation_action": "reload_vision_model",
                "error_message": "[QC] VISION-INSPECT-FAIL: station={station_id} model={model_version} confidence_avg={confidence_avg} frames_dropped={frames_dropped}",
                "stack_trace": (
                    "=== VISION INSPECTION DIAGNOSTIC — {station_id} ===\n"
                    "Model: {model_version} | Window: 5 min\n"
                    "------------------------------------------------------------------------\n"
                    "STAGE             | STATUS    | METRIC\n"
                    "------------------------------------------------------------------------\n"
                    "camera_trigger     | OK        | 220 fps\n"
                    "frame_capture      | DEGRADED  | {frames_dropped} dropped\n"
                    "preprocess         | OK        | mean 8ms\n"
                    "inference          | DEGRADED  | confidence_avg={confidence_avg}\n"
                    "postprocess        | OK        | mean 3ms\n"
                    "------------------------------------------------------------------------\n"
                    "VISION-INSPECT-FAIL: pipeline degraded — defects may be passing through"
                ),
            },
            11: {
                "name": "CMMS Work Order Backlog",
                "subsystem": "maintenance",
                "vehicle_section": "cmms_scheduler",
                "error_type": "CMMS-WORK-ORDER-BACKLOG",
                "sensor_type": "cmms_scheduler",
                "affected_services": ["maintenance-scheduler"],
                "cascade_services": ["mes-controller", "oee-analytics"],
                "description": "Preventive maintenance backlog growing across multiple critical assets; MTBF risk",
                "investigation_notes": (
                    "Root Cause: PM backlogs grow when scheduling priority is dominated by reactive (corrective) work, "
                    "when craft labor is short, or when a parts shortage blocks a critical PM. Backlogs over 90 days for "
                    "Class A assets correlate strongly with future unplanned downtime.\n"
                    "Remediation: 1) Pull backlog by criticality: `cmms-admin backlog --asset-class A --overdue-days 30`. "
                    "2) Reprioritize and approve overtime if MTBF is dropping. "
                    "3) Confirm parts availability: `cmms-admin parts-status --asset {asset_id}`. "
                    "4) Re-balance the schedule: `cmms-admin rebalance-schedule --week-of {week}`. "
                    "5) Escalate to maintenance manager if Class A backlog exceeds policy threshold."
                ),
                "remediation_action": "rebalance_pm_schedule",
                "error_message": "[CMMS] CMMS-WORK-ORDER-BACKLOG: overdue={overdue_count} class_a_overdue={class_a_overdue} oldest_days={oldest_days}",
                "stack_trace": (
                    "=== CMMS BACKLOG REPORT ===\n"
                    "Total overdue: {overdue_count} | Class A overdue: {class_a_overdue} | Oldest: {oldest_days}d\n"
                    "------------------------------------------------------------------------\n"
                    "ASSET         | CLASS | TYPE       | OVERDUE (d)  | LAST PM\n"
                    "------------------------------------------------------------------------\n"
                    "MTR-CONV-01    | A     | preventive | {oldest_days}            | --\n"
                    "SPN-MILL-04    | A     | preventive | 45           | 2026-01-14\n"
                    "PMP-COOL-02    | B     | preventive | 22           | 2026-02-01\n"
                    "CMP-AIR-01     | A     | predictive | 18           | 2026-02-08\n"
                    "------------------------------------------------------------------------\n"
                    "CMMS-WORK-ORDER-BACKLOG: PM compliance trending down; MTBF risk increasing"
                ),
            },
            12: {
                "name": "Predictive Maintenance Anomaly",
                "subsystem": "maintenance",
                "vehicle_section": "predictive_engine",
                "error_type": "PREDICTIVE-MAINT-ANOMALY",
                "sensor_type": "vibration_sensor",
                "affected_services": ["maintenance-scheduler"],
                "cascade_services": ["mes-controller", "scada-gateway"],
                "description": "Vibration / thermal anomaly on a critical asset; remaining useful life estimate dropped",
                "investigation_notes": (
                    "Root Cause: Vibration RMS climbing above ISO 10816 zone B for a Class A motor or spindle is an "
                    "early warning of bearing wear, misalignment, or unbalance. Thermal deltas above 8°C between "
                    "matched bearings are an early warning of inadequate lubrication or imminent failure.\n"
                    "Remediation: 1) Pull the trend: `cmms-admin signal-trend --asset {asset_id} --sensor vibration_rms_mm_s`. "
                    "2) Schedule a precision alignment check next available window. "
                    "3) Lubricate per the manufacturer's spec if not already done in the last cycle. "
                    "4) Order spare bearing assembly to local stock if not already on hand. "
                    "5) If RMS exceeds zone C (per ISO 10816), schedule a planned shutdown for the next changeover, "
                    "do NOT wait for unplanned failure."
                ),
                "remediation_action": "schedule_predictive_intervention",
                "error_message": "[CMMS] PREDICTIVE-MAINT-ANOMALY: asset={asset_id} sensor={sensor_type} value={sensor_value} rul_days={rul_days} confidence={ml_confidence}",
                "stack_trace": (
                    "=== PREDICTIVE MAINTENANCE — {asset_id} ===\n"
                    "Sensor: {sensor_type} | Current: {sensor_value} | ISO 10816 Zone: C\n"
                    "------------------------------------------------------------------------\n"
                    "TIME (h ago) | VALUE   | TREND\n"
                    "------------------------------------------------------------------------\n"
                    "168          | 1.8     | ↑ slow\n"
                    "72           | 2.4     | ↑ slow\n"
                    "24           | 4.1     | ↑ accelerating\n"
                    "1            | {sensor_value}   | ↑ accelerating\n"
                    "------------------------------------------------------------------------\n"
                    "Remaining Useful Life: {rul_days} days (ML confidence: {ml_confidence})\n"
                    "PREDICTIVE-MAINT-ANOMALY: schedule intervention before next changeover"
                ),
            },
            13: {
                "name": "OEE Analytics Container OOM",
                "subsystem": "oee",
                "vehicle_section": "k8s_pod",
                "error_type": "ANALYTICS-CONTAINER-OOM",
                "sensor_type": "k8s_pod",
                "affected_services": ["oee-analytics"],
                "cascade_services": ["mes-controller", "shopfloor-portal"],
                "description": "OEE analytics k8s pod OOM-killed when caching unprocessed events during an upstream slowdown",
                "investigation_notes": (
                    "Root Cause: When the SCADA / MES upstream slows or backlogs, the OEE analytics service buffers "
                    "incoming events. If the per-pod memory limit is below the buffer high-watermark, the kubelet kills "
                    "the pod with OOMKilled (exit 137). Because the cached state is lost, the next pod recomputes from "
                    "scratch — producing a saw-tooth OEE pattern that's misleading to operators.\n"
                    "Remediation: 1) Inspect the kill: `kubectl describe pod -n mfg oee-analytics-* | grep -A 5 'Last State'`. "
                    "2) Right-size the memory request/limit: `kubectl set resources deploy/oee-analytics -n mfg "
                    "--limits=memory={new_mem_limit}`. 3) Reduce buffer high-watermark in the service config and "
                    "redeploy. 4) Add a memory pressure HPA. 5) Add a Watcher rule for repeated OOMKills "
                    "on this deployment."
                ),
                "remediation_action": "resize_pod_memory",
                "error_message": "[OEE-K8S] ANALYTICS-CONTAINER-OOM: pod={pod_name} container={container_name} restarts={restart_count} mem_limit={mem_limit_mb}MB last_exit_code=137",
                "stack_trace": (
                    "=== KUBERNETES POD STATE — {pod_name} ===\n"
                    "Namespace: mfg | Container: {container_name}\n"
                    "------------------------------------------------------------------------\n"
                    "Last State:        Terminated\n"
                    "  Reason:          OOMKilled\n"
                    "  Exit Code:       137\n"
                    "  Started:         2026-05-06T14:22:11Z\n"
                    "  Finished:        2026-05-06T14:38:42Z\n"
                    "Memory Limit:      {mem_limit_mb}Mi\n"
                    "Memory Peak:       {mem_peak_mb}Mi (last sample before kill)\n"
                    "Restart Count:     {restart_count}\n"
                    "------------------------------------------------------------------------\n"
                    "ANALYTICS-CONTAINER-OOM: pod {pod_name} OOMKilled — saw-tooth OEE pattern likely"
                ),
            },
            14: {
                "name": "ERP Windows Service Crash",
                "subsystem": "erp",
                "vehicle_section": "windows_service",
                "error_type": "ERP-WIN-SERVICE-CRASH",
                "sensor_type": "windows_event_log",
                "affected_services": ["erp-bridge"],
                "cascade_services": ["mes-controller", "inventory-sync"],
                "description": "Windows service on the ERP bridge stopped unexpectedly; SAP IDoc transmission halted",
                "investigation_notes": (
                    "Root Cause: A Windows service (e.g., SAPHostControl) terminating unexpectedly emits Event ID 7031 "
                    "(Service Control Manager) in the System channel. Common causes: a Windows Update reboot during a "
                    "live IDoc batch, a memory leak in a long-running RFC connection, or an expired domain service "
                    "account credential.\n"
                    "Remediation: 1) Pull the System event log: `Get-WinEvent -LogName System -FilterHashtable "
                    "@{ID=7031,7034} -MaxEvents 50` on `mfg-sap-bridge-01`. 2) Inspect the service account: "
                    "`sc.exe qc {win_service_name}`. 3) Restart the service: `sc.exe start {win_service_name}`. "
                    "4) If credentials expired, rotate via the AD service-account workflow. "
                    "5) Replay the IDoc backlog: `sap-admin replay-idoc --since {failure_time}`. "
                    "6) Add a Watcher on Windows event log channel `System` for event ID 7031 / 7034 on this host."
                ),
                "remediation_action": "restart_windows_service",
                "error_message": "[ERP-WIN] ERP-WIN-SERVICE-CRASH: host=mfg-sap-bridge-01 service={win_service_name} event_id=7031 idoc_backlog={idoc_backlog} elapsed_min={elapsed_min}",
                "stack_trace": (
                    "=== WINDOWS EVENT LOG — System ===\n"
                    "Source:           Service Control Manager\n"
                    "Event ID:         7031\n"
                    "Level:            Error\n"
                    "Computer:         mfg-sap-bridge-01\n"
                    "Channel:          System\n"
                    "------------------------------------------------------------------------\n"
                    "The {win_service_name} service terminated unexpectedly. It has done this {crash_count} time(s).\n"
                    "The following corrective action will be taken in 60000 milliseconds: Restart the service.\n"
                    "------------------------------------------------------------------------\n"
                    "Related Event ID 7034: The {win_service_name} service terminated unexpectedly.\n"
                    "Related Event ID 7036: The {win_service_name} service entered the stopped state.\n"
                    "ERP-WIN-SERVICE-CRASH: IDoc backlog={idoc_backlog}; SAP RFC unavailable for {elapsed_min}m"
                ),
            },
            15: {
                "name": "Raw Material Shortage",
                "subsystem": "inventory",
                "vehicle_section": "wms_inventory",
                "error_type": "RAW-MATERIAL-SHORTAGE",
                "sensor_type": "wms_inventory",
                "affected_services": ["inventory-sync"],
                "cascade_services": ["mes-controller", "oee-analytics"],
                "description": "Raw material on-hand fell below reorder point; line scheduled to starve in N hours",
                "investigation_notes": (
                    "Root Cause: A reorder-point breach can come from a short PO from the supplier, a higher-than-forecast "
                    "consumption rate due to scrap, or a delayed receipt at the dock. The MES forward-look projection is "
                    "the most accurate predictor of when the line will starve.\n"
                    "Remediation: 1) Confirm the on-hand vs. system count: `wms-admin physical-vs-system --material {material_code}`. "
                    "2) Expedite an open PO: `erp-admin expedite-po --po {po_number}`. "
                    "3) If no open PO, issue an emergency PO: `erp-admin issue-po --material {material_code} --qty {emergency_qty} "
                    "--priority CRITICAL`. 4) Check substitute lots: `mes-admin substitute-options --material {material_code}`. "
                    "5) Notify production planning to reschedule affected work orders. 6) Open a supplier scorecard issue."
                ),
                "remediation_action": "expedite_po",
                "error_message": "[WMS] RAW-MATERIAL-SHORTAGE: material={material_code} on_hand={on_hand} reorder_point={reorder_point} hours_to_starve={hours_to_starve}",
                "stack_trace": (
                    "=== INVENTORY REORDER ALERT — {material_code} ===\n"
                    "On-hand: {on_hand} | Reorder Point: {reorder_point} | Safety Stock: {safety_stock}\n"
                    "------------------------------------------------------------------------\n"
                    "Open POs:\n"
                    "  PO {po_number} | qty={po_quantity} | supplier=SUP-{supplier_id} | ETA={po_eta}\n"
                    "Forward consumption (next 8h): est {forward_consumption} units\n"
                    "Affected work orders: {affected_wo_count}\n"
                    "------------------------------------------------------------------------\n"
                    "RAW-MATERIAL-SHORTAGE: line will starve in {hours_to_starve}h without expedite"
                ),
            },
            16: {
                "name": "Shopfloor Portal Container Crashloop",
                "subsystem": "portal",
                "vehicle_section": "k8s_deployment",
                "error_type": "PORTAL-CONTAINER-CRASHLOOP",
                "sensor_type": "k8s_pod",
                "affected_services": ["shopfloor-portal"],
                "cascade_services": ["mes-controller"],
                "description": "Operator portal Docker container in CrashLoopBackOff after a bad image push; auto-rollback eligible",
                "investigation_notes": (
                    "Root Cause: A container that exits non-zero on startup multiple times in a short window enters "
                    "CrashLoopBackOff. The most common manufacturing-floor cause is a bad image push (missing config "
                    "map, broken migration on the embedded SQLite, or a Node.js dependency mismatch from a hot-fix build). "
                    "Auto-rollback to the prior image tag is safe when the previous tag was healthy in production.\n"
                    "Remediation (auto-remediate eligible): 1) Confirm the prior image was healthy: "
                    "`kubectl rollout history deploy/shopfloor-portal -n mfg`. 2) Roll back: `kubectl rollout "
                    "undo deploy/shopfloor-portal -n mfg`. 3) Verify operator kiosks recover within 60s. "
                    "4) File a build issue against {image_tag} for the dev team to investigate."
                ),
                "remediation_action": "rollback_container_image",
                "error_message": "[PORTAL-K8S] PORTAL-CONTAINER-CRASHLOOP: pod={pod_name} image={image_tag} restarts={restart_count} reason=CrashLoopBackOff exit_code={exit_code}",
                "stack_trace": (
                    "=== KUBERNETES DEPLOYMENT — shopfloor-portal ===\n"
                    "Namespace: mfg | Replicas: 3 (desired) / 0 (ready)\n"
                    "------------------------------------------------------------------------\n"
                    "POD                              | STATUS              | RESTARTS  | IMAGE\n"
                    "------------------------------------------------------------------------\n"
                    "{pod_name}                       | CrashLoopBackOff    | {restart_count}        | {image_tag}\n"
                    "shopfloor-portal-7c8d9f4b6-aa1bb | CrashLoopBackOff    | {restart_count}        | {image_tag}\n"
                    "shopfloor-portal-7c8d9f4b6-cc2dd | CrashLoopBackOff    | {restart_count}        | {image_tag}\n"
                    "------------------------------------------------------------------------\n"
                    "Last State: Terminated | Exit Code: {exit_code} | Reason: Error\n"
                    "PORTAL-CONTAINER-CRASHLOOP: rollback to prior image tag eligible"
                ),
            },
            17: {
                "name": "Inventory Sync Batch Failure",
                "subsystem": "inventory",
                "vehicle_section": "batch_sync",
                "error_type": "INVENTORY-SYNC-BATCH-FAIL",
                "sensor_type": "batch_sync",
                "affected_services": ["inventory-sync"],
                "cascade_services": ["erp-bridge"],
                "description": "Hourly inventory delta batch from WMS to ERP failed; auto-retry eligible",
                "investigation_notes": (
                    "Root Cause: Transient batch failures in the WMS→ERP path are usually idempotent network or "
                    "RFC-session timeouts. The auto-retry job is safe to invoke when the failure mode is "
                    "`SOCKET_TIMEOUT` or `RFC_HANDLE_INVALID`.\n"
                    "Remediation (auto-remediate eligible): 1) Identify the failed batch: `wms-admin batch-status "
                    "--last 1h --status FAILED`. 2) Retry: `wms-admin retry-batch --batch {batch_id}`. "
                    "3) Confirm reconciliation: `wms-admin reconcile --since {failure_time}`."
                ),
                "remediation_action": "retry_inventory_batch",
                "error_message": "[WMS] INVENTORY-SYNC-BATCH-FAIL: batch={batch_id} records={record_count} failure_mode={failure_mode} retry_count={retry_count}",
                "stack_trace": (
                    "=== INVENTORY SYNC BATCH — {batch_id} ===\n"
                    "Records: {record_count} | Started: 2026-05-06T14:00:00Z\n"
                    "------------------------------------------------------------------------\n"
                    "STAGE         | STATUS    | DURATION (s)\n"
                    "------------------------------------------------------------------------\n"
                    "extract        | OK        | 12\n"
                    "transform      | OK        | 8\n"
                    "rfc_call       | FAILED    | 30 — {failure_mode}\n"
                    "------------------------------------------------------------------------\n"
                    "INVENTORY-SYNC-BATCH-FAIL: idempotent failure; retry eligible (retry {retry_count}/3)"
                ),
            },
            18: {
                "name": "MES Queue Overflow",
                "subsystem": "mes",
                "vehicle_section": "work_order_queue",
                "error_type": "MES-QUEUE-OVERFLOW",
                "sensor_type": "work_order_queue",
                "affected_services": ["mes-controller"],
                "cascade_services": ["oee-analytics"],
                "description": "MES work-order queue backlog exceeded soft watermark; auto-scale workers eligible",
                "investigation_notes": (
                    "Root Cause: Queue depth growing past the soft watermark indicates inbound rate has temporarily "
                    "exceeded the worker pool's drain rate. This is normal during shift change and during morning "
                    "release windows. Auto-scaling workers within the configured max is safe.\n"
                    "Remediation (auto-remediate eligible): 1) Scale workers: `mes-admin scale-workers --pool "
                    "WORK-ORDER --count {target_workers}`. 2) Confirm queue depth recovers within 5 min. "
                    "3) If recurring, raise the steady-state pool size in the deployment config."
                ),
                "remediation_action": "scale_mes_workers",
                "error_message": "[MES] MES-QUEUE-OVERFLOW: queue=WORK-ORDER depth={queue_depth} soft_watermark=2000 hard_watermark=5000 workers={current_workers}",
                "stack_trace": (
                    "=== MES QUEUE STATUS — WORK-ORDER ===\n"
                    "Depth: {queue_depth} | Soft watermark: 2000 | Hard watermark: 5000\n"
                    "Workers: {current_workers} (max: 16)\n"
                    "------------------------------------------------------------------------\n"
                    "Recent rates:\n"
                    "  Inbound:    480/min\n"
                    "  Drain:      320/min\n"
                    "  Net:        +160/min\n"
                    "------------------------------------------------------------------------\n"
                    "MES-QUEUE-OVERFLOW: auto-scale workers from {current_workers} → {target_workers}"
                ),
            },
            19: {
                "name": "SCADA Connection Pool Exhausted",
                "subsystem": "scada",
                "vehicle_section": "session_pool",
                "error_type": "SCADA-CONNECTION-POOL-EXHAUST",
                "sensor_type": "session_pool",
                "affected_services": ["scada-gateway"],
                "cascade_services": ["mes-controller"],
                "description": "SCADA gateway client connection pool fully utilized; auto-restart pool eligible",
                "investigation_notes": (
                    "Root Cause: A leaked client session — typically a cancelled subscription that didn't release its "
                    "channel — accumulates over hours until the pool is exhausted. New downstream consumers (MES, "
                    "historian, dashboards) get connection refused.\n"
                    "Remediation (auto-remediate eligible): 1) Restart the pool: `scada-admin restart-pool --pool "
                    "client-sessions`. 2) Confirm pool free count returns to ≥ 10. "
                    "3) Open a code issue if leak recurs within 24h — usually a missing `dispose()` on the consumer side."
                ),
                "remediation_action": "restart_session_pool",
                "error_message": "[SCADA] SCADA-CONNECTION-POOL-EXHAUST: pool=client-sessions used={pool_used} max=64 leaked_estimate={leaked_count}",
                "stack_trace": (
                    "=== SCADA CLIENT SESSION POOL ===\n"
                    "Pool: client-sessions | Used: {pool_used}/64 | Idle: 0\n"
                    "------------------------------------------------------------------------\n"
                    "CONSUMER             | SESSIONS | OLDEST (h) | STATUS\n"
                    "------------------------------------------------------------------------\n"
                    "mes-controller        | 12       | 0.5        | active\n"
                    "ot-historian          | 8        | 0.3        | active\n"
                    "(orphaned)            | {leaked_count}       | 14.2       | leaked\n"
                    "------------------------------------------------------------------------\n"
                    "SCADA-CONNECTION-POOL-EXHAUST: restart pool — leaked sessions reclaimed"
                ),
            },
            20: {
                "name": "OEE Cache Invalidation",
                "subsystem": "oee",
                "vehicle_section": "result_cache",
                "error_type": "OEE-CACHE-INVALIDATION",
                "sensor_type": "result_cache",
                "affected_services": ["oee-analytics"],
                "cascade_services": ["shopfloor-portal"],
                "description": "OEE result cache holding stale entries after an upstream MES retroactive correction; auto-flush eligible",
                "investigation_notes": (
                    "Root Cause: When MES posts a retroactive correction (e.g., reclassifying downtime from unplanned "
                    "to planned), already-computed OEE results in the cache become stale. The cache TTL eventually "
                    "expires them, but the dashboard shows the wrong number until then. A targeted flush is safe.\n"
                    "Remediation (auto-remediate eligible): 1) Flush stale entries: `oee-admin cache-flush --since "
                    "{correction_time}`. 2) Recompute the affected window: `oee-admin recompute --line {line_id} "
                    "--window {affected_window}`. 3) Confirm dashboards refresh within 30s."
                ),
                "remediation_action": "flush_oee_cache",
                "error_message": "[OEE] OEE-CACHE-INVALIDATION: line={line_id} stale_entries={stale_entries} correction_time={correction_time} affected_window={affected_window}",
                "stack_trace": (
                    "=== OEE RESULT CACHE — STALE ENTRIES ===\n"
                    "Line: {line_id} | Correction posted: {correction_time}\n"
                    "------------------------------------------------------------------------\n"
                    "WINDOW START      | KEY                          | STALE\n"
                    "------------------------------------------------------------------------\n"
                    "13:00–14:00       | oee:{line_id}:13:00          | YES\n"
                    "14:00–15:00       | oee:{line_id}:14:00          | YES\n"
                    "15:00–16:00       | oee:{line_id}:15:00          | YES\n"
                    "------------------------------------------------------------------------\n"
                    "OEE-CACHE-INVALIDATION: {stale_entries} entries stale; auto-flush eligible"
                ),
            },
        }

    # -- Topology ---------------------------------------------------------------

    @property
    def service_topology(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "mes-controller": [
                ("scada-gateway", "/api/v1/scada/tag-read", "GET"),
                ("ot-historian", "/api/v1/historian/range-query", "GET"),
                ("oee-analytics", "/api/v1/oee/event", "POST"),
                ("quality-inspector", "/api/v1/quality/result", "GET"),
                ("erp-bridge", "/api/v1/erp/work-order-update", "POST"),
                ("inventory-sync", "/api/v1/inventory/consume", "POST"),
                ("shopfloor-portal", "/api/v1/portal/work-order-status", "POST"),
            ],
            "scada-gateway": [
                ("ot-historian", "/api/v1/historian/tag-write", "POST"),
                ("mes-controller", "/api/v1/mes/equipment-state", "POST"),
            ],
            "ot-historian": [
                ("oee-analytics", "/api/v1/oee/tag-feed", "POST"),
            ],
            "oee-analytics": [
                ("mes-controller", "/api/v1/mes/oee-feedback", "POST"),
                ("shopfloor-portal", "/api/v1/portal/oee-tile", "POST"),
            ],
            "quality-inspector": [
                ("mes-controller", "/api/v1/mes/quality-event", "POST"),
                ("oee-analytics", "/api/v1/oee/quality-feed", "POST"),
            ],
            "maintenance-scheduler": [
                ("mes-controller", "/api/v1/mes/maintenance-window", "POST"),
                ("erp-bridge", "/api/v1/erp/spare-parts-request", "POST"),
            ],
            "erp-bridge": [
                ("inventory-sync", "/api/v1/inventory/material-master", "POST"),
            ],
            "inventory-sync": [
                ("mes-controller", "/api/v1/mes/material-availability", "POST"),
            ],
            "shopfloor-portal": [
                ("mes-controller", "/api/v1/mes/operator-action", "POST"),
                ("quality-inspector", "/api/v1/quality/operator-flag", "POST"),
            ],
        }

    @property
    def entry_endpoints(self) -> dict[str, list[tuple[str, str]]]:
        return {
            "mes-controller": [
                ("/api/v1/mes/work-orders", "POST"),
                ("/api/v1/mes/release-line", "POST"),
                ("/api/v1/mes/batch-genealogy", "GET"),
            ],
            "scada-gateway": [("/api/v1/scada/tag-write", "POST")],
            "ot-historian": [("/api/v1/historian/query", "POST")],
            "oee-analytics": [("/api/v1/oee/calculate", "POST")],
            "quality-inspector": [("/api/v1/quality/inspect", "POST")],
            "maintenance-scheduler": [("/api/v1/cmms/work-order", "POST")],
            "erp-bridge": [("/api/v1/erp/idoc", "POST")],
            "inventory-sync": [("/api/v1/inventory/sync", "POST")],
            "shopfloor-portal": [("/api/v1/portal/scan", "POST")],
        }

    @property
    def db_operations(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "mes-controller": [
                ("SELECT", "work_orders", "SELECT work_order_id, line_id, product_code, quantity, status FROM work_orders WHERE status IN ('RELEASED', 'IN_PROGRESS')"),
                ("INSERT", "equipment_state_history", "INSERT INTO equipment_state_history (line_id, equipment_id, state, started_at, operator_id) VALUES (?, ?, ?, NOW(), ?)"),
                ("UPDATE", "work_orders", "UPDATE work_orders SET status = ?, completed_qty = ?, last_updated = NOW() WHERE work_order_id = ?"),
            ],
            "scada-gateway": [
                ("INSERT", "tag_subscription_log", "INSERT INTO tag_subscription_log (plc_id, tag_name, value, quality, ts) VALUES (?, ?, ?, ?, NOW())"),
            ],
            "ot-historian": [
                ("INSERT", "tag_archive_writes", "INSERT INTO tag_archive_writes (archive_id, tag_name, value, ts, quality) VALUES (?, ?, ?, ?, ?)"),
                ("SELECT", "tag_archive", "SELECT tag_name, value, ts FROM tag_archive WHERE tag_name = ? AND ts BETWEEN ? AND ?"),
            ],
            "oee-analytics": [
                ("SELECT", "shift_summary", "SELECT line_id, shift, availability_pct, performance_pct, quality_pct FROM shift_summary WHERE shift_date = CURRENT_DATE"),
                ("INSERT", "oee_calculations", "INSERT INTO oee_calculations (line_id, shift, window_start, availability, performance, quality, oee) VALUES (?, ?, ?, ?, ?, ?, ?)"),
            ],
            "quality-inspector": [
                ("INSERT", "inspection_results", "INSERT INTO inspection_results (station_id, part_id, characteristic, measured_value, result) VALUES (?, ?, ?, ?, ?)"),
                ("SELECT", "spc_baselines", "SELECT characteristic, target, usl, lsl, sigma FROM spc_baselines WHERE line_id = ? AND active = 1"),
            ],
            "maintenance-scheduler": [
                ("SELECT", "maintenance_work_orders", "SELECT mwo_id, asset_id, work_type, priority, scheduled_at, status FROM maintenance_work_orders WHERE status IN ('open', 'scheduled')"),
                ("INSERT", "predictive_signals", "INSERT INTO predictive_signals (asset_id, sensor_type, value, health_score, ts) VALUES (?, ?, ?, ?, NOW())"),
            ],
            "erp-bridge": [
                ("SELECT", "idoc_outbox", "SELECT idoc_id, idoc_type, payload, retries FROM idoc_outbox WHERE status = 'pending' ORDER BY created_at LIMIT 100"),
            ],
            "inventory-sync": [
                ("SELECT", "material_master", "SELECT material_code, on_hand_qty, reorder_point, safety_stock FROM material_master WHERE plant_id = ?"),
                ("INSERT", "inventory_deltas", "INSERT INTO inventory_deltas (material_code, delta_units, location, source_doc, ts) VALUES (?, ?, ?, ?, NOW())"),
            ],
            "shopfloor-portal": [
                ("SELECT", "operator_sessions", "SELECT session_id, operator_id, kiosk_id, started_at FROM operator_sessions WHERE status = 'active'"),
            ],
        }

    # -- Infrastructure ---------------------------------------------------------

    @property
    def hosts(self) -> list[dict[str, Any]]:
        return [
            {
                "host.name": "mfg-aws-host-01",
                "host.id": "i-0m1f2g3a4w5s67890",
                "host.arch": "amd64",
                "host.type": "m5.xlarge",
                "host.image.id": "ami-0mfg12345aws",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8175M CPU @ 2.50GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "4",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.0.3.50", "172.16.2.10"],
                "host.mac": ["0a:3b:4c:5d:6e:7f", "0a:3b:4c:5d:6e:80"],
                "os.type": "linux",
                "os.description": "Amazon Linux 2023.6.20250115",
                "cloud.provider": "aws",
                "cloud.platform": "aws_ec2",
                "cloud.region": "us-east-1",
                "cloud.availability_zone": "us-east-1a",
                "cloud.account.id": "345678901234",
                "cloud.instance.id": "i-0m1f2g3a4w5s67890",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 250 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "mfg-gcp-host-01",
                "host.id": "8273456789012345678",
                "host.arch": "amd64",
                "host.type": "e2-standard-4",
                "host.image.id": "projects/debian-cloud/global/images/debian-12-bookworm-v20250115",
                "host.cpu.model.name": "Intel(R) Xeon(R) CPU @ 2.20GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "7",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.128.2.20", "10.128.2.21"],
                "host.mac": ["42:01:0a:82:02:14", "42:01:0a:82:02:15"],
                "os.type": "linux",
                "os.description": "Debian GNU/Linux 12 (bookworm)",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "us-central1",
                "cloud.availability_zone": "us-central1-a",
                "cloud.account.id": "mfg-project-prod",
                "cloud.instance.id": "8273456789012345678",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 100 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "mfg-sap-bridge-01",
                "host.id": "/subscriptions/mfg-abc/resourceGroups/mfg-rg/providers/Microsoft.Compute/virtualMachines/mfg-sap-bridge-01",
                "host.arch": "amd64",
                "host.type": "Standard_D4s_v3",
                "host.image.id": "MicrosoftWindowsServer:WindowsServer:2022-Datacenter:latest",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "106",
                "host.cpu.stepping": "6",
                "host.cpu.cache.l2.size": 1310720,
                "host.ip": ["10.3.0.4", "10.3.0.5"],
                "host.mac": ["00:0d:3a:7b:6c:5d", "00:0d:3a:7b:6c:5e"],
                "os.type": "windows",
                "os.description": "Windows Server 2022 Datacenter",
                "cloud.provider": "azure",
                "cloud.platform": "azure_vm",
                "cloud.region": "eastus",
                "cloud.availability_zone": "eastus-1",
                "cloud.account.id": "mfg-abc-def-ghi",
                "cloud.instance.id": "mfg-sap-bridge-01",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 256 * 1024 * 1024 * 1024,
            },
        ]

    @property
    def k8s_clusters(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "mfg-eks-cluster",
                "provider": "aws",
                "platform": "aws_eks",
                "region": "us-east-1",
                "zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
                "os_description": "Amazon Linux 2",
                "services": ["mes-controller", "scada-gateway", "ot-historian"],
            },
            {
                "name": "mfg-gke-cluster",
                "provider": "gcp",
                "platform": "gcp_gke",
                "region": "us-central1",
                "zones": ["us-central1-a", "us-central1-b", "us-central1-c"],
                "os_description": "Container-Optimized OS",
                "services": ["oee-analytics", "quality-inspector", "maintenance-scheduler"],
            },
            {
                "name": "mfg-aks-cluster",
                "provider": "azure",
                "platform": "azure_aks",
                "region": "eastus",
                "zones": ["eastus-1", "eastus-2", "eastus-3"],
                "os_description": "Ubuntu 22.04 LTS",
                "services": ["erp-bridge", "inventory-sync", "shopfloor-portal"],
            },
        ]

    # -- Theme ------------------------------------------------------------------

    @property
    def theme(self) -> UITheme:
        return UITheme(
            bg_primary="#1a1f24",
            bg_secondary="#222931",
            bg_tertiary="#2c343d",
            accent_primary="#F26522",
            accent_secondary="#FFA826",
            text_primary="#e6edf3",
            text_secondary="#8b949e",
            text_accent="#F26522",
            status_nominal="#3fb950",
            status_warning="#d29922",
            status_critical="#f85149",
            status_info="#58a6ff",
            font_family="'Inter', system-ui, sans-serif",
            font_mono="'JetBrains Mono', 'Fira Code', monospace",
            chaos_title="Plant Incident Simulator",
            service_label="System",
            channel_label="Incident",
        )

    @property
    def countdown_config(self) -> CountdownConfig:
        return CountdownConfig(enabled=False)

    # -- Agent Config -----------------------------------------------------------

    @property
    def agent_config(self) -> dict[str, Any]:
        return {
            "id": "mfg-operations-analyst",
            "name": "Manufacturing Operations Analyst",
            "assessment_tool_name": "production_readiness_assessment",
            "system_prompt": (
                "You are the Manufacturing Operations Analyst, an expert AI assistant for "
                "discrete manufacturing operations spanning OT and IT. You help plant operations "
                "and IT teams investigate system anomalies, analyze OT/IT integration failures, "
                "and provide root cause analysis for fault conditions across 9 systems on "
                "AWS, GCP, and Azure. "
                "You have deep expertise in MES (work orders, batch genealogy, equipment state), "
                "SCADA / OPC-UA / Modbus / EtherNet-IP, OT historian time-series stores, OEE "
                "(availability x performance x quality), SPC and Cpk process capability, vision "
                "inspection, CMMS and predictive maintenance (vibration RMS, ISO 10816), Windows "
                "event logs (event IDs 7031/7034/7036, channel System), Docker/Kubernetes pod "
                "OOM and CrashLoopBackOff diagnostics, ISA-95 levels, and IATF 16949 / FDA "
                "21 CFR Part 11 traceability. "
                "When investigating incidents, search for these system identifiers in logs: "
                "OT/SCADA faults (PLC-COMM-LOSS, SCADA-TAG-STORM, PROTOCOL-DRIFT, OPC-UA-CERT-EXPIRY), "
                "MES faults (MES-WORK-ORDER-DEADLOCK, MES-BATCH-GENEALOGY-BREAK, MES-QUEUE-OVERFLOW), "
                "Historian faults (OT-HISTORIAN-BACKPRESSURE), "
                "Quality faults (SPC-OUT-OF-CONTROL, VISION-INSPECT-FAIL), "
                "Maintenance faults (CMMS-WORK-ORDER-BACKLOG, PREDICTIVE-MAINT-ANOMALY), "
                "OEE faults (OEE-AVAILABILITY-DROP, ANALYTICS-CONTAINER-OOM, OEE-CACHE-INVALIDATION), "
                "ERP faults (ERP-WIN-SERVICE-CRASH), "
                "Inventory faults (RAW-MATERIAL-SHORTAGE, INVENTORY-SYNC-BATCH-FAIL), "
                "and Portal faults (PORTAL-CONTAINER-CRASHLOOP, SCADA-CONNECTION-POOL-EXHAUST). "
                "Log messages are in body.text — NEVER search the body field alone."
            ),
        }

    @property
    def assessment_tool_config(self) -> dict[str, Any]:
        return {
            "id": "production_readiness_assessment",
            "description": (
                "Plant-wide production readiness assessment. Evaluates OEE health, OT "
                "connectivity, MES queue depth, quality drift (Cpk), and IT-side "
                "dependencies (ERP bridge, shopfloor portal) for safe continued production "
                "at SLA targets. Returns aggregated error/warning counts across the 9 "
                "manufacturing systems. Log message field: body.text (never use 'body' alone)."
            ),
        }

    @property
    def knowledge_base_docs(self) -> list[dict[str, Any]]:
        return []  # Populated by deployer from channel_registry

    # -- Service Classes --------------------------------------------------------

    def get_service_classes(self) -> list[type]:
        from scenarios.manufacturing.services.mes_controller import MESControllerService
        from scenarios.manufacturing.services.scada_gateway import SCADAGatewayService
        from scenarios.manufacturing.services.ot_historian import OTHistorianService
        from scenarios.manufacturing.services.oee_analytics import OEEAnalyticsService
        from scenarios.manufacturing.services.quality_inspector import QualityInspectorService
        from scenarios.manufacturing.services.maintenance_scheduler import MaintenanceSchedulerService
        from scenarios.manufacturing.services.erp_bridge import ERPBridgeService
        from scenarios.manufacturing.services.inventory_sync import InventorySyncService
        from scenarios.manufacturing.services.shopfloor_portal import ShopfloorPortalService

        return [
            MESControllerService,
            SCADAGatewayService,
            OTHistorianService,
            OEEAnalyticsService,
            QualityInspectorService,
            MaintenanceSchedulerService,
            ERPBridgeService,
            InventorySyncService,
            ShopfloorPortalService,
        ]

    # -- Trace Attributes & RCA -------------------------------------------------

    def get_trace_attributes(self, service_name: str, rng) -> dict:
        hour = int(time.time()) % 86400 // 3600
        if hour < 7:
            shift = "C"
        elif hour < 15:
            shift = "A"
        else:
            shift = "B"
        base = {
            "plant.site": rng.choice(["Houston-TX", "Greenville-SC", "Loveland-OH", "Reno-NV", "Monterrey-MX"]),
            "plant.shift": shift,
        }
        svc_attrs = {
            "mes-controller": {
                "mes.line": rng.choice(["LINE-01", "LINE-02", "LINE-03", "LINE-04", "LINE-05"]),
                "mes.product_family": rng.choice(["bracket", "housing", "shaft", "pcb_assy", "valve"]),
            },
            "scada-gateway": {
                "scada.protocol": rng.choice(["opcua", "opcua", "modbus_tcp", "ethernet_ip"]),
                "scada.subscription_count": rng.randint(120, 320),
            },
            "ot-historian": {
                "historian.archive_tier": rng.choice(["hot", "warm", "cold"]),
                "historian.compression": rng.choice(["lz4", "zstd"]),
            },
            "oee-analytics": {
                "oee.calc_window_min": rng.choice([5, 15, 60]),
                "oee.line": rng.choice(["LINE-01", "LINE-02", "LINE-03", "LINE-04", "LINE-05"]),
            },
            "quality-inspector": {
                "quality.station_type": rng.choice(["vision", "cmm", "torque", "leak_test"]),
                "quality.characteristic": rng.choice(["LENGTH_MM", "DIAMETER_MM", "TORQUE_NM", "WEIGHT_G"]),
            },
            "maintenance-scheduler": {
                "maintenance.asset_class": rng.choice(["A", "A", "B", "C"]),
                "maintenance.work_type": rng.choice(["preventive", "corrective", "predictive"]),
            },
            "erp-bridge": {
                "erp.system": "SAP-ECC",
                "erp.idoc_type": rng.choice(["ORDERS05", "DELVRY07", "MATMAS05", "INVOIC02"]),
            },
            "inventory-sync": {
                "inventory.warehouse": rng.choice(["WH-A-01", "WH-B-02", "WH-RAW-01"]),
                "inventory.material_class": rng.choice(["raw", "wip", "fg", "spare"]),
            },
            "shopfloor-portal": {
                "portal.kiosk_type": rng.choice(["kiosk", "tablet", "mobile_scanner"]),
                "portal.line": rng.choice(["LINE-01", "LINE-02", "LINE-03", "LINE-04", "LINE-05"]),
            },
        }
        base.update(svc_attrs.get(service_name, {}))
        return base

    def get_rca_clues(self, channel: int, service_name: str, rng) -> dict:
        clues = {
            1: {  # PLC Communication Loss
                "scada-gateway": {"opcua.last_keepalive_s": rng.randint(15, 600), "opcua.secure_channel_status": "BadSecureChannelClosed"},
                "mes-controller": {"mes.work_order_blocked_count": rng.randint(8, 60), "mes.upstream_tag_age_s": rng.randint(30, 600)},
                "ot-historian": {"historian.tag_drop_count": rng.randint(50, 800)},
                "oee-analytics": {"oee.stale_window_count": rng.randint(2, 12)},
                "shopfloor-portal": {"portal.work_order_status_stale": True},
            },
            2: {  # MES Work Order Deadlock
                "mes-controller": {"mes.deadlock_tx_count": rng.randint(2, 12), "mes.routing_ruleset_version": "v3.4.1-beta"},
                "oee-analytics": {"oee.line_stalled_min": rng.randint(5, 35)},
                "shopfloor-portal": {"portal.operator_actions_held": rng.randint(4, 25)},
            },
            3: {  # Batch Genealogy Break
                "mes-controller": {"mes.orphan_operations": rng.randint(2, 14), "mes.consumption_event_lag_s": rng.randint(60, 900)},
                "quality-inspector": {"quality.batch_under_review": True},
                "ot-historian": {"historian.consumption_event_gap": True},
            },
            4: {  # SCADA Tag Storm
                "scada-gateway": {"scada.publish_rate_per_s": rng.randint(15_000, 60_000), "scada.deadband_pct": 0.0},
                "ot-historian": {"historian.buffer_high_watermark_pct": round(rng.uniform(85.0, 99.5), 1)},
                "mes-controller": {"mes.tag_feed_lag_s": rng.randint(5, 35)},
                "oee-analytics": {"oee.event_intake_lag_s": rng.randint(8, 45)},
            },
            5: {  # OT Historian Backpressure
                "ot-historian": {"historian.write_lag_s": rng.randint(8, 45), "historian.compaction_status": "stalled"},
                "scada-gateway": {"scada.write_retry_count": rng.randint(10, 200)},
                "oee-analytics": {"oee.tag_feed_lag_s": rng.randint(5, 30)},
            },
            6: {  # Protocol Drift
                "scada-gateway": {"scada.parse_failure_count": rng.randint(20, 200), "scada.firmware_diff": True},
                "mes-controller": {"mes.implausible_tag_value_count": rng.randint(2, 25)},
                "ot-historian": {"historian.tag_quality_bad_count": rng.randint(5, 80)},
            },
            7: {  # OPC-UA Cert Expiry
                "scada-gateway": {"opcua.cert_status": "expired", "opcua.cert_expired_days": rng.randint(1, 14)},
                "mes-controller": {"mes.scada_link_status": "down"},
                "ot-historian": {"historian.scada_link_status": "down"},
                "shopfloor-portal": {"portal.scada_link_status": "down"},
            },
            8: {  # OEE Availability Drop
                "oee-analytics": {"oee.availability_pct": round(rng.uniform(45.0, 74.0), 1), "oee.target_pct": 85.0},
                "mes-controller": {"mes.unplanned_downtime_min": rng.randint(8, 45)},
                "shopfloor-portal": {"portal.line_alert_displayed": True},
            },
            9: {  # SPC Out-of-Control
                "quality-inspector": {"quality.spc_rule_fired": rng.choice(["WE-1", "WE-2", "Nelson-5"]), "quality.cpk": round(rng.uniform(0.65, 1.20), 3)},
                "mes-controller": {"mes.lot_under_quarantine": True},
                "oee-analytics": {"oee.quality_pct": round(rng.uniform(82.0, 94.0), 1)},
            },
            10: {  # Vision Inspect Fail
                "quality-inspector": {"vision.confidence_avg": round(rng.uniform(0.55, 0.78), 3), "vision.frames_dropped": rng.randint(50, 800)},
                "mes-controller": {"mes.unverified_parts_count": rng.randint(20, 300)},
                "oee-analytics": {"oee.quality_pct": round(rng.uniform(80.0, 92.0), 1)},
            },
            11: {  # CMMS Backlog
                "maintenance-scheduler": {"cmms.class_a_overdue": rng.randint(3, 18), "cmms.oldest_overdue_days": rng.randint(30, 120)},
                "mes-controller": {"mes.maintenance_at_risk_lines": rng.randint(1, 4)},
                "oee-analytics": {"oee.mtbf_hours_trend": "decreasing"},
            },
            12: {  # Predictive Maint Anomaly
                "maintenance-scheduler": {"cmms.vibration_zone": "C", "cmms.rul_days": rng.randint(3, 21)},
                "mes-controller": {"mes.asset_at_risk": True},
                "scada-gateway": {"scada.thermal_dt_c": round(rng.uniform(8.0, 18.0), 1)},
            },
            13: {  # Analytics Container OOM
                "oee-analytics": {"k8s.last_oom_kill": True, "k8s.restart_count": rng.randint(2, 12), "k8s.mem_limit_mi": 512},
                "mes-controller": {"mes.oee_feedback_lag_s": rng.randint(15, 90)},
                "shopfloor-portal": {"portal.oee_tile_stale": True},
            },
            14: {  # ERP Win Service Crash
                "erp-bridge": {"winlog.event_id": 7031, "winlog.crash_count": rng.randint(1, 5), "erp.idoc_backlog": rng.randint(20, 250)},
                "mes-controller": {"mes.erp_link_status": "down"},
                "inventory-sync": {"inventory.erp_master_sync_lag_s": rng.randint(120, 900)},
            },
            15: {  # Raw Material Shortage
                "inventory-sync": {"inventory.material_below_reorder": True, "inventory.hours_to_starve": rng.randint(2, 14)},
                "mes-controller": {"mes.work_orders_at_risk": rng.randint(3, 18)},
                "oee-analytics": {"oee.starvation_risk_pct": round(rng.uniform(15.0, 65.0), 1)},
            },
            16: {  # Portal Container Crashloop
                "shopfloor-portal": {"k8s.crashloopbackoff": True, "k8s.restart_count": rng.randint(5, 25), "k8s.image_tag": "1.18.3-broken"},
                "mes-controller": {"mes.operator_action_lag_s": rng.randint(30, 240)},
            },
            17: {  # Inventory Sync Batch Fail
                "inventory-sync": {"wms.batch_failure_mode": rng.choice(["SOCKET_TIMEOUT", "RFC_HANDLE_INVALID"]), "wms.retry_count": rng.randint(0, 2)},
                "erp-bridge": {"erp.idoc_outbox_lag_s": rng.randint(60, 600)},
            },
            18: {  # MES Queue Overflow
                "mes-controller": {"mes.queue_depth": rng.randint(2200, 4800), "mes.worker_count": rng.randint(4, 8)},
                "oee-analytics": {"oee.event_intake_lag_s": rng.randint(15, 75)},
            },
            19: {  # SCADA Pool Exhausted
                "scada-gateway": {"scada.session_pool_used": rng.randint(58, 64), "scada.leaked_session_count": rng.randint(15, 45)},
                "mes-controller": {"mes.scada_connection_refused_count": rng.randint(3, 25)},
            },
            20: {  # OEE Cache Invalidation
                "oee-analytics": {"oee.stale_cache_entries": rng.randint(8, 80), "oee.correction_window_min": rng.randint(15, 240)},
                "shopfloor-portal": {"portal.oee_tile_stale": True},
            },
        }
        channel_clues = clues.get(channel, {})
        return channel_clues.get(service_name, {})

    def get_correlation_attribute(self, channel: int, is_error: bool, rng) -> dict:
        correlation_attrs = {
            1: ("infra.opcua_gateway_build", "scada-gateway-v4.2.1-rc3"),
            2: ("deployment.mes_routing_ruleset", "routing-v3.4.1-beta"),
            3: ("deployment.mes_genealogy_engine", "genealogy-v2.7.0-experimental"),
            4: ("infra.scada_publish_config", "deadband-zero-experimental"),
            5: ("infra.historian_storage_volume", "ar-current-vol-degraded"),
            6: ("infra.plc_firmware_version", "siemens-s7-1500-v3.1.7-unsigned"),
            7: ("infra.opcua_cert_profile", "ot-pki-shortlived-30d"),
            8: ("deployment.oee_calc_engine", "oee-v5.1.0-rc2"),
            9: ("deployment.spc_baseline_config", "baseline-v2.3-tightened"),
            10: ("deployment.vision_model_version", "yolo-v8-mfg-v3.4-beta"),
            11: ("deployment.cmms_scheduler_config", "scheduler-v4.0.0-aggressive"),
            12: ("infra.predictive_model_version", "rul-xgboost-v2.1-rc1"),
            13: ("deployment.oee_analytics_image", "oee-analytics:5.1.0-rc2"),
            14: ("infra.windows_patch_level", "win2022-kb5034441-pending"),
            15: ("deployment.wms_forecast_engine", "forecast-v3.0.0-tuning"),
            16: ("deployment.shopfloor_portal_image", "shopfloor-portal:1.18.3-broken"),
            17: ("infra.rfc_gateway_pool", "rfc-pool-experimental-32conn"),
            18: ("deployment.mes_worker_pool_config", "worker-pool-v2.5.0-low-concurrency"),
            19: ("infra.scada_session_pool_config", "session-pool-v3.1-leak"),
            20: ("deployment.oee_cache_ttl_config", "ttl-aggressive-300s"),
        }
        attr_key, attr_val = correlation_attrs.get(channel, ("deployment.config_version", "unknown"))
        if is_error:
            if rng.random() < 0.90:
                return {attr_key: attr_val}
        else:
            if rng.random() < 0.05:
                return {attr_key: attr_val}
        return {}

    # -- Fault Parameters -------------------------------------------------------

    def get_fault_params(self, channel: int) -> dict[str, Any]:
        return {
            # Lines, products, batches
            "line_id": random.choice(["LINE-01", "LINE-02", "LINE-03", "LINE-04", "LINE-05"]),
            "product_code": random.choice(["PRD-A100", "PRD-A200", "PRD-B450", "PRD-B475", "PRD-C901"]),
            "batch_id": f"BATCH-{random.randint(100000, 999999)}",
            "work_order_id": f"WO-{random.randint(100000, 999999)}",
            "operation_id": f"OP-{random.choice(['010', '020', '030', '040', '050'])}",
            # OPC-UA / SCADA / PLC
            "plc_id": random.choice(["PLC-LINE01-A", "PLC-LINE02-A", "PLC-LINE03-A", "PLC-LINE03-B", "PLC-PACK-01"]),
            "plc_host": f"plc-{random.randint(10, 99)}.ot.internal",
            "opcua_status": random.choice(["0x80AC0000", "0x80820000", "0x80130000"]),
            "subscription_id": f"sub-{random.randint(1000, 9999)}",
            "comm_loss_seconds": random.randint(15, 600),
            "tag_name": random.choice(["MotorSpeed", "OvenTempC", "ConveyorRPM", "PressurePsi", "PartsCounter"]),
            "tag_rate": random.randint(15_000, 60_000),
            "affected_plcs": random.randint(1, 4),
            "protocol": random.choice(["modbus_tcp", "ethernet_ip"]),
            "firmware_version": random.choice(["v3.1.7", "v3.2.0", "v3.2.1"]),
            "firmware_baseline": "v3.0.4",
            "parse_failure_count": random.randint(20, 200),
            "cert_subject": "CN=scada-gateway-prod, O=Manufacturing OT",
            "cert_thumbprint": secrets.token_hex(20),
            "cert_expiry_date": "2026-04-12 00:00:00 UTC",
            "cert_expired_days": random.randint(1, 14),
            # MES
            "tx_id": f"TX-{random.randint(100000, 999999)}",
            "queue_depth": random.randint(2200, 4800),
            "stuck_seconds": random.randint(120, 1800),
            "missing_link_count": random.randint(2, 14),
            "linked_count": random.randint(8, 12),
            "raw_lot_id": f"{random.randint(100000, 999999)}",
            "current_workers": random.randint(4, 8),
            "target_workers": random.randint(10, 16),
            # Historian
            "archive_id": random.choice(["AR-CURRENT", "AR-DAILY-01", "AR-DAILY-02"]),
            "buffer_depth": random.randint(38_000, 50_000),
            "write_lag_s": random.randint(8, 45),
            # OEE / Analytics
            "availability_pct": round(random.uniform(45.0, 74.0), 1),
            "downtime_minutes": random.randint(8, 45),
            "target_oee": 85.0,
            "pod_name": f"oee-analytics-{random.choice(['7c8d9f4b6', '6b9c8e3d2'])}-{secrets.token_hex(2)}xq",
            "container_name": "oee-analytics",
            "restart_count": random.randint(2, 12),
            "mem_limit_mb": 512,
            "mem_peak_mb": random.randint(495, 525),
            "new_mem_limit": "1024Mi",
            "stale_entries": random.randint(8, 80),
            "correction_time": "2026-05-06T13:42:18Z",
            "affected_window": "13:00–16:00",
            # Quality
            "characteristic": random.choice(["LENGTH_MM", "DIAMETER_MM", "TORQUE_NM", "WEIGHT_G"]),
            "spc_rule": random.choice(["WE-1", "WE-2", "Nelson-5"]),
            "cpk": round(random.uniform(0.65, 1.20), 3),
            "station_id": random.choice(["VIS-01", "VIS-02", "VIS-03", "CMM-01"]),
            "model_version": random.choice(["yolo-v8-mfg-v3.4-beta", "yolo-v8-mfg-v3.3"]),
            "confidence_avg": round(random.uniform(0.55, 0.78), 3),
            "frames_dropped": random.randint(50, 800),
            # Maintenance
            "asset_id": random.choice(["MTR-CONV-01", "SPN-MILL-04", "PMP-COOL-02", "CMP-AIR-01"]),
            "sensor_type": random.choice(["vibration_rms_mm_s", "bearing_temp_c", "thermal_dt_c"]),
            "sensor_value": round(random.uniform(4.5, 12.0), 2),
            "rul_days": random.randint(3, 21),
            "ml_confidence": round(random.uniform(0.78, 0.96), 3),
            "overdue_count": random.randint(15, 95),
            "class_a_overdue": random.randint(3, 18),
            "oldest_days": random.randint(30, 120),
            "week": "2026-W19",
            # ERP / Windows
            "win_service_name": random.choice(["SAPHostControl", "SAPHostExec", "MSSQLSERVER"]),
            "crash_count": random.randint(1, 5),
            "idoc_backlog": random.randint(20, 250),
            "elapsed_min": random.randint(5, 45),
            "failure_time": "2026-05-06T14:15:32Z",
            # Inventory
            "material_code": random.choice(["RM-STEEL-A36", "RM-ALU-6061", "RM-PLASTIC-ABS", "RM-COPPER-110"]),
            "on_hand": random.randint(800, 1800),
            "reorder_point": random.randint(2000, 4000),
            "safety_stock": random.randint(500, 1500),
            "po_number": f"PO-{random.randint(100000, 999999)}",
            "po_quantity": random.randint(2000, 12000),
            "supplier_id": random.randint(1000, 9999),
            "po_eta": "2026-05-12T08:00:00Z",
            "forward_consumption": random.randint(1500, 4500),
            "affected_wo_count": random.randint(3, 18),
            "hours_to_starve": random.randint(2, 14),
            "emergency_qty": random.randint(2000, 8000),
            # Portal / k8s
            "image_tag": "registry.mfg.internal/shopfloor-portal:1.18.3-broken",
            "exit_code": random.choice([1, 137, 139]),
            # Inventory batch
            "record_count": random.randint(500, 4500),
            "failure_mode": random.choice(["SOCKET_TIMEOUT", "RFC_HANDLE_INVALID"]),
            "retry_count": random.randint(0, 2),
            # SCADA pool
            "pool_used": random.randint(58, 64),
            "leaked_count": random.randint(15, 45),
        }


# Module-level instance for registry discovery
scenario = ManufacturingScenario()

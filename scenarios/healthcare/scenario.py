"""Healthcare Clinical Systems scenario — hospital operations with EHR, patient monitoring, and clinical workflows."""

from __future__ import annotations

import random
import secrets
import time
from typing import Any

from scenarios.base import BaseScenario, CountdownConfig, UITheme


class HealthcareScenario(BaseScenario):
    """Hospital clinical systems with 9 healthcare services and 20 fault channels."""

    # -- Identity ---------------------------------------------------------------

    @property
    def scenario_id(self) -> str:
        return "healthcare"

    @property
    def scenario_icon(self) -> str:
        return "🏥"

    @property
    def scenario_name(self) -> str:
        return "Healthcare Systems"

    @property
    def scenario_description(self) -> str:
        return (
            "Hospital clinical systems including EHR, patient monitoring, lab "
            "integration, pharmacy, imaging, scheduling, billing, and clinical "
            "alerting. Clean, calm clinical interface."
        )

    @property
    def namespace(self) -> str:
        return "healthcare"

    @property
    def sort_order(self) -> int:
        return 4

    @property
    def raw_log_profile(self) -> dict[str, Any]:
        return {
            "service_name": "patient-portal-edge",
            "user_id_prefix": "mem",
            "tier_field": "plan_type",
            "tier_values": [("hmo", 45), ("ppo", 35), ("medicare", 20)],
            "country_weights": {"US": 95, "CA": 3, "MX": 2},
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "paths": [
                "/api/v1/patients/{id}", "/api/v1/appointments",
                "/api/v1/orders/lab", "/api/v1/billing", "/api/v1/messages",
                "/api/v1/prescriptions", "/login", "/health",
            ],
            "change_point_path": "/api/v1/orders/lab",
        }

    @property
    def executive_kpi_emitter_service_name(self) -> str:
        return "billing-processor"

    @property
    def executive_dashboard_intro(self) -> str:
        return (
            "**Hospital operations KPIs** — access & throughput, revenue cycle, clinical quality, "
            "and EHR operations (synthetic `business.*` from `billing-processor`)."
        )

    @property
    def executive_kpi_sections(self) -> list[dict]:
        return [
            {
                "header": "**Access & throughput** — ED time, admits, discharges, bed, OR, and ICU",
                "specs": [
                    ("ED door-to-provider (min)", "metrics.business.ed_door_to_provider_min"),
                    ("Admits / min", "metrics.business.admits_per_min"),
                    ("Discharges / min", "metrics.business.discharges_per_min"),
                    ("Bed occupancy (%)", "metrics.business.bed_occupancy_pct"),
                    ("OR utilization (%)", "metrics.business.or_utilization_pct"),
                    ("ICU capacity (%)", "metrics.business.icu_capacity_pct"),
                ],
            },
            {
                "header": "**Revenue cycle** — claims, clean rate, denials, AR days, and collections",
                "specs": [
                    ("Claims submitted / min", "metrics.business.claims_submitted_per_min"),
                    ("Clean claim rate (%)", "metrics.business.clean_claim_rate_pct"),
                    ("Denials / min", "metrics.business.denials_per_min"),
                    ("AR days", "metrics.business.accounts_receivable_days"),
                    ("Collections (USD/min)", "metrics.business.collections_usd_per_min"),
                    ("Unbilled charges (USD/min)", "metrics.business.unbilled_charges_usd_per_min"),
                ],
            },
            {
                "header": "**Clinical quality** — order TAT, lab alerts, med reconciliation, and safety",
                "specs": [
                    ("Order turnaround (min)", "metrics.business.order_turnaround_min"),
                    ("Lab critical notification (%)", "metrics.business.lab_critical_notification_pct"),
                    ("Medication reconciliation (%)", "metrics.business.medication_reconciliation_rate_pct"),
                    ("Patient safety events / min", "metrics.business.patient_safety_events_per_min"),
                    ("HCAHPS proxy score", "metrics.business.hcahps_proxy_score"),
                    ("Readmission risk (0–100)", "metrics.business.readmission_risk_index_0_100"),
                ],
            },
            {
                "header": "**Operations** — EHR response, HL7, imaging, no-shows, satisfaction, and compliance",
                "specs": [
                    ("EHR response time (ms)", "metrics.business.ehr_response_time_ms"),
                    ("HL7 messages / min", "metrics.business.hl7_messages_per_min"),
                    ("Imaging worklist size", "metrics.business.imaging_worklist_size"),
                    ("Appointment no-show rate (%)", "metrics.business.appointment_no_show_rate_pct"),
                    ("Patient satisfaction (NPS-like)", "metrics.business.patient_satisfaction_nps"),
                    ("Staff compliance rate (%)", "metrics.business.staff_compliance_rate_pct"),
                ],
            },
        ]

    @property
    def executive_trend_charts(self) -> list[dict]:
        return [
            {"title": "Admits / min", "field": "metrics.business.admits_per_min", "y_label": "admits/min"},
            {"title": "Bed occupancy (%)", "field": "metrics.business.bed_occupancy_pct", "y_label": "%"},
            {"title": "Collections (USD/min)", "field": "metrics.business.collections_usd_per_min", "y_label": "USD/min"},
            {"title": "Clean claim rate (%)", "field": "metrics.business.clean_claim_rate_pct", "y_label": "%"},
            {"title": "ED door-to-provider (min)", "field": "metrics.business.ed_door_to_provider_min", "y_label": "min"},
            {"title": "EHR response time (ms)", "field": "metrics.business.ehr_response_time_ms", "y_label": "ms"},
        ]

    # -- Services ---------------------------------------------------------------

    @property
    def services(self) -> dict[str, dict[str, Any]]:
        return {
            "ehr-system": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1a",
                "subsystem": "clinical_records",
                "language": "java",
            },
            "patient-monitor": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1b",
                "subsystem": "vital_signs",
                "language": "python",
            },
            "lab-integration": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1c",
                "subsystem": "laboratory",
                "language": "go",
            },
            "pharmacy-system": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "medication",
                "language": "java",
            },
            "imaging-service": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-b",
                "subsystem": "radiology",
                "language": "python",
            },
            "scheduling-api": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "scheduling",
                "language": "go",
            },
            "billing-processor": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "billing",
                "language": "dotnet",
            },
            "clinical-alerts": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-2",
                "subsystem": "alerting",
                "language": "python",
            },
            "data-warehouse": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "analytics",
                "language": "java",
            },
        }

    # -- Channel Registry -------------------------------------------------------

    @property
    def channel_registry(self) -> dict[int, dict[str, Any]]:
        return {
            1: {
                "name": "HL7 Message Parsing Failure",
                "subsystem": "clinical_records",
                "vehicle_section": "adt_interface",
                "error_type": "HL7-ACK-AE",
                "sensor_type": "hl7_parser",
                "affected_services": ["ehr-system", "lab-integration"],
                "cascade_services": ["patient-monitor", "clinical-alerts"],
                "description": "HL7 v2.x message parsing fails due to malformed segments or unsupported message types in the ADT interface",
                "investigation_notes": (
                    "Root Cause: Malformed HL7 v2.x segments typically originate from upstream ADT/ORM source systems sending "
                    "non-standard field encodings or unsupported Z-segments. Check the MSH-9 message type and MSH-12 version "
                    "against the interface specification.\n"
                    "Remediation: 1) Review the ACK/NAK disposition — AE (Application Error) vs AR (Application Reject) determines "
                    "retry eligibility. 2) Inspect the Mirth Connect or Rhapsody channel logs for the failing message ID. "
                    "3) Flush the dead-letter queue: `./mirth-cli queue flush --channel ADT-INBOUND --state ERROR`. "
                    "4) If messages are stuck, restart the HL7 listener: `systemctl restart mirth-hl7-listener`. "
                    "5) Verify segment encoding with: `hl7-validator --file /tmp/failed_msg.hl7 --version 2.5.1`. "
                    "6) Reconcile message control IDs in the MSA segment to ensure no duplicate deliveries after recovery."
                ),
                "remediation_action": "restart_hl7_interface",
                "error_message": "[EHR] HL7-ACK-AE: msg_type={msg_type} segment={hl7_segment} position={position} patient=MRN-{mrn}",
                "stack_trace": (
                    "MSH|^~\\&|EHR-CORE|FACILITY-01|LAB-LIS|LAB-01|20260217143052||{msg_type}|MSG-{mrn}.001|P|2.5.1|||AL|NE\n"
                    "EVN|A01|20260217143052|||ADMIN-SYS\n"
                    "PID|1||{mrn}^^^FACILITY-01^MR||DOE^JANE^M||19650315|F|||123 MAIN ST^^ANYTOWN^ST^12345||555-0100|||M|NON|{encounter_id}\n"
                    "{hl7_segment}|<<< PARSE ERROR at position {position} >>>\n"
                    "--- ACK ---\n"
                    "MSH|^~\\&|LAB-LIS|LAB-01|EHR-CORE|FACILITY-01|20260217143052||ACK^{msg_type}|ACK-{mrn}.001|P|2.5.1\n"
                    "MSA|AE|MSG-{mrn}.001|HL7-ACK-AE: Segment {hl7_segment} at position {position} contains invalid field encoding\n"
                    "ERR|^^^207&Application internal error&HL70357|{hl7_segment}^{position}|E|||Invalid segment structure"
                ),
            },
            2: {
                "name": "Vital Signs Alert Storm",
                "subsystem": "vital_signs",
                "vehicle_section": "vitals_engine",
                "error_type": "VITAL-ALERT-STORM",
                "sensor_type": "vital_signs_monitor",
                "affected_services": ["patient-monitor", "clinical-alerts"],
                "cascade_services": ["ehr-system"],
                "description": "Excessive simultaneous vital sign alerts overwhelming the alerting pipeline from bedside monitors",
                "investigation_notes": (
                    "Root Cause: Alert storms occur when bedside monitor thresholds are misconfigured or a genuine multi-patient "
                    "event (e.g., unit-wide SpO2 probe disconnects during rounds) floods the clinical alerting pipeline. The GE/Philips "
                    "central station queues alerts faster than the CDS engine can evaluate them.\n"
                    "Remediation: 1) Check the alert threshold configuration on the central monitoring station for the affected "
                    "nursing unit — verify HR, SpO2, RR, and BP limits match unit acuity (ICU vs MedSurg). "
                    "2) Recalibrate monitors: `monitor-admin recalibrate --unit {nursing_unit} --params HR,SpO2,RR`. "
                    "3) Reset the vitals feed aggregator: `systemctl restart vitals-feed-aggregator`. "
                    "4) Enable alert suppression windowing (10s dedup) on the central station to prevent duplicate firings. "
                    "5) Review biomedical engineering ticket queue for known sensor hardware faults on the unit."
                ),
                "remediation_action": "recalibrate_monitors",
                "error_message": "[MONITOR] VITAL-ALERT-STORM: unit={nursing_unit} alerts={alert_count} window={window_seconds}s patient={patient_id} hr={heart_rate} spo2={spo2}%",
                "stack_trace": (
                    "=== BEDSIDE MONITOR ALERT SUMMARY — {nursing_unit} ===\n"
                    "Interval: {window_seconds}s | Total Alerts: {alert_count} | Threshold: 10/60s\n"
                    "------------------------------------------------------------------------\n"
                    "PATIENT     | PARAM   | VALUE   | LIMIT   | PRIORITY  | STATUS\n"
                    "------------------------------------------------------------------------\n"
                    "{patient_id} | HR      | {heart_rate} bpm | 40-150  | CRITICAL  | UNACKED\n"
                    "{patient_id} | SpO2    | {spo2}%    | >90%    | HIGH      | UNACKED\n"
                    "{patient_id} | RR      | 28 br/m | 8-25    | MEDIUM    | UNACKED\n"
                    "PT-XXXXXX  | BP-SYS  | 185 mmHg| <180    | HIGH      | UNACKED\n"
                    "PT-XXXXXX  | TEMP    | 39.8 C  | <38.5   | MEDIUM    | ESCALATED\n"
                    "------------------------------------------------------------------------\n"
                    "VITAL-ALERT-STORM: {alert_count} alerts in {window_seconds}s exceeds storm threshold on {nursing_unit}\n"
                    "ACTION: Alert pipeline saturated — downstream CDS rule evaluation delayed"
                ),
            },
            3: {
                "name": "Lab Result Delivery Delay",
                "subsystem": "laboratory",
                "vehicle_section": "lab_interface",
                "error_type": "LIS-RESULT-DELAY",
                "sensor_type": "lab_result_queue",
                "affected_services": ["lab-integration", "ehr-system"],
                "cascade_services": ["pharmacy-system", "clinical-alerts"],
                "description": "Laboratory result delivery exceeds critical TAT threshold, delaying clinical decisions",
                "investigation_notes": (
                    "Root Cause: TAT breaches stem from either LIS instrument interface backlogs, specimen processing delays, "
                    "or the HL7 ORU^R01 result delivery queue being stalled. STAT orders should have a 30-minute TAT for "
                    "critical tests (Troponin, BNP, Lactate) but queue congestion delays the OBX result segments.\n"
                    "Remediation: 1) Check the LIS outbound queue depth: `lis-admin queue-status --interface EHR-RESULTS`. "
                    "2) Verify the ASTM/LIS2-A2 instrument interface is connected: `netstat -an | grep 5562`. "
                    "3) For stuck results, force requeue: `lis-admin requeue --order {lab_order_id} --priority STAT`. "
                    "4) Review the analyzer worklist for instrument flags (QC lockout, reagent expiry). "
                    "5) If the HL7 result channel is down, restart: `systemctl restart lis-hl7-outbound`. "
                    "6) Notify lab supervisor and clinical staff of delayed critical results per CAP notification protocol."
                ),
                "remediation_action": "restart_lis_interface",
                "error_message": "[LIS] LIS-RESULT-DELAY: order={lab_order_id} test={test_code} tat={tat_minutes}min sla={max_tat}min patient={patient_id}",
                "stack_trace": (
                    "H|\\^&|||LIS-CORE^Lab Integration|||||LIS2-A2||P|1|20260217143052\n"
                    "P|1||{patient_id}||DOE^JANE||19650315|F\n"
                    "OBR|1|{lab_order_id}||{test_code}|||20260217143052||||||||SERUM\n"
                    "OBX|1|NM|{test_code}^Result^^LIS||--PENDING--|mg/dL|3.5-5.0|N|||F\n"
                    "--- TAT BREACH ---\n"
                    "Order: {lab_order_id} | Test: {test_code} | Collected: 20260217143052\n"
                    "TAT Elapsed: {tat_minutes} min | SLA Target: {max_tat} min | Status: BREACHED\n"
                    "Patient: {patient_id} | Priority: STAT | Specimen: SERUM\n"
                    "LIS-RESULT-DELAY: Result pending for {tat_minutes}min exceeds {max_tat}min SLA\n"
                    "L|1|N"
                ),
            },
            4: {
                "name": "HIPAA Audit Log Integrity Error",
                "subsystem": "analytics",
                "vehicle_section": "audit_subsystem",
                "error_type": "HIPAA-AUDIT-FAIL",
                "sensor_type": "audit_log_integrity",
                "affected_services": ["data-warehouse", "ehr-system"],
                "cascade_services": ["clinical-alerts", "billing-processor"],
                "description": "HIPAA-mandated audit log chain integrity check fails, indicating possible tampering or data loss",
                "investigation_notes": (
                    "Root Cause: HIPAA audit chain integrity failures (SHA-256 hash mismatches) indicate either log record "
                    "tampering, storage corruption, or an out-of-order write during high-volume PHI access logging. Per 45 CFR "
                    "164.312(b), audit controls must maintain an unbroken chain of custody for all PHI access events.\n"
                    "Remediation: 1) Identify the break point: `audit-admin chain-verify --chain {chain_id} --from-sequence "
                    "{sequence_number} --range 100`. 2) Recover audit records from the write-ahead log: `audit-admin recover-wal "
                    "--chain {chain_id} --sequence {sequence_number}`. 3) Rebuild the hash chain from the last valid entry: "
                    "`audit-admin rebuild-chain --chain {chain_id} --from-last-valid`. "
                    "4) Check for storage I/O errors: `audit-admin storage-health --volume audit-vol-01`. "
                    "5) Close the compliance gap: generate an incident report for the Privacy Officer per HIPAA breach "
                    "notification procedures (45 CFR 164.408). "
                    "6) Enable write verification: `audit-admin set-write-verify --chain {chain_id} --mode synchronous`."
                ),
                "remediation_action": "rebuild_audit_chain",
                "error_message": "[DW] HIPAA-AUDIT-FAIL: chain={chain_id} sequence={sequence_number} expected_hash={expected_hash} actual_hash={actual_hash}",
                "stack_trace": (
                    "=== HIPAA AUDIT CHAIN INTEGRITY REPORT ===\n"
                    "Chain: {chain_id} | Algorithm: SHA-256 | Verification: FAILED\n"
                    "------------------------------------------------------------------------\n"
                    "SEQUENCE   | TIMESTAMP   | ACTION       | EXPECTED HASH        | STATUS\n"
                    "------------------------------------------------------------------------\n"
                    "{sequence_number:10d} | 20260217143052 | PHI_ACCESS   | {expected_hash} | MISMATCH\n"
                    "  Stored:   {actual_hash}\n"
                    "  Expected: {expected_hash}\n"
                    "------------------------------------------------------------------------\n"
                    "Previous 3 entries: VALID\n"
                    "Next entry: CANNOT VERIFY (chain broken)\n"
                    "------------------------------------------------------------------------\n"
                    "HIPAA-AUDIT-FAIL: Chain {chain_id} integrity broken at sequence {sequence_number}\n"
                    "Hash mismatch indicates possible record tampering or data corruption\n"
                    "Compliance officer notification triggered — investigation required per 45 CFR 164.312(b)"
                ),
            },
            5: {
                "name": "Medication Interaction Alert Overflow",
                "subsystem": "medication",
                "vehicle_section": "cpoe_engine",
                "error_type": "CPOE-DDI-CRITICAL",
                "sensor_type": "drug_interaction_checker",
                "affected_services": ["pharmacy-system", "ehr-system"],
                "cascade_services": ["clinical-alerts"],
                "description": "Drug interaction checking engine overwhelmed by excessive concurrent medication orders",
                "investigation_notes": (
                    "Root Cause: The CPOE drug-drug interaction (DDI) engine uses a real-time screening database (First Databank "
                    "or Medi-Span) that becomes overloaded when discharge reconciliation generates bulk medication orders. "
                    "Critical interactions (QT prolongation, renal contraindications) queue behind lower-severity checks.\n"
                    "Remediation: 1) Check the CPOE interaction queue: `cpoe-admin queue-depth --engine DDI`. "
                    "2) Reset the CPOE interface to clear stale sessions: `cpoe-admin reset-interface --service DDI-SCREENING`. "
                    "3) Restart the pharmacy queue processor: `systemctl restart pharmacy-order-queue`. "
                    "4) Verify the FDB/Medi-Span knowledge base subscription is active and the local cache is current. "
                    "5) For blocked CRITICAL interactions, escalate to attending physician for dual-sign override per pharmacy P&P. "
                    "6) Monitor the screening engine thread pool: `cpoe-admin thread-status --pool interaction-checker`."
                ),
                "remediation_action": "reset_cpoe_interface",
                "error_message": "[PHARM] CPOE-DDI-CRITICAL: patient={patient_id} med={medication_id} interactions_queued={interaction_count} severity={severity_level}",
                "stack_trace": (
                    "=== DRUG INTERACTION SCREENING — CPOE ENGINE ===\n"
                    "Patient: {patient_id} | New Order: {medication_id}\n"
                    "Severity: {severity_level} | Queue Depth: {interaction_count}\n"
                    "------------------------------------------------------------------------\n"
                    "DRUG-A          | DRUG-B          | TYPE     | SEVERITY  | ACTION\n"
                    "------------------------------------------------------------------------\n"
                    "{medication_id}  | Warfarin 5mg    | PK/PD    | CRITICAL  | BLOCK\n"
                    "{medication_id}  | Amiodarone 200mg| QT-PROLONG| MAJOR    | WARN\n"
                    "{medication_id}  | Metformin 1000mg| RENAL    | MODERATE  | MONITOR\n"
                    "------------------------------------------------------------------------\n"
                    "CPOE-DDI-CRITICAL: {interaction_count} interaction checks queued\n"
                    "Screening engine capacity exceeded — new orders held pending review\n"
                    "Override requires attending physician dual-sign authorization"
                ),
            },
            6: {
                "name": "E-Prescribe Transmission Error",
                "subsystem": "medication",
                "vehicle_section": "eprescribe_gateway",
                "error_type": "NCPDP-SCRIPT-FAIL",
                "sensor_type": "ncpdp_transmitter",
                "affected_services": ["pharmacy-system", "ehr-system"],
                "cascade_services": ["clinical-alerts", "billing-processor"],
                "description": "Electronic prescription transmission to external pharmacy via NCPDP SCRIPT fails",
                "investigation_notes": (
                    "Root Cause: NCPDP SCRIPT 10.6 NEWRX transmission failures are typically caused by pharmacy NPI validation "
                    "errors at the Surescripts network, expired DEA registrations for controlled substances, or SCRIPT message "
                    "formatting issues in the UIB/UIH envelope segments.\n"
                    "Remediation: 1) Verify the pharmacy NPI against the NPPES registry: `ncpdp-admin npi-lookup --npi {pharmacy_npi}`. "
                    "2) Check the Surescripts connection status: `ncpdp-admin connection-test --endpoint surescripts-prod`. "
                    "3) Restart the pharmacy transmission queue: `systemctl restart eprescribe-gateway`. "
                    "4) Review the NCPDP STATUS response codes — 000=accepted, 600=rejected, 900=system error. "
                    "5) For controlled substances (Schedule II-V), verify EPCS two-factor authentication tokens are valid. "
                    "6) Resubmit failed prescriptions: `ncpdp-admin resubmit --rx {prescription_id} --force-npi-refresh`."
                ),
                "remediation_action": "restart_pharmacy_queue",
                "error_message": "[PHARM] NCPDP-SCRIPT-FAIL: rx={prescription_id} patient={patient_id} pharmacy_npi={pharmacy_npi} ncpdp_status={ncpdp_status}",
                "stack_trace": (
                    "--- NCPDP SCRIPT 10.6 MESSAGE TRACE ---\n"
                    ">>> NEWRX Request\n"
                    "  UIB+UNOA:0++{prescription_id}+{pharmacy_npi}:D+20260217143052\n"
                    "  UIH+SCRIPT:010:006:NEWRX+{prescription_id}:P\n"
                    "  PVD+PC+{pharmacy_npi}:HPI+++COMMUNITY PHARMACY\n"
                    "  PTT+1+{patient_id}+DOE:JANE+19650315:F\n"
                    "  DRU+P:MEDICATION:{medication_id}+85+EA+++1\n"
                    "  UIT+{prescription_id}+7\n"
                    "  UIZ++1\n"
                    "<<< STATUS Response\n"
                    "  STS+{ncpdp_status}:NCPDP-SCRIPT-FAIL\n"
                    "  FreeText: Transmission rejected — pharmacy NPI {pharmacy_npi} validation failed\n"
                    "  Rx {prescription_id} for patient {patient_id}: queued for retry"
                ),
            },
            7: {
                "name": "Patient Identity Match Failure",
                "subsystem": "clinical_records",
                "vehicle_section": "mpi_engine",
                "error_type": "EMPI-MATCH-FAIL",
                "sensor_type": "mpi_matcher",
                "affected_services": ["ehr-system", "patient-monitor"],
                "cascade_services": ["lab-integration", "pharmacy-system"],
                "description": "Master Patient Index fails to resolve patient identity, risking duplicate records",
                "investigation_notes": (
                    "Root Cause: EMPI probabilistic matching scores fall below threshold when patient demographics contain "
                    "discrepancies (name spelling variants, transposed DOB digits, SSN mismatches). The matching algorithm "
                    "(Jaro-Winkler + probabilistic weighting) requires tuning when registration workflows change.\n"
                    "Remediation: 1) Review the EMPI candidate match table for near-matches and manually adjudicate: "
                    "`empi-admin review-queue --mrn {mrn}`. 2) Check if the matching algorithm weights need adjustment: "
                    "`empi-admin config --show-weights`. 3) Run a patient index reconciliation report: "
                    "`empi-admin reconcile --facility FACILITY-01 --threshold 40`. "
                    "4) For confirmed duplicates, merge records via HIM worklist: `empi-admin merge --source MRN-DUPLICATE "
                    "--target MRN-PRIMARY --reason 'duplicate_registration'`. "
                    "5) Notify HIM (Health Information Management) department to review and finalize identity resolution. "
                    "6) Audit downstream systems (lab, pharmacy, billing) for orders linked to the duplicate MRN."
                ),
                "remediation_action": "reconcile_patient_index",
                "error_message": "[EHR] EMPI-MATCH-FAIL: mrn={mrn} encounter={encounter_id} score={match_score}% threshold={match_threshold}% action=REVIEW_REQUIRED",
                "stack_trace": (
                    "=== EMPI CANDIDATE MATCH TABLE ===\n"
                    "Query MRN: {mrn} | Encounter: {encounter_id}\n"
                    "Match Threshold: {match_threshold}% | Algorithm: Probabilistic\n"
                    "------------------------------------------------------------------------\n"
                    "CANDIDATE MRN | LAST     | FIRST  | DOB        | SSN-LAST4 | SCORE\n"
                    "------------------------------------------------------------------------\n"
                    "MRN-8832104   | DOE      | JANE   | 1965-03-15 | 4589      | {match_score}%\n"
                    "MRN-7741023   | DOE      | JANE M | 1965-03-15 | 4589      | 42.3%\n"
                    "MRN-6629817   | DOE      | JEAN   | 1965-04-15 | 4590      | 28.7%\n"
                    "------------------------------------------------------------------------\n"
                    "EMPI-MATCH-FAIL: Best score {match_score}% below {match_threshold}% threshold\n"
                    "Action: REVIEW_REQUIRED — potential duplicate for {mrn}\n"
                    "HIM worklist item created, manual identity resolution pending"
                ),
            },
            8: {
                "name": "Bed Management Sync Error",
                "subsystem": "scheduling",
                "vehicle_section": "bed_board",
                "error_type": "SCHED-BED-MGMT-FAIL",
                "sensor_type": "bed_tracker",
                "affected_services": ["scheduling-api", "ehr-system"],
                "cascade_services": ["clinical-alerts"],
                "description": "Bed management system loses synchronization with ADT events, showing stale census data",
                "investigation_notes": (
                    "Root Cause: The bed board receives ADT A01 (admit), A02 (transfer), and A03 (discharge) events via HL7 "
                    "interface. Sync lag occurs when the ADT feed queue backs up or the bed board API fails to process events "
                    "in order, causing census discrepancies between the bed board UI and actual patient locations.\n"
                    "Remediation: 1) Check the ADT-to-bed-board interface queue: `bed-admin queue-status --unit {nursing_unit}`. "
                    "2) Force a census resync from the ADT master: `bed-admin resync --unit {nursing_unit} --source ADT-MASTER`. "
                    "3) Restart the bed board sync service: `systemctl restart bed-management-sync`. "
                    "4) Verify the HL7 ADT listener port is accepting connections: `netstat -an | grep 2575`. "
                    "5) Manually update conflicting bed status via charge nurse console if patient safety is at risk. "
                    "6) Review the bed board event processing log for out-of-order sequence numbers."
                ),
                "remediation_action": "resync_bed_board",
                "error_message": "[SCHED] SCHED-BED-MGMT-FAIL: unit={nursing_unit} bed={bed_id} status={bed_status} adt_event={adt_event} sync_lag={sync_lag_seconds}s",
                "stack_trace": (
                    "=== BED BOARD STATUS — {nursing_unit} ===\n"
                    "Sync Lag: {sync_lag_seconds}s | Last ADT Event: {adt_event}\n"
                    "------------------------------------------------------------------------\n"
                    "BED       | BED-BOARD  | ADT-STATE  | PATIENT     | CONFLICT\n"
                    "------------------------------------------------------------------------\n"
                    "{bed_id}   | {bed_status:10s} | {adt_event:10s} | {patient_id}  | YES\n"
                    "A-102     | occupied   | occupied   | PT-443821   | NO\n"
                    "B-205     | vacant     | vacant     | --          | NO\n"
                    "C-310     | cleaning   | cleaning   | --          | NO\n"
                    "------------------------------------------------------------------------\n"
                    "SCHED-BED-MGMT-FAIL: Bed {bed_id} state mismatch detected\n"
                    "Bed board shows '{bed_status}' but ADT event '{adt_event}' received {sync_lag_seconds}s ago\n"
                    "Census accuracy degraded — patient placement at risk"
                ),
            },
            9: {
                "name": "Appointment Scheduling Conflict",
                "subsystem": "scheduling",
                "vehicle_section": "scheduler_core",
                "error_type": "SCHED-CONFLICT",
                "sensor_type": "appointment_scheduler",
                "affected_services": ["scheduling-api", "ehr-system"],
                "cascade_services": ["billing-processor"],
                "description": "Double-booking or resource conflict detected in appointment scheduling engine",
                "investigation_notes": (
                    "Root Cause: Scheduling conflicts arise from race conditions in the appointment booking engine when multiple "
                    "schedulers attempt to reserve the same provider/resource/time slot simultaneously. The optimistic locking "
                    "mechanism in the scheduling database fails under high concurrency during morning booking windows.\n"
                    "Remediation: 1) Review the conflicting bookings: `sched-admin conflicts --provider {provider_id} --date today`. "
                    "2) Release the conflicting slot lock: `sched-admin release-lock --slot {time_slot} --resource {resource_type}`. "
                    "3) Restart the scheduling conflict resolver: `systemctl restart scheduling-conflict-engine`. "
                    "4) Rebook the displaced patient into the next available slot: `sched-admin rebook --patient {patient_id} "
                    "--provider {provider_id} --type new-patient`. "
                    "5) Enable pessimistic locking for high-demand providers during peak booking hours. "
                    "6) Verify the scheduling database connection pool is not exhausted: `sched-admin db-pool-status`."
                ),
                "remediation_action": "resolve_scheduling_conflict",
                "error_message": "[SCHED] SCHED-CONFLICT: provider={provider_id} slot={time_slot} patient={patient_id} encounter={encounter_id} resource={resource_type}",
                "stack_trace": (
                    "=== SCHEDULING CONFLICT DETAIL ===\n"
                    "Provider: {provider_id} | Slot: {time_slot} | Resource: {resource_type}\n"
                    "------------------------------------------------------------------------\n"
                    "EXISTING BOOKING:\n"
                    "  Patient: PT-EXISTING | Encounter: ENC-887432 | Type: follow-up\n"
                    "  Booked: {time_slot} | Duration: 30min | Resource: {resource_type}\n"
                    "CONFLICTING REQUEST:\n"
                    "  Patient: {patient_id} | Encounter: {encounter_id} | Type: new-patient\n"
                    "  Requested: {time_slot} | Duration: 45min | Resource: {resource_type}\n"
                    "------------------------------------------------------------------------\n"
                    "SCHED-CONFLICT: Double-booking detected for provider {provider_id} at {time_slot}\n"
                    "Resource {resource_type} unavailable — patient {patient_id} requires rescheduling"
                ),
            },
            10: {
                "name": "Insurance Eligibility Check Timeout",
                "subsystem": "billing",
                "vehicle_section": "eligibility_gateway",
                "error_type": "X12-271-TIMEOUT",
                "sensor_type": "x12_270_271",
                "affected_services": ["billing-processor", "scheduling-api"],
                "cascade_services": ["ehr-system"],
                "description": "Real-time insurance eligibility verification via X12 270/271 transaction times out",
                "investigation_notes": (
                    "Root Cause: X12 270 eligibility inquiries timeout when the payer clearinghouse connection is degraded or the "
                    "payer's adjudication system is overloaded. Common during open enrollment periods or when a payer's real-time "
                    "eligibility API is undergoing maintenance. The ISA/GS envelope must match the payer's expected format.\n"
                    "Remediation: 1) Test payer connectivity: `x12-admin ping --payer {payer_id} --transaction 270`. "
                    "2) Check the clearinghouse status page for the payer (Availity, Change Healthcare, or Trizetto). "
                    "3) Reset the X12 gateway connection pool: `systemctl restart x12-eligibility-gateway`. "
                    "4) For timed-out requests, resubmit in batch mode: `x12-admin resubmit --insurance {insurance_id} --mode batch`. "
                    "5) Verify the ISA qualifier (ZZ) and receiver ID match the payer's enrollment records. "
                    "6) Fall back to manual eligibility verification via payer portal if real-time remains unavailable."
                ),
                "remediation_action": "reset_x12_gateway",
                "error_message": "[CLAIMS] X12-271-TIMEOUT: payer={payer_id} insurance={insurance_id} patient={patient_id} elapsed={elapsed_ms}ms timeout={timeout_ms}ms",
                "stack_trace": (
                    "--- X12 270/271 TRANSACTION TRACE ---\n"
                    ">>> 270 Eligibility Inquiry\n"
                    "ISA*00*          *00*          *ZZ*FACILITY-01    *ZZ*{payer_id}        *20260217143052*^*00501*000000001*0*P*:\n"
                    "GS*HS*FACILITY-01*{payer_id}*20260217143052*0001*X*005010X279A1\n"
                    "ST*270*0001*005010X279A1\n"
                    "BHT*0022*13*{insurance_id}*20260217143052\n"
                    "HL*1**20*1\n"
                    "NM1*PR*2*{payer_id}*****PI*{payer_id}\n"
                    "HL*2*1*21*1\n"
                    "NM1*IL*1*DOE*JANE****MI*{insurance_id}\n"
                    "SE*9*0001\n"
                    "<<< 271 Response — TIMEOUT\n"
                    "X12-271-TIMEOUT: No response from {payer_id} after {elapsed_ms}ms (limit: {timeout_ms}ms)\n"
                    "Patient: {patient_id} | Insurance: {insurance_id} | Queued for retry"
                ),
            },
            11: {
                "name": "Claims Processing Batch Failure",
                "subsystem": "billing",
                "vehicle_section": "claims_engine",
                "error_type": "X12-837-REJECT",
                "sensor_type": "x12_837",
                "affected_services": ["billing-processor", "data-warehouse"],
                "cascade_services": ["ehr-system", "scheduling-api"],
                "description": "Batch claims processing pipeline fails during X12 837 generation or submission",
                "investigation_notes": (
                    "Root Cause: X12 837 Professional/Institutional claim rejections are stage-specific. Validation-stage failures "
                    "indicate missing/invalid CLM segment data (DX codes, CPT codes, NPI). Submission-stage failures point to "
                    "clearinghouse connectivity or envelope (ISA/GS) formatting issues. Adjudication-stage rejections come from "
                    "payer business rules (timely filing, authorization requirements).\n"
                    "Remediation by stage: VALIDATION — run claim scrubber: `claims-admin scrub --batch {batch_id} --fix-codes`. "
                    "SUBMISSION — verify clearinghouse connection: `claims-admin ch-status --payer {payer_id}` and resubmit: "
                    "`claims-admin resubmit --batch {batch_id} --claims-only REJECTED`. "
                    "ADJUDICATION — review the 999/277 response for specific rejection reason codes and correct per payer guidelines. "
                    "General: 1) Reset the X12 837 gateway: `systemctl restart claims-submission-engine`. "
                    "2) Verify the 5010 companion guide for the rejecting payer is current. "
                    "3) Resubmit corrected claims: `claims-admin resubmit --batch {batch_id} --stage {claim_stage}`."
                ),
                "remediation_action": "resubmit_claims_batch",
                "error_message": "[CLAIMS] X12-837-REJECT: batch={batch_id} claim={claim_id} patient={patient_id} payer={payer_id} stage={claim_stage}",
                "stack_trace": (
                    "--- X12 837 CLAIM SUBMISSION TRACE ---\n"
                    ">>> 837 Professional Claim\n"
                    "ISA*00*          *00*          *ZZ*FACILITY-01    *ZZ*{payer_id}        *20260217143052*^*00501*000000001*0*P*:\n"
                    "GS*HC*FACILITY-01*{payer_id}*20260217143052*0001*X*005010X222A1\n"
                    "ST*837*0001*005010X222A1\n"
                    "BHT*0019*00*{batch_id}*20260217143052*CH\n"
                    "CLM*{claim_id}*5000***11:B:1*Y**A*Y*Y\n"
                    "NM1*IL*1*DOE*JANE****MI*{insurance_id}\n"
                    "SE*8*0001\n"
                    "<<< 999 Acknowledgment\n"
                    "  AK9*R*1*1*0\n"
                    "  IK3*CLM*4*2300*8\n"
                    "  IK4*2*782*7*{claim_stage}\n"
                    "X12-837-REJECT: Claim {claim_id} in batch {batch_id} rejected at {claim_stage}\n"
                    "Patient: {patient_id} | Payer: {payer_id} | Queued for correction"
                ),
            },
            12: {
                "name": "Surgical Schedule Conflict",
                "subsystem": "scheduling",
                "vehicle_section": "or_scheduler",
                "error_type": "SCHED-SURGICAL-CONFLICT",
                "sensor_type": "surgical_scheduler",
                "affected_services": ["scheduling-api", "ehr-system"],
                "cascade_services": ["billing-processor", "clinical-alerts"],
                "description": "Operating room scheduling conflict detected between overlapping surgical cases",
                "investigation_notes": (
                    "Root Cause: OR scheduling conflicts occur when the block schedule management system allows overlapping case "
                    "bookings due to stale cache data, surgeon preference card changes, or emergency add-on cases that override "
                    "the time-slot validation. Turnover time buffers may also be insufficient between consecutive cases.\n"
                    "Remediation: 1) Review the OR block schedule: `sched-admin or-blocks --room {or_number} --date today`. "
                    "2) Identify the conflict and reassign: `sched-admin or-reassign --case {case_id} --to-room NEXT-AVAILABLE`. "
                    "3) Verify surgeon block time ownership: `sched-admin surgeon-blocks --npi {surgeon_id}`. "
                    "4) Restart the OR scheduling engine: `systemctl restart or-scheduling-engine`. "
                    "5) Update turnover time buffers if consecutive cases are too tightly packed: `sched-admin set-turnover "
                    "--room {or_number} --minutes 45`. 6) Notify the surgical coordinator and anesthesia scheduling of the change."
                ),
                "remediation_action": "reassign_or_schedule",
                "error_message": "[SCHED] SCHED-SURGICAL-CONFLICT: or={or_number} case={case_id} surgeon={surgeon_id} conflict_time={conflict_time} patient={patient_id}",
                "stack_trace": (
                    "=== OR SCHEDULE BLOCK — {or_number} ===\n"
                    "------------------------------------------------------------------------\n"
                    "TIME      | CASE       | SURGEON         | PATIENT     | STATUS\n"
                    "------------------------------------------------------------------------\n"
                    "07:00     | SURG-44821 | NPI-1234567890  | PT-332145   | COMPLETED\n"
                    "09:30     | SURG-44822 | NPI-9876543210  | PT-445678   | IN-PROGRESS\n"
                    "{conflict_time}     | {case_id} | {surgeon_id} | {patient_id}  | CONFLICT\n"
                    "{conflict_time}     | SURG-EXIST | NPI-EXISTING   | PT-EXISTING | BOOKED\n"
                    "------------------------------------------------------------------------\n"
                    "SCHED-SURGICAL-CONFLICT: {or_number} at {conflict_time} — double-booked\n"
                    "Case {case_id} for surgeon {surgeon_id} overlaps with existing booking\n"
                    "Patient {patient_id} requires OR reassignment or time shift"
                ),
            },
            13: {
                "name": "Clinical Decision Support Overload",
                "subsystem": "alerting",
                "vehicle_section": "cds_engine",
                "error_type": "CDS-OVERLOAD",
                "sensor_type": "cds_rule_engine",
                "affected_services": ["clinical-alerts", "ehr-system"],
                "cascade_services": ["pharmacy-system", "patient-monitor"],
                "description": "Clinical decision support rule engine overloaded, unable to evaluate rules within SLA",
                "investigation_notes": (
                    "Root Cause: CDS rule engine overload occurs when complex rule sets (sepsis screening, VTE prophylaxis, fall "
                    "risk) are evaluated against large patient populations simultaneously, typically during shift change when "
                    "nursing assessments trigger bulk re-evaluations. The Arden Syntax MLM execution pool becomes saturated.\n"
                    "Remediation: 1) Check the CDS rule engine thread pool: `cds-admin pool-status --engine RULE-EVAL`. "
                    "2) Restart the CDS evaluation service: `systemctl restart cds-rule-engine`. "
                    "3) Prioritize critical rule sets: `cds-admin prioritize --ruleset sepsis-screening --level URGENT`. "
                    "4) Temporarily disable low-priority rule sets: `cds-admin disable --ruleset fall-risk --duration 30m`. "
                    "5) Scale the rule engine worker pool: `cds-admin scale-workers --count 8 --engine RULE-EVAL`. "
                    "6) Verify the patient context cache is not stale — flush if needed: `cds-admin cache-flush --scope patient-context`."
                ),
                "remediation_action": "restart_cds_engine",
                "error_message": "[CDS] CDS-OVERLOAD: rules_queued={pending_rules} eval_ms={eval_ms} threshold={max_eval_ms}ms patient={patient_id}",
                "stack_trace": (
                    "=== CDS RULE ENGINE STATUS ===\n"
                    "Patient Context: {patient_id}\n"
                    "Evaluation Time: {eval_ms}ms | SLA Threshold: {max_eval_ms}ms | STATUS: BREACHED\n"
                    "------------------------------------------------------------------------\n"
                    "RULE SET            | RULES | STATUS    | EVAL MS | RESULT\n"
                    "------------------------------------------------------------------------\n"
                    "Sepsis Screening    | 12    | TIMEOUT   | {eval_ms}   | INCOMPLETE\n"
                    "Drug Interaction    | 8     | QUEUED    | --      | PENDING\n"
                    "Fall Risk           | 5     | QUEUED    | --      | PENDING\n"
                    "VTE Prophylaxis     | 6     | QUEUED    | --      | PENDING\n"
                    "------------------------------------------------------------------------\n"
                    "Total Pending: {pending_rules} rules | Queue Depth: SATURATED\n"
                    "CDS-OVERLOAD: Evaluation backlog — {pending_rules} rules queued, {eval_ms}ms exceeds {max_eval_ms}ms SLA\n"
                    "Clinical alerts for {patient_id} delayed — escalation required"
                ),
            },
            14: {
                "name": "Nurse Call System Integration Failure",
                "subsystem": "alerting",
                "vehicle_section": "nurse_call_bridge",
                "error_type": "NURSE-CALL-STORM",
                "sensor_type": "nurse_call_interface",
                "affected_services": ["clinical-alerts", "patient-monitor"],
                "cascade_services": ["ehr-system"],
                "description": "Integration bridge between nurse call system and EHR loses connectivity",
                "investigation_notes": (
                    "Root Cause: The nurse call system (Hill-Rom/Rauland) integration bridge communicates with the EHR via a "
                    "middleware TCP socket. Bridge failures cause call events to queue without EHR documentation, leading to "
                    "undelivered notifications and potential patient safety events. Emergency calls default to overhead paging.\n"
                    "Remediation: 1) Check the nurse call bridge connectivity: `ncs-admin bridge-status --station {station_id}`. "
                    "2) Restart the EHR-NCS bridge service: `systemctl restart ehr-nursecall-bridge`. "
                    "3) Verify the TCP socket connection to the nurse call server: `ncs-admin test-connection --host ncs-server "
                    "--port 3001`. 4) Clear the undelivered call queue: `ncs-admin flush-queue --unit {nursing_unit}`. "
                    "5) Confirm overhead paging failover is active for emergency and code calls. "
                    "6) Review the call escalation timers — ensure STAT calls escalate to charge nurse after 60s unacknowledged."
                ),
                "remediation_action": "restart_nursecall_bridge",
                "error_message": "[CDS] NURSE-CALL-STORM: station={station_id} unit={nursing_unit} bed={bed_id} call_type={call_type} undelivered={undelivered_seconds}s",
                "stack_trace": (
                    "=== NURSE CALL SYSTEM STATUS — {nursing_unit} ===\n"
                    "Station: {station_id} | Bridge: EHR-NCS-BRIDGE-01 | Status: DEGRADED\n"
                    "------------------------------------------------------------------------\n"
                    "BED       | CALL TYPE       | INITIATED   | DELIVERED | WAIT (s)\n"
                    "------------------------------------------------------------------------\n"
                    "{bed_id}   | {call_type:15s} | 20260217143052 | PENDING   | {undelivered_seconds}\n"
                    "B-208     | routine         | 20260217143052 | PENDING   | 45\n"
                    "C-312     | bathroom        | 20260217143052 | YES       | 0\n"
                    "------------------------------------------------------------------------\n"
                    "NURSE-CALL-STORM: {station_id} — {call_type} call from bed {bed_id} undelivered for {undelivered_seconds}s\n"
                    "EHR bridge connectivity degraded on {nursing_unit}\n"
                    "Failover to overhead paging initiated"
                ),
            },
            15: {
                "name": "Blood Bank Inventory Sync Error",
                "subsystem": "laboratory",
                "vehicle_section": "blood_bank_interface",
                "error_type": "BB-INVENTORY-SYNC",
                "sensor_type": "blood_bank_inventory",
                "affected_services": ["lab-integration", "clinical-alerts"],
                "cascade_services": ["ehr-system", "scheduling-api"],
                "description": "Blood bank inventory management system loses sync with transfusion service records",
                "investigation_notes": (
                    "Root Cause: Blood bank inventory discrepancies arise when the ISBT 128-coded product tracking system loses "
                    "sync with the transfusion service module — typically after manual dispensing without barcode scanning, "
                    "product expiration dispositions not recorded, or crossmatch cancellations not propagated back.\n"
                    "Remediation: 1) Initiate a physical recount per blood bank SOP: `bb-admin recount --product {blood_product} "
                    "--type {blood_type}`. 2) Check the ISBT barcode scanner interface: `bb-admin scanner-status --station all`. "
                    "3) Reconcile system inventory with physical counts: `bb-admin reconcile --auto-adjust --audit-trail`. "
                    "4) Review the crossmatch pending list for unreturned units: `bb-admin crossmatch-pending --older-than 4h`. "
                    "5) Restart the blood bank inventory sync service: `systemctl restart bb-inventory-sync`. "
                    "6) Notify the blood bank medical director if discrepancy exceeds 2 units per AABB standards."
                ),
                "remediation_action": "reconcile_blood_bank",
                "error_message": "[LIS] BB-INVENTORY-SYNC: product={blood_product} type={blood_type} on_hand={units_on_hand} system={system_count} discrepancy={discrepancy}",
                "stack_trace": (
                    "=== BLOOD BANK INVENTORY RECONCILIATION ===\n"
                    "Reconciliation Time: 20260217143052\n"
                    "------------------------------------------------------------------------\n"
                    "PRODUCT         | TYPE | PHYSICAL | SYSTEM | DISCREPANCY | STATUS\n"
                    "------------------------------------------------------------------------\n"
                    "{blood_product:15s} | {blood_type:4s} | {units_on_hand:8d} | {system_count:6d} | {discrepancy:11d} | MISMATCH\n"
                    "PRBC            | O-   | 12       | 12     | 0           | OK\n"
                    "FFP             | AB+  | 8        | 8      | 0           | OK\n"
                    "Platelets       | O+   | 6        | 6      | 0           | OK\n"
                    "------------------------------------------------------------------------\n"
                    "BB-INVENTORY-SYNC: {blood_product} {blood_type} — physical count {units_on_hand} vs system {system_count}\n"
                    "Discrepancy of {discrepancy} units detected — transfusion service notified\n"
                    "Manual physical recount required per blood bank SOP"
                ),
            },
            16: {
                "name": "PACS Storage Capacity Warning",
                "subsystem": "radiology",
                "vehicle_section": "pacs_storage",
                "error_type": "PACS-CAPACITY-CRITICAL",
                "sensor_type": "storage_monitor",
                "affected_services": ["imaging-service", "data-warehouse"],
                "cascade_services": ["clinical-alerts", "ehr-system"],
                "description": "PACS archive storage capacity approaching critical threshold, risking image loss",
                "investigation_notes": (
                    "Root Cause: PACS storage volumes fill when DICOM image retention policies are not enforced, modality worklists "
                    "generate excessive preliminary/secondary capture images, or archive migration jobs to long-term storage (VNA) "
                    "have stalled. High-resolution modalities (CT, MRI) consume 500MB-2GB per study.\n"
                    "Remediation: 1) Check the archive migration job status: `pacs-admin archive-status --volume {volume_id}`. "
                    "2) Trigger emergency archive migration to VNA: `pacs-admin migrate --volume {volume_id} --older-than 90d "
                    "--destination VNA-TIER2`. 3) Identify and purge orphaned DICOM objects: `pacs-admin cleanup --volume "
                    "{volume_id} --orphans-only`. 4) Expand the volume if migration is insufficient: `pacs-admin volume-expand "
                    "--volume {volume_id} --add-tb 10`. 5) Review retention policies per radiology department guidelines. "
                    "6) Enable DICOM compression (JPEG2000 lossless) for new studies to reduce storage consumption."
                ),
                "remediation_action": "expand_pacs_storage",
                "error_message": "[PACS] PACS-CAPACITY-CRITICAL: volume={volume_id} usage={usage_pct}% threshold={threshold_pct}% remaining={remaining_gb}GB",
                "stack_trace": (
                    "=== PACS STORAGE VOLUME REPORT ===\n"
                    "------------------------------------------------------------------------\n"
                    "VOLUME          | TOTAL TB | USED TB | FREE GB | USAGE% | STATUS\n"
                    "------------------------------------------------------------------------\n"
                    "{volume_id:15s} | 50.0     | {usage_pct}%  | {remaining_gb}    | {usage_pct}%  | CRITICAL\n"
                    "PACS-VOL-02     | 50.0     | 72.3%   | 13850   | 72.3%  | OK\n"
                    "PACS-ARCHIVE-01 | 200.0    | 65.1%   | 69800   | 65.1%  | OK\n"
                    "------------------------------------------------------------------------\n"
                    "PACS-CAPACITY-CRITICAL: {volume_id} at {usage_pct}% (threshold: {threshold_pct}%)\n"
                    "Remaining: {remaining_gb}GB — estimated time to full: <48 hours\n"
                    "Action required: archive migration or volume expansion"
                ),
            },
            17: {
                "name": "ADT Feed Synchronization Gap",
                "subsystem": "clinical_records",
                "vehicle_section": "adt_interface",
                "error_type": "ADT-SYNC-FAIL",
                "sensor_type": "adt_feed",
                "affected_services": ["ehr-system", "scheduling-api"],
                "cascade_services": ["patient-monitor", "billing-processor", "lab-integration"],
                "description": "ADT (Admit-Discharge-Transfer) event feed falls behind, causing stale patient location data",
                "investigation_notes": (
                    "Root Cause: ADT feed synchronization gaps occur when the HL7 ADT event processor cannot keep pace with "
                    "admission/discharge/transfer volume — common during high-census periods, mass casualty events, or when the "
                    "receiving interface engine (Mirth/Rhapsody) has a thread pool exhaustion issue.\n"
                    "Remediation: 1) Restart the ADT feed processor: `adt-admin restart-feed --feed {feed_id}`. "
                    "2) Check the ADT event queue depth and drain rate: `adt-admin queue-status --feed {feed_id} --verbose`. "
                    "3) Run a patient index reconciliation against the ADT master: `adt-admin reconcile --feed {feed_id} "
                    "--source ADT-MASTER --mode FULL`. 4) Flush the dead-letter queue for unprocessable events: "
                    "`adt-admin flush-dlq --feed {feed_id} --requeue-valid`. "
                    "5) Verify downstream consumers (bed board, billing, lab) are receiving events: `adt-admin subscriber-status`. "
                    "6) Scale the ADT processor thread pool: `adt-admin scale-threads --feed {feed_id} --count 8`."
                ),
                "remediation_action": "restart_adt_feed",
                "error_message": "[EHR] ADT-SYNC-FAIL: feed={feed_id} lag={gap_seconds}s queue_depth={queue_depth} patient={patient_id} event={adt_event_type}",
                "stack_trace": (
                    "=== ADT FEED STATUS — {feed_id} ===\n"
                    "Feed Lag: {gap_seconds}s | Queue Depth: {queue_depth} | Threshold: 30s\n"
                    "------------------------------------------------------------------------\n"
                    "SEQ    | EVENT | PATIENT     | TIMESTAMP   | STATUS\n"
                    "------------------------------------------------------------------------\n"
                    "001247 | {adt_event_type}    | {patient_id}  | 20260217143052 | QUEUED\n"
                    "001246 | A08   | PT-887432   | 20260217143052 | QUEUED\n"
                    "001245 | A03   | PT-556201   | 20260217143052 | QUEUED\n"
                    "001244 | A01   | PT-334789   | 20260217143052 | DELIVERED\n"
                    "------------------------------------------------------------------------\n"
                    "ADT-SYNC-FAIL: {feed_id} lagging {gap_seconds}s with {queue_depth} events queued\n"
                    "Patient {patient_id} event {adt_event_type} pending delivery\n"
                    "Downstream systems receiving stale location data"
                ),
            },
            18: {
                "name": "Data Warehouse ETL Pipeline Stall",
                "subsystem": "analytics",
                "vehicle_section": "etl_pipeline",
                "error_type": "ETL-PIPELINE-STALL",
                "sensor_type": "etl_monitor",
                "affected_services": ["data-warehouse", "billing-processor"],
                "cascade_services": ["ehr-system"],
                "description": "Clinical data warehouse ETL pipeline stalls during extraction or transformation phase",
                "investigation_notes": (
                    "Root Cause: ETL pipeline stalls are caused by source database connection pool exhaustion, long-running "
                    "transformation queries locking clinical tables, or target warehouse staging area disk full conditions. "
                    "Extract-phase stalls often indicate the source EHR database is under heavy OLTP load during clinical hours.\n"
                    "Remediation: 1) Check the ETL job status: `etl-admin pipeline-status --pipeline {pipeline_id}`. "
                    "2) Restart the stalled pipeline stage: `etl-admin restart-stage --pipeline {pipeline_id} --stage {etl_stage}`. "
                    "3) Verify source database connectivity: `etl-admin test-source --pipeline {pipeline_id}`. "
                    "4) Check for blocking queries on the source: `etl-admin blocking-queries --pipeline {pipeline_id}`. "
                    "5) If the target staging area is full, expand or purge: `etl-admin staging-cleanup --pipeline {pipeline_id} "
                    "--older-than 7d`. 6) Reschedule extract-phase jobs to off-peak hours (02:00-05:00) to avoid OLTP contention."
                ),
                "remediation_action": "restart_etl_pipeline",
                "error_message": "[DW] ETL-PIPELINE-STALL: pipeline={pipeline_id} stage={etl_stage} rows={rows_processed}/{total_rows} stalled={stall_seconds}s",
                "stack_trace": (
                    "=== ETL PIPELINE STATUS REPORT ===\n"
                    "------------------------------------------------------------------------\n"
                    "PIPELINE        | STAGE     | ROWS DONE   | TOTAL ROWS  | STALL(s) | STATUS\n"
                    "------------------------------------------------------------------------\n"
                    "{pipeline_id} | {etl_stage:9s} | {rows_processed:11d} | {total_rows:11d} | {stall_seconds:8d} | STALLED\n"
                    "ETL-BILLING-02  | load      | 1200000     | 1200000     | 0        | COMPLETE\n"
                    "ETL-LAB-03      | transform | 450000      | 800000      | 0        | RUNNING\n"
                    "ETL-QUALITY-04  | extract   | 0           | 500000      | 0        | QUEUED\n"
                    "------------------------------------------------------------------------\n"
                    "ETL-PIPELINE-STALL: {pipeline_id} stalled at {etl_stage} for {stall_seconds}s\n"
                    "Progress: {rows_processed}/{total_rows} rows — no advancement detected\n"
                    "Source connection pool may be exhausted — DBA review recommended"
                ),
            },
            19: {
                "name": "DICOM Transfer Failure",
                "subsystem": "radiology",
                "vehicle_section": "pacs_gateway",
                "error_type": "DICOM-STORE-FAIL",
                "sensor_type": "dicom_transfer",
                "affected_services": ["imaging-service", "ehr-system"],
                "cascade_services": ["clinical-alerts", "data-warehouse"],
                "description": "DICOM C-STORE or C-MOVE operation fails during modality-to-PACS image transfer",
                "investigation_notes": (
                    "Root Cause: DICOM association failures (status 0xA700/0xA900) indicate either AE title mismatch, transfer "
                    "syntax negotiation failure, or storage commitment refusal. The PACS SCP rejects the C-STORE when the "
                    "Presentation Context (Abstract Syntax + Transfer Syntax) is not in the accepted list.\n"
                    "Remediation: 1) Verify the DICOM association: `dcm4che-tool storescu --called PACS-SCP-01 --calling {modality}-SCU "
                    "--connect pacs-host:11112 --cecho`. 2) Reset the DICOM association: `pacs-admin reset-association --ae-title "
                    "{modality}-SCU`. 3) Check the PACS gateway connection pool: `pacs-admin gateway-status`. "
                    "4) If persistent, restart the PACS gateway service: `systemctl restart dcm4chee-arc`. "
                    "5) Verify transfer syntax compatibility — ensure Explicit VR Little Endian (1.2.840.10008.1.2.1) is configured. "
                    "6) For C-MOVE failures, verify the destination AE title is registered in the DICOM configuration."
                ),
                "remediation_action": "restart_pacs_gateway",
                "error_message": "[PACS] DICOM-STORE-FAIL: study={dicom_study_uid} modality={modality} operation={dicom_operation} status={dicom_error_code}",
                "stack_trace": (
                    "A-ASSOCIATE-RQ PDU\n"
                    "  Called AE Title:  PACS-SCP-01\n"
                    "  Calling AE Title: {modality}-SCU\n"
                    "  Application Context: 1.2.840.10008.3.1.1.1\n"
                    "  Presentation Context:\n"
                    "    Abstract Syntax: 1.2.840.10008.5.1.4.1.1.2 ({modality} Image Storage)\n"
                    "    Transfer Syntax: 1.2.840.10008.1.2.1 (Explicit VR Little Endian)\n"
                    "A-ASSOCIATE-AC — Association accepted\n"
                    "{dicom_operation}-RQ | Study: {dicom_study_uid} | Series: 1 of 3\n"
                    "{dicom_operation}-RSP | Status: {dicom_error_code} | FAILURE\n"
                    "  Error Comment: DICOM-STORE-FAIL — Storage commitment refused, dataset mismatch\n"
                    "  Affected SOP Instance: {dicom_study_uid}.1.1\n"
                    "A-RELEASE-RQ\n"
                    "A-RELEASE-RP — Association released"
                ),
            },
            20: {
                "name": "Telehealth Session Quality Degradation",
                "subsystem": "vital_signs",
                "vehicle_section": "telehealth_engine",
                "error_type": "TELEHEALTH-QOS-DEGRAD",
                "sensor_type": "telehealth_qos",
                "affected_services": ["patient-monitor", "clinical-alerts"],
                "cascade_services": ["ehr-system", "scheduling-api"],
                "description": "Telehealth video session quality degrades below clinical acceptability threshold",
                "investigation_notes": (
                    "Root Cause: WebRTC session quality degradation is caused by network congestion (packet loss >2%), insufficient "
                    "bandwidth (<750kbps for clinical-grade video), or TURN server overload. Clinical telehealth requires higher "
                    "QoS than standard video conferencing — remote physical examinations need >24fps at 720p minimum.\n"
                    "Remediation: 1) Check the TURN/STUN server status: `telehealth-admin server-status --session {session_id}`. "
                    "2) Reset the media relay for the session: `telehealth-admin reset-relay --session {session_id}`. "
                    "3) Switch to a lower-latency TURN region: `telehealth-admin switch-region --session {session_id} --region closest`. "
                    "4) If bandwidth is insufficient, downgrade to audio-only with screen share: `telehealth-admin set-mode "
                    "--session {session_id} --mode audio-plus-share`. "
                    "5) Check the patient's network quality: `telehealth-admin client-diagnostics --session {session_id}`. "
                    "6) If persistent, reschedule as in-person visit: `sched-admin convert-to-inperson --session {session_id}`."
                ),
                "remediation_action": "reset_telehealth_relay",
                "error_message": "[MONITOR] TELEHEALTH-QOS-DEGRAD: session={session_id} patient={patient_id} bitrate={bitrate_kbps}kbps loss={packet_loss_pct}% latency={latency_ms}ms",
                "stack_trace": (
                    "=== WEBRTC QUALITY METRICS — SESSION {session_id} ===\n"
                    "Patient: {patient_id} | Provider: NPI-ATTENDING\n"
                    "------------------------------------------------------------------------\n"
                    "METRIC              | VALUE          | THRESHOLD     | STATUS\n"
                    "------------------------------------------------------------------------\n"
                    "Video Bitrate       | {bitrate_kbps} kbps    | >750 kbps     | DEGRADED\n"
                    "Packet Loss         | {packet_loss_pct}%         | <2.0%         | CRITICAL\n"
                    "Round-Trip Latency  | {latency_ms} ms       | <300 ms       | DEGRADED\n"
                    "Jitter              | 45 ms          | <30 ms        | WARNING\n"
                    "Frame Rate          | 12 fps         | >24 fps       | DEGRADED\n"
                    "Audio MOS           | 2.8            | >3.5          | WARNING\n"
                    "------------------------------------------------------------------------\n"
                    "TELEHEALTH-QOS-DEGRAD: Session {session_id} below clinical acceptability\n"
                    "Video quality insufficient for remote physical examination\n"
                    "Recommendation: Switch to audio-only or reschedule in-person visit"
                ),
            },
        }

    # -- Topology ---------------------------------------------------------------

    @property
    def service_topology(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "ehr-system": [
                ("lab-integration", "/api/v1/lab/orders", "POST"),
                ("lab-integration", "/api/v1/lab/results", "GET"),
                ("pharmacy-system", "/api/v1/pharmacy/orders", "POST"),
                ("pharmacy-system", "/api/v1/pharmacy/verify", "GET"),
                ("imaging-service", "/api/v1/imaging/orders", "POST"),
                ("scheduling-api", "/api/v1/schedule/appointments", "GET"),
                ("billing-processor", "/api/v1/billing/charges", "POST"),
                ("clinical-alerts", "/api/v1/alerts/patient", "GET"),
            ],
            "patient-monitor": [
                ("ehr-system", "/api/v1/ehr/vitals", "POST"),
                ("clinical-alerts", "/api/v1/alerts/vital-signs", "POST"),
            ],
            "lab-integration": [
                ("ehr-system", "/api/v1/ehr/results", "POST"),
                ("clinical-alerts", "/api/v1/alerts/critical-lab", "POST"),
            ],
            "pharmacy-system": [
                ("ehr-system", "/api/v1/ehr/medication-admin", "POST"),
                ("clinical-alerts", "/api/v1/alerts/drug-interaction", "POST"),
            ],
            "imaging-service": [
                ("ehr-system", "/api/v1/ehr/imaging-results", "POST"),
                ("data-warehouse", "/api/v1/warehouse/imaging-archive", "POST"),
            ],
            "scheduling-api": [
                ("ehr-system", "/api/v1/ehr/encounter", "POST"),
                ("billing-processor", "/api/v1/billing/encounter-charges", "POST"),
            ],
            "billing-processor": [
                ("data-warehouse", "/api/v1/warehouse/claims", "POST"),
            ],
            "clinical-alerts": [
                ("ehr-system", "/api/v1/ehr/alert-response", "POST"),
            ],
        }

    @property
    def entry_endpoints(self) -> dict[str, list[tuple[str, str]]]:
        return {
            "ehr-system": [
                ("/api/v1/ehr/patient", "GET"),
                ("/api/v1/ehr/encounter", "POST"),
                ("/api/v1/ehr/clinical-notes", "POST"),
            ],
            "patient-monitor": [("/api/v1/vitals/stream", "POST")],
            "lab-integration": [("/api/v1/lab/submit", "POST")],
            "pharmacy-system": [("/api/v1/pharmacy/dispense", "POST")],
            "imaging-service": [("/api/v1/imaging/study", "POST")],
            "scheduling-api": [("/api/v1/schedule/book", "POST")],
            "billing-processor": [("/api/v1/billing/submit-claim", "POST")],
            "clinical-alerts": [("/api/v1/alerts/evaluate", "POST")],
            "data-warehouse": [("/api/v1/warehouse/etl-trigger", "POST")],
        }

    @property
    def db_operations(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "ehr-system": [
                ("SELECT", "patient_demographics", "SELECT * FROM patient_demographics WHERE mrn = ? AND facility_id = ?"),
                ("INSERT", "clinical_encounters", "INSERT INTO clinical_encounters (patient_id, encounter_type, admit_dt, provider_id) VALUES (?, ?, NOW(), ?)"),
                ("UPDATE", "patient_chart", "UPDATE patient_chart SET last_modified = NOW(), modified_by = ? WHERE patient_id = ?"),
            ],
            "patient-monitor": [
                ("INSERT", "vital_readings", "INSERT INTO vital_readings (patient_id, hr, bp_sys, bp_dia, spo2, temp, rr, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, NOW())"),
                ("SELECT", "alert_thresholds", "SELECT threshold_type, min_val, max_val FROM alert_thresholds WHERE unit_id = ? AND active = 1"),
            ],
            "lab-integration": [
                ("SELECT", "lab_orders", "SELECT order_id, test_code, priority, status FROM lab_orders WHERE patient_id = ? AND status IN ('pending', 'in-progress')"),
                ("INSERT", "lab_results", "INSERT INTO lab_results (order_id, test_code, value, unit, reference_range, abnormal_flag) VALUES (?, ?, ?, ?, ?, ?)"),
            ],
            "pharmacy-system": [
                ("SELECT", "medication_orders", "SELECT rx_id, drug_code, dose, route, frequency FROM medication_orders WHERE patient_id = ? AND status = 'active'"),
                ("SELECT", "drug_interactions", "SELECT drug_a, drug_b, severity, description FROM drug_interactions WHERE drug_a IN (?) OR drug_b IN (?)"),
            ],
            "billing-processor": [
                ("SELECT", "claim_submissions", "SELECT claim_id, payer_id, total_charges, status FROM claim_submissions WHERE batch_id = ? ORDER BY created_at"),
                ("INSERT", "claim_submissions", "INSERT INTO claim_submissions (encounter_id, payer_id, total_charges, dx_codes, cpt_codes) VALUES (?, ?, ?, ?, ?)"),
            ],
            "data-warehouse": [
                ("SELECT", "etl_pipeline_status", "SELECT pipeline_id, stage, rows_processed, total_rows, started_at FROM etl_pipeline_status WHERE status = 'running'"),
            ],
        }

    # -- Infrastructure ---------------------------------------------------------

    @property
    def hosts(self) -> list[dict[str, Any]]:
        return [
            {
                "host.name": "healthcare-aws-host-01",
                "host.id": "i-0h1c2a3l4t5h67890",
                "host.arch": "amd64",
                "host.type": "m5.xlarge",
                "host.image.id": "ami-0healthcare12345a",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8175M CPU @ 2.50GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "4",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.0.2.50", "172.16.1.10"],
                "host.mac": ["0a:2b:3c:4d:5e:6f", "0a:2b:3c:4d:5e:70"],
                "os.type": "linux",
                "os.description": "Amazon Linux 2023.6.20250115",
                "cloud.provider": "aws",
                "cloud.platform": "aws_ec2",
                "cloud.region": "us-east-1",
                "cloud.availability_zone": "us-east-1a",
                "cloud.account.id": "234567890123",
                "cloud.instance.id": "i-0h1c2a3l4t5h67890",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 200 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "healthcare-gcp-host-01",
                "host.id": "6738912345678901234",
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
                "host.mac": ["42:01:0a:81:01:14", "42:01:0a:81:01:15"],
                "os.type": "linux",
                "os.description": "Debian GNU/Linux 12 (bookworm)",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "us-central1",
                "cloud.availability_zone": "us-central1-a",
                "cloud.account.id": "healthcare-project-prod",
                "cloud.instance.id": "6738912345678901234",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 100 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "healthcare-azure-host-01",
                "host.id": "/subscriptions/hca-def/resourceGroups/healthcare-rg/providers/Microsoft.Compute/virtualMachines/healthcare-vm-01",
                "host.arch": "amd64",
                "host.type": "Standard_D4s_v3",
                "host.image.id": "Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "106",
                "host.cpu.stepping": "6",
                "host.cpu.cache.l2.size": 1310720,
                "host.ip": ["10.2.0.4", "10.2.0.5"],
                "host.mac": ["00:0d:3a:6b:5c:4d", "00:0d:3a:6b:5c:4e"],
                "os.type": "linux",
                "os.description": "Ubuntu 22.04.5 LTS",
                "cloud.provider": "azure",
                "cloud.platform": "azure_vm",
                "cloud.region": "eastus",
                "cloud.availability_zone": "eastus-1",
                "cloud.account.id": "hca-def-ghi-jkl",
                "cloud.instance.id": "healthcare-vm-01",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 128 * 1024 * 1024 * 1024,
            },
        ]

    @property
    def k8s_clusters(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "healthcare-eks-cluster",
                "provider": "aws",
                "platform": "aws_eks",
                "region": "us-east-1",
                "zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
                "os_description": "Amazon Linux 2",
                "services": ["ehr-system", "patient-monitor", "lab-integration"],
            },
            {
                "name": "healthcare-gke-cluster",
                "provider": "gcp",
                "platform": "gcp_gke",
                "region": "us-central1",
                "zones": ["us-central1-a", "us-central1-b", "us-central1-c"],
                "os_description": "Container-Optimized OS",
                "services": ["pharmacy-system", "imaging-service", "scheduling-api"],
            },
            {
                "name": "healthcare-aks-cluster",
                "provider": "azure",
                "platform": "azure_aks",
                "region": "eastus",
                "zones": ["eastus-1", "eastus-2", "eastus-3"],
                "os_description": "Ubuntu 22.04 LTS",
                "services": ["billing-processor", "clinical-alerts", "data-warehouse"],
            },
        ]

    # -- Theme ------------------------------------------------------------------

    @property
    def theme(self) -> UITheme:
        return UITheme(
            bg_primary="#f5f5f5",
            bg_secondary="#ffffff",
            bg_tertiary="#e8e8e8",
            accent_primary="#00796b",
            accent_secondary="#004d40",
            text_primary="#212121",
            text_secondary="#757575",
            text_accent="#00796b",
            status_nominal="#2e7d32",
            status_warning="#f9a825",
            status_critical="#c62828",
            status_info="#1565c0",
            font_family="'Inter', system-ui, sans-serif",
            font_mono="'JetBrains Mono', 'Fira Code', monospace",
            chaos_title="System Disruption Simulator",
            service_label="Service",
            channel_label="Channel",
        )

    @property
    def countdown_config(self) -> CountdownConfig:
        return CountdownConfig(enabled=False)

    # -- Agent Config -----------------------------------------------------------

    @property
    def agent_config(self) -> dict[str, Any]:
        return {
            "id": "healthcare-clinical-analyst",
            "name": "Clinical Systems Analyst",
            "assessment_tool_name": "patient_safety_assessment",
            "system_prompt": (
                "You are the Clinical Systems Analyst, an expert AI assistant for "
                "hospital clinical operations. You help IT operations teams investigate "
                "system anomalies, analyze integration failures, and provide root cause "
                "analysis for fault conditions across 9 clinical systems spanning "
                "AWS, GCP, and Azure. "
                "You have deep expertise in HL7 v2.x ADT/ORM/ORU messaging, DICOM "
                "C-STORE/C-MOVE/C-FIND protocols, NCPDP SCRIPT e-prescribing, X12 "
                "270/271 eligibility and 837 claims transactions, ASTM laboratory "
                "interfaces, clinical decision support (CDS) rule engines, HIPAA "
                "audit compliance, and healthcare ETL pipelines. "
                "When investigating incidents, search for these system identifiers in logs: "
                "EHR faults (HL7-ACK-AE, EMPI-MATCH-FAIL, ADT-SYNC-FAIL), "
                "Vital Signs faults (VITAL-ALERT-STORM, TELEHEALTH-QOS-DEGRAD), "
                "Laboratory faults (LIS-RESULT-DELAY, BB-INVENTORY-SYNC), "
                "Radiology faults (DICOM-STORE-FAIL, PACS-CAPACITY-CRITICAL), "
                "Medication faults (CPOE-DDI-CRITICAL, NCPDP-SCRIPT-FAIL), "
                "Scheduling faults (SCHED-BED-MGMT-FAIL, SCHED-CONFLICT, SCHED-SURGICAL-CONFLICT), "
                "Billing faults (X12-271-TIMEOUT, X12-837-REJECT), "
                "Alerting faults (CDS-OVERLOAD, NURSE-CALL-STORM), "
                "and Analytics faults (ETL-PIPELINE-STALL, HIPAA-AUDIT-FAIL). "
                "Log messages are in body.text — NEVER search the body field alone."
            ),
        }

    @property
    def assessment_tool_config(self) -> dict[str, Any]:
        return {
            "id": "patient_safety_assessment",
            "description": (
                "Comprehensive patient safety assessment. Evaluates all "
                "clinical systems against operational health criteria for patient care "
                "continuity. Returns data for safety evaluation across EHR, patient "
                "monitoring, laboratory, pharmacy, and imaging systems. "
                "Log message field: body.text (never use 'body' alone)."
            ),
        }

    @property
    def knowledge_base_docs(self) -> list[dict[str, Any]]:
        return []  # Populated by deployer from channel_registry

    # -- Service Classes --------------------------------------------------------

    def get_service_classes(self) -> list[type]:
        from scenarios.healthcare.services.ehr_system import EHRSystemService
        from scenarios.healthcare.services.patient_monitor import PatientMonitorService
        from scenarios.healthcare.services.lab_integration import LabIntegrationService
        from scenarios.healthcare.services.pharmacy_system import PharmacySystemService
        from scenarios.healthcare.services.imaging_service import ImagingServiceService
        from scenarios.healthcare.services.scheduling_api import SchedulingAPIService
        from scenarios.healthcare.services.billing_processor import BillingProcessorService
        from scenarios.healthcare.services.clinical_alerts import ClinicalAlertsService
        from scenarios.healthcare.services.data_warehouse import DataWarehouseService

        return [
            EHRSystemService,
            PatientMonitorService,
            LabIntegrationService,
            PharmacySystemService,
            ImagingServiceService,
            SchedulingAPIService,
            BillingProcessorService,
            ClinicalAlertsService,
            DataWarehouseService,
        ]

    # -- Trace Attributes & RCA -------------------------------------------------

    def get_trace_attributes(self, service_name: str, rng) -> dict:
        hour = int(time.time()) % 86400 // 3600
        if hour < 7:
            shift = "night"
        elif hour < 15:
            shift = "day"
        else:
            shift = "evening"
        base = {
            "hospital.wing": rng.choice(["East", "West", "North", "South", "Central"]),
            "hospital.shift": shift,
        }
        svc_attrs = {
            "ehr-system": {
                "patient.acuity_level": rng.choice([1, 2, 3, 4, 5]),
                "patient.department": rng.choice(["Emergency", "ICU", "MedSurg", "Oncology", "Pediatrics", "Cardiology"]),
            },
            "patient-monitor": {
                "vitals.sampling_rate_hz": rng.choice([1, 2, 5, 10]),
                "vitals.bed_id": f"{rng.choice(['A', 'B', 'C', 'D'])}-{rng.randint(101, 450)}",
            },
            "lab-integration": {
                "lab.specimen_type": rng.choice(["serum", "plasma", "whole_blood", "urine", "csf", "tissue"]),
                "lab.turnaround_min": rng.randint(15, 120),
            },
            "pharmacy-system": {
                "pharmacy.medication_class": rng.choice(["antibiotic", "anticoagulant", "analgesic", "antihypertensive", "vasopressor", "sedative"]),
                "pharmacy.interaction_score": round(rng.uniform(0.0, 10.0), 1),
            },
            "imaging-service": {
                "imaging.modality": rng.choice(["CT", "MRI", "XR", "US", "MG", "NM", "PET"]),
                "imaging.study_priority": rng.choice(["STAT", "URGENT", "ROUTINE", "ELECTIVE"]),
            },
            "scheduling-api": {
                "scheduling.appointment_type": rng.choice(["new_patient", "follow_up", "procedure", "consult", "telehealth"]),
                "scheduling.provider_load": rng.randint(4, 24),
            },
            "billing-processor": {
                "billing.claim_type": rng.choice(["professional", "institutional", "dental", "pharmacy"]),
                "billing.payer_category": rng.choice(["commercial", "medicare", "medicaid", "tricare", "self_pay"]),
            },
            "clinical-alerts": {
                "alerts.rule_category": rng.choice(["sepsis", "fall_risk", "vte_prophylaxis", "drug_interaction", "critical_lab"]),
                "alerts.priority_level": rng.choice(["critical", "high", "medium", "low", "informational"]),
            },
            "data-warehouse": {
                "compliance.audit_scope": rng.choice(["phi_access", "order_modification", "medication_override", "record_amendment"]),
                "compliance.hipaa_zone": rng.choice(["treatment", "payment", "operations", "research", "restricted"]),
            },
        }
        base.update(svc_attrs.get(service_name, {}))
        return base

    def get_rca_clues(self, channel: int, service_name: str, rng) -> dict:
        clues = {
            1: {  # HL7 Message Parsing Failure
                "ehr-system": {"hl7.segment_encoding": "non_standard_z_segment", "hl7.msh_version": "2.3.1"},
                "lab-integration": {"hl7.oru_queue_depth": rng.randint(200, 800), "hl7.ack_disposition": "AE"},
                "patient-monitor": {"upstream.ehr_feed_status": "degraded", "vitals.documentation_lag_s": rng.randint(30, 120)},
                "clinical-alerts": {"alerts.ehr_integration_status": "stale_data", "alerts.suppressed_count": rng.randint(5, 30)},
            },
            2: {  # Vital Signs Alert Storm
                "patient-monitor": {"vitals.threshold_config": "mismatched_acuity", "vitals.monitor_firmware": "ge-carescape-v4.1.2"},
                "clinical-alerts": {"alerts.storm_window_s": rng.randint(30, 120), "alerts.dedup_disabled": True},
                "ehr-system": {"upstream.vitals_feed_status": "flooded", "ehr.cds_queue_depth": rng.randint(100, 500)},
            },
            3: {  # Lab Result Delivery Delay
                "lab-integration": {"lis.outbound_queue_depth": rng.randint(500, 2000), "lis.instrument_interface": "stalled"},
                "ehr-system": {"ehr.pending_results_count": rng.randint(50, 200), "ehr.oru_channel_status": "backlogged"},
                "pharmacy-system": {"pharmacy.awaiting_lab_results": rng.randint(10, 50), "pharmacy.dosing_hold": True},
                "clinical-alerts": {"alerts.critical_lab_pending": rng.randint(3, 15), "alerts.tat_breach_count": rng.randint(5, 25)},
            },
            4: {  # HIPAA Audit Log Integrity Error
                "data-warehouse": {"audit.chain_break_detected": True, "audit.wal_recovery_available": rng.choice([True, False])},
                "ehr-system": {"ehr.phi_access_logging": "degraded", "ehr.unaudited_access_count": rng.randint(10, 100)},
                "clinical-alerts": {"alerts.compliance_violation_fired": True, "alerts.breach_notification_pending": True},
                "billing-processor": {"billing.audit_gap_in_claims": True, "billing.cms_reporting_risk": rng.choice(["low", "medium", "high"])},
            },
            5: {  # Medication Interaction Alert Overflow
                "pharmacy-system": {"cpoe.ddi_queue_depth": rng.randint(100, 500), "cpoe.fdb_cache_stale": True},
                "ehr-system": {"ehr.medication_orders_held": rng.randint(10, 50), "ehr.cpoe_screening_lag_s": rng.randint(30, 180)},
                "clinical-alerts": {"alerts.drug_interaction_backlog": rng.randint(20, 80), "alerts.critical_block_pending": rng.randint(2, 8)},
            },
            6: {  # E-Prescribe Transmission Error
                "pharmacy-system": {"ncpdp.npi_validation_status": "failed", "ncpdp.script_version": "10.6"},
                "ehr-system": {"ehr.pending_erx_count": rng.randint(5, 30), "ehr.surescripts_link": "degraded"},
                "clinical-alerts": {"alerts.erx_failure_count": rng.randint(3, 15)},
                "billing-processor": {"billing.rx_claim_pending": rng.randint(5, 20), "billing.ncpdp_d0_queue": rng.randint(10, 50)},
            },
            7: {  # Patient Identity Match Failure
                "ehr-system": {"empi.matching_algorithm": "jaro_winkler", "empi.threshold_pct": 85},
                "patient-monitor": {"vitals.patient_id_confidence": "low", "vitals.dual_band_mismatch": True},
                "lab-integration": {"lis.duplicate_mrn_detected": True, "lis.specimen_hold": rng.randint(2, 8)},
                "pharmacy-system": {"pharmacy.patient_merge_pending": True, "pharmacy.orders_held": rng.randint(3, 12)},
            },
            8: {  # Bed Management Sync Error
                "scheduling-api": {"bed_board.adt_queue_lag_s": rng.randint(60, 600), "bed_board.stale_census_count": rng.randint(3, 15)},
                "ehr-system": {"ehr.adt_event_backlog": rng.randint(20, 100), "ehr.census_accuracy_pct": round(rng.uniform(70, 90), 1)},
                "clinical-alerts": {"alerts.patient_location_stale": True, "alerts.affected_units": rng.randint(1, 4)},
            },
            9: {  # Appointment Scheduling Conflict
                "scheduling-api": {"sched.lock_type": "optimistic", "sched.concurrent_bookings": rng.randint(5, 20)},
                "ehr-system": {"ehr.encounter_conflict_count": rng.randint(2, 8)},
                "billing-processor": {"billing.duplicate_encounter_charge": True, "billing.held_claims": rng.randint(2, 10)},
            },
            10: {  # Insurance Eligibility Check Timeout
                "billing-processor": {"x12.clearinghouse_status": "degraded", "x12.payer_response_ms": rng.randint(5000, 30000)},
                "scheduling-api": {"sched.eligibility_check_pending": rng.randint(10, 40), "sched.self_pay_fallback": True},
                "ehr-system": {"ehr.unverified_insurance_count": rng.randint(5, 25)},
            },
            11: {  # Claims Processing Batch Failure
                "billing-processor": {"x12.batch_rejection_rate_pct": round(rng.uniform(15, 60), 1), "x12.isa_envelope_error": True},
                "data-warehouse": {"etl.claims_feed_stalled": True, "etl.pending_claim_records": rng.randint(500, 5000)},
                "ehr-system": {"ehr.unbilled_encounters": rng.randint(20, 100)},
                "scheduling-api": {"sched.charge_capture_lag_s": rng.randint(300, 1800)},
            },
            12: {  # Surgical Schedule Conflict
                "scheduling-api": {"sched.or_block_cache_stale": True, "sched.turnover_buffer_min": rng.randint(15, 30)},
                "ehr-system": {"ehr.surgical_consent_pending": rng.randint(1, 5), "ehr.or_preference_card_stale": True},
                "billing-processor": {"billing.surgical_pre_auth_pending": rng.randint(1, 3)},
                "clinical-alerts": {"alerts.or_schedule_conflict_count": rng.randint(1, 4)},
            },
            13: {  # Clinical Decision Support Overload
                "clinical-alerts": {"cds.rule_eval_pool_saturated": True, "cds.arden_mlm_queue": rng.randint(50, 300)},
                "ehr-system": {"ehr.cds_evaluation_lag_s": rng.randint(30, 180), "ehr.pending_cds_results": rng.randint(20, 100)},
                "pharmacy-system": {"pharmacy.ddi_screening_delayed": True, "pharmacy.held_orders": rng.randint(5, 25)},
                "patient-monitor": {"vitals.alert_evaluation_stale": True, "vitals.sepsis_screen_pending": rng.randint(2, 10)},
            },
            14: {  # Nurse Call System Integration Failure
                "clinical-alerts": {"ncs.bridge_status": "disconnected", "ncs.undelivered_calls": rng.randint(5, 30)},
                "patient-monitor": {"vitals.nurse_response_lag_s": rng.randint(60, 300), "vitals.overhead_paging_active": True},
                "ehr-system": {"ehr.undocumented_calls": rng.randint(3, 15)},
            },
            15: {  # Blood Bank Inventory Sync Error
                "lab-integration": {"bb.isbt_scanner_status": "offline", "bb.physical_count_mismatch": True},
                "clinical-alerts": {"alerts.blood_shortage_alert": True, "alerts.crossmatch_pending_expired": rng.randint(2, 8)},
                "ehr-system": {"ehr.transfusion_orders_held": rng.randint(1, 5)},
                "scheduling-api": {"sched.surgical_cases_held": rng.randint(1, 3), "sched.blood_type_screen_pending": True},
            },
            16: {  # PACS Storage Capacity Warning
                "imaging-service": {"pacs.archive_migration_stalled": True, "pacs.volume_fill_rate_gb_day": round(rng.uniform(50, 200), 0)},
                "data-warehouse": {"etl.imaging_archive_full": True, "etl.vna_migration_pending": rng.randint(500, 5000)},
                "clinical-alerts": {"alerts.storage_critical_fired": True},
                "ehr-system": {"ehr.new_study_routing": "blocked"},
            },
            17: {  # ADT Feed Synchronization Gap
                "ehr-system": {"adt.feed_processor_threads_exhausted": True, "adt.queue_drain_rate_per_s": round(rng.uniform(0.5, 3.0), 1)},
                "scheduling-api": {"sched.patient_location_stale": True, "sched.bed_board_accuracy_pct": round(rng.uniform(60, 85), 1)},
                "patient-monitor": {"vitals.patient_assignment_stale": True, "vitals.affected_beds": rng.randint(5, 20)},
                "billing-processor": {"billing.encounter_sync_lag_s": rng.randint(120, 600)},
                "lab-integration": {"lis.specimen_routing_stale": True, "lis.misrouted_results": rng.randint(2, 10)},
            },
            18: {  # Data Warehouse ETL Pipeline Stall
                "data-warehouse": {"etl.source_db_pool_exhausted": True, "etl.blocking_query_count": rng.randint(3, 12)},
                "billing-processor": {"billing.revenue_cycle_report_stale": True, "billing.days_behind": rng.randint(1, 5)},
                "ehr-system": {"ehr.oltp_contention_detected": True, "ehr.query_timeout_count": rng.randint(5, 30)},
            },
            19: {  # DICOM Transfer Failure
                "imaging-service": {"dicom.ae_title_mismatch": True, "dicom.transfer_syntax": "1.2.840.10008.1.2.1"},
                "ehr-system": {"ehr.pending_imaging_results": rng.randint(5, 30), "ehr.pacs_link_status": "disconnected"},
                "clinical-alerts": {"alerts.imaging_delay_count": rng.randint(2, 10)},
                "data-warehouse": {"etl.imaging_archive_stalled": True, "etl.pending_studies": rng.randint(20, 100)},
            },
            20: {  # Telehealth Session Quality Degradation
                "patient-monitor": {"telehealth.turn_server_overloaded": True, "telehealth.bandwidth_kbps": rng.randint(128, 512)},
                "clinical-alerts": {"alerts.session_quality_breach_count": rng.randint(3, 15), "alerts.provider_notified": rng.choice([True, False])},
                "ehr-system": {"ehr.visit_documentation_incomplete": True, "ehr.telehealth_encounter_held": rng.randint(1, 5)},
                "scheduling-api": {"sched.telehealth_to_inperson_conversions": rng.randint(1, 5), "sched.rebooking_queue": rng.randint(2, 10)},
            },
        }
        channel_clues = clues.get(channel, {})
        return channel_clues.get(service_name, {})

    def get_correlation_attribute(self, channel: int, is_error: bool, rng) -> dict:
        correlation_attrs = {
            1: ("deployment.ehr_hl7_version", "mirth-3.12.0-hotfix7"),
            2: ("infra.monitor_firmware", "ge-carescape-v4.1.2-rc"),
            3: ("deployment.lis_interface_version", "lis2a2-bridge-v2.8.1-beta"),
            4: ("deployment.audit_chain_version", "sha256-chain-v2.1.0-rc3"),
            5: ("deployment.cpoe_engine_config", "fdb-cache-aggressive-v2"),
            6: ("infra.ncpdp_gateway_version", "surescripts-adapter-v6.0.3-rc1"),
            7: ("deployment.empi_algorithm_config", "jaro-winkler-tuned-v3.2"),
            8: ("infra.bed_board_sync_driver", "adt-bridge-v1.9.4-unstable"),
            9: ("deployment.scheduler_lock_mode", "optimistic-lock-v2.1-exp"),
            10: ("infra.x12_gateway_config", "availity-adapter-v4.3.0-rc2"),
            11: ("deployment.claims_engine_build", "x12-837-processor-v5.1.2-beta"),
            12: ("infra.or_scheduler_config", "block-mgmt-v3.2.0-beta"),
            13: ("deployment.cds_rule_engine", "arden-mlm-v3.0.1-experimental"),
            14: ("infra.nursecall_bridge_fw", "hillrom-bridge-v2.4.0-rc1"),
            15: ("deployment.bb_isbt_driver", "isbt128-scanner-v1.7.3-patched"),
            16: ("infra.pacs_storage_controller", "netapp-ontap-9.14.1-patch"),
            17: ("deployment.adt_processor_build", "mirth-adt-v3.12.0-hotfix9"),
            18: ("infra.etl_db_pool_config", "hikari-pool-experimental-64conn"),
            19: ("infra.pacs_gateway_build", "dcm4chee-5.31.1-patch3"),
            20: ("infra.turn_server_build", "coturn-4.6.2-high-concurrency"),
        }
        attr_key, attr_val = correlation_attrs.get(channel, ("deployment.config_version", "unknown"))
        # 90% on errors, 5% on healthy
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
            # Patient/clinical identifiers
            "patient_id": f"PT-{random.randint(100000, 999999)}",
            "mrn": f"MRN-{random.randint(1000000, 9999999)}",
            "encounter_id": f"ENC-{random.randint(100000, 999999)}",
            # HL7 / ADT
            "msg_type": random.choice(["ADT^A01", "ADT^A03", "ADT^A08", "ORU^R01", "ORM^O01"]),
            "hl7_segment": random.choice(["PID", "PV1", "OBX", "OBR", "MSH", "NK1", "DG1"]),
            "position": random.randint(1, 25),
            "adt_event_type": random.choice(["A01", "A02", "A03", "A04", "A08"]),
            "feed_id": random.choice(["ADT-FEED-01", "ADT-FEED-02", "ADT-FEED-03"]),
            # Vitals
            "alert_count": random.randint(15, 120),
            "window_seconds": random.choice([30, 60, 120]),
            "nursing_unit": random.choice(["ICU-3A", "ICU-3B", "MedSurg-4N", "MedSurg-4S", "ED-1", "NICU-2"]),
            "heart_rate": random.randint(35, 180),
            "spo2": random.randint(70, 100),
            # Lab
            "lab_order_id": f"LAB-{random.randint(100000, 999999)}",
            "test_code": random.choice(["CBC", "BMP", "CMP", "PT/INR", "Troponin", "BNP", "Lipase", "UA"]),
            "tat_minutes": random.randint(60, 360),
            "max_tat": random.choice([30, 45, 60]),
            # DICOM / Imaging
            "dicom_study_uid": f"1.2.840.{random.randint(10000, 99999)}.{random.randint(1, 999)}.{random.randint(1, 99)}",
            "modality": random.choice(["CT", "MRI", "XR", "US", "MG", "NM"]),
            "dicom_operation": random.choice(["C-STORE", "C-MOVE", "C-FIND"]),
            "dicom_error_code": f"0x{random.choice(['A700', 'A900', 'C000', 'A801'])}",
            "volume_id": random.choice(["PACS-VOL-01", "PACS-VOL-02", "PACS-ARCHIVE-01"]),
            "usage_pct": round(random.uniform(88.0, 98.5), 1),
            "threshold_pct": 85.0,
            "remaining_gb": random.randint(50, 500),
            # Pharmacy / Medication
            "medication_id": f"MED-{random.randint(10000, 99999)}",
            "interaction_count": random.randint(50, 500),
            "severity_level": random.choice(["critical", "major", "moderate"]),
            "prescription_id": f"RX-{random.randint(100000, 999999)}",
            "pharmacy_npi": f"{random.randint(1000000000, 9999999999)}",
            "ncpdp_status": random.choice(["000", "600", "900", "510", "210"]),
            # Patient identity
            "match_score": round(random.uniform(45.0, 78.0), 1),
            "match_threshold": 85.0,
            # Scheduling / Beds
            "bed_id": f"{random.choice(['A', 'B', 'C', 'D'])}-{random.randint(101, 450)}",
            "bed_status": random.choice(["occupied", "vacant", "cleaning", "blocked"]),
            "adt_event": random.choice(["discharge", "transfer", "admit"]),
            "sync_lag_seconds": random.randint(60, 600),
            "provider_id": f"NPI-{random.randint(1000000000, 9999999999)}",
            "time_slot": f"{random.randint(7, 17):02d}:{random.choice(['00', '15', '30', '45'])}",
            "resource_type": random.choice(["exam_room", "procedure_room", "consult_room"]),
            # Surgical
            "or_number": f"OR-{random.randint(1, 12)}",
            "case_id": f"SURG-{random.randint(10000, 99999)}",
            "surgeon_id": f"NPI-{random.randint(1000000000, 9999999999)}",
            "conflict_time": f"{random.randint(7, 17):02d}:{random.choice(['00', '30'])}",
            # Billing / Insurance
            "insurance_id": f"INS-{random.randint(100000, 999999)}",
            "payer_id": random.choice(["BCBS-001", "AETNA-002", "UHC-003", "CIGNA-004", "MDCR-005", "MDCD-006"]),
            "elapsed_ms": random.randint(5000, 30000),
            "timeout_ms": 5000,
            "batch_id": f"BATCH-{random.randint(1000, 9999)}",
            "claim_id": f"CLM-{random.randint(100000, 999999)}",
            "claim_stage": random.choice(["validation", "scrubbing", "submission", "adjudication"]),
            # Clinical alerts / CDS
            "pending_rules": random.randint(50, 500),
            "eval_ms": random.randint(3000, 15000),
            "max_eval_ms": 2000,
            "station_id": f"NCS-{random.choice(['ICU', 'MEDSURG', 'ED', 'NICU'])}-{random.randint(1, 20)}",
            "call_type": random.choice(["emergency", "routine", "bathroom", "pain_management"]),
            "undelivered_seconds": random.randint(30, 300),
            # Blood bank
            "blood_product": random.choice(["PRBC", "FFP", "Platelets", "Cryoprecipitate"]),
            "blood_type": random.choice(["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]),
            "units_on_hand": random.randint(2, 15),
            "system_count": random.randint(8, 25),
            "discrepancy": random.randint(3, 12),
            # ADT sync
            "gap_seconds": random.randint(60, 600),
            "queue_depth": random.randint(100, 5000),
            # ETL / Data Warehouse
            "pipeline_id": random.choice(["ETL-CLINICAL-01", "ETL-BILLING-02", "ETL-LAB-03", "ETL-QUALITY-04"]),
            "etl_stage": random.choice(["extract", "transform", "load", "validate"]),
            "rows_processed": random.randint(10000, 500000),
            "total_rows": random.randint(500000, 2000000),
            "stall_seconds": random.randint(120, 1800),
            # HIPAA audit
            "chain_id": f"AUDIT-{random.randint(1000, 9999)}",
            "sequence_number": random.randint(1, 100000),
            "expected_hash": f"sha256:{secrets.token_hex(16)}",
            "actual_hash": f"sha256:{secrets.token_hex(16)}",
            # Telehealth
            "session_id": f"TH-{random.randint(100000, 999999)}",
            "bitrate_kbps": random.randint(128, 512),
            "packet_loss_pct": round(random.uniform(5.0, 25.0), 1),
            "latency_ms": random.randint(200, 2000),
        }


# Module-level instance for registry discovery
scenario = HealthcareScenario()

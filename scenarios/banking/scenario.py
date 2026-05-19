"""Retail Banking Platform scenario — financial services with mobile banking,
insurance claims processing, fraud detection, and customer authentication."""

from __future__ import annotations

import random
import time
from typing import Any

from scenarios.base import BaseScenario, CountdownConfig, UITheme


class BankingScenario(BaseScenario):
    """Retail banking platform with 9 services and 20 fault channels."""

    # ── Identity ──────────────────────────────────────────────────────

    @property
    def scenario_id(self) -> str:
        return "banking"

    @property
    def scenario_icon(self) -> str:
        return "🏦"

    @property
    def scenario_name(self) -> str:
        return "Retail Banking Platform"

    @property
    def scenario_description(self) -> str:
        return (
            "Retail banking platform with mobile banking, insurance "
            "claims processing, policy management, fraud detection, and customer "
            "authentication. Serving millions of customers and families."
        )

    @property
    def namespace(self) -> str:
        return "banking"

    @property
    def sort_order(self) -> int:
        return 6

    @property
    def raw_log_profile(self) -> dict[str, Any]:
        return {
            "service_name": "banking-gateway",
            "user_id_prefix": "acct",
            "tier_field": "account_tier",
            "tier_values": [("standard", 70), ("premier", 22), ("private", 8)],
            "country_weights": {"US": 50, "GB": 15, "DE": 8, "FR": 5, "CA": 10, "AU": 5, "SG": 4, "JP": 3},
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "paths": [
                "/api/v1/accounts", "/api/v1/transfers", "/api/v1/cards",
                "/api/v1/loans", "/api/v1/payees", "/api/v1/statements",
                "/login", "/health",
            ],
            "change_point_path": "/api/v1/transfers",
        }

    @property
    def executive_kpi_emitter_service_name(self) -> str:
        return "member-portal"

    @property
    def executive_dashboard_intro(self) -> str:
        return (
            "**Retail banking KPIs** — revenue & margins, digital adoption, risk & compliance, "
            "and customer health (synthetic `business.*` from `member-portal`)."
        )

    @property
    def executive_kpi_sections(self) -> list[dict]:
        return [
            {
                "header": "**Revenue & margins** — NII, fees, origination, interchange, and deposits",
                "specs": [
                    ("Net interest income (USD/min)", "metrics.business.net_interest_income_usd_per_min"),
                    ("Fee revenue (USD/min)", "metrics.business.fee_revenue_usd_per_min"),
                    ("Loan origination (USD/min)", "metrics.business.loan_origination_usd_per_min"),
                    ("Card interchange (USD/min)", "metrics.business.card_interchange_usd_per_min"),
                    ("Wealth AUM delta (USD/min)", "metrics.business.wealth_aum_delta_usd_per_min"),
                    ("Deposit growth (USD/min)", "metrics.business.deposit_growth_usd_per_min"),
                ],
            },
            {
                "header": "**Digital adoption** — sessions, mobile, self-service, and API usage",
                "specs": [
                    ("Active digital sessions", "metrics.business.active_digital_sessions"),
                    ("Mobile logins / min", "metrics.business.mobile_logins_per_min"),
                    ("Digital transaction (%)", "metrics.business.digital_transaction_pct"),
                    ("Self-service deflection (%)", "metrics.business.self_service_deflection_pct"),
                    ("App session duration (s)", "metrics.business.app_session_duration_sec"),
                    ("API calls / min", "metrics.business.api_calls_per_min"),
                ],
            },
            {
                "header": "**Risk & compliance** — fraud, AML, chargebacks, and regulatory",
                "specs": [
                    ("Fraud detection rate (%)", "metrics.business.fraud_detection_rate_pct"),
                    ("Suspicious activity alerts / min", "metrics.business.suspicious_activity_alerts_per_min"),
                    ("AML flags / min", "metrics.business.aml_flags_per_min"),
                    ("Failed auth attempts / min", "metrics.business.failed_auth_attempts_per_min"),
                    ("Chargeback rate (%)", "metrics.business.chargeback_rate_pct"),
                    ("Regulatory breach count", "metrics.business.regulatory_breach_count"),
                ],
            },
            {
                "header": "**Customer health** — NPS, openings, closures, churn & satisfaction",
                "specs": [
                    ("Satisfaction proxy (NPS-like)", "metrics.business.net_satisfaction_proxy_nps"),
                    ("Account openings / min", "metrics.business.account_openings_per_min"),
                    ("Account closures / min", "metrics.business.account_closures_per_min"),
                    ("Churn risk (0–100)", "metrics.business.churn_risk_index_0_100"),
                    ("Complaint tickets / min", "metrics.business.complaint_tickets_per_min"),
                    ("CSAT (0–5)", "metrics.business.csat_score_0_5"),
                ],
            },
        ]

    @property
    def executive_trend_charts(self) -> list[dict]:
        return [
            {"title": "Net interest income trend", "field": "metrics.business.net_interest_income_usd_per_min", "y_label": "USD/min"},
            {"title": "Loan origination trend", "field": "metrics.business.loan_origination_usd_per_min", "y_label": "USD/min"},
            {"title": "Active digital sessions", "field": "metrics.business.active_digital_sessions", "y_label": "sessions"},
            {"title": "Deposit growth trend", "field": "metrics.business.deposit_growth_usd_per_min", "y_label": "USD/min"},
            {"title": "Fraud detection rate", "field": "metrics.business.fraud_detection_rate_pct", "y_label": "%"},
            {"title": "Churn risk index", "field": "metrics.business.churn_risk_index_0_100", "y_label": "index"},
        ]

    # ── Services ──────────────────────────────────────────────────────

    @property
    def services(self) -> dict[str, dict[str, Any]]:
        return {
            # AWS — Core Banking
            "mobile-gateway": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1a",
                "subsystem": "digital_banking",
                "language": "java",
            },
            "claims-processor": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1b",
                "subsystem": "claims_management",
                "language": "java",
            },
            "payment-engine": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1c",
                "subsystem": "payment_processing",
                "language": "go",
            },
            # GCP — Insurance & Security
            "policy-manager": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "policy_administration",
                "language": "python",
            },
            "fraud-sentinel": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-b",
                "subsystem": "fraud_detection",
                "language": "python",
            },
            "auth-gateway": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-c",
                "subsystem": "authentication",
                "language": "go",
            },
            # Azure — Member Services
            "quote-engine": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "underwriting",
                "language": "java",
            },
            "member-portal": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-2",
                "subsystem": "member_services",
                "language": "python",
            },
            "document-vault": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-3",
                "subsystem": "document_management",
                "language": "dotnet",
            },
        }

    # ── Channel Registry ──────────────────────────────────────────────

    @property
    def channel_registry(self) -> dict[int, dict[str, Any]]:
        return {
            1: {
                "name": "Fraud Model False Positive Surge",
                "subsystem": "fraud_detection",
                "vehicle_section": "fraud_engine",
                "error_type": "FRAUD-FP-SURGE",
                "sensor_type": "fraud_classifier",
                "affected_services": ["fraud-sentinel", "payment-engine"],
                "cascade_services": ["mobile-gateway", "auth-gateway"],
                "description": "Fraud detection model generating excessive false positives blocking legitimate member transactions",
                "investigation_notes": (
                    "1. Root cause is PCS_SEASON — Permanent Change of Station moves cause massive geographic velocity "
                    "changes that the fraud model interprets as account takeover. This is a known seasonal pattern.\n"
                    "2. Feature drift analysis: geo_velocity_feature at 0.92 drift and ip_diversity at 0.87 drift confirm "
                    "the model's geographic features are firing on legitimate PCS relocations.\n"
                    "3. With 4,200 active PCS orders, the model needs a PCS whitelist — members with active PCS orders "
                    "should have relaxed geo-velocity thresholds. Query: SELECT member_id FROM pcs_orders WHERE status='ACTIVE'.\n"
                    "4. Revenue impact at $892K/hr blocked is severe. Precision dropped to 3.2% means 97% of blocks are "
                    "false positives. Immediately raise the fraud score threshold from current to 75/100 for PCS-flagged members.\n"
                    "5. Initiate emergency model retrain with PCS-labeled training data. Include features: has_active_pcs, "
                    "days_since_pcs_order, destination_matches_new_duty_station.\n"
                    "6. Short-term fix: whitelist all members with active PCS orders in the fraud rules table. "
                    "INSERT INTO fraud_whitelist SELECT member_id FROM pcs_orders WHERE status='ACTIVE' AND effective_date > CURRENT_DATE - 90."
                ),
                "remediation_action": "recalibrate_fraud_model",
                "error_message": "[FRAUD] FRAUD-FP-SURGE: blocked={fraud_blocked} window={fraud_window_s}s fp_rate={fraud_fp_rate}% model={fraud_model} pattern={fraud_pattern}",
                "stack_trace": (
                    "=== FRAUD MODEL PERFORMANCE ===\n"
                    "model={fraud_model}  pattern={fraud_pattern}  window={fraud_window_s}s\n"
                    "--- CLASSIFICATION MATRIX ---\n"
                    "                    PREDICTED_FRAUD   PREDICTED_LEGIT\n"
                    "  ACTUAL_FRAUD           8               1\n"
                    "  ACTUAL_LEGIT          {fraud_blocked}              3,847\n"
                    "--- METRICS ---\n"
                    "  true_positive_rate    88.9%\n"
                    "  false_positive_rate   {fraud_fp_rate}%  <<< SURGE THRESHOLD\n"
                    "  precision             3.2%\n"
                    "  blocked_txns          {fraud_blocked}\n"
                    "  member_impact         $892,000/hr revenue blocked\n"
                    "--- DRIFT ANALYSIS ---\n"
                    "  trigger=PCS_SEASON  (military relocation spike)\n"
                    "  geo_velocity_feature=0.92_drift  ip_diversity=0.87_drift\n"
                    "  pcs_orders_active=4,200  geolocation_changes=HIGH\n"
                    "ACTION: whitelist_pcs=true  retrain_model=true  alert=FRAUD-FP-SURGE"
                ),
            },
            2: {
                "name": "Mobile Deposit Processing Failure",
                "subsystem": "digital_banking",
                "vehicle_section": "mobile_deposit",
                "error_type": "MOBILE-DEPOSIT-FAIL",
                "sensor_type": "deposit_processor",
                "affected_services": ["mobile-gateway", "document-vault"],
                "cascade_services": ["claims-processor", "payment-engine"],
                "description": "Mobile check deposit image capture and processing pipeline failure",
                "investigation_notes": (
                    "1. Check the amount_verify stage — OCR-extracted amount vs member-entered amount mismatch is the "
                    "most common failure. Review image quality scores; quality <85% correlates with OCR errors.\n"
                    "2. Inspect MICR line extraction: routing and account numbers must parse correctly from the magnetic "
                    "ink character recognition scan. Failed MICR reads require manual keying or re-capture.\n"
                    "3. Verify Reg CC hold policies are correctly applied — military early pay eligibility and next-business-day "
                    "availability depend on correct member tier classification in the deposit rules engine.\n"
                    "4. Check document-vault connectivity — deposit images must be stored before processing continues. "
                    "S3 upload failures in document-vault will block the entire deposit pipeline.\n"
                    "5. Review duplicate detection window — 90-day lookback should catch re-deposited checks. "
                    "If duplicate_check passes but amount_verify fails, the issue is OCR accuracy, not fraud."
                ),
                "remediation_action": "restart_deposit_processor",
                "error_message": "[MOBILE] MOBILE-DEPOSIT-FAIL: deposit={deposit_id} amount=${deposit_amount} member={member_id} stage={deposit_stage} error={deposit_error}",
                "stack_trace": (
                    "=== MOBILE DEPOSIT PIPELINE ===\n"
                    "deposit={deposit_id}  member={member_id}  amount=${deposit_amount}\n"
                    "--- PROCESSING STAGES ---\n"
                    "  STAGE                STATUS      DETAIL\n"
                    "  image_capture        COMPLETE    front+back captured, quality=92%\n"
                    "  ocr_extraction       COMPLETE    MICR: routing={routing_number} acct=****{acct_last4}\n"
                    "  duplicate_check      COMPLETE    no duplicates in 90-day window\n"
                    "  amount_verify        FAILED      ocr_amount=${deposit_amount} entered=$0.00  <<< MISMATCH\n"
                    "  fraud_screen         SKIPPED     blocked by amount_verify failure\n"
                    "  funds_hold           SKIPPED     ---\n"
                    "stage={deposit_stage}  error={deposit_error}\n"
                    "hold_policy=REG-CC  availability=NEXT_BUSINESS_DAY  risk_tier=LOW\n"
                    "ACTION: reject_deposit=true  notify_member=true  alert=MOBILE-DEPOSIT-FAIL"
                ),
            },
            3: {
                "name": "Push Notification Storm",
                "subsystem": "digital_banking",
                "vehicle_section": "notification_service",
                "error_type": "MOBILE-NOTIF-STORM",
                "sensor_type": "notification_rate",
                "affected_services": ["mobile-gateway", "auth-gateway"],
                "cascade_services": ["member-portal", "fraud-sentinel"],
                "description": "Push notification system sending duplicate or excessive alerts to members",
                "investigation_notes": (
                    "1. Check dedup cache status — OVERFLOW at 500K entries means the cache cannot prevent duplicate sends. "
                    "Inspect Redis memory: redis-cli INFO memory | grep used_memory_human.\n"
                    "2. Identify the root_cause event_replay source — transaction_processor is re-emitting events that "
                    "trigger notifications. Check transaction_processor logs for reprocessing or replay activity.\n"
                    "3. Monitor APNS throttling — Apple will rate-limit and eventually block the push certificate if "
                    "abuse continues. Check APNS feedback service for unregistered device tokens.\n"
                    "4. Review member complaint volume — 200+ complaints in a notification storm triggers regulatory "
                    "attention. CFPB considers excessive notifications a UDAAP (unfair practices) concern.\n"
                    "5. Flush and resize the dedup cache immediately, then identify which event types are replaying. "
                    "Check: SELECT event_type, COUNT(*) FROM notification_events WHERE ts > NOW() - INTERVAL 5 MINUTE GROUP BY event_type."
                ),
                "remediation_action": "flush_notification_queue",
                "error_message": "[MOBILE] MOBILE-NOTIF-STORM: rate={notif_rate}/min max={notif_max}/min duplicates={notif_dupes} channel={notif_channel} window={notif_window_s}s",
                "stack_trace": (
                    "=== NOTIFICATION SERVICE STATS ===\n"
                    "channel={notif_channel}  window={notif_window_s}s\n"
                    "--- DELIVERY METRICS ---\n"
                    "  CHANNEL          SENT      DELIVERED   FAILED    DUPES\n"
                    "  APNS             12,450    11,980      470       {notif_dupes}\n"
                    "  FCM              8,320     8,140       180       {notif_dupes}\n"
                    "  SMS              2,100     2,085       15        0\n"
                    "  EMAIL            4,500     4,480       20        0\n"
                    "--- RATE ANALYSIS ---\n"
                    "  current_rate={notif_rate}/min  max_allowed={notif_max}/min\n"
                    "  dedup_cache=OVERFLOW  cache_size=500000  cache_capacity=500000\n"
                    "  root_cause=event_replay  source=transaction_processor\n"
                    "member_complaints=247  unsubscribes=18  APNS_throttled=true\n"
                    "ACTION: throttle_all=true  flush_dedup_cache=true  alert=MOBILE-NOTIF-STORM"
                ),
            },
            4: {
                "name": "ACH Direct Deposit Delay",
                "subsystem": "payment_processing",
                "vehicle_section": "ach_processor",
                "error_type": "PAY-ACH-DELAY",
                "sensor_type": "ach_processing",
                "affected_services": ["payment-engine", "mobile-gateway"],
                "cascade_services": ["member-portal", "fraud-sentinel"],
                "description": "ACH direct deposit batch processing delayed affecting military pay and allotments",
                "investigation_notes": (
                    "1. Check account_lookup stage — this is the bottleneck. High latency here indicates the member account "
                    "database is under load or replication lag is causing timeouts on lookups.\n"
                    "2. DFAS (Defense Finance and Accounting Service) military pay files arrive in the 06:00 ET Fed window. "
                    "Delays past 08:00 ET affect Early Pay eligibility — members expecting funds by morning will call.\n"
                    "3. Review NACHA file parsing metrics — entry counts >30K in a single batch may overwhelm the OFAC "
                    "screening step. Consider splitting large DFAS batches into sub-batches of 10K entries.\n"
                    "4. Check Aurora PostgreSQL connection pool on payment-engine: SELECT count(*) FROM pg_stat_activity "
                    "WHERE state = 'active'. Connection saturation causes account_lookup stalls.\n"
                    "5. Verify OFAC screening service response times — the 45s elapsed is within SLA but leaves no headroom. "
                    "If OFAC screening degrades, the entire batch pipeline will breach SLA. Monitor Treasury SDN list update status."
                ),
                "remediation_action": "reset_ach_processor",
                "error_message": "[PAY] PAY-ACH-DELAY: batch={ach_batch_id} entries={ach_entry_count} delay_min={ach_delay_min} sla_min={ach_sla_min} type={ach_type}",
                "stack_trace": (
                    "=== ACH BATCH PROCESSING STATUS ===\n"
                    "batch={ach_batch_id}  type={ach_type}  entries={ach_entry_count}\n"
                    "--- NACHA FILE PROCESSING ---\n"
                    "  STAGE                STATUS      ELAPSED\n"
                    "  file_receive         COMPLETE    0.2s     (Fed window: 06:00 ET)\n"
                    "  header_validate      COMPLETE    1.4s\n"
                    "  entry_parse          COMPLETE    12.8s    ({ach_entry_count} entries)\n"
                    "  ofac_screening       COMPLETE    45.2s\n"
                    "  account_lookup       STALLED     {ach_delay_min}min  <<< BOTTLENECK\n"
                    "  balance_post         PENDING     ---\n"
                    "  notification         PENDING     ---\n"
                    "--- IMPACT ---\n"
                    "  military_pay_entries={ach_entry_count}  total_amount=$4,247,892.00\n"
                    "  dfas_originator=true  early_pay_eligible=true\n"
                    "delay={ach_delay_min}min  sla={ach_sla_min}min  breach=true\n"
                    "ACTION: escalate_ops=true  notify_dfas_liaison=true  alert=PAY-ACH-DELAY"
                ),
            },
            5: {
                "name": "Bill Pay Execution Failure",
                "subsystem": "payment_processing",
                "vehicle_section": "bill_pay",
                "error_type": "PAY-BILLPAY-FAIL",
                "sensor_type": "bill_pay_status",
                "affected_services": ["payment-engine", "member-portal"],
                "cascade_services": ["mobile-gateway", "document-vault"],
                "description": "Scheduled bill payments failing to execute on due date",
                "investigation_notes": (
                    "1. Check FedACH window status — bill pay electronic payments can only transmit during Fed operating "
                    "windows. If the window is CLOSED and retries are exhausted, payments queue until next window (06:00 ET).\n"
                    "2. Review the specific failure reason: INSUFFICIENT_FUNDS requires member notification with balance info; "
                    "PAYEE_ACCOUNT_CLOSED needs payee record update; ROUTING_NUMBER_INVALID indicates stale payee data.\n"
                    "3. Assess late fee and credit impact risk — failed bill payments on due date can trigger late fees from "
                    "payees and potential credit score impact. Flag HIGH risk payments for immediate member outreach.\n"
                    "4. Check payment-engine retry logic — 3/3 attempts exhausted means auto-retry will not help. "
                    "Manual intervention required: SELECT * FROM bill_payments WHERE status='FAILED' AND due_date=CURRENT_DATE.\n"
                    "5. For military members on deployment, verify SCRA protections apply — late fees may be waivable "
                    "under Servicemembers Civil Relief Act. Check member.deployment_status in member profile."
                ),
                "remediation_action": "restart_billpay_processor",
                "error_message": "[PAY] PAY-BILLPAY-FAIL: payment={billpay_id} payee={payee_name} amount=${billpay_amount} member={member_id} reason={billpay_reason}",
                "stack_trace": (
                    "=== BILL PAY EXECUTION LOG ===\n"
                    "payment={billpay_id}  member={member_id}\n"
                    "--- PAYMENT DETAILS ---\n"
                    "  payee={payee_name}  amount=${billpay_amount}\n"
                    "  method=ELECTRONIC  scheduled_date=2026-02-18\n"
                    "  funding_account=****{acct_last4}  available_balance=${available_balance}\n"
                    "--- EXECUTION ATTEMPT ---\n"
                    "  attempt=3/3  last_error={billpay_reason}\n"
                    "  FedACH_window=CLOSED  next_window=06:00_ET_TOMORROW\n"
                    "  payee_routing={routing_number}  payee_status=ACTIVE\n"
                    "--- MEMBER IMPACT ---\n"
                    "  late_fee_risk=HIGH  credit_score_impact=POSSIBLE\n"
                    "  auto_retry=EXHAUSTED  member_notified=false\n"
                    "ACTION: notify_member=true  schedule_retry=true  alert=PAY-BILLPAY-FAIL"
                ),
            },
            6: {
                "name": "Wire Transfer OFAC Block",
                "subsystem": "payment_processing",
                "vehicle_section": "wire_transfer",
                "error_type": "PAY-OFAC-BLOCK",
                "sensor_type": "compliance_screening",
                "affected_services": ["payment-engine", "fraud-sentinel"],
                "cascade_services": ["member-portal", "auth-gateway"],
                "description": "Wire transfer held due to OFAC SDN list match requiring manual BSA review",
                "investigation_notes": (
                    "1. Review the OFAC match score and algorithm — JARO_WINKLER scores above 85% require BSA officer review "
                    "within 24 hours per bank policy. Scores 75-85% may be false positives from common name patterns.\n"
                    "2. Check the SDN list version — if the match is against a recently added entry, verify the member's "
                    "identity against the actual SDN record. Military members with common names frequently trigger false matches.\n"
                    "3. Wire destination analysis: PCS_RELOCATION and DEPLOYMENT_EXPENSE purposes to allied nations (DE, JP, KR, GB) "
                    "are typically legitimate. Cross-reference with member's duty station assignment orders.\n"
                    "4. BSA/AML compliance requirements: SAR filing must be evaluated within 24h SLA. If the wire exceeds $10K, "
                    "verify CTR filing status. Check 314(b) information sharing requests from FinCEN.\n"
                    "5. Do NOT release the wire without BSA officer sign-off — OFAC violations carry strict liability penalties "
                    "up to $20M per violation. Escalate to BSA team: bsa-review@bankops.internal with wire reference number."
                ),
                "remediation_action": "escalate_bsa_review",
                "error_message": "[PAY] PAY-OFAC-BLOCK: wire={wire_id} amount=${wire_amount} member={member_id} match_score={ofac_score} list={ofac_list}",
                "stack_trace": (
                    "=== OFAC SCREENING RESULT ===\n"
                    "wire={wire_id}  member={member_id}  amount=${wire_amount}\n"
                    "--- SDN LIST MATCH ---\n"
                    "  list={ofac_list}  match_score={ofac_score}%\n"
                    "  match_type=NAME_SIMILARITY  algorithm=JARO_WINKLER\n"
                    "  member_name='{member_name}'  sdn_entry='{ofac_match_name}'\n"
                    "  country={wire_country}  program=SDGT\n"
                    "--- WIRE DETAILS ---\n"
                    "  originator=RETAIL_BANK_FSB  beneficiary_bank={beneficiary_bank}\n"
                    "  swift_code={swift_code}  purpose={wire_purpose}\n"
                    "  fedwire_ref=FW{wire_id}\n"
                    "--- BSA REQUIREMENTS ---\n"
                    "  sar_filing=PENDING  ctr_threshold=false  314b_request=false\n"
                    "  bsa_officer_review=REQUIRED  sla_hours=24\n"
                    "ACTION: hold_wire=true  escalate_bsa=true  alert=PAY-OFAC-BLOCK"
                ),
            },
            7: {
                "name": "Debit Card Authorization Failure",
                "subsystem": "payment_processing",
                "vehicle_section": "card_auth",
                "error_type": "PAY-CARD-AUTH-FAIL",
                "sensor_type": "card_authorization",
                "affected_services": ["payment-engine", "fraud-sentinel"],
                "cascade_services": ["mobile-gateway", "member-portal"],
                "description": "Debit card authorization requests failing at Visa/Mastercard network level",
                "investigation_notes": (
                    "1. Check the ISO 8583 response code: 05=Do Not Honor, 14=Invalid Card, 51=Insufficient Funds, "
                    "54=Expired Card, 61=Exceeds Limit, 91=Issuer Unavailable, 96=System Malfunction.\n"
                    "2. Response code 91 (SYSTEM_MALFUNCTION) indicates the card network itself is having issues — "
                    "check Visa/Mastercard network status pages and recent advisories for regional outages.\n"
                    "3. Verify STIP (Stand-In Processing) eligibility — if network_auth fails but STIP is available, "
                    "the payment-engine should authorize locally using risk parameters and post-authorize later.\n"
                    "4. Monitor decline rate by merchant MCC code — elevated declines at military exchanges (MCC 5411, AAFES) "
                    "or commissaries (DeCA) indicate a pattern requiring immediate network liaison escalation.\n"
                    "5. Check fraud-sentinel score — if fraud_score PASS with score 12/100 but network declines, the issue "
                    "is external. Contact card network operations: Visa (1-800-847-2750) or MC (1-800-307-7309).\n"
                    "6. Review retry_eligible flag — if true, implement exponential backoff retry (2s, 4s, 8s) before "
                    "returning decline to member. Log all retry attempts for chargeback dispute support."
                ),
                "remediation_action": "reset_card_auth_gateway",
                "error_message": "[PAY] PAY-CARD-AUTH-FAIL: auth={auth_id} card=****{card_last4} amount=${auth_amount} merchant={merchant_name} decline_code={decline_code}",
                "stack_trace": (
                    "=== CARD AUTHORIZATION FAILURE ===\n"
                    "auth={auth_id}  card=****{card_last4}  network={card_network}\n"
                    "--- TRANSACTION ---\n"
                    "  merchant={merchant_name}  mcc={merchant_mcc}\n"
                    "  amount=${auth_amount}  currency=USD\n"
                    "  pos_entry=CHIP  pin_verified=true\n"
                    "--- AUTHORIZATION CHAIN ---\n"
                    "  STEP                STATUS      CODE\n"
                    "  velocity_check      PASS        ---\n"
                    "  balance_check       PASS        avail=${available_balance}\n"
                    "  fraud_score         PASS        score=12/100\n"
                    "  network_auth        DECLINED    {decline_code}  <<< FAILED\n"
                    "  stand_in            N/A         STIP not eligible\n"
                    "--- NETWORK RESPONSE ---\n"
                    "  iso8583_rc={decline_code}  response_ms=2340  timeout=false\n"
                    "  issuer_response=SYSTEM_MALFUNCTION  retry_eligible=true\n"
                    "ACTION: retry_network=true  notify_member=true  alert=PAY-CARD-AUTH-FAIL"
                ),
            },
            8: {
                "name": "Claims FNOL Intake Backlog",
                "subsystem": "claims_management",
                "vehicle_section": "fnol_intake",
                "error_type": "CLAIMS-FNOL-BACKLOG",
                "sensor_type": "claims_queue",
                "affected_services": ["claims-processor", "document-vault"],
                "cascade_services": ["payment-engine", "member-portal"],
                "description": "First Notice of Loss intake queue backlogged after catastrophic weather event",
                "investigation_notes": (
                    "1. Activate CAT (catastrophe) response team — surge staffing protocol brings in adjusters from "
                    "unaffected regions. Check CAT team deployment status and estimated time to field.\n"
                    "2. Monitor intake vs processing rate deficit — at 55 claims/hr deficit, the backlog grows by ~1,320 "
                    "claims per day. Enable virtual adjusting and photo-based estimates to increase processing throughput.\n"
                    "3. Review claim distribution by type — auto_comp (hail/flood) claims marked HIGH severity require "
                    "field inspection. Property claims marked SEVERE may need emergency mitigation services.\n"
                    "4. Enable self-service FNOL paths: mobile app photo submission, automated triage chatbot, and "
                    "simplified loss reporting forms to reduce call center load and queue depth.\n"
                    "5. Check military base proximity — catastrophic events near military installations (Fort Liberty, "
                    "Fort Cavazos, NAS Jacksonville) affect concentrated member populations. Coordinate with base "
                    "family readiness groups for member outreach. Priority-queue SCRA-protected members."
                ),
                "remediation_action": "activate_cat_response",
                "error_message": "[CLAIMS] CLAIMS-FNOL-BACKLOG: queue_depth={claims_queue} avg_wait_min={claims_wait_min} cat_event={cat_event} region={cat_region} pending={claims_pending}",
                "stack_trace": (
                    "=== FNOL INTAKE STATUS ===\n"
                    "cat_event={cat_event}  region={cat_region}\n"
                    "--- QUEUE METRICS ---\n"
                    "  queue_depth={claims_queue}  avg_wait={claims_wait_min}min  sla=15min\n"
                    "  intake_rate=142/hr  processing_rate=87/hr  deficit=55/hr\n"
                    "--- CLAIM DISTRIBUTION ---\n"
                    "  TYPE              COUNT     PCT     AVG_SEVERITY\n"
                    "  auto_collision    {claims_pending}     42%     MODERATE\n"
                    "  auto_comp         320       28%     HIGH (hail/flood)\n"
                    "  property          180       16%     SEVERE\n"
                    "  renters           160       14%     LOW\n"
                    "--- ADJUSTER POOL ---\n"
                    "  available=42  in_field=28  cat_team_deployed=true\n"
                    "  virtual_adjusting=ENABLED  photo_estimate=ACTIVE\n"
                    "ACTION: activate_cat_response=true  deploy_surge_staff=true  alert=CLAIMS-FNOL-BACKLOG"
                ),
            },
            9: {
                "name": "Photo Damage Estimation Timeout",
                "subsystem": "claims_management",
                "vehicle_section": "damage_estimation",
                "error_type": "CLAIMS-PHOTO-EST-TIMEOUT",
                "sensor_type": "ai_estimation",
                "affected_services": ["claims-processor", "document-vault"],
                "cascade_services": ["member-portal", "mobile-gateway"],
                "description": "AI-powered photo damage estimation model exceeding response time threshold",
                "investigation_notes": (
                    "1. Check GPU utilization on the DamageNet inference cluster — 98% GPU util with 847 queued batches "
                    "indicates the model fleet is saturated. Scale GPU instances: aws autoscaling set-desired-capacity.\n"
                    "2. The repair_vs_replace stage is the bottleneck — this is the most compute-intensive step requiring "
                    "part-level damage classification and repair cost lookup against the CCC ONE/Mitchell databases.\n"
                    "3. Review model version DamageNet-v4.2 performance — if inference P99 exceeds SLA after a recent "
                    "model update, consider rolling back: kubectl rollout undo deployment/damage-estimator.\n"
                    "4. Enable MANUAL_ADJUSTER fallback routing — estimated 2-4hr delay is acceptable for non-drivable "
                    "vehicles. For drivable vehicles, provide preliminary estimate and supplement later.\n"
                    "5. Monitor image preprocessing — low quality images (blur, poor lighting) cause the damage_detection "
                    "stage to run multiple passes. Add client-side image quality validation before upload.\n"
                    "6. Check if CAT event volume is causing the surge — photo estimates spike 10-20x after hailstorms. "
                    "Pre-scale GPU fleet when CAT alerts are issued."
                ),
                "remediation_action": "scale_estimation_fleet",
                "error_message": "[CLAIMS] CLAIMS-PHOTO-EST-TIMEOUT: claim={claim_id} model_latency_ms={model_latency_ms} sla_ms={model_sla_ms} vehicle={vehicle_desc} images={image_count}",
                "stack_trace": (
                    "=== PHOTO ESTIMATION PIPELINE ===\n"
                    "claim={claim_id}  vehicle={vehicle_desc}\n"
                    "--- IMAGE ANALYSIS ---\n"
                    "  images_submitted={image_count}  quality_pass={image_count}\n"
                    "  STEP                    STATUS      ELAPSED_MS\n"
                    "  image_preprocessing     COMPLETE    420\n"
                    "  damage_detection        COMPLETE    1,240\n"
                    "  part_identification     COMPLETE    890\n"
                    "  repair_vs_replace       TIMEOUT     {model_latency_ms}  <<< STUCK\n"
                    "  cost_estimation         SKIPPED     ---\n"
                    "  supplement_prediction   SKIPPED     ---\n"
                    "--- MODEL HEALTH ---\n"
                    "  model_version=DamageNet-v4.2  gpu_util=98%  batch_queue=847\n"
                    "  inference_p99={model_latency_ms}ms  sla={model_sla_ms}ms\n"
                    "  fallback=MANUAL_ADJUSTER  estimated_delay=2-4hrs\n"
                    "ACTION: route_manual=true  scale_gpu_fleet=true  alert=CLAIMS-PHOTO-EST-TIMEOUT"
                ),
            },
            10: {
                "name": "Claims Payment Disbursement Failure",
                "subsystem": "claims_management",
                "vehicle_section": "claims_payment",
                "error_type": "CLAIMS-DISBURSEMENT-FAIL",
                "sensor_type": "payment_disbursement",
                "affected_services": ["claims-processor", "payment-engine"],
                "cascade_services": ["member-portal", "document-vault"],
                "description": "Claims settlement payment failing to disburse to member account or body shop",
                "investigation_notes": (
                    "1. Check the disbursement error type: PAYEE_ACCOUNT_MISMATCH means the body shop's banking details "
                    "changed — verify with DRP (Direct Repair Program) network coordinator. DAILY_LIMIT_EXCEEDED requires "
                    "treasury approval for limit override.\n"
                    "2. For ROUTING_VALIDATION_FAIL, the payee's routing number failed ABA validation — cross-reference "
                    "with the Federal Reserve's E-Payments routing directory: https://www.frbservices.org/EPaymentsDirectory.\n"
                    "3. FRAUD_HOLD_ACTIVE means fraud-sentinel flagged the disbursement — review the fraud alert and "
                    "determine if the hold is legitimate or a false positive from the claims payment pattern.\n"
                    "4. Member impact: 12 days since loss with rental_extension=REQUIRED means the member's rental car "
                    "coverage is expiring. Approve rental extension while disbursement is resolved to avoid out-of-pocket.\n"
                    "5. For body shop payees in the DRP network, contact the shop directly to verify banking details. "
                    "Non-DRP shops may require updated W-9 and payment authorization forms.\n"
                    "6. Check 1099 generation — failed disbursements that were partially processed may need 1099 reversal "
                    "to avoid incorrect tax reporting to the IRS."
                ),
                "remediation_action": "retry_claims_disbursement",
                "error_message": "[CLAIMS] CLAIMS-DISBURSEMENT-FAIL: claim={claim_id} amount=${claim_amount} payee={claim_payee} method={disbursement_method} error={disbursement_error}",
                "stack_trace": (
                    "=== CLAIMS DISBURSEMENT STATUS ===\n"
                    "claim={claim_id}  amount=${claim_amount}  payee={claim_payee}\n"
                    "--- PAYMENT ATTEMPT ---\n"
                    "  method={disbursement_method}  attempt=3/3\n"
                    "  STEP                STATUS      DETAIL\n"
                    "  claim_approved      COMPLETE    adjuster_id=ADJ-4827\n"
                    "  amount_verified     COMPLETE    estimate=${claim_amount} deductible=$500\n"
                    "  payee_validated     COMPLETE    {claim_payee}\n"
                    "  funds_transfer      FAILED      {disbursement_error}  <<< BLOCKED\n"
                    "  1099_generation     SKIPPED     ---\n"
                    "--- PAYEE INFO ---\n"
                    "  type=BODY_SHOP  routing={routing_number}  acct=****{acct_last4}\n"
                    "  DRP_network=true  preferred_shop=true\n"
                    "rental_extension=REQUIRED  member_waiting=true  days_since_loss=12\n"
                    "ACTION: retry_payment=true  extend_rental=true  alert=CLAIMS-DISBURSEMENT-FAIL"
                ),
            },
            11: {
                "name": "Policy Renewal Batch Failure",
                "subsystem": "policy_administration",
                "vehicle_section": "renewal_engine",
                "error_type": "POLICY-RENEWAL-FAIL",
                "sensor_type": "renewal_batch",
                "affected_services": ["policy-manager", "quote-engine"],
                "cascade_services": ["member-portal", "document-vault"],
                "description": "Automated policy renewal batch processing failing causing coverage gaps",
                "investigation_notes": (
                    "1. Check premium_calculation failure reason: RATING_ENGINE_TIMEOUT means the actuarial rating service "
                    "is degraded — verify quote-engine health and response times in APM traces.\n"
                    "2. MVR_DATA_STALE indicates driving record pulls returned cached data beyond acceptable freshness. "
                    "Check the LexisNexis/TransUnion MVR feed connectivity and last successful pull timestamp.\n"
                    "3. CLUE_SERVICE_UNAVAILABLE means loss history lookups failed — CLUE (Comprehensive Loss Underwriting "
                    "Exchange) outages affect all carriers. Check A-PLUS/CLUE system status with LexisNexis.\n"
                    "4. Coverage gap risk is HIGH — policies that fail renewal before effective_date create uninsured "
                    "periods. Extend grace period to 30 days and notify members. State insurance departments require "
                    "reporting of lapsed auto policies.\n"
                    "5. Check SCRA-protected members — 12 policies with deployment_hold cannot be non-renewed under "
                    "the Servicemembers Civil Relief Act. These must be manually renewed at the prior term premium.\n"
                    "6. Run manual renewal batch for failed policies: POST /api/v1/policy/batch-renew with override flags."
                ),
                "remediation_action": "restart_renewal_engine",
                "error_message": "[POLICY] POLICY-RENEWAL-FAIL: batch={renewal_batch_id} policies={renewal_count} failed={renewal_failed} reason={renewal_reason} effective={renewal_date}",
                "stack_trace": (
                    "=== POLICY RENEWAL BATCH STATUS ===\n"
                    "batch={renewal_batch_id}  effective_date={renewal_date}\n"
                    "--- BATCH METRICS ---\n"
                    "  total_policies={renewal_count}  processed=0  failed={renewal_failed}\n"
                    "  STEP                    STATUS      DETAIL\n"
                    "  rating_refresh          COMPLETE    new_rates_applied\n"
                    "  mvr_pull                COMPLETE    driving_records_updated\n"
                    "  clue_check              COMPLETE    loss_history_verified\n"
                    "  premium_calculation     FAILED      {renewal_reason}  <<< BLOCKED\n"
                    "  dec_page_generate       SKIPPED     ---\n"
                    "  payment_schedule        SKIPPED     ---\n"
                    "--- COVERAGE RISK ---\n"
                    "  lapse_risk=HIGH  grace_period=30_days  state_reporting=REQUIRED\n"
                    "  military_deployment_hold={deployment_hold}\n"
                    "  scra_protected_members=12\n"
                    "ACTION: manual_renewal=true  extend_grace=true  alert=POLICY-RENEWAL-FAIL"
                ),
            },
            12: {
                "name": "Underwriting Rules Engine Error",
                "subsystem": "underwriting",
                "vehicle_section": "rules_engine",
                "error_type": "UW-RULES-ENGINE-ERR",
                "sensor_type": "underwriting_rules",
                "affected_services": ["quote-engine", "policy-manager"],
                "cascade_services": ["member-portal", "claims-processor"],
                "description": "Underwriting rules engine producing inconsistent decisions on policy applications",
                "investigation_notes": (
                    "1. Identify the conflicting rule — check which specific rule in the 2,847-rule chain is producing "
                    "inconsistent results. Cross-reference with change_set CS-4827 deployed on 2026-02-15.\n"
                    "2. Conflict rate 2.4% vs 0.5% threshold indicates a systematic issue, not isolated cases. Review "
                    "the rule deployment diff: git diff CS-4826..CS-4827 -- rules/ to identify changed rules.\n"
                    "3. Check rule execution order dependencies — rules like military_discount_eligibility and "
                    "multi_policy_bundle may have ordering conflicts when both conditions apply simultaneously.\n"
                    "4. Verify garaging_zip risk factors are using current ISO territory data — outdated territory "
                    "mappings near military bases can cause incorrect risk classification (e.g., Fort Liberty zip codes).\n"
                    "5. For affected applications, route to manual underwriting queue with full rule execution trace. "
                    "Flag applications where expected=APPROVE but actual=DECLINE for priority review — these represent "
                    "members being incorrectly denied coverage.\n"
                    "6. Consider rules engine rollback if conflict rate doesn't stabilize within 1 hour. "
                    "Rollback command: kubectl rollout undo deployment/rules-engine -n banking-underwriting."
                ),
                "remediation_action": "rollback_rules_engine",
                "error_message": "[UW] UW-RULES-ENGINE-ERR: application={app_id} product={insurance_product} rule={failed_rule} expected={expected_decision} actual={actual_decision}",
                "stack_trace": (
                    "=== UNDERWRITING RULES ENGINE ===\n"
                    "application={app_id}  product={insurance_product}\n"
                    "--- RULE EXECUTION CHAIN ---\n"
                    "  RULE                     RESULT      DETAIL\n"
                    "  eligibility_check        PASS        member_since=2018, active_duty\n"
                    "  credit_score_tier        PASS        score=742, tier=PREFERRED\n"
                    "  driving_record           PASS        violations=0, accidents=0\n"
                    "  garaging_zip_risk        PASS        zip={garaging_zip}, risk=LOW\n"
                    "  {failed_rule}            CONFLICT    expected={expected_decision} got={actual_decision}\n"
                    "  bundle_discount          SKIPPED     blocked by conflict\n"
                    "--- RULE ENGINE HEALTH ---\n"
                    "  version=RulesEngine-v7.4  rule_count=2,847\n"
                    "  conflict_rate=2.4%  threshold=0.5%  <<< EXCEEDED\n"
                    "  last_deployment=2026-02-15  change_set=CS-4827\n"
                    "ACTION: flag_manual_uw=true  rollback_rules=EVALUATE  alert=UW-RULES-ENGINE-ERR"
                ),
            },
            13: {
                "name": "VA Loan Rate Lock Failure",
                "subsystem": "underwriting",
                "vehicle_section": "va_lending",
                "error_type": "UW-VA-RATELOCK-FAIL",
                "sensor_type": "rate_lock",
                "affected_services": ["quote-engine", "payment-engine"],
                "cascade_services": ["member-portal", "document-vault"],
                "description": "VA home loan rate lock requests failing due to secondary market pricing feed disruption",
                "investigation_notes": (
                    "1. Check GNMA (Ginnie Mae) MBS pricing feed status — STALE data 47min old means the secondary "
                    "market pricing API is not responding. Verify connectivity to the pricing vendor feed.\n"
                    "2. Secondary market conditions: 10yr Treasury at 4.28% with HIGH volatility means MBS prices are "
                    "moving rapidly. Stale pricing creates risk of locking at incorrect rates.\n"
                    "3. VA loan rate locks require current GNMA MBS pricing because VA loans are pooled into Ginnie Mae "
                    "securities. Without accurate MBS pricing, the bank cannot calculate its margin correctly.\n"
                    "4. Honor the quoted rate for members who received a rate quote before the feed went down — this is "
                    "both regulatory best practice and member trust policy. Queue locks for execution when feed recovers.\n"
                    "5. Check Certificate of Eligibility (COE) verification — ensure the VA eligibility service is still "
                    "operational even if rate locking is paused. Members can continue applications without locking.\n"
                    "6. Monitor the VA funding fee calculation — first-time use vs subsequent use rates differ, and "
                    "disabled veterans may qualify for fee exemption. These calculations don't depend on MBS pricing."
                ),
                "remediation_action": "restart_ratelock_service",
                "error_message": "[UW] UW-VA-RATELOCK-FAIL: loan={loan_id} rate={va_rate}% lock_period={lock_days}d member={member_id} error={ratelock_error}",
                "stack_trace": (
                    "=== VA LOAN RATE LOCK STATUS ===\n"
                    "loan={loan_id}  member={member_id}\n"
                    "--- LOAN DETAILS ---\n"
                    "  product=VA_30YR_FIXED  amount=${loan_amount}\n"
                    "  requested_rate={va_rate}%  lock_period={lock_days}days\n"
                    "  va_funding_fee={va_funding_fee}%  coe_verified=true\n"
                    "--- PRICING PIPELINE ---\n"
                    "  STEP                    STATUS      DETAIL\n"
                    "  coe_validation          COMPLETE    certificate_of_eligibility=valid\n"
                    "  credit_pull             COMPLETE    score=748, dti=32%\n"
                    "  secondary_market_price  FAILED      {ratelock_error}  <<< FEED DOWN\n"
                    "  margin_calculation      SKIPPED     ---\n"
                    "  lock_confirmation       SKIPPED     ---\n"
                    "--- MARKET CONDITIONS ---\n"
                    "  10yr_treasury=4.28%  spread=1.72%  volatility=HIGH\n"
                    "  gnma_mbs_price=STALE  last_update=47min_ago\n"
                    "ACTION: queue_lock=true  honor_quoted_rate=true  alert=UW-VA-RATELOCK-FAIL"
                ),
            },
            14: {
                "name": "Biometric Auth Service Degradation",
                "subsystem": "authentication",
                "vehicle_section": "biometric_auth",
                "error_type": "AUTH-BIOMETRIC-DEGRADE",
                "sensor_type": "biometric_verification",
                "affected_services": ["auth-gateway", "mobile-gateway"],
                "cascade_services": ["member-portal", "fraud-sentinel"],
                "description": "Biometric authentication (Face ID, fingerprint) verification service experiencing high failure rate",
                "investigation_notes": (
                    "1. Analyze failure distribution by method — voice_print at 32% fail rate is worst, likely due to "
                    "background noise in military environments (flight line, motor pool, barracks). Consider increasing "
                    "noise tolerance thresholds for voice authentication.\n"
                    "2. Liveness check failures (42%) indicate potential issues with the anti-spoofing model, not member "
                    "behavior. Check BioAuth-v3.1 model performance — last retrain was 2026-01-28, may need refresh.\n"
                    "3. Template mismatch (31%) can occur after device changes or significant appearance changes common "
                    "in military (new glasses, weight change during deployment). Prompt template re-enrollment.\n"
                    "4. Monitor fallback path capacity — PIN attempts surging 340% means auth-gateway PIN verification "
                    "is absorbing all biometric failures. Check auth-gateway rate limits and connection pool.\n"
                    "5. Call center overflow at 22min wait indicates members cannot self-recover. Enable temporary "
                    "password-based authentication bypass for verified members: POST /api/v1/auth/temp-bypass.\n"
                    "6. Check device compatibility matrix — new iOS/Android versions may break biometric SDKs. "
                    "Review crash reports from mobile-gateway for biometric SDK exceptions."
                ),
                "remediation_action": "reset_biometric_service",
                "error_message": "[AUTH] AUTH-BIOMETRIC-DEGRADE: method={bio_method} fail_rate={bio_fail_rate}% threshold={bio_threshold}% attempts={bio_attempts} fallback={bio_fallback}",
                "stack_trace": (
                    "=== BIOMETRIC SERVICE HEALTH ===\n"
                    "method={bio_method}  window=5min\n"
                    "--- VERIFICATION STATS ---\n"
                    "  METHOD           ATTEMPTS   SUCCESS    FAIL_RATE\n"
                    "  face_id          {bio_attempts}      72%        28%\n"
                    "  fingerprint      1,240      81%        19%\n"
                    "  voice_print      420        68%        32%  <<< WORST\n"
                    "--- FAILURE ANALYSIS ---\n"
                    "  liveness_check_fail=42%  template_mismatch=31%\n"
                    "  timeout=18%  device_incompatible=9%\n"
                    "  overall_fail_rate={bio_fail_rate}%  threshold={bio_threshold}%\n"
                    "--- FALLBACK STATUS ---\n"
                    "  fallback={bio_fallback}  pin_attempts_surge=340%\n"
                    "  call_center_overflow=true  wait_time=22min\n"
                    "model_version=BioAuth-v3.1  last_retrain=2026-01-28\n"
                    "ACTION: enable_fallback=true  increase_tolerance=true  alert=AUTH-BIOMETRIC-DEGRADE"
                ),
            },
            15: {
                "name": "MFA Delivery Failure",
                "subsystem": "authentication",
                "vehicle_section": "mfa_service",
                "error_type": "AUTH-MFA-DELIVERY-FAIL",
                "sensor_type": "mfa_delivery",
                "affected_services": ["auth-gateway", "mobile-gateway"],
                "cascade_services": ["member-portal", "payment-engine"],
                "description": "Multi-factor authentication code delivery failing via SMS and email channels",
                "investigation_notes": (
                    "1. SMS delivery at 70% is critically degraded — check carrier blocking status. T-Mobile and Verizon "
                    "SPAM_FILTER blocking on short code 872438 requires carrier re-registration and compliance review.\n"
                    "2. Military-specific impact: OCONUS members (342 affected) on overseas deployments rely heavily on "
                    "SMS MFA. Satellite phones do not support short code SMS. Enable TOTP bypass for deployed members.\n"
                    "3. Check MFA provider status — Twilio and AWS SNS have regional outage dashboards. Provider RATE_LIMIT_EXCEEDED "
                    "means the sending volume exceeded the provisioned throughput. Request limit increase.\n"
                    "4. Deployed member lockout (89 members) is a critical issue — these members cannot authenticate "
                    "to manage finances during deployment. Activate emergency access protocol: verify identity via "
                    "security questions + last 4 SSN, then issue temporary TOTP enrollment.\n"
                    "5. Route all SMS traffic to EMAIL fallback while SMS is degraded. For members without email on file, "
                    "enable PUSH notification MFA through the mobile app.\n"
                    "6. SCRA flag on affected accounts means special regulatory handling — ensure no account restrictions "
                    "are applied due to authentication failures on SCRA-protected accounts."
                ),
                "remediation_action": "reset_mfa_delivery",
                "error_message": "[AUTH] AUTH-MFA-DELIVERY-FAIL: channel={mfa_channel} delivery_rate={mfa_delivery_rate}% member={member_id} provider={mfa_provider} error={mfa_error}",
                "stack_trace": (
                    "=== MFA DELIVERY STATUS ===\n"
                    "channel={mfa_channel}  provider={mfa_provider}\n"
                    "--- DELIVERY METRICS ---\n"
                    "  CHANNEL     SENT      DELIVERED   RATE      STATUS\n"
                    "  SMS         4,200     2,940       70%       DEGRADED\n"
                    "  EMAIL       2,800     2,744       98%       OK\n"
                    "  PUSH        1,600     1,520       95%       OK\n"
                    "  TOTP        890       890         100%      OK\n"
                    "--- SMS FAILURE DETAIL ---\n"
                    "  provider={mfa_provider}  error={mfa_error}\n"
                    "  carrier_block=T-MOBILE,VERIZON  reason=SPAM_FILTER\n"
                    "  short_code=872438  throughput=120/min  queue=4,200\n"
                    "--- MILITARY IMPACT ---\n"
                    "  oconus_members_affected=342  satellite_phone=NOT_SUPPORTED\n"
                    "  deployed_members_lockout=89  scra_flag=true\n"
                    "ACTION: route_to_email=true  enable_totp_bypass=true  alert=AUTH-MFA-DELIVERY-FAIL"
                ),
            },
            16: {
                "name": "Mobile App API Timeout",
                "subsystem": "digital_banking",
                "vehicle_section": "mobile_api",
                "error_type": "MOBILE-API-TIMEOUT",
                "sensor_type": "api_latency",
                "affected_services": ["mobile-gateway", "auth-gateway"],
                "cascade_services": ["member-portal", "payment-engine"],
                "description": "Mobile banking API requests exceeding response time SLA causing member app failures",
                "investigation_notes": (
                    "1. Check mobile-gateway connection pool utilization — pool_active near pool_max indicates exhaustion. "
                    "Run: kubectl exec -it mobile-gateway -- curl localhost:8080/actuator/metrics/hikaricp.connections.active\n"
                    "2. Review backend_routing phase — latency spike at this stage points to upstream service degradation, "
                    "not the gateway itself. Check auth-gateway and payment-engine response times in APM.\n"
                    "3. Inspect circuit breaker state: HALF_OPEN means the gateway is testing recovery. If stuck in HALF_OPEN "
                    "for >60s, the upstream service is intermittently failing. Check: /actuator/health for dependency status.\n"
                    "4. Queue depth >2000 indicates backpressure buildup — consider scaling mobile-gateway replicas or "
                    "enabling request shedding. Check HPA metrics: kubectl get hpa mobile-gateway -n banking-prod.\n"
                    "5. Verify CACHE_STALE fallback is returning acceptable data — stale cached responses may show "
                    "incorrect balances. Review cache TTL settings in mobile-gateway ConfigMap."
                ),
                "remediation_action": "restart_mobile_gateway",
                "error_message": "[MOBILE] MOBILE-API-TIMEOUT: endpoint={endpoint} latency_ms={latency_ms} sla_ms={sla_ms} member={member_id} device={device_type}",
                "stack_trace": (
                    "=== MOBILE GATEWAY LATENCY REPORT ===\n"
                    "endpoint={endpoint}  member={member_id}  device={device_type}\n"
                    "--- REQUEST PIPELINE ---\n"
                    "  PHASE                ELAPSED_MS    STATUS\n"
                    "  tls_handshake            42        OK\n"
                    "  auth_token_verify        180       OK\n"
                    "  rate_limit_check         12        OK\n"
                    "  backend_routing          {latency_ms}     TIMEOUT  <<< BOTTLENECK\n"
                    "  response_serialize       ---       SKIPPED\n"
                    "total_ms={latency_ms}  sla_ms={sla_ms}  breach=true\n"
                    "connection_pool_active=847  pool_max=1000  queue_depth=2340\n"
                    "circuit_breaker=HALF_OPEN  retry_count=3  fallback=CACHE_STALE\n"
                    "ACTION: circuit_break=true  return_cached=true  alert=MOBILE-API-TIMEOUT"
                ),
            },
            17: {
                "name": "Member Session Timeout Cascade",
                "subsystem": "member_services",
                "vehicle_section": "session_manager",
                "error_type": "PORTAL-SESSION-CASCADE",
                "sensor_type": "session_management",
                "affected_services": ["member-portal", "auth-gateway"],
                "cascade_services": ["mobile-gateway", "payment-engine"],
                "description": "Mass member session invalidation causing authentication storm and portal outage",
                "investigation_notes": (
                    "1. Redis cluster primary failure caused the session store to lose all active sessions. Check Redis "
                    "sentinel logs: redis-cli -p 26379 SENTINEL get-master-addr-by-name banking-sessions.\n"
                    "2. Thundering herd problem: reauth rate exceeds auth-gateway capacity (rate vs 500/min). "
                    "Implement token extension — issue new JWT tokens with extended TTL to surviving sessions without "
                    "requiring full re-authentication.\n"
                    "3. Circuit breaker on auth-gateway opened at T+12s — this prevents total auth system collapse but "
                    "blocks all new logins. Set circuit breaker to HALF_OPEN with 10% traffic sampling.\n"
                    "4. Redis cluster recovery: verify replicas 2/3 are healthy, promote a replica to primary. "
                    "Command: redis-cli -p 26379 SENTINEL failover banking-sessions. Estimated recovery 5min.\n"
                    "5. Rate limit re-authentication attempts with exponential backoff on the client side — mobile app "
                    "and portal should retry with jitter to prevent synchronized retry storms.\n"
                    "6. Post-incident: implement session persistence to a secondary store (DynamoDB/Elasticache Global) "
                    "so Redis primary failure doesn't cascade to full session loss."
                ),
                "remediation_action": "reset_session_pool",
                "error_message": "[PORTAL] PORTAL-SESSION-CASCADE: invalidated={sessions_invalidated} active_before={sessions_active} trigger={session_trigger} reauth_rate={reauth_rate}/min",
                "stack_trace": (
                    "=== SESSION CASCADE REPORT ===\n"
                    "trigger={session_trigger}\n"
                    "--- SESSION METRICS ---\n"
                    "  active_before={sessions_active}  invalidated={sessions_invalidated}\n"
                    "  reauth_attempts={reauth_rate}/min  auth_capacity=500/min\n"
                    "  overflow={reauth_rate}/min vs 500/min capacity  <<< THUNDERING HERD\n"
                    "--- TIMELINE ---\n"
                    "  T+0s    session_store_failover triggered\n"
                    "  T+2s    redis_cluster primary failed\n"
                    "  T+5s    {sessions_invalidated} sessions lost\n"
                    "  T+8s    reauth storm begins ({reauth_rate}/min)\n"
                    "  T+12s   auth-gateway circuit breaker OPEN\n"
                    "--- INFRASTRUCTURE ---\n"
                    "  redis_cluster=DEGRADED  primary=DOWN  replicas=2/3\n"
                    "  session_store=REBUILDING  estimated_recovery=5min\n"
                    "ACTION: rate_limit_auth=true  extend_tokens=true  alert=PORTAL-SESSION-CASCADE"
                ),
            },
            18: {
                "name": "Document Upload Service Failure",
                "subsystem": "document_management",
                "vehicle_section": "upload_service",
                "error_type": "DOC-UPLOAD-FAIL",
                "sensor_type": "document_upload",
                "affected_services": ["document-vault", "member-portal"],
                "cascade_services": ["claims-processor", "policy-manager"],
                "description": "Document upload and digital storage service failing affecting claims photos and policy documents",
                "investigation_notes": (
                    "1. Check S3 upload failure type: S3_WRITE_TIMEOUT indicates network latency to S3 endpoint — verify "
                    "VPC endpoint configuration and S3 gateway endpoint health in us-east-1.\n"
                    "2. BUCKET_QUOTA_EXCEEDED means storage limits hit — check bucket metrics: aws s3api head-bucket "
                    "--bucket banking-member-docs-prod. Request quota increase or implement lifecycle policy for old documents.\n"
                    "3. ENCRYPTION_KEY_ERROR indicates KMS key access issue — verify the document-vault service role has "
                    "kms:GenerateDataKey and kms:Decrypt permissions. Check KMS key rotation status.\n"
                    "4. PII detection pipeline is working (ssn=REDACTED, dob=REDACTED) but uploads are blocking at S3. "
                    "With 2,847 queued documents and oldest pending 12min, enable local cache fallback to prevent data loss.\n"
                    "5. Critical document types: DD214_DISCHARGE and COE_VA_LOAN uploads are time-sensitive for member "
                    "benefits. Flag these for priority retry when S3 recovers.\n"
                    "6. Check virus_scan throughput — ClamAV scanning should not be the bottleneck but verify: "
                    "kubectl logs -l app=document-vault --tail=100 | grep 'virus_scan' | grep -c 'TIMEOUT'."
                ),
                "remediation_action": "restart_document_service",
                "error_message": "[DOC] DOC-UPLOAD-FAIL: upload={upload_id} type={doc_type} size_mb={doc_size_mb} member={member_id} error={upload_error}",
                "stack_trace": (
                    "=== DOCUMENT UPLOAD SERVICE ===\n"
                    "upload={upload_id}  member={member_id}\n"
                    "--- UPLOAD DETAILS ---\n"
                    "  type={doc_type}  size={doc_size_mb}MB  format=PDF/JPEG\n"
                    "  classification=AUTO  sensitivity=PII_DETECTED\n"
                    "--- PROCESSING PIPELINE ---\n"
                    "  STEP                STATUS      DETAIL\n"
                    "  virus_scan          COMPLETE    clean\n"
                    "  format_validate     COMPLETE    valid\n"
                    "  pii_redaction       COMPLETE    ssn=REDACTED, dob=REDACTED\n"
                    "  s3_upload           FAILED      {upload_error}  <<< BLOCKED\n"
                    "  index_metadata      SKIPPED     ---\n"
                    "  ocr_extract         SKIPPED     ---\n"
                    "--- STORAGE HEALTH ---\n"
                    "  s3_bucket=banking-member-docs-prod  region=us-east-1\n"
                    "  error={upload_error}  retry=3/3\n"
                    "  queue_depth=2,847  oldest_pending=12min\n"
                    "ACTION: retry_upload=true  enable_local_cache=true  alert=DOC-UPLOAD-FAIL"
                ),
            },
            19: {
                "name": "Database Replication Lag",
                "subsystem": "payment_processing",
                "vehicle_section": "database_infra",
                "error_type": "INFRA-DB-REPL-LAG",
                "sensor_type": "replication_monitor",
                "affected_services": ["payment-engine", "mobile-gateway"],
                "cascade_services": ["claims-processor", "member-portal"],
                "description": "Primary-replica database replication lag causing stale reads and balance inconsistencies",
                "investigation_notes": (
                    "1. Replication lag root cause: WAL replay rate (8MB/s) cannot keep up with WAL send rate (12MB/s) — "
                    "33% throughput deficit means lag will continue growing. Check replica disk IOPS saturation.\n"
                    "2. Stale balance reads affect 33% of queries (round-robin across 3 nodes, 1 lagged) — members may "
                    "see incorrect available balances, leading to overdrafts or failed transactions.\n"
                    "3. Immediate action: route all reads to primary to ensure consistency. This increases primary load "
                    "but prevents stale data. Command: UPDATE pg_settings SET setting='primary' WHERE name='read_routing'.\n"
                    "4. Scale replica IOPS: aws rds modify-db-instance --db-instance-identifier {cluster}-b "
                    "--iops 10000 --apply-immediately. Current IOPS is SATURATED — Aurora allows up to 64K IOPS.\n"
                    "5. Check for long-running queries on the replica that may be blocking WAL replay: "
                    "SELECT pid, now()-query_start, query FROM pg_stat_activity WHERE state='active' ORDER BY query_start.\n"
                    "6. Monitor pending_txns — if this exceeds 100K, the replica may need to be rebuilt from snapshot. "
                    "Aurora can create a new replica in ~15 minutes from the primary's storage volume."
                ),
                "remediation_action": "failover_db_replica",
                "error_message": "[INFRA] INFRA-DB-REPL-LAG: cluster={db_cluster} lag_ms={db_lag_ms} max_ms={db_max_lag_ms} replica={db_replica} pending_txns={db_pending_txns}",
                "stack_trace": (
                    "=== DATABASE REPLICATION STATUS ===\n"
                    "cluster={db_cluster}  engine=Aurora_PostgreSQL_15.4\n"
                    "--- REPLICATION TOPOLOGY ---\n"
                    "  NODE              ROLE        LAG_MS    STATUS\n"
                    "  {db_cluster}-a    PRIMARY     0         OK\n"
                    "  {db_cluster}-b    REPLICA     {db_lag_ms}     BEHIND  <<< ALERT\n"
                    "  {db_cluster}-c    REPLICA     1,240     WARNING\n"
                    "--- LAG ANALYSIS ---\n"
                    "  current_lag={db_lag_ms}ms  max_allowed={db_max_lag_ms}ms  breach=true\n"
                    "  pending_txns={db_pending_txns}  wal_send_rate=12MB/s  wal_replay_rate=8MB/s\n"
                    "  disk_iops=SATURATED  cpu_replica=94%\n"
                    "--- IMPACT ---\n"
                    "  stale_balance_reads=POSSIBLE  affected_members=~12,000\n"
                    "  read_routing=ROUND_ROBIN  stale_read_pct=33%\n"
                    "ACTION: route_reads_primary=true  scale_replica_iops=true  alert=INFRA-DB-REPL-LAG"
                ),
            },
            20: {
                "name": "Certificate Expiration Cascade",
                "subsystem": "authentication",
                "vehicle_section": "certificate_mgmt",
                "error_type": "INFRA-CERT-EXPIRE",
                "sensor_type": "certificate_monitor",
                "affected_services": ["auth-gateway", "mobile-gateway"],
                "cascade_services": ["payment-engine", "member-portal"],
                "description": "TLS certificate expiration causing cascading authentication and API failures",
                "investigation_notes": (
                    "1. Check ACME auto-renewal failure — DNS_CHALLENGE_TIMEOUT indicates the DNS TXT record for domain "
                    "validation could not be created or propagated. Verify Route53/Cloud DNS API permissions.\n"
                    "2. Impact assessment: mobile-gateway and auth-gateway are FAILING (ERR_CERT_DATE_INVALID) — all "
                    "mobile app and authentication traffic is affected. member-portal is DEGRADED using pinned cert fallback.\n"
                    "3. Emergency certificate issuance: use AWS ACM for immediate cert provisioning if the domain is "
                    "AWS-hosted. For cross-cloud domains, use DigiCert rapid SSL: openssl req -new -key server.key -out server.csr.\n"
                    "4. Check cert-manager pod health in Kubernetes: kubectl get pods -n cert-manager -o wide. If cert-manager "
                    "is DEGRADED, manually install the cert: kubectl create secret tls {domain}-tls --cert=cert.pem --key=key.pem.\n"
                    "5. For mTLS-dependent services (payment-engine), the intermediate CA must also be valid. Check the "
                    "full certificate chain: openssl s_client -connect api.retailbank.com:443 -showcerts.\n"
                    "6. Post-incident: implement certificate expiration monitoring at 30/14/7/3/1 day thresholds. "
                    "Add cert-monitor alert rule to prevent future expiration cascades."
                ),
                "remediation_action": "emergency_cert_renewal",
                "error_message": "[INFRA] INFRA-CERT-EXPIRE: domain={cert_domain} expires_in={cert_hours_left}h serial={cert_serial} issuer={cert_issuer} services_affected={cert_svc_count}",
                "stack_trace": (
                    "=== CERTIFICATE STATUS REPORT ===\n"
                    "domain={cert_domain}  issuer={cert_issuer}\n"
                    "--- CERTIFICATE DETAILS ---\n"
                    "  serial={cert_serial}\n"
                    "  not_before=2025-02-18T00:00:00Z\n"
                    "  not_after=2026-02-18T23:59:59Z\n"
                    "  remaining={cert_hours_left}h  <<< EXPIRING\n"
                    "  subject=CN={cert_domain}\n"
                    "  san={cert_domain},*.{cert_domain}\n"
                    "--- IMPACT ANALYSIS ---\n"
                    "  services_affected={cert_svc_count}\n"
                    "  SERVICE              TLS_STATUS    LAST_HANDSHAKE\n"
                    "  mobile-gateway       FAILING       ERR_CERT_DATE_INVALID\n"
                    "  auth-gateway         FAILING       ERR_CERT_DATE_INVALID\n"
                    "  member-portal        DEGRADED      fallback_to_pinned_cert\n"
                    "  payment-engine       DEGRADED      mTLS_validation_warn\n"
                    "--- AUTO-RENEWAL ---\n"
                    "  acme_client=FAILED  last_attempt=2h_ago  error=DNS_CHALLENGE_TIMEOUT\n"
                    "  manual_renewal=REQUIRED  cert_manager=DEGRADED\n"
                    "ACTION: emergency_cert_issue=true  notify_security=true  alert=INFRA-CERT-EXPIRE"
                ),
            },
        }

    # ── Topology ──────────────────────────────────────────────────────

    @property
    def service_topology(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "mobile-gateway": [
                ("auth-gateway", "/api/v1/auth/verify-token", "POST"),
                ("payment-engine", "/api/v1/payments/initiate", "POST"),
                ("claims-processor", "/api/v1/claims/submit-fnol", "POST"),
                ("member-portal", "/api/v1/member/profile", "GET"),
                ("document-vault", "/api/v1/docs/upload", "POST"),
            ],
            "claims-processor": [
                ("document-vault", "/api/v1/docs/attach-claim", "POST"),
                ("payment-engine", "/api/v1/payments/disburse", "POST"),
                ("policy-manager", "/api/v1/policy/coverage-check", "GET"),
            ],
            "payment-engine": [
                ("fraud-sentinel", "/api/v1/fraud/screen-transaction", "POST"),
                ("auth-gateway", "/api/v1/auth/verify-payment", "POST"),
                ("document-vault", "/api/v1/docs/payment-receipt", "POST"),
            ],
            "policy-manager": [
                ("quote-engine", "/api/v1/quote/rate-policy", "POST"),
                ("document-vault", "/api/v1/docs/generate-dec-page", "POST"),
                ("member-portal", "/api/v1/member/policy-update", "POST"),
            ],
            "member-portal": [
                ("auth-gateway", "/api/v1/auth/session-validate", "POST"),
                ("mobile-gateway", "/api/v1/mobile/sync-preferences", "POST"),
                ("payment-engine", "/api/v1/payments/bill-pay", "POST"),
            ],
            "fraud-sentinel": [
                ("auth-gateway", "/api/v1/auth/risk-score", "GET"),
                ("payment-engine", "/api/v1/payments/hold-transaction", "POST"),
            ],
        }

    @property
    def entry_endpoints(self) -> dict[str, list[tuple[str, str]]]:
        return {
            "mobile-gateway": [
                ("/api/v1/mobile/login", "POST"),
                ("/api/v1/mobile/accounts", "GET"),
                ("/api/v1/mobile/deposit", "POST"),
                ("/api/v1/mobile/transfer", "POST"),
            ],
            "claims-processor": [
                ("/api/v1/claims/fnol", "POST"),
                ("/api/v1/claims/status", "GET"),
                ("/api/v1/claims/estimate", "POST"),
            ],
            "payment-engine": [
                ("/api/v1/payments/ach", "POST"),
                ("/api/v1/payments/wire", "POST"),
                ("/api/v1/payments/card-auth", "POST"),
            ],
            "policy-manager": [
                ("/api/v1/policy/renew", "POST"),
                ("/api/v1/policy/endorsement", "PUT"),
                ("/api/v1/policy/details", "GET"),
            ],
            "fraud-sentinel": [
                ("/api/v1/fraud/analyze", "POST"),
                ("/api/v1/fraud/alerts", "GET"),
            ],
            "auth-gateway": [
                ("/api/v1/auth/login", "POST"),
                ("/api/v1/auth/mfa", "POST"),
                ("/api/v1/auth/biometric", "POST"),
            ],
            "quote-engine": [
                ("/api/v1/quote/auto", "POST"),
                ("/api/v1/quote/property", "POST"),
                ("/api/v1/quote/va-loan", "POST"),
            ],
            "member-portal": [
                ("/api/v1/portal/dashboard", "GET"),
                ("/api/v1/portal/accounts", "GET"),
                ("/api/v1/portal/documents", "GET"),
            ],
            "document-vault": [
                ("/api/v1/docs/upload", "POST"),
                ("/api/v1/docs/retrieve", "GET"),
            ],
        }

    @property
    def db_operations(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "mobile-gateway": [
                ("SELECT", "member_sessions", "SELECT session_id, member_id, device_type, last_activity FROM member_sessions WHERE member_id = ? AND status = 'ACTIVE'"),
                ("INSERT", "mobile_deposits", "INSERT INTO mobile_deposits (deposit_id, member_id, amount, image_front, image_back, status, ts) VALUES (?, ?, ?, ?, ?, 'PENDING', NOW())"),
            ],
            "claims-processor": [
                ("INSERT", "claims", "INSERT INTO claims (claim_id, policy_id, member_id, loss_type, loss_date, status, ts) VALUES (?, ?, ?, ?, ?, 'FNOL', NOW())"),
                ("SELECT", "claims", "SELECT claim_id, status, assigned_adjuster, estimate_amount FROM claims WHERE member_id = ? ORDER BY ts DESC LIMIT 20"),
            ],
            "payment-engine": [
                ("INSERT", "ach_transactions", "INSERT INTO ach_transactions (batch_id, entry_id, routing, amount, type, status, ts) VALUES (?, ?, ?, ?, ?, 'PENDING', NOW())"),
                ("UPDATE", "account_balances", "UPDATE account_balances SET available = available + ?, posted = posted + ?, last_updated = NOW() WHERE account_id = ?"),
            ],
            "policy-manager": [
                ("SELECT", "policies", "SELECT policy_id, product_type, premium, effective_date, expiry_date FROM policies WHERE member_id = ? AND status = 'ACTIVE'"),
                ("UPDATE", "policies", "UPDATE policies SET premium = ?, effective_date = ?, status = 'RENEWED' WHERE policy_id = ?"),
            ],
            "fraud-sentinel": [
                ("INSERT", "fraud_alerts", "INSERT INTO fraud_alerts (alert_id, transaction_id, score, model_version, disposition, ts) VALUES (?, ?, ?, ?, 'PENDING', NOW())"),
                ("SELECT", "fraud_rules", "SELECT rule_id, pattern, threshold, action FROM fraud_rules WHERE product_type = ? AND active = true"),
            ],
            "auth-gateway": [
                ("SELECT", "member_credentials", "SELECT member_id, auth_method, mfa_enrolled, last_login FROM member_credentials WHERE member_id = ? AND status = 'ACTIVE'"),
                ("INSERT", "auth_events", "INSERT INTO auth_events (event_id, member_id, method, result, ip_addr, device, ts) VALUES (?, ?, ?, ?, ?, ?, NOW())"),
            ],
        }

    # ── Infrastructure ────────────────────────────────────────────────

    @property
    def hosts(self) -> list[dict[str, Any]]:
        return [
            {
                "host.name": "banking-aws-host-01",
                "host.id": "i-0a1b2c3d4e5f67890",
                "host.arch": "amd64",
                "host.type": "r6i.2xlarge",
                "host.image.id": "ami-0abcdef1234567890",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "106",
                "host.cpu.stepping": "6",
                "host.cpu.cache.l2.size": 1310720,
                "host.ip": ["10.0.3.40", "172.16.2.10"],
                "host.mac": ["0a:3b:4c:5d:6e:7f", "0a:3b:4c:5d:6e:80"],
                "os.type": "linux",
                "os.description": "Amazon Linux 2023.6.20250115",
                "cloud.provider": "aws",
                "cloud.platform": "aws_ec2",
                "cloud.region": "us-east-1",
                "cloud.availability_zone": "us-east-1a",
                "cloud.account.id": "112233445566",
                "cloud.instance.id": "i-0a1b2c3d4e5f67890",
                "cpu_count": 8,
                "memory_total_bytes": 64 * 1024 * 1024 * 1024,
                "disk_total_bytes": 500 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "banking-gcp-host-01",
                "host.id": "4567890123456789012",
                "host.arch": "amd64",
                "host.type": "n2-standard-8",
                "host.image.id": "projects/ubuntu-os-cloud/global/images/ubuntu-2204-jammy-v20250115",
                "host.cpu.model.name": "Intel(R) Xeon(R) CPU @ 2.80GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "7",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.128.2.30", "10.128.2.31"],
                "host.mac": ["42:01:0a:80:02:1e", "42:01:0a:80:02:1f"],
                "os.type": "linux",
                "os.description": "Ubuntu 22.04.5 LTS",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "us-central1",
                "cloud.availability_zone": "us-central1-a",
                "cloud.account.id": "banking-member-services-prod",
                "cloud.instance.id": "4567890123456789012",
                "cpu_count": 8,
                "memory_total_bytes": 32 * 1024 * 1024 * 1024,
                "disk_total_bytes": 256 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "banking-azure-host-01",
                "host.id": "/subscriptions/abc-123/resourceGroups/banking-rg/providers/Microsoft.Compute/virtualMachines/banking-vm-01",
                "host.arch": "amd64",
                "host.type": "Standard_D8s_v5",
                "host.image.id": "Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "106",
                "host.cpu.stepping": "6",
                "host.cpu.cache.l2.size": 1310720,
                "host.ip": ["10.3.0.20", "10.3.0.21"],
                "host.mac": ["00:0d:3a:7c:6d:5e", "00:0d:3a:7c:6d:5f"],
                "os.type": "linux",
                "os.description": "Ubuntu 22.04.5 LTS",
                "cloud.provider": "azure",
                "cloud.platform": "azure_vm",
                "cloud.region": "eastus",
                "cloud.availability_zone": "eastus-1",
                "cloud.account.id": "abc-123-def-456",
                "cloud.instance.id": "banking-vm-01",
                "cpu_count": 8,
                "memory_total_bytes": 32 * 1024 * 1024 * 1024,
                "disk_total_bytes": 512 * 1024 * 1024 * 1024,
            },
        ]

    @property
    def k8s_clusters(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "banking-eks-cluster",
                "provider": "aws",
                "platform": "aws_eks",
                "region": "us-east-1",
                "zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
                "os_description": "Amazon Linux 2",
                "services": ["mobile-gateway", "claims-processor", "payment-engine"],
            },
            {
                "name": "banking-gke-cluster",
                "provider": "gcp",
                "platform": "gcp_gke",
                "region": "us-central1",
                "zones": ["us-central1-a", "us-central1-b", "us-central1-c"],
                "os_description": "Container-Optimized OS",
                "services": ["policy-manager", "fraud-sentinel", "auth-gateway"],
            },
            {
                "name": "banking-aks-cluster",
                "provider": "azure",
                "platform": "azure_aks",
                "region": "eastus",
                "zones": ["eastus-1", "eastus-2", "eastus-3"],
                "os_description": "Ubuntu 22.04 LTS",
                "services": ["quote-engine", "member-portal", "document-vault"],
            },
        ]

    # ── Theme ─────────────────────────────────────────────────────────

    @property
    def theme(self) -> UITheme:
        return UITheme(
            bg_primary="#001a33",
            bg_secondary="#002244",
            bg_tertiary="#003366",
            accent_primary="#0067B1",
            accent_secondary="#4da6e8",
            text_primary="#e8f0f8",
            text_secondary="#8ab4d4",
            text_accent="#4da6e8",
            status_nominal="#3fb950",
            status_warning="#d29922",
            status_critical="#f85149",
            status_info="#4da6e8",
            font_family="'Inter', 'Segoe UI', system-ui, sans-serif",
            font_mono="'JetBrains Mono', 'Fira Code', monospace",
            chaos_title="Incident Simulator",
            service_label="Service",
            channel_label="Channel",
        )

    @property
    def countdown_config(self) -> CountdownConfig:
        return CountdownConfig(enabled=False)

    # ── Agent Config ──────────────────────────────────────────────────

    @property
    def agent_config(self) -> dict[str, Any]:
        return {
            "id": "banking-ops-analyst",
            "name": "Member Services Operations Analyst",
            "assessment_tool_name": "member_services_assessment",
            "system_prompt": (
                "You are the Member Services Operations Analyst, an expert AI assistant for "
                "the retail banking platform. You help operations teams "
                "investigate incidents, analyze service health, and provide root cause analysis "
                "for fault conditions across 9 member services spanning AWS, GCP, and Azure. "
                "You have deep expertise in mobile banking operations, insurance claims processing "
                "(FNOL, photo estimation, disbursement), payment processing (ACH, wire, bill pay, "
                "card authorization), fraud detection and prevention, biometric authentication, "
                "MFA delivery, policy administration, VA home loan underwriting, and document "
                "management. You understand military-specific needs including deployment support, "
                "PCS (Permanent Change of Station) relocation impacts, SCRA (Servicemembers Civil "
                "Relief Act) benefits, DFAS pay processing, and OCONUS member challenges. "
                "When investigating incidents, search for these system identifiers in logs: "
                "Mobile faults (MOBILE-API-TIMEOUT, MOBILE-DEPOSIT-FAIL, MOBILE-NOTIF-STORM), "
                "Payment faults (PAY-ACH-DELAY, PAY-BILLPAY-FAIL, PAY-OFAC-BLOCK, PAY-CARD-AUTH-FAIL), "
                "Claims faults (CLAIMS-FNOL-BACKLOG, CLAIMS-PHOTO-EST-TIMEOUT, CLAIMS-DISBURSEMENT-FAIL), "
                "Policy faults (POLICY-RENEWAL-FAIL, UW-RULES-ENGINE-ERR, UW-VA-RATELOCK-FAIL), "
                "Auth faults (AUTH-BIOMETRIC-DEGRADE, AUTH-MFA-DELIVERY-FAIL), "
                "Fraud faults (FRAUD-FP-SURGE), "
                "Portal faults (PORTAL-SESSION-CASCADE), "
                "Document faults (DOC-UPLOAD-FAIL), "
                "and Infrastructure faults (INFRA-DB-REPL-LAG, INFRA-CERT-EXPIRE). "
                "Log messages are in body.text — NEVER search the body field alone."
            ),
        }

    @property
    def assessment_tool_config(self) -> dict[str, Any]:
        return {
            "id": "member_services_assessment",
            "description": (
                "Comprehensive member services platform health assessment. Evaluates all "
                "services against operational readiness criteria for mobile banking, claims "
                "processing, payment systems, and authentication services. "
                "Returns data for operational evaluation across digital banking, insurance, "
                "payments, fraud detection, and member portal systems. "
                "Log message field: body.text (never use 'body' alone)."
            ),
        }

    @property
    def knowledge_base_docs(self) -> list[dict[str, Any]]:
        return []  # Populated by deployer from channel_registry

    # ── Service Classes ───────────────────────────────────────────────

    def get_service_classes(self) -> list[type]:
        from scenarios.banking.services.mobile_gateway import MobileGatewayService
        from scenarios.banking.services.claims_processor import ClaimsProcessorService
        from scenarios.banking.services.payment_engine import PaymentEngineService
        from scenarios.banking.services.policy_manager import PolicyManagerService
        from scenarios.banking.services.fraud_sentinel import FraudSentinelService
        from scenarios.banking.services.auth_gateway import AuthGatewayService
        from scenarios.banking.services.quote_engine import QuoteEngineService
        from scenarios.banking.services.member_portal import MemberPortalService
        from scenarios.banking.services.document_vault import DocumentVaultService

        return [
            MobileGatewayService,
            ClaimsProcessorService,
            PaymentEngineService,
            PolicyManagerService,
            FraudSentinelService,
            AuthGatewayService,
            QuoteEngineService,
            MemberPortalService,
            DocumentVaultService,
        ]

    # ── Trace Attributes & RCA ───────────────────────────────────────

    def get_trace_attributes(self, service_name: str, rng) -> dict:
        session_epoch = int(time.time()) % 86400
        base = {
            "member.segment": rng.choice(["active-duty", "veteran", "family", "retired", "guard-reserve"]),
            "platform.channel": rng.choice(["mobile", "web", "api", "ivr"]),
        }
        svc_attrs = {
            "mobile-gateway": {
                "gateway.platform": rng.choice(["iOS", "Android", "iPadOS"]),
                "gateway.api_version": rng.choice(["v1.8.2", "v1.9.0", "v2.0.0-beta", "v1.8.5"]),
                "gateway.session_age_s": session_epoch % 3600,
                "gateway.device_trust_level": rng.choice(["trusted", "registered", "unknown"]),
            },
            "claims-processor": {
                "claims.type": rng.choice(["auto_collision", "auto_comprehensive", "homeowners", "renters", "life"]),
                "claims.priority": rng.choice(["standard", "high", "urgent", "catastrophe"]),
                "claims.adjuster_pool": rng.choice(["internal", "DRP_network", "CAT_team", "virtual"]),
                "claims.fnol_channel": rng.choice(["mobile_app", "call_center", "web_portal", "agent"]),
            },
            "payment-engine": {
                "payment.method": rng.choice(["ACH", "wire", "debit_card", "bill_pay", "P2P", "check"]),
                "payment.amount_tier": rng.choice(["micro", "standard", "large", "wire_threshold"]),
                "payment.rail": rng.choice(["FedACH", "FedWire", "Visa_Direct", "RTP", "NACHA_batch"]),
                "payment.compliance_check": rng.choice(["OFAC_clear", "CTR_pending", "SAR_review", "clear"]),
            },
            "policy-manager": {
                "policy.type": rng.choice(["auto", "homeowners", "renters", "umbrella", "life", "VPP"]),
                "policy.renewal_status": rng.choice(["active", "pending_renewal", "grace_period", "lapsed"]),
                "policy.underwriting_tier": rng.choice(["preferred", "standard", "non_standard", "military_discount"]),
                "policy.state_jurisdiction": rng.choice(["TX", "VA", "CA", "FL", "NC", "GA", "WA"]),
            },
            "fraud-sentinel": {
                "fraud.risk_score": rng.randint(0, 100),
                "fraud.model_version": rng.choice(["FraudNet-v5.2", "FraudNet-v5.3-canary", "FraudNet-v5.1"]),
                "fraud.detection_method": rng.choice(["ML_ensemble", "rules_engine", "velocity_check", "geo_analysis"]),
                "fraud.alert_disposition": rng.choice(["auto_cleared", "pending_review", "confirmed", "escalated"]),
            },
            "auth-gateway": {
                "auth.method": rng.choice(["biometric_face", "biometric_fingerprint", "mfa_sms", "mfa_totp", "password", "CAC_PIV"]),
                "auth.device_trust": rng.choice(["enrolled", "verified", "new_device", "jailbroken_suspect"]),
                "auth.session_type": rng.choice(["interactive", "api_token", "service_account", "refresh_token"]),
                "auth.risk_signal": rng.choice(["low", "medium", "elevated", "high"]),
            },
            "quote-engine": {
                "quote.product_line": rng.choice(["auto", "homeowners", "renters", "umbrella", "VA_mortgage", "life"]),
                "quote.rating_algorithm": rng.choice(["actuarial_v7", "ML_pricing_v3", "manual_rate", "competitive_match"]),
                "quote.military_discount_applied": rng.choice([True, True, True, False]),
                "quote.bundle_eligible": rng.choice([True, False]),
            },
            "member-portal": {
                "portal.page_context": rng.choice(["dashboard", "accounts", "claims", "insurance", "investments", "settings"]),
                "portal.session_duration_s": rng.randint(30, 1800),
                "portal.accessibility_mode": rng.choice(["standard", "high_contrast", "screen_reader", "large_text"]),
                "portal.content_personalization": rng.choice(["active_duty", "veteran", "spouse", "general"]),
            },
            "document-vault": {
                "document.type": rng.choice(["DD214", "COE_VA_loan", "claims_photo", "policy_dec_page", "tax_1099", "bank_statement"]),
                "document.classification": rng.choice(["PII", "PHI", "financial", "military_record", "general"]),
                "document.storage_tier": rng.choice(["hot", "warm", "archive", "compliance_hold"]),
                "document.encryption_status": rng.choice(["AES256_KMS", "AES256_SSE", "client_side_encrypted"]),
            },
        }
        base.update(svc_attrs.get(service_name, {}))
        return base

    def get_rca_clues(self, channel: int, service_name: str, rng) -> dict:
        clues = {
            1: {  # Fraud Model False Positive Surge
                "fraud-sentinel": {"fraud.false_positive_rate_pct": round(rng.uniform(8, 18), 1), "fraud.trigger_pattern": "PCS_SEASON"},
                "payment-engine": {"payment.blocked_txn_revenue_per_hr": rng.randint(500000, 1200000), "payment.auto_decline_count": rng.randint(200, 800)},
                "mobile-gateway": {"gateway.member_block_complaints": rng.randint(100, 400), "gateway.txn_retry_surge": True},
                "auth-gateway": {"auth.pcs_whitelist_status": "NOT_APPLIED", "auth.geo_velocity_alerts": rng.randint(500, 2000)},
            },
            2: {  # Mobile Deposit Processing Failure
                "mobile-gateway": {"gateway.deposit_ocr_quality": round(rng.uniform(55, 84), 1), "gateway.image_capture_retries": rng.randint(2, 5)},
                "document-vault": {"document.s3_upload_status": "TIMEOUT", "document.queue_depth": rng.randint(500, 2000)},
                "claims-processor": {"claims.deposit_image_missing": True, "claims.pipeline_blocked_by": "document-vault"},
                "payment-engine": {"payment.deposit_hold_policy": "REG_CC_EXTENDED", "payment.micr_parse_status": "FAILED"},
            },
            3: {  # Push Notification Storm
                "mobile-gateway": {"gateway.notification_rate_per_min": rng.randint(8000, 15000), "gateway.dedup_cache_status": "OVERFLOW"},
                "auth-gateway": {"auth.notification_trigger_source": "event_replay", "auth.apns_throttle_status": "RATE_LIMITED"},
                "member-portal": {"portal.complaint_volume": rng.randint(150, 400), "portal.unsubscribe_spike": True},
                "fraud-sentinel": {"fraud.notification_anomaly_detected": True, "fraud.alert_source": "transaction_processor_replay"},
            },
            4: {  # ACH Direct Deposit Delay
                "payment-engine": {"payment.ach_batch_stage": "account_lookup_stalled", "payment.nacha_entry_count": rng.randint(20000, 40000)},
                "mobile-gateway": {"gateway.early_pay_status": "DELAYED", "gateway.member_inquiries_spike": True},
                "member-portal": {"portal.balance_display_stale": True, "portal.dfas_pay_eta": "UNKNOWN"},
                "fraud-sentinel": {"fraud.ach_screening_queue_depth": rng.randint(5000, 15000), "fraud.ofac_response_ms": rng.randint(30000, 60000)},
            },
            5: {  # Bill Pay Execution Failure
                "payment-engine": {"payment.billpay_fedach_window": "CLOSED", "payment.retry_attempts_exhausted": True},
                "member-portal": {"portal.billpay_failure_notifications": rng.randint(100, 500), "portal.late_fee_risk_count": rng.randint(50, 200)},
                "mobile-gateway": {"gateway.billpay_status_queries_spike": rng.randint(2000, 8000), "gateway.payment_confirmation": "PENDING"},
                "document-vault": {"document.payment_receipt_generation": "BLOCKED", "document.receipt_queue_depth": rng.randint(200, 800)},
            },
            6: {  # Wire Transfer OFAC Block
                "payment-engine": {"payment.wire_hold_reason": "OFAC_SDN_MATCH", "payment.bsa_review_sla_hours": 24},
                "fraud-sentinel": {"fraud.ofac_match_algorithm": "JARO_WINKLER", "fraud.match_score_pct": round(rng.uniform(75, 95), 1)},
                "member-portal": {"portal.wire_status_display": "HELD_FOR_REVIEW", "portal.member_notification": "PENDING"},
                "auth-gateway": {"auth.wire_authorization_level": "BSA_OFFICER_REQUIRED", "auth.dual_control_status": "AWAITING_SECOND"},
            },
            7: {  # Debit Card Authorization Failure
                "payment-engine": {"payment.iso8583_response_code": rng.choice(["05", "91", "96"]), "payment.network_auth_status": "DECLINED"},
                "fraud-sentinel": {"fraud.card_risk_score": rng.randint(5, 25), "fraud.card_screening_result": "PASS"},
                "mobile-gateway": {"gateway.card_decline_display": "NETWORK_ERROR", "gateway.stip_eligible": False},
                "member-portal": {"portal.card_decline_notification_sent": True, "portal.merchant_mcc": rng.choice(["5411", "5541", "5999", "7011"])},
            },
            8: {  # Claims FNOL Intake Backlog
                "claims-processor": {"claims.intake_rate_per_hr": rng.randint(120, 180), "claims.processing_rate_per_hr": rng.randint(60, 95)},
                "document-vault": {"document.fnol_image_queue": rng.randint(500, 2000), "document.cat_event_volume": "SURGE"},
                "payment-engine": {"payment.claim_advance_requests": rng.randint(50, 200), "payment.rental_extensions_pending": rng.randint(80, 300)},
                "member-portal": {"portal.fnol_self_service_enabled": True, "portal.claims_status_queries_spike": rng.randint(3000, 10000)},
            },
            9: {  # Photo Damage Estimation Timeout
                "claims-processor": {"claims.gpu_utilization_pct": round(rng.uniform(93, 99), 1), "claims.model_inference_queue": rng.randint(500, 1200)},
                "document-vault": {"document.damage_photo_resolution": rng.choice(["4K", "1080p", "720p"]), "document.image_preprocessing_ms": rng.randint(300, 800)},
                "member-portal": {"portal.estimate_eta_display": "DELAYED", "portal.manual_adjuster_fallback": True},
                "mobile-gateway": {"gateway.photo_upload_success_rate": round(rng.uniform(0.85, 0.95), 2), "gateway.damage_estimate_timeout": True},
            },
            10: {  # Claims Payment Disbursement Failure
                "claims-processor": {"claims.disbursement_error_type": rng.choice(["PAYEE_ACCOUNT_MISMATCH", "ROUTING_VALIDATION_FAIL", "DAILY_LIMIT_EXCEEDED"]), "claims.days_since_loss": rng.randint(5, 30)},
                "payment-engine": {"payment.disbursement_retry_count": 3, "payment.drp_payee_validation": "FAILED"},
                "member-portal": {"portal.rental_extension_needed": True, "portal.member_outreach_status": "PENDING"},
                "document-vault": {"document.w9_on_file": rng.choice([True, False]), "document.tax_1099_status": "BLOCKED"},
            },
            11: {  # Policy Renewal Batch Failure
                "policy-manager": {"policy.renewal_batch_failure_reason": rng.choice(["RATING_ENGINE_TIMEOUT", "MVR_DATA_STALE", "CLUE_SERVICE_UNAVAILABLE"]), "policy.scra_protected_count": rng.randint(5, 20)},
                "quote-engine": {"quote.rating_engine_response_ms": rng.randint(8000, 30000), "quote.actuarial_model_status": "DEGRADED"},
                "member-portal": {"portal.renewal_notice_generation": "BLOCKED", "portal.coverage_gap_risk_count": rng.randint(100, 500)},
                "document-vault": {"document.dec_page_generation": "QUEUED", "document.renewal_docs_pending": rng.randint(200, 800)},
            },
            12: {  # Underwriting Rules Engine Error
                "quote-engine": {"quote.rules_engine_conflict_rate_pct": round(rng.uniform(1.5, 4.0), 1), "quote.change_set_version": "CS-4827"},
                "policy-manager": {"policy.manual_uw_queue_depth": rng.randint(50, 300), "policy.incorrect_decline_count": rng.randint(10, 80)},
                "member-portal": {"portal.application_status_display": "UNDER_REVIEW", "portal.member_callback_requested": rng.randint(20, 100)},
                "claims-processor": {"claims.coverage_verification_delayed": True, "claims.rule_conflict_flag": True},
            },
            13: {  # VA Loan Rate Lock Failure
                "quote-engine": {"quote.gnma_mbs_feed_age_min": rng.randint(30, 120), "quote.secondary_market_status": "STALE"},
                "payment-engine": {"payment.va_funding_fee_calc_status": "OK", "payment.escrow_setup_blocked": True},
                "member-portal": {"portal.rate_quote_display": "UNAVAILABLE", "portal.coe_verification_status": "VALID"},
                "document-vault": {"document.coe_document_on_file": True, "document.loan_package_generation": "BLOCKED"},
            },
            14: {  # Biometric Auth Service Degradation
                "auth-gateway": {"auth.biometric_fail_rate_pct": round(rng.uniform(20, 40), 1), "auth.liveness_check_status": "DEGRADED"},
                "mobile-gateway": {"gateway.biometric_sdk_version": rng.choice(["BioAuth-v3.1", "BioAuth-v3.0"]), "gateway.fallback_pin_surge_pct": rng.randint(200, 500)},
                "member-portal": {"portal.auth_fallback_active": True, "portal.call_center_wait_min": rng.randint(15, 35)},
                "fraud-sentinel": {"fraud.identity_verification_degraded": True, "fraud.biometric_spoof_attempts": rng.randint(0, 5)},
            },
            15: {  # MFA Delivery Failure
                "auth-gateway": {"auth.sms_delivery_rate_pct": round(rng.uniform(60, 78), 1), "auth.carrier_block_list": rng.choice(["T-MOBILE", "VERIZON", "T-MOBILE,VERIZON"])},
                "mobile-gateway": {"gateway.mfa_fallback_channel": rng.choice(["PUSH", "EMAIL", "TOTP"]), "gateway.oconus_members_affected": rng.randint(200, 500)},
                "member-portal": {"portal.deployed_member_lockout_count": rng.randint(50, 150), "portal.scra_flag_check": True},
                "payment-engine": {"payment.mfa_blocked_transactions": rng.randint(500, 2000), "payment.step_up_auth_failures": rng.randint(100, 500)},
            },
            16: {  # Mobile App API Timeout
                "mobile-gateway": {"gateway.connection_pool_active": rng.randint(800, 1000), "gateway.backend_routing_phase": "stalled"},
                "auth-gateway": {"auth.token_verify_latency_ms": rng.randint(400, 900), "auth.session_cache_hit_rate": round(rng.uniform(0.1, 0.3), 2)},
                "member-portal": {"upstream.degraded_dependency": "mobile-gateway", "portal.response_queue_depth": rng.randint(1500, 3000)},
                "payment-engine": {"payment.upstream_timeout_count": rng.randint(50, 200), "payment.circuit_breaker_state": "HALF_OPEN"},
            },
            17: {  # Member Session Timeout Cascade
                "member-portal": {"portal.sessions_lost": rng.randint(10000, 50000), "portal.redis_cluster_status": "PRIMARY_DOWN"},
                "auth-gateway": {"auth.reauth_storm_rate_per_min": rng.randint(2000, 8000), "auth.circuit_breaker_state": "OPEN"},
                "mobile-gateway": {"gateway.session_recovery_attempts": rng.randint(5000, 20000), "gateway.jwt_extension_enabled": False},
                "payment-engine": {"payment.in_flight_txn_orphaned": rng.randint(50, 300), "payment.session_dependent_holds": rng.randint(20, 100)},
            },
            18: {  # Document Upload Service Failure
                "document-vault": {"document.s3_error_type": rng.choice(["S3_WRITE_TIMEOUT", "BUCKET_QUOTA_EXCEEDED", "ENCRYPTION_KEY_ERROR"]), "document.upload_queue_depth": rng.randint(1000, 5000)},
                "member-portal": {"portal.upload_retry_display": "FAILED", "portal.member_docs_pending": rng.randint(200, 1000)},
                "claims-processor": {"claims.photo_attachment_blocked": True, "claims.claims_without_docs": rng.randint(50, 200)},
                "policy-manager": {"policy.dec_page_storage_blocked": True, "policy.renewal_docs_delayed": rng.randint(100, 400)},
            },
            19: {  # Database Replication Lag
                "payment-engine": {"payment.db_repl_lag_ms": rng.randint(5000, 30000), "payment.wal_replay_deficit_pct": round(rng.uniform(20, 50), 0)},
                "mobile-gateway": {"gateway.stale_balance_reads_pct": round(rng.uniform(25, 40), 1), "gateway.read_routing_policy": "ROUND_ROBIN"},
                "claims-processor": {"claims.claim_status_stale": True, "claims.db_read_routing": "REPLICA_LAGGED"},
                "member-portal": {"portal.balance_inconsistency_reports": rng.randint(50, 200), "portal.overdraft_risk_elevated": True},
            },
            20: {  # Certificate Expiration Cascade
                "auth-gateway": {"auth.tls_cert_remaining_hours": round(rng.uniform(-2, 4), 1), "auth.acme_renewal_status": "DNS_CHALLENGE_TIMEOUT"},
                "mobile-gateway": {"gateway.tls_handshake_failures": rng.randint(5000, 20000), "gateway.cert_pinning_fallback": rng.choice([True, False])},
                "payment-engine": {"payment.mtls_validation_status": "WARNING", "payment.cert_chain_valid": False},
                "member-portal": {"portal.cert_status": "DEGRADED", "portal.pinned_cert_fallback_active": True},
            },
        }
        channel_clues = clues.get(channel, {})
        return channel_clues.get(service_name, {})

    def get_correlation_attribute(self, channel: int, is_error: bool, rng) -> dict:
        correlation_attrs = {
            1: ("runtime.fraud_model_weights", "FraudNet-v5.3-canary-weights"),
            2: ("infra.ocr_engine_version", "tesseract-v5.3.4-patch1"),
            3: ("runtime.notification_broker", "rabbitmq-v3.12.14-hotfix"),
            4: ("infra.nacha_parser_version", "nacha-proc-v4.1.0-rc2"),
            5: ("deployment.billpay_scheduler", "quartz-v2.5.0-experimental"),
            6: ("infra.ofac_sdn_list_version", "sdn-2026-02-15-delta"),
            7: ("network.card_network_proxy", "visa-proxy-v1.4.3-unstable"),
            8: ("deployment.claims_intake_build", "fnol-intake-v3.7.0-beta"),
            9: ("runtime.damage_model_weights", "DamageNet-v4.2.1-retrain"),
            10: ("infra.disbursement_routing_table", "pay-route-v2.1.0-rc3"),
            11: ("deployment.rating_engine_rules", "actuarial-rules-CS-4827"),
            12: ("runtime.underwriting_rule_chain", "uw-rules-v7.4.1-canary"),
            13: ("infra.mbs_pricing_feed", "gnma-feed-adapter-v2.0.3-patch"),
            14: ("deployment.biometric_sdk", "bioauth-v3.1.2-rc1"),
            15: ("infra.sms_gateway_config", "twilio-gw-v4.8.0-hotfix"),
            16: ("deployment.api_gateway_version", "gateway-v2.9.1-canary"),
            17: ("infra.redis_cluster_config", "redis-7.2.4-sentinel-patch"),
            18: ("deployment.s3_endpoint_config", "vpc-endpoint-v1.3.0-rc2"),
            19: ("infra.aurora_replica_config", "aurora-pg15-iops-tuned-v2"),
            20: ("deployment.cert_manager_version", "cert-manager-v1.14.5-rc1"),
        }
        attr_key, attr_val = correlation_attrs.get(channel, ("deployment.api_gateway_version", "unknown"))
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
        member_prefixes = ["M", "MBR", "USR"]
        device_types = ["iPhone_15_Pro", "Samsung_S24", "iPad_Air", "Pixel_8", "iPhone_14"]
        endpoints = [
            "/api/v1/mobile/accounts", "/api/v1/mobile/transfer",
            "/api/v1/mobile/deposit", "/api/v1/mobile/pay-bills",
            "/api/v1/mobile/claims", "/api/v1/mobile/insurance",
        ]
        payee_names = [
            "Auto Insurance Premium", "Credit Union Transfer", "AT&T Wireless",
            "GEICO", "State Farm", "Mortgage Company", "Electric Utility",
            "Water Authority", "Comcast", "Progressive Insurance",
        ]
        insurance_products = [
            "AUTO_PERSONAL", "AUTO_COMMERCIAL", "HOMEOWNERS_HO3",
            "RENTERS_HO4", "UMBRELLA", "VALUABLE_PERSONAL_PROPERTY",
        ]
        cat_events = [
            "CAT-2026-GULF-HURRICANE", "CAT-2026-TX-HAILSTORM",
            "CAT-2026-CA-WILDFIRE", "CAT-2026-FL-FLOODING",
            "CAT-2026-CO-TORNADO", "CAT-2026-NC-ICE-STORM",
        ]
        cat_regions = [
            "Gulf Coast TX", "San Antonio TX", "Jacksonville FL",
            "Virginia Beach VA", "Colorado Springs CO", "Fayetteville NC",
        ]
        vehicle_descs = [
            "2024 Toyota Camry SE", "2023 Ford F-150 XLT",
            "2024 Honda CR-V EX", "2023 Chevrolet Silverado 1500",
            "2024 Hyundai Tucson SEL", "2023 Jeep Wrangler Rubicon",
        ]
        claim_payees = [
            "Caliber Collision", "Service King", "ABRA Auto Body",
            "Gerber Collision", "Maaco", "Member Direct Deposit",
        ]
        bio_methods = ["FACE_ID", "FINGERPRINT", "VOICE_PRINT"]
        mfa_channels = ["SMS", "EMAIL", "PUSH", "TOTP"]
        mfa_providers = ["Twilio", "AWS_SNS", "SendGrid", "Firebase_Cloud_Messaging"]
        mfa_errors = [
            "CARRIER_BLOCKED", "RATE_LIMIT_EXCEEDED", "INVALID_NUMBER",
            "PROVIDER_TIMEOUT", "SHORT_CODE_FILTERED",
        ]
        fraud_models = ["FraudNet-v5.2", "DeepFraud-v3.1", "RiskScore-v4.0"]
        fraud_patterns = [
            "PCS_GEO_VELOCITY", "NEW_DEVICE_BURST", "CARD_NOT_PRESENT_SPIKE",
            "ACH_RETURN_PATTERN", "ACCOUNT_TAKEOVER_SIG",
        ]
        session_triggers = [
            "redis_failover", "session_store_corruption",
            "config_push_error", "cert_rotation_failure",
        ]
        doc_types = [
            "CLAIM_PHOTO", "POLICY_DEC_PAGE", "ID_VERIFICATION",
            "PROOF_OF_LOSS", "COE_VA_LOAN", "DD214_DISCHARGE",
        ]
        upload_errors = [
            "S3_WRITE_TIMEOUT", "BUCKET_QUOTA_EXCEEDED",
            "ENCRYPTION_KEY_ERROR", "NETWORK_TIMEOUT",
        ]
        cert_domains = [
            "mobile.retailbank.com", "api.retailbank.com", "auth.retailbank.com",
            "portal.retailbank.com", "claims.retailbank.com",
        ]
        cert_issuers = ["DigiCert", "AWS_ACM", "Let's_Encrypt"]
        db_clusters = ["banking-aurora-payments", "banking-aurora-members", "banking-aurora-claims"]
        wire_countries = ["AE", "DE", "JP", "KR", "GB", "IT"]
        beneficiary_banks = [
            "Deutsche Bank", "Barclays", "MUFG Bank",
            "Kookmin Bank", "Emirates NBD", "UniCredit",
        ]
        swift_codes = ["DEUTDEFF", "BARCGB22", "BOTKJPJT", "CZNBKRSE", "EABOROBI", "UNCRITMM"]
        wire_purposes = ["PCS_RELOCATION", "FAMILY_SUPPORT", "DEPLOYMENT_EXPENSE", "EDUCATION", "REAL_ESTATE"]
        uw_rules = [
            "military_discount_eligibility", "multi_policy_bundle",
            "garaging_risk_factor", "vehicle_safety_rating",
            "deployment_surcharge_waiver", "good_driver_discount",
        ]
        decline_codes = ["05", "14", "51", "54", "61", "91", "96"]
        card_networks = ["VISA", "MASTERCARD", "AMEX"]
        merchant_names = [
            "AAFES PX Fort Liberty", "Commissary DeCA", "Navy Exchange",
            "Shell Gas Station", "Amazon.com", "Walmart Supercenter",
        ]
        notif_channels = ["APNS", "FCM", "SMS_GATEWAY", "EMAIL_RELAY"]
        deposit_stages = ["amount_verify", "fraud_screen", "funds_hold", "ocr_extraction"]
        deposit_errors = [
            "AMOUNT_MISMATCH", "DUPLICATE_DETECTED", "IMAGE_QUALITY_LOW",
            "MICR_UNREADABLE", "ENDORSEMENT_MISSING",
        ]
        billpay_reasons = [
            "INSUFFICIENT_FUNDS", "PAYEE_ACCOUNT_CLOSED",
            "ROUTING_NUMBER_INVALID", "DUPLICATE_PAYMENT", "FEDACH_WINDOW_CLOSED",
        ]
        disbursement_methods = ["ACH_CREDIT", "CHECK_MAIL", "VIRTUAL_CARD", "WIRE"]
        disbursement_errors = [
            "PAYEE_ACCOUNT_MISMATCH", "DAILY_LIMIT_EXCEEDED",
            "ROUTING_VALIDATION_FAIL", "FRAUD_HOLD_ACTIVE",
        ]
        renewal_reasons = [
            "RATING_ENGINE_TIMEOUT", "MVR_DATA_STALE",
            "CLUE_SERVICE_UNAVAILABLE", "PREMIUM_CALC_OVERFLOW",
        ]
        ratelock_errors = [
            "GNMA_MBS_FEED_DOWN", "SECONDARY_MARKET_CLOSED",
            "PRICING_ENGINE_TIMEOUT", "RATE_SHEET_EXPIRED",
        ]
        garaging_zips = ["78209", "78216", "32225", "23452", "80917", "28307"]
        ofac_lists = ["SDN", "CONSOLIDATED", "SSI", "FSE"]
        ofac_match_names = [
            "AL-RASHID Trading Co", "PETROCHINA International",
            "ROSNEFT Oil Company", "BANK MELLI IRAN",
        ]

        return {
            # Member identifiers
            "member_id": f"{random.choice(member_prefixes)}-{random.randint(1000000, 9999999)}",
            "member_name": random.choice([
                "James Wilson", "Sarah Mitchell", "Robert Thompson",
                "Maria Garcia", "David Chen", "Jennifer Adams",
            ]),
            "device_type": random.choice(device_types),
            "endpoint": random.choice(endpoints),
            # Mobile / API
            "latency_ms": random.randint(3000, 30000),
            "sla_ms": 2000,
            # Deposit
            "deposit_id": f"DEP-{random.randint(100000, 999999)}",
            "deposit_amount": round(random.uniform(50.0, 5000.0), 2),
            "deposit_stage": random.choice(deposit_stages),
            "deposit_error": random.choice(deposit_errors),
            "routing_number": f"{random.randint(100000000, 999999999)}",
            "acct_last4": f"{random.randint(1000, 9999)}",
            # Notifications
            "notif_rate": random.randint(500, 5000),
            "notif_max": 200,
            "notif_dupes": random.randint(100, 2000),
            "notif_channel": random.choice(notif_channels),
            "notif_window_s": random.randint(60, 600),
            # ACH
            "ach_batch_id": f"ACH-{random.randint(100000, 999999)}",
            "ach_entry_count": random.randint(1000, 50000),
            "ach_delay_min": random.randint(30, 480),
            "ach_sla_min": 15,
            "ach_type": random.choice(["MILITARY_PAY", "ALLOTMENT", "DIRECT_DEPOSIT", "DFAS_RETIRED_PAY"]),
            # Bill pay
            "billpay_id": f"BP-{random.randint(100000, 999999)}",
            "payee_name": random.choice(payee_names),
            "billpay_amount": round(random.uniform(25.0, 3000.0), 2),
            "billpay_reason": random.choice(billpay_reasons),
            "available_balance": round(random.uniform(100.0, 25000.0), 2),
            # Wire transfer
            "wire_id": f"WR-{random.randint(100000, 999999)}",
            "wire_amount": round(random.uniform(1000.0, 100000.0), 2),
            "ofac_score": round(random.uniform(75.0, 98.0), 1),
            "ofac_list": random.choice(ofac_lists),
            "ofac_match_name": random.choice(ofac_match_names),
            "wire_country": random.choice(wire_countries),
            "beneficiary_bank": random.choice(beneficiary_banks),
            "swift_code": random.choice(swift_codes),
            "wire_purpose": random.choice(wire_purposes),
            # Card auth
            "auth_id": f"AUTH-{random.randint(100000, 999999)}",
            "card_last4": f"{random.randint(1000, 9999)}",
            "auth_amount": round(random.uniform(5.0, 2000.0), 2),
            "merchant_name": random.choice(merchant_names),
            "merchant_mcc": random.choice(["5411", "5541", "5912", "5999", "7011", "5311"]),
            "decline_code": random.choice(decline_codes),
            "card_network": random.choice(card_networks),
            # Claims
            "claim_id": f"CLM-{random.randint(100000, 999999)}",
            "claims_queue": random.randint(200, 2000),
            "claims_wait_min": random.randint(30, 240),
            "cat_event": random.choice(cat_events),
            "cat_region": random.choice(cat_regions),
            "claims_pending": random.randint(100, 1000),
            # Photo estimation
            "model_latency_ms": random.randint(10000, 60000),
            "model_sla_ms": 5000,
            "vehicle_desc": random.choice(vehicle_descs),
            "image_count": random.randint(4, 12),
            # Claims payment
            "claim_amount": round(random.uniform(500.0, 50000.0), 2),
            "claim_payee": random.choice(claim_payees),
            "disbursement_method": random.choice(disbursement_methods),
            "disbursement_error": random.choice(disbursement_errors),
            # Policy renewal
            "renewal_batch_id": f"RNW-{random.randint(1000, 9999)}",
            "renewal_count": random.randint(500, 5000),
            "renewal_failed": random.randint(50, 500),
            "renewal_reason": random.choice(renewal_reasons),
            "renewal_date": "2026-03-01",
            "deployment_hold": random.choice(["true", "false"]),
            # Underwriting
            "app_id": f"APP-{random.randint(100000, 999999)}",
            "insurance_product": random.choice(insurance_products),
            "failed_rule": random.choice(uw_rules),
            "expected_decision": random.choice(["APPROVE", "REFER"]),
            "actual_decision": random.choice(["DECLINE", "APPROVE", "REFER"]),
            "garaging_zip": random.choice(garaging_zips),
            # VA loan
            "loan_id": f"VA-{random.randint(100000, 999999)}",
            "va_rate": round(random.uniform(5.5, 7.5), 3),
            "lock_days": random.choice([30, 45, 60]),
            "loan_amount": round(random.uniform(150000, 750000), 0),
            "va_funding_fee": round(random.uniform(1.25, 3.3), 2),
            "ratelock_error": random.choice(ratelock_errors),
            # Biometric auth
            "bio_method": random.choice(bio_methods),
            "bio_fail_rate": round(random.uniform(15.0, 45.0), 1),
            "bio_threshold": 10.0,
            "bio_attempts": random.randint(500, 3000),
            "bio_fallback": random.choice(["PIN", "PASSWORD", "SECURITY_QUESTIONS"]),
            # MFA
            "mfa_channel": random.choice(mfa_channels),
            "mfa_delivery_rate": round(random.uniform(50.0, 80.0), 1),
            "mfa_provider": random.choice(mfa_providers),
            "mfa_error": random.choice(mfa_errors),
            # Fraud
            "fraud_blocked": random.randint(50, 500),
            "fraud_window_s": random.randint(60, 600),
            "fraud_fp_rate": round(random.uniform(15.0, 65.0), 1),
            "fraud_model": random.choice(fraud_models),
            "fraud_pattern": random.choice(fraud_patterns),
            # Session cascade
            "sessions_invalidated": random.randint(5000, 50000),
            "sessions_active": random.randint(50000, 200000),
            "session_trigger": random.choice(session_triggers),
            "reauth_rate": random.randint(1000, 5000),
            # Document upload
            "upload_id": f"UPL-{random.randint(100000, 999999)}",
            "doc_type": random.choice(doc_types),
            "doc_size_mb": round(random.uniform(0.5, 25.0), 1),
            "upload_error": random.choice(upload_errors),
            # Database replication
            "db_cluster": random.choice(db_clusters),
            "db_lag_ms": random.randint(5000, 60000),
            "db_max_lag_ms": 3000,
            "db_replica": random.choice(["replica-b", "replica-c"]),
            "db_pending_txns": random.randint(1000, 50000),
            # Certificate
            "cert_domain": random.choice(cert_domains),
            "cert_hours_left": round(random.uniform(0.5, 48.0), 1),
            "cert_serial": f"{random.randint(10000000, 99999999):08X}",
            "cert_issuer": random.choice(cert_issuers),
            "cert_svc_count": random.randint(2, 6),
        }


# Module-level instance for registry discovery
scenario = BankingScenario()

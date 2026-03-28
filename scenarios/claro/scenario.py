"""Claro Network Operations Center scenario — Latin American telecom with 5G/4G, billing,
SMS, CDN, voice, and IoT services across AWS, GCP, and Azure."""

from __future__ import annotations

import random
import time
from typing import Any

from scenarios.base import BaseScenario, CountdownConfig, UITheme


class ClaroScenario(BaseScenario):
    """Claro telecom NOC platform with 9 services and 20 fault channels."""

    # ── Identity ──────────────────────────────────────────────────────

    @property
    def scenario_id(self) -> str:
        return "claro"

    @property
    def scenario_name(self) -> str:
        return "Claro Network Operations Center"

    @property
    def scenario_description(self) -> str:
        return (
            "Latin American telecom NOC managing 5G/4G mobile core, real-time billing, "
            "SMS messaging, CDN video streaming, VoIP, and IoT connectivity across "
            "18 countries and 300M+ subscribers."
        )

    @property
    def namespace(self) -> str:
        return "claro"

    # ── Services ──────────────────────────────────────────────────────

    @property
    def services(self) -> dict[str, dict[str, Any]]:
        return {
            # AWS us-east-1 — Mobile Core & Billing
            "mobile-core": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1a",
                "subsystem": "mobile_network",
                "language": "go",
            },
            "billing-engine": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1b",
                "subsystem": "charging",
                "language": "java",
            },
            "sms-gateway": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1c",
                "subsystem": "messaging",
                "language": "go",
            },
            # GCP us-central1 — Digital Services
            "customer-portal": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "digital_services",
                "language": "python",
            },
            "content-delivery": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-b",
                "subsystem": "cdn",
                "language": "go",
            },
            "network-analytics": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-c",
                "subsystem": "analytics",
                "language": "python",
            },
            # Azure eastus — Operations
            "voice-platform": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "voice",
                "language": "java",
            },
            "iot-connect": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-2",
                "subsystem": "iot",
                "language": "python",
            },
            "noc-dashboard": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-3",
                "subsystem": "operations",
                "language": "python",
            },
        }

    # ── Channel Registry ──────────────────────────────────────────────

    @property
    def channel_registry(self) -> dict[int, dict[str, Any]]:
        return {
            1: {
                "name": "5G SA Core Session Failure",
                "subsystem": "mobile_network",
                "vehicle_section": "5g_packet_core",
                "error_type": "5G-SESSION-FAIL",
                "sensor_type": "pdu_session",
                "affected_services": ["mobile-core", "billing-engine"],
                "cascade_services": ["customer-portal", "noc-dashboard"],
                "description": "5G SA PDU session establishment failures in the packet core, dropping subscriber data plane",
                "investigation_notes": (
                    "1. Check AMF (Access and Mobility Management Function) registration status — "
                    "RegistrationRejectCause=11 (PLMN_NOT_ALLOWED) indicates a roaming config issue; "
                    "cause=22 (CONGESTION) means the AMF is overloaded.\n"
                    "2. Review SMF (Session Management Function) PDU session create response — "
                    "Cause=ResourceLimitReached typically means the UPF IP pool is exhausted. "
                    "Check: kubectl exec -it smf-0 -- smf-cli show pdu-session stats\n"
                    "3. Inspect UPF (User Plane Function) tunnel health — GTP-U tunnel failures indicate "
                    "N3 interface connectivity issues between gNB and UPF. Check MTU mismatch (1500 vs 1460).\n"
                    "4. Verify N2 interface signaling between AMF and gNB — SCTP association resets will "
                    "cause mass deregistration. Check: ss -s | grep SCTP on AMF nodes.\n"
                    "5. Review NSSAI (network slice) configuration — if the requested S-NSSAI is not "
                    "supported in the HPLMN, all slice-specific sessions will fail. "
                    "Cross-reference with PCF slice policies."
                ),
                "remediation_action": "restart_smf_pod",
                "error_message": "[5G] 5G-SESSION-FAIL: imsi={imsi} pdu_session={pdu_id} cause={reject_cause} smf={smf_instance} upf={upf_node}",
                "stack_trace": (
                    "=== 5G SESSION ESTABLISHMENT FAILURE ===\n"
                    "imsi={imsi} supi=imsi-{imsi} pdu_session={pdu_id}\n"
                    "--- N1/N2 SIGNALING ---\n"
                    " STEP                 STATUS    CAUSE\n"
                    " Registration Request COMPLETE  SUCI decoded\n"
                    " Auth Challenge       COMPLETE  5G-AKA success\n"
                    " SecurityModeCmd      COMPLETE  NAS ciphered\n"
                    " PDU Sess Create Req  FAILED    {reject_cause} <<< BOTTLENECK\n"
                    " PDU Sess Create Rsp  N/A       ---\n"
                    "--- CORE NF STATUS ---\n"
                    " amf={amf_instance} smf={smf_instance} upf={upf_node}\n"
                    " nssai=01:000001 dnn=internet qos=QCI-9\n"
                    "ue_ip=UNALLOCATED tunnel_id=NONE gtp_state=FAILED\n"
                    "ACTION: trigger_pdu_retry=true notify_ran_ops=true alert=5G-SESSION-FAIL"
                ),
            },
            2: {
                "name": "LTE Handover Storm",
                "subsystem": "mobile_network",
                "vehicle_section": "lte_ran",
                "error_type": "LTE-HO-STORM",
                "sensor_type": "handover_rate",
                "affected_services": ["mobile-core", "noc-dashboard"],
                "cascade_services": ["billing-engine", "customer-portal"],
                "description": "Mass LTE X2 handover failures causing subscriber call drops across multiple eNodeBs",
                "investigation_notes": (
                    "1. Check X2 interface status between eNodeBs — HO failure cause=4 (UE_NOT_FOUND) "
                    "means the target eNodeB lost UE context, likely due to an S1/MME path reset.\n"
                    "2. Review MME (Mobility Management Entity) signaling load — if the MME is in OVERLOAD, "
                    "it sends S1AP Overload Start, causing eNodeBs to reject new connections and HOs.\n"
                    "3. Inspect S-GW (Serving Gateway) bearer modification latency — HO failures occur when "
                    "the S-GW takes >100ms to respond to Modify Bearer Requests during X2-HO.\n"
                    "4. Check the RSRPreport threshold — if RSRP <-110dBm is triggering A3 events on "
                    "many cells simultaneously, it could indicate a neighbor list misconfiguration causing "
                    "ping-pong HOs between edge cells.\n"
                    "5. Verify TA (Tracking Area) list consistency — TAU storms from boundary cells "
                    "cause signaling overload. Review TA boundary configuration in the SON system."
                ),
                "remediation_action": "reset_x2_interface",
                "error_message": "[LTE] LTE-HO-STORM: enb_src={enb_src} enb_tgt={enb_tgt} cause={ho_cause} ue_count={ue_count} drop_rate={drop_rate}%",
                "stack_trace": (
                    "=== LTE HANDOVER FAILURE REPORT ===\n"
                    "period=last_5min enb_src={enb_src} enb_tgt={enb_tgt}\n"
                    "--- X2 HANDOVER STATS ---\n"
                    " METRIC            VALUE  THRESHOLD STATUS\n"
                    " ho_attempts       {ue_count}    ---    ---\n"
                    " ho_success        12        ---    ---\n"
                    " ho_fail           {ue_count}   >10    ALERT\n"
                    " drop_rate         {drop_rate}%  >5%    CRITICAL\n"
                    "--- FAILURE BREAKDOWN ---\n"
                    " cause={ho_cause} count={ue_count}\n"
                    " x2_timeout=48  s1_path_switch=0\n"
                    " ue_ctx_missing={ue_count}  prep_fail=0\n"
                    "mme_overload=true sgw_latency_ms=340\n"
                    "ACTION: fallback_s1_ho=true page_ue=true alert=LTE-HO-STORM"
                ),
            },
            3: {
                "name": "CDR Processing Backlog",
                "subsystem": "charging",
                "vehicle_section": "cdr_mediation",
                "error_type": "BILL-CDR-BACKLOG",
                "sensor_type": "cdr_queue_depth",
                "affected_services": ["billing-engine", "mobile-core"],
                "cascade_services": ["customer-portal", "noc-dashboard"],
                "description": "Call Detail Record mediation backlog causing billing delays and possible revenue leakage",
                "investigation_notes": (
                    "1. Check CDR queue depth on the mediation server — queue >500K records indicates "
                    "the rating engine cannot keep pace with inbound CDR volume from the gateways.\n"
                    "2. Review Diameter Gy interface performance — Rf (offline charging) CDRs are "
                    "dropped silently when the CDF (Charging Data Function) is unreachable. "
                    "Check: diameterc -c Gy -s\n"
                    "3. Inspect CDR file format changes — version mismatch between ASN.1 schema "
                    "deployed on new SGSN/SGW and the mediation parser config causes parse failures.\n"
                    "4. Verify the SFTP transfer from core nodes — CDR files must arrive at mediation "
                    "within 5 minutes of closure. SFTP failures >15 min cause revenue recognition gaps.\n"
                    "5. Check duplicate suppression — during mediation restarts, reprocessing without "
                    "deduplication can cause double-billing events that trigger regulatory complaints. "
                    "Enable xDR dedup flag in mediation config before retry."
                ),
                "remediation_action": "drain_cdr_queue",
                "error_message": "[BILL] BILL-CDR-BACKLOG: queue_depth={cdr_queue} parse_fail={parse_failures} revenue_at_risk=${revenue_risk} lag_min={cdr_lag_min}",
                "stack_trace": (
                    "=== CDR MEDIATION STATUS ===\n"
                    "mediation_host=claro-cdr-med-01 period=last_15min\n"
                    "--- QUEUE METRICS ---\n"
                    " SOURCE           RECEIVED  PARSED  FAILED  QUEUED\n"
                    " 5G-SMF           128,420   98,210  2,340   {cdr_queue}\n"
                    " LTE-SGW          84,100    80,900  420     {cdr_queue}\n"
                    " VOICE-IMS        22,180    21,900  280     {cdr_queue}\n"
                    " SMS-SMSC         9,840     9,800   40      {cdr_queue}\n"
                    "--- BOTTLENECK ---\n"
                    " parse_fail={parse_failures} cause=ASN1_SCHEMA_MISMATCH\n"
                    " rating_engine_lag={cdr_lag_min}min revenue_at_risk=${revenue_risk}\n"
                    " sftp_status=OK dedup=ENABLED\n"
                    "ACTION: pause_ingest=false priority_drain=true alert=BILL-CDR-BACKLOG"
                ),
            },
            4: {
                "name": "OCS Credit Control Failure",
                "subsystem": "charging",
                "vehicle_section": "online_charging",
                "error_type": "BILL-OCS-FAIL",
                "sensor_type": "ocs_latency",
                "affected_services": ["billing-engine", "mobile-core"],
                "cascade_services": ["sms-gateway", "voice-platform"],
                "description": "Online Charging System (OCS) Diameter Gy failures blocking prepaid subscriber data sessions",
                "investigation_notes": (
                    "1. Check OCS Diameter peer status — TRANSPORT_FAILURE on Gy interface means "
                    "the PCEF (Policy and Charging Enforcement Function) cannot authorize data sessions "
                    "for prepaid subscribers. Default action is deny, causing immediate service impact.\n"
                    "2. Review CCR-I (Credit Control Request Initial) success rate — rates <99.5% "
                    "indicate OCS is rejecting initial session authorizations. Check for DB connection "
                    "pool exhaustion on the OCS subscriber balance store.\n"
                    "3. Inspect quota reservation size — if the granted unit quota (MB) is too small, "
                    "CCR-U storms (mid-session updates) will overload the OCS. Recommended: 50-100MB grants.\n"
                    "4. Verify fallback-on-failure policy — if PCEF is configured to DENY on OCS failure, "
                    "ALL prepaid data is blocked. Check: pcef-cli show charging-policy. Consider "
                    "temporary whitelist for critical data types (emergency, medical).\n"
                    "5. Check OCS DB replication lag — primary/replica sync delays >2s cause quota "
                    "double-grants leading to revenue leakage. Monitor: SHOW SLAVE STATUS\\G"
                ),
                "remediation_action": "failover_ocs_instance",
                "error_message": "[BILL] BILL-OCS-FAIL: ccr_type={ccr_type} imsi={imsi} result_code={diameter_result} ocs_host={ocs_host} latency_ms={ocs_latency_ms}",
                "stack_trace": (
                    "=== OCS DIAMETER Gy FAILURE ===\n"
                    "peer=pcef-01.claro imsi={imsi} session={session_id}\n"
                    "--- DIAMETER MESSAGE ---\n"
                    " CCR-{ccr_type} → OCS host={ocs_host}\n"
                    " Service-Identifier: 1 (DATA)\n"
                    " Requested-Service-Unit: 102400 octets\n"
                    " ← CCA result_code={diameter_result} latency_ms={ocs_latency_ms}\n"
                    "--- IMPACT ---\n"
                    " subscriber_type=PREPAID session_blocked=true\n"
                    " affected_subscribers={affected_subs} revenue_at_risk=${ocs_revenue}\n"
                    " fallback_policy=DENY quota_granted=0\n"
                    "ocs_db_replication_lag_ms=2840 pool_exhausted=true\n"
                    "ACTION: failover_ocs=true notify_pcef=true alert=BILL-OCS-FAIL"
                ),
            },
            5: {
                "name": "Real-Time Charging Fraud Spike",
                "subsystem": "charging",
                "vehicle_section": "fraud_guard",
                "error_type": "BILL-FRAUD-SPIKE",
                "sensor_type": "fraud_score",
                "affected_services": ["billing-engine", "sms-gateway"],
                "cascade_services": ["mobile-core", "customer-portal"],
                "description": "Real-time charging system detecting abnormal usage pattern indicating SIM swap or toll fraud",
                "investigation_notes": (
                    "1. Check IMSI/MSISDN correlation — SIM swap fraud shows the same MSISDN "
                    "appearing simultaneously on two IMSIs in different locations. "
                    "Query: SELECT msisdn, COUNT(DISTINCT imsi) FROM active_sessions GROUP BY msisdn HAVING COUNT > 1.\n"
                    "2. Review velocity rules triggering — >500 SMS in 60 seconds from a single MSISDN "
                    "is the primary indicator for premium rate SMS fraud. Check the SMSC throttle queue.\n"
                    "3. Inspect international call patterns — sudden IPRN (International Premium Rate Number) "
                    "traffic to 232/234/236 country codes from previously domestic-only subscribers "
                    "indicates call-forwarding fraud. Enable emergency IPRN block if confirmed.\n"
                    "4. Verify the ML fraud model freshness — if the model last updated >24h ago, "
                    "false negative rates increase. Check: fraud-engine status --model-age\n"
                    "5. Cross-reference with recent SIM swap requests in the HLR — fraudulent SIM swaps "
                    "often occur 2-6 hours before the fraud spike. Check CRM for social-engineering "
                    "events: SELECT * FROM sim_swap_requests WHERE ts > NOW() - INTERVAL 6 HOUR."
                ),
                "remediation_action": "block_fraud_msisdn",
                "error_message": "[BILL] BILL-FRAUD-SPIKE: msisdn={msisdn} fraud_type={fraud_type} score={fraud_score}/100 velocity={sms_velocity}/min revenue_at_risk=${fraud_revenue}",
                "stack_trace": (
                    "=== REAL-TIME FRAUD ALERT ===\n"
                    "msisdn={msisdn} detected_at={timestamp}\n"
                    "--- FRAUD INDICATORS ---\n"
                    " RULE                   STATUS   DETAIL\n"
                    " velocity_sms           TRIGGER  {sms_velocity}/min (max: 50)\n"
                    " dual_imsi_active        TRIGGER  2 IMSIs same MSISDN\n"
                    " iprn_destination       TRIGGER  country=232 (Sierra Leone)\n"
                    " location_impossible    TRIGGER  BR→MX 8min impossible travel\n"
                    " model_score            {fraud_score}/100  threshold: 70\n"
                    "--- IMPACT ---\n"
                    " fraud_type={fraud_type}\n"
                    " revenue_at_risk=${fraud_revenue} exposure_window_min=12\n"
                    " subscribers_impacted=1 sim_swap_flagged=true\n"
                    "ACTION: block_msisdn=true notify_security=true alert=BILL-FRAUD-SPIKE"
                ),
            },
            6: {
                "name": "SMSC Queue Overflow",
                "subsystem": "messaging",
                "vehicle_section": "smsc",
                "error_type": "SMS-SMSC-OVERFLOW",
                "sensor_type": "smsc_queue",
                "affected_services": ["sms-gateway", "billing-engine"],
                "cascade_services": ["customer-portal", "mobile-core"],
                "description": "Short Message Service Center queue overflow causing SMS delivery delays and drops",
                "investigation_notes": (
                    "1. Check SMSC queue fill level — >90% utilization triggers message drops per "
                    "3GPP TS 23.040. Priority classes: Class 0 (immediate display), Class 1 (ME storage), "
                    "Class 2 (SIM storage). Drop Class 1/2 before Class 0.\n"
                    "2. Review upstream A2P (Application-to-Person) traffic — marketing broadcast "
                    "campaigns often cause sudden queue spikes. Check the A2P gateway throttle settings "
                    "and verify campaign approval was obtained from the NOC.\n"
                    "3. Inspect HLR query rate — SMSC must query HLR for each MO-MT delivery to get "
                    "the subscriber's current MSC/SGSN address. HLR timeout causes SMSC retry storms.\n"
                    "4. Check SS7 MAP signaling — MT-ForwardSM failures with cause=AbsentSubscriber "
                    "are normal but spikes indicate mass network event (power outage, tower failure).\n"
                    "5. Verify flash SMS throttling — Class 0 flash SMS have no storage and must be "
                    "delivered immediately. A flood of Class 0 messages bypasses queue and can OOM the SMSC."
                ),
                "remediation_action": "throttle_a2p_gateway",
                "error_message": "[SMS] SMS-SMSC-OVERFLOW: queue_depth={smsc_queue} drop_rate={sms_drop_rate}% a2p_rate={a2p_rate}/s hlr_timeout={hlr_timeout_ms}ms",
                "stack_trace": (
                    "=== SMSC QUEUE STATUS ===\n"
                    "smsc_host=claro-smsc-01 period=last_5min\n"
                    "--- QUEUE METRICS ---\n"
                    " CLASS   QUEUED   CAPACITY  FILL%  STATUS\n"
                    " CLASS-0 4,200    10,000    42%    OK\n"
                    " CLASS-1 {smsc_queue}   100,000   92%    OVERFLOW\n"
                    " CLASS-2 18,400   20,000    92%    OVERFLOW\n"
                    "--- TRAFFIC BREAKDOWN ---\n"
                    " MO_P2P    28,400/min  NORMAL\n"
                    " MT_P2P    31,200/min  NORMAL\n"
                    " A2P_PUSH  {a2p_rate}/s  THROTTLE <<< SPIKE\n"
                    "hlr_timeout_ms={hlr_timeout_ms} drop_rate={sms_drop_rate}%\n"
                    "ACTION: throttle_a2p=true priority_flush=true alert=SMS-SMSC-OVERFLOW"
                ),
            },
            7: {
                "name": "SMPP Bind Failure",
                "subsystem": "messaging",
                "vehicle_section": "smpp_server",
                "error_type": "SMS-SMPP-BIND-FAIL",
                "sensor_type": "smpp_connections",
                "affected_services": ["sms-gateway", "customer-portal"],
                "cascade_services": ["billing-engine", "mobile-core"],
                "description": "SMPP (Short Message Peer-to-Peer) bind failures rejecting enterprise and A2P messaging clients",
                "investigation_notes": (
                    "1. Check SMPP server connection limit — max_bind=500 reached means no new "
                    "ESME (External Short Message Entity) connections can be established. "
                    "Review idle connections: SELECT * FROM smpp_sessions WHERE last_activity < NOW() - INTERVAL 5 MIN.\n"
                    "2. Review system_id authentication — bind_fail_reason=INVALID_PASSWORD often "
                    "indicates a credential rotation that wasn't propagated to the ESME clients. "
                    "Check recent provisioning changes in the SMPP account manager.\n"
                    "3. Inspect TPS (Transactions Per Second) throttle — THROTTLING (0x00000058) errors "
                    "mean the ESME exceeded its contracted TPS limit. Review the ESME's SLA agreement.\n"
                    "4. Check for TCP port exhaustion on the SMPP server — high connection churn from "
                    "misbehaving clients can exhaust ephemeral port range. "
                    "Check: ss -s | grep TIME-WAIT; consider SO_REUSEADDR tuning.\n"
                    "5. Verify SMPP enquire_link heartbeat — sessions with no enquire_link for >60s "
                    "are zombie connections consuming slots. Enable server-side idle detection."
                ),
                "remediation_action": "purge_idle_smpp_sessions",
                "error_message": "[SMS] SMS-SMPP-BIND-FAIL: system_id={smpp_system_id} bind_type={smpp_bind_type} error={smpp_error} connections_active={smpp_active} max={smpp_max}",
                "stack_trace": (
                    "=== SMPP SERVER BIND FAILURE ===\n"
                    "server=claro-smpp-01:2775 system_id={smpp_system_id}\n"
                    "--- BIND ATTEMPT ---\n"
                    " bind_type={smpp_bind_type}\n"
                    " system_id={smpp_system_id} password=*** interface_version=3.4\n"
                    " ← bind_resp error={smpp_error} (0x{smpp_error_hex})\n"
                    "--- SERVER STATUS ---\n"
                    " active_sessions={smpp_active} max_sessions={smpp_max}\n"
                    " idle_sessions=234  zombie_sessions=48\n"
                    " auth_failures_1h=1,284  throttle_events_1h=892\n"
                    "tcp_time_wait=48,200 ephemeral_ports_used=92%\n"
                    "ACTION: purge_idle=true notify_esme=true alert=SMS-SMPP-BIND-FAIL"
                ),
            },
            8: {
                "name": "Customer Portal Auth Cascade",
                "subsystem": "digital_services",
                "vehicle_section": "auth_service",
                "error_type": "PORTAL-AUTH-CASCADE",
                "sensor_type": "auth_failure_rate",
                "affected_services": ["customer-portal", "billing-engine"],
                "cascade_services": ["mobile-core", "noc-dashboard"],
                "description": "Self-service portal authentication cascade failure blocking subscribers from account management",
                "investigation_notes": (
                    "1. Check the OAuth2/OIDC token endpoint health — if the Identity Provider (IdP) "
                    "is returning 503, all portal sessions requiring token refresh will fail simultaneously "
                    "causing a cascade of 401 errors across the portal.\n"
                    "2. Review session store (Redis) health — portal sessions stored in Redis will be "
                    "invalidated if the Redis cluster experiences a failover. Check Redis Sentinel logs: "
                    "redis-cli -h sentinel-01 sentinel masters\n"
                    "3. Inspect SSO (Single Sign-On) federation — if Claro's SAML IdP certificate "
                    "expires or the metadata endpoint is unreachable, SSO-authenticated users cannot "
                    "log in. Check: openssl s_client -connect sso.claro.com.br:443 | grep 'notAfter'\n"
                    "4. Check rate limiting on the auth endpoint — DDoS or credential stuffing attacks "
                    "can exhaust the auth service capacity causing legitimate user lockouts. "
                    "Review WAF logs for IP concentration patterns.\n"
                    "5. Verify backend API gateway circuit breaker state — if auth-service is in "
                    "OPEN state on the API gateway, all auth requests fail fast without reaching the IdP."
                ),
                "remediation_action": "restart_auth_service",
                "error_message": "[PORTAL] PORTAL-AUTH-CASCADE: failure_rate={auth_fail_rate}% idp_status={idp_status} affected_users={affected_users} redis_state={redis_state}",
                "stack_trace": (
                    "=== CUSTOMER PORTAL AUTH FAILURE ===\n"
                    "portal=mi.claro.com.br period=last_5min\n"
                    "--- AUTH METRICS ---\n"
                    " METRIC              VALUE    THRESHOLD STATUS\n"
                    " login_attempts      42,840   ---       ---\n"
                    " auth_success        {auth_success}      ---       ---\n"
                    " auth_fail           {auth_fail}      >100      CRITICAL\n"
                    " failure_rate        {auth_fail_rate}%    >5%       ALERT\n"
                    "--- DEPENDENCIES ---\n"
                    " IdP (Okta)          {idp_status}  timeout_ms=8420\n"
                    " Redis Sessions      {redis_state}  evictions=12,400\n"
                    " SSO Federation      DEGRADED cert_days_remaining=0\n"
                    "affected_users={affected_users} self_care_blocked=true\n"
                    "ACTION: failover_idp=true invalidate_sessions=false alert=PORTAL-AUTH-CASCADE"
                ),
            },
            9: {
                "name": "Self-Care API Rate Limit",
                "subsystem": "digital_services",
                "vehicle_section": "api_gateway",
                "error_type": "PORTAL-API-RATELIMIT",
                "sensor_type": "api_throttle",
                "affected_services": ["customer-portal", "network-analytics"],
                "cascade_services": ["billing-engine", "sms-gateway"],
                "description": "Customer self-care API rate limits exceeded blocking plan changes, recharges, and support tickets",
                "investigation_notes": (
                    "1. Identify the top-consuming API clients — use API gateway access logs to find "
                    "which client_id or IP is consuming the quota. Often a poorly implemented mobile "
                    "app retry loop is the cause.\n"
                    "2. Review the rate limit policy tiers — B2C mobile app: 1000 req/min; "
                    "B2B integrators: 5000 req/min; internal: unlimited. Verify the offending "
                    "client is in the correct tier.\n"
                    "3. Check for bulk account management operations — CRM migrations or marketing "
                    "campaign triggers can cause burst API traffic. Coordinate with the CRM team "
                    "for off-peak scheduling.\n"
                    "4. Inspect the /recharge endpoint specifically — automated top-up scripts that "
                    "poll balance frequently cause disproportionate load on the OCS query path.\n"
                    "5. Consider implementing adaptive throttling — if the backend is healthy, "
                    "temporarily increase limits by 50% and alert the API client team."
                ),
                "remediation_action": "adjust_rate_limits",
                "error_message": "[PORTAL] PORTAL-API-RATELIMIT: client_id={api_client} endpoint={api_endpoint} rate={api_rate}/min limit={api_limit}/min throttled={throttled_reqs}",
                "stack_trace": (
                    "=== API GATEWAY RATE LIMIT EXCEEDED ===\n"
                    "gateway=api.claro.com.br client_id={api_client}\n"
                    "--- RATE ANALYSIS ---\n"
                    " endpoint={api_endpoint}\n"
                    " current_rate={api_rate}/min limit={api_limit}/min\n"
                    " throttled_requests={throttled_reqs} window=60s\n"
                    "--- TOP ENDPOINTS (last 5min) ---\n"
                    " /v1/account/balance    284,200 req  42% of quota\n"
                    " /v1/recharge          {throttled_reqs}   THROTTLED\n"
                    " /v1/plan/change         12,400 req   OK\n"
                    " /v1/support/ticket       8,200 req   OK\n"
                    "retry_storm=true client_tier=B2C\n"
                    "ACTION: throttle_client=true notify_client=true alert=PORTAL-API-RATELIMIT"
                ),
            },
            10: {
                "name": "CDN Cache Purge Storm",
                "subsystem": "cdn",
                "vehicle_section": "cache_manager",
                "error_type": "CDN-PURGE-STORM",
                "sensor_type": "cache_hit_rate",
                "affected_services": ["content-delivery", "customer-portal"],
                "cascade_services": ["network-analytics", "noc-dashboard"],
                "description": "Mass CDN cache invalidation causing origin server overload and video streaming degradation",
                "investigation_notes": (
                    "1. Identify the purge source — programmatic cache purges from the CMS or "
                    "deployment pipeline often trigger mass invalidations. Check API audit logs: "
                    "GET /api/v1/purge/history?limit=100\n"
                    "2. Review cache-hit ratio drop — from 89% to 12% indicates almost all requests "
                    "are going to origin. Calculate origin server capacity headroom before escalating.\n"
                    "3. Inspect the purge scope — a wildcard purge ('/*') will invalidate all cached "
                    "content. Prefer pattern-specific purges ('/video/live/*') to minimize blast radius.\n"
                    "4. Check origin shield (mid-tier cache) — if the shield is also invalidated, "
                    "origin load multiplies by edge PoP count (48 PoPs in LATAM). Enable shield "
                    "protection: cdn-cli shield protect --all-pops\n"
                    "5. Verify video manifest (.m3u8) and segment (.ts) TTLs — if TTL=0 is set on "
                    "video content due to a misconfigured cache rule, live stream segments will never "
                    "cache and always hit origin."
                ),
                "remediation_action": "restore_cache_rules",
                "error_message": "[CDN] CDN-PURGE-STORM: cache_hit={cache_hit_rate}% origin_rps={origin_rps} purge_count={purge_count} pop={cdn_pop} video_rebuffer={rebuffer_rate}%",
                "stack_trace": (
                    "=== CDN CACHE INVALIDATION STORM ===\n"
                    "pop={cdn_pop} period=last_10min\n"
                    "--- CACHE METRICS ---\n"
                    " METRIC           BEFORE  NOW     STATUS\n"
                    " cache_hit_rate   89%     {cache_hit_rate}%   CRITICAL\n"
                    " origin_rps       1,200   {origin_rps}  OVERLOAD\n"
                    " ttfb_ms          42      840     DEGRADED\n"
                    " video_rebuffer   0.2%    {rebuffer_rate}%  ALERT\n"
                    "--- PURGE AUDIT ---\n"
                    " purge_count={purge_count} scope=WILDCARD scope_pattern=/*\n"
                    " triggered_by=cms-deploy-bot source=CI/CD pipeline\n"
                    " shield_invalidated=true edge_pops_affected=48\n"
                    "ACTION: restore_shield=true partial_repopulate=true alert=CDN-PURGE-STORM"
                ),
            },
            11: {
                "name": "Video Transcoding Pipeline Stall",
                "subsystem": "cdn",
                "vehicle_section": "transcode_farm",
                "error_type": "CDN-TRANSCODE-STALL",
                "sensor_type": "transcode_queue",
                "affected_services": ["content-delivery", "network-analytics"],
                "cascade_services": ["customer-portal", "noc-dashboard"],
                "description": "Video transcoding pipeline stall causing live event and VOD encoding backlog",
                "investigation_notes": (
                    "1. Check GPU worker availability — if all GPU transcoding workers are BUSY, "
                    "live events are delayed and VOD encoding queues build up. Check: "
                    "kubectl get pods -l app=transcoder -n cdn | grep -v Running\n"
                    "2. Review live event priority queue — live events (Claro Sports, Claro TV) "
                    "must preempt VOD encoding. Verify the priority scheduler is functioning: "
                    "transcode-cli queue list --type=LIVE --status=WAITING\n"
                    "3. Inspect encoding profile failures — H.265/HEVC encoding failures often "
                    "indicate a GPU driver version mismatch with the NVENC library. Check nvidia-smi.\n"
                    "4. Check input manifest integrity — corrupted or malformed HLS input from "
                    "the ingest server (tsErrors in the stream) will cause the transcoder to "
                    "abort and requeue, causing the worker to be perpetually busy.\n"
                    "5. Verify DRM (Widevine/PlayReady) signing service — if the DRM key server "
                    "is unreachable, transcoded segments cannot be encrypted and are held in queue."
                ),
                "remediation_action": "scale_transcode_workers",
                "error_message": "[CDN] CDN-TRANSCODE-STALL: queue_depth={transcode_queue} live_delayed={live_events_delayed} vod_backlog={vod_backlog_hours}h gpu_util={gpu_util}%",
                "stack_trace": (
                    "=== VIDEO TRANSCODE PIPELINE STATUS ===\n"
                    "farm=claro-transcode-gcp-01 period=last_15min\n"
                    "--- WORKER STATUS ---\n"
                    " WORKER        STATUS  CURRENT_JOB            GPU\n"
                    " gpu-worker-01 BUSY    live-clarosports-4k     92%\n"
                    " gpu-worker-02 BUSY    live-clarotv-hd         88%\n"
                    " gpu-worker-03 FAILED  vod-{vod_job_id}        ---\n"
                    " gpu-worker-04 BUSY    vod-batch-{vod_batch}   {gpu_util}%\n"
                    "--- QUEUE METRICS ---\n"
                    " live_events_queued={live_events_delayed}  vod_jobs_queued={transcode_queue}\n"
                    " avg_encode_fps=24 target_fps=60 deficit={transcode_queue}fps\n"
                    " drm_signing=DEGRADED latency_ms=4200 threshold_ms=500\n"
                    "ACTION: priority_live=true scale_workers=true alert=CDN-TRANSCODE-STALL"
                ),
            },
            12: {
                "name": "Network Analytics Pipeline Lag",
                "subsystem": "analytics",
                "vehicle_section": "stream_processor",
                "error_type": "ANALYTICS-PIPELINE-LAG",
                "sensor_type": "pipeline_lag",
                "affected_services": ["network-analytics", "noc-dashboard"],
                "cascade_services": ["content-delivery", "mobile-core"],
                "description": "Real-time network analytics stream processing lag causing stale NOC dashboards and missed SLA alerts",
                "investigation_notes": (
                    "1. Check Kafka consumer group lag — consumer group 'noc-analytics' lag >100K "
                    "events means the processing pipeline is falling behind the ingest rate. "
                    "Run: kafka-consumer-groups.sh --describe --group noc-analytics\n"
                    "2. Review Flink job health — failed Flink operators cause checkpointing delays "
                    "and processing restarts. Check Flink dashboard for operator backpressure: "
                    "http://flink-master:8081/#/overview\n"
                    "3. Inspect IPFIX/NetFlow collector performance — if the flow collector is "
                    "dropping packets, analytics data gaps cause false SLA breach alerts. "
                    "Check: netflow-collector stats --missed\n"
                    "4. Verify Elasticsearch ingest pipeline — the analytics results are written to "
                    "Elastic. If the ingest queue is saturated, writes are rejected. "
                    "Check: GET /_nodes/stats/ingest\n"
                    "5. Check cluster auto-scaling — if the analytics cluster is at max scale and "
                    "traffic is growing (e.g., post-game spike, new event), lag will increase "
                    "until manual capacity addition."
                ),
                "remediation_action": "rebalance_kafka_partitions",
                "error_message": "[ANALYTICS] ANALYTICS-PIPELINE-LAG: consumer_lag={kafka_lag} flink_backpressure={flink_bp}% processing_delay_min={processing_delay} dashboard_stale=true",
                "stack_trace": (
                    "=== ANALYTICS PIPELINE STATUS ===\n"
                    "cluster=claro-analytics-gcp period=last_5min\n"
                    "--- KAFKA CONSUMER LAG ---\n"
                    " GROUP=noc-analytics\n"
                    " TOPIC                    LAG      STATUS\n"
                    " netflow.ipfix.raw        {kafka_lag}  CRITICAL\n"
                    " mobile.kpi.5min          84,200   WARNING\n"
                    " cdn.access.realtime      12,400   OK\n"
                    "--- FLINK STATUS ---\n"
                    " backpressure={flink_bp}%  checkpoints=FAILING interval=30s\n"
                    " operator=AggregateKPIs  status=SLOW\n"
                    " restart_count=4  last_restart=08min_ago\n"
                    "processing_delay_min={processing_delay} noc_dashboards_stale=true\n"
                    "ACTION: increase_parallelism=true restart_operators=true alert=ANALYTICS-PIPELINE-LAG"
                ),
            },
            13: {
                "name": "DPI Traffic Classification Failure",
                "subsystem": "analytics",
                "vehicle_section": "dpi_engine",
                "error_type": "ANALYTICS-DPI-FAIL",
                "sensor_type": "dpi_classification",
                "affected_services": ["network-analytics", "billing-engine"],
                "cascade_services": ["mobile-core", "content-delivery"],
                "description": "Deep Packet Inspection classification failures causing incorrect traffic shaping and OCS quota accounting",
                "investigation_notes": (
                    "1. Check DPI signature database version — an outdated signature database "
                    "(>7 days old) will misclassify encrypted traffic (QUIC, TLS 1.3) and may "
                    "incorrectly rate new applications. Update: dpi-cli signatures update\n"
                    "2. Review classification confidence threshold — if threshold is set >95%, "
                    "many flows default to 'UNKNOWN' and receive default QoS treatment. "
                    "Lower to 80% for encrypted traffic classes.\n"
                    "3. Inspect QUIC/HTTP3 handling — QUIC traffic on UDP/443 is commonly "
                    "misclassified as generic UDP. Enable QUIC-aware classification: "
                    "dpi-cli config set quic-aware=true\n"
                    "4. Verify policy enforcement on misclassified traffic — OCS incorrectly "
                    "charging video traffic as 'data' (not streaming quota) causes subscriber "
                    "complaints. Check OCS traffic-type mapping table.\n"
                    "5. Check DPI processing throughput — at >40Gbps per node, DPI engines "
                    "may enter sampled mode and miss flows. Review: dpi-cli stats --node all"
                ),
                "remediation_action": "update_dpi_signatures",
                "error_message": "[ANALYTICS] ANALYTICS-DPI-FAIL: unclassified_rate={unclassified_pct}% throughput_gbps={dpi_throughput} sig_age_days={sig_age} quic_misclass={quic_misclass}%",
                "stack_trace": (
                    "=== DPI CLASSIFICATION STATUS ===\n"
                    "dpi_cluster=claro-dpi-gcp-01 period=last_10min\n"
                    "--- CLASSIFICATION METRICS ---\n"
                    " CATEGORY        FLOWS    CLASSIFIED  CONFIDENCE\n"
                    " VIDEO_STREAM    284,200  41%         LOW\n"
                    " SOCIAL_MEDIA    142,100  78%         MEDIUM\n"
                    " VOIP            28,400   91%         HIGH\n"
                    " QUIC_HTTP3      {quic_misclass}%    UNKNOWN     N/A\n"
                    " UNKNOWN         {unclassified_pct}%  ---         ---\n"
                    "--- ENGINE HEALTH ---\n"
                    " throughput={dpi_throughput}Gbps  mode=SAMPLED (>40Gbps)\n"
                    " sig_db_version=2024.01.15 age_days={sig_age} status=STALE\n"
                    " encrypted_traffic=72% quic_flows=38%\n"
                    "ACTION: update_signatures=true enable_quic_mode=true alert=ANALYTICS-DPI-FAIL"
                ),
            },
            14: {
                "name": "SIP Trunk Saturation",
                "subsystem": "voice",
                "vehicle_section": "sip_proxy",
                "error_type": "VOICE-SIP-SATURATION",
                "sensor_type": "sip_capacity",
                "affected_services": ["voice-platform", "mobile-core"],
                "cascade_services": ["customer-portal", "noc-dashboard"],
                "description": "SIP trunk capacity saturation causing voice call setup failures and busy-tone returns",
                "investigation_notes": (
                    "1. Check SIP trunk channel utilization — >95% utilization means new calls receive "
                    "SIP 503 (Service Unavailable). Peak events (New Year, emergencies) can cause "
                    "instantaneous saturation. Review current call concurrency vs. trunk capacity.\n"
                    "2. Review INVITE failure distribution — SIP 486 (BUSY) vs 503 (Service Unavailable) "
                    "indicates different problems: 486 is termination-side busy; 503 is your trunk capacity.\n"
                    "3. Inspect SS7 ISUP interface if PSTN trunks are involved — CIC (Circuit Identification "
                    "Code) exhaustion on E1/T1 trunk groups causes ISUP REL with cause=34 (no circuit available).\n"
                    "4. Check media gateway (RTP) port allocation — even if SIP signaling succeeds, "
                    "RTP media might fail if the MSBC/media gateway runs out of RTP ports.\n"
                    "5. Consider emergency trunk expansion — contact the interconnect carrier to temporarily "
                    "increase trunk capacity or activate overflow routing to backup SIP provider."
                ),
                "remediation_action": "activate_overflow_trunk",
                "error_message": "[VOICE] VOICE-SIP-SATURATION: trunk_util={trunk_util}% active_calls={active_calls} max_calls={max_calls} sip_503_rate={sip_503}/min cic_exhausted={cic_exhausted}",
                "stack_trace": (
                    "=== SIP TRUNK SATURATION ALERT ===\n"
                    "proxy=claro-sbc-azure-01 period=last_5min\n"
                    "--- TRUNK METRICS ---\n"
                    " TRUNK         CAPACITY  ACTIVE  UTIL   STATUS\n"
                    " PSTN-GRP-01   2,400     {active_calls}   {trunk_util}%  SATURATED\n"
                    " SIP-CARRIER-A 1,200     1,180   98%    SATURATED\n"
                    " SIP-CARRIER-B 800       420     52%    OK\n"
                    " OVERFLOW      0         0       ---    INACTIVE\n"
                    "--- CALL STATS ---\n"
                    " sip_invite_recv=8,400/min\n"
                    " sip_503=      {sip_503}/min  <<< CAPACITY EXCEEDED\n"
                    " sip_486=         240/min\n"
                    " rtp_sessions={active_calls}  rtp_port_avail=12%\n"
                    "cic_exhausted={cic_exhausted} cause=34 (no_circuit_available)\n"
                    "ACTION: activate_overflow=true notify_carrier=true alert=VOICE-SIP-SATURATION"
                ),
            },
            15: {
                "name": "IMS Registration Storm",
                "subsystem": "voice",
                "vehicle_section": "ims_core",
                "error_type": "VOICE-IMS-STORM",
                "sensor_type": "ims_registrations",
                "affected_services": ["voice-platform", "billing-engine"],
                "cascade_services": ["mobile-core", "sms-gateway"],
                "description": "IMS (IP Multimedia Subsystem) mass re-registration storm after network event causing P-CSCF overload",
                "investigation_notes": (
                    "1. Identify the triggering network event — IMS storms commonly follow: "
                    "power restoration after outage, S-CSCF restart, P-CSCF failover, or "
                    "mass LTE reattach after RAN issue. Check event timeline correlation.\n"
                    "2. Review P-CSCF registration capacity — the Proxy-CSCF is the IMS entry point. "
                    "P-CSCF under storm conditions will return 500 (Server Internal Error) or "
                    "503 with Retry-After to spread re-registrations. Verify Retry-After is being honored.\n"
                    "3. Check registration expiry distribution — if all subscribers have the same "
                    "registration expiry (3600s default), they all re-register simultaneously. "
                    "Implement jitter: random expiry between 3400-4200s.\n"
                    "4. Inspect HSS (Home Subscriber Server) Diameter Cx interface — Cx queries "
                    "from I-CSCF to HSS must complete in <200ms. HSS overload causes REGISTER "
                    "chain delays and amplifies the storm.\n"
                    "5. Enable IMS admission control — temporarily limit REGISTER rate to "
                    "5000/s on P-CSCF to prevent HSS overload. Normal rate: ~2000/s."
                ),
                "remediation_action": "enable_ims_admission_control",
                "error_message": "[VOICE] VOICE-IMS-STORM: reg_rate={ims_reg_rate}/s p_cscf_load={pcscf_load}% hss_cx_latency_ms={hss_latency_ms} reg_queue={ims_queue}",
                "stack_trace": (
                    "=== IMS REGISTRATION STORM ===\n"
                    "p_cscf=claro-pcscf-azure-01 period=last_5min\n"
                    "--- REGISTRATION METRICS ---\n"
                    " METRIC               VALUE    NORMAL   STATUS\n"
                    " register_rate        {ims_reg_rate}/s  2,000/s  STORM\n"
                    " p_cscf_cpu           {pcscf_load}%  <60%     OVERLOAD\n"
                    " hss_cx_latency_ms    {hss_latency_ms}  <200ms   CRITICAL\n"
                    " register_queue       {ims_queue}   <100     STORM\n"
                    "--- FAILURE BREAKDOWN ---\n"
                    " 200_OK              2,840/min\n"
                    " 500_SERVER_ERROR    {ims_reg_rate}/min  <<< SPIKE\n"
                    " 503_RETRY_AFTER        480/min\n"
                    "trigger_event=S_CSCF_RESTART affected_subscribers=2.4M\n"
                    "ACTION: enable_admission=true rate_limit=5000 alert=VOICE-IMS-STORM"
                ),
            },
            16: {
                "name": "IoT MQTT Broker Overload",
                "subsystem": "iot",
                "vehicle_section": "mqtt_broker",
                "error_type": "IOT-MQTT-OVERLOAD",
                "sensor_type": "mqtt_connections",
                "affected_services": ["iot-connect", "network-analytics"],
                "cascade_services": ["billing-engine", "noc-dashboard"],
                "description": "MQTT broker overload from IoT device connection storm causing message delivery failures",
                "investigation_notes": (
                    "1. Check MQTT broker connection count — broker at max_connections=500K means "
                    "new device connections are rejected with CONNACK rc=2 (Identifier Rejected). "
                    "Check: mosquitto_sub -t '$SYS/broker/clients/connected' -C 1\n"
                    "2. Review device reconnect storm — IoT devices using exponential backoff with "
                    "jitter should prevent storms. Devices with constant retry interval cause "
                    "synchronized reconnection waves. Check keep-alive settings in device firmware.\n"
                    "3. Inspect QoS 1/2 message queue size — undelivered QoS 1/2 messages accumulate "
                    "in broker memory. At 8GB heap usage, the broker OOMs. "
                    "Check: mosquitto_sub -t '$SYS/broker/messages/stored' -C 1\n"
                    "4. Check per-topic subscription count — topics with >10K subscribers cause "
                    "message fan-out storms. Identify hot topics: "
                    "SELECT topic, COUNT(*) FROM subscriptions GROUP BY topic ORDER BY 2 DESC LIMIT 10\n"
                    "5. Verify IoT device certificate validity — mass certificate expiry causes "
                    "TLS handshake failures and reconnect storms if not rotated before expiry."
                ),
                "remediation_action": "scale_mqtt_broker",
                "error_message": "[IOT] IOT-MQTT-OVERLOAD: connections={mqtt_connections} max={mqtt_max} msg_queue_mb={msg_queue_mb} qos1_undelivered={qos1_undelivered} reconnect_rate={reconnect_rate}/s",
                "stack_trace": (
                    "=== MQTT BROKER STATUS ===\n"
                    "broker=claro-mqtt-azure-01 period=last_10min\n"
                    "--- CONNECTION METRICS ---\n"
                    " METRIC              VALUE      THRESHOLD STATUS\n"
                    " active_connections  {mqtt_connections}   500,000   CRITICAL\n"
                    " reconnect_rate      {reconnect_rate}/s  <100/s    STORM\n"
                    " new_connects/min    42,800     ---       ---\n"
                    " rejected_connects   {mqtt_connections}   >0        ALERT\n"
                    "--- QUEUE METRICS ---\n"
                    " msg_queue_mb={msg_queue_mb}  heap_used=91%\n"
                    " qos0_msgs=2.4M  qos1_undelivered={qos1_undelivered}  qos2_pending=0\n"
                    " hot_topics=['telemetry/+/status', 'cmd/+/set']\n"
                    "device_firmware_reconnect_interval=0s (no_backoff)\n"
                    "ACTION: scale_broker=true push_backoff_config=true alert=IOT-MQTT-OVERLOAD"
                ),
            },
            17: {
                "name": "IoT Device Certificate Expiry Wave",
                "subsystem": "iot",
                "vehicle_section": "device_registry",
                "error_type": "IOT-CERT-EXPIRY",
                "sensor_type": "cert_validity",
                "affected_services": ["iot-connect", "customer-portal"],
                "cascade_services": ["mobile-core", "billing-engine"],
                "description": "Mass IoT device certificate expiration causing fleet-wide TLS failures and service disconnection",
                "investigation_notes": (
                    "1. Identify the affected certificate cohort — certificates issued in the same "
                    "batch have the same expiry. Query: "
                    "SELECT serial_prefix, COUNT(*), MIN(expiry) FROM device_certs WHERE expiry < NOW() + INTERVAL 7 DAY GROUP BY 1\n"
                    "2. Check OCSP (Online Certificate Status Protocol) responder — if the OCSP "
                    "responder is unreachable, devices doing OCSP stapling will fail TLS even "
                    "with valid certs. Test: openssl ocsp -issuer ca.pem -cert device.pem -url http://ocsp.claro.iot\n"
                    "3. Review device OTA capability — can affected devices receive certificate "
                    "rotation via MQTT or HTTP OTA? Check device_registry for OTA-capable firmware versions.\n"
                    "4. Assess impact by device type — smart meters and industrial sensors may not "
                    "support automatic cert rotation and require field technician visits. "
                    "Priority: critical infrastructure (utilities, health) over consumer devices.\n"
                    "5. Issue emergency short-lived certificates — using the subordinate CA, issue "
                    "30-day certs via EST (Enrollment over Secure Transport) protocol to buy time "
                    "for full PKI rotation."
                ),
                "remediation_action": "rotate_device_certificates",
                "error_message": "[IOT] IOT-CERT-EXPIRY: expired_count={expired_devices} expiring_24h={expiring_soon} tls_failures={tls_failures}/min ocsp_status={ocsp_status} ota_capable={ota_pct}%",
                "stack_trace": (
                    "=== IOT CERTIFICATE EXPIRY ALERT ===\n"
                    "registry=claro-iot-registry period=last_6h\n"
                    "--- CERTIFICATE STATUS ---\n"
                    " STATUS          COUNT    PCT\n"
                    " VALID            4.2M    82%\n"
                    " EXPIRING_7D      {expiring_soon}   12%\n"
                    " EXPIRED          {expired_devices}   6% <<< FAILING TLS\n"
                    " REVOKED           12,400  <1%\n"
                    "--- FAILURE IMPACT ---\n"
                    " tls_handshake_fail={tls_failures}/min\n"
                    " ocsp_responder={ocsp_status} latency_ms=8420 <<< UNREACHABLE\n"
                    " disconnected_devices={expired_devices} reconnect_attempts=0\n"
                    "ota_capable_pct={ota_pct}% field_dispatch_required=true\n"
                    "ACTION: issue_emergency_certs=true dispatch_field=true alert=IOT-CERT-EXPIRY"
                ),
            },
            18: {
                "name": "NOC Alert Correlation Failure",
                "subsystem": "operations",
                "vehicle_section": "alert_manager",
                "error_type": "NOC-ALERT-STORM",
                "sensor_type": "alert_volume",
                "affected_services": ["noc-dashboard", "network-analytics"],
                "cascade_services": ["mobile-core", "billing-engine"],
                "description": "NOC alert storm from uncorrelated upstream events overwhelming operators and hiding root cause",
                "investigation_notes": (
                    "1. Enable alert correlation rules — a single root cause can generate thousands "
                    "of alerts from dependent systems. The correlation engine should suppress child "
                    "alerts when a parent root-cause alert is active.\n"
                    "2. Check alert deduplication window — if dedup_window=0s, every metric breach "
                    "generates a new alert ticket. Recommended: 300s dedup window for non-critical.\n"
                    "3. Review alert priority distribution — if 80% of alerts are P1, operators "
                    "experience 'alert fatigue' and miss genuine P1 events. Recalibrate thresholds.\n"
                    "4. Inspect the upstream event that caused the storm — use the timeline to find "
                    "the first alert. The root cause is typically 2-5 minutes before the storm peak.\n"
                    "5. Enable automatic NOC situation room — if alert volume >1000/min, trigger "
                    "automated incident bridge and page the on-call team lead."
                ),
                "remediation_action": "enable_alert_correlation",
                "error_message": "[NOC] NOC-ALERT-STORM: alert_rate={alert_rate}/min active_alerts={active_alerts} p1_count={p1_alerts} correlated={correlated_pct}% mtta_min={mtta_min}",
                "stack_trace": (
                    "=== NOC ALERT MANAGER STATUS ===\n"
                    "host=claro-alertmanager-azure period=last_10min\n"
                    "--- ALERT METRICS ---\n"
                    " METRIC               VALUE    NORMAL  STATUS\n"
                    " alert_rate           {alert_rate}/min  <50/min STORM\n"
                    " active_alerts        {active_alerts}   <200    CRITICAL\n"
                    " p1_alerts            {p1_alerts}  <10     OVERLOAD\n"
                    " correlated_pct       {correlated_pct}%   >80%    POOR\n"
                    " mtta_min             {mtta_min}  <5min   BREACH\n"
                    "--- TOP ALERT SOURCES ---\n"
                    " mobile-core          420 alerts  34%\n"
                    " billing-engine       280 alerts  23%\n"
                    " sms-gateway          180 alerts  15%\n"
                    " voice-platform       140 alerts  11%\n"
                    " other               {active_alerts}  17%\n"
                    "dedup_window=0s correlation_rules=DISABLED\n"
                    "ACTION: enable_correlation=true page_team_lead=true alert=NOC-ALERT-STORM"
                ),
            },
            19: {
                "name": "BGP Route Flap",
                "subsystem": "operations",
                "vehicle_section": "core_routing",
                "error_type": "NOC-BGP-FLAP",
                "sensor_type": "bgp_stability",
                "affected_services": ["noc-dashboard", "mobile-core"],
                "cascade_services": ["content-delivery", "voice-platform"],
                "description": "BGP route instability causing intermittent network reachability and traffic black-holing",
                "investigation_notes": (
                    "1. Identify the flapping BGP peer — 'show bgp summary' on the core routers. "
                    "Peer with high 'Flaps' count and recent 'Up/Down' timestamp is the culprit. "
                    "Check physical interface errors: 'show interfaces Gi0/0/0 | include error'\n"
                    "2. Review BGP route count changes — sudden decrease in received prefixes "
                    "from a peer indicates the peer withdrew routes (network event on their side). "
                    "Check: 'show bgp neighbors X.X.X.X received-routes | count'\n"
                    "3. Inspect BFD (Bidirectional Forwarding Detection) status — BFD failure triggers "
                    "immediate BGP session teardown. BFD false positives from high CPU can cause "
                    "unnecessary flaps. Check BFD timers: 'show bfd sessions'\n"
                    "4. Check RPKI (Resource Public Key Infrastructure) validity — RPKI invalid "
                    "prefixes are dropped. A botched route origin authorization (ROA) update can "
                    "make your own prefixes RPKI-invalid.\n"
                    "5. Apply BGP dampening — if a peer flaps >3 times in 30 minutes, enable "
                    "route dampening to suppress unstable prefixes: 'bgp dampening 15 750 2000 60'"
                ),
                "remediation_action": "apply_bgp_dampening",
                "error_message": "[NOC] NOC-BGP-FLAP: peer_ip={bgp_peer} asn={peer_asn} flap_count={flap_count} prefixes_lost={prefixes_lost} traffic_impacted_gbps={traffic_gbps}",
                "stack_trace": (
                    "=== BGP ROUTE INSTABILITY ===\n"
                    "router=claro-core-azure-01 period=last_30min\n"
                    "--- BGP PEER STATUS ---\n"
                    " PEER           ASN     STATE      FLAPS  UP/DOWN\n"
                    " {bgp_peer}  {peer_asn}  {bgp_state}   {flap_count}    2min_ago\n"
                    " 198.51.100.2   64500   ESTABLISHED  0      18d\n"
                    " 203.0.113.10   64501   ESTABLISHED  0      42d\n"
                    "--- IMPACT ---\n"
                    " prefixes_withdrawn={prefixes_lost} routes_blackholed=12\n"
                    " traffic_impacted_gbps={traffic_gbps}\n"
                    " bfd_status=FAILED bfd_interval_ms=300\n"
                    " rpki_status=VALID dampening=DISABLED\n"
                    "ACTION: apply_dampening=true check_physical=true alert=NOC-BGP-FLAP"
                ),
            },
            20: {
                "name": "DNS Resolution Failure",
                "subsystem": "mobile_network",
                "vehicle_section": "dns_infrastructure",
                "error_type": "5G-DNS-FAIL",
                "sensor_type": "dns_resolution",
                "affected_services": ["mobile-core", "noc-dashboard"],
                "cascade_services": ["customer-portal", "content-delivery"],
                "description": "Mobile network DNS resolution failures blocking subscriber internet access and internal NF discovery",
                "investigation_notes": (
                    "1. Check DNS resolver cluster health — if the primary DNS cluster returns "
                    "SERVFAIL, devices fall back to secondary. If both fail, all internet-dependent "
                    "services fail. Check: dig @dns-primary.claro +time=2 google.com\n"
                    "2. Review NRF (Network Repository Function) DNS dependency — 5G NFs use DNS "
                    "for service discovery via NRF. DNS failure causes NF deregistration and SMF/AMF "
                    "cannot discover UPF instances. Check: nrf-cli list nf-instances\n"
                    "3. Inspect DNS cache hit rate — DNSSEC validation failures causing SERVFAIL "
                    "often stem from key rollover issues. Check: "
                    "dig +dnssec +cd claro.com.br — if CD (Checking Disabled) resolves but normal fails, DNSSEC misconfiguration.\n"
                    "4. Check for DNS amplification attack — sudden spike in DNS query rate from "
                    "spoofed source IPs (UDP port 53) can saturate DNS server NIC bandwidth. "
                    "Enable DNS response rate limiting (RRL): rndc rrl 50/s\n"
                    "5. Verify DHCP-assigned DNS propagation — if DHCP is distributing wrong DNS "
                    "IPs to mobile subscribers, all subscriber DNS will fail. "
                    "Check: grep 'domain-name-server' /etc/dhcp/dhcpd.conf"
                ),
                "remediation_action": "failover_dns_cluster",
                "error_message": "[5G] 5G-DNS-FAIL: resolver={dns_resolver} qtype={dns_qtype} rcode={dns_rcode} query_rate={dns_qps}/s cache_hit={dns_cache_hit}% nrf_affected={nrf_affected}",
                "stack_trace": (
                    "=== DNS RESOLUTION FAILURE ===\n"
                    "resolver={dns_resolver} period=last_5min\n"
                    "--- QUERY METRICS ---\n"
                    " METRIC          VALUE    NORMAL  STATUS\n"
                    " query_rate      {dns_qps}/s  <50K/s  SPIKE\n"
                    " cache_hit       {dns_cache_hit}%  >85%    CRITICAL\n"
                    " NOERROR         12%      >98%    CRITICAL\n"
                    " SERVFAIL        {dns_qps}/s  <1%     FAILURE\n"
                    " NXDOMAIN        2%       ---     NORMAL\n"
                    "--- NRF IMPACT ---\n"
                    " nrf_dns_query_fail=true nf_discovery=DOWN\n"
                    " smf_upf_resolution=FAILED amf_registered_gnbs=0\n"
                    " nrf_affected={nrf_affected} slice=FAILED\n"
                    "dnssec_validation=FAIL rrl_enabled=false amplification_detected=true\n"
                    "ACTION: enable_rrl=true failover_resolver=true alert=5G-DNS-FAIL"
                ),
            },
        }

    # ── Service Topology ──────────────────────────────────────────────

    @property
    def service_topology(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "mobile-core": [
                ("billing-engine", "/diameter/gy/ccr", "POST"),
                ("network-analytics", "/api/v1/kpi/push", "POST"),
                ("noc-dashboard", "/api/v1/alarm/push", "POST"),
            ],
            "billing-engine": [
                ("customer-portal", "/api/v1/balance/notify", "POST"),
                ("sms-gateway", "/api/v1/sms/send", "POST"),
            ],
            "sms-gateway": [
                ("customer-portal", "/api/v1/notification/delivery", "POST"),
            ],
            "customer-portal": [
                ("billing-engine", "/api/v1/account/balance", "GET"),
                ("content-delivery", "/api/v1/cdn/stream-token", "GET"),
            ],
            "content-delivery": [
                ("network-analytics", "/api/v1/cdn/metrics", "POST"),
            ],
            "network-analytics": [
                ("noc-dashboard", "/api/v1/dashboard/update", "POST"),
            ],
            "voice-platform": [
                ("billing-engine", "/diameter/rf/acr", "POST"),
                ("mobile-core", "/api/v1/ims/register", "POST"),
            ],
            "iot-connect": [
                ("billing-engine", "/api/v1/iot/usage", "POST"),
                ("network-analytics", "/api/v1/iot/telemetry", "POST"),
            ],
            "noc-dashboard": [
                ("network-analytics", "/api/v1/query/realtime", "GET"),
            ],
        }

    # ── Entry Endpoints ───────────────────────────────────────────────

    @property
    def entry_endpoints(self) -> dict[str, list[tuple[str, str]]]:
        return {
            "mobile-core": [
                ("/api/v1/pdu/session/create", "POST"),
                ("/api/v1/ue/register", "POST"),
                ("/api/v1/handover/x2", "POST"),
                ("/api/v1/dns/resolve", "GET"),
            ],
            "billing-engine": [
                ("/api/v1/cdr/ingest", "POST"),
                ("/api/v1/balance/query", "GET"),
                ("/api/v1/recharge", "POST"),
                ("/diameter/gy/ccr", "POST"),
            ],
            "sms-gateway": [
                ("/api/v1/sms/mo", "POST"),
                ("/api/v1/sms/mt", "POST"),
                ("/api/v1/smpp/bind", "POST"),
            ],
            "customer-portal": [
                ("/api/v1/account/login", "POST"),
                ("/api/v1/account/balance", "GET"),
                ("/api/v1/plan/change", "PUT"),
                ("/api/v1/recharge", "POST"),
                ("/api/v1/support/ticket", "POST"),
            ],
            "content-delivery": [
                ("/api/v1/stream/live", "GET"),
                ("/api/v1/vod/play", "GET"),
                ("/api/v1/cdn/purge", "POST"),
            ],
            "network-analytics": [
                ("/api/v1/kpi/query", "GET"),
                ("/api/v1/dpi/classify", "POST"),
                ("/api/v1/netflow/ingest", "POST"),
            ],
            "voice-platform": [
                ("/sip/invite", "INVITE"),
                ("/api/v1/ims/register", "POST"),
                ("/api/v1/conference/join", "POST"),
            ],
            "iot-connect": [
                ("/mqtt/connect", "CONNECT"),
                ("/api/v1/device/register", "POST"),
                ("/api/v1/cert/rotate", "POST"),
            ],
            "noc-dashboard": [
                ("/api/v1/alarm/active", "GET"),
                ("/api/v1/dashboard/realtime", "GET"),
                ("/api/v1/incident/create", "POST"),
            ],
        }

    # ── DB Operations ─────────────────────────────────────────────────

    @property
    def db_operations(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "mobile-core": [
                ("SELECT", "ue_contexts", "SELECT * FROM ue_contexts WHERE imsi=?"),
                ("INSERT", "pdu_sessions", "INSERT INTO pdu_sessions VALUES (?)"),
                ("UPDATE", "handover_log", "UPDATE handover_log SET status=? WHERE ho_id=?"),
            ],
            "billing-engine": [
                ("SELECT", "subscriber_balances", "SELECT balance FROM subscriber_balances WHERE msisdn=?"),
                ("INSERT", "cdr_records", "INSERT INTO cdr_records VALUES (?)"),
                ("UPDATE", "quota_grants", "UPDATE quota_grants SET granted_mb=? WHERE session_id=?"),
            ],
            "sms-gateway": [
                ("SELECT", "smpp_sessions", "SELECT * FROM smpp_sessions WHERE system_id=?"),
                ("INSERT", "message_log", "INSERT INTO message_log VALUES (?)"),
                ("UPDATE", "delivery_status", "UPDATE delivery_status SET status=? WHERE msg_id=?"),
            ],
            "customer-portal": [
                ("SELECT", "subscriber_accounts", "SELECT * FROM subscriber_accounts WHERE msisdn=?"),
                ("INSERT", "session_tokens", "INSERT INTO session_tokens VALUES (?)"),
                ("UPDATE", "plan_subscriptions", "UPDATE plan_subscriptions SET plan_id=? WHERE account_id=?"),
            ],
            "content-delivery": [
                ("SELECT", "content_catalog", "SELECT * FROM content_catalog WHERE asset_id=?"),
                ("INSERT", "stream_sessions", "INSERT INTO stream_sessions VALUES (?)"),
                ("UPDATE", "cache_manifest", "UPDATE cache_manifest SET ttl=? WHERE asset_id=?"),
            ],
            "network-analytics": [
                ("SELECT", "kpi_aggregates", "SELECT * FROM kpi_aggregates WHERE ts > NOW() - INTERVAL 5 MIN"),
                ("INSERT", "dpi_classifications", "INSERT INTO dpi_classifications VALUES (?)"),
                ("SELECT", "netflow_records", "SELECT * FROM netflow_records WHERE src_ip=?"),
            ],
            "voice-platform": [
                ("SELECT", "sip_registrations", "SELECT * FROM sip_registrations WHERE aor=?"),
                ("INSERT", "cdr_voice", "INSERT INTO cdr_voice VALUES (?)"),
                ("UPDATE", "trunk_status", "UPDATE trunk_status SET active_calls=? WHERE trunk_id=?"),
            ],
            "iot-connect": [
                ("SELECT", "device_registry", "SELECT * FROM device_registry WHERE device_id=?"),
                ("SELECT", "device_certs", "SELECT expiry FROM device_certs WHERE device_id=?"),
                ("UPDATE", "mqtt_sessions", "UPDATE mqtt_sessions SET last_seen=? WHERE client_id=?"),
            ],
            "noc-dashboard": [
                ("SELECT", "active_alarms", "SELECT * FROM active_alarms WHERE severity='P1' ORDER BY ts DESC"),
                ("INSERT", "incident_log", "INSERT INTO incident_log VALUES (?)"),
                ("UPDATE", "alarm_status", "UPDATE alarm_status SET ack=? WHERE alarm_id=?"),
            ],
        }

    # ── Infrastructure ─────────────────────────────────────────────────

    @property
    def hosts(self) -> list[dict[str, Any]]:
        return [
            {
                "host.name": "claro-aws-core-01",
                "host.id": "i-0a1b2c3d4e5f60001",
                "host.arch": "amd64",
                "host.type": "m5.16xlarge",
                "host.image.id": "ami-0fedcba987654321",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8175M CPU @ 2.50GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "4",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.20.1.10", "172.16.0.10"],
                "host.mac": ["0a:1b:2c:3d:4e:5f", "0a:1b:2c:3d:4e:60"],
                "os.type": "linux",
                "os.description": "Ubuntu 22.04.3 LTS",
                "cloud.provider": "aws",
                "cloud.platform": "aws_ec2",
                "cloud.region": "us-east-1",
                "cloud.availability_zone": "us-east-1a",
                "cloud.account.id": "123456789012",
                "cloud.instance.id": "i-0a1b2c3d4e5f60001",
                "cpu_count": 64,
                "memory_total_bytes": 274877906944,
                "disk_total_bytes": 1099511627776,
            },
            {
                "host.name": "claro-gcp-digital-01",
                "host.id": "claro-gcp-digital-01-id",
                "host.arch": "amd64",
                "host.type": "n2-standard-32",
                "host.image.id": "projects/claro-digital/images/ubuntu-2204",
                "host.cpu.model.name": "Intel(R) Xeon(R) Gold 6154 CPU @ 3.00GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "4",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.20.2.10"],
                "host.mac": ["0a:1b:2c:3d:4e:61"],
                "os.type": "linux",
                "os.description": "Ubuntu 22.04.3 LTS",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "us-central1",
                "cloud.availability_zone": "us-central1-a",
                "cloud.account.id": "claro-digital-prod",
                "cloud.instance.id": "claro-gcp-digital-01-id",
                "cpu_count": 32,
                "memory_total_bytes": 137438953472,
                "disk_total_bytes": 549755813888,
            },
            {
                "host.name": "claro-azure-ops-01",
                "host.id": "claro-azure-ops-01-id",
                "host.arch": "amd64",
                "host.type": "Standard_D32s_v5",
                "host.image.id": "Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:22.04.202401010",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8272CL CPU @ 2.60GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "7",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.20.3.10"],
                "host.mac": ["0a:1b:2c:3d:4e:62"],
                "os.type": "linux",
                "os.description": "Ubuntu 22.04.3 LTS",
                "cloud.provider": "azure",
                "cloud.platform": "azure_vm",
                "cloud.region": "eastus",
                "cloud.availability_zone": "eastus-1",
                "cloud.account.id": "claro-azure-prod",
                "cloud.instance.id": "claro-azure-ops-01-id",
                "cpu_count": 32,
                "memory_total_bytes": 137438953472,
                "disk_total_bytes": 549755813888,
            },
        ]

    @property
    def k8s_clusters(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "claro-eks-core",
                "provider": "aws",
                "platform": "aws_eks",
                "region": "us-east-1",
                "zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
                "os_description": "Amazon Linux 2",
                "services": ["mobile-core", "billing-engine", "sms-gateway"],
            },
            {
                "name": "claro-gke-digital",
                "provider": "gcp",
                "platform": "gcp_kubernetes_engine",
                "region": "us-central1",
                "zones": ["us-central1-a", "us-central1-b"],
                "os_description": "Container-Optimized OS",
                "services": ["customer-portal", "content-delivery", "network-analytics"],
            },
            {
                "name": "claro-aks-ops",
                "provider": "azure",
                "platform": "azure_aks",
                "region": "eastus",
                "zones": ["eastus-1", "eastus-2"],
                "os_description": "Ubuntu 22.04 LTS",
                "services": ["voice-platform", "iot-connect", "noc-dashboard"],
            },
        ]

    # ── UI & Theme ─────────────────────────────────────────────────────

    @property
    def theme(self) -> UITheme:
        return UITheme(
            bg_primary="#0A0F1A",
            bg_secondary="#0F1828",
            bg_tertiary="#1A2540",
            accent_primary="#DA291C",
            accent_secondary="#FF6B35",
            text_primary="#F0F4FF",
            text_secondary="#8B9CB8",
            text_accent="#DA291C",
            status_nominal="#2ECC71",
            status_warning="#F39C12",
            status_critical="#DA291C",
            status_info="#3498DB",
            font_family="'Inter', 'Segoe UI', system-ui, sans-serif",
            font_mono="'JetBrains Mono', 'Fira Code', monospace",
            font_size_base="14px",
            scanline_effect=False,
            glow_effect=False,
            grid_background=True,
            gradient_accent="linear-gradient(135deg, #DA291C 0%, #FF6B35 100%)",
            dashboard_title="Claro NOC — Red Operations",
            chaos_title="Network Fault Simulator",
            landing_title="Claro Network Operations Center",
            service_label="Network Function",
            channel_label="Fault",
        )

    @property
    def nominal_label(self) -> str:
        return "OPERACIONAL"

    # ── Agent & Elastic Config ─────────────────────────────────────────

    @property
    def agent_config(self) -> dict[str, Any]:
        return {
            "id": "claro-noc-analyst",
            "name": "Claro NOC Analyst",
            "system_prompt": (
                "You are the Claro NOC Analyst AI, an expert in Latin American telecommunications "
                "network operations. You have deep expertise in 5G/4G mobile core networks (AMF, SMF, UPF, "
                "IMS, EPC), real-time billing systems (OCS/OFCS, Diameter Gy/Rf/Cx), SS7/SIGTRAN signaling, "
                "CDN and video streaming operations, IoT MQTT broker management, BGP/MPLS routing, and "
                "SIP/VoIP infrastructure. You serve Claro's 300M+ subscribers across 18 Latin American "
                "countries. Your role is to rapidly investigate network incidents, correlate telemetry from "
                "9 microservices across AWS, GCP, and Azure, identify root causes, and recommend remediation "
                "steps. You communicate with urgency and precision, prioritizing subscriber impact and "
                "revenue protection. Always reference specific telemetry values from your search results "
                "and cite the affected service and IMSI/MSISDN ranges when available."
            ),
            "assessment_tool_name": "network_impact_assessment",
        }

    @property
    def assessment_tool_config(self) -> dict[str, Any]:
        return {
            "id": "network_impact_assessment",
            "description": (
                "Assess the operational impact of the current network incident on Claro subscribers. "
                "Queries error and warning telemetry across all 9 network functions to produce "
                "a subscriber impact estimate, revenue-at-risk calculation, and SLA breach assessment. "
                "Services monitored: mobile-core, billing-engine, sms-gateway, customer-portal, "
                "content-delivery, network-analytics, voice-platform, iot-connect, noc-dashboard."
            ),
        }

    # ── Knowledge Base ─────────────────────────────────────────────────

    @property
    def knowledge_base_docs(self) -> list[dict[str, Any]]:
        return [
            {
                "title": "5G SA Core Architecture — Claro LATAM",
                "content": (
                    "Claro's 5G Standalone (SA) core uses a cloud-native architecture with AMF, SMF, UPF, "
                    "PCF, and NRF deployed on AWS EKS. The AMF handles UE registration and mobility, SMF manages "
                    "PDU sessions and QoS, UPF is the data plane anchor. For PDU session failures, always check "
                    "SMF-UPF N4 interface first, then AMF-SMF N11, then NRF service discovery. GTP-U tunnel "
                    "issues are identified by checking the N3 interface MTU (should be 1500, inner 1460). "
                    "Common causes of mass session failure: UPF IP pool exhaustion, SMF pod crash/restart, "
                    "NRF unavailability blocking NF discovery."
                ),
            },
            {
                "title": "Real-Time Billing — OCS and Diameter Gy Interface",
                "content": (
                    "Claro uses an Online Charging System (OCS) for prepaid subscribers connected via "
                    "Diameter Gy interface. The PCEF (Policy and Charging Enforcement Function) is co-located "
                    "with the UPF. CCR-I (Initial), CCR-U (Update), CCR-T (Terminate) messages flow from PCEF "
                    "to OCS. Result code 4012 (Credit Limit Reached) means quota exhausted; 5030 (User Unknown) "
                    "means IMSI not found in OCS. OCS DB runs on Aurora PostgreSQL with read replicas. "
                    "Replication lag >2s risks double-granting. Default fallback on OCS failure is DENY for "
                    "prepaid. Offline charging (postpaid CDRs) uses Rf interface to CDF, then mediation to billing."
                ),
            },
            {
                "title": "SMS Infrastructure — SMSC and SMPP Integration",
                "content": (
                    "Claro LATAM operates regional SMSCs connected via SMPP v3.4 on TCP port 2775 (plain) "
                    "and 9749 (TLS). A2P messaging clients connect as ESME using bind_transceiver. "
                    "Throughput limits: B2C apps 1000 TPS, B2B 5000 TPS, premium 10000 TPS. "
                    "SMSC connects to HLR via SS7 MAP (MAP-SEND-ROUTING-INFO-FOR-SM) to get routing. "
                    "For queue overflow: Class-2 (SIM) drops first, Class-1 (ME), then Class-0 (flash, never drops). "
                    "A2P campaigns must be pre-approved by NOC with at least 24h notice. "
                    "SPAM detection runs on real-time content filter scoring 0-100; block threshold is 85."
                ),
            },
            {
                "title": "Customer Self-Care Portal — Authentication and API",
                "content": (
                    "The Mi Claro portal (mi.claro.com.br, mi.claro.com.co, etc.) uses OAuth2/OIDC via Okta "
                    "as IdP. Sessions are stored in Redis Cluster (3 primaries, 3 replicas per region). "
                    "SSO is federated via SAML 2.0 for enterprise customers. API rate limits: "
                    "B2C mobile app 1000 req/min per client_id, B2B integrators 5000 req/min. "
                    "The /recharge endpoint is highest-volume and most frequently throttled. "
                    "WAF rules protect against credential stuffing: >10 auth failures/IP/min triggers CAPTCHA. "
                    "For auth cascade failures, first check Okta status page, then Redis memory eviction rate, "
                    "then SSO certificate validity."
                ),
            },
            {
                "title": "CDN and Video Streaming — Claro TV and Sports",
                "content": (
                    "Claro TV and Claro Sports use a multi-CDN strategy with 48 PoPs across LATAM. "
                    "Video is encoded in H.264 (max compat) and H.265/HEVC (4K). Live events use HLS with "
                    "6-second segments; VOD uses DASH. DRM: Widevine (Android/Chrome), PlayReady (Windows), "
                    "FairPlay (iOS/macOS). Cache TTLs: live manifests 2s, live segments 6s, VOD manifests 300s, "
                    "VOD segments 86400s. Origin shield is mandatory — edge PoPs fetch from shield, not origin. "
                    "Cache purge scope should always be path-specific, never wildcard. "
                    "Transcoding farm runs on GCP with NVIDIA T4 GPUs; live events take priority over VOD."
                ),
            },
            {
                "title": "Network Analytics — DPI, NetFlow, and KPI Pipeline",
                "content": (
                    "Claro's network analytics stack ingests IPFIX/NetFlow v9 from 2,400 routers and "
                    "DPI classified flows from 18 DPI clusters (capacity 40Gbps each). "
                    "Stream processing runs on Apache Flink on GCP. Kafka topics: netflow.ipfix.raw (1200 partitions), "
                    "mobile.kpi.5min (240 partitions), cdn.access.realtime (120 partitions). "
                    "DPI signatures must be updated weekly; stale signatures cause UNKNOWN classification spikes. "
                    "QUIC/HTTP3 traffic requires quic-aware=true DPI config. KPI results are written to Elasticsearch "
                    "for NOC dashboards. Consumer lag >100K events is critical — triggers auto-scaling of Flink workers."
                ),
            },
            {
                "title": "Voice Platform — SIP, IMS, and VoIP Operations",
                "content": (
                    "Claro voice infrastructure uses IMS (IP Multimedia Subsystem) with P-CSCF, I-CSCF, "
                    "S-CSCF, and HSS. SIP trunks connect to PSTN via ISUP over SIP-T. "
                    "SBC (Session Border Controller) capacity: 2,400 simultaneous sessions per node. "
                    "IMS registration expiry is randomized 3400-4200s to prevent synchronized re-registration storms. "
                    "Diameter Cx interface (I-CSCF to HSS) must complete in <200ms. "
                    "SIP failure codes to know: 486 BUSY (termination), 503 SERVICE UNAVAILABLE (capacity), "
                    "500 SERVER ERROR (IMS internal), 408 TIMEOUT (network). "
                    "Emergency IMS admission control limit: 5000 REGISTER/s. Normal baseline: ~2000 REGISTER/s."
                ),
            },
            {
                "title": "IoT Platform — MQTT, Device Registry, and PKI",
                "content": (
                    "Claro IoT Connect manages 5.2M devices across smart meters, industrial sensors, "
                    "connected vehicles, and consumer IoT. MQTT broker runs on Eclipse Mosquitto cluster "
                    "(Azure AKS), max 500K concurrent connections. Devices use X.509 certificates from "
                    "Claro's PKI (2-tier CA). Certificate lifetime: 2 years for fixed devices, 1 year for mobile. "
                    "OTA certificate rotation supported on 78% of device fleet; legacy devices require field dispatch. "
                    "MQTT QoS levels: smart meters use QoS 1 (at-least-once), industrial safety uses QoS 2. "
                    "Device reconnect must use exponential backoff with jitter: base 5s, max 300s, jitter 0.2. "
                    "Critical devices (hospitals, utilities): guaranteed SLA 99.99%, monitored via dedicated NOC queue."
                ),
            },
            {
                "title": "BGP and Core Routing — Claro LATAM Backbone",
                "content": (
                    "Claro's LATAM backbone uses BGP (iBGP + eBGP) with MPLS transport. "
                    "Core routers: Cisco ASR 9000 series, Juniper MX960. "
                    "AS number: AS28573 (Brazil), AS10097 (Argentina), AS8167 (regional). "
                    "RPKI is deployed — all originated prefixes have valid ROAs. "
                    "BFD timers: 300ms interval, multiplier 3 (900ms detection). "
                    "BGP dampening should activate after 3 flaps in 30 minutes. "
                    "Peering points: NAP do Brasil (São Paulo), PTT Metro (Rio), CABASE (Buenos Aires). "
                    "For BGP flaps: check physical layer first, then BFD false positives (CPU spikes), "
                    "then RPKI validity of withdrawn prefixes. Never apply dampening to eBGP routes from "
                    "single-homed customers."
                ),
            },
            {
                "title": "NOC Operations — Alert Management and Incident Response",
                "content": (
                    "Claro NOC operates 24/7 with Tier 1/2/3 escalation. Severity: P1 (<15min response), "
                    "P2 (<1h response), P3 (<4h response). Alert deduplication window: 300s for P2/P3, "
                    "60s for P1. Correlation engine groups alerts by root cause using topology maps. "
                    "Alert storm threshold: >1000 alerts/min triggers automatic incident bridge page. "
                    "Runbooks are stored in Elastic Knowledge Base (index: claro-knowledge-base). "
                    "Shift handoff at 06:00, 14:00, 22:00 local time. "
                    "Escalation chain: NOC Analyst → Senior NOC → Network Engineer → Service Manager → CTO. "
                    "Post-incident review required for all P1 events within 48 hours."
                ),
            },
            {
                "title": "5G DNS and NRF Service Discovery",
                "content": (
                    "5G core NFs use DNS-based service discovery via NRF. Each NF registers with NRF "
                    "and queries NRF for peer NF addresses. NRF itself uses DNS to resolve NF FQDN templates. "
                    "DNS failure cascades to NF discovery failure, breaking SMF-UPF pairing and AMF-SMF signaling. "
                    "Primary DNS: claro-dns-cluster-01 (AWS). Secondary: claro-dns-cluster-02 (AWS). "
                    "DNSSEC is enabled — DNSSEC validation failures often from DNSKEY rollover issues. "
                    "RRL (Response Rate Limiting): 50/s per source. "
                    "For DNS amplification: enable RRL, block non-recursive queries from external IPs. "
                    "DHCP DNS option: 150.164.0.1 (BR primary), 150.164.1.1 (BR secondary)."
                ),
            },
            {
                "title": "Fraud Detection — Real-Time Charging and SIM Swap",
                "content": (
                    "Claro's fraud system monitors for: premium rate fraud (IPRN), SIM swap attacks, "
                    "calling-card arbitrage, and subscription fraud. "
                    "Real-time rules: SMS velocity >50/min triggers alert; >500/min triggers block. "
                    "SIM swap verification: mandatory 24h cooling period after SIM swap before allowing "
                    "sensitive operations (bank OTP, password reset). "
                    "IPRN block list: automatically block calls to 232 (Sierra Leone), 234 (Nigeria premium), "
                    "236 (Central African Republic) unless subscriber has explicit international roaming. "
                    "Dual-IMSI detection: same MSISDN active on 2 IMSIs simultaneously is SIM clone. "
                    "ML model: FraudNet-v6.1, updated daily. Threshold: score >70 = block, 50-70 = challenge."
                ),
            },
            {
                "title": "LTE Handover — X2 and S1 Procedures",
                "content": (
                    "LTE X2 handover (direct eNodeB-to-eNodeB) is preferred for intra-frequency mobility. "
                    "S1 handover (via MME) is fallback for inter-frequency or cross-MME scenarios. "
                    "Common X2 HO failure causes: UE_NOT_FOUND (target lost UE context), NO_RADIO_RESOURCES "
                    "(target cell full), UNKNOWN_ENODEB (X2 interface not configured). "
                    "A3 event threshold (RSRP): trigger offset 3dB, time-to-trigger 160ms. "
                    "Ping-pong HO: A3 events within 1 second of HO completion. Tune: increase TTT or offset. "
                    "MME signaling load: OVERLOAD at >80% CPU triggers S1AP Overload Start (reduction factor 90%). "
                    "S-GW bearer modification must complete in <100ms for seamless handover."
                ),
            },
            {
                "title": "OCS Fault Procedures — Prepaid Service Recovery",
                "content": (
                    "When OCS Diameter Gy fails, ALL prepaid data sessions are blocked (DENY fallback policy). "
                    "Immediate actions: (1) page on-call OCS engineer, (2) check OCS primary DB health, "
                    "(3) initiate OCS-B failover if primary is down. "
                    "Failover procedure: pcef-cli set ocs-primary=ocs-b.claro.internal "
                    "Temporary whitelist for emergency: pcef-cli whitelist add --dnn=emergency --quota=10MB "
                    "OCS-B failover takes approximately 90 seconds. "
                    "Revenue impact calculation: prepaid_subs × avg_data_rev_per_min × outage_minutes. "
                    "ARPU LATAM prepaid: $0.18/hour data. For a 1M subscriber outage: $3,000/min revenue impact."
                ),
            },
            {
                "title": "CDR Mediation — Revenue Assurance",
                "content": (
                    "CDR mediation processes raw charging records from 5G-SMF, LTE-SGW, IMS (voice), "
                    "and SMSC (SMS). CDRs arrive via SFTP every 5 minutes from each network element. "
                    "Mediation pipeline: receive → validate → parse (ASN.1) → normalize → rate → output to billing. "
                    "Parse failure root causes: ASN.1 schema version mismatch (most common after NE upgrade), "
                    "truncated CDR files (SFTP interruption), encoding errors (UTF-8 vs Latin-1 in subscriber names). "
                    "Revenue assurance rule: if mediation lag >15 min, trigger revenue assurance alert. "
                    "Deduplication: 90-day window using CDR sequence numbers. Never disable dedup during reprocessing. "
                    "SLA: 99.9% of CDRs rated within 1 hour of generation."
                ),
            },
            {
                "title": "Portal API — Rate Limiting and Quota Management",
                "content": (
                    "Claro self-care API rate limits by client_id (OAuth2 client credential). "
                    "Tiers: B2C (1000 req/min), B2B-Standard (5000 req/min), B2B-Premium (20000 req/min), "
                    "Internal (unlimited). Rate limit response: HTTP 429 with Retry-After header (60s). "
                    "Burst allowance: 2× limit for 10 seconds. "
                    "High-traffic endpoints: /balance (42% of traffic), /recharge (28%), /plan/change (18%). "
                    "For rate limit violations: (1) identify client, (2) check for retry storm (exponential backoff?), "
                    "(3) contact client team, (4) consider temporary limit increase if backend is healthy. "
                    "A/B testing and marketing campaigns must notify the API team 48h in advance."
                ),
            },
            {
                "title": "MQTT Broker — IoT Device Reconnection Procedures",
                "content": (
                    "MQTT broker capacity: 500K concurrent connections per cluster (3-node cluster on Azure AKS). "
                    "Reconnection storm prevention: all device firmware must implement exponential backoff "
                    "with jitter. Recommended: base=5s, max=300s, jitter=random(0, 0.2 × current_interval). "
                    "When broker is at capacity: (1) identify top clients by connection rate, "
                    "(2) push backoff config via MQTT retained message on $SYS/config/reconnect, "
                    "(3) scale broker replicas: kubectl scale deployment mqtt-broker --replicas=6. "
                    "QoS 1 message accumulation: check heap usage. At 80% heap, enable message expiry "
                    "(message-expiry-interval: 3600). At 90%, force-disconnect lowest-priority clients. "
                    "Priority: critical IoT (hospitals, utilities) > industrial > smart meters > consumer."
                ),
            },
            {
                "title": "Video Transcoding — GPU Farm Operations",
                "content": (
                    "Claro TV and Claro Sports transcoding runs on GCP with NVIDIA T4 GPUs (NVENC). "
                    "Encoding profiles: H.264 (360p, 480p, 720p, 1080p), H.265 (1080p, 4K). "
                    "Live priority queue: channels CLAROSPORTS1-4 and CLAROTV-HD preempt all VOD jobs. "
                    "Worker failure recovery: (1) drain failed worker, (2) reassign job to available GPU, "
                    "(3) if no workers available, scale: kubectl scale deployment transcoder --replicas=8. "
                    "DRM signing key server: drm.claro.internal:8443. SLA: <500ms signing latency. "
                    "HLS ingest quality check: TS errors >0.1% trigger ingest stream restart from origin. "
                    "GPU driver version must match NVENC library version — check: nvidia-smi + nvcc --version."
                ),
            },
            {
                "title": "IMS Registration — Overload Protection",
                "content": (
                    "IMS registration storm typically follows: power restoration, S-CSCF restart, "
                    "or mass LTE reattach. Recovery sequence: "
                    "(1) Enable P-CSCF admission control: p-cscf-cli admission-control rate-limit=5000 "
                    "(2) Monitor HSS Cx latency — must be <200ms before lifting rate limit "
                    "(3) Disable admission control only when registration rate drops below 3000/s "
                    "Registration storm duration: typically 8-15 minutes until all subscribers re-register. "
                    "HSS capacity: 50M subscribers, 10K Cx operations/second peak. "
                    "S-CSCF assignment algorithm: round-robin with capability matching. "
                    "During storm: disable non-essential S-CSCF features (presence, conferencing) to free CPU."
                ),
            },
            {
                "title": "Incident Playbook — Subscriber Impact Assessment",
                "content": (
                    "For any network incident, the NOC Analyst must immediately assess subscriber impact: "
                    "1. Mobile Data: affected_IMSIs × avg_data_rev = revenue_at_risk (data ARPU: $0.18/hour). "
                    "2. Voice: blocked_calls × avg_call_duration × voice_ARPU = revenue_at_risk. "
                    "3. SMS: undelivered_messages × SMS_ARPU = revenue_at_risk. "
                    "4. Regulatory: telecom regulators (ANATEL/BR, CRC/CO, etc.) require notification "
                    "within 1 hour for outages affecting >100K subscribers or >30 minutes duration. "
                    "5. SLA breach: Enterprise/B2B customers have SLA credits for >99.9% availability. "
                    "Escalate to Service Manager immediately for any P1 affecting >1M subscribers. "
                    "Customer notification: SMS broadcast to affected MSISDNs within 15 minutes of P1 confirmation."
                ),
            },
        ]

    # ── Service Classes ────────────────────────────────────────────────

    def get_service_classes(self) -> list[type]:
        from scenarios.claro.services.mobile_core import MobileCoreService
        from scenarios.claro.services.billing_engine import BillingEngineService
        from scenarios.claro.services.sms_gateway import SmsGatewayService
        from scenarios.claro.services.customer_portal import CustomerPortalService
        from scenarios.claro.services.content_delivery import ContentDeliveryService
        from scenarios.claro.services.network_analytics import NetworkAnalyticsService
        from scenarios.claro.services.voice_platform import VoicePlatformService
        from scenarios.claro.services.iot_connect import IotConnectService
        from scenarios.claro.services.noc_dashboard import NocDashboardService

        return [
            MobileCoreService,
            BillingEngineService,
            SmsGatewayService,
            CustomerPortalService,
            ContentDeliveryService,
            NetworkAnalyticsService,
            VoicePlatformService,
            IotConnectService,
            NocDashboardService,
        ]

    # ── Fault Parameters ───────────────────────────────────────────────

    def get_fault_params(self, channel: int) -> dict[str, Any]:
        rng = random.Random()
        imsi = f"724{rng.randint(10,99)}{rng.randint(100000000, 999999999)}"
        msisdn = f"+55{rng.randint(11,99)}{rng.randint(900000000, 999999999)}"

        params = {
            # Common
            "imsi": imsi,
            "msisdn": msisdn,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            # 5G
            "pdu_id": f"pdu-{rng.randint(100000, 999999)}",
            "reject_cause": rng.choice(["ResourceLimitReached", "CongestionDetected", "UPF_Unavailable"]),
            "amf_instance": f"amf-{rng.randint(1,4):02d}",
            "smf_instance": f"smf-{rng.randint(1,4):02d}",
            "upf_node": f"upf-node-{rng.randint(1,12):02d}",
            # LTE
            "enb_src": f"eNB-{rng.randint(10000, 99999)}",
            "enb_tgt": f"eNB-{rng.randint(10000, 99999)}",
            "ho_cause": rng.choice(["UE_NOT_FOUND", "NO_RADIO_RESOURCES", "S1_PATH_SWITCH_FAIL"]),
            "ue_count": rng.randint(200, 2400),
            "drop_rate": round(rng.uniform(15, 45), 1),
            # Billing
            "cdr_queue": rng.randint(500000, 2000000),
            "parse_failures": rng.randint(2000, 15000),
            "revenue_risk": f"{rng.randint(50, 500):,}000",
            "cdr_lag_min": rng.randint(15, 90),
            "ccr_type": rng.choice(["I", "U", "T"]),
            "session_id": f"sess-{rng.randint(1000000, 9999999)}",
            "diameter_result": rng.choice(["5012", "4012", "3002"]),
            "ocs_host": f"ocs-{rng.choice(['a','b'])}.claro.internal",
            "ocs_latency_ms": rng.randint(2000, 15000),
            "affected_subs": f"{rng.randint(100, 800):,}K",
            "ocs_revenue": f"{rng.randint(10, 180):,}000",
            "fraud_type": rng.choice(["SIM_SWAP", "IPRN_FRAUD", "PREMIUM_SMS"]),
            "fraud_score": rng.randint(72, 98),
            "sms_velocity": rng.randint(500, 2000),
            "fraud_revenue": f"{rng.randint(5, 80):,}000",
            # SMS
            "smsc_queue": rng.randint(80000, 180000),
            "sms_drop_rate": round(rng.uniform(5, 25), 1),
            "a2p_rate": rng.randint(5000, 20000),
            "hlr_timeout_ms": rng.randint(800, 5000),
            "smpp_system_id": f"esme-{rng.choice(['mktg','crm','bank','health'])}-{rng.randint(1,9)}",
            "smpp_bind_type": rng.choice(["bind_transmitter", "bind_receiver", "bind_transceiver"]),
            "smpp_error": rng.choice(["ESME_RBINDFAIL", "ESME_RINVPASWD", "ESME_RTHROTTLED"]),
            "smpp_error_hex": rng.choice(["0000000D", "0000000E", "00000058"]),
            "smpp_active": rng.randint(480, 500),
            "smpp_max": 500,
            # Portal
            "auth_fail_rate": round(rng.uniform(42, 82), 1),
            "auth_success": rng.randint(100, 800),
            "auth_fail": rng.randint(20000, 42000),
            "idp_status": rng.choice(["TIMEOUT", "ERROR_503", "UNREACHABLE"]),
            "affected_users": f"{rng.randint(50, 800):,}K",
            "redis_state": rng.choice(["FAILOVER", "EVICTING", "OOM"]),
            "api_client": f"client-{rng.randint(1000, 9999)}",
            "api_endpoint": rng.choice(["/v1/account/balance", "/v1/recharge", "/v1/plan/change"]),
            "api_rate": rng.randint(3000, 8000),
            "api_limit": 1000,
            "throttled_reqs": rng.randint(2000, 6000),
            # CDN
            "cache_hit_rate": rng.randint(8, 18),
            "origin_rps": rng.randint(40000, 120000),
            "purge_count": rng.randint(2000000, 8000000),
            "cdn_pop": rng.choice(["SAO-01", "RIO-01", "BOG-01", "MIA-01", "MEX-01"]),
            "rebuffer_rate": round(rng.uniform(8, 35), 1),
            "transcode_queue": rng.randint(200, 800),
            "live_events_delayed": rng.randint(2, 8),
            "vod_backlog_hours": round(rng.uniform(4, 18), 1),
            "gpu_util": rng.randint(88, 99),
            "vod_job_id": f"vod-{rng.randint(10000, 99999)}",
            "vod_batch": f"batch-{rng.randint(100, 999)}",
            # Analytics
            "kafka_lag": rng.randint(500000, 5000000),
            "flink_bp": rng.randint(75, 99),
            "processing_delay": rng.randint(8, 35),
            "unclassified_pct": rng.randint(35, 65),
            "dpi_throughput": round(rng.uniform(38, 52), 1),
            "sig_age": rng.randint(8, 21),
            "quic_misclass": rng.randint(60, 90),
            # Voice
            "trunk_util": rng.randint(94, 99),
            "active_calls": rng.randint(2200, 2390),
            "max_calls": 2400,
            "sip_503": rng.randint(1000, 5000),
            "cic_exhausted": rng.choice(["true", "false"]),
            "ims_reg_rate": rng.randint(8000, 25000),
            "pcscf_load": rng.randint(88, 99),
            "hss_latency_ms": rng.randint(800, 4200),
            "ims_queue": rng.randint(5000, 25000),
            # IoT
            "mqtt_connections": rng.randint(490000, 500000),
            "mqtt_max": 500000,
            "msg_queue_mb": rng.randint(6000, 8000),
            "qos1_undelivered": rng.randint(500000, 2000000),
            "reconnect_rate": rng.randint(2000, 8000),
            "expired_devices": f"{rng.randint(100, 400):,}K",
            "expiring_soon": f"{rng.randint(400, 800):,}K",
            "tls_failures": rng.randint(5000, 25000),
            "ocsp_status": rng.choice(["UNREACHABLE", "TIMEOUT", "ERROR"]),
            "ota_pct": rng.randint(65, 80),
            # NOC
            "alert_rate": rng.randint(800, 2400),
            "active_alerts": rng.randint(1200, 4800),
            "p1_alerts": rng.randint(80, 240),
            "correlated_pct": rng.randint(8, 25),
            "mtta_min": rng.randint(18, 45),
            "bgp_peer": f"100.{rng.randint(1,254)}.{rng.randint(1,254)}.1",
            "peer_asn": rng.randint(64500, 65000),
            "bgp_state": rng.choice(["ACTIVE", "CONNECT", "IDLE"]),
            "flap_count": rng.randint(8, 48),
            "prefixes_lost": rng.randint(800, 4800),
            "traffic_gbps": round(rng.uniform(8, 42), 1),
            "dns_resolver": rng.choice(["claro-dns-01.aws", "claro-dns-02.aws"]),
            "dns_qtype": rng.choice(["A", "AAAA", "SRV"]),
            "dns_rcode": rng.choice(["SERVFAIL", "TIMEOUT"]),
            "dns_qps": rng.randint(80000, 200000),
            "dns_cache_hit": rng.randint(4, 12),
            "nrf_affected": rng.randint(3, 9),
            # Other
            "routing_number": f"0{rng.randint(10000000, 99999999)}",
            "acct_last4": rng.randint(1000, 9999),
        }
        return params

    def get_trace_attributes(self, service_name: str, rng) -> dict:
        country = rng.choice(["BR", "CO", "AR", "CL", "PE", "MX", "EC", "PY", "UY", "GT"])
        return {
            "claro.country": country,
            "claro.region": f"LATAM-{country}",
            "claro.network_type": rng.choice(["5G-SA", "LTE", "5G-NSA"]),
        }

    def get_rca_clues(self, channel: int, service_name: str, rng) -> dict:
        clues = {
            1: {"claro.pdu.reject_cause": rng.choice(["ResourceLimitReached", "CongestionDetected"])},
            2: {"claro.lte.ho_cause": rng.choice(["UE_NOT_FOUND", "NO_RADIO_RESOURCES"])},
            3: {"claro.cdr.parse_error": "ASN1_SCHEMA_MISMATCH"},
            4: {"claro.ocs.result_code": rng.choice(["5012", "4012"])},
            5: {"claro.fraud.type": rng.choice(["SIM_SWAP", "IPRN_FRAUD"])},
            6: {"claro.smsc.overflow_class": rng.choice(["CLASS-1", "CLASS-2"])},
            7: {"claro.smpp.error": rng.choice(["ESME_RBINDFAIL", "ESME_RTHROTTLED"])},
            8: {"claro.portal.idp_status": rng.choice(["TIMEOUT", "ERROR_503"])},
            9: {"claro.api.throttle_reason": "RATE_LIMIT_EXCEEDED"},
            10: {"claro.cdn.purge_scope": "WILDCARD"},
            11: {"claro.cdn.gpu_worker_status": "FAILED"},
            12: {"claro.analytics.lag_cause": "FLINK_BACKPRESSURE"},
            13: {"claro.dpi.sig_staleness_days": str(rng.randint(8, 21))},
            14: {"claro.voice.trunk_failure": "CIC_EXHAUSTED"},
            15: {"claro.ims.storm_cause": "S_CSCF_RESTART"},
            16: {"claro.iot.broker_failure": "MAX_CONNECTIONS_REACHED"},
            17: {"claro.iot.cert_failure": "X509_EXPIRED"},
            18: {"claro.noc.correlation_disabled": "true"},
            19: {"claro.bgp.flap_cause": rng.choice(["BFD_FAILURE", "PHYSICAL_LINK_ERROR"])},
            20: {"claro.dns.rcode": rng.choice(["SERVFAIL", "TIMEOUT"])},
        }
        return clues.get(channel, {})

    def get_correlation_attribute(self, channel: int, is_error: bool, rng) -> dict:
        if is_error:
            return {"claro.fault_channel": str(channel)}
        return {}


# Module-level singleton for scenario registry discovery
scenario = ClaroScenario()

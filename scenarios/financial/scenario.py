"""Financial Trading Platform scenario — real-time trading operations with order management,
matching engine, risk calculation, market data, and settlement systems."""

from __future__ import annotations

import random
import time
from typing import Any

from scenarios.base import BaseScenario, CountdownConfig, UITheme


class FinancialScenario(BaseScenario):
    """Financial trading platform with 9 trading services and 20 fault channels."""

    # ── Identity ──────────────────────────────────────────────────────

    @property
    def scenario_id(self) -> str:
        return "financial"

    @property
    def scenario_icon(self) -> str:
        return "💹"

    @property
    def scenario_name(self) -> str:
        return "Financial Trading Platform"

    @property
    def scenario_description(self) -> str:
        return (
            "Real-time trading operations with order management, matching engine, "
            "risk calculation, market data, and settlement systems. Bloomberg "
            "terminal-style Operations Center."
        )

    @property
    def namespace(self) -> str:
        return "finserv"

    @property
    def sort_order(self) -> int:
        return 3

    @property
    def raw_log_profile(self) -> dict[str, Any]:
        return {
            "service_name": "trading-edge",
            "user_id_prefix": "trader",
            "tier_field": "account_class",
            "tier_values": [("retail", 55), ("prime", 30), ("institutional", 15)],
            "country_weights": {"US": 45, "GB": 15, "JP": 10, "SG": 10, "DE": 8, "HK": 7, "CH": 5},
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "paths": [
                "/api/v1/orders", "/api/v1/positions", "/api/v1/market-data",
                "/api/v1/risk", "/api/v1/quotes", "/api/v1/portfolios",
                "/login", "/health",
            ],
            "change_point_path": "/api/v1/orders",
        }

    @property
    def executive_kpi_emitter_service_name(self) -> str:
        return "risk-calculator"

    @property
    def executive_dashboard_intro(self) -> str:
        return (
            "**Trading platform KPIs** — trade flow, risk exposure, market quality, "
            "and settlement operations (synthetic `business.*` from `risk-calculator`)."
        )

    @property
    def executive_kpi_sections(self) -> list[dict]:
        return [
            {
                "header": "**Trade flow** — orders, fill rate, notional, executions, and rejects",
                "specs": [
                    ("Order flow / min", "metrics.business.order_flow_per_min"),
                    ("Fill rate (%)", "metrics.business.fill_rate_pct"),
                    ("Notional value (USD/min)", "metrics.business.notional_value_usd_per_min"),
                    ("Executed trades / min", "metrics.business.executed_trades_per_min"),
                    ("Rejected orders / min", "metrics.business.rejected_orders_per_min"),
                    ("Cancel-replace rate (%)", "metrics.business.cancel_replace_rate_pct"),
                ],
            },
            {
                "header": "**Risk exposure** — VaR, margin, limits, delta, counterparty, and P&L",
                "specs": [
                    ("Portfolio VaR (USD)", "metrics.business.portfolio_var_usd"),
                    ("Margin utilization (%)", "metrics.business.margin_utilization_pct"),
                    ("Position limit breaches", "metrics.business.position_limit_breaches"),
                    ("Delta exposure (USD)", "metrics.business.delta_exposure_usd"),
                    ("Counterparty credit risk (USD)", "metrics.business.counterparty_credit_risk_usd"),
                    ("Mark-to-market P&L (USD/min)", "metrics.business.mark_to_market_pnl_usd_per_min"),
                ],
            },
            {
                "header": "**Market quality** — spread, impact, slippage, latency, and best execution",
                "specs": [
                    ("Avg spread (bps)", "metrics.business.avg_spread_bps"),
                    ("Market impact (bps)", "metrics.business.market_impact_bps"),
                    ("Slippage cost (USD/min)", "metrics.business.slippage_cost_usd_per_min"),
                    ("Latency SLA breach (%)", "metrics.business.latency_sla_breach_rate_pct"),
                    ("Best execution (%)", "metrics.business.best_execution_pct"),
                    ("Venue fill quality (%)", "metrics.business.venue_fill_quality_pct"),
                ],
            },
            {
                "header": "**Operations** — settlement, fails, breaks, alerts, availability, and reporting",
                "specs": [
                    ("Settlement success rate (%)", "metrics.business.settlement_success_rate_pct"),
                    ("Settlement fails in queue", "metrics.business.settlement_fails_in_queue"),
                    ("Reconciliation breaks", "metrics.business.reconciliation_breaks"),
                    ("Ops alerts / min", "metrics.business.ops_alerts_per_min"),
                    ("System availability (%)", "metrics.business.system_availability_pct"),
                    ("Reporting latency (s)", "metrics.business.reporting_latency_sec"),
                ],
            },
        ]

    @property
    def executive_trend_charts(self) -> list[dict]:
        return [
            {"title": "Order flow / min", "field": "metrics.business.order_flow_per_min", "y_label": "orders/min"},
            {"title": "Notional value (USD/min)", "field": "metrics.business.notional_value_usd_per_min", "y_label": "USD/min"},
            {"title": "Mark-to-market P&L", "field": "metrics.business.mark_to_market_pnl_usd_per_min", "y_label": "USD/min"},
            {"title": "Portfolio VaR", "field": "metrics.business.portfolio_var_usd", "y_label": "USD"},
            {"title": "Fill rate", "field": "metrics.business.fill_rate_pct", "y_label": "%"},
            {"title": "Settlement success rate", "field": "metrics.business.settlement_success_rate_pct", "y_label": "%"},
        ]

    # ── Services ──────────────────────────────────────────────────────

    @property
    def services(self) -> dict[str, dict[str, Any]]:
        return {
            "order-gateway": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1a",
                "subsystem": "order_management",
                "language": "java",
            },
            "matching-engine": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1b",
                "subsystem": "trade_execution",
                "language": "cpp",
            },
            "risk-calculator": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1c",
                "subsystem": "risk_management",
                "language": "python",
            },
            "market-data-feed": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "market_data",
                "language": "go",
            },
            "settlement-processor": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-b",
                "subsystem": "settlement",
                "language": "java",
            },
            "fraud-detector": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "compliance",
                "language": "python",
            },
            "compliance-monitor": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "compliance",
                "language": "dotnet",
            },
            "customer-portal": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-2",
                "subsystem": "client_services",
                "language": "python",
            },
            "audit-logger": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "audit",
                "language": "go",
            },
        }

    # ── Channel Registry ──────────────────────────────────────────────

    @property
    def channel_registry(self) -> dict[int, dict[str, Any]]:
        return {
            1: {
                "name": "Order Book Inconsistency",
                "subsystem": "order_management",
                "vehicle_section": "order_book",
                "error_type": "OMS-BOOK-IMBALANCE",
                "sensor_type": "order_book_integrity",
                "affected_services": ["order-gateway", "matching-engine"],
                "cascade_services": ["risk-calculator", "audit-logger"],
                "description": "Order book bid/ask levels out of sync between primary and replica shards",
                "error_message": "[OMS] OMS-BOOK-IMBALANCE: instrument={instrument} bid_ask_spread={spread}ticks max_spread={max_spread}ticks book={book_id}",
                "stack_trace": (
                    "=== ORDER BOOK SNAPSHOT {book_id} ===\n"
                    "instrument={instrument}  status=IMBALANCED\n"
                    "--------- BID SIDE ---------  --------- ASK SIDE ---------\n"
                    "  LEVEL   PRICE     QTY         LEVEL   PRICE     QTY\n"
                    "  1       244.50    1200         1       244.85    800\n"
                    "  2       244.48    3400         2       244.90    2100\n"
                    "  3       244.45    5600         3       244.95    1500\n"
                    "  4       244.40    2800         4       245.10    4200\n"
                    "  5       244.35    1100         5       245.25    6700\n"
                    "spread={spread}ticks  max_allowed={max_spread}ticks\n"
                    "replica_sync=STALE  last_sync_us=48230  primary_seq=8832014  replica_seq=8831997\n"
                    "ACTION: halt_matching=true  alert=OMS-BOOK-IMBALANCE"
                ),
            },
            2: {
                "name": "Audit Log Sequence Gap",
                "subsystem": "audit",
                "vehicle_section": "audit_pipeline",
                "error_type": "AUDIT-SEQ-GAP",
                "sensor_type": "sequence_validator",
                "affected_services": ["audit-logger", "compliance-monitor"],
                "cascade_services": ["settlement-processor"],
                "description": "Audit trail event sequence numbers have gaps indicating lost events",
                "error_message": "[AUDIT] AUDIT-SEQ-GAP: stream={audit_stream} expected={expected_seq} received={last_seq} gap_count={gap_count}",
                "stack_trace": (
                    "=== AUDIT PIPELINE STATUS ===\n"
                    "stream={audit_stream}  partition=0\n"
                    "--- SEQUENCE ANALYSIS ---\n"
                    "  last_committed_seq   {last_seq}\n"
                    "  expected_next_seq    {expected_seq}\n"
                    "  gap_size             {gap_count} events\n"
                    "  gap_duration         ~4.2s\n"
                    "--- PIPELINE HEALTH ---\n"
                    "  kafka_consumer_lag   2,340\n"
                    "  write_ahead_log      BEHIND\n"
                    "  hash_chain           BROKEN (gap invalidates chain from seq {expected_seq})\n"
                    "  immutability_proof   INVALID\n"
                    "--- RECOVERY ---\n"
                    "  replay_source=kafka  replay_from={expected_seq}  estimated_time=12s\n"
                    "  reg_impact=SEC-17a4  audit_gap_report=REQUIRED\n"
                    "ACTION: pause_pipeline=true  request_replay=true  alert=AUDIT-SEQ-GAP"
                ),
            },
            3: {
                "name": "Price Feed Gap",
                "subsystem": "market_data",
                "vehicle_section": "feed_handler",
                "error_type": "MDF-PRICE-GAP",
                "sensor_type": "feed_continuity",
                "affected_services": ["market-data-feed", "matching-engine"],
                "cascade_services": ["risk-calculator", "customer-portal"],
                "description": "Market data feed missing price ticks for one or more instruments",
                "error_message": "[MDF] MDF-PRICE-GAP: symbol={symbol} gap_ms={gap_ms} exchange={exchange} seq_start={seq_start} seq_end={seq_end}",
                "stack_trace": (
                    "=== FEED HANDLER SEQUENCE ANALYSIS ===\n"
                    "symbol={symbol}  exchange={exchange}  feed_id=MDF-PRIMARY-01\n"
                    "seq_expected={seq_start}  seq_received={seq_end}\n"
                    "gap_duration_ms={gap_ms}  max_allowed_ms=200\n"
                    "--- SEQUENCE WINDOW ---\n"
                    "  seq {seq_start}  MISSING  (gap start)\n"
                    "  ...  ({gap_ms}ms silence)\n"
                    "  seq {seq_end}  RECEIVED  price=244.7200  qty=1500  ts=14:32:07.882\n"
                    "retransmit_requested=true  channel=FAST/FIX  multicast_grp=224.0.31.1:14310\n"
                    "handler_state=RECOVERING  stale_instruments=12  affected_books=3\n"
                    "ACTION: mark_stale=true  request_retransmit=true  alert=MDF-PRICE-GAP"
                ),
            },
            4: {
                "name": "Risk Limit Breach",
                "subsystem": "risk_management",
                "vehicle_section": "risk_engine",
                "error_type": "RISK-LIMIT-BREACH",
                "sensor_type": "risk_threshold",
                "affected_services": ["risk-calculator", "order-gateway"],
                "cascade_services": ["matching-engine", "compliance-monitor"],
                "description": "Trading desk risk exposure exceeds configured limit thresholds",
                "error_message": "[RISK] RISK-LIMIT-BREACH: desk={desk_id} exposure=${exposure} limit=${risk_limit} asset_class={asset_class}",
                "stack_trace": (
                    "=== RISK CALCULATION REPORT ===\n"
                    "desk={desk_id}  asset_class={asset_class}\n"
                    "--- EXPOSURE BREAKDOWN ---\n"
                    "  gross_long     ${exposure}\n"
                    "  gross_short    $42.3M\n"
                    "  net_exposure   ${exposure}\n"
                    "  limit          ${risk_limit}\n"
                    "  utilization    287%  <<< BREACH\n"
                    "--- VAR IMPACT ---\n"
                    "  VaR_95  $18.7M   (pre-breach: $9.2M)\n"
                    "  VaR_99  $28.1M   (pre-breach: $13.8M)\n"
                    "  stress_loss  $41.5M  scenario=2008-LEHMAN\n"
                    "kill_switch=ARMED  new_orders_blocked=true  liquidation_queue=PENDING\n"
                    "ACTION: block_new_orders=true  notify_desk_head=true  alert=RISK-LIMIT-BREACH"
                ),
            },
            5: {
                "name": "Margin Call Calculation Error",
                "subsystem": "risk_management",
                "vehicle_section": "margin_system",
                "error_type": "RISK-MARGIN-CALL",
                "sensor_type": "margin_calculator",
                "affected_services": ["risk-calculator", "settlement-processor"],
                "cascade_services": ["customer-portal", "compliance-monitor"],
                "description": "Margin requirement calculation fails due to stale collateral valuations",
                "error_message": "[RISK] RISK-MARGIN-CALL: account={account_id} margin_ratio={margin_ratio} maintenance_ratio={maintenance_ratio} valuation_age_s={valuation_age_s}",
                "stack_trace": (
                    "=== MARGIN SUMMARY ===\n"
                    "account={account_id}  margin_ratio={margin_ratio}  maintenance={maintenance_ratio}\n"
                    "--- COLLATERAL ---\n"
                    "  cash          $2,340,000    valued=CURRENT\n"
                    "  treasuries    $8,120,000    valued=STALE ({valuation_age_s}s)\n"
                    "  equities      $4,560,000    valued=STALE ({valuation_age_s}s)\n"
                    "  total_col     $15,020,000\n"
                    "--- REQUIREMENTS ---\n"
                    "  initial_margin    $18,450,000\n"
                    "  maintenance       $14,760,000\n"
                    "  current_equity    $12,180,000  <<< BELOW MAINTENANCE\n"
                    "  shortfall         $2,580,000\n"
                    "collateral_stale=true  valuation_age={valuation_age_s}s  max_staleness=300s\n"
                    "ACTION: issue_margin_call=true  liquidation_t+1=PENDING  alert=RISK-MARGIN-CALL"
                ),
            },
            6: {
                "name": "Position Reconciliation Failure",
                "subsystem": "risk_management",
                "vehicle_section": "position_keeper",
                "error_type": "RISK-POSITION-RECON",
                "sensor_type": "reconciliation",
                "affected_services": ["risk-calculator", "settlement-processor"],
                "cascade_services": ["audit-logger"],
                "description": "Position records diverge between real-time and end-of-day systems",
                "error_message": "[RISK] RISK-POSITION-RECON: instrument={instrument} realtime_qty={realtime_qty} eod_qty={eod_qty} delta={position_delta} account={account_id}",
                "stack_trace": (
                    "=== POSITION RECONCILIATION TABLE ===\n"
                    "account={account_id}  instrument={instrument}\n"
                    "SOURCE          QTY        AVG_PX      NOTIONAL\n"
                    "realtime        {realtime_qty}     $244.52     $12,430,100\n"
                    "eod_system      {eod_qty}     $244.50     $11,918,550\n"
                    "DELTA           {position_delta}                 $511,550\n"
                    "--- BREAK ANALYSIS ---\n"
                    "  missing_fills=7  late_cancels=2  amendment_lag=3\n"
                    "  last_match_rt=14:32:07.112  last_match_eod=14:31:54.890\n"
                    "  rt_source=OMS-REALTIME  eod_source=DTCC-NSCC-CNS\n"
                    "recon_status=BREAK  severity=MATERIAL  auto_resolve=false\n"
                    "ACTION: escalate_ops=true  block_settlement=true  alert=RISK-POSITION-RECON"
                ),
            },
            7: {
                "name": "Settlement Timeout",
                "subsystem": "settlement",
                "vehicle_section": "settlement_engine",
                "error_type": "SETTLE-T2-TIMEOUT",
                "sensor_type": "settlement_timer",
                "affected_services": ["settlement-processor", "audit-logger"],
                "cascade_services": ["risk-calculator", "compliance-monitor"],
                "description": "Trade settlement fails to complete within T+2 SLA window",
                "error_message": "[SETTLE] SETTLE-T2-TIMEOUT: trade={trade_id} settlement={settlement_id} pending_hours={pending_hours}h sla={sla_hours}h counterparty={counterparty}",
                "stack_trace": (
                    "=== SETTLEMENT LIFECYCLE ===\n"
                    "trade={trade_id}  settlement={settlement_id}  counterparty={counterparty}\n"
                    "PHASE               STATUS      TIMESTAMP\n"
                    "trade_capture       COMPLETE    2026-02-14T14:32:07Z\n"
                    "affirmation         COMPLETE    2026-02-14T15:01:22Z\n"
                    "netting             COMPLETE    2026-02-14T18:00:00Z\n"
                    "DTCC_submission     COMPLETE    2026-02-14T20:15:33Z\n"
                    "NSCC_CNS_match      PENDING     ---  <<< STALLED\n"
                    "DTC_delivery        WAITING     ---\n"
                    "funds_transfer      WAITING     ---\n"
                    "elapsed={pending_hours}h  sla={sla_hours}h  breach=true\n"
                    "depository=DTC  clearing=NSCC  method=DVP\n"
                    "ACTION: escalate_counterparty=true  reg_report=SEC-15c6  alert=SETTLE-T2-TIMEOUT"
                ),
            },
            8: {
                "name": "Failed Trade Settlement",
                "subsystem": "settlement",
                "vehicle_section": "settlement_engine",
                "error_type": "SETTLE-FAIL",
                "sensor_type": "settlement_status",
                "affected_services": ["settlement-processor", "risk-calculator"],
                "cascade_services": ["compliance-monitor", "audit-logger"],
                "description": "Trade settlement fails due to insufficient securities or funding",
                "error_message": "[SETTLE] SETTLE-FAIL: trade={trade_id} instrument={instrument} qty={quantity} reason={failure_reason} counterparty={counterparty}",
                "stack_trace": (
                    "=== SWIFT MT548 SETTLEMENT STATUS ===\n"
                    ":16R:GENL\n"
                    ":20C::SEME//{settlement_id}\n"
                    ":23G:INST\n"
                    ":16R:STAT\n"
                    ":25D::SETT//PEND\n"
                    ":24B::PEND//LACK  (reason={failure_reason})\n"
                    ":16S:STAT\n"
                    ":16R:SETTRAN\n"
                    ":35B:ISIN US0378331005  {instrument}\n"
                    ":36B::SETT//UNIT/{quantity}\n"
                    ":97A::SAFE//DTC-{counterparty}\n"
                    ":16S:SETTRAN\n"
                    ":16S:GENL\n"
                    "trade={trade_id}  fail_code=LACK  auto_borrow=ATTEMPTED  borrow_result=UNAVAILABLE\n"
                    "ACTION: recycle_instruction=true  notify_ops=true  alert=SETTLE-FAIL"
                ),
            },
            9: {
                "name": "Netting Calculation Error",
                "subsystem": "settlement",
                "vehicle_section": "netting_engine",
                "error_type": "SETTLE-NETTING-CALC",
                "sensor_type": "netting_integrity",
                "affected_services": ["settlement-processor", "risk-calculator"],
                "cascade_services": ["audit-logger", "compliance-monitor"],
                "description": "Multilateral netting calculation produces inconsistent net obligations",
                "error_message": "[SETTLE] SETTLE-NETTING-CALC: batch={batch_id} net_mismatch=${net_mismatch} counterparties={counterparty_count} currency={currency}",
                "stack_trace": (
                    "=== NETTING BATCH SUMMARY ===\n"
                    "batch={batch_id}  currency={currency}  counterparties={counterparty_count}\n"
                    "COUNTERPARTY          DELIVER        RECEIVE       NET\n"
                    "Goldman Sachs         $42,300,000    $38,100,000   ($4,200,000)\n"
                    "Morgan Stanley        $31,500,000    $35,800,000    $4,300,000\n"
                    "JP Morgan             $28,700,000    $27,200,000   ($1,500,000)\n"
                    "Citadel Securities    $19,400,000    $21,800,000    $2,400,000\n"
                    "--- BALANCE CHECK ---\n"
                    "  sum_delivers   $121,900,000\n"
                    "  sum_receives   $122,900,000\n"
                    "  mismatch       ${net_mismatch}  <<< NON-ZERO\n"
                    "  tolerance      $0.01\n"
                    "reduction_pct=72.4%  expected_reduction=75.0%  NSCC_CNS=REJECTED\n"
                    "ACTION: recompute_batch=true  hold_settlement=true  alert=SETTLE-NETTING-CALC"
                ),
            },
            10: {
                "name": "Fraud Detection False Positive Storm",
                "subsystem": "compliance",
                "vehicle_section": "fraud_engine",
                "error_type": "COMPL-FRAUD-FP-STORM",
                "sensor_type": "fraud_classifier",
                "affected_services": ["fraud-detector", "order-gateway"],
                "cascade_services": ["compliance-monitor", "customer-portal"],
                "description": "Fraud detection model generating excessive false positive alerts blocking legitimate orders",
                "error_message": "[COMPL] COMPL-FRAUD-FP-STORM: blocked={blocked_orders} window={window_s}s fp_rate={fp_rate}% pattern={pattern_id}",
                "stack_trace": (
                    "=== FRAUD DETECTION MODEL STATS ===\n"
                    "pattern={pattern_id}  window={window_s}s  model=v3.2.1\n"
                    "--- CLASSIFICATION MATRIX ---\n"
                    "                PREDICTED_FRAUD   PREDICTED_LEGIT\n"
                    "  ACTUAL_FRAUD       12               2\n"
                    "  ACTUAL_LEGIT      {blocked_orders}              4,210\n"
                    "--- RATES ---\n"
                    "  true_positive_rate   85.7%\n"
                    "  false_positive_rate  {fp_rate}%  <<< STORM THRESHOLD EXCEEDED\n"
                    "  precision            2.8%\n"
                    "  orders_blocked       {blocked_orders}\n"
                    "  revenue_impact       $1,247,000/hr\n"
                    "feature_drift=DETECTED  top_feature=txn_velocity_5m  drift_score=0.847\n"
                    "ACTION: raise_threshold=true  queue_manual_review=true  alert=COMPL-FRAUD-FP-STORM"
                ),
            },
            11: {
                "name": "Regulatory Report Generation Failure",
                "subsystem": "compliance",
                "vehicle_section": "reporting_engine",
                "error_type": "COMPL-REG-REPORT-FAIL",
                "sensor_type": "report_generator",
                "affected_services": ["compliance-monitor", "audit-logger"],
                "cascade_services": ["settlement-processor"],
                "description": "Mandatory regulatory report fails to generate before submission deadline",
                "error_message": "[COMPL] COMPL-REG-REPORT-FAIL: report={report_type} period={report_period} stage={stage} deadline={deadline_utc}",
                "stack_trace": (
                    "=== REG REPORT PIPELINE STATUS ===\n"
                    "report={report_type}  period={report_period}  deadline={deadline_utc}\n"
                    "STAGE               STATUS       RECORDS     ERRORS\n"
                    "data_collection     COMPLETE     1,247,832   0\n"
                    "validation          FAILED       1,247,832   3,412  <<< BLOCKED\n"
                    "aggregation         PENDING      ---         ---\n"
                    "formatting          PENDING      ---         ---\n"
                    "submission          PENDING      ---         ---\n"
                    "--- VALIDATION ERRORS ---\n"
                    "  missing_LEI=1,204  invalid_UTI=892  stale_price=1,316\n"
                    "  regulator=ESMA  schema=ISO20022  format=XML\n"
                    "failed_stage={stage}  retry_count=3  max_retries=3\n"
                    "ACTION: manual_remediation=true  regulator_extension=REQUESTED  alert=COMPL-REG-REPORT-FAIL"
                ),
            },
            12: {
                "name": "AML Screening Timeout",
                "subsystem": "compliance",
                "vehicle_section": "screening_engine",
                "error_type": "COMPL-AML-SCREENING",
                "sensor_type": "aml_screener",
                "affected_services": ["compliance-monitor", "fraud-detector"],
                "cascade_services": ["order-gateway", "customer-portal"],
                "description": "Anti-money laundering screening service exceeds response time SLA",
                "error_message": "[COMPL] COMPL-AML-SCREENING: transaction={transaction_id} screening_ms={screening_ms} sla_ms={aml_sla_ms} jurisdiction={jurisdiction}",
                "stack_trace": (
                    "=== AML SCREENING RESULTS ===\n"
                    "transaction={transaction_id}  jurisdiction={jurisdiction}\n"
                    "--- WATCHLIST CHECKS ---\n"
                    "  OFAC_SDN         checked=true   hits=0   elapsed=1,240ms\n"
                    "  EU_SANCTIONS     checked=true   hits=0   elapsed=2,100ms\n"
                    "  UN_CONSOLIDATED  checked=true   hits=0   elapsed=890ms\n"
                    "  PEP_DATABASE     checked=true   hits=1   elapsed=8,400ms  <<< SLOW\n"
                    "  ADVERSE_MEDIA    checked=false  hits=--  elapsed=TIMEOUT\n"
                    "total_screening_ms={screening_ms}  sla_ms={aml_sla_ms}  breach=true\n"
                    "pep_hit_score=0.72  pep_name_match='partial'  disposition=PENDING_REVIEW\n"
                    "ACTION: hold_transaction=true  escalate_mlro=true  alert=COMPL-AML-SCREENING"
                ),
            },
            13: {
                "name": "Customer Session Timeout",
                "subsystem": "client_services",
                "vehicle_section": "portal_gateway",
                "error_type": "PORTAL-SESSION-TIMEOUT",
                "sensor_type": "session_manager",
                "affected_services": ["customer-portal", "order-gateway"],
                "cascade_services": ["audit-logger"],
                "description": "Customer trading sessions expiring mid-transaction causing order failures",
                "error_message": "[PORTAL] PORTAL-SESSION-TIMEOUT: session={session_id} user={user_id} idle={session_age_s}s max=900s operation={operation}",
                "stack_trace": (
                    "=== SESSION DETAILS ===\n"
                    "session={session_id}  user={user_id}\n"
                    "  created=14:02:17Z  last_activity=14:17:42Z  idle={session_age_s}s  max=900s\n"
                    "  ip=10.2.0.47  user_agent=Bloomberg-Terminal/2026.1\n"
                    "  auth_method=SSO/SAML  mfa=TOTP\n"
                    "--- PENDING OPERATIONS ---\n"
                    "  operation={operation}  status=IN_PROGRESS\n"
                    "  pending_orders={pending_orders}\n"
                    "  unsaved_changes=true  last_heartbeat=892s_ago\n"
                    "--- IMPACT ---\n"
                    "  orders_cancelled_on_disconnect={pending_orders}\n"
                    "  portfolio_lock_released=true\n"
                    "ACTION: force_logout=true  cancel_pending=true  alert=PORTAL-SESSION-TIMEOUT"
                ),
            },
            14: {
                "name": "Portfolio Valuation Lag",
                "subsystem": "client_services",
                "vehicle_section": "valuation_engine",
                "error_type": "PORTAL-VALUATION-LAG",
                "sensor_type": "valuation_timer",
                "affected_services": ["customer-portal", "risk-calculator"],
                "cascade_services": ["compliance-monitor"],
                "description": "Real-time portfolio valuation falling behind, showing stale P&L to clients",
                "error_message": "[PORTAL] PORTAL-VALUATION-LAG: portfolio={portfolio_id} lag_s={lag_s} max_lag_s={max_lag_s} pending_positions={position_count}",
                "stack_trace": (
                    "=== PORTFOLIO VALUATION STATS ===\n"
                    "portfolio={portfolio_id}  positions={position_count}\n"
                    "--- VALUATION PIPELINE ---\n"
                    "  market_data_fetch   OK       12ms\n"
                    "  price_snap          OK       8ms\n"
                    "  fx_conversion       SLOW     4,200ms  <<< BOTTLENECK\n"
                    "  greeks_calc         QUEUED   ---\n"
                    "  pnl_attribution     QUEUED   ---\n"
                    "  total_lag           {lag_s}s  max={max_lag_s}s\n"
                    "--- POSITION BREAKDOWN ---\n"
                    "  equities=142  fixed_income=87  options=64  fx=29  futures=18\n"
                    "  stale_positions={position_count}  fresh_positions=0\n"
                    "displayed_pnl=STALE  client_visible=true  disclaimer_shown=false\n"
                    "ACTION: show_stale_banner=true  queue_priority_reval=true  alert=PORTAL-VALUATION-LAG"
                ),
            },
            15: {
                "name": "Trade Confirmation Delay",
                "subsystem": "client_services",
                "vehicle_section": "confirmation_service",
                "error_type": "PORTAL-CONFIRM-DELAY",
                "sensor_type": "confirmation_timer",
                "affected_services": ["customer-portal", "settlement-processor"],
                "cascade_services": ["audit-logger", "compliance-monitor"],
                "description": "Trade confirmation messages delayed beyond regulatory reporting window",
                "error_message": "[PORTAL] PORTAL-CONFIRM-DELAY: trade={trade_id} delay_s={delay_s} reg_max_s={reg_max_s} instrument={instrument} qty={quantity}",
                "stack_trace": (
                    "=== CONFIRMATION PIPELINE STATUS ===\n"
                    "trade={trade_id}  instrument={instrument}  qty={quantity}\n"
                    "STAGE                STATUS      ELAPSED\n"
                    "trade_capture        COMPLETE    0.2s\n"
                    "enrichment           COMPLETE    1.4s\n"
                    "template_render      COMPLETE    0.8s\n"
                    "compliance_check     COMPLETE    3.2s\n"
                    "delivery_queue       STUCK       {delay_s}s  <<< BACKLOG\n"
                    "client_ack           PENDING     ---\n"
                    "--- DELIVERY STATS ---\n"
                    "  queue_depth=4,217  consumers=2  consumer_lag=3,890\n"
                    "  format=FIX-Confirmation(AH)  protocol=SWIFT-MT515\n"
                    "  reg_window={reg_max_s}s  elapsed={delay_s}s  breach=true\n"
                    "ACTION: scale_consumers=true  reg_exception_report=true  alert=PORTAL-CONFIRM-DELAY"
                ),
            },
            16: {
                "name": "Matching Engine Latency",
                "subsystem": "trade_execution",
                "vehicle_section": "matching_core",
                "error_type": "ME-LATENCY-SLA",
                "sensor_type": "latency_monitor",
                "affected_services": ["matching-engine", "order-gateway"],
                "cascade_services": ["risk-calculator", "settlement-processor"],
                "description": "Matching engine order processing latency exceeds SLA threshold",
                "error_message": "[ME] ME-LATENCY-SLA: order={order_id} latency_us={latency_us} sla_us={sla_us} partition={partition_id}",
                "stack_trace": (
                    "=== MATCHING ENGINE PERF DUMP ===\n"
                    "order_id={order_id}  partition={partition_id}\n"
                    "phase              elapsed_us   pct\n"
                    "order_decode          12         0.1%\n"
                    "pre_trade_risk       340         2.7%\n"
                    "book_lookup           45         0.4%\n"
                    "price_time_match   11280        89.2%  <<< BOTTLENECK\n"
                    "fill_generation      310         2.5%\n"
                    "post_trade_pub       650         5.1%\n"
                    "TOTAL             {latency_us}us  SLA={sla_us}us  BREACH=true\n"
                    "queue_depth=14832  lock_contention_ns=8420  cpu_affinity=core-7\n"
                    "ACTION: throttle_inbound=true  alert=ME-LATENCY-SLA"
                ),
            },
            17: {
                "name": "Cross-Region Replication Lag",
                "subsystem": "audit",
                "vehicle_section": "replication_bus",
                "error_type": "AUDIT-REPLICATION-LAG",
                "sensor_type": "replication_monitor",
                "affected_services": ["audit-logger", "settlement-processor"],
                "cascade_services": ["compliance-monitor", "risk-calculator"],
                "description": "Cross-region audit log replication falling behind, DR site stale",
                "error_message": "[AUDIT] AUDIT-REPLICATION-LAG: source={source_region} dest={dest_region} lag_ms={lag_ms} max_ms={max_lag_ms} pending={pending_events}",
                "stack_trace": (
                    "=== REPLICATION STATUS REPORT ===\n"
                    "source={source_region}  dest={dest_region}\n"
                    "--- REPLICATION CHANNELS ---\n"
                    "  CHANNEL        LAG_MS    PENDING   STATUS\n"
                    "  orders         {lag_ms}     {pending_events}     BEHIND\n"
                    "  trades         12,400     892       BEHIND\n"
                    "  settlements    8,200      341       WARNING\n"
                    "  risk-events    {lag_ms}     {pending_events}     BEHIND\n"
                    "  compliance     3,100      127       OK\n"
                    "--- NETWORK ---\n"
                    "  bandwidth_mbps=840  utilization=94%  packet_loss=0.02%\n"
                    "  tcp_retransmits=247  rtt_ms=68\n"
                    "dr_site_staleness={lag_ms}ms  max_allowed={max_lag_ms}ms  rpo_breach=true\n"
                    "ACTION: increase_batch_size=true  failover_ready=false  alert=AUDIT-REPLICATION-LAG"
                ),
            },
            18: {
                "name": "Market Data Stale Quote",
                "subsystem": "market_data",
                "vehicle_section": "quote_cache",
                "error_type": "MDF-STALE-QUOTE",
                "sensor_type": "quote_freshness",
                "affected_services": ["market-data-feed", "risk-calculator"],
                "cascade_services": ["matching-engine", "customer-portal"],
                "description": "Cached market quotes exceeding staleness threshold affecting pricing",
                "error_message": "[MDF] MDF-STALE-QUOTE: symbol={symbol} stale_ms={stale_ms} max_age_ms={quote_max_age_ms} source={data_source}",
                "stack_trace": (
                    "=== QUOTE CACHE STATS ===\n"
                    "symbol={symbol}  source={data_source}\n"
                    "--- CACHE ENTRY ---\n"
                    "  last_bid=244.50  last_ask=244.55  last_trade=244.52\n"
                    "  update_ts=14:31:42.112  age_ms={stale_ms}  max_age_ms={quote_max_age_ms}\n"
                    "  cache_hits=14,230  cache_misses=0  evictions=0\n"
                    "--- FEED STATUS ---\n"
                    "  primary_feed={data_source}  status=CONNECTED  last_msg=14:31:42.112\n"
                    "  backup_feed=Reuters-Elektron  status=CONNECTED  last_msg=14:31:41.890\n"
                    "  failover_triggered=false\n"
                    "--- IMPACT ---\n"
                    "  dependent_books=4  stale_risk_calcs=12  client_views_affected=89\n"
                    "ACTION: mark_indicative=true  trigger_failover=PENDING  alert=MDF-STALE-QUOTE"
                ),
            },
            19: {
                "name": "FIX Protocol Parse Error",
                "subsystem": "order_management",
                "vehicle_section": "fix_gateway",
                "error_type": "FIX-PARSE-REJECT",
                "sensor_type": "protocol_parser",
                "affected_services": ["order-gateway", "audit-logger"],
                "cascade_services": ["matching-engine", "compliance-monitor"],
                "description": "FIX 4.4 message parsing failure due to malformed tags or checksum errors",
                "error_message": "[FIX] FIX-PARSE-REJECT: session={fix_session} msg_type={msg_type} tag={bad_tag} checksum_expected={expected_checksum} checksum_actual={actual_checksum}",
                "stack_trace": (
                    "=== RAW FIX MESSAGE DUMP ===\n"
                    "8=FIX.4.4|9=176|35={msg_type}|49=SENDER|56=TARGET|34=12847|\n"
                    "52=20260217-14:32:07.882|11=ORD-847291|55=AAPL|54=1|38=2500|\n"
                    "44=244.52|40=2|59=0|{bad_tag}=<<<MALFORMED>>>|\n"
                    "10={actual_checksum}|\n"
                    "--- PARSE ANALYSIS ---\n"
                    "  session={fix_session}  msg_type={msg_type}  direction=INBOUND\n"
                    "  tag_{bad_tag}  status=INVALID  reason=unexpected_value_format\n"
                    "  checksum  expected={expected_checksum}  actual={actual_checksum}  match=false\n"
                    "  body_length=176  computed_length=174  length_match=false\n"
                    "--- SESSION STATS ---\n"
                    "  msgs_today=124,832  parse_errors=47  reject_rate=0.038%\n"
                    "  last_good_seq=12846  gap_detected=false\n"
                    "ACTION: send_reject(35=3)  increment_error_count=true  alert=FIX-PARSE-REJECT"
                ),
            },
            20: {
                "name": "Dark Pool Routing Failure",
                "subsystem": "trade_execution",
                "vehicle_section": "smart_router",
                "error_type": "ME-DARKPOOL-REJECT",
                "sensor_type": "routing_engine",
                "affected_services": ["matching-engine", "order-gateway"],
                "cascade_services": ["risk-calculator", "audit-logger", "compliance-monitor"],
                "description": "Smart order router fails to route block orders to dark pool venues",
                "error_message": "[ME] ME-DARKPOOL-REJECT: order={order_id} symbol={symbol} qty={quantity} venue={venue} reason={rejection_reason}",
                "stack_trace": (
                    "=== DARK POOL REJECTION DETAILS ===\n"
                    "order={order_id}  symbol={symbol}  qty={quantity}\n"
                    "--- ROUTING ATTEMPT ---\n"
                    "  venue={venue}  protocol=FIX-4.4  order_type=IOI\n"
                    "  min_size=10,000  submitted_qty={quantity}\n"
                    "  rejection_reason={rejection_reason}\n"
                    "--- VENUE SCORECARD ---\n"
                    "  VENUE            FILL_RATE   AVG_SIZE    STATUS\n"
                    "  SIGMA-X          67.2%       45,000      AVAILABLE\n"
                    "  CROSSFINDER      72.1%       38,000      AVAILABLE\n"
                    "  SUPERX           58.4%       52,000      RESTRICTED\n"
                    "  LIQUIDNET        81.3%       120,000     AVAILABLE\n"
                    "--- FALLBACK ---\n"
                    "  next_venue=CROSSFINDER  algo=TWAP-4h  urgency=LOW\n"
                    "  lit_market_impact_est=12bps\n"
                    "ACTION: try_next_venue=true  update_venue_score=true  alert=ME-DARKPOOL-REJECT"
                ),
            },
        }

    # ── Topology ──────────────────────────────────────────────────────

    @property
    def service_topology(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "order-gateway": [
                ("matching-engine", "/api/v1/orders/submit", "POST"),
                ("matching-engine", "/api/v1/orders/cancel", "DELETE"),
                ("risk-calculator", "/api/v1/risk/pre-trade-check", "POST"),
                ("fraud-detector", "/api/v1/fraud/screen-order", "POST"),
                ("audit-logger", "/api/v1/audit/log-order", "POST"),
            ],
            "matching-engine": [
                ("risk-calculator", "/api/v1/risk/position-update", "POST"),
                ("settlement-processor", "/api/v1/settlement/initiate", "POST"),
                ("market-data-feed", "/api/v1/market/last-price", "GET"),
            ],
            "risk-calculator": [
                ("market-data-feed", "/api/v1/market/quotes", "GET"),
                ("settlement-processor", "/api/v1/settlement/margin-status", "GET"),
            ],
            "settlement-processor": [
                ("audit-logger", "/api/v1/audit/log-settlement", "POST"),
                ("compliance-monitor", "/api/v1/compliance/settlement-report", "POST"),
            ],
            "customer-portal": [
                ("order-gateway", "/api/v1/orders/place", "POST"),
                ("risk-calculator", "/api/v1/risk/portfolio-exposure", "GET"),
                ("market-data-feed", "/api/v1/market/stream", "GET"),
            ],
            "compliance-monitor": [
                ("audit-logger", "/api/v1/audit/compliance-event", "POST"),
                ("fraud-detector", "/api/v1/fraud/alert-status", "GET"),
            ],
        }

    @property
    def entry_endpoints(self) -> dict[str, list[tuple[str, str]]]:
        return {
            "order-gateway": [
                ("/api/v1/orders/new", "POST"),
                ("/api/v1/orders/status", "GET"),
                ("/api/v1/orders/amend", "PUT"),
            ],
            "matching-engine": [("/api/v1/engine/health", "GET")],
            "risk-calculator": [
                ("/api/v1/risk/evaluate", "POST"),
                ("/api/v1/risk/limits", "GET"),
            ],
            "market-data-feed": [
                ("/api/v1/market/subscribe", "POST"),
                ("/api/v1/market/snapshot", "GET"),
            ],
            "settlement-processor": [("/api/v1/settlement/status", "GET")],
            "fraud-detector": [("/api/v1/fraud/analyze", "POST")],
            "compliance-monitor": [
                ("/api/v1/compliance/report", "GET"),
                ("/api/v1/compliance/alerts", "GET"),
            ],
            "customer-portal": [
                ("/api/v1/portfolio/overview", "GET"),
                ("/api/v1/portfolio/positions", "GET"),
                ("/api/v1/portfolio/pnl", "GET"),
            ],
            "audit-logger": [("/api/v1/audit/query", "POST")],
        }

    @property
    def db_operations(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "order-gateway": [
                ("INSERT", "orders", "INSERT INTO orders (order_id, instrument, side, qty, price, status, ts) VALUES (?, ?, ?, ?, ?, 'NEW', NOW())"),
                ("SELECT", "orders", "SELECT order_id, status, filled_qty FROM orders WHERE account_id = ? AND status IN ('NEW', 'PARTIAL') ORDER BY ts DESC LIMIT 50"),
            ],
            "matching-engine": [
                ("UPDATE", "order_book", "UPDATE order_book SET best_bid = ?, best_ask = ?, last_match_ts = NOW() WHERE instrument = ?"),
                ("INSERT", "trades", "INSERT INTO trades (trade_id, instrument, buy_order, sell_order, qty, price, ts) VALUES (?, ?, ?, ?, ?, ?, NOW())"),
            ],
            "risk-calculator": [
                ("SELECT", "positions", "SELECT instrument, net_qty, avg_price, unrealized_pnl FROM positions WHERE desk_id = ? AND asset_class = ?"),
                ("UPDATE", "risk_limits", "UPDATE risk_limits SET current_exposure = ?, last_checked = NOW() WHERE desk_id = ? AND limit_type = ?"),
            ],
            "settlement-processor": [
                ("SELECT", "settlements", "SELECT settlement_id, trade_id, status, due_date FROM settlements WHERE status = 'PENDING' AND due_date < NOW() + INTERVAL 1 DAY"),
                ("UPDATE", "settlements", "UPDATE settlements SET status = ?, settled_at = NOW() WHERE settlement_id = ?"),
            ],
            "audit-logger": [
                ("INSERT", "audit_events", "INSERT INTO audit_events (event_id, event_type, actor, payload, seq_num, ts) VALUES (?, ?, ?, ?, ?, NOW())"),
                ("SELECT", "audit_events", "SELECT event_id, event_type, payload FROM audit_events WHERE stream_id = ? AND seq_num > ? ORDER BY seq_num ASC LIMIT 100"),
            ],
        }

    # ── Infrastructure ────────────────────────────────────────────────

    @property
    def hosts(self) -> list[dict[str, Any]]:
        return [
            {
                "host.name": "finserv-aws-host-01",
                "host.id": "i-0f1a2b3c4d5e67890",
                "host.arch": "amd64",
                "host.type": "c5.2xlarge",
                "host.image.id": "ami-0fedcba9876543210",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8275CL CPU @ 3.00GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "7",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.0.2.50", "172.16.1.10"],
                "host.mac": ["0a:2b:3c:4d:5e:6f", "0a:2b:3c:4d:5e:70"],
                "os.type": "linux",
                "os.description": "Amazon Linux 2023.6.20250115",
                "cloud.provider": "aws",
                "cloud.platform": "aws_ec2",
                "cloud.region": "us-east-1",
                "cloud.availability_zone": "us-east-1a",
                "cloud.account.id": "987654321098",
                "cloud.instance.id": "i-0f1a2b3c4d5e67890",
                "cpu_count": 8,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 500 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "finserv-gcp-host-01",
                "host.id": "7823456789012345678",
                "host.arch": "amd64",
                "host.type": "c2-standard-8",
                "host.image.id": "projects/debian-cloud/global/images/debian-12-bookworm-v20250115",
                "host.cpu.model.name": "Intel(R) Xeon(R) CPU @ 3.10GHz",
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
                "cloud.account.id": "finserv-trading-prod",
                "cloud.instance.id": "7823456789012345678",
                "cpu_count": 8,
                "memory_total_bytes": 32 * 1024 * 1024 * 1024,
                "disk_total_bytes": 200 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "finserv-azure-host-01",
                "host.id": "/subscriptions/def-456/resourceGroups/finserv-rg/providers/Microsoft.Compute/virtualMachines/finserv-vm-01",
                "host.arch": "amd64",
                "host.type": "Standard_F8s_v2",
                "host.image.id": "Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "106",
                "host.cpu.stepping": "6",
                "host.cpu.cache.l2.size": 1310720,
                "host.ip": ["10.2.0.10", "10.2.0.11"],
                "host.mac": ["00:0d:3a:6b:5c:4d", "00:0d:3a:6b:5c:4e"],
                "os.type": "linux",
                "os.description": "Ubuntu 22.04.5 LTS",
                "cloud.provider": "azure",
                "cloud.platform": "azure_vm",
                "cloud.region": "eastus",
                "cloud.availability_zone": "eastus-1",
                "cloud.account.id": "def-456-ghi-789",
                "cloud.instance.id": "finserv-vm-01",
                "cpu_count": 8,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 256 * 1024 * 1024 * 1024,
            },
        ]

    @property
    def k8s_clusters(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "finserv-eks-cluster",
                "provider": "aws",
                "platform": "aws_eks",
                "region": "us-east-1",
                "zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
                "os_description": "Amazon Linux 2",
                "services": ["order-gateway", "matching-engine", "risk-calculator"],
            },
            {
                "name": "finserv-gke-cluster",
                "provider": "gcp",
                "platform": "gcp_gke",
                "region": "us-central1",
                "zones": ["us-central1-a", "us-central1-b", "us-central1-c"],
                "os_description": "Container-Optimized OS",
                "services": ["market-data-feed", "settlement-processor", "fraud-detector"],
            },
            {
                "name": "finserv-aks-cluster",
                "provider": "azure",
                "platform": "azure_aks",
                "region": "eastus",
                "zones": ["eastus-1", "eastus-2", "eastus-3"],
                "os_description": "Ubuntu 22.04 LTS",
                "services": ["compliance-monitor", "customer-portal", "audit-logger"],
            },
        ]

    # ── Theme ─────────────────────────────────────────────────────────

    @property
    def theme(self) -> UITheme:
        return UITheme(
            bg_primary="#0a1628",
            bg_secondary="#0f1d32",
            bg_tertiary="#162240",
            accent_primary="#ffa500",
            accent_secondary="#ff6600",
            text_primary="#ff8c00",
            text_secondary="#cc7000",
            text_accent="#ffa500",
            status_nominal="#00ff00",
            status_warning="#ffa500",
            status_critical="#ff0000",
            font_family="'Bloomberg Terminal', 'Consolas', monospace",
            font_mono="'Bloomberg Terminal', 'Consolas', monospace",
            chaos_title="Market Disruption Simulator",
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
            "id": "finserv-trading-analyst",
            "name": "Trading Operations Analyst",
            "assessment_tool_name": "trading_risk_assessment",
            "system_prompt": (
                "You are the Trading Operations Analyst, an expert AI assistant for "
                "financial trading platform operations. You help trading desk operators "
                "investigate incidents, analyze order flow, and provide root cause analysis "
                "for fault conditions across 9 trading infrastructure services spanning "
                "AWS, GCP, and Azure. "
                "You have deep expertise in FIX 4.4 protocol, order management systems, "
                "matching engine internals, risk limit frameworks (VaR, margin), "
                "T+2 settlement, DTCC/NSCC clearing, regulatory reporting (EMIR, MiFID II, CAT), "
                "AML/KYC screening, and cross-region audit replication. "
                "When investigating incidents, search for these system identifiers in logs: "
                "Order Management faults (OMS-BOOK-IMBALANCE, FIX-PARSE-REJECT), "
                "Matching Engine faults (ME-LATENCY-SLA, ME-DARKPOOL-REJECT), "
                "Market Data faults (MDF-PRICE-GAP, MDF-STALE-QUOTE), "
                "Risk faults (RISK-LIMIT-BREACH, RISK-MARGIN-CALL, RISK-POSITION-RECON), "
                "Settlement faults (SETTLE-T2-TIMEOUT, SETTLE-FAIL, SETTLE-NETTING-CALC), "
                "Compliance faults (COMPL-FRAUD-FP-STORM, COMPL-REG-REPORT-FAIL, COMPL-AML-SCREENING), "
                "Portal faults (PORTAL-SESSION-TIMEOUT, PORTAL-VALUATION-LAG, PORTAL-CONFIRM-DELAY), "
                "and Audit faults (AUDIT-SEQ-GAP, AUDIT-REPLICATION-LAG). "
                "Log messages are in body.text — NEVER search the body field alone."
            ),
        }

    @property
    def assessment_tool_config(self) -> dict[str, Any]:
        return {
            "id": "trading_risk_assessment",
            "description": (
                "Comprehensive pre-market trading risk assessment. Evaluates all "
                "services against operational readiness criteria for trading sessions. "
                "Returns data for risk evaluation across order management, matching "
                "engine, settlement, and compliance systems. "
                "Log message field: body.text (never use 'body' alone)."
            ),
        }

    @property
    def knowledge_base_docs(self) -> list[dict[str, Any]]:
        return []  # Populated by deployer from channel_registry

    # ── Service Classes ───────────────────────────────────────────────

    def get_service_classes(self) -> list[type]:
        from scenarios.financial.services.order_gateway import OrderGatewayService
        from scenarios.financial.services.matching_engine import MatchingEngineService
        from scenarios.financial.services.risk_calculator import RiskCalculatorService
        from scenarios.financial.services.market_data_feed import MarketDataFeedService
        from scenarios.financial.services.settlement_processor import SettlementProcessorService
        from scenarios.financial.services.fraud_detector import FraudDetectorService
        from scenarios.financial.services.compliance_monitor import ComplianceMonitorService
        from scenarios.financial.services.customer_portal import CustomerPortalService
        from scenarios.financial.services.audit_logger import AuditLoggerService

        return [
            OrderGatewayService,
            MatchingEngineService,
            RiskCalculatorService,
            MarketDataFeedService,
            SettlementProcessorService,
            FraudDetectorService,
            ComplianceMonitorService,
            CustomerPortalService,
            AuditLoggerService,
        ]

    # ── Fault Parameters ──────────────────────────────────────────────

    def get_fault_params(self, channel: int) -> dict[str, Any]:
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "JPM", "GS", "MS", "BAC", "C"]
        instruments = ["US.AAPL", "US.GOOGL", "US.MSFT", "US.AMZN", "US.TSLA", "FX.EURUSD", "FX.GBPUSD", "FUT.ES", "FUT.NQ", "OPT.SPX"]
        exchanges = ["NYSE", "NASDAQ", "CBOE", "CME", "ICE", "BATS", "IEX"]
        venues = ["SIGMA-X", "CROSSFINDER", "SUPERX", "POSIT", "LIQUIDNET", "INSTINET"]
        counterparties = ["Goldman Sachs", "Morgan Stanley", "JP Morgan", "Citadel Securities", "Virtu Financial", "Jane Street"]
        currencies = ["USD", "EUR", "GBP", "JPY", "CHF"]
        asset_classes = ["equity", "fixed_income", "fx", "derivatives", "commodities"]
        jurisdictions = ["US-SEC", "US-CFTC", "UK-FCA", "EU-ESMA", "SG-MAS", "JP-FSA"]
        report_types = ["EMIR-TR", "MiFID-II-RTS25", "CAT-FINRA", "SFTR", "SEC-13F", "TRF-TRACE"]
        failure_reasons = ["insufficient_securities", "funding_shortfall", "counterparty_default", "DTCC_rejection", "SSI_mismatch"]
        rejection_reasons = ["minimum_size_not_met", "price_outside_band", "venue_capacity", "symbol_restricted", "IOI_expired"]

        return {
            # Order/trade identifiers
            "order_id": f"ORD-{random.randint(100000, 999999)}",
            "trade_id": f"TRD-{random.randint(100000, 999999)}",
            "settlement_id": f"STL-{random.randint(100000, 999999)}",
            "batch_id": f"NET-{random.randint(1000, 9999)}",
            "transaction_id": f"TXN-{random.randint(100000, 999999)}",
            "book_id": f"BOOK-{random.choice(['EQ', 'FI', 'FX', 'DRV'])}-{random.randint(1, 50):02d}",
            # Instruments and symbols
            "symbol": random.choice(symbols),
            "instrument": random.choice(instruments),
            "exchange": random.choice(exchanges),
            "venue": random.choice(venues),
            # Pricing and quantity
            "price": round(random.uniform(50.0, 500.0), 2),
            "quantity": random.randint(100, 50000),
            "spread": random.randint(5, 50),
            "max_spread": 3,
            # Latency (microseconds for HFT)
            "latency_us": random.randint(500, 50000),
            "sla_us": 200,
            "partition_id": f"P-{random.randint(0, 15)}",
            # Market data
            "gap_ms": random.randint(500, 10000),
            "seq_start": random.randint(1000000, 9999999),
            "seq_end": random.randint(1000000, 9999999),
            "stale_ms": random.randint(5000, 60000),
            "quote_max_age_ms": 3000,
            "data_source": random.choice(["Bloomberg-B-PIPE", "Reuters-Elektron", "CQS-SIP", "OPRA", "CME-MDP3"]),
            # Risk parameters
            "desk_id": f"DESK-{random.choice(['EQ-FLOW', 'EQ-PROP', 'FI-RATES', 'FX-SPOT', 'DRV-VOL'])}",
            "exposure": f"{random.randint(10, 500)}M",
            "risk_limit": f"{random.randint(5, 100)}M",
            "asset_class": random.choice(asset_classes),
            # Margin
            "account_id": f"ACC-{random.randint(10000, 99999)}",
            "margin_ratio": round(random.uniform(0.05, 0.20), 3),
            "maintenance_ratio": 0.25,
            "valuation_age_s": random.randint(300, 3600),
            # Position reconciliation
            "realtime_qty": random.randint(1000, 100000),
            "eod_qty": random.randint(1000, 100000),
            "position_delta": random.randint(1, 5000),
            # Settlement
            "counterparty": random.choice(counterparties),
            "pending_hours": round(random.uniform(48.5, 96.0), 1),
            "sla_hours": 48,
            "failure_reason": random.choice(failure_reasons),
            "currency": random.choice(currencies),
            "net_mismatch": round(random.uniform(10000, 5000000), 2),
            "counterparty_count": random.randint(3, 20),
            # Compliance / fraud
            "blocked_orders": random.randint(50, 500),
            "window_s": random.randint(30, 300),
            "fp_rate": round(random.uniform(15.0, 85.0), 1),
            "pattern_id": f"FRD-{random.choice(['VELOCITY', 'GEOLOC', 'AMOUNT', 'PATTERN', 'WASH'])}-{random.randint(1, 99):02d}",
            "report_type": random.choice(report_types),
            "report_period": f"2026-Q{random.randint(1, 4)}",
            "stage": random.choice(["data_collection", "validation", "aggregation", "formatting", "submission"]),
            "deadline_utc": "2026-02-16T23:59:00Z",
            "screening_ms": random.randint(5000, 30000),
            "aml_sla_ms": 3000,
            "jurisdiction": random.choice(jurisdictions),
            # Client services
            "session_id": f"SESS-{random.randint(100000, 999999)}",
            "user_id": f"USR-{random.randint(10000, 99999)}",
            "session_age_s": random.randint(1800, 7200),
            "operation": random.choice(["order_submit", "portfolio_view", "position_close", "margin_check"]),
            "pending_orders": random.randint(1, 10),
            "portfolio_id": f"PF-{random.randint(10000, 99999)}",
            "lag_s": round(random.uniform(30.0, 300.0), 1),
            "max_lag_s": 15.0,
            "position_count": random.randint(50, 500),
            "delay_s": round(random.uniform(600, 7200), 1),
            "reg_max_s": 300,
            # Audit
            "audit_stream": random.choice(["orders", "trades", "settlements", "risk-events", "compliance-alerts"]),
            "expected_seq": random.randint(1000000, 9999999),
            "last_seq": random.randint(1000000, 9999999),
            "gap_count": random.randint(1, 100),
            # Replication
            "source_region": random.choice(["us-east-1", "us-central1", "eastus"]),
            "dest_region": random.choice(["eu-west-1", "us-west-2", "westus"]),
            "lag_ms": random.randint(5000, 60000),
            "max_lag_ms": 3000,
            "pending_events": random.randint(100, 10000),
            # FIX protocol
            "fix_session": f"FIX-{random.choice(['NYSE', 'NSDQ', 'CBOE', 'CME'])}-{random.randint(1, 20):02d}",
            "msg_type": random.choice(["D", "G", "F", "8", "9"]),
            "bad_tag": random.choice([35, 49, 56, 11, 55, 44, 38, 54, 40]),
            "expected_checksum": f"{random.randint(0, 255):03d}",
            "actual_checksum": f"{random.randint(0, 255):03d}",
            # Dark pool
            "rejection_reason": random.choice(rejection_reasons),
        }


# Module-level instance for registry discovery
scenario = FinancialScenario()

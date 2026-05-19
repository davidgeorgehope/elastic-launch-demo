"""Synthetic `business.*` OTLP gauges for the Banking Executive Dashboard."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.base_service import BaseService


def emit_executive_business_metrics_if_eligible(service: "BaseService") -> None:
    """Emit retail banking leadership KPI gauges once per telemetry cycle from the designated service."""
    ctx = getattr(service, "_ctx", None)
    if not ctx:
        return
    want = getattr(ctx.scenario, "executive_kpi_emitter_service_name", None)
    if not want or want != service.SERVICE_NAME:
        return

    emit = service.emit_metric

    # Revenue & margins
    emit("business.net_interest_income_usd_per_min", round(random.uniform(180_000.0, 850_000.0), 1), "USD/min")
    emit("business.fee_revenue_usd_per_min", round(random.uniform(12_000.0, 95_000.0), 1), "USD/min")
    emit("business.loan_origination_usd_per_min", round(random.uniform(280_000.0, 2_100_000.0), 1), "USD/min")
    emit("business.card_interchange_usd_per_min", round(random.uniform(8_000.0, 72_000.0), 1), "USD/min")
    emit("business.wealth_aum_delta_usd_per_min", round(random.uniform(-45_000.0, 180_000.0), 1), "USD/min")
    emit("business.deposit_growth_usd_per_min", round(random.uniform(25_000.0, 320_000.0), 1), "USD/min")

    # Digital adoption
    emit("business.active_digital_sessions", float(random.randint(12_000, 180_000)), "sessions")
    emit("business.mobile_logins_per_min", float(random.randint(400, 8_500)), "logins/min")
    emit("business.digital_transaction_pct", round(random.uniform(62.0, 94.0), 2), "%")
    emit("business.self_service_deflection_pct", round(random.uniform(45.0, 88.0), 2), "%")
    emit("business.app_session_duration_sec", round(random.uniform(95.0, 420.0), 1), "s")
    emit("business.api_calls_per_min", float(random.randint(22_000, 380_000)), "calls/min")

    # Risk & compliance
    emit("business.fraud_detection_rate_pct", round(random.uniform(0.02, 0.85), 3), "%")
    emit("business.suspicious_activity_alerts_per_min", round(random.uniform(0.1, 3.8), 2), "alerts/min")
    emit("business.aml_flags_per_min", round(random.uniform(0.05, 1.2), 3), "flags/min")
    emit("business.failed_auth_attempts_per_min", float(random.randint(12, 280)), "attempts/min")
    emit("business.chargeback_rate_pct", round(random.uniform(0.04, 0.38), 3), "%")
    emit("business.regulatory_breach_count", float(random.randint(0, 2)), "count")

    # Customer health
    emit("business.net_satisfaction_proxy_nps", round(random.uniform(22.0, 68.0), 1), "score")
    emit("business.account_openings_per_min", round(random.uniform(0.8, 12.0), 2), "openings/min")
    emit("business.account_closures_per_min", round(random.uniform(0.1, 2.8), 2), "closures/min")
    emit("business.churn_risk_index_0_100", round(random.uniform(8.0, 35.0), 1), "index")
    emit("business.complaint_tickets_per_min", round(random.uniform(0.2, 4.5), 2), "tickets/min")
    emit("business.csat_score_0_5", round(random.uniform(3.2, 4.8), 2), "score")

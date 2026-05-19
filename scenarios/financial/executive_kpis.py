"""Synthetic `business.*` OTLP gauges for the Financial Trading Executive Dashboard."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.base_service import BaseService


def emit_executive_business_metrics_if_eligible(service: "BaseService") -> None:
    """Emit financial trading leadership KPI gauges once per telemetry cycle from the designated service."""
    ctx = getattr(service, "_ctx", None)
    if not ctx:
        return
    want = getattr(ctx.scenario, "executive_kpi_emitter_service_name", None)
    if not want or want != service.SERVICE_NAME:
        return

    emit = service.emit_metric

    # Trade flow
    emit("business.order_flow_per_min", float(random.randint(850, 28_000)), "orders/min")
    emit("business.fill_rate_pct", round(random.uniform(89.0, 99.6), 2), "%")
    emit("business.notional_value_usd_per_min", round(random.uniform(2_800_000.0, 48_000_000.0), 1), "USD/min")
    emit("business.executed_trades_per_min", float(random.randint(620, 18_000)), "trades/min")
    emit("business.rejected_orders_per_min", float(random.randint(2, 85)), "orders/min")
    emit("business.cancel_replace_rate_pct", round(random.uniform(3.2, 18.4), 2), "%")

    # Risk exposure
    emit("business.portfolio_var_usd", round(random.uniform(180_000.0, 2_400_000.0), 1), "USD")
    emit("business.margin_utilization_pct", round(random.uniform(42.0, 88.0), 2), "%")
    emit("business.position_limit_breaches", float(random.randint(0, 8)), "count")
    emit("business.delta_exposure_usd", round(random.uniform(-850_000.0, 2_100_000.0), 1), "USD")
    emit("business.counterparty_credit_risk_usd", round(random.uniform(280_000.0, 4_800_000.0), 1), "USD")
    emit("business.mark_to_market_pnl_usd_per_min", round(random.uniform(-120_000.0, 380_000.0), 1), "USD/min")

    # Market quality
    emit("business.avg_spread_bps", round(random.uniform(0.8, 12.4), 2), "bps")
    emit("business.market_impact_bps", round(random.uniform(0.2, 4.8), 2), "bps")
    emit("business.slippage_cost_usd_per_min", round(random.uniform(850.0, 12_000.0), 1), "USD/min")
    emit("business.latency_sla_breach_rate_pct", round(random.uniform(0.01, 0.85), 3), "%")
    emit("business.best_execution_pct", round(random.uniform(92.0, 99.8), 2), "%")
    emit("business.venue_fill_quality_pct", round(random.uniform(88.0, 98.4), 2), "%")

    # Operations
    emit("business.settlement_success_rate_pct", round(random.uniform(97.2, 99.98), 3), "%")
    emit("business.settlement_fails_in_queue", float(random.randint(0, 28)), "count")
    emit("business.reconciliation_breaks", float(random.randint(0, 12)), "count")
    emit("business.ops_alerts_per_min", round(random.uniform(0.2, 4.8), 2), "alerts/min")
    emit("business.system_availability_pct", round(random.uniform(99.2, 99.99), 3), "%")
    emit("business.reporting_latency_sec", round(random.uniform(0.8, 12.4), 2), "s")

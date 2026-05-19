"""Synthetic `business.*` OTLP gauges for the Ecommerce Executive Dashboard."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.base_service import BaseService


def emit_executive_business_metrics_if_eligible(service: "BaseService") -> None:
    """Emit global commerce leadership KPI gauges once per telemetry cycle from the designated service."""
    ctx = getattr(service, "_ctx", None)
    if not ctx:
        return
    want = getattr(ctx.scenario, "executive_kpi_emitter_service_name", None)
    if not want or want != service.SERVICE_NAME:
        return

    emit = service.emit_metric

    # Revenue
    emit("business.gmv_usd_per_min", round(random.uniform(85_000.0, 680_000.0), 1), "USD/min")
    emit("business.conversion_rate_pct", round(random.uniform(1.8, 6.4), 2), "%")
    emit("business.average_order_value_usd", round(random.uniform(42.0, 195.0), 2), "USD")
    emit("business.ad_revenue_usd_per_min", round(random.uniform(28_000.0, 185_000.0), 1), "USD/min")
    emit("business.subscription_mrr_usd_per_min", round(random.uniform(12_000.0, 95_000.0), 1), "USD/min")
    emit("business.seller_fee_revenue_usd_per_min", round(random.uniform(4_500.0, 38_000.0), 1), "USD/min")

    # Traffic & engagement
    emit("business.sessions_per_min", float(random.randint(1_200, 18_000)), "sessions/min")
    emit("business.page_views_per_min", float(random.randint(8_500, 95_000)), "views/min")
    emit("business.cart_adds_per_min", float(random.randint(380, 4_800)), "adds/min")
    emit("business.search_queries_per_min", float(random.randint(620, 8_200)), "queries/min")
    emit("business.content_completion_rate_pct", round(random.uniform(38.0, 82.0), 2), "%")
    emit("business.return_visitor_pct", round(random.uniform(28.0, 56.0), 2), "%")

    # Fulfillment
    emit("business.orders_placed_per_min", float(random.randint(85, 980)), "orders/min")
    emit("business.fulfillment_sla_pct", round(random.uniform(91.0, 99.4), 2), "%")
    emit("business.returns_per_min", float(random.randint(8, 120)), "returns/min")
    emit("business.cancel_rate_pct", round(random.uniform(1.2, 5.8), 2), "%")
    emit("business.same_day_eligible_pct", round(random.uniform(22.0, 68.0), 2), "%")
    emit("business.inventory_turn_rate", round(random.uniform(4.2, 18.6), 2), "turns")

    # Customer health
    emit("business.csat_score_0_5", round(random.uniform(3.4, 4.9), 2), "score")
    emit("business.net_satisfaction_proxy_nps", round(random.uniform(18.0, 72.0), 1), "score")
    emit("business.churn_risk_index_0_100", round(random.uniform(12.0, 48.0), 1), "index")
    emit("business.email_open_rate_pct", round(random.uniform(14.0, 38.0), 2), "%")
    emit("business.push_notification_ctr_pct", round(random.uniform(1.8, 9.4), 2), "%")
    emit("business.loyalty_points_redeemed_per_min", float(random.randint(12_000, 180_000)), "pts/min")

"""Synthetic `business.*` OTLP gauges for the Fanatics Executive Dashboard."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.base_service import BaseService


def emit_executive_business_metrics_if_eligible(service: "BaseService") -> None:
    """Emit Fanatics leadership KPI gauges once per telemetry cycle from the designated service."""
    ctx = getattr(service, "_ctx", None)
    if not ctx:
        return
    want = getattr(ctx.scenario, "executive_kpi_emitter_service_name", None)
    if not want or want != service.SERVICE_NAME:
        return

    emit = service.emit_metric

    # Monetization & wagering
    emit("business.ad_revenue_usd_per_min", round(random.uniform(85_000.0, 520_000.0), 1), "USD/min")
    emit("business.programmatic_fill_rate_pct", round(random.uniform(82.0, 98.4), 2), "%")
    emit("business.betting_handle_usd_per_min", round(random.uniform(180_000.0, 2_200_000.0), 1), "USD/min")
    emit("business.betting_hold_pct", round(random.uniform(6.5, 14.2), 2), "%")
    emit("business.betting_gross_win_usd_per_min", round(random.uniform(12_000.0, 210_000.0), 1), "USD/min")
    emit("business.subscription_mrr_usd_per_min", round(random.uniform(18_000.0, 185_000.0), 1), "USD/min")

    # Audience & engagement
    emit("business.live_concurrent_viewers", float(random.randint(78_000, 520_000)), "viewers")
    emit("business.video_minutes_engaged_per_min", round(random.uniform(120_000.0, 980_000.0), 1), "min/min")
    emit("business.page_views_per_min", float(random.randint(180_000, 2_400_000)), "views/min")
    emit("business.app_sessions_per_min", float(random.randint(900, 12_000)), "sessions/min")
    emit("business.content_completion_rate_pct", round(random.uniform(38.0, 82.0), 2), "%")
    emit("business.fantasy_active_entries", float(random.randint(9_000, 220_000)), "entries")

    # Commerce & partners
    emit("business.merch_gmv_usd_per_min", round(random.uniform(28_000.0, 310_000.0), 1), "USD/min")
    emit("business.live_event_ticketing_usd_per_min", round(random.uniform(4_500.0, 98_000.0), 1), "USD/min")
    emit("business.partner_sponsorship_usd_per_min", round(random.uniform(15_000.0, 195_000.0), 1), "USD/min")
    emit("business.api_data_partner_revenue_usd_per_min", round(random.uniform(6_000.0, 72_000.0), 1), "USD/min")
    emit("business.sponsored_inventory_seconds_per_min", float(random.randint(400, 12_000)), "s/min")
    emit("business.premium_tier_arpu_usd", round(random.uniform(8.2, 34.9), 2), "USD")

    # Marketing & health
    emit("business.push_notification_ctr_pct", round(random.uniform(2.0, 11.5), 2), "%")
    emit("business.newsletter_open_rate_pct", round(random.uniform(16.0, 38.0), 2), "%")
    emit("business.loyalty_points_redeemed_per_min", float(random.randint(25_000, 380_000)), "pts/min")
    emit("business.social_clip_shares_per_min", float(random.randint(3_000, 95_000)), "shares/min")
    emit("business.churn_risk_index_0_100", round(random.uniform(11.0, 52.0), 1), "index")
    emit("business.net_satisfaction_proxy_nps", round(random.uniform(-8.0, 68.0), 1), "score")

"""Synthetic `business.*` OTLP gauges for the Gaming Executive Dashboard."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.base_service import BaseService


def emit_executive_business_metrics_if_eligible(service: "BaseService") -> None:
    """Emit live gaming leadership KPI gauges once per telemetry cycle from the designated service."""
    ctx = getattr(service, "_ctx", None)
    if not ctx:
        return
    want = getattr(ctx.scenario, "executive_kpi_emitter_service_name", None)
    if not want or want != service.SERVICE_NAME:
        return

    emit = service.emit_metric

    # Player engagement
    emit("business.daily_active_users", float(random.randint(45_000, 680_000)), "users")
    emit("business.sessions_per_min", float(random.randint(1_800, 28_000)), "sessions/min")
    emit("business.avg_session_duration_min", round(random.uniform(18.0, 95.0), 1), "min")
    emit("business.matches_played_per_min", float(random.randint(380, 8_500)), "matches/min")
    emit("business.quests_completed_per_min", float(random.randint(850, 18_000)), "quests/min")
    emit("business.daily_retention_rate_pct", round(random.uniform(28.0, 68.0), 2), "%")

    # Monetization
    emit("business.revenue_usd_per_min", round(random.uniform(12_000.0, 185_000.0), 1), "USD/min")
    emit("business.in_app_purchases_per_min", float(random.randint(85, 1_800)), "purchases/min")
    emit("business.battle_pass_conversions_per_min", float(random.randint(12, 380)), "conversions/min")
    emit("business.avg_revenue_per_user_usd", round(random.uniform(2.8, 28.4), 2), "USD")
    emit("business.loot_opens_per_min", float(random.randint(280, 5_800)), "opens/min")
    emit("business.cosmetic_sales_usd_per_min", round(random.uniform(4_500.0, 72_000.0), 1), "USD/min")

    # Community
    emit("business.chat_messages_per_min", float(random.randint(8_500, 180_000)), "messages/min")
    emit("business.social_clip_shares_per_min", float(random.randint(120, 4_800)), "shares/min")
    emit("business.toxic_report_rate_pct", round(random.uniform(0.8, 4.2), 2), "%")
    emit("business.creator_uploads_per_min", float(random.randint(2, 85)), "uploads/min")
    emit("business.streaming_viewers", float(random.randint(4_500, 85_000)), "viewers")
    emit("business.new_registrations_per_min", float(random.randint(12, 380)), "registrations/min")

    # Live ops health
    emit("business.server_tick_lag_ms", round(random.uniform(12.0, 85.0), 1), "ms")
    emit("business.crash_rate_pct", round(random.uniform(0.01, 0.38), 3), "%")
    emit("business.player_bug_reports_per_min", round(random.uniform(0.2, 8.5), 2), "reports/min")
    emit("business.churn_risk_index_0_100", round(random.uniform(18.0, 52.0), 1), "index")
    emit("business.net_satisfaction_proxy_nps", round(random.uniform(25.0, 72.0), 1), "score")
    emit("business.content_moderation_queue_size", float(random.randint(0, 285)), "items")

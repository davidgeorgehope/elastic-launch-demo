"""Ad Platform service — GCP us-central1-a. Ad serving, click attribution, and revenue tracking."""

from __future__ import annotations

import random

from app.services.base_service import BaseService
from scenarios.ecommerce.executive_kpis import emit_executive_business_metrics_if_eligible


class AdPlatformService(BaseService):
    SERVICE_NAME = "ad-platform"

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # Ad revenue is the most critical business metric for this service.
        # If ads stop serving, revenue drops to zero — reportable to senior leadership.
        revenue_per_minute_usd = round(random.uniform(850.0, 3200.0), 2)
        impressions_per_sec = round(random.uniform(8000.0, 28000.0), 1)
        fill_rate_pct = round(random.uniform(82.0, 96.0), 2)
        cpm_usd = round(random.uniform(1.80, 7.50), 2)
        click_through_rate_pct = round(random.uniform(0.8, 3.5), 3)

        self.emit_metric("ads.revenue_per_minute_usd", revenue_per_minute_usd, "USD/min")
        self.emit_metric("ads.impressions_per_sec", impressions_per_sec, "imp/s")
        self.emit_metric("ads.fill_rate_pct", fill_rate_pct, "%")
        self.emit_metric("ads.cpm_usd", cpm_usd, "USD")
        self.emit_metric("ads.click_through_rate_pct", click_through_rate_pct, "%")

        self.emit_log(
            "INFO",
            f"ads.health fill_rate={fill_rate_pct}% revenue/min=${revenue_per_minute_usd} "
            f"impressions/sec={impressions_per_sec} cpm=${cpm_usd} ctr={click_through_rate_pct}%",
            {
                "operation": "ads_health",
                "ads.revenue_per_minute_usd": revenue_per_minute_usd,
                "ads.impressions_per_sec": impressions_per_sec,
                "ads.fill_rate_pct": fill_rate_pct,
                "ads.cpm_usd": cpm_usd,
                "ads.click_through_rate_pct": click_through_rate_pct,
            },
        )

        active_campaigns = random.randint(45, 280)
        budget_utilization_pct = round(random.uniform(35.0, 85.0), 1)
        self.emit_log(
            "INFO",
            f"ads.campaign_health active_campaigns={active_campaigns} budget_utilization={budget_utilization_pct}%",
            {
                "operation": "campaign_health",
                "ads.active_campaigns": active_campaigns,
                "ads.budget_utilization_pct": budget_utilization_pct,
            },
        )

        emit_executive_business_metrics_if_eligible(self)

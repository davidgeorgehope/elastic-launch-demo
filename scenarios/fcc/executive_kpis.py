"""Synthetic `business.*` OTLP gauges for the FCC Communications Executive Dashboard."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.base_service import BaseService


def emit_executive_business_metrics_if_eligible(service: "BaseService") -> None:
    """Emit FCC leadership KPI gauges once per telemetry cycle from the designated service."""
    ctx = getattr(service, "_ctx", None)
    if not ctx:
        return
    want = getattr(ctx.scenario, "executive_kpi_emitter_service_name", None)
    if not want or want != service.SERVICE_NAME:
        return

    emit = service.emit_metric

    # Broadband & consumer protection
    emit("business.broadband_availability_pct", round(random.uniform(91.0, 99.2), 2), "%")
    emit("business.speed_test_median_down_mbps", round(random.uniform(120.0, 680.0), 1), "Mbps")
    emit("business.consumer_complaints_per_min", float(random.randint(12, 240)), "complaints/min")
    emit("business.complaint_sla_compliance_pct", round(random.uniform(86.0, 99.5), 2), "%")
    emit("business.net_neutrality_review_queue", float(random.randint(20, 850)), "cases")
    emit("business.robocall_blocks_per_min", float(random.randint(25_000, 1_200_000)), "blocks/min")

    # Spectrum & licensing
    emit("business.spectrum_occupancy_pct", round(random.uniform(54.0, 91.0), 2), "%")
    emit("business.interference_cases_open", float(random.randint(4, 160)), "cases")
    emit("business.license_processing_backlog", float(random.randint(120, 14_000)), "applications")
    emit("business.auction_bid_volume_usd_per_min", round(random.uniform(150_000.0, 24_000_000.0), 1), "USD/min")
    emit("business.license_system_success_rate_pct", round(random.uniform(96.0, 99.99), 3), "%")
    emit("business.enforcement_actions_per_min", round(random.uniform(0.1, 8.0), 2), "actions/min")

    # Public safety & emergency communications
    emit("business.eas_delivery_success_pct", round(random.uniform(97.5, 99.999), 3), "%")
    emit("business.wea_delivery_latency_ms", round(random.uniform(250.0, 4500.0), 1), "ms")
    emit("business.psap_911_availability_pct", round(random.uniform(99.0, 99.999), 4), "%")
    emit("business.outage_reports_per_min", float(random.randint(0, 950)), "reports/min")
    emit("business.restoration_eta_min", round(random.uniform(8.0, 240.0), 1), "min")
    emit("business.public_safety_risk_index_0_100", round(random.uniform(8.0, 88.0), 2), "index")

    # Platform operations
    emit("business.api_success_rate_pct", round(random.uniform(98.5, 99.995), 3), "%")
    emit("business.data_ingest_lag_sec", round(random.uniform(1.0, 360.0), 1), "s")
    emit("business.caseworker_productivity_per_hour", round(random.uniform(18.0, 94.0), 1), "cases/hour")
    emit("business.fraud_detection_precision_pct", round(random.uniform(82.0, 98.0), 2), "%")
    emit("business.incident_mttd_min", round(random.uniform(0.6, 18.0), 2), "min")
    emit("business.incident_mttr_min", round(random.uniform(4.0, 160.0), 1), "min")

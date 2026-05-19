"""Synthetic `business.*` OTLP gauges for the GCP Network Operations Executive Dashboard."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.base_service import BaseService


def emit_executive_business_metrics_if_eligible(service: "BaseService") -> None:
    """Emit GCP network operations leadership KPI gauges once per telemetry cycle from the designated service."""
    ctx = getattr(service, "_ctx", None)
    if not ctx:
        return
    want = getattr(ctx.scenario, "executive_kpi_emitter_service_name", None)
    if not want or want != service.SERVICE_NAME:
        return

    emit = service.emit_metric

    # Delivery
    emit("business.cdn_cache_hit_rate_pct", round(random.uniform(82.0, 98.4), 2), "%")
    emit("business.requests_per_min", float(random.randint(2_800_000, 48_000_000)), "requests/min")
    emit("business.bytes_egress_gib_per_min", round(random.uniform(18_000.0, 380_000.0), 1), "GiB/min")
    emit("business.origin_offload_pct", round(random.uniform(72.0, 96.0), 2), "%")
    emit("business.edge_latency_p50_ms", round(random.uniform(8.0, 28.0), 1), "ms")
    emit("business.cdn_error_rate_pct", round(random.uniform(0.02, 0.85), 3), "%")

    # Capacity & security
    emit("business.peak_bandwidth_utilization_pct", round(random.uniform(38.0, 88.0), 2), "%")
    emit("business.interconnect_utilization_pct", round(random.uniform(22.0, 78.0), 2), "%")
    emit("business.cloud_armor_blocks_per_min", float(random.randint(180, 8_500)), "blocks/min")
    emit("business.vpc_flow_anomalies_per_min", round(random.uniform(0.2, 12.0), 2), "anomalies/min")
    emit("business.nat_port_exhaustion_rate_pct", round(random.uniform(0.1, 4.8), 3), "%")
    emit("business.load_balancer_rps", float(random.randint(28_000, 480_000)), "req/s")

    # SLO & reliability
    emit("business.uptime_pct", round(random.uniform(99.5, 99.999), 4), "%")
    emit("business.api_success_rate_pct", round(random.uniform(99.2, 99.99), 3), "%")
    emit("business.network_sla_compliance_pct", round(random.uniform(98.5, 99.99), 3), "%")
    emit("business.incident_mttd_min", round(random.uniform(0.8, 12.4), 2), "min")
    emit("business.incident_mttr_min", round(random.uniform(4.5, 85.0), 1), "min")
    emit("business.availability_index_0_100", round(random.uniform(88.0, 100.0), 2), "index")

    # Commercial
    emit("business.cloud_spend_usd_per_min", round(random.uniform(8_500.0, 95_000.0), 1), "USD/min")
    emit("business.committed_use_discount_utilization_pct", round(random.uniform(62.0, 98.0), 2), "%")
    emit("business.cost_per_million_requests_usd", round(random.uniform(1.2, 28.4), 2), "USD")
    emit("business.resource_efficiency_pct", round(random.uniform(58.0, 88.0), 2), "%")
    emit("business.carbon_intensity_gco2_per_tib", round(random.uniform(0.8, 4.2), 3), "gCO2/TiB")
    emit("business.customer_sla_breach_count", float(random.randint(0, 12)), "count")

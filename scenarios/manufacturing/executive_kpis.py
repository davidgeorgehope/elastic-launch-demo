"""Synthetic `business.*` OTLP gauges for the Manufacturing Executive Dashboard."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.base_service import BaseService


def emit_executive_business_metrics_if_eligible(service: "BaseService") -> None:
    """Emit manufacturing leadership KPI gauges once per telemetry cycle from the designated service."""
    ctx = getattr(service, "_ctx", None)
    if not ctx:
        return
    want = getattr(ctx.scenario, "executive_kpi_emitter_service_name", None)
    if not want or want != service.SERVICE_NAME:
        return

    emit = service.emit_metric

    # Production performance — OEE and throughput
    emit("business.oee_overall_pct", round(random.uniform(68.0, 92.0), 2), "%")
    emit("business.oee_availability_pct", round(random.uniform(78.0, 96.0), 2), "%")
    emit("business.oee_performance_pct", round(random.uniform(82.0, 98.0), 2), "%")
    emit("business.oee_quality_pct", round(random.uniform(94.0, 99.6), 2), "%")
    emit("business.throughput_units_per_hour", float(random.randint(420, 1250)), "units/hr")
    emit("business.cycle_time_seconds", round(random.uniform(38.0, 92.0), 1), "s")

    # Quality — yield, scrap, defects
    emit("business.first_pass_yield_pct", round(random.uniform(91.0, 99.2), 2), "%")
    emit("business.scrap_rate_pct", round(random.uniform(0.4, 4.8), 2), "%")
    emit("business.defect_ppm", float(random.randint(120, 4500)), "ppm")
    emit("business.rework_hours_per_shift", round(random.uniform(0.5, 6.5), 2), "hours")
    emit("business.process_cpk", round(random.uniform(1.05, 1.95), 3), "index")
    emit("business.customer_complaints_per_day", round(random.uniform(0.0, 4.5), 2), "count/day")

    # Maintenance & reliability
    emit("business.unplanned_downtime_min_per_shift", round(random.uniform(2.0, 38.0), 1), "min")
    emit("business.mtbf_hours", round(random.uniform(180.0, 720.0), 1), "hours")
    emit("business.mttr_minutes", round(random.uniform(8.0, 95.0), 1), "min")
    emit("business.pm_compliance_pct", round(random.uniform(72.0, 98.0), 2), "%")
    emit("business.spare_parts_stockout_risk_pct", round(random.uniform(2.0, 18.0), 2), "%")
    emit("business.maintenance_backlog_count", float(random.randint(8, 95)), "count")

    # Cost & operations
    emit("business.cost_of_poor_quality_usd_per_min", round(random.uniform(35.0, 480.0), 1), "USD/min")
    emit("business.energy_consumption_kwh", round(random.uniform(3200.0, 12_500.0), 1), "kWh")
    emit("business.material_variance_usd", round(random.uniform(-8500.0, 12_000.0), 1), "USD")
    emit("business.on_time_delivery_pct", round(random.uniform(86.0, 99.2), 2), "%")
    emit("business.inventory_turns", round(random.uniform(6.5, 18.5), 2), "turns/yr")
    emit("business.recordable_safety_incidents", float(random.randint(0, 2)), "count")

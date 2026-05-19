"""Synthetic `business.*` OTLP gauges for the NOVA-7 Space Mission Executive Dashboard."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.base_service import BaseService


def emit_executive_business_metrics_if_eligible(service: "BaseService") -> None:
    """Emit NOVA-7 mission leadership KPI gauges once per telemetry cycle from the designated service."""
    ctx = getattr(service, "_ctx", None)
    if not ctx:
        return
    want = getattr(ctx.scenario, "executive_kpi_emitter_service_name", None)
    if not want or want != service.SERVICE_NAME:
        return

    emit = service.emit_metric

    # Mission assurance
    emit("business.mission_success_probability_pct", round(random.uniform(92.0, 99.8), 2), "%")
    emit("business.critical_system_uptime_pct", round(random.uniform(99.2, 99.999), 4), "%")
    emit("business.fault_events_per_min", round(random.uniform(0.01, 2.8), 3), "events/min")
    emit("business.autonomous_recovery_rate_pct", round(random.uniform(82.0, 99.0), 2), "%")
    emit("business.telemetry_coverage_pct", round(random.uniform(88.0, 99.4), 2), "%")
    emit("business.spacecraft_health_index_0_100", round(random.uniform(72.0, 99.0), 1), "index")

    # Orbital mechanics
    emit("business.trajectory_deviation_meters", round(random.uniform(0.1, 850.0), 1), "m")
    emit("business.delta_v_budget_remaining_mps", round(random.uniform(12.0, 285.0), 1), "m/s")
    emit("business.orbital_period_drift_ms", round(random.uniform(0.0, 18.4), 2), "ms")
    emit("business.maneuver_accuracy_pct", round(random.uniform(96.0, 99.98), 3), "%")
    emit("business.station_keeping_fuel_remaining_pct", round(random.uniform(28.0, 92.0), 2), "%")
    emit("business.perigee_altitude_km", round(random.uniform(380.0, 420.0), 1), "km")

    # Communications
    emit("business.downlink_data_rate_mbps", round(random.uniform(125.0, 1_200.0), 1), "Mbps")
    emit("business.uplink_latency_ms", round(random.uniform(28.0, 450.0), 1), "ms")
    emit("business.contact_window_utilization_pct", round(random.uniform(72.0, 98.0), 2), "%")
    emit("business.packet_loss_rate_pct", round(random.uniform(0.01, 1.2), 3), "%")
    emit("business.command_acceptance_rate_pct", round(random.uniform(98.5, 99.99), 3), "%")
    emit("business.ground_station_availability_pct", round(random.uniform(92.0, 99.8), 2), "%")

    # Program health
    emit("business.schedule_variance_days", round(random.uniform(-8.0, 18.0), 1), "days")
    emit("business.launch_readiness_index_0_100", round(random.uniform(72.0, 98.0), 1), "index")
    emit("business.contractor_sla_compliance_pct", round(random.uniform(88.0, 99.2), 2), "%")
    emit("business.cost_variance_pct", round(random.uniform(-4.8, 12.4), 2), "%")
    emit("business.risk_burn_down_rate", round(random.uniform(0.8, 4.8), 2), "rate")
    emit("business.program_net_satisfaction_proxy_nps", round(random.uniform(32.0, 85.0), 1), "score")

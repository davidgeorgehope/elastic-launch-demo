"""Synthetic `business.*` OTLP gauges for the Healthcare Executive Dashboard."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.base_service import BaseService


def emit_executive_business_metrics_if_eligible(service: "BaseService") -> None:
    """Emit healthcare leadership KPI gauges once per telemetry cycle from the designated service."""
    ctx = getattr(service, "_ctx", None)
    if not ctx:
        return
    want = getattr(ctx.scenario, "executive_kpi_emitter_service_name", None)
    if not want or want != service.SERVICE_NAME:
        return

    emit = service.emit_metric

    # Access & throughput
    emit("business.ed_door_to_provider_min", round(random.uniform(8.0, 45.0), 1), "min")
    emit("business.admits_per_min", round(random.uniform(0.8, 4.2), 2), "admits/min")
    emit("business.discharges_per_min", round(random.uniform(0.6, 3.8), 2), "discharges/min")
    emit("business.bed_occupancy_pct", round(random.uniform(68.0, 98.0), 2), "%")
    emit("business.or_utilization_pct", round(random.uniform(72.0, 96.0), 2), "%")
    emit("business.icu_capacity_pct", round(random.uniform(55.0, 92.0), 2), "%")

    # Revenue cycle
    emit("business.claims_submitted_per_min", float(random.randint(12, 180)), "claims/min")
    emit("business.clean_claim_rate_pct", round(random.uniform(88.0, 98.4), 2), "%")
    emit("business.denials_per_min", round(random.uniform(0.5, 8.5), 2), "denials/min")
    emit("business.accounts_receivable_days", round(random.uniform(28.0, 65.0), 1), "days")
    emit("business.collections_usd_per_min", round(random.uniform(18_000.0, 185_000.0), 1), "USD/min")
    emit("business.unbilled_charges_usd_per_min", round(random.uniform(4_500.0, 45_000.0), 1), "USD/min")

    # Clinical quality
    emit("business.order_turnaround_min", round(random.uniform(2.8, 18.4), 2), "min")
    emit("business.lab_critical_notification_pct", round(random.uniform(88.0, 99.4), 2), "%")
    emit("business.medication_reconciliation_rate_pct", round(random.uniform(78.0, 96.0), 2), "%")
    emit("business.patient_safety_events_per_min", round(random.uniform(0.01, 0.45), 3), "events/min")
    emit("business.hcahps_proxy_score", round(random.uniform(68.0, 94.0), 1), "score")
    emit("business.readmission_risk_index_0_100", round(random.uniform(8.0, 45.0), 1), "index")

    # Operations
    emit("business.ehr_response_time_ms", round(random.uniform(280.0, 1_800.0), 1), "ms")
    emit("business.hl7_messages_per_min", float(random.randint(850, 18_000)), "messages/min")
    emit("business.imaging_worklist_size", float(random.randint(0, 285)), "items")
    emit("business.appointment_no_show_rate_pct", round(random.uniform(8.4, 28.6), 2), "%")
    emit("business.patient_satisfaction_nps", round(random.uniform(18.0, 72.0), 1), "score")
    emit("business.staff_compliance_rate_pct", round(random.uniform(88.0, 99.2), 2), "%")

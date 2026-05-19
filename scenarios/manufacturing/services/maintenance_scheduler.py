"""Maintenance Scheduler service — GCP us-central1-a. CMMS integration, predictive maintenance signals."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class MaintenanceSchedulerService(BaseService):
    SERVICE_NAME = "maintenance-scheduler"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._work_orders_total = 0
        self._last_pm_report = time.time()
        self._assets = ["MTR-CONV-01", "MTR-CONV-02", "SPN-MILL-04", "PMP-COOL-02", "CMP-AIR-01"]

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_predictive_signal()
        self._emit_work_order_event()

        if time.time() - self._last_pm_report > 10:
            self._emit_pm_compliance()
            self._last_pm_report = time.time()

        self._work_orders_total += 1
        self.emit_metric("maintenance.work_orders_total", float(self._work_orders_total), "orders")
        backlog = (
            random.randint(8, 35)
            if not active_channels
            else random.randint(80, 240)
        )
        self.emit_metric("maintenance.backlog_count", float(backlog), "orders")
        self.emit_metric("maintenance.mtbf_hours", round(random.uniform(220.0, 680.0), 1), "hours")

    def _emit_predictive_signal(self) -> None:
        asset = random.choice(self._assets)
        sensor = random.choice(["vibration_rms_mm_s", "bearing_temp_c", "current_amp", "thermal_dt_c"])
        value = round(random.uniform(0.5, 8.0), 2)
        self.emit_log(
            "INFO",
            f"[CMMS] predictive_signal asset={asset} sensor={sensor} value={value} health_score={round(random.uniform(0.65, 0.99), 3)}",
            {
                "operation": "predictive_signal",
                "maintenance.asset": asset,
                "maintenance.sensor": sensor,
                "maintenance.value": value,
            },
        )

    def _emit_work_order_event(self) -> None:
        wo_id = f"MWO-{random.randint(10000, 99999)}"
        asset = random.choice(self._assets)
        wo_type = random.choice(["preventive", "preventive", "corrective", "predictive"])
        priority = random.choice(["low", "medium", "high"])
        self.emit_log(
            "INFO",
            f"[CMMS] mwo_status wo={wo_id} asset={asset} type={wo_type} priority={priority} status=SCHEDULED",
            {
                "operation": "mwo_status",
                "maintenance.work_order_id": wo_id,
                "maintenance.asset": asset,
                "maintenance.work_type": wo_type,
                "maintenance.priority": priority,
            },
        )

    def _emit_pm_compliance(self) -> None:
        compliance = round(random.uniform(82.0, 98.0), 1)
        overdue = random.randint(2, 18)
        self.emit_log(
            "INFO",
            f"[CMMS] pm_compliance pct={compliance} overdue={overdue} mttr_min={random.randint(15, 95)}",
            {
                "operation": "pm_compliance",
                "maintenance.pm_compliance_pct": compliance,
                "maintenance.overdue_count": overdue,
            },
        )

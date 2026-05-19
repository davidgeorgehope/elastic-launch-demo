"""Clinical Alerts service — Azure eastus-2. Clinical decision support, nurse call integration, and alert routing."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class ClinicalAlertsService(BaseService):
    SERVICE_NAME = "clinical-alerts"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._alerts_processed = 0
        self._last_cds_report = time.time()
        self._alert_types = [
            "critical_lab",
            "vital_sign",
            "drug_interaction",
            "fall_risk",
            "sepsis_screen",
            "nurse_call",
            "code_blue",
        ]

    def generate_telemetry(self) -> None:
        # -- Fault injection ------------------------------------
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Normal telemetry -----------------------------------
        self._emit_alert_event()
        self._emit_rule_evaluation()

        if time.time() - self._last_cds_report > 10:
            self._emit_cds_summary()
            self._last_cds_report = time.time()

        # Metrics
        self._alerts_processed += 1
        self.emit_metric(
            "clinical_alerts.alerts_processed", float(self._alerts_processed), "alerts"
        )
        eval_ms = (
            random.randint(50, 500)
            if not active_channels
            else random.randint(3000, 12000)
        )
        self.emit_metric("clinical_alerts.rule_eval_ms", float(eval_ms), "ms")
        self.emit_metric(
            "clinical_alerts.active_rules", float(random.randint(200, 350)), "rules"
        )

    def _emit_alert_event(self) -> None:
        alert_type = random.choice(self._alert_types)
        patient_id = f"PT-{random.randint(100000, 999999)}"
        unit = random.choice(["ICU-3A", "ICU-3B", "MedSurg-4N", "ED-1", "NICU-2"])
        priority = random.choice(["low", "medium", "high", "critical"])
        delivery_ms = random.randint(100, 1200)
        self.emit_log(
            "INFO",
            f"[CDS] alert_delivered type={alert_type} priority={priority} patient={patient_id} unit={unit} delivery_ms={delivery_ms} status=DELIVERED",
            {
                "operation": "alert_delivery",
                "alert.type": alert_type,
                "alert.patient_id": patient_id,
                "alert.unit": unit,
                "alert.priority": priority,
                "alert.delivery_ms": delivery_ms,
                "alert.status": "DELIVERED",
            },
        )

    def _emit_rule_evaluation(self) -> None:
        rules_evaluated = random.randint(5, 30)
        triggered = random.randint(0, 3)
        eval_ms = random.randint(80, 600)
        patient_id = f"PT-{random.randint(100000, 999999)}"
        self.emit_log(
            "INFO",
            f"[CDS] rule_eval patient={patient_id} rules_checked={rules_evaluated} triggered={triggered} eval_ms={eval_ms} status=OK",
            {
                "operation": "rule_evaluation",
                "cds.rules_evaluated": rules_evaluated,
                "cds.rules_triggered": triggered,
                "cds.eval_ms": eval_ms,
                "cds.patient_id": patient_id,
            },
        )

    def _emit_cds_summary(self) -> None:
        total_rules = random.randint(250, 350)
        alerts_hour = random.randint(80, 250)
        self.emit_log(
            "INFO",
            f"[CDS] engine_summary active_rules={total_rules} alerts_per_hr={alerts_hour} total_processed={self._alerts_processed} engine=NOMINAL",
            {
                "operation": "cds_summary",
                "cds.active_rules": total_rules,
                "cds.alerts_per_hour": alerts_hour,
                "cds.total_processed": self._alerts_processed,
            },
        )

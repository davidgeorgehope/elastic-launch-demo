"""EHR System service — AWS us-east-1a. Electronic health records, clinical documentation, and patient charts."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class EHRSystemService(BaseService):
    SERVICE_NAME = "ehr-system"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._encounters_total = 0
        self._last_census_report = time.time()
        self._departments = [
            "ED",
            "ICU-3A",
            "MedSurg-4N",
            "L&D",
            "Oncology",
            "Cardiology",
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
        self._emit_encounter_event()
        self._emit_chart_access()

        if time.time() - self._last_census_report > 10:
            self._emit_census_snapshot()
            self._last_census_report = time.time()

        # Metrics
        self._encounters_total += 1
        self.emit_metric(
            "ehr.encounters_total", float(self._encounters_total), "encounters"
        )
        self.emit_metric(
            "ehr.active_sessions", float(random.randint(40, 120)), "sessions"
        )
        query_ms = (
            random.randint(5, 80) if not active_channels else random.randint(800, 5000)
        )
        self.emit_metric("ehr.query_latency_ms", float(query_ms), "ms")

    def _emit_encounter_event(self) -> None:
        dept = random.choice(self._departments)
        mrn = f"MRN-{random.randint(1000000, 9999999)}"
        enc_type = random.choice(
            ["inpatient", "outpatient", "emergency", "observation"]
        )
        self.emit_log(
            "INFO",
            f"[EHR] encounter_open type={enc_type} mrn={mrn} dept={dept} status=ACTIVE",
            {
                "operation": "encounter_open",
                "encounter.type": enc_type,
                "encounter.department": dept,
                "patient.mrn": mrn,
                "encounter.status": "ACTIVE",
            },
        )

    def _emit_chart_access(self) -> None:
        action = random.choice(["view", "edit", "sign", "cosign", "addendum"])
        doc_type = random.choice(
            ["progress_note", "h_and_p", "discharge_summary", "order_set"]
        )
        provider = f"NPI-{random.randint(1000000000, 9999999999)}"
        latency_ms = random.randint(15, 120)
        self.emit_log(
            "INFO",
            f"[EHR] chart_access action={action} doc_type={doc_type} provider={provider} latency={latency_ms}ms status=OK",
            {
                "operation": "chart_access",
                "chart.action": action,
                "chart.document_type": doc_type,
                "chart.provider": provider,
                "chart.latency_ms": latency_ms,
            },
        )

    def _emit_census_snapshot(self) -> None:
        total_patients = random.randint(180, 350)
        self.emit_log(
            "INFO",
            f"[EHR] census_snapshot patients={total_patients} departments={len(self._departments)} adt_sync=CURRENT status=NOMINAL",
            {
                "operation": "census_snapshot",
                "census.total_patients": total_patients,
                "census.departments": len(self._departments),
                "census.status": "NOMINAL",
            },
        )

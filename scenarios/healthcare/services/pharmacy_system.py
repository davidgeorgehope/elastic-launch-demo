"""Pharmacy System service — GCP us-central1-a. Medication ordering, dispensing, and drug interaction checking."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class PharmacySystemService(BaseService):
    SERVICE_NAME = "pharmacy-system"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._orders_dispensed = 0
        self._last_formulary_check = time.time()
        self._medications = [
            "Metoprolol 50mg",
            "Lisinopril 10mg",
            "Heparin 5000u",
            "Vancomycin 1g",
            "Morphine 4mg",
            "Ondansetron 4mg",
            "Ceftriaxone 1g",
            "Pantoprazole 40mg",
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
        self._emit_dispense_event()
        self._emit_interaction_check()

        if time.time() - self._last_formulary_check > 10:
            self._emit_formulary_status()
            self._last_formulary_check = time.time()

        # Metrics
        self._orders_dispensed += 1
        self.emit_metric(
            "pharmacy.orders_dispensed", float(self._orders_dispensed), "orders"
        )
        interaction_queue = (
            random.randint(2, 15) if not active_channels else random.randint(80, 400)
        )
        self.emit_metric(
            "pharmacy.interaction_queue_depth", float(interaction_queue), "checks"
        )
        self.emit_metric(
            "pharmacy.formulary_compliance_pct",
            round(random.uniform(95.0, 99.8), 1),
            "%",
        )

    def _emit_dispense_event(self) -> None:
        med = random.choice(self._medications)
        patient_id = f"PT-{random.randint(100000, 999999)}"
        rx_id = f"RX-{random.randint(100000, 999999)}"
        route = random.choice(["IV", "PO", "IM", "SQ", "topical"])
        self.emit_log(
            "INFO",
            f"[PHARM] dispense rx={rx_id} med={med} route={route} patient={patient_id} status=VERIFIED",
            {
                "operation": "dispense",
                "pharmacy.rx_id": rx_id,
                "pharmacy.medication": med,
                "pharmacy.route": route,
                "pharmacy.patient_id": patient_id,
                "pharmacy.status": "DISPENSED",
            },
        )

    def _emit_interaction_check(self) -> None:
        med_a = random.choice(self._medications)
        med_b = random.choice(self._medications)
        severity = random.choice(["none", "none", "minor", "moderate"])
        check_ms = random.randint(5, 40)
        self.emit_log(
            "INFO",
            f"[PHARM] ddi_screen drug_a={med_a} drug_b={med_b} severity={severity} eval_ms={check_ms} status=CLEAR",
            {
                "operation": "interaction_check",
                "pharmacy.drug_a": med_a,
                "pharmacy.drug_b": med_b,
                "pharmacy.interaction_severity": severity,
                "pharmacy.check_ms": check_ms,
            },
        )

    def _emit_formulary_status(self) -> None:
        formulary_items = random.randint(2800, 3200)
        self.emit_log(
            "INFO",
            f"[PHARM] formulary_status items={formulary_items} dispensed={self._orders_dispensed} cpoe_pipeline=NOMINAL",
            {
                "operation": "formulary_status",
                "formulary.active_items": formulary_items,
                "formulary.total_dispensed": self._orders_dispensed,
            },
        )

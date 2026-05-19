"""Scheduling API service — GCP us-central1-a. Appointment booking, bed management, and OR scheduling."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class SchedulingAPIService(BaseService):
    SERVICE_NAME = "scheduling-api"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._appointments_booked = 0
        self._last_bed_census = time.time()
        self._units = ["ICU-3A", "ICU-3B", "MedSurg-4N", "MedSurg-4S", "ED-1", "NICU-2"]
        self._resource_types = [
            "exam_room",
            "procedure_room",
            "consult_room",
            "infusion_bay",
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
        self._emit_appointment_booking()
        self._emit_bed_update()

        if time.time() - self._last_bed_census > 10:
            self._emit_bed_census()
            self._last_bed_census = time.time()

        # Metrics
        self._appointments_booked += 1
        self.emit_metric(
            "scheduling.appointments_booked",
            float(self._appointments_booked),
            "appointments",
        )
        occupancy = (
            round(random.uniform(75.0, 96.0), 1)
            if not active_channels
            else round(random.uniform(97.0, 100.0), 1)
        )
        self.emit_metric("scheduling.bed_occupancy_pct", occupancy, "%")
        self.emit_metric(
            "scheduling.or_utilization_pct", round(random.uniform(65.0, 92.0), 1), "%"
        )

    def _emit_appointment_booking(self) -> None:
        patient_id = f"PT-{random.randint(100000, 999999)}"
        provider = f"NPI-{random.randint(1000000000, 9999999999)}"
        resource = random.choice(self._resource_types)
        slot = f"{random.randint(7, 17):02d}:{random.choice(['00', '15', '30', '45'])}"
        self.emit_log(
            "INFO",
            f"[SCHED] appointment_booked patient={patient_id} provider={provider} slot={slot} resource={resource} status=CONFIRMED",
            {
                "operation": "appointment_book",
                "scheduling.patient_id": patient_id,
                "scheduling.provider_id": provider,
                "scheduling.resource": resource,
                "scheduling.time_slot": slot,
                "scheduling.status": "CONFIRMED",
            },
        )

    def _emit_bed_update(self) -> None:
        unit = random.choice(self._units)
        bed = f"{random.choice(['A', 'B', 'C', 'D'])}-{random.randint(101, 450)}"
        status = random.choice(["occupied", "vacant", "cleaning", "reserved"])
        self.emit_log(
            "INFO",
            f"[SCHED] bed_update unit={unit} bed={bed} new_status={status} adt_sync=OK",
            {
                "operation": "bed_update",
                "bed.unit": unit,
                "bed.id": bed,
                "bed.status": status,
            },
        )

    def _emit_bed_census(self) -> None:
        total_beds = random.randint(280, 350)
        occupied = int(total_beds * random.uniform(0.78, 0.95))
        self.emit_log(
            "INFO",
            f"[SCHED] bed_census occupied={occupied}/{total_beds} units={len(self._units)} adt_sync=CURRENT",
            {
                "operation": "bed_census",
                "census.total_beds": total_beds,
                "census.occupied": occupied,
                "census.units": len(self._units),
                "census.adt_sync": "CURRENT",
            },
        )

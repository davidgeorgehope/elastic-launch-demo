"""Lab Integration service — AWS us-east-1c. Laboratory information system interface and result routing."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class LabIntegrationService(BaseService):
    SERVICE_NAME = "lab-integration"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._results_processed = 0
        self._last_queue_report = time.time()
        self._test_types = [
            "CBC",
            "BMP",
            "CMP",
            "PT/INR",
            "Troponin",
            "BNP",
            "Lipase",
            "UA",
            "Blood Culture",
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
        self._emit_result_delivery()
        self._emit_order_processing()

        if time.time() - self._last_queue_report > 10:
            self._emit_queue_status()
            self._last_queue_report = time.time()

        # Metrics
        self._results_processed += 1
        self.emit_metric(
            "lab.results_processed", float(self._results_processed), "results"
        )
        tat_minutes = (
            random.randint(10, 45) if not active_channels else random.randint(90, 300)
        )
        self.emit_metric("lab.avg_turnaround_minutes", float(tat_minutes), "min")
        self.emit_metric("lab.pending_orders", float(random.randint(20, 80)), "orders")

    def _emit_result_delivery(self) -> None:
        test = random.choice(self._test_types)
        order_id = f"LAB-{random.randint(100000, 999999)}"
        tat_min = random.randint(12, 55)
        abnormal = random.choice([True, False, False, False])
        flag = "ABNORMAL" if abnormal else "NORMAL"
        self.emit_log(
            "INFO",
            f"[LIS] result_delivered order={order_id} test={test} tat={tat_min}min flag={flag} status=DELIVERED",
            {
                "operation": "result_delivery",
                "lab.order_id": order_id,
                "lab.test_code": test,
                "lab.tat_minutes": tat_min,
                "lab.abnormal_flag": flag,
                "lab.status": "DELIVERED",
            },
        )

    def _emit_order_processing(self) -> None:
        test = random.choice(self._test_types)
        priority = random.choice(["STAT", "ROUTINE", "ROUTINE", "TIMED"])
        patient_id = f"PT-{random.randint(100000, 999999)}"
        self.emit_log(
            "INFO",
            f"[LIS] order_received test={test} priority={priority} patient={patient_id} specimen=RECEIVED status=IN_PROGRESS",
            {
                "operation": "order_processing",
                "lab.test_code": test,
                "lab.priority": priority,
                "lab.patient_id": patient_id,
                "lab.status": "SPECIMEN_RECEIVED",
            },
        )

    def _emit_queue_status(self) -> None:
        pending = random.randint(15, 60)
        in_progress = random.randint(10, 40)
        self.emit_log(
            "INFO",
            f"[LIS] queue_status pending={pending} in_progress={in_progress} completed={self._results_processed} pipeline=NOMINAL",
            {
                "operation": "queue_status",
                "queue.pending": pending,
                "queue.in_progress": in_progress,
                "queue.completed": self._results_processed,
            },
        )

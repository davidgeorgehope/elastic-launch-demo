"""Imaging Service — GCP us-central1-b. DICOM/PACS image transfer, storage, and radiology workflows."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class ImagingServiceService(BaseService):
    SERVICE_NAME = "imaging-service"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._studies_processed = 0
        self._last_pacs_report = time.time()
        self._modalities = ["CT", "MRI", "XR", "US", "MG", "NM"]

    def generate_telemetry(self) -> None:
        # -- Fault injection ------------------------------------
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Normal telemetry -----------------------------------
        self._emit_study_transfer()
        self._emit_worklist_event()

        if time.time() - self._last_pacs_report > 10:
            self._emit_pacs_status()
            self._last_pacs_report = time.time()

        # Metrics
        self._studies_processed += 1
        self.emit_metric(
            "imaging.studies_processed", float(self._studies_processed), "studies"
        )
        transfer_ms = (
            random.randint(200, 2000)
            if not active_channels
            else random.randint(8000, 30000)
        )
        self.emit_metric("imaging.transfer_latency_ms", float(transfer_ms), "ms")
        self.emit_metric(
            "imaging.pacs_storage_used_pct", round(random.uniform(60.0, 82.0), 1), "%"
        )

    def _emit_study_transfer(self) -> None:
        modality = random.choice(self._modalities)
        study_uid = f"1.2.840.{random.randint(10000, 99999)}.{random.randint(1, 999)}"
        images = random.randint(20, 600)
        size_mb = round(random.uniform(50.0, 1500.0), 1)
        transfer_ms = random.randint(500, 3000)
        self.emit_log(
            "INFO",
            f"[PACS] c_store_complete modality={modality} study={study_uid} images={images} size={size_mb}MB transfer_ms={transfer_ms} status=STORED",
            {
                "operation": "study_transfer",
                "imaging.modality": modality,
                "imaging.study_uid": study_uid,
                "imaging.image_count": images,
                "imaging.size_mb": size_mb,
                "imaging.transfer_ms": transfer_ms,
                "imaging.status": "STORED",
            },
        )

    def _emit_worklist_event(self) -> None:
        modality = random.choice(self._modalities)
        pending = random.randint(2, 20)
        next_patient = f"PT-{random.randint(100000, 999999)}"
        self.emit_log(
            "INFO",
            f"[PACS] mwl_query modality={modality} queued={pending} next_patient={next_patient} status=OK",
            {
                "operation": "worklist_query",
                "imaging.modality": modality,
                "imaging.worklist_pending": pending,
                "imaging.next_patient": next_patient,
            },
        )

    def _emit_pacs_status(self) -> None:
        volumes_online = random.randint(3, 5)
        total_tb = round(random.uniform(40.0, 80.0), 1)
        self.emit_log(
            "INFO",
            f"[PACS] storage_status volumes={volumes_online} total_tb={total_tb} studies_today={self._studies_processed} archive=NOMINAL",
            {
                "operation": "pacs_status",
                "pacs.volumes_online": volumes_online,
                "pacs.total_storage_tb": total_tb,
                "pacs.studies_today": self._studies_processed,
            },
        )

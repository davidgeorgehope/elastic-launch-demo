"""Document Vault service — Azure eastus-3. Document management & digital storage."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class DocumentVaultService(BaseService):
    SERVICE_NAME = "document-vault"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._docs_processed = 0
        self._last_summary = time.time()

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_document_operation()
        self._emit_storage_health()

        if time.time() - self._last_summary > 10:
            self._emit_vault_summary()
            self._last_summary = time.time()

        upload_rate = (
            round(random.uniform(40, 150), 1)
            if not active_channels
            else round(random.uniform(5, 20), 1)
        )
        self.emit_metric("document_vault.upload_rate", upload_rate, "docs/min")
        self.emit_metric(
            "document_vault.storage_used_tb", round(random.uniform(42, 48), 2), "TB"
        )
        self.emit_metric(
            "document_vault.ocr_queue_depth", float(random.randint(5, 50)), "docs"
        )

    def _emit_document_operation(self) -> None:
        self._docs_processed += 1
        doc_type = random.choice(
            [
                "CLAIM_PHOTO",
                "POLICY_DEC_PAGE",
                "ID_VERIFICATION",
                "PROOF_OF_LOSS",
                "COE_VA_LOAN",
                "DD214_DISCHARGE",
            ]
        )
        operation = random.choice(["UPLOAD", "RETRIEVE", "INDEX"])
        size_mb = round(random.uniform(0.2, 15.0), 1)
        self.emit_log(
            "INFO",
            f"[DOC] document_{operation.lower()} type={doc_type} size={size_mb}MB pii_scan=CLEAN encryption=AES256 status=SUCCESS",
            {
                "operation": f"document_{operation.lower()}",
                "doc.type": doc_type,
                "doc.size_mb": size_mb,
                "doc.pii_scan": "CLEAN",
            },
        )

    def _emit_storage_health(self) -> None:
        bucket_util = round(random.uniform(62, 78), 1)
        self.emit_log(
            "INFO",
            f"[DOC] storage_health bucket_utilization={bucket_util}% replication=3x encryption=SSE-KMS lifecycle_policy=ACTIVE status=NOMINAL",
            {
                "operation": "storage_health",
                "storage.utilization": bucket_util,
                "storage.replication": 3,
            },
        )

    def _emit_vault_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[DOC] vault_summary processed={self._docs_processed} storage_tb=45.2 compliance=SOX/HIPAA retention=7yr status=NOMINAL",
            {
                "operation": "vault_summary",
                "vault.processed": self._docs_processed,
                "vault.storage_tb": 45.2,
            },
        )

"""Data Warehouse service — Azure eastus-1. Clinical data warehouse ETL, HIPAA audit, and analytics."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class DataWarehouseService(BaseService):
    SERVICE_NAME = "data-warehouse"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._etl_runs_completed = 0
        self._last_audit_check = time.time()
        self._pipelines = [
            "ETL-CLINICAL-01",
            "ETL-BILLING-02",
            "ETL-LAB-03",
            "ETL-QUALITY-04",
        ]
        self._stages = ["extract", "transform", "load", "validate"]

    def generate_telemetry(self) -> None:
        # -- Fault injection ------------------------------------
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Normal telemetry -----------------------------------
        self._emit_etl_progress()
        self._emit_audit_event()

        if time.time() - self._last_audit_check > 12:
            self._emit_audit_integrity_check()
            self._last_audit_check = time.time()

        # Metrics
        self._etl_runs_completed += 1
        self.emit_metric(
            "warehouse.etl_runs_completed", float(self._etl_runs_completed), "runs"
        )
        rows_per_sec = (
            random.randint(5000, 25000)
            if not active_channels
            else random.randint(100, 2000)
        )
        self.emit_metric("warehouse.etl_rows_per_second", float(rows_per_sec), "rows/s")
        self.emit_metric(
            "warehouse.storage_used_tb", round(random.uniform(8.0, 25.0), 1), "TB"
        )

    def _emit_etl_progress(self) -> None:
        pipeline = random.choice(self._pipelines)
        stage = random.choice(self._stages)
        rows = random.randint(10000, 200000)
        total = rows + random.randint(50000, 500000)
        elapsed_s = random.randint(30, 600)
        self.emit_log(
            "INFO",
            f"[DW] etl_progress pipeline={pipeline} stage={stage} rows={rows}/{total} elapsed={elapsed_s}s status=RUNNING",
            {
                "operation": "etl_progress",
                "etl.pipeline_id": pipeline,
                "etl.stage": stage,
                "etl.rows_processed": rows,
                "etl.total_rows": total,
                "etl.elapsed_seconds": elapsed_s,
                "etl.status": "RUNNING",
            },
        )

    def _emit_audit_event(self) -> None:
        action = random.choice(
            ["PHI_ACCESS", "RECORD_EXPORT", "REPORT_GENERATE", "BULK_QUERY"]
        )
        user = f"user-{random.randint(1000, 9999)}@hospital.org"
        records_accessed = random.randint(1, 500)
        self.emit_log(
            "INFO",
            f"[DW] hipaa_audit action={action} user={user} records={records_accessed} chain_hash=VERIFIED",
            {
                "operation": "audit_log",
                "audit.action": action,
                "audit.user": user,
                "audit.records_accessed": records_accessed,
                "audit.hash_valid": True,
            },
        )

    def _emit_audit_integrity_check(self) -> None:
        chains_verified = random.randint(10, 25)
        total_entries = random.randint(500000, 2000000)
        self.emit_log(
            "INFO",
            f"[DW] integrity_check chains_verified={chains_verified} total_entries={total_entries} hash_chain=INTACT",
            {
                "operation": "integrity_check",
                "audit.chains_verified": chains_verified,
                "audit.total_entries": total_entries,
                "audit.integrity_status": "VALID",
            },
        )

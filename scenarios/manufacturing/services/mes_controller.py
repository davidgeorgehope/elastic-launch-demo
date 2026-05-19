"""MES Controller service — AWS us-east-1a. Manufacturing Execution System: work orders, batch genealogy, equipment state."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class MESControllerService(BaseService):
    SERVICE_NAME = "mes-controller"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._work_orders_total = 0
        self._last_batch_report = time.time()
        self._lines = ["LINE-01", "LINE-02", "LINE-03", "LINE-04", "LINE-05"]
        self._product_codes = ["PRD-A100", "PRD-A200", "PRD-B450", "PRD-B475", "PRD-C901"]

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_work_order_dispatch()
        self._emit_equipment_state()

        if time.time() - self._last_batch_report > 10:
            self._emit_batch_genealogy()
            self._last_batch_report = time.time()

        self._work_orders_total += 1
        self.emit_metric("mes.work_orders_processed", float(self._work_orders_total), "orders")
        queue_depth = (
            random.randint(8, 40)
            if not active_channels
            else random.randint(180, 950)
        )
        self.emit_metric("mes.work_order_queue_depth", float(queue_depth), "orders")
        self.emit_metric("mes.line_utilization_pct", round(random.uniform(72.0, 96.0), 1), "%")

    def _emit_work_order_dispatch(self) -> None:
        wo_id = f"WO-{random.randint(100000, 999999)}"
        line = random.choice(self._lines)
        product = random.choice(self._product_codes)
        qty = random.randint(50, 1200)
        self.emit_log(
            "INFO",
            f"[MES] work_order_dispatch wo={wo_id} line={line} product={product} qty={qty} status=RELEASED",
            {
                "operation": "work_order_dispatch",
                "mes.work_order_id": wo_id,
                "mes.line": line,
                "mes.product_code": product,
                "mes.quantity": qty,
                "mes.status": "RELEASED",
            },
        )

    def _emit_equipment_state(self) -> None:
        line = random.choice(self._lines)
        state = random.choice(["RUNNING", "RUNNING", "RUNNING", "IDLE", "CHANGEOVER"])
        oee = round(random.uniform(72.0, 94.0), 1)
        self.emit_log(
            "INFO",
            f"[MES] equipment_state line={line} state={state} oee={oee}% operator=OP-{random.randint(1000, 9999)}",
            {
                "operation": "equipment_state",
                "mes.line": line,
                "mes.equipment_state": state,
                "mes.oee_pct": oee,
            },
        )

    def _emit_batch_genealogy(self) -> None:
        batch_id = f"BATCH-{random.randint(100000, 999999)}"
        product = random.choice(self._product_codes)
        lot_count = random.randint(2, 8)
        self.emit_log(
            "INFO",
            f"[MES] batch_genealogy batch={batch_id} product={product} raw_lots={lot_count} traceability=COMPLETE",
            {
                "operation": "batch_genealogy",
                "mes.batch_id": batch_id,
                "mes.product_code": product,
                "mes.raw_material_lots": lot_count,
                "mes.traceability_status": "COMPLETE",
            },
        )

"""Inventory Sync service — Azure eastus-1. WMS / supplier feeds / raw material levels."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class InventorySyncService(BaseService):
    SERVICE_NAME = "inventory-sync"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._batches_total = 0
        self._last_supplier_report = time.time()
        self._materials = ["RM-STEEL-A36", "RM-ALU-6061", "RM-PLASTIC-ABS", "RM-COPPER-110", "RM-RUBBER-EPDM"]

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_inventory_delta()
        self._emit_supplier_event()

        if time.time() - self._last_supplier_report > 10:
            self._emit_reorder_check()
            self._last_supplier_report = time.time()

        self._batches_total += 1
        self.emit_metric("inventory.batches_synced", float(self._batches_total), "batches")
        self.emit_metric("inventory.stockout_risk_pct", round(random.uniform(2.0, 14.5), 2), "%")
        self.emit_metric("inventory.turns_per_year", round(random.uniform(7.0, 16.0), 2), "turns/yr")

    def _emit_inventory_delta(self) -> None:
        material = random.choice(self._materials)
        delta = random.randint(-500, 2000)
        on_hand = random.randint(2000, 50000)
        self.emit_log(
            "INFO",
            f"[WMS] inventory_delta material={material} delta={delta} on_hand={on_hand} location=WH-A-01",
            {
                "operation": "inventory_delta",
                "inventory.material": material,
                "inventory.delta_units": delta,
                "inventory.on_hand_units": on_hand,
            },
        )

    def _emit_supplier_event(self) -> None:
        supplier = f"SUP-{random.randint(1000, 9999)}"
        po_id = f"PO-{random.randint(100000, 999999)}"
        lead_days = random.randint(3, 28)
        self.emit_log(
            "INFO",
            f"[WMS] supplier_po po={po_id} supplier={supplier} lead_days={lead_days} status=CONFIRMED",
            {
                "operation": "supplier_po",
                "inventory.purchase_order": po_id,
                "inventory.supplier": supplier,
                "inventory.lead_days": lead_days,
            },
        )

    def _emit_reorder_check(self) -> None:
        material = random.choice(self._materials)
        on_hand = random.randint(800, 12000)
        reorder_point = random.randint(1500, 4000)
        self.emit_log(
            "INFO",
            f"[WMS] reorder_check material={material} on_hand={on_hand} reorder_point={reorder_point} action={'REORDER' if on_hand < reorder_point else 'NONE'}",
            {
                "operation": "reorder_check",
                "inventory.material": material,
                "inventory.on_hand_units": on_hand,
                "inventory.reorder_point": reorder_point,
            },
        )

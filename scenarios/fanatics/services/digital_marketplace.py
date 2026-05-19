"""Digital Marketplace service — AWS us-east-1b. E-commerce platform for physical and digital cards."""

from __future__ import annotations

import random

from app.services.base_service import BaseService
from scenarios.fanatics.executive_kpis import emit_executive_business_metrics_if_eligible


class DigitalMarketplaceService(BaseService):
    SERVICE_NAME = "digital-marketplace"

    def generate_telemetry(self) -> None:
        # -- Fault injection --
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Transaction metrics --
        active_users = random.randint(800, 3500)
        transactions_per_sec = round(random.uniform(45.0, 120.0), 1)
        cart_conversion = round(random.uniform(2.5, 6.8), 2)
        avg_response_ms = round(random.uniform(35.0, 120.0), 1)

        self.emit_metric("marketplace.active_users", float(active_users), "users")
        self.emit_metric(
            "marketplace.transactions_per_sec", transactions_per_sec, "tps"
        )
        self.emit_metric("marketplace.cart_conversion_pct", cart_conversion, "%")
        self.emit_metric("marketplace.avg_response_ms", avg_response_ms, "ms")

        emit_executive_business_metrics_if_eligible(self)

        self.emit_log(
            "INFO",
            f"marketplace.health active_users={active_users} tps={transactions_per_sec} "
            f"cart_conversion={cart_conversion}% response_ms={avg_response_ms}",
            {
                "operation": "marketplace_health",
                "marketplace.active_users": active_users,
                "marketplace.tps": transactions_per_sec,
                "marketplace.conversion": cart_conversion,
                "marketplace.response_ms": avg_response_ms,
            },
        )

        # Catalog sync status
        catalog_items = random.randint(120000, 180000)
        self.emit_log(
            "INFO",
            f"marketplace.catalog_sync status=nominal items_indexed={catalog_items}",
            {"operation": "catalog_sync", "catalog.item_count": catalog_items},
        )

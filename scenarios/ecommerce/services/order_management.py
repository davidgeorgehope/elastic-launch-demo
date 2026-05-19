"""Order Management service — AWS us-east-1c. Order processing, cart, and checkout."""

from __future__ import annotations

import random

from app.services.base_service import BaseService


class OrderManagementService(BaseService):
    SERVICE_NAME = "order-management"

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        orders_per_min = round(random.uniform(120.0, 450.0), 1)
        gmv_usd = round(random.uniform(15000.0, 65000.0), 2)
        avg_order_value_usd = round(random.uniform(48.0, 185.0), 2)
        checkout_abandonment_pct = round(random.uniform(18.0, 32.0), 2)

        self.emit_metric("orders.per_minute", orders_per_min, "orders/min")
        self.emit_metric("orders.gmv_usd", gmv_usd, "USD")
        self.emit_metric("orders.avg_order_value_usd", avg_order_value_usd, "USD")
        self.emit_metric("orders.checkout_abandonment_pct", checkout_abandonment_pct, "%")

        self.emit_log(
            "INFO",
            f"orders.health orders_per_min={orders_per_min} gmv_usd={gmv_usd} "
            f"avg_order_value={avg_order_value_usd} abandonment={checkout_abandonment_pct}%",
            {
                "operation": "orders_health",
                "orders.per_minute": orders_per_min,
                "orders.gmv_usd": gmv_usd,
                "orders.avg_order_value_usd": avg_order_value_usd,
                "orders.checkout_abandonment_pct": checkout_abandonment_pct,
            },
        )

        payment_success_rate = round(random.uniform(97.5, 99.8), 2)
        self.emit_log(
            "INFO",
            f"orders.payment_health success_rate={payment_success_rate}% orders_per_min={orders_per_min}",
            {"operation": "payment_health", "orders.payment_success_rate_pct": payment_success_rate},
        )

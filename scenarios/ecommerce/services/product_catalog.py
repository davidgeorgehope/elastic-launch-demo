"""Product Catalog service — AWS us-east-1b. Search, browse, and product data."""

from __future__ import annotations

import random

from app.services.base_service import BaseService


class ProductCatalogService(BaseService):
    SERVICE_NAME = "product-catalog"

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        search_latency_ms = round(random.uniform(18.0, 95.0), 1)
        items_indexed = random.randint(1200000, 2000000)
        reco_click_rate = round(random.uniform(4.5, 12.0), 2)
        search_rps = round(random.uniform(300.0, 1200.0), 1)

        self.emit_metric("catalog.search_latency_ms", search_latency_ms, "ms")
        self.emit_metric("catalog.items_indexed", float(items_indexed), "items")
        self.emit_metric("catalog.recommendation_click_rate_pct", reco_click_rate, "%")
        self.emit_metric("catalog.search_rps", search_rps, "rps")

        self.emit_log(
            "INFO",
            f"catalog.health search_latency_ms={search_latency_ms} items_indexed={items_indexed} "
            f"reco_click_rate={reco_click_rate}% search_rps={search_rps}",
            {
                "operation": "catalog_health",
                "catalog.search_latency_ms": search_latency_ms,
                "catalog.items_indexed": items_indexed,
                "catalog.reco_click_rate_pct": reco_click_rate,
                "catalog.search_rps": search_rps,
            },
        )

        index_health_pct = round(random.uniform(98.5, 100.0), 2)
        self.emit_log(
            "INFO",
            f"catalog.index_health health_pct={index_health_pct}% items={items_indexed}",
            {"operation": "index_health", "catalog.index_health_pct": index_health_pct},
        )

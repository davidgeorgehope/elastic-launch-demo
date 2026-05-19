"""Cloud CDN Service — GCP us-central1. CDN caching, origin pulls, cache invalidation."""

from __future__ import annotations

import random

from app.services.base_service import BaseService
from scenarios.gcp.executive_kpis import emit_executive_business_metrics_if_eligible


class CloudCdnService(BaseService):
    SERVICE_NAME = "cloud-cdn-service"

    BACKENDS = [
        "gcpnet-cdn-backend-01",
        "gcpnet-cdn-backend-02",
        "gcpnet-cdn-backend-03",
    ]
    CACHE_MODES = ["CACHE_ALL_STATIC", "USE_ORIGIN_HEADERS", "FORCE_CACHE_ALL"]

    def generate_telemetry(self) -> None:
        # -- Fault injection --
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Cache hit ratio --
        backend = random.choice(self.BACKENDS)
        hit_ratio = (
            round(random.uniform(80.0, 98.0), 1)
            if not active_channels
            else round(random.uniform(15.0, 45.0), 1)
        )
        miss_rate = (
            random.randint(50, 200)
            if not active_channels
            else random.randint(500, 5000)
        )
        self.emit_metric("cdn.cache_hit_ratio", hit_ratio, "%")
        self.emit_metric("cdn.cache_miss_rate", float(miss_rate), "req/s")

        self.emit_log(
            "INFO",
            f"cloud-cdn: backend={backend} hit_ratio={hit_ratio}% "
            f"miss_rate={miss_rate}/s cache_mode={random.choice(self.CACHE_MODES)}",
            {
                "operation": "cache_stats",
                "cdn.backend": backend,
                "cdn.hit_ratio": hit_ratio,
                "cdn.miss_rate": miss_rate,
            },
        )

        # -- Origin latency --
        origin_latency = (
            round(random.uniform(10.0, 50.0), 1)
            if not active_channels
            else round(random.uniform(200.0, 2000.0), 1)
        )
        origin_errors = (
            random.randint(0, 2) if not active_channels else random.randint(50, 500)
        )
        self.emit_metric("cdn.origin_latency_ms", origin_latency, "ms")
        self.emit_metric("cdn.origin_errors", float(origin_errors), "errors")

        self.emit_log(
            "INFO",
            f"cloud-cdn: origin_latency={origin_latency}ms origin_errors={origin_errors} "
            f"backend={backend} interval=60s",
            {
                "operation": "origin_health",
                "cdn.origin_latency": origin_latency,
                "cdn.origin_errors": origin_errors,
            },
        )

        # -- Bandwidth --
        egress_gbps = round(random.uniform(1.0, 10.0), 2)
        requests_total = random.randint(100000, 500000)
        self.emit_metric("cdn.egress_gbps", egress_gbps, "Gbps")
        self.emit_metric("cdn.requests_total", float(requests_total), "requests")

        self.emit_log(
            "INFO",
            f"cloud-cdn: egress={egress_gbps}Gbps requests={requests_total} "
            f"served_from_cache={round(hit_ratio * requests_total / 100)} interval=60s",
            {
                "operation": "bandwidth_stats",
                "cdn.egress_gbps": egress_gbps,
                "cdn.requests_total": requests_total,
            },
        )

        # -- Cache fill --
        cache_fill_pct = round(random.uniform(60.0, 90.0), 1)
        self.emit_metric("cdn.cache_fill_pct", cache_fill_pct, "%")
        self.emit_log(
            "INFO",
            f"cloud-cdn: cache_fill={cache_fill_pct}% backend={backend} "
            f"ttl_default=3600s signed_urls=enabled",
            {
                "operation": "cache_fill",
                "cdn.cache_fill_pct": cache_fill_pct,
            },
        )

        emit_executive_business_metrics_if_eligible(self)

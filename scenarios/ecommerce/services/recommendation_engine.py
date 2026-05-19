"""Recommendation Engine service — GCP us-central1-b. ML-powered personalization."""

from __future__ import annotations

import random

from app.services.base_service import BaseService


class RecommendationEngineService(BaseService):
    SERVICE_NAME = "recommendation-engine"

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        requests_per_sec = round(random.uniform(2500.0, 8500.0), 1)
        latency_p99_ms = round(random.uniform(45.0, 280.0), 1)
        personalization_hit_rate_pct = round(random.uniform(68.0, 92.0), 2)
        cache_hit_rate_pct = round(random.uniform(80.0, 95.0), 2)

        self.emit_metric("recommendations.requests_per_sec", requests_per_sec, "rps")
        self.emit_metric("recommendations.latency_p99_ms", latency_p99_ms, "ms")
        self.emit_metric("recommendations.personalization_hit_rate_pct", personalization_hit_rate_pct, "%")
        self.emit_metric("recommendations.cache_hit_rate_pct", cache_hit_rate_pct, "%")

        self.emit_log(
            "INFO",
            f"reco.health rps={requests_per_sec} p99_ms={latency_p99_ms} "
            f"hit_rate={personalization_hit_rate_pct}% cache_hit={cache_hit_rate_pct}%",
            {
                "operation": "reco_health",
                "reco.requests_per_sec": requests_per_sec,
                "reco.latency_p99_ms": latency_p99_ms,
                "reco.hit_rate_pct": personalization_hit_rate_pct,
                "reco.cache_hit_rate_pct": cache_hit_rate_pct,
            },
        )

        heap_used_mb = random.randint(2000, 7500)
        heap_max_mb = 10240
        self.emit_log(
            "INFO",
            f"reco.model_health heap_used={heap_used_mb}MB heap_max={heap_max_mb}MB",
            {
                "operation": "model_health",
                "reco.heap_used_mb": heap_used_mb,
                "reco.heap_max_mb": heap_max_mb,
                "reco.heap_utilization_pct": round(heap_used_mb / heap_max_mb * 100, 1),
            },
        )

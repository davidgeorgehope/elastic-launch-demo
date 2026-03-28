"""Content Delivery service — GCP us-central1-b. CDN, video transcoding, Claro TV and Sports."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class ContentDeliveryService(BaseService):
    SERVICE_NAME = "content-delivery"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._requests_served = 0
        self._last_summary = time.time()

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_cdn_request()
        self._emit_transcode_health()

        if time.time() - self._last_summary > 10:
            self._emit_cdn_summary()
            self._last_summary = time.time()

        cache_hit = round(random.uniform(85, 94), 1) if not active_channels else round(random.uniform(8, 20), 1)
        self.emit_metric("content_delivery.cache_hit_rate", cache_hit, "%")
        self.emit_metric("content_delivery.origin_rps", float(random.randint(800, 2000)), "req/s")
        self.emit_metric("content_delivery.video_rebuffer_rate", round(random.uniform(0.1, 0.4), 2), "%")

    def _emit_cdn_request(self) -> None:
        self._requests_served += random.randint(500, 2000)
        pop = random.choice(["SAO-01", "RIO-01", "BOG-01", "MEX-01"])
        content_type = random.choice(["live_stream", "vod_segment", "manifest"])
        self.emit_log(
            "INFO",
            f"[CDN] cache_serve pop={pop} type={content_type} "
            f"cache=HIT ttfb_ms={random.randint(8,42)} bitrate_kbps={random.choice([1200,2400,4800,8000])} status=OK",
            {
                "operation": "cache_serve",
                "cdn.pop": pop,
                "cdn.content_type": content_type,
                "cdn.cache_result": "HIT",
            },
        )

    def _emit_transcode_health(self) -> None:
        workers = random.randint(3, 4)
        queue_depth = random.randint(0, 50)
        self.emit_log(
            "INFO",
            f"[TRANSCODE] worker_health active_workers={workers}/4 queue_depth={queue_depth} "
            f"gpu_util={random.randint(40,75)}% drm_signing=OK status=NOMINAL",
            {
                "operation": "worker_health",
                "transcode.active_workers": workers,
                "transcode.queue_depth": queue_depth,
            },
        )

    def _emit_cdn_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[CDN] cdn_summary requests_served={self._requests_served:,} "
            f"cache_hit=89% live_channels=48 vod_library=280K status=NOMINAL",
            {
                "operation": "cdn_summary",
                "cdn.requests_served": self._requests_served,
            },
        )

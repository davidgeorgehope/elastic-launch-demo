"""Content Delivery service — AWS us-east-1c. CDN edge caching, asset bundles, and patch distribution."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class ContentDeliveryService(BaseService):
    SERVICE_NAME = "content-delivery"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._assets_served = 0
        self._last_cdn_report = time.time()
        self._edge_nodes = ["edge-iad-01", "edge-lax-02", "edge-fra-01", "edge-nrt-01"]
        self._asset_types = [
            "textures-hd",
            "models-characters",
            "audio-sfx",
            "maps-terrain",
            "shaders",
        ]

    def generate_telemetry(self) -> None:
        # ── Fault injection ────────────────────────────────────
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── Normal telemetry ───────────────────────────────────
        self._emit_asset_served()
        self._emit_edge_health()

        if time.time() - self._last_cdn_report > 10:
            self._emit_cdn_summary()
            self._last_cdn_report = time.time()

        # Metrics
        hit_rate = (
            round(random.uniform(92.0, 99.5), 1)
            if not active_channels
            else round(random.uniform(30.0, 70.0), 1)
        )
        self.emit_metric("cdn.cache_hit_rate", hit_rate, "%")
        bandwidth = round(random.uniform(500.0, 5000.0), 1)
        self.emit_metric("cdn.bandwidth_mbps", bandwidth, "Mbps")
        self.emit_metric("cdn.assets_served", float(self._assets_served), "assets")

    def _emit_asset_served(self) -> None:
        self._assets_served += 1
        edge = random.choice(self._edge_nodes)
        asset_type = random.choice(self._asset_types)
        size_mb = round(random.uniform(0.5, 120.0), 1)
        latency_ms = round(random.uniform(5.0, 80.0), 1)
        self.emit_log(
            "INFO",
            f"[CDN] asset_served edge={edge} type={asset_type} size={size_mb}MB latency={latency_ms}ms cache=HIT",
            {
                "operation": "asset_served",
                "cdn.edge_node": edge,
                "cdn.asset_type": asset_type,
                "cdn.size_mb": size_mb,
                "cdn.latency_ms": latency_ms,
                "cdn.cache_status": "HIT",
            },
        )

    def _emit_edge_health(self) -> None:
        edge = random.choice(self._edge_nodes)
        connections = random.randint(500, 10000)
        cpu_pct = round(random.uniform(15.0, 65.0), 1)
        self.emit_log(
            "INFO",
            f"[CDN] edge_health node={edge} connections={connections} cpu={cpu_pct}% bandwidth_gbps=4.2 evictions=0",
            {
                "operation": "edge_health",
                "edge.node": edge,
                "edge.connections": connections,
                "edge.cpu_pct": cpu_pct,
            },
        )

    def _emit_cdn_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[CDN] summary assets_served={self._assets_served} edge_nodes={len(self._edge_nodes)} origin_rps=42 hit_rate=96.2%",
            {
                "operation": "cdn_summary",
                "summary.assets_served": self._assets_served,
                "summary.edge_count": len(self._edge_nodes),
            },
        )

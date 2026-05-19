"""Telemetry Relay service — Azure eastus. Cross-cloud telemetry routing."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class TelemetryRelayService(BaseService):
    SERVICE_NAME = "telemetry-relay"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._frame_count = 0
        self._total_packets = 0
        self._last_relay_summary = time.time()

    ROUTES = [
        ("aws", "gcp"),
        ("aws", "azure"),
        ("gcp", "aws"),
        ("gcp", "azure"),
        ("azure", "aws"),
        ("azure", "gcp"),
    ]

    def generate_telemetry(self) -> None:
        # ── Fault injection ────────────────────────────────────
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── Route telemetry ────────────────────────────────────
        self._frame_count += 1
        for source, dest in random.sample(self.ROUTES, k=3):
            latency = round(random.uniform(5.0, 45.0), 1)
            packets = random.randint(100, 500)
            dropped = random.randint(0, 2)
            self._total_packets += packets

            self.emit_metric(f"relay.latency_{source}_{dest}", latency, "ms")
            self.emit_log(
                "INFO",
                f"[RLY] route={source}->{dest} packets={packets} latency={latency}ms dropped={dropped} status=NOMINAL",
                {
                    "relay.source_cloud": source,
                    "relay.dest_cloud": dest,
                    "relay.latency_ms": latency,
                    "relay.packets": packets,
                    "relay.dropped": dropped,
                    "operation": "relay_route",
                },
            )

        # ── Aggregate metrics ──────────────────────────────────
        total_throughput = round(random.uniform(800.0, 1200.0), 0)
        self.emit_metric("relay.total_throughput", total_throughput, "packets/s")
        self.emit_metric("relay.frame_count", float(self._frame_count), "frames")
        self.emit_metric("relay.total_packets", float(self._total_packets), "packets")

        if time.time() - self._last_relay_summary > 10:
            self.emit_log(
                "INFO",
                f"[RLY] aggregate throughput={total_throughput}pkt/s routes=6 frames={self._frame_count} total_packets={self._total_packets} buffer_util=34% status=NOMINAL",
                {
                    "operation": "relay_summary",
                    "relay.total_throughput": total_throughput,
                    "relay.frame_count": self._frame_count,
                    "relay.total_packets": self._total_packets,
                    "relay.status": "NOMINAL",
                },
            )
            self._last_relay_summary = time.time()
        else:
            self.emit_log(
                "INFO",
                f"[RLY] aggregate throughput={total_throughput}pkt/s routes=6 buffer_util=34% status=NOMINAL",
                {
                    "operation": "relay_summary",
                    "relay.total_throughput": total_throughput,
                    "relay.status": "NOMINAL",
                },
            )

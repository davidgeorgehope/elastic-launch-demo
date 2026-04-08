"""Network Analytics service — GCP us-central1-c. DPI, NetFlow/IPFIX, Flink stream processing."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class NetworkAnalyticsService(BaseService):
    SERVICE_NAME = "network-analytics"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._flows_processed = 0
        self._last_summary = time.time()

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_flow_processing()
        self._emit_dpi_stats()

        if time.time() - self._last_summary > 10:
            self._emit_analytics_summary()
            self._last_summary = time.time()

        lag = float(random.randint(0, 5000)) if not active_channels else float(random.randint(500000, 5000000))
        self.emit_metric("network_analytics.kafka_consumer_lag", lag, "events")
        self.emit_metric("network_analytics.dpi_throughput_gbps", round(random.uniform(18, 38), 1), "Gbps")
        self.emit_metric("network_analytics.flink_backpressure_pct", round(random.uniform(0, 15), 1), "%")

    def _emit_flow_processing(self) -> None:
        self._flows_processed += random.randint(10000, 50000)
        self.emit_log(
            "INFO",
            f"[ANALYTICS] flow_processing flows_total={self._flows_processed:,} "
            f"kafka_lag=1200 flink_checkpoint=OK throughput_gbps={round(random.uniform(20,35),1)} status=NOMINAL",
            {
                "operation": "flow_processing",
                "analytics.flows_total": self._flows_processed,
                "analytics.kafka_lag": random.randint(100, 5000),
            },
        )

    def _emit_dpi_stats(self) -> None:
        classified_pct = round(random.uniform(88, 96), 1)
        self.emit_log(
            "INFO",
            f"[DPI] classification_stats classified={classified_pct}% unknown=4% "
            f"throughput_gbps={round(random.uniform(20,38),1)} sig_age_days=2 status=NOMINAL",
            {
                "operation": "classification_stats",
                "dpi.classified_pct": classified_pct,
                "dpi.sig_age_days": 2,
            },
        )

    def _emit_analytics_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[ANALYTICS] analytics_summary flows_processed={self._flows_processed:,} "
            f"kpi_dashboards_fresh=true noc_alerts_sent=3 status=NOMINAL",
            {
                "operation": "analytics_summary",
                "analytics.flows_processed": self._flows_processed,
            },
        )

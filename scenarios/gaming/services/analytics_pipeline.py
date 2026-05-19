"""Analytics Pipeline service — Azure eastus-2. Event ingestion, player telemetry, and live-ops dashboards."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService
from scenarios.gaming.executive_kpis import emit_executive_business_metrics_if_eligible


class AnalyticsPipelineService(BaseService):
    SERVICE_NAME = "analytics-pipeline"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._events_ingested = 0
        self._last_pipeline_report = time.time()
        self._pipelines = ["events-primary", "events-secondary", "replay-pipeline"]
        self._event_types = [
            "match_complete",
            "player_login",
            "item_purchased",
            "level_up",
            "achievement_unlocked",
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
        self._emit_event_ingested()
        self._emit_pipeline_health()

        if time.time() - self._last_pipeline_report > 10:
            self._emit_pipeline_summary()
            self._last_pipeline_report = time.time()

        # Metrics
        throughput = (
            random.randint(3000, 8000)
            if not active_channels
            else random.randint(100, 2000)
        )
        self.emit_metric("analytics.throughput", float(throughput), "events/s")
        lag_s = (
            round(random.uniform(0.1, 3.0), 1)
            if not active_channels
            else round(random.uniform(30.0, 600.0), 1)
        )
        self.emit_metric("analytics.pipeline_lag_s", lag_s, "s")
        self.emit_metric(
            "analytics.events_ingested", float(self._events_ingested), "events"
        )
        buffer_pct = (
            round(random.uniform(10.0, 60.0), 1)
            if not active_channels
            else round(random.uniform(85.0, 100.0), 1)
        )
        self.emit_metric("analytics.buffer_usage_pct", buffer_pct, "%")

        emit_executive_business_metrics_if_eligible(self)

    def _emit_event_ingested(self) -> None:
        self._events_ingested += random.randint(50, 500)
        pipeline = random.choice(self._pipelines)
        event_type = random.choice(self._event_types)
        batch_size = random.randint(100, 1000)
        latency_ms = round(random.uniform(5.0, 50.0), 1)
        self.emit_log(
            "INFO",
            f"[Analytics] ingest pipeline={pipeline} event_type={event_type} batch={batch_size} latency={latency_ms}ms partitions=16",
            {
                "operation": "event_ingested",
                "analytics.pipeline": pipeline,
                "analytics.event_type": event_type,
                "analytics.batch_size": batch_size,
                "analytics.latency_ms": latency_ms,
            },
        )

    def _emit_pipeline_health(self) -> None:
        pipeline = random.choice(self._pipelines)
        consumer_lag = random.randint(0, 500)
        partitions = random.randint(8, 32)
        self.emit_log(
            "INFO",
            f"[Analytics] pipeline_health name={pipeline} consumer_lag={consumer_lag} partitions={partitions} throughput=4201/s",
            {
                "operation": "pipeline_health",
                "pipeline.name": pipeline,
                "pipeline.consumer_lag": consumer_lag,
                "pipeline.partitions": partitions,
            },
        )

    def _emit_pipeline_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[Analytics] summary events_ingested={self._events_ingested} pipelines={len(self._pipelines)} buffer_pct=32.1% lag_s=0.4",
            {
                "operation": "pipeline_summary",
                "summary.events_ingested": self._events_ingested,
                "summary.pipeline_count": len(self._pipelines),
            },
        )

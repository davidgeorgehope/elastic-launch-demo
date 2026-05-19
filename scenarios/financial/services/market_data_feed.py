"""Market Data Feed service — GCP us-central1-a. Real-time price feeds and quote distribution."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class MarketDataFeedService(BaseService):
    SERVICE_NAME = "market-data-feed"

    FEEDS = {
        "CQS-SIP": {"exchange": "NYSE/NASDAQ", "symbols": 8000},
        "OPRA": {"exchange": "Options", "symbols": 500000},
        "CME-MDP3": {"exchange": "CME", "symbols": 3000},
        "Bloomberg-B-PIPE": {"exchange": "Multi", "symbols": 50000},
        "Reuters-Elektron": {"exchange": "Multi", "symbols": 40000},
    }

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._ticks_processed = 0
        self._last_feed_summary = time.time()

    def generate_telemetry(self) -> None:
        # ── Fault injection ────────────────────────────────────
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── Normal telemetry ───────────────────────────────────
        self._emit_tick_processing()
        self._emit_feed_health()

        if time.time() - self._last_feed_summary > 10:
            self._emit_feed_summary()
            self._last_feed_summary = time.time()

        # Metrics
        tps = (
            random.randint(50000, 200000)
            if not active_channels
            else random.randint(5000, 20000)
        )
        self.emit_metric("market_data.ticks_per_second", float(tps), "tps")
        self.emit_metric(
            "market_data.feed_latency_us", float(random.randint(10, 500)), "us"
        )
        self.emit_metric(
            "market_data.active_subscriptions",
            float(random.randint(5000, 50000)),
            "subscriptions",
        )

    def _emit_tick_processing(self) -> None:
        self._ticks_processed += random.randint(1000, 10000)
        feed = random.choice(list(self.FEEDS.keys()))
        feed_info = self.FEEDS[feed]
        latency_us = random.randint(10, 200)
        symbol = random.choice(["AAPL", "GOOGL", "MSFT", "AMZN", "SPY", "QQQ"])
        price = round(random.uniform(100.0, 500.0), 4)
        self.emit_log(
            "INFO",
            f"[MDF] tick_processed symbol={symbol} price=${price} feed={feed} exchange={feed_info['exchange']} latency_us={latency_us}",
            {
                "operation": "tick_process",
                "tick.symbol": symbol,
                "tick.price": price,
                "tick.feed": feed,
                "tick.exchange": feed_info["exchange"],
                "tick.latency_us": latency_us,
            },
        )

    def _emit_feed_health(self) -> None:
        feed = random.choice(list(self.FEEDS.keys()))
        gap_count = random.randint(0, 2)
        self.emit_log(
            "INFO",
            f"[MDF] feed_health feed={feed} gaps_60s={gap_count} status=CONNECTED",
            {
                "operation": "feed_health",
                "feed.name": feed,
                "feed.gap_count": gap_count,
                "feed.status": "CONNECTED",
            },
        )

    def _emit_feed_summary(self) -> None:
        active_feeds = len(self.FEEDS)
        self.emit_log(
            "INFO",
            f"[MDF] feed_summary active_feeds={active_feeds} total_ticks={self._ticks_processed} status=NOMINAL",
            {
                "operation": "feed_summary",
                "summary.active_feeds": active_feeds,
                "summary.total_ticks": self._ticks_processed,
                "summary.status": "NOMINAL",
            },
        )

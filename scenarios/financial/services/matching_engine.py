"""Matching Engine service — AWS us-east-1b. Ultra-low-latency order matching."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class MatchingEngineService(BaseService):
    SERVICE_NAME = "matching-engine"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._matches_total = 0
        self._last_book_snapshot = time.time()
        self._instruments = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "JPM", "GS"]

    def generate_telemetry(self) -> None:
        # ── Fault injection ────────────────────────────────────
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── Normal telemetry ───────────────────────────────────
        self._emit_match_event()
        self._emit_book_depth()

        if time.time() - self._last_book_snapshot > 8:
            self._emit_book_snapshot()
            self._last_book_snapshot = time.time()

        # Metrics
        latency = (
            random.randint(5, 80) if not active_channels else random.randint(500, 50000)
        )
        self.emit_metric("matching_engine.match_latency_us", float(latency), "us")
        self.emit_metric(
            "matching_engine.matches_total", float(self._matches_total), "trades"
        )
        self.emit_metric(
            "matching_engine.order_book_depth",
            float(random.randint(500, 5000)),
            "levels",
        )

    def _emit_match_event(self) -> None:
        self._matches_total += 1
        instrument = random.choice(self._instruments)
        price = round(random.uniform(100.0, 400.0), 2)
        qty = random.randint(100, 2000)
        latency_us = random.randint(5, 80)
        self.emit_log(
            "INFO",
            f"[ME] trade_match instrument={instrument} qty={qty} price=${price} latency_us={latency_us} status=FILLED",
            {
                "operation": "trade_match",
                "trade.instrument": instrument,
                "trade.price": price,
                "trade.quantity": qty,
                "trade.latency_us": latency_us,
                "trade.status": "FILLED",
            },
        )

    def _emit_book_depth(self) -> None:
        instrument = random.choice(self._instruments)
        bid_levels = random.randint(50, 200)
        ask_levels = random.randint(50, 200)
        spread_bps = round(random.uniform(0.5, 3.0), 2)
        self.emit_log(
            "INFO",
            f"[ME] book_depth instrument={instrument} bid_levels={bid_levels} ask_levels={ask_levels} spread_bps={spread_bps}",
            {
                "operation": "book_depth",
                "book.instrument": instrument,
                "book.bid_levels": bid_levels,
                "book.ask_levels": ask_levels,
                "book.spread_bps": spread_bps,
            },
        )

    def _emit_book_snapshot(self) -> None:
        total_instruments = len(self._instruments)
        self.emit_log(
            "INFO",
            f"[ME] book_snapshot instruments={total_instruments} total_matches={self._matches_total} status=NOMINAL",
            {
                "operation": "book_snapshot",
                "snapshot.instrument_count": total_instruments,
                "snapshot.total_matches": self._matches_total,
                "snapshot.status": "NOMINAL",
            },
        )

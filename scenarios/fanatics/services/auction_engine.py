"""Auction Engine service — AWS us-east-1c. Real-time bidding and auction management."""

from __future__ import annotations

import random

from app.services.base_service import BaseService


class AuctionEngineService(BaseService):
    SERVICE_NAME = "auction-engine"

    def generate_telemetry(self) -> None:
        # -- Fault injection --
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Auction metrics --
        active_auctions = random.randint(50, 250)
        bids_per_min = random.randint(200, 1500)
        bid_latency_ms = round(random.uniform(8.0, 45.0), 1)
        websocket_connections = random.randint(2000, 8000)

        self.emit_metric("auction.active_auctions", float(active_auctions), "auctions")
        self.emit_metric("auction.bids_per_min", float(bids_per_min), "bids/min")
        self.emit_metric("auction.bid_latency_ms", bid_latency_ms, "ms")
        self.emit_metric(
            "auction.websocket_connections", float(websocket_connections), "connections"
        )

        self.emit_log(
            "INFO",
            f"level=info ts=2025-01-15T14:32:01.234Z caller=auction.go:47 "
            f'msg="health" active_auctions={active_auctions} bids_per_min={bids_per_min} '
            f"latency_ms={bid_latency_ms} ws_connections={websocket_connections}",
            {
                "operation": "auction_health",
                "auction.active_count": active_auctions,
                "auction.bids_per_min": bids_per_min,
                "auction.latency_ms": bid_latency_ms,
                "auction.ws_connections": websocket_connections,
            },
        )

        # Bid processing summary
        self.emit_log(
            "INFO",
            'level=info ts=2025-01-15T14:32:01.456Z caller=pipeline.go:112 msg="pipeline_check" '
            "status=healthy queues_draining=true",
            {"operation": "pipeline_check", "check.result": "PASS"},
        )

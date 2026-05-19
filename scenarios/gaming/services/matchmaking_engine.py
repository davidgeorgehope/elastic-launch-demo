"""Matchmaking Engine service — AWS us-east-1b. Player queuing, skill-based matching, and lobby formation."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class MatchmakingEngineService(BaseService):
    SERVICE_NAME = "matchmaking-engine"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._matches_formed = 0
        self._last_queue_report = time.time()
        self._queues = ["ranked-solo", "ranked-duo", "casual-squad", "tournament-5v5"]

    def generate_telemetry(self) -> None:
        # ── Fault injection ────────────────────────────────────
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── Normal telemetry ───────────────────────────────────
        self._emit_match_formed()
        self._emit_queue_status()

        if time.time() - self._last_queue_report > 10:
            self._emit_queue_summary()
            self._last_queue_report = time.time()

        # Metrics
        queue_depth = (
            random.randint(200, 3000)
            if not active_channels
            else random.randint(8000, 50000)
        )
        self.emit_metric("matchmaking.queue_depth", float(queue_depth), "players")
        avg_wait = (
            random.uniform(8.0, 30.0)
            if not active_channels
            else random.uniform(60.0, 300.0)
        )
        self.emit_metric("matchmaking.avg_wait_time_s", round(avg_wait, 1), "s")
        self.emit_metric(
            "matchmaking.matches_formed", float(self._matches_formed), "matches"
        )

    def _emit_match_formed(self) -> None:
        self._matches_formed += 1
        queue = random.choice(self._queues)
        team_size = random.choice([1, 2, 4, 5])
        avg_mmr = random.randint(800, 3500)
        mmr_spread = random.randint(20, 200)
        wait_s = round(random.uniform(5.0, 45.0), 1)
        self.emit_log(
            "INFO",
            f"[MM] match_formed pool={queue} teams={team_size}v{team_size} avg_mmr={avg_mmr} spread={mmr_spread} wait={wait_s}s status=READY",
            {
                "operation": "match_formed",
                "match.queue": queue,
                "match.team_size": team_size,
                "match.avg_mmr": avg_mmr,
                "match.mmr_spread": mmr_spread,
                "match.wait_seconds": wait_s,
            },
        )

    def _emit_queue_status(self) -> None:
        queue = random.choice(self._queues)
        depth = random.randint(100, 2000)
        avg_wait = round(random.uniform(5.0, 35.0), 1)
        self.emit_log(
            "INFO",
            f"[MM] queue_status pool={queue} depth={depth} avg_wait={avg_wait}s dequeue_rate=12/s",
            {
                "operation": "queue_status",
                "queue.name": queue,
                "queue.depth": depth,
                "queue.avg_wait_s": avg_wait,
            },
        )

    def _emit_queue_summary(self) -> None:
        total_waiting = random.randint(500, 5000)
        self.emit_log(
            "INFO",
            f"[MM] summary matches_formed={self._matches_formed} total_waiting={total_waiting} pools=4 avg_quality=0.87",
            {
                "operation": "queue_summary",
                "summary.matches_formed": self._matches_formed,
                "summary.total_waiting": total_waiting,
            },
        )

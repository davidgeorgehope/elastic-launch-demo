"""Leaderboard API service — GCP us-central1-b. Ranking, season progression, and reward distribution."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class LeaderboardApiService(BaseService):
    SERVICE_NAME = "leaderboard-api"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._rank_updates = 0
        self._last_board_snapshot = time.time()
        self._boards = [
            "ranked-global",
            "seasonal-solo",
            "guild-wars",
            "tournament-finals",
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
        self._emit_rank_update()
        self._emit_season_progress()

        if time.time() - self._last_board_snapshot > 10:
            self._emit_board_snapshot()
            self._last_board_snapshot = time.time()

        # Metrics
        query_latency = (
            round(random.uniform(2.0, 15.0), 1)
            if not active_channels
            else round(random.uniform(50.0, 500.0), 1)
        )
        self.emit_metric("leaderboard.query_latency_ms", query_latency, "ms")
        self.emit_metric(
            "leaderboard.rank_updates", float(self._rank_updates), "updates"
        )
        total_entries = random.randint(500000, 2000000)
        self.emit_metric("leaderboard.total_entries", float(total_entries), "entries")

    def _emit_rank_update(self) -> None:
        self._rank_updates += 1
        board = random.choice(self._boards)
        player_id = f"PLR-{random.randint(100000, 999999)}"
        old_rank = random.randint(2, 5000)
        new_rank = max(1, old_rank + random.randint(-50, 50))
        score = random.randint(1000, 50000)
        self.emit_log(
            "INFO",
            f"[LB] rank_update board={board} player={player_id} old_rank={old_rank} new_rank={new_rank} score={score} zset_ops=2",
            {
                "operation": "rank_update",
                "leaderboard.board": board,
                "leaderboard.player_id": player_id,
                "leaderboard.old_rank": old_rank,
                "leaderboard.new_rank": new_rank,
                "leaderboard.score": score,
            },
        )

    def _emit_season_progress(self) -> None:
        player_id = f"PLR-{random.randint(100000, 999999)}"
        tier = random.randint(1, 100)
        xp_gained = random.randint(50, 5000)
        season = f"S{random.randint(1, 12)}"
        self.emit_log(
            "INFO",
            f"[LB] season_progress season={season} player={player_id} tier={tier} xp_gained={xp_gained} premium=true",
            {
                "operation": "season_progress",
                "season.id": season,
                "season.player_id": player_id,
                "season.tier": tier,
                "season.xp_gained": xp_gained,
            },
        )

    def _emit_board_snapshot(self) -> None:
        self.emit_log(
            "INFO",
            f"[LB] snapshot rank_updates={self._rank_updates} boards={len(self._boards)} redis_mem=142MB consistency=OK",
            {
                "operation": "board_snapshot",
                "snapshot.rank_updates": self._rank_updates,
                "snapshot.board_count": len(self._boards),
            },
        )

"""Game Server service — AWS us-east-1a. Authoritative game loop, physics, and state replication."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class GameServerService(BaseService):
    SERVICE_NAME = "game-server"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._tick_count = 0
        self._last_perf_report = time.time()
        self._active_matches = random.randint(80, 200)
        self._regions = ["US-E", "US-W", "EU-W", "AP-SE"]

    def generate_telemetry(self) -> None:
        # ── Fault injection ────────────────────────────────────
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── Normal telemetry ───────────────────────────────────
        self._emit_tick_cycle()
        self._emit_player_action()

        if time.time() - self._last_perf_report > 10:
            self._emit_performance_report()
            self._last_perf_report = time.time()

        # Metrics
        tick_rate = (
            64.0 if not active_channels else round(random.uniform(18.0, 45.0), 1)
        )
        self.emit_metric("game_server.tick_rate", tick_rate, "Hz")
        self.emit_metric(
            "game_server.active_matches", float(self._active_matches), "matches"
        )
        connected = self._active_matches * random.randint(4, 10)
        self.emit_metric("game_server.connected_players", float(connected), "players")
        frame_time = round(1000.0 / max(tick_rate, 1), 1)
        self.emit_metric("game_server.frame_time_ms", frame_time, "ms")

    def _emit_tick_cycle(self) -> None:
        self._tick_count += 1
        region = random.choice(self._regions)
        players_in_tick = random.randint(200, 2000)
        entities = random.randint(500, 5000)
        self.emit_log(
            "INFO",
            f"[Net] tick={self._tick_count} players={players_in_tick} entities={entities} region={region} server_fps=62.8 status=RUNNING",
            {
                "operation": "tick_cycle",
                "tick.number": self._tick_count,
                "tick.players": players_in_tick,
                "tick.entities": entities,
                "tick.region": region,
            },
        )

    def _emit_player_action(self) -> None:
        action = random.choice(["move", "shoot", "interact", "ability", "reload"])
        latency_ms = round(random.uniform(5.0, 45.0), 1)
        match_id = f"MATCH-{random.randint(100000, 999999)}"
        self.emit_log(
            "INFO",
            f"[Engine] action={action} latency={latency_ms}ms match={match_id} result=ACK input_seq={random.randint(10000, 99999)}",
            {
                "operation": "player_action",
                "action.type": action,
                "action.latency_ms": latency_ms,
                "action.match_id": match_id,
            },
        )

    def _emit_performance_report(self) -> None:
        self._active_matches = max(50, self._active_matches + random.randint(-10, 10))
        self.emit_log(
            "INFO",
            f"[Engine] perf_report active_matches={self._active_matches} total_ticks={self._tick_count} regions=4/4 gc_pause_ms=0.3 heap_mb=1204",
            {
                "operation": "perf_report",
                "perf.active_matches": self._active_matches,
                "perf.total_ticks": self._tick_count,
            },
        )

"""Chat Service — GCP us-central1-a. Real-time text and voice chat, channel management."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class ChatServiceService(BaseService):
    SERVICE_NAME = "chat-service"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._messages_processed = 0
        self._last_channel_report = time.time()
        self._channels = [
            "global-en",
            "guild-12345",
            "match-lobby",
            "trade-market",
            "lfg-ranked",
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
        self._emit_message_routed()
        self._emit_voice_status()

        if time.time() - self._last_channel_report > 10:
            self._emit_channel_summary()
            self._last_channel_report = time.time()

        # Metrics
        msg_rate = (
            random.randint(50, 400)
            if not active_channels
            else random.randint(800, 5000)
        )
        self.emit_metric("chat.message_rate", float(msg_rate), "msg/s")
        active_users = random.randint(5000, 50000)
        self.emit_metric("chat.active_users", float(active_users), "users")
        voice_channels = random.randint(200, 2000)
        self.emit_metric(
            "chat.voice_channels_active", float(voice_channels), "channels"
        )

    def _emit_message_routed(self) -> None:
        self._messages_processed += 1
        channel = random.choice(self._channels)
        latency_ms = round(random.uniform(1.0, 15.0), 1)
        self.emit_log(
            "INFO",
            f"[Chat] msg_routed channel={channel} latency={latency_ms}ms delivery=OK subscribers=247",
            {
                "operation": "message_routed",
                "chat.channel": channel,
                "chat.latency_ms": latency_ms,
                "chat.delivery_status": "OK",
            },
        )

    def _emit_voice_status(self) -> None:
        voice_id = f"VC-{random.randint(10000, 99999)}"
        participants = random.randint(2, 20)
        bitrate_kbps = random.choice([48, 64, 96, 128])
        packet_loss = round(random.uniform(0.0, 1.5), 2)
        self.emit_log(
            "INFO",
            f"[Voice] channel={voice_id} participants={participants} bitrate={bitrate_kbps}kbps loss={packet_loss}% codec=opus MOS=4.2",
            {
                "operation": "voice_status",
                "voice.channel_id": voice_id,
                "voice.participants": participants,
                "voice.bitrate_kbps": bitrate_kbps,
                "voice.packet_loss_pct": packet_loss,
            },
        )

    def _emit_channel_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[Chat] summary msgs_processed={self._messages_processed} channels={len(self._channels)} mod_queue=12 voice_active=84",
            {
                "operation": "channel_summary",
                "summary.messages_processed": self._messages_processed,
                "summary.channel_count": len(self._channels),
            },
        )

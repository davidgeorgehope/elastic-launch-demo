"""SMS Gateway service — AWS us-east-1c. SMSC, SMPP server, A2P messaging."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class SmsGatewayService(BaseService):
    SERVICE_NAME = "sms-gateway"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._messages_sent = 0
        self._last_summary = time.time()

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_sms_delivery()
        self._emit_smpp_session()

        if time.time() - self._last_summary > 10:
            self._emit_smsc_summary()
            self._last_summary = time.time()

        queue = float(random.randint(0, 10000)) if not active_channels else float(random.randint(80000, 180000))
        self.emit_metric("sms_gateway.smsc_queue_depth", queue, "messages")
        self.emit_metric("sms_gateway.delivery_rate", round(random.uniform(98.5, 99.8), 2), "%")
        self.emit_metric("sms_gateway.smpp_active_sessions", float(random.randint(200, 450)), "sessions")

    def _emit_sms_delivery(self) -> None:
        self._messages_sent += random.randint(50, 200)
        msg_type = random.choice(["P2P", "P2P", "P2P", "A2P"])
        self.emit_log(
            "INFO",
            f"[SMS] message_delivery type={msg_type} delivered={self._messages_sent} "
            f"delivery_rate=99.4% hlr_latency_ms={random.randint(20,80)} status=DELIVERED",
            {
                "operation": "message_delivery",
                "sms.msg_type": msg_type,
                "sms.delivered": self._messages_sent,
            },
        )

    def _emit_smpp_session(self) -> None:
        system_id = f"esme-{random.choice(['mktg','crm','bank'])}-{random.randint(1,5)}"
        tps = random.randint(100, 800)
        self.emit_log(
            "INFO",
            f"[SMPP] session_health system_id={system_id} bind=ACTIVE "
            f"tps={tps} quota_used=42% status=NOMINAL",
            {
                "operation": "session_health",
                "smpp.system_id": system_id,
                "smpp.tps": tps,
            },
        )

    def _emit_smsc_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[SMSC] smsc_summary total_delivered={self._messages_sent} "
            f"queue_fill=8% spam_blocked=24 a2p_campaigns=3 status=NOMINAL",
            {
                "operation": "smsc_summary",
                "smsc.total_delivered": self._messages_sent,
            },
        )

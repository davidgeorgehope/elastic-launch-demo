"""SCADA Gateway service — AWS us-east-1b. OPC-UA / Modbus / EtherNet-IP bridge to PLCs and HMIs."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class SCADAGatewayService(BaseService):
    SERVICE_NAME = "scada-gateway"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._tag_updates_total = 0
        self._last_subscription_report = time.time()
        self._plcs = ["PLC-LINE01-A", "PLC-LINE02-A", "PLC-LINE03-A", "PLC-LINE03-B", "PLC-PACK-01"]
        self._protocols = ["opcua", "opcua", "opcua", "modbus_tcp", "ethernet_ip"]

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_tag_update()
        self._emit_session_health()

        if time.time() - self._last_subscription_report > 10:
            self._emit_subscription_summary()
            self._last_subscription_report = time.time()

        self._tag_updates_total += random.randint(50, 200)
        self.emit_metric("scada.tag_updates_total", float(self._tag_updates_total), "updates")
        rate = (
            random.randint(800, 1500)
            if not active_channels
            else random.randint(15_000, 60_000)
        )
        self.emit_metric("scada.tag_update_rate_per_s", float(rate), "updates/s")
        self.emit_metric("scada.active_subscriptions", float(random.randint(180, 320)), "subs")

    def _emit_tag_update(self) -> None:
        plc = random.choice(self._plcs)
        protocol = random.choice(self._protocols)
        tag = random.choice(["MotorSpeed", "OvenTempC", "ConveyorRPM", "PressurePsi", "PartsCounter"])
        value = round(random.uniform(0.0, 1500.0), 2)
        self.emit_log(
            "INFO",
            f"[SCADA] tag_update plc={plc} protocol={protocol} tag={tag} value={value} quality=GOOD",
            {
                "operation": "tag_update",
                "scada.plc": plc,
                "scada.protocol": protocol,
                "scada.tag_name": tag,
                "scada.value": value,
                "scada.quality": "GOOD",
            },
        )

    def _emit_session_health(self) -> None:
        plc = random.choice(self._plcs)
        rtt_ms = random.randint(2, 18)
        self.emit_log(
            "DEBUG",
            f"[SCADA] session_keepalive plc={plc} rtt_ms={rtt_ms} secure_channel=ACTIVE",
            {
                "operation": "session_keepalive",
                "scada.plc": plc,
                "scada.rtt_ms": rtt_ms,
            },
        )

    def _emit_subscription_summary(self) -> None:
        active = random.randint(180, 320)
        self.emit_log(
            "INFO",
            f"[SCADA] subscription_summary active={active} total_tags={active * random.randint(8, 24)} health=NOMINAL",
            {
                "operation": "subscription_summary",
                "scada.active_subscriptions": active,
            },
        )

"""IoT Connect service — Azure eastus-2. MQTT broker, device registry, PKI certificate management."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class IotConnectService(BaseService):
    SERVICE_NAME = "iot-connect"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._messages_processed = 0
        self._last_summary = time.time()

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_mqtt_stats()
        self._emit_cert_health()

        if time.time() - self._last_summary > 10:
            self._emit_iot_summary()
            self._last_summary = time.time()

        connections = float(random.randint(280000, 420000)) if not active_channels else float(random.randint(490000, 500000))
        self.emit_metric("iot_connect.mqtt_connections", connections, "connections")
        self.emit_metric("iot_connect.message_throughput", float(random.randint(50000, 200000)), "msg/s")
        self.emit_metric("iot_connect.cert_expiry_7d", float(random.randint(0, 500)), "devices")

    def _emit_mqtt_stats(self) -> None:
        self._messages_processed += random.randint(1000, 5000)
        device_type = random.choice(["smart_meter", "industrial_sensor", "connected_vehicle", "consumer_iot"])
        self.emit_log(
            "INFO",
            f"[MQTT] broker_stats connections={random.randint(280000,420000):,} "
            f"msg_rate={random.randint(50000,150000):,}/s device_type={device_type} qos1_queue=12MB status=NOMINAL",
            {
                "operation": "broker_stats",
                "mqtt.device_type": device_type,
                "mqtt.messages_processed": self._messages_processed,
            },
        )

    def _emit_cert_health(self) -> None:
        valid_pct = round(random.uniform(96, 99), 1)
        self.emit_log(
            "INFO",
            f"[PKI] cert_health valid_pct={valid_pct}% expiring_7d=120 "
            f"ocsp_latency_ms=42 ca_status=ONLINE status=NOMINAL",
            {
                "operation": "cert_health",
                "pki.valid_pct": valid_pct,
                "pki.expiring_7d": 120,
            },
        )

    def _emit_iot_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[IOT] iot_summary connected_devices=5.2M messages_today={self._messages_processed:,} "
            f"critical_devices_online=99.99% cert_rotations_today=240 status=NOMINAL",
            {
                "operation": "iot_summary",
                "iot.connected_devices": 5200000,
                "iot.messages_today": self._messages_processed,
            },
        )

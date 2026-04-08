"""Voice Platform service — Azure eastus-1. IMS core, SIP trunks, VoIP SBC."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class VoicePlatformService(BaseService):
    SERVICE_NAME = "voice-platform"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._calls_processed = 0
        self._last_summary = time.time()

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_sip_call()
        self._emit_ims_health()

        if time.time() - self._last_summary > 10:
            self._emit_voice_summary()
            self._last_summary = time.time()

        trunk_util = round(random.uniform(30, 65), 1) if not active_channels else round(random.uniform(92, 99), 1)
        self.emit_metric("voice_platform.sip_trunk_utilization_pct", trunk_util, "%")
        self.emit_metric("voice_platform.active_calls", float(random.randint(800, 1800)), "calls")
        self.emit_metric("voice_platform.ims_reg_rate", float(random.randint(1500, 2200)), "reg/s")

    def _emit_sip_call(self) -> None:
        self._calls_processed += 1
        codec = random.choice(["G.711", "G.722", "OPUS"])
        mos = round(random.uniform(4.0, 4.5), 2)
        self.emit_log(
            "INFO",
            f"[SIP] call_established codec={codec} mos={mos} "
            f"duration_s={random.randint(30,300)} sbc=claro-sbc-azure-01 status=ACTIVE",
            {
                "operation": "call_established",
                "sip.codec": codec,
                "sip.mos": mos,
            },
        )

    def _emit_ims_health(self) -> None:
        registrations = random.randint(18000000, 22000000)
        self.emit_log(
            "INFO",
            f"[IMS] ims_health p_cscf=UP s_cscf=UP hss=UP "
            f"registrations={registrations:,} reg_rate=1980/s status=NOMINAL",
            {
                "operation": "ims_health",
                "ims.registrations": registrations,
                "ims.reg_rate": 1980,
            },
        )

    def _emit_voice_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[VOICE] voice_summary calls_today={self._calls_processed * 1000} "
            f"avg_mos=4.2 sip_503_rate=0.02% trunk_util=52% status=NOMINAL",
            {
                "operation": "voice_summary",
                "voice.calls_today": self._calls_processed * 1000,
            },
        )

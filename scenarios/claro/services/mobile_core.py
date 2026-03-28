"""Mobile Core service — AWS us-east-1a. 5G/4G packet core: AMF, SMF, UPF, MME."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class MobileCoreService(BaseService):
    SERVICE_NAME = "mobile-core"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._session_count = 0
        self._last_summary = time.time()

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        self._emit_pdu_session()
        self._emit_ran_stats()

        if time.time() - self._last_summary > 10:
            self._emit_core_summary()
            self._last_summary = time.time()

        latency_ms = round(random.uniform(5, 80), 1) if not active_channels else round(random.uniform(800, 8000), 1)
        self.emit_metric("mobile_core.pdu_session_latency_ms", latency_ms, "ms")
        self.emit_metric("mobile_core.active_sessions_5g", float(random.randint(800000, 2000000)), "sessions")
        self.emit_metric("mobile_core.active_sessions_lte", float(random.randint(5000000, 12000000)), "sessions")
        self.emit_metric("mobile_core.handover_success_rate", round(random.uniform(98.5, 99.9), 2), "%")

    def _emit_pdu_session(self) -> None:
        self._session_count += 1
        country = random.choice(["BR", "CO", "AR", "MX", "CL"])
        dnn = random.choice(["internet", "ims", "emergency"])
        self.emit_log(
            "INFO",
            f"[5G] pdu_session_create imsi=724{random.randint(10,99)}{random.randint(100000000,999999999)} "
            f"dnn={dnn} country={country} status=ESTABLISHED latency_ms={random.randint(20,120)}",
            {
                "operation": "pdu_session_create",
                "mobile.dnn": dnn,
                "mobile.country": country,
                "mobile.session_count": self._session_count,
            },
        )

    def _emit_ran_stats(self) -> None:
        enb_id = f"eNB-{random.randint(10000, 99999)}"
        prb_util = round(random.uniform(30, 75), 1)
        self.emit_log(
            "INFO",
            f"[RAN] cell_stats enb={enb_id} prb_util={prb_util}% ho_success=99.4% "
            f"cqi_avg=12 sinr_db=18.4 status=NOMINAL",
            {
                "operation": "cell_stats",
                "ran.enb_id": enb_id,
                "ran.prb_util": prb_util,
            },
        )

    def _emit_core_summary(self) -> None:
        self.emit_log(
            "INFO",
            f"[CORE] nf_health amf=UP smf=UP upf=UP nrf=UP pcf=UP "
            f"total_sessions={self._session_count * 1000} status=NOMINAL",
            {
                "operation": "nf_health",
                "core.total_sessions": self._session_count * 1000,
            },
        )

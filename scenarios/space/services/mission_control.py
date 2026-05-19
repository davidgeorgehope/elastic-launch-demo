"""Mission Control service — AWS us-east-1. Orchestrates launch sequence."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService
from scenarios.space.executive_kpis import emit_executive_business_metrics_if_eligible


class MissionControlService(BaseService):
    SERVICE_NAME = "mission-control"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._last_health_summary = time.time()
        self._subsystem_poll_idx = 0
        self._subsystems = [
            "propulsion",
            "guidance",
            "communications",
            "payload",
            "relay",
            "ground",
            "validation",
            "safety",
        ]

    def generate_telemetry(self) -> None:
        # ── Check for active faults (this is a cascade target) ──
        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── Normal telemetry ───────────────────────────────────
        self._emit_subsystem_poll()
        self._emit_phase_log()

        if time.time() - self._last_health_summary > 10:
            self._emit_health_summary()
            self._last_health_summary = time.time()

        # Metrics
        self.emit_metric(
            "mission_control.subsystem_polls",
            self._subsystem_poll_idx,
            "polls",
        )
        self.emit_metric(
            "mission_control.active_alerts",
            float(len(cascade_channels)),
            "alerts",
        )

        emit_executive_business_metrics_if_eligible(self)

    def _emit_subsystem_poll(self) -> None:
        subsystem = self._subsystems[self._subsystem_poll_idx % len(self._subsystems)]
        self._subsystem_poll_idx += 1
        latency = round(random.uniform(1.2, 8.5), 1)
        self.emit_log(
            "INFO",
            f"[MCC] subsystem={subsystem} poll_latency={latency}ms response=ACK status=NOMINAL",
            {
                "operation": "subsystem_poll",
                "target.subsystem": subsystem,
                "poll.latency_ms": latency,
                "poll.result": "NOMINAL",
            },
        )

    def _emit_phase_log(self) -> None:
        phases_messages = {
            "PRE-LAUNCH": [
                "[MCC] phase=PRE-LAUNCH checks=IN_PROGRESS systems=ALL_REPORTING status=NOMINAL",
                "[MCC] phase=PRE-LAUNCH vehicle_pwr=NOMINAL telem_links=ACTIVE status=GO",
                "[MCC] phase=PRE-LAUNCH readiness_review=UNDERWAY director=CONFIRMED status=NOMINAL",
            ],
            "COUNTDOWN": [
                "[MCC] phase=COUNTDOWN sequence=ACTIVE subsystems=MONITORING status=NOMINAL",
                "[MCC] phase=COUNTDOWN go_nogo_poll=IN_PROGRESS responses=PENDING status=NOMINAL",
                "[MCC] phase=COUNTDOWN verification=FINAL systems=ALL_GO status=NOMINAL",
            ],
            "LAUNCH": [
                "[MCC] phase=LAUNCH event=MECO_IGNITION engines=ALL_NOMINAL status=GO",
                "[MCC] phase=LAUNCH event=TOWER_CLEAR engines=NOMINAL thrust=100% status=GO",
                "[MCC] phase=LAUNCH thrust=NOMINAL trajectory=ON_PROFILE status=GO",
            ],
            "ASCENT": [
                "[MCC] phase=ASCENT event=MAX_Q structural_loads=NOMINAL status=GO",
                "[MCC] phase=ASCENT event=STAGE_SEP_APPROACH systems=ALL_GO status=NOMINAL",
                "[MCC] phase=ASCENT telemetry=NOMINAL tracking=STABLE status=GO",
            ],
        }
        messages = phases_messages.get(self._phase, phases_messages["PRE-LAUNCH"])
        self.emit_log("INFO", random.choice(messages), {"operation": "phase_status"})

    def _emit_health_summary(self) -> None:
        active = self.get_cascade_channels_for_service()
        status = "NOMINAL" if not active else "DEGRADED"
        self.emit_log(
            "INFO",
            f"[MCC] health_check subsystems={len(self._subsystems)} alerts={len(active)} overall={status}",
            {
                "operation": "health_summary",
                "health.subsystem_count": len(self._subsystems),
                "health.overall_status": status,
                "health.active_alerts": len(active),
            },
        )

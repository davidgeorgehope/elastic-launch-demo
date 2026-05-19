"""Sensor Validator service — Azure eastus. PRIMARY FAULT TARGET.

Validates sensor readings against calibration baselines.
Has fault injection logic for all 20 channels.
"""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class SensorValidatorService(BaseService):
    SERVICE_NAME = "sensor-validator"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._validation_count = 0
        self._last_pipeline_report = time.time()

    VALIDATION_SENSORS = [
        "thermal",
        "pressure",
        "flow_rate",
        "gps",
        "imu",
        "star_tracker",
        "rf_signal",
        "packet_integrity",
        "antenna_position",
        "vibration",
        "electrical",
        "weather",
        "hydraulic",
        "pipeline_health",
        "calibration",
        "safety_system",
        "radar_tracking",
        "network_latency",
        "data_integrity",
    ]

    def generate_telemetry(self) -> None:
        # ── Fault injection — this is the primary fault target ──
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)
            self._emit_validation_failure(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── Normal validation passes ───────────────────────────
        sensors_to_validate = random.sample(
            self.VALIDATION_SENSORS, k=min(5, len(self.VALIDATION_SENSORS))
        )
        for sensor_type in sensors_to_validate:
            confidence = round(random.uniform(0.95, 1.0), 4)
            epoch = int(time.time()) - random.randint(0, 3600)
            self.emit_log(
                "INFO",
                f"[VV] validate sensor={sensor_type} epoch={epoch} confidence={confidence} result=PASS status=NOMINAL",
                {
                    "validation.result": "PASS",
                    "validation.sensor_type": sensor_type,
                    "validation.calibration_epoch": epoch,
                    "validation.confidence": confidence,
                    "operation": "sensor_validation",
                },
            )

        # ── Metrics ────────────────────────────────────────────
        self._validation_count += len(sensors_to_validate)
        validations_per_sec = round(random.uniform(45.0, 65.0), 1)
        queue_depth = random.randint(0, 20)
        self.emit_metric(
            "sensor_validator.validations_per_sec", validations_per_sec, "validations/s"
        )
        self.emit_metric("sensor_validator.queue_depth", float(queue_depth), "items")
        self.emit_metric(
            "sensor_validator.total_validations", float(self._validation_count), "validations"
        )

        if time.time() - self._last_pipeline_report > 10:
            self.emit_log(
                "INFO",
                f"[VV] pipeline_status rate={validations_per_sec}/s queue_depth={queue_depth} total={self._validation_count} status=NOMINAL",
                {
                    "operation": "pipeline_health",
                    "validation.rate": validations_per_sec,
                    "validation.queue_depth": queue_depth,
                    "validation.total_count": self._validation_count,
                },
            )
            self._last_pipeline_report = time.time()
        else:
            self.emit_log(
                "INFO",
                f"[VV] pipeline_status rate={validations_per_sec}/s queue_depth={queue_depth} status=NOMINAL",
                {
                    "operation": "pipeline_health",
                    "validation.rate": validations_per_sec,
                    "validation.queue_depth": queue_depth,
                },
            )

    def _emit_validation_failure(self, channel: int) -> None:
        """Emit additional validation-specific failure logs when a channel is active."""
        ch = self._channel_registry.get(channel)
        if not ch:
            return
        confidence = round(random.uniform(0.1, 0.5), 4)
        epoch = int(time.time()) - random.randint(3600, 86400)
        attrs = {
            "validation.result": "FAIL",
            "validation.sensor_type": ch["sensor_type"],
            "validation.calibration_epoch": epoch,
            "validation.confidence": confidence,
            "error.type": ch["error_type"],
            "vehicle_section": ch["vehicle_section"],
            "chaos.channel": channel,
            "chaos.fault_type": ch["name"],
            "operation": "sensor_validation",
            "system.status": "CRITICAL",
        }
        # Inject callback URL and user email for workflow auto-remediation
        meta = self.chaos_controller.get_channel_metadata(channel)
        if meta.get("callback_url"):
            attrs["chaos.callback_url"] = meta["callback_url"]
        if meta.get("user_email"):
            attrs["chaos.user_email"] = meta["user_email"]

        # Set event_name with remediation metadata (indexed keyword field)
        ev_name = None
        if meta.get("callback_url") or meta.get("user_email"):
            import json as _json

            ev_name = _json.dumps(
                {
                    "callback_url": meta.get("callback_url", ""),
                    "user_email": meta.get("user_email", ""),
                    "deployment_id": self._ctx.scenario_id if self._ctx else "",
                }
            )
        self.emit_log(
            "ERROR",
            f"Validation FAIL: {ch['sensor_type']} sensor calibration out of bounds — {ch['error_type']}",
            attrs,
            event_name=ev_name,
        )

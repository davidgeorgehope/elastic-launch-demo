"""Patient Monitor service — AWS us-east-1b. Bedside vital signs streaming and alert evaluation."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class PatientMonitorService(BaseService):
    SERVICE_NAME = "patient-monitor"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._readings_total = 0
        self._last_device_status = time.time()
        self._units = ["ICU-3A", "ICU-3B", "MedSurg-4N", "MedSurg-4S", "ED-1", "NICU-2"]

    def generate_telemetry(self) -> None:
        # -- Fault injection ------------------------------------
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Normal telemetry -----------------------------------
        self._emit_vital_reading()
        self._emit_waveform_status()

        if time.time() - self._last_device_status > 12:
            self._emit_device_summary()
            self._last_device_status = time.time()

        # Metrics
        self._readings_total += 1
        self.emit_metric(
            "patient_monitor.readings_total", float(self._readings_total), "readings"
        )
        self.emit_metric(
            "patient_monitor.active_devices", float(random.randint(60, 150)), "devices"
        )
        alert_rate = (
            random.randint(1, 8) if not active_channels else random.randint(30, 120)
        )
        self.emit_metric(
            "patient_monitor.alerts_per_minute", float(alert_rate), "alerts/min"
        )

    def _emit_vital_reading(self) -> None:
        unit = random.choice(self._units)
        patient_id = f"PT-{random.randint(100000, 999999)}"
        hr = random.randint(55, 110)
        spo2 = random.randint(92, 100)
        bp_sys = random.randint(100, 160)
        bp_dia = random.randint(60, 95)
        temp = round(random.uniform(36.2, 38.0), 1)
        self.emit_log(
            "INFO",
            f"[MONITOR] vitals_recorded patient={patient_id} unit={unit} hr={hr} bp={bp_sys}/{bp_dia} spo2={spo2}% temp={temp}C status=NORMAL",
            {
                "operation": "vital_reading",
                "vitals.unit": unit,
                "vitals.patient_id": patient_id,
                "vitals.heart_rate": hr,
                "vitals.spo2": spo2,
                "vitals.bp_systolic": bp_sys,
                "vitals.bp_diastolic": bp_dia,
                "vitals.temperature": temp,
            },
        )

    def _emit_waveform_status(self) -> None:
        unit = random.choice(self._units)
        devices_active = random.randint(8, 25)
        packet_loss = round(random.uniform(0.0, 0.5), 2)
        self.emit_log(
            "INFO",
            f"[MONITOR] waveform_stream unit={unit} devices={devices_active} packet_loss={packet_loss}% status=STREAMING",
            {
                "operation": "waveform_status",
                "waveform.unit": unit,
                "waveform.devices_active": devices_active,
                "waveform.packet_loss_pct": packet_loss,
            },
        )

    def _emit_device_summary(self) -> None:
        total_devices = random.randint(120, 200)
        online = total_devices - random.randint(0, 5)
        self.emit_log(
            "INFO",
            f"[MONITOR] device_summary online={online}/{total_devices} units={len(self._units)} telemetry=NOMINAL",
            {
                "operation": "device_summary",
                "devices.total": total_devices,
                "devices.online": online,
                "devices.units": len(self._units),
            },
        )

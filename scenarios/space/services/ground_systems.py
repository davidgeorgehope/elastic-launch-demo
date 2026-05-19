"""Ground Systems service — AWS us-east-1. Launch pad infrastructure and weather."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class GroundSystemsService(BaseService):
    SERVICE_NAME = "ground-systems"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._weather_cycle = 0
        self._last_gse_summary = time.time()

    WEATHER_PARAMS = [
        ("wind_speed", "knots", 2.0, 12.0),
        ("wind_direction", "deg", 0.0, 360.0),
        ("temperature", "C", 18.0, 28.0),
        ("humidity", "pct", 40.0, 70.0),
        ("visibility", "km", 8.0, 15.0),
        ("ceiling", "ft", 5000.0, 15000.0),
        ("barometric_pressure", "hPa", 1010.0, 1025.0),
    ]

    PAD_SYSTEMS = [
        "umbilical_connection",
        "cryogenic_loading",
        "electrical_bus",
        "hydraulic_clamps",
        "sound_suppression",
        "flame_deflector",
        "access_arm",
    ]

    def generate_telemetry(self) -> None:
        # ── Fault injection ────────────────────────────────────
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── Weather monitoring ─────────────────────────────────
        self._weather_cycle += 1
        self._emit_weather_readings()

        # ── Pad status ─────────────────────────────────────────
        self._emit_pad_status()

        # ── Ground support equipment ───────────────────────────
        self._emit_gse_check()

    def _emit_weather_readings(self) -> None:
        for param, unit, low, high in self.WEATHER_PARAMS:
            value = round(random.uniform(low, high), 1)
            self.emit_metric(f"ground.weather.{param}", value, unit)

        wind = round(random.uniform(2.0, 12.0), 1)
        vis = round(random.uniform(8.0, 15.0), 1)
        self.emit_metric("ground.weather_cycle", float(self._weather_cycle), "cycles")
        self.emit_log(
            "INFO",
            f"[GND] weather_check cycle={self._weather_cycle} wind={wind}kts visibility={vis}km ceiling=12000ft constraint=WITHIN status=GO",
            {
                "operation": "weather_check",
                "weather.cycle": self._weather_cycle,
                "weather.wind_speed_knots": wind,
                "weather.visibility_km": vis,
                "weather.status": "GO",
            },
        )

    def _emit_pad_status(self) -> None:
        system = random.choice(self.PAD_SYSTEMS)
        self.emit_log(
            "INFO",
            f"[GND] pad_check system={system} result=PASS status=NOMINAL",
            {
                "operation": "pad_check",
                "pad.system": system,
                "pad.status": "NOMINAL",
            },
        )
        self.emit_metric("ground.pad_system_checks", 1.0, "checks")

    def _emit_gse_check(self) -> None:
        gse_items = [
            "LOX transfer line",
            "RP-1 transfer line",
            "helium pressurization",
            "nitrogen purge",
            "fire suppression",
        ]
        item = random.choice(gse_items)
        self.emit_log(
            "INFO",
            f"[GND] gse_check equipment={item} result=OPERATIONAL status=NOMINAL",
            {
                "operation": "gse_check",
                "gse.equipment": item,
                "gse.status": "OPERATIONAL",
            },
        )

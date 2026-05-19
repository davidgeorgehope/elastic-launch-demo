"""Navigation service — GCP us-central1. IMU, GPS, star tracker telemetry."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService


class NavigationService(BaseService):
    SERVICE_NAME = "navigation"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._fix_count = 0
        self._last_nav_report = time.time()

    NAV_SYSTEMS = {
        "gps": {
            "drift_ms_range": (0.1, 1.5),
            "confidence_range": (0.95, 0.999),
            "satellites_range": (8, 14),
        },
        "imu": {
            "drift_ms_range": (0.01, 0.5),
            "confidence_range": (0.97, 0.999),
            "axes": ["X", "Y", "Z"],
        },
        "star_tracker": {
            "alignment_arcsec_range": (0.1, 3.0),
            "confidence_range": (0.96, 0.999),
            "catalog_stars_range": (12, 28),
        },
    }

    def generate_telemetry(self) -> None:
        # ── Fault injection ────────────────────────────────────
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── GPS telemetry ──────────────────────────────────────
        gps = self.NAV_SYSTEMS["gps"]
        gps_drift = round(random.uniform(*gps["drift_ms_range"]), 3)
        gps_conf = round(random.uniform(*gps["confidence_range"]), 4)
        gps_sats = random.randint(*gps["satellites_range"])

        self._fix_count += 1
        self.emit_metric("navigation.gps.drift_ms", gps_drift, "ms")
        self.emit_metric("navigation.gps.confidence", gps_conf, "ratio")
        self.emit_metric("navigation.gps.satellites", float(gps_sats), "count")
        self.emit_metric("navigation.fix_count", float(self._fix_count), "fixes")
        self.emit_log(
            "INFO",
            f"[GNC] gps_fix fix={self._fix_count} sv_count={gps_sats} drift={gps_drift}ms confidence={gps_conf} solution=NOMINAL",
            {
                "nav.system": "gps",
                "nav.fix_count": self._fix_count,
                "nav.drift_ms": gps_drift,
                "nav.confidence": gps_conf,
                "nav.gps_satellites": gps_sats,
                "operation": "gps_fix",
            },
        )

        # ── IMU telemetry ──────────────────────────────────────
        imu = self.NAV_SYSTEMS["imu"]
        for axis in imu["axes"]:
            drift = round(random.uniform(*imu["drift_ms_range"]), 4)
            conf = round(random.uniform(*imu["confidence_range"]), 4)
            self.emit_metric(f"navigation.imu.drift_{axis.lower()}", drift, "ms")
            self.emit_log(
                "INFO",
                f"[GNC] imu_reading axis={axis} drift={drift}ms confidence={conf} sync=LOCKED status=NOMINAL",
                {
                    "nav.system": "imu",
                    "nav.drift_ms": drift,
                    "nav.confidence": conf,
                    "nav.imu_axis": axis,
                    "operation": "imu_reading",
                },
            )

        # ── Star tracker telemetry ─────────────────────────────
        st = self.NAV_SYSTEMS["star_tracker"]
        alignment = round(random.uniform(*st["alignment_arcsec_range"]), 2)
        st_conf = round(random.uniform(*st["confidence_range"]), 4)
        stars = random.randint(*st["catalog_stars_range"])

        self.emit_metric(
            "navigation.star_tracker.alignment_arcsec", alignment, "arcsec"
        )
        self.emit_metric("navigation.star_tracker.confidence", st_conf, "ratio")
        self.emit_log(
            "INFO",
            f"[GNC] star_tracker catalog_matches={stars} alignment={alignment}arcsec confidence={st_conf} status=NOMINAL",
            {
                "nav.system": "star_tracker",
                "nav.drift_ms": alignment * 0.01,  # approx conversion
                "nav.confidence": st_conf,
                "nav.star_count": stars,
                "operation": "star_tracker_reading",
            },
        )

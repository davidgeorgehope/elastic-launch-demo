"""FCC scenario services - communications oversight, public safety, and licensing platforms."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService
from scenarios.fcc.executive_kpis import emit_executive_business_metrics_if_eligible


class FCCService(BaseService):
    """Shared telemetry generator for FCC demo services."""

    DOMAIN = "communications"
    OPERATIONS = ("health_check", "case_update", "data_sync")
    METRIC_PREFIX = "fcc"

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._events_total = 0
        self._last_summary = time.time()

    def generate_telemetry(self) -> None:
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        op = random.choice(self.OPERATIONS)
        latency_ms = random.randint(25, 220) if not active_channels else random.randint(900, 6500)
        records = random.randint(50, 9000)
        region = self.service_cfg["cloud_region"]

        self._events_total += records
        self.emit_metric(f"{self.METRIC_PREFIX}.latency_ms", float(latency_ms), "ms")
        self.emit_metric(f"{self.METRIC_PREFIX}.records_total", float(self._events_total), "records")
        self.emit_metric(f"{self.METRIC_PREFIX}.queue_depth", float(random.randint(0, 180 if not active_channels else 5000)), "items")

        self.emit_log(
            "INFO",
            f"[FCC] service={self.SERVICE_NAME} op={op} domain={self.DOMAIN} region={region} "
            f"records={records} latency_ms={latency_ms} status=OK",
            {
                "operation": op,
                "fcc.domain": self.DOMAIN,
                "fcc.records": records,
                "fcc.latency_ms": latency_ms,
            },
        )

        if time.time() - self._last_summary > 10:
            self._emit_summary()
            self._last_summary = time.time()

        emit_executive_business_metrics_if_eligible(self)

    def _emit_summary(self) -> None:
        score = round(random.uniform(92.0, 99.99), 2)
        self.emit_log(
            "INFO",
            f"[FCC] operational_summary service={self.SERVICE_NAME} domain={self.DOMAIN} "
            f"compliance_score={score}% status={self._nominal_label}",
            {
                "operation": "operational_summary",
                "fcc.domain": self.DOMAIN,
                "fcc.compliance_score": score,
            },
        )


class BroadbandMapService(FCCService):
    SERVICE_NAME = "broadband-map"
    DOMAIN = "broadband_mapping"
    OPERATIONS = ("availability_tile_refresh", "fabric_challenge_match", "speed_claim_validation")
    METRIC_PREFIX = "broadband"


class SpectrumMonitorService(FCCService):
    SERVICE_NAME = "spectrum-monitor"
    DOMAIN = "spectrum_enforcement"
    OPERATIONS = ("rf_scan_ingest", "interference_geolocate", "licensed_band_check")
    METRIC_PREFIX = "spectrum"


class EASGatewayService(FCCService):
    SERVICE_NAME = "eas-gateway"
    DOMAIN = "emergency_alerting"
    OPERATIONS = ("cap_message_validate", "participant_fanout", "alert_receipt_audit")
    METRIC_PREFIX = "eas"


class ConsumerComplaintsService(FCCService):
    SERVICE_NAME = "consumer-complaints"
    DOMAIN = "consumer_protection"
    OPERATIONS = ("complaint_intake", "carrier_routing", "sla_escalation")
    METRIC_PREFIX = "complaints"


class LicenseManagerService(FCCService):
    SERVICE_NAME = "license-manager"
    DOMAIN = "licensing"
    OPERATIONS = ("application_review", "uls_record_update", "fee_status_check")
    METRIC_PREFIX = "licensing"


class AuctionPlatformService(FCCService):
    SERVICE_NAME = "auction-platform"
    DOMAIN = "spectrum_auction"
    OPERATIONS = ("bid_window_validate", "eligibility_points_calc", "round_result_publish")
    METRIC_PREFIX = "auction"


class OutageReportingService(FCCService):
    SERVICE_NAME = "outage-reporting"
    DOMAIN = "network_outage"
    OPERATIONS = ("nors_report_ingest", "dirS_911_impact_check", "restoration_update")
    METRIC_PREFIX = "outage"


class RobocallAnalyticsService(FCCService):
    SERVICE_NAME = "robocall-analytics"
    DOMAIN = "robocall_mitigation"
    OPERATIONS = ("stir_shaken_attestation", "traceback_graph_update", "campaign_score")
    METRIC_PREFIX = "robocall"


class DataExchangeService(FCCService):
    SERVICE_NAME = "data-exchange"
    DOMAIN = "public_data"
    OPERATIONS = ("open_data_export", "carrier_feed_normalize", "foia_package_prepare")
    METRIC_PREFIX = "data_exchange"

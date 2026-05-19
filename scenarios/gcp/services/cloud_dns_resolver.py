"""Cloud DNS Resolver service — GCP us-east1. DNS zones, DNSSEC, resolution."""

from __future__ import annotations

import random

from app.services.base_service import BaseService


class CloudDnsResolverService(BaseService):
    SERVICE_NAME = "cloud-dns-resolver"

    ZONES = ["gcpnet-internal", "gcpnet-prod-zone", "gcpnet-services", "gcpnet-reverse"]
    RECORD_TYPES = ["A", "AAAA", "CNAME", "MX", "SRV", "TXT"]

    def generate_telemetry(self) -> None:
        # -- Fault injection --
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Query volume --
        zone = random.choice(self.ZONES)
        queries_per_sec = random.randint(5000, 30000)
        latency_avg_ms = (
            round(random.uniform(1.0, 5.0), 2)
            if not active_channels
            else round(random.uniform(50.0, 500.0), 2)
        )

        self.emit_metric("dns.queries_per_sec", float(queries_per_sec), "qps")
        self.emit_metric("dns.latency_avg_ms", latency_avg_ms, "ms")

        self.emit_log(
            "INFO",
            f"cloud-dns: zone={zone} qps={queries_per_sec} "
            f"avg_latency={latency_avg_ms}ms visibility=private",
            {
                "operation": "query_stats",
                "dns.zone": zone,
                "dns.qps": queries_per_sec,
                "dns.latency_avg": latency_avg_ms,
            },
        )

        # -- DNSSEC status --
        dnssec_state = (
            "ON"
            if not active_channels
            else random.choice(["VALIDATION_ERROR", "KEY_ROTATION_PENDING"])
        )
        validation_errors = (
            random.randint(0, 2) if not active_channels else random.randint(50, 500)
        )
        self.emit_metric(
            "dns.dnssec_validation_errors", float(validation_errors), "errors"
        )

        self.emit_log(
            "INFO",
            f"cloud-dns: zone={zone} dnssec_state={dnssec_state} "
            f"validation_errors={validation_errors}/min algorithm=RSASHA256",
            {
                "operation": "dnssec_status",
                "dns.dnssec_state": dnssec_state,
                "dns.validation_errors": validation_errors,
            },
        )

        # -- Resolution types --
        record_type = random.choice(self.RECORD_TYPES)
        nxdomain_count = (
            random.randint(0, 10) if not active_channels else random.randint(100, 1000)
        )
        servfail_count = (
            random.randint(0, 2) if not active_channels else random.randint(50, 300)
        )
        self.emit_metric("dns.nxdomain_count", float(nxdomain_count), "responses")
        self.emit_metric("dns.servfail_count", float(servfail_count), "responses")

        self.emit_log(
            "INFO",
            f"cloud-dns: record_type={record_type} nxdomain={nxdomain_count} "
            f"servfail={servfail_count} zone={zone}",
            {
                "operation": "resolution_stats",
                "dns.record_type": record_type,
                "dns.nxdomain": nxdomain_count,
                "dns.servfail": servfail_count,
            },
        )

        # -- Zone record count --
        record_count = random.randint(200, 1500)
        self.emit_metric("dns.zone_record_count", float(record_count), "records")
        self.emit_log(
            "INFO",
            f"cloud-dns: zone={zone} records={record_count} "
            f"pending_changes=0 propagation_status=DONE",
            {
                "operation": "zone_health",
                "dns.zone": zone,
                "dns.record_count": record_count,
            },
        )

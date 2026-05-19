#!/usr/bin/env python3
"""VPC Flow Log Generator — sends AWS and GCP VPC flow logs via OTLP.

Generates logs that populate:
  - [AWS VPC OTEL] VPC Flow Logs Overview dashboard
  - [AWS VPC OTEL] Traffic Analysis dashboard
  - [AWS VPC OTEL] Interface Analysis dashboard
  - [GCP VPC OTEL] VPC Flow Logs Overview dashboard
  - [GCP VPC OTEL] Traffic Analysis dashboard
  - [GCP VPC OTEL] Interface Analysis dashboard

Sends to separate data streams (aws_vpcflow / gcp_vpcflow) so fields are
properly indexed and searchable by ES|QL — NOT the default `logs` stream
which uses passthrough mapping.

Usage (standalone):
    python3 -m log_generators.vpc_flow_generator
"""

from __future__ import annotations

import logging
import os
import random
import signal
import threading
import time

from app.telemetry import OTLPClient, _format_attributes, SCHEMA_URL, _now_ns
from app.config import NAMESPACE

logger = logging.getLogger("vpc-flow-generator")

FLOW_INTERVAL = int(os.getenv("VPC_FLOW_INTERVAL", "5"))
BATCH_SIZE_MIN = 10
BATCH_SIZE_MAX = 20

SCOPE_NAME = f"{NAMESPACE}-vpc-flow-generator"
SCOPE_VERSION = "1.0.0"

# ── Realistic IP pools ──────────────────────────────────────────────────────

AWS_INTERNAL_IPS = [
    "10.0.1.42",
    "10.0.1.100",
    "10.0.2.15",
    "10.0.2.88",
    "10.0.3.22",
    "10.0.3.55",
    "10.0.4.10",
    "10.0.4.77",
    "10.0.5.33",
    "10.0.5.99",
]
AWS_EXTERNAL_IPS = [
    "203.0.113.10",
    "203.0.113.25",
    "198.51.100.44",
    "198.51.100.77",
    "192.0.2.100",
    "192.0.2.200",
    "54.239.28.85",
    "52.94.76.10",
]

GCP_INTERNAL_IPS = [
    "10.128.0.15",
    "10.128.0.20",
    "10.128.1.5",
    "10.128.1.30",
    "10.128.2.10",
    "10.128.2.50",
    "10.128.3.8",
    "10.128.3.42",
]
GCP_EXTERNAL_IPS = [
    "35.201.97.10",
    "35.201.97.55",
    "34.120.50.22",
    "34.120.50.88",
    "104.199.30.5",
    "104.199.30.77",
    "142.250.80.10",
    "142.250.80.25",
]

GCP_VPC_NAMES = [
    f"{NAMESPACE}-vpc-prod",
    f"{NAMESPACE}-vpc-staging",
    f"{NAMESPACE}-vpc-data",
]
COUNTRY_CODES = ["USA", "DEU", "GBR", "JPN", "AUS", "CAN", "FRA", "BRA", "IND", "SGP"]
TRANSPORTS = ["tcp", "udp", "icmp"]
COMMON_PORTS = [22, 53, 80, 443, 3306, 5432, 6379, 8080, 8443, 9200, 9300]

AWS_ENI_IDS = [
    "eni-0a1b2c3d4e5f60001",
    "eni-0a1b2c3d4e5f60002",
    "eni-0a1b2c3d4e5f60003",
    "eni-0a1b2c3d4e5f60004",
    "eni-0a1b2c3d4e5f60005",
    "eni-0a1b2c3d4e5f60006",
    "eni-0a1b2c3d4e5f60007",
    "eni-0a1b2c3d4e5f60008",
]

PORT_TO_PROTOCOL = {
    22: "ssh",
    53: "dns",
    80: "http",
    443: "https",
    3306: "mysql",
    5432: "postgresql",
    6379: "redis",
    8080: "http",
    8443: "https",
    9200: "http",
    9300: "http",
}


# ── AWS VPC flow log generation ─────────────────────────────────────────────


def _build_aws_resource() -> dict:
    attrs = {
        "cloud.provider": "aws",
        "cloud.platform": "aws_ec2",
        "cloud.region": "us-east-1",
        "cloud.account.id": "123456789012",
        "data_stream.type": "logs",
        "data_stream.dataset": "aws.vpcflow",
        "data_stream.namespace": "default",
        "service.name": "aws-vpc-flow",
        "telemetry.sdk.name": "opentelemetry",
        "telemetry.sdk.version": "1.24.0",
    }
    return {"attributes": _format_attributes(attrs), "schemaUrl": SCHEMA_URL}


def _generate_aws_flow_record(rng: random.Random) -> dict:
    """Generate a single AWS VPC flow log record."""
    now_ns = _now_ns()
    action = rng.choice(["ACCEPT"] * 8 + ["REJECT"] * 2)  # 80% accept
    src_ip = rng.choice(AWS_INTERNAL_IPS + AWS_EXTERNAL_IPS)
    dst_ip = rng.choice(AWS_INTERNAL_IPS + AWS_EXTERNAL_IPS)
    src_port = (
        rng.choice(COMMON_PORTS) if rng.random() < 0.6 else rng.randint(1024, 65535)
    )
    dst_port = (
        rng.choice(COMMON_PORTS) if rng.random() < 0.7 else rng.randint(1024, 65535)
    )
    bytes_transferred = rng.randint(64, 1_500_000)
    transport = rng.choice(["tcp"] * 6 + ["udp"] * 3 + ["icmp"])
    packets = max(1, bytes_transferred // rng.randint(500, 1500))
    protocol = PORT_TO_PROTOCOL.get(dst_port, PORT_TO_PROTOCOL.get(src_port, transport))

    attrs = {
        "aws.vpc.flow.action": action,
        "aws.vpc.flow.bytes": bytes_transferred,
        "aws.vpc.flow.packets": packets,
        "source.address": src_ip,
        "source.port": src_port,
        "destination.address": dst_ip,
        "destination.port": dst_port,
        "network.transport": transport,
        "network.interface.name": rng.choice(AWS_ENI_IDS),
        "network.protocol.name": protocol,
    }

    body = (
        f"{action} {src_ip}:{src_port} -> {dst_ip}:{dst_port} "
        f"{bytes_transferred} bytes"
    )

    return {
        "timeUnixNano": now_ns,
        "severityText": "INFO",
        "severityNumber": 9,
        "body": {"stringValue": body},
        "attributes": _format_attributes(attrs),
    }


# ── GCP VPC flow log generation ─────────────────────────────────────────────


def _build_gcp_resource() -> dict:
    attrs = {
        "cloud.provider": "gcp",
        "cloud.platform": "gcp_compute_engine",
        "cloud.region": "us-central1",
        "cloud.account.id": f"{NAMESPACE}-project-prod",
        "data_stream.type": "logs",
        "data_stream.dataset": "gcp.vpcflow",
        "data_stream.namespace": "default",
        "service.name": "gcp-vpc-flow",
        "telemetry.sdk.name": "opentelemetry",
        "telemetry.sdk.version": "1.24.0",
    }
    return {"attributes": _format_attributes(attrs), "schemaUrl": SCHEMA_URL}


def _generate_gcp_flow_record(
    rng: random.Random, gcp_vpc_names: list | None = None
) -> dict:
    """Generate a single GCP VPC flow log record."""
    _vpc_names = gcp_vpc_names or GCP_VPC_NAMES

    now_ns = _now_ns()
    src_ip = rng.choice(GCP_INTERNAL_IPS + GCP_EXTERNAL_IPS)
    dst_ip = rng.choice(GCP_INTERNAL_IPS + GCP_EXTERNAL_IPS)
    bytes_sent = rng.randint(64, 2_000_000)
    packets_sent = max(1, bytes_sent // rng.randint(500, 1500))
    reporter = rng.choice(["SRC", "DEST"])
    src_vpc = rng.choice(_vpc_names)
    dst_vpc = rng.choice(_vpc_names)
    transport = rng.choice(["tcp"] * 6 + ["udp"] * 3 + ["icmp"])
    src_port = (
        rng.choice(COMMON_PORTS) if rng.random() < 0.6 else rng.randint(1024, 65535)
    )
    dst_port = (
        rng.choice(COMMON_PORTS) if rng.random() < 0.7 else rng.randint(1024, 65535)
    )
    protocol = PORT_TO_PROTOCOL.get(dst_port, PORT_TO_PROTOCOL.get(src_port, transport))

    attrs = {
        "gcp.vpc.flow.bytes_sent": bytes_sent,
        "gcp.vpc.flow.packets_sent": packets_sent,
        "gcp.vpc.flow.reporter": reporter,
        "gcp.vpc.flow.source.vpc.name": src_vpc,
        "gcp.vpc.flow.destination.vpc.name": dst_vpc,
        "gcp.vpc.flow.source.geo.country.iso_code.alpha3": rng.choice(COUNTRY_CODES),
        "source.address": src_ip,
        "source.port": src_port,
        "destination.address": dst_ip,
        "destination.port": dst_port,
        "network.transport": transport,
        "network.interface.name": rng.choice(["nic0", "nic1"]),
        "network.protocol.name": protocol,
    }

    body = (
        f"{reporter} {src_ip} -> {dst_ip} via {src_vpc} "
        f"{bytes_sent}B {packets_sent}pkts {transport}"
    )

    return {
        "timeUnixNano": now_ns,
        "severityText": "INFO",
        "severityNumber": 9,
        "body": {"stringValue": body},
        "attributes": _format_attributes(attrs),
    }


# ── Run loop ─────────────────────────────────────────────────────────────────


def run(
    client: OTLPClient, stop_event: threading.Event, scenario_data: dict | None = None
) -> None:
    """Run VPC flow log generator loop until stop_event is set."""
    rng = random.Random()

    # Rebuild namespace-dependent data from scenario_data to avoid import-time freezing
    if scenario_data:
        ns = scenario_data["namespace"]
        scope_name = f"{ns}-vpc-flow-generator"
        gcp_vpc_names = [f"{ns}-vpc-prod", f"{ns}-vpc-staging", f"{ns}-vpc-data"]
        # Rebuild GCP resource with dynamic namespace
        gcp_attrs = {
            "cloud.provider": "gcp",
            "cloud.platform": "gcp_compute_engine",
            "cloud.region": "us-central1",
            "cloud.account.id": f"{ns}-project-prod",
            "data_stream.type": "logs",
            "data_stream.dataset": "gcp.vpcflow",
            "data_stream.namespace": "default",
            "service.name": "gcp-vpc-flow",
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.version": "1.24.0",
        }
        gcp_resource = {
            "attributes": _format_attributes(gcp_attrs),
            "schemaUrl": SCHEMA_URL,
        }
    else:
        scope_name = SCOPE_NAME
        gcp_vpc_names = GCP_VPC_NAMES
        gcp_resource = _build_gcp_resource()

    aws_resource = _build_aws_resource()

    logger.info(
        "VPC flow generator started (interval=%ds, batch=%d-%d per provider, scope=%s)",
        FLOW_INTERVAL,
        BATCH_SIZE_MIN,
        BATCH_SIZE_MAX,
        scope_name,
    )

    batch_count = 0
    while not stop_event.is_set():
        # AWS flow logs
        aws_batch_size = rng.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)
        aws_records = [_generate_aws_flow_record(rng) for _ in range(aws_batch_size)]
        aws_payload = {
            "resourceLogs": [
                {
                    "resource": aws_resource,
                    "scopeLogs": [
                        {
                            "scope": {"name": scope_name, "version": SCOPE_VERSION},
                            "logRecords": aws_records,
                        }
                    ],
                }
            ]
        }
        client._send(f"{client.endpoint}/v1/logs", aws_payload, "aws-vpc-flow")

        # GCP flow logs
        gcp_batch_size = rng.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)
        gcp_records = [
            _generate_gcp_flow_record(rng, gcp_vpc_names) for _ in range(gcp_batch_size)
        ]
        gcp_payload = {
            "resourceLogs": [
                {
                    "resource": gcp_resource,
                    "scopeLogs": [
                        {
                            "scope": {"name": scope_name, "version": SCOPE_VERSION},
                            "logRecords": gcp_records,
                        }
                    ],
                }
            ]
        }
        client._send(f"{client.endpoint}/v1/logs", gcp_payload, "gcp-vpc-flow")

        batch_count += 1
        if batch_count % 12 == 0:
            logger.info(
                "VPC flow batch %d: sent %d AWS + %d GCP records",
                batch_count,
                aws_batch_size,
                gcp_batch_size,
            )

        stop_event.wait(FLOW_INTERVAL)

    logger.info("VPC flow generator stopped after %d batches", batch_count)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    client = OTLPClient()
    stop_event = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())

    duration = int(os.environ.get("RUN_DURATION", "60"))
    timer = threading.Timer(duration, stop_event.set)
    timer.daemon = True
    timer.start()
    logger.info("Running for %ds (standalone)", duration)
    run(client, stop_event)
    timer.cancel()
    client.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Nginx Log Generator — sends synthetic nginx access & error logs via OTLP.

Imports and reuses the existing OTLPClient from app.telemetry to send
structured nginx-style log records directly to the Elastic OTLP endpoint.

Usage (standalone):
    python3 -m log_generators.nginx_log_generator
"""

from __future__ import annotations

import logging
import os
import random
import secrets
import signal
import threading
import time

from app.telemetry import (
    OTLPClient,
    _format_attributes,
    SCHEMA_URL,
    SCOPE_NAME,
    _now_ns,
)
from app.config import SEVERITY_MAP, NAMESPACE

# Span kind constants
SPAN_KIND_SERVER = 2
SPAN_KIND_CLIENT = 3
STATUS_OK = 1
STATUS_ERROR = 2

logger = logging.getLogger("nginx-log-generator")

# ── Configuration ─────────────────────────────────────────────────────────────
BATCH_INTERVAL_MIN = 2
BATCH_INTERVAL_MAX = 5
BATCH_SIZE_MIN = 5
BATCH_SIZE_MAX = 20

# ── Realistic nginx data pools ────────────────────────────────────────────────
ENDPOINTS = [
    "/api/v1/telemetry",
    "/api/v1/health",
    "/api/v1/metrics",
    "/api/v1/traces",
    "/api/v1/logs",
    f"/api/v1/agents/{NAMESPACE}",
    "/api/v1/channels/status",
    "/api/v1/operations/status",
    "/api/v1/operations/emergency",
    "/api/v2/telemetry/stream",
    "/static/app.js",
    "/static/app.css",
    "/static/dashboard.js",
    "/static/favicon.ico",
    "/dashboard",
    "/dashboard/operations",
    "/dashboard/overview",
    "/login",
    "/logout",
    "/healthz",
    "/readyz",
]

METHODS = [
    "GET",
    "GET",
    "GET",
    "GET",
    "POST",
    "POST",
    "PUT",
    "DELETE",
    "HEAD",
    "OPTIONS",
]

STATUS_WEIGHTS = {
    200: 60,
    301: 3,
    304: 8,
    400: 5,
    401: 3,
    403: 2,
    404: 8,
    405: 1,
    500: 4,
    502: 3,
    503: 2,
    504: 1,
}
STATUS_CODES = []
for code, weight in STATUS_WEIGHTS.items():
    STATUS_CODES.extend([code] * weight)

CLIENT_IPS = [
    "10.0.1.42",
    "10.0.1.87",
    "10.0.2.15",
    "10.0.2.200",
    "10.0.3.55",
    "172.16.0.10",
    "172.16.0.25",
    "172.16.1.100",
    "192.168.1.1",
    "192.168.1.50",
    "203.0.113.42",
    "203.0.113.99",
    "198.51.100.23",
    "198.51.100.77",
]

USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 Safari/605.1.15",
    "python-httpx/0.27.0",
    "curl/8.4.0",
    "Go-http-client/2.0",
    "Platform-Monitor/1.0",
    "Elastic-Heartbeat/8.12.0",
    "kube-probe/1.28",
]

SERVER_NAMES = [f"{NAMESPACE}-proxy-01", f"{NAMESPACE}-proxy-02"]

ERROR_MESSAGES = [
    "upstream timed out (110: Connection timed out) while connecting to upstream",
    "upstream prematurely closed connection while reading response header from upstream",
    "connect() failed (111: Connection refused) while connecting to upstream",
    "no live upstreams while connecting to upstream",
    "recv() failed (104: Connection reset by peer)",
    "client intended to send too large body: 10485760 bytes",
    "access forbidden by rule",
    "SSL_do_handshake() failed (SSL: error:0A000126:SSL routines::unexpected eof while reading)",
    'open() "/usr/share/nginx/html/missing" failed (2: No such file or directory)',
    "upstream sent too big header while reading response header from upstream",
]

UPSTREAM_ADDRS = [
    "10.0.1.100:8080",
    "10.0.1.101:8080",
    "10.0.1.102:8080",
    "10.0.2.100:8080",
    "10.0.2.101:8080",
]


# ── Resource builders ─────────────────────────────────────────────────────────
def _build_access_resource() -> dict:
    return {
        "attributes": _format_attributes(
            {
                "service.name": "nginx-proxy",
                "service.namespace": NAMESPACE,
                "service.version": "1.25.4",
                "service.instance.id": "nginx-proxy-001",
                "telemetry.sdk.language": "python",
                "telemetry.sdk.name": "opentelemetry",
                "telemetry.sdk.version": "1.24.0",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "us-central1",
                "cloud.availability_zone": "us-central1-a",
                "deployment.environment": f"production-{NAMESPACE}",
                "host.name": f"{NAMESPACE}-proxy-host",
                "host.architecture": "amd64",
                "os.type": "linux",
                "data_stream.type": "logs",
                "data_stream.dataset": "nginx.access",
                "data_stream.namespace": "default",
            }
        ),
        "schemaUrl": SCHEMA_URL,
    }


def _build_error_resource() -> dict:
    return {
        "attributes": _format_attributes(
            {
                "service.name": "nginx-proxy",
                "service.namespace": NAMESPACE,
                "service.version": "1.25.4",
                "service.instance.id": "nginx-proxy-001",
                "telemetry.sdk.language": "python",
                "telemetry.sdk.name": "opentelemetry",
                "telemetry.sdk.version": "1.24.0",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "us-central1",
                "cloud.availability_zone": "us-central1-a",
                "deployment.environment": f"production-{NAMESPACE}",
                "host.name": f"{NAMESPACE}-proxy-host",
                "host.architecture": "amd64",
                "os.type": "linux",
                "data_stream.type": "logs",
                "data_stream.dataset": "nginx.error",
                "data_stream.namespace": "default",
            }
        ),
        "schemaUrl": SCHEMA_URL,
    }


def _build_trace_resource() -> dict:
    return {
        "attributes": _format_attributes(
            {
                "service.name": "nginx-proxy",
                "service.namespace": NAMESPACE,
                "service.version": "1.25.4",
                "service.instance.id": "nginx-proxy-001",
                "telemetry.sdk.language": "python",
                "telemetry.sdk.name": "opentelemetry",
                "telemetry.sdk.version": "1.24.0",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "us-central1",
                "cloud.availability_zone": "us-central1-a",
                "deployment.environment": f"production-{NAMESPACE}",
                "host.name": f"{NAMESPACE}-proxy-host",
                "host.architecture": "amd64",
                "os.type": "linux",
                "data_stream.type": "traces",
                "data_stream.dataset": "generic",
                "data_stream.namespace": "default",
            }
        ),
        "schemaUrl": SCHEMA_URL,
    }


# ── Log record generators ────────────────────────────────────────────────────
def _generate_access_log(
    client: OTLPClient,
    rng: random.Random,
    endpoints: list | None = None,
    server_names: list | None = None,
    namespace: str | None = None,
) -> tuple[dict, dict | None]:
    """Generate an access log record and optionally an HTTP trace span.

    Returns (log_record, span_or_None).
    """
    _endpoints = endpoints or ENDPOINTS
    _server_names = server_names or SERVER_NAMES
    _ns = namespace or NAMESPACE

    method = rng.choice(METHODS)
    path = rng.choice(_endpoints)
    status = rng.choice(STATUS_CODES)
    body_bytes = rng.randint(0, 50000) if status == 200 else rng.randint(0, 500)
    client_ip = rng.choice(CLIENT_IPS)
    ua = rng.choice(USER_AGENTS)
    server = rng.choice(_server_names)
    upstream = rng.choice(UPSTREAM_ADDRS)
    request_time = round(rng.uniform(0.001, 0.3), 3)

    # Slower requests for error statuses
    if status >= 500:
        request_time = round(rng.uniform(0.2, 0.8), 3)

    severity = "INFO"
    if status >= 500:
        severity = "ERROR"
    elif status >= 400:
        severity = "WARN"

    # Generate trace/span IDs for correlation
    trace_id = secrets.token_hex(16)
    span_id = secrets.token_hex(8)

    body = (
        f'{client_ip} - - "{method} {path} HTTP/1.1" {status} {body_bytes} '
        f'"{ua}" rt={request_time}'
    )

    attrs = {
        "http.request.method": method,
        "url.path": path,
        "http.response.status_code": status,
        "http.response.body.bytes": body_bytes,
        "client.address": client_ip,
        "user_agent.original": ua,
        "server.address": server,
        "url.domain": f"{_ns}.internal",
        "network.protocol.name": "http",
        "network.protocol.version": "1.1",
        "upstream.address": upstream,
        "nginx.request_time": request_time,
    }

    log_record = client.build_log_record(
        severity=severity,
        body=body,
        attributes=attrs,
        trace_id=trace_id,
        span_id=span_id,
    )

    # Build a correlated HTTP span
    span_status = STATUS_ERROR if status >= 500 else STATUS_OK
    duration_ms = int(request_time * 1000)
    span = client.build_span(
        name=f"{method} {path}",
        trace_id=trace_id,
        span_id=span_id,
        kind=SPAN_KIND_SERVER,
        duration_ms=max(1, duration_ms),
        status_code=span_status,
        attributes={
            "http.request.method": method,
            "url.path": path,
            "http.response.status_code": status,
            "server.address": server,
            "server.port": 80,
            "client.address": client_ip,
            "user_agent.original": ua,
            "network.protocol.version": "1.1",
        },
    )

    return log_record, span


def _generate_error_log(
    client: OTLPClient,
    rng: random.Random,
    endpoints: list | None = None,
    server_names: list | None = None,
) -> dict:
    _endpoints = endpoints or ENDPOINTS
    _server_names = server_names or SERVER_NAMES

    error_msg = rng.choice(ERROR_MESSAGES)
    server = rng.choice(_server_names)
    upstream = rng.choice(UPSTREAM_ADDRS)
    client_ip = rng.choice(CLIENT_IPS)
    path = rng.choice(_endpoints)

    body = f'[error] {error_msg}, client: {client_ip}, server: {server}, request: "GET {path} HTTP/1.1", upstream: "http://{upstream}{path}"'

    attrs = {
        "error.message": error_msg,
        "client.address": client_ip,
        "server.address": server,
        "url.path": path,
        "upstream.address": upstream,
        "event.category": "web",
        "event.type": "error",
        "event.kind": "event",
    }

    return client.build_log_record(severity="ERROR", body=body, attributes=attrs)


# ── Run loop (used by ServiceManager and standalone) ──────────────────────────
def run(
    client: OTLPClient, stop_event: threading.Event, scenario_data: dict | None = None
) -> None:
    """Run nginx log generator loop until stop_event is set."""
    rng = random.Random()

    # Rebuild namespace-dependent data from scenario_data to avoid import-time freezing
    if scenario_data:
        ns = scenario_data["namespace"]
    else:
        ns = NAMESPACE

    server_names = [f"{ns}-proxy-01", f"{ns}-proxy-02"]
    endpoints = [
        "/api/v1/telemetry",
        "/api/v1/health",
        "/api/v1/metrics",
        "/api/v1/traces",
        "/api/v1/logs",
        f"/api/v1/agents/{ns}",
        "/api/v1/channels/status",
        "/api/v1/operations/status",
        "/api/v1/operations/emergency",
        "/api/v2/telemetry/stream",
        "/static/app.js",
        "/static/app.css",
        "/static/dashboard.js",
        "/static/favicon.ico",
        "/dashboard",
        "/dashboard/operations",
        "/dashboard/overview",
        "/login",
        "/logout",
        "/healthz",
        "/readyz",
    ]

    def _build_resource_dynamic(dataset: str, data_stream_type: str = "logs") -> dict:
        return {
            "attributes": _format_attributes(
                {
                    "service.name": "nginx-proxy",
                    "service.namespace": ns,
                    "service.version": "1.25.4",
                    "service.instance.id": "nginx-proxy-001",
                    "telemetry.sdk.language": "python",
                    "telemetry.sdk.name": "opentelemetry",
                    "telemetry.sdk.version": "1.24.0",
                    "cloud.provider": "gcp",
                    "cloud.platform": "gcp_compute_engine",
                    "cloud.region": "us-central1",
                    "cloud.availability_zone": "us-central1-a",
                    "deployment.environment": f"production-{ns}",
                    "host.name": f"{ns}-proxy-host",
                    "host.architecture": "amd64",
                    "os.type": "linux",
                    "data_stream.type": data_stream_type,
                    "data_stream.dataset": dataset,
                    "data_stream.namespace": "default",
                }
            ),
            "schemaUrl": SCHEMA_URL,
        }

    access_resource = _build_resource_dynamic("nginx.access")
    error_resource = _build_resource_dynamic("nginx.error")
    trace_resource = _build_resource_dynamic("generic", "traces")

    # Only emit traces if nginx-proxy is in the scenario's services (avoids
    # disconnected Service Map nodes when the scenario doesn't include it).
    _emit_traces = True
    if scenario_data and "services" in scenario_data:
        _emit_traces = "nginx-proxy" in scenario_data["services"]

    total_sent = 0
    total_spans = 0
    error_spike_active = False

    logger.info("Nginx log generator started (namespace=%s)", ns)

    while not stop_event.is_set():
        batch_size = rng.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)

        # 10% chance of an error spike each cycle
        if rng.random() < 0.10:
            error_spike_active = True
        elif error_spike_active and rng.random() < 0.5:
            error_spike_active = False

        # Generate access logs + correlated trace spans
        access_records = []
        spans = []
        for _ in range(batch_size):
            log_record, span = _generate_access_log(
                client, rng, endpoints, server_names, ns
            )
            access_records.append(log_record)
            if span:
                spans.append(span)
        client.send_logs(access_resource, access_records)

        # Send correlated trace spans (only if nginx-proxy is in scenario topology)
        if spans and _emit_traces:
            client.send_traces(trace_resource, spans)
            total_spans += len(spans)

        # Generate error logs (more during spikes)
        error_count = rng.randint(3, 10) if error_spike_active else rng.randint(0, 2)
        if error_count > 0:
            error_records = []
            for _ in range(error_count):
                error_records.append(
                    _generate_error_log(client, rng, endpoints, server_names)
                )
            client.send_logs(error_resource, error_records)

        total_sent += batch_size + error_count
        logger.info(
            "Sent %d access + %d error logs, %d spans (total=%d logs, %d spans)",
            batch_size,
            error_count,
            len(spans),
            total_sent,
            total_spans,
        )

        sleep_time = rng.uniform(BATCH_INTERVAL_MIN, BATCH_INTERVAL_MAX)
        stop_event.wait(sleep_time)

    logger.info(
        "Nginx log generator stopped. Total: %d logs, %d spans", total_sent, total_spans
    )


# ── Standalone entry point ────────────────────────────────────────────────────
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
    logger.info("Running for %ds (standalone mode)", duration)

    run(client, stop_event)
    timer.cancel()
    client.close()


if __name__ == "__main__":
    main()

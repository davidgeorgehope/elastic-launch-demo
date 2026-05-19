#!/usr/bin/env python3
"""Nginx Metrics Generator — sends nginx stub_status metrics via OTLP.

Generates metrics that populate the [Metrics Nginx OTEL] Overview dashboard:
  - nginx.requests (cumulative counter)
  - nginx.connections_handled (cumulative counter)
  - nginx.connections_accepted (cumulative counter)
  - nginx.connections_current (gauge with state: active/reading/writing/waiting)

Usage (standalone):
    python3 -m log_generators.nginx_metrics_generator
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

logger = logging.getLogger("nginx-metrics-generator")

METRICS_INTERVAL = int(os.getenv("NGINX_METRICS_INTERVAL", "10"))

SCOPE_NAME = (
    "github.com/open-telemetry/opentelemetry-collector-contrib/receiver/nginxreceiver"
)
SCOPE_VERSION = "0.115.0"

# Two nginx instances across different hosts (derived from active scenario)
NGINX_HOSTS = [
    {
        "host.name": f"{NAMESPACE}-nginx-01",
        "service.name": "nginx-proxy",
        "service.instance.id": "nginx-proxy-001",
        "cloud.provider": "aws",
        "cloud.platform": "aws_ec2",
        "cloud.region": "us-east-1",
    },
    {
        "host.name": f"{NAMESPACE}-nginx-02",
        "service.name": "nginx-proxy",
        "service.instance.id": "nginx-proxy-002",
        "cloud.provider": "gcp",
        "cloud.platform": "gcp_compute_engine",
        "cloud.region": "us-central1",
    },
]


def _build_resource(host_cfg: dict) -> dict:
    attrs = {
        **host_cfg,
        "telemetry.sdk.name": "opentelemetry",
        "telemetry.sdk.version": "1.24.0",
        "telemetry.sdk.language": "python",
        "data_stream.type": "metrics",
        "data_stream.dataset": "nginxreceiver",
        "data_stream.namespace": "default",
    }
    return {"attributes": _format_attributes(attrs), "schemaUrl": SCHEMA_URL}


class NginxState:
    """Tracks cumulative counter values for one nginx instance."""

    def __init__(self, rng: random.Random):
        self._rng = rng
        self.requests = rng.randint(500_000, 2_000_000)
        self.connections_accepted = rng.randint(100_000, 500_000)
        self.connections_handled = self.connections_accepted - rng.randint(0, 100)

    def tick(self):
        rng = self._rng
        new_requests = rng.randint(50, 500)
        self.requests += new_requests
        new_accepted = rng.randint(5, 50)
        self.connections_accepted += new_accepted
        # handled is usually == accepted, occasionally slightly less
        self.connections_handled += new_accepted - (1 if rng.random() < 0.05 else 0)


def _build_cumulative_sum(name: str, unit: str, value: int) -> dict:
    now = _now_ns()
    return {
        "name": name,
        "unit": unit,
        "sum": {
            "dataPoints": [
                {
                    "startTimeUnixNano": str(int(now) - 60_000_000_000),
                    "timeUnixNano": now,
                    "asInt": str(value),
                }
            ],
            "aggregationTemporality": 2,
            "isMonotonic": True,
        },
    }


def _build_gauge(name: str, unit: str, value, attributes: dict | None = None) -> dict:
    now = _now_ns()
    dp: dict = {"timeUnixNano": now}
    if isinstance(value, int):
        dp["asInt"] = str(value)
    else:
        dp["asDouble"] = float(value)
    if attributes:
        dp["attributes"] = _format_attributes(attributes)
    return {"name": name, "unit": unit, "gauge": {"dataPoints": [dp]}}


def _generate_metrics(state: NginxState, rng: random.Random) -> list:
    state.tick()
    metrics = [
        _build_cumulative_sum("nginx.requests", "{request}", state.requests),
        _build_cumulative_sum(
            "nginx.connections_accepted", "{connection}", state.connections_accepted
        ),
        _build_cumulative_sum(
            "nginx.connections_handled", "{connection}", state.connections_handled
        ),
    ]

    # connections_current is a gauge with state attribute
    active = rng.randint(50, 300)
    reading = rng.randint(1, 20)
    writing = rng.randint(5, 50)
    waiting = active - reading - writing
    if waiting < 0:
        waiting = rng.randint(5, 30)

    for state_name, val in [
        ("active", active),
        ("reading", reading),
        ("writing", writing),
        ("waiting", waiting),
    ]:
        metrics.append(
            _build_gauge(
                "nginx.connections_current",
                "{connection}",
                val,
                attributes={"state": state_name},
            )
        )

    return metrics


def run(
    client: OTLPClient, stop_event: threading.Event, scenario_data: dict | None = None
) -> None:
    """Run nginx metrics generator loop until stop_event is set."""
    rng = random.Random()

    # Rebuild host list dynamically from scenario_data to avoid import-time freezing
    if scenario_data:
        ns = scenario_data["namespace"]
        nginx_hosts = [
            {
                "host.name": f"{ns}-nginx-01",
                "service.name": "nginx-proxy",
                "service.instance.id": "nginx-proxy-001",
                "cloud.provider": "aws",
                "cloud.platform": "aws_ec2",
                "cloud.region": "us-east-1",
            },
            {
                "host.name": f"{ns}-nginx-02",
                "service.name": "nginx-proxy",
                "service.instance.id": "nginx-proxy-002",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "us-central1",
            },
        ]
    else:
        nginx_hosts = NGINX_HOSTS

    resources = [_build_resource(h) for h in nginx_hosts]
    states = [NginxState(rng) for _ in nginx_hosts]

    logger.info(
        "Nginx metrics generator started (interval=%ds, hosts=%d)",
        METRICS_INTERVAL,
        len(nginx_hosts),
    )

    scrape_count = 0
    while not stop_event.is_set():
        resource_metrics = []
        for resource, state in zip(resources, states):
            metrics = _generate_metrics(state, rng)
            resource_metrics.append(
                {
                    "resource": resource,
                    "scopeMetrics": [
                        {
                            "scope": {"name": SCOPE_NAME, "version": SCOPE_VERSION},
                            "metrics": metrics,
                        }
                    ],
                }
            )

        payload = {"resourceMetrics": resource_metrics}
        client._send(f"{client.endpoint}/v1/metrics", payload, "nginx-metrics")

        scrape_count += 1
        if scrape_count % 6 == 0:
            logger.info("Nginx metrics scrape %d complete", scrape_count)

        stop_event.wait(METRICS_INTERVAL)

    logger.info("Nginx metrics generator stopped after %d scrapes", scrape_count)


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

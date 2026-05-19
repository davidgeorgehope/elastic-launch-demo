"""Cloud Load Balancer service — GCP us-central1. L4/L7 load balancing, backends, health checks."""

from __future__ import annotations

import random

from app.services.base_service import BaseService


class CloudLoadBalancerService(BaseService):
    SERVICE_NAME = "cloud-load-balancer"

    FORWARDING_RULES = [
        "gcpnet-fr-https-global",
        "gcpnet-fr-tcp-regional",
        "gcpnet-fr-udp-internal",
        "gcpnet-fr-grpc-global",
    ]
    BACKEND_SERVICES = ["gcpnet-bs-web", "gcpnet-bs-api", "gcpnet-bs-grpc"]

    def generate_telemetry(self) -> None:
        # -- Fault injection --
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Request distribution --
        fr = random.choice(self.FORWARDING_RULES)
        requests_per_sec = random.randint(5000, 25000)
        latency_p50 = round(random.uniform(5.0, 25.0), 1)
        latency_p99 = (
            round(random.uniform(50.0, 200.0), 1)
            if not active_channels
            else round(random.uniform(500.0, 3000.0), 1)
        )

        self.emit_metric("lb.requests_per_sec", float(requests_per_sec), "req/s")
        self.emit_metric("lb.latency_p50_ms", latency_p50, "ms")
        self.emit_metric("lb.latency_p99_ms", latency_p99, "ms")

        self.emit_log(
            "INFO",
            f"cloud-lb: forwarding_rule={fr} rps={requests_per_sec} "
            f"p50={latency_p50}ms p99={latency_p99}ms status=SERVING",
            {
                "operation": "request_distribution",
                "lb.forwarding_rule": fr,
                "lb.rps": requests_per_sec,
                "lb.latency_p50": latency_p50,
                "lb.latency_p99": latency_p99,
            },
        )

        # -- Backend health --
        bs = random.choice(self.BACKEND_SERVICES)
        total_backends = random.randint(6, 12)
        healthy = (
            total_backends
            if not active_channels
            else random.randint(1, total_backends - 2)
        )
        self.emit_metric("lb.backends_healthy", float(healthy), "instances")
        self.emit_metric("lb.backends_total", float(total_backends), "instances")

        self.emit_log(
            "INFO",
            f"cloud-lb: backend_service={bs} healthy={healthy}/{total_backends} "
            f"health_check=hc-http-8080 protocol=HTTP2",
            {
                "operation": "backend_health",
                "lb.backend_service": bs,
                "lb.healthy_backends": healthy,
                "lb.total_backends": total_backends,
            },
        )

        # -- SSL termination --
        ssl_connections = random.randint(2000, 10000)
        ssl_handshake_ms = round(random.uniform(2.0, 8.0), 1)
        self.emit_metric("lb.ssl_connections", float(ssl_connections), "connections")
        self.emit_metric("lb.ssl_handshake_ms", ssl_handshake_ms, "ms")

        self.emit_log(
            "INFO",
            f"cloud-lb: ssl_active_connections={ssl_connections} "
            f"handshake_latency={ssl_handshake_ms}ms tls_version=TLS1.3",
            {
                "operation": "ssl_status",
                "lb.ssl_connections": ssl_connections,
                "lb.ssl_handshake_ms": ssl_handshake_ms,
            },
        )

        # -- Error rate --
        error_rate_5xx = (
            round(random.uniform(0.0, 0.5), 2)
            if not active_channels
            else round(random.uniform(5.0, 25.0), 2)
        )
        self.emit_metric("lb.error_rate_5xx_pct", error_rate_5xx, "%")
        self.emit_log(
            "INFO",
            f"cloud-lb: 5xx_error_rate={error_rate_5xx}% "
            f"forwarding_rule={fr} interval=60s",
            {
                "operation": "error_rate",
                "lb.error_rate_5xx": error_rate_5xx,
            },
        )

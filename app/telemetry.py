"""OTLP Telemetry Client — sends traces, metrics, and logs in OTLP JSON format.

Adapted from otel-demo-gen/backend/generator.py. Uses httpx with auth headers,
batching, and graceful failure when the collector is unavailable.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

import httpx

from app.config import (
    OTLP_API_KEY,
    OTLP_AUTH_TYPE,
    OTLP_ENDPOINT,
    SEVERITY_MAP,
)

logger = logging.getLogger("nova7.telemetry")

SCHEMA_URL = "https://opentelemetry.io/schemas/1.35.0"
SCOPE_NAME = "elastic-launch-demo"


def _format_attributes(attrs: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert a flat dict to OTLP key-value attribute list."""
    formatted = []
    for key, value in attrs.items():
        if value is None:
            continue
        if isinstance(value, bool):
            val_dict = {"boolValue": value}
        elif isinstance(value, int):
            val_dict = {"intValue": str(value)}
        elif isinstance(value, float):
            val_dict = {"doubleValue": value}
        elif isinstance(value, str):
            val_dict = {"stringValue": value}
        else:
            val_dict = {"stringValue": str(value)}
        formatted.append({"key": key, "value": val_dict})
    return formatted


def _now_ns() -> str:
    return str(int(time.time() * 1_000_000_000))


class OTLPClient:
    """Sends OTLP JSON payloads to an HTTP endpoint (typically an OTel Collector)."""

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        auth_type: str | None = None,
    ):
        self.endpoint = (endpoint or OTLP_ENDPOINT).rstrip("/")
        self.api_key = api_key or OTLP_API_KEY
        self.auth_type = auth_type or OTLP_AUTH_TYPE

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"{self.auth_type} {self.api_key}"

        self.client = httpx.Client(headers=headers, http2=True, timeout=5)
        self.consecutive_failures = 0
        self.max_failures_before_backoff = 5

    def reconfigure(self, endpoint: str, api_key: str, auth_type: str = "ApiKey"):
        """Update endpoint and auth for a running client."""
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.auth_type = auth_type
        self.consecutive_failures = 0

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"{self.auth_type} {self.api_key}"
        # Close old client, create new one
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
        self.client = httpx.Client(headers=headers, http2=True, timeout=5)
        logger.info("OTLPClient reconfigured → %s", self.endpoint)

    # ── Resource helpers ───────────────────────────────────────────────
    @staticmethod
    def build_resource(
        service_name: str, service_cfg: dict[str, Any], namespace: str = "demo"
    ) -> dict[str, Any]:
        """Build an OTLP resource object for a service."""
        language = service_cfg.get("language", "python")
        attrs = {
            "service.name": service_name,
            "service.namespace": namespace,
            "service.version": "1.0.0",
            "service.instance.id": f"{service_name}-001",
            "telemetry.sdk.language": language,
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.version": "1.24.0",
            "cloud.provider": service_cfg["cloud_provider"],
            "cloud.platform": service_cfg["cloud_platform"],
            "cloud.region": service_cfg["cloud_region"],
            "cloud.availability_zone": service_cfg["cloud_availability_zone"],
            "deployment.environment": "production",
            "host.name": f"{service_name}-host",
            "host.architecture": "amd64",
            "os.type": "linux",
            "data_stream.type": "logs",
            "data_stream.dataset": "generic",
            "data_stream.namespace": "default",
            "elasticsearch.index": "logs.otel",
        }
        # Add process.runtime attributes so Elastic APM can identify the runtime
        _RUNTIME_ATTRS = {
            "java": {
                "process.runtime.name": "OpenJDK Runtime Environment",
                "process.runtime.version": "21.0.5+11-LTS",
                "process.runtime.description": "Eclipse Adoptium OpenJDK 64-Bit Server VM 21.0.5+11-LTS",
            },
            "python": {
                "process.runtime.name": "CPython",
                "process.runtime.version": "3.12.3",
                "process.runtime.description": "CPython 3.12.3",
            },
            "go": {
                "process.runtime.name": "go",
                "process.runtime.version": "go1.22.4",
                "process.runtime.description": "go1.22.4 linux/amd64",
            },
            "dotnet": {
                "process.runtime.name": ".NET",
                "process.runtime.version": "8.0.6",
                "process.runtime.description": ".NET 8.0.6",
            },
            "rust": {
                "process.runtime.name": "rustc",
                "process.runtime.version": "1.79.0",
                "process.runtime.description": "rustc 1.79.0",
            },
            "cpp": {
                "process.runtime.name": "gcc",
                "process.runtime.version": "13.2.0",
                "process.runtime.description": "GCC 13.2.0",
            },
        }
        if language in _RUNTIME_ATTRS:
            attrs.update(_RUNTIME_ATTRS[language])
        return {
            "attributes": _format_attributes(attrs),
            "schemaUrl": SCHEMA_URL,
        }

    # ── Log sending ────────────────────────────────────────────────────
    def send_logs(
        self,
        resource: dict[str, Any],
        log_records: list[dict[str, Any]],
    ) -> None:
        """Send a batch of log records for a single resource."""
        if not log_records:
            return
        payload = {
            "resourceLogs": [
                {
                    "resource": resource,
                    "scopeLogs": [
                        {
                            "scope": {"name": SCOPE_NAME},
                            "logRecords": log_records,
                        }
                    ],
                }
            ]
        }
        self._send(f"{self.endpoint}/v1/logs", payload, "logs")

    def build_log_record(
        self,
        severity: str,
        body: str,
        attributes: dict[str, Any] | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        event_name: str | None = None,
    ) -> dict[str, Any]:
        """Build a single OTLP log record."""
        ts = _now_ns()
        record: dict[str, Any] = {
            "timeUnixNano": ts,
            "observedTimeUnixNano": ts,
            "severityText": severity.upper(),
            "severityNumber": SEVERITY_MAP.get(severity.upper(), 9),
            "body": {"stringValue": body},
        }
        if trace_id:
            record["traceId"] = trace_id
        if span_id:
            record["spanId"] = span_id
        if event_name:
            record["eventName"] = event_name
        if attributes:
            record["attributes"] = _format_attributes(attributes)
        return record

    # ── Metric sending ─────────────────────────────────────────────────
    def send_metrics(
        self,
        resource: dict[str, Any],
        metrics: list[dict[str, Any]],
    ) -> None:
        """Send a batch of metrics for a single resource."""
        if not metrics:
            return
        # Patch resource data_stream for metrics
        metric_resource = self._patch_resource_data_stream(resource, "metrics")
        payload = {
            "resourceMetrics": [
                {
                    "resource": metric_resource,
                    "scopeMetrics": [
                        {
                            "scope": {"name": SCOPE_NAME},
                            "metrics": metrics,
                        }
                    ],
                }
            ]
        }
        self._send(f"{self.endpoint}/v1/metrics", payload, "metrics")

    def build_gauge(
        self,
        name: str,
        value: float,
        unit: str = "",
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        dp: dict[str, Any] = {
            "timeUnixNano": _now_ns(),
            "asDouble": value,
        }
        if attributes:
            dp["attributes"] = _format_attributes(attributes)
        metric: dict[str, Any] = {
            "name": name,
            "gauge": {"dataPoints": [dp]},
        }
        if unit:
            metric["unit"] = unit
        return metric

    # ── Trace sending ──────────────────────────────────────────────────
    def send_traces(
        self,
        resource: dict[str, Any],
        spans: list[dict[str, Any]],
    ) -> None:
        """Send a batch of spans for a single resource."""
        if not spans:
            return
        trace_resource = self._patch_resource_data_stream(resource, "traces")
        payload = {
            "resourceSpans": [
                {
                    "resource": trace_resource,
                    "scopeSpans": [
                        {
                            "scope": {"name": SCOPE_NAME},
                            "spans": spans,
                        }
                    ],
                }
            ]
        }
        self._send(f"{self.endpoint}/v1/traces", payload, "traces")

    def build_span(
        self,
        name: str,
        trace_id: str,
        span_id: str,
        parent_span_id: str | None = None,
        kind: int = 1,
        duration_ms: int = 50,
        attributes: dict[str, Any] | None = None,
        status_code: int = 1,
        events: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        start = _now_ns()
        end = str(int(start) + duration_ms * 1_000_000)
        span: dict[str, Any] = {
            "traceId": trace_id,
            "spanId": span_id,
            "name": name,
            "kind": kind,
            "startTimeUnixNano": start,
            "endTimeUnixNano": end,
            "status": {"code": status_code},
        }
        if parent_span_id:
            span["parentSpanId"] = parent_span_id
        if attributes:
            span["attributes"] = _format_attributes(attributes)
        if events:
            span["events"] = events
        return span

    @staticmethod
    def build_exception_event(
        exception_type: str,
        message: str,
        stacktrace: str | None = None,
    ) -> dict[str, Any]:
        """Build an OTel span event for an exception (powers Kibana APM Errors)."""
        attrs = {
            "exception.type": exception_type,
            "exception.message": message,
        }
        if stacktrace:
            attrs["exception.stacktrace"] = stacktrace
        return {
            "timeUnixNano": _now_ns(),
            "name": "exception",
            "attributes": _format_attributes(attrs),
        }

    # ── Internal ───────────────────────────────────────────────────────
    def _patch_resource_data_stream(
        self, resource: dict[str, Any], stream_type: str
    ) -> dict[str, Any]:
        """Return a copy of the resource with data_stream.type patched."""
        import copy

        res = copy.deepcopy(resource)
        # Remove elasticsearch.index so metrics/traces use default data_stream routing
        res["attributes"] = [
            attr
            for attr in res.get("attributes", [])
            if attr["key"] != "elasticsearch.index"
        ]
        for attr in res["attributes"]:
            if attr["key"] == "data_stream.type":
                attr["value"]["stringValue"] = stream_type
                break
        return res

    def _send(self, url: str, payload: dict, signal_name: str) -> None:
        if not self.endpoint:
            return  # No endpoint configured yet; silently drop until reconfigure() is called
        if self.consecutive_failures >= self.max_failures_before_backoff:
            # Exponential backoff — skip sending
            backoff = min(
                2 ** (self.consecutive_failures - self.max_failures_before_backoff), 30
            )
            if time.time() % backoff > 1:
                return

        try:
            response = self.client.post(url, data=json.dumps(payload))
            response.raise_for_status()
            self.consecutive_failures = 0
        except httpx.RequestError as exc:
            self.consecutive_failures += 1
            if self.consecutive_failures <= 3:
                logger.warning("OTLP %s send failed (connection): %s", signal_name, exc)
        except httpx.HTTPStatusError as exc:
            self.consecutive_failures += 1
            if self.consecutive_failures <= 3:
                logger.warning(
                    "OTLP %s send failed (HTTP %d): %s",
                    signal_name,
                    exc.response.status_code,
                    exc.response.text[:200],
                )
        except Exception as exc:
            self.consecutive_failures += 1
            if self.consecutive_failures <= 3:
                logger.warning("OTLP %s send failed: %s", signal_name, exc)

    def close(self) -> None:
        if self.client:
            self.client.close()


class ESBulkClient:
    """Posts plain ECS-shaped documents to an Elasticsearch data stream via `_bulk`.

    Used by the raw access-log generator (which deliberately bypasses OTLP so the
    demo can showcase non-OTel log onboarding and AI-driven Streams parsing).
    Silently no-ops if ELASTIC_URL / ELASTIC_API_KEY are not configured.
    """

    def __init__(
        self,
        elastic_url: str | None = None,
        api_key: str | None = None,
    ):
        from app.config import ELASTIC_URL, ELASTIC_API_KEY

        self.elastic_url = (elastic_url or ELASTIC_URL or "").strip().rstrip("/")
        self.api_key = (api_key or ELASTIC_API_KEY or "").strip()

        headers = {"Content-Type": "application/x-ndjson"}
        if self.api_key:
            headers["Authorization"] = f"ApiKey {self.api_key}"
        self.client = httpx.Client(headers=headers, http2=True, timeout=10)
        self.consecutive_failures = 0
        self.max_failures_before_backoff = 5

    @property
    def configured(self) -> bool:
        return bool(self.elastic_url and self.api_key)

    def reconfigure(self, elastic_url: str, api_key: str) -> None:
        self.elastic_url = elastic_url.strip().rstrip("/")
        self.api_key = api_key.strip()
        self.consecutive_failures = 0
        headers = {"Content-Type": "application/x-ndjson"}
        if self.api_key:
            headers["Authorization"] = f"ApiKey {self.api_key}"
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
        self.client = httpx.Client(headers=headers, http2=True, timeout=10)
        logger.info("ESBulkClient reconfigured -> %s", self.elastic_url)

    def send_bulk(self, data_stream: str, docs: list[dict[str, Any]]) -> int:
        """POST docs to {elastic_url}/{data_stream}/_bulk using `create` actions.

        Returns the number of docs the server reports as indexed (0 if request failed).
        """
        if not docs or not self.configured:
            return 0
        if self.consecutive_failures >= self.max_failures_before_backoff:
            backoff = min(
                2 ** (self.consecutive_failures - self.max_failures_before_backoff), 30
            )
            if time.time() % backoff > 1:
                return 0

        lines: list[str] = []
        for doc in docs:
            lines.append('{"create":{}}')
            lines.append(json.dumps(doc, separators=(",", ":")))
        body = "\n".join(lines) + "\n"

        url = f"{self.elastic_url}/{data_stream}/_bulk"
        try:
            resp = self.client.post(url, content=body)
            resp.raise_for_status()
            self.consecutive_failures = 0
            data = resp.json()
            if data.get("errors"):
                # Surface first error so misconfigured templates/mappings show up early.
                first = next(
                    (
                        it["create"].get("error")
                        for it in data.get("items", [])
                        if it.get("create", {}).get("error")
                    ),
                    None,
                )
                if first:
                    logger.warning("ESBulk %s partial failure: %s", data_stream, first)
            return len(docs)
        except httpx.RequestError as exc:
            self.consecutive_failures += 1
            if self.consecutive_failures <= 3:
                logger.warning("ESBulk %s send failed (connection): %s", data_stream, exc)
        except httpx.HTTPStatusError as exc:
            self.consecutive_failures += 1
            if self.consecutive_failures <= 3:
                logger.warning(
                    "ESBulk %s send failed (HTTP %d): %s",
                    data_stream,
                    exc.response.status_code,
                    exc.response.text[:200],
                )
        except Exception as exc:
            self.consecutive_failures += 1
            if self.consecutive_failures <= 3:
                logger.warning("ESBulk %s send failed: %s", data_stream, exc)
        return 0

    def close(self) -> None:
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass

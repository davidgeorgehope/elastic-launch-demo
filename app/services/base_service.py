"""Abstract base class for all NOVA-7 simulated services."""

from __future__ import annotations

import logging
import random
import secrets
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from app.config import ACTIVE_SCENARIO, CHANNEL_REGISTRY, MISSION_ID, SERVICES
from app.telemetry import OTLPClient
from app.trace_context import _trace_context_store

logger = logging.getLogger("nova7.services")


def _get_scenario():
    from scenarios import get_scenario

    return get_scenario(ACTIVE_SCENARIO)


class BaseService(ABC):
    """Base class providing telemetry emission, threading, and fault injection hooks."""

    # Subclasses MUST set this
    SERVICE_NAME: str = ""

    # Class-level context — set by ServiceManager before batch-creating services.
    # Avoids changing 37 subclass constructors.
    _context = None  # ScenarioContext | None
    _context_lock = threading.Lock()

    @classmethod
    def set_context(cls, ctx):
        """Set the scenario context for the next batch of service instantiations."""
        cls._context = ctx

    @classmethod
    def clear_context(cls):
        """Clear the class-level context after batch creation."""
        cls._context = None

    def __init__(self, chaos_controller, otlp_client: OTLPClient):
        self.chaos_controller = chaos_controller
        self.otlp = otlp_client

        # Capture context at creation time
        ctx = self.__class__._context
        if ctx:
            self._ctx = ctx
            self.service_cfg = ctx.services[self.SERVICE_NAME]
            self._channel_registry = ctx.channel_registry
            self._mission_id = ctx.mission_id
            self._namespace = ctx.namespace
        else:
            # Backward-compatible: module-level globals
            self._ctx = None
            self.service_cfg = SERVICES[self.SERVICE_NAME]
            self._channel_registry = CHANNEL_REGISTRY
            self._mission_id = MISSION_ID
            self._namespace = "nova7"

        self.resource = OTLPClient.build_resource(
            self.SERVICE_NAME,
            self.service_cfg,
            namespace=self._namespace,
        )

        # Derive nominal label from scenario (space="NOMINAL", others="NORMAL")
        if self._ctx:
            self._nominal_label = self._ctx.scenario.nominal_label
        else:
            self._nominal_label = _get_scenario().nominal_label

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._phase = "ACTIVE"
        self._status = self._nominal_label
        self._last_status_change = time.time()

    # ── Lifecycle ──────────────────────────────────────────────────────

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop, name=f"svc-{self.SERVICE_NAME}", daemon=True
        )
        self._thread.start()
        logger.info("Service %s started", self.SERVICE_NAME)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._thread = None
        logger.info("Service %s stopped", self.SERVICE_NAME)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.generate_telemetry()
            except Exception:
                logger.exception("Error in %s telemetry loop", self.SERVICE_NAME)
            interval = random.uniform(1.5, 3.0)
            self._stop_event.wait(interval)

    # ── Abstract ───────────────────────────────────────────────────────

    @abstractmethod
    def generate_telemetry(self) -> None:
        """Produce one cycle of logs/metrics/traces. Called every 1.5-3s."""
        ...

    # ── Fault injection hooks ──────────────────────────────────────────

    def is_channel_active(self, channel: int) -> bool:
        """Check if a specific chaos channel is currently active."""
        return self.chaos_controller.is_active(channel)

    def get_active_channels_for_service(self) -> list[int]:
        """Return list of active channels that affect this service."""
        active = []
        for ch_id, ch_def in self._channel_registry.items():
            if self.SERVICE_NAME in ch_def["affected_services"]:
                if self.is_channel_active(ch_id):
                    active.append(ch_id)
        return active

    def get_cascade_channels_for_service(self) -> list[int]:
        """Return list of active channels where this service is in the cascade."""
        active = []
        for ch_id, ch_def in self._channel_registry.items():
            if self.SERVICE_NAME in ch_def.get("cascade_services", []):
                if self.is_channel_active(ch_id):
                    active.append(ch_id)
        return active

    # ── Status ─────────────────────────────────────────────────────────

    def get_status(self) -> dict[str, Any]:
        active = self.get_active_channels_for_service()
        cascade = self.get_cascade_channels_for_service()
        if active:
            status = "CRITICAL"
        elif cascade:
            status = "WARNING"
        else:
            status = self._nominal_label
        self._status = status
        return {
            "service": self.SERVICE_NAME,
            "subsystem": self.service_cfg["subsystem"],
            "cloud_provider": self.service_cfg["cloud_provider"],
            "cloud_region": self.service_cfg["cloud_region"],
            "status": status,
            "phase": self._phase,
            "active_faults": active,
            "cascade_faults": cascade,
        }

    def set_phase(self, phase: str) -> None:
        self._phase = phase

    # ── Telemetry helpers ──────────────────────────────────────────────

    def _base_log_attrs(self) -> dict[str, Any]:
        """Fields required on every log record."""
        return {
            "ops.mission_id": self._mission_id,
            "ops.phase": self._phase,
            "system.subsystem": self.service_cfg["subsystem"],
            "system.status": self._status,
        }

    def emit_log(
        self,
        level: str,
        message: str,
        extra_attrs: dict[str, Any] | None = None,
        event_name: str | None = None,
    ) -> None:
        attrs = self._base_log_attrs()
        if extra_attrs:
            attrs.update(extra_attrs)
        trace_id, span_id = _trace_context_store.get(self.SERVICE_NAME)
        record = self.otlp.build_log_record(
            severity=level,
            body=message,
            attributes=attrs,
            event_name=event_name,
            trace_id=trace_id,
            span_id=span_id,
        )
        self.otlp.send_logs(self.resource, [record])

    def emit_metric(
        self,
        name: str,
        value: float,
        unit: str = "",
        extra_attrs: dict[str, Any] | None = None,
    ) -> None:
        attrs = extra_attrs or {}
        metric = self.otlp.build_gauge(name, value, unit, attrs)
        self.otlp.send_metrics(self.resource, [metric])

    def emit_trace(
        self,
        span_name: str,
        duration_ms: int = 50,
        extra_attrs: dict[str, Any] | None = None,
        status_code: int = 1,
        events: list[dict[str, Any]] | None = None,
    ) -> None:
        trace_id = secrets.token_hex(16)
        span_id = secrets.token_hex(8)
        attrs = self._base_log_attrs()
        if extra_attrs:
            attrs.update(extra_attrs)
        span = self.otlp.build_span(
            name=span_name,
            trace_id=trace_id,
            span_id=span_id,
            duration_ms=duration_ms,
            attributes=attrs,
            status_code=status_code,
            events=events,
        )
        self.otlp.send_traces(self.resource, [span])

    @staticmethod
    def _safe_format(template: str, params: dict) -> str:
        """Format a template string, ignoring missing keys."""
        import string

        class SafeDict(dict):
            def __missing__(self, key):
                return f"{{{key}}}"

        return string.Formatter().vformat(template, (), SafeDict(params))

    def emit_fault_logs(self, channel: int) -> None:
        """Emit error logs matching the channel's exact error signature."""
        ch = self._channel_registry.get(channel)
        if not ch:
            return

        # Emit one-shot infrastructure events (idempotent — tracked internally)
        self.emit_infrastructure_events(channel)

        # Generate 2-4 error logs per cycle when channel is active
        for _ in range(random.randint(2, 4)):
            fault_params = self._generate_fault_params(channel)
            msg = self._safe_format(ch["error_message"], fault_params)
            stack = self._safe_format(ch["stack_trace"], fault_params)

            attrs = self._base_log_attrs()
            attrs.update(
                {
                    "error.type": ch["error_type"],
                    "sensor.type": ch["sensor_type"],
                    "vehicle_section": ch["vehicle_section"],
                    "chaos.channel": channel,
                    "chaos.fault_type": ch["name"],
                    "exception.type": ch["error_type"],
                    "exception.message": msg,
                    "exception.stacktrace": stack,
                    "system.status": "CRITICAL",
                }
            )
            # Inject callback URL and user email for workflow auto-remediation
            meta = self.chaos_controller.get_channel_metadata(channel)
            if meta.get("callback_url"):
                attrs["chaos.callback_url"] = meta["callback_url"]
            if meta.get("user_email"):
                attrs["chaos.user_email"] = meta["user_email"]

            # Set event_name with remediation metadata (indexed keyword field)
            ev_name = None
            if meta.get("callback_url") or meta.get("user_email"):
                import json as _json

                ev_name = _json.dumps(
                    {
                        "callback_url": meta.get("callback_url", ""),
                        "user_email": meta.get("user_email", ""),
                        "deployment_id": self._ctx.scenario_id if self._ctx else "",
                    }
                )
            self.emit_log("ERROR", msg, attrs, event_name=ev_name)

    def emit_cascade_logs(self, channel: int) -> None:
        """Emit warning logs for cascading effects (not matching the SE query)."""
        ch = self._channel_registry.get(channel)
        if not ch:
            return
        error_type = ch.get("error_type", "unknown")
        messages = [
            f"Upstream dependency alert: {ch['subsystem']} reporting {error_type} — monitoring {ch['vehicle_section']} for cascade impact",
            f"Anomalous telemetry from {ch['vehicle_section']}: correlated with {error_type} in {ch['subsystem']} subsystem",
            f"Health check degraded: elevated error rate in {ch['subsystem']} dependency, see {error_type} for root cause",
        ]
        attrs = self._base_log_attrs()
        attrs.update(
            {
                "cascade.source_channel": channel,
                "cascade.source_subsystem": ch["subsystem"],
                "system.status": "WARNING",
            }
        )
        self.emit_log("WARN", random.choice(messages), attrs)

    def emit_infrastructure_events(self, channel: int) -> None:
        """Emit one-shot infrastructure/audit events when a channel fires.

        Reads optional 'infrastructure_events' list from channel_registry entry.
        Each event: {body, severity, event_name, attributes, service (optional)}.
        Events are only emitted once per channel activation.
        """
        if not hasattr(self, "_infra_events_emitted"):
            self._infra_events_emitted: set[tuple[int, int]] = set()

        ch = self._channel_registry.get(channel)
        if not ch:
            return
        infra_events = ch.get("infrastructure_events", [])
        if not infra_events:
            return

        for idx, evt in enumerate(infra_events):
            # Only emit for this service (or if no service filter specified)
            evt_service = evt.get("service")
            if evt_service and evt_service != self.SERVICE_NAME:
                continue

            key = (channel, idx)
            if key in self._infra_events_emitted:
                continue
            self._infra_events_emitted.add(key)

            attrs = self._base_log_attrs()
            if evt.get("attributes"):
                attrs.update(evt["attributes"])
            attrs["chaos.channel"] = channel
            attrs["infrastructure.event"] = True

            self.emit_log(
                evt.get("severity", "WARN"),
                evt["body"],
                attrs,
                event_name=evt.get("event_name"),
            )

    def reset_infrastructure_events(self) -> None:
        """Clear tracked infrastructure events (call on channel resolve)."""
        if hasattr(self, "_infra_events_emitted"):
            self._infra_events_emitted.clear()

    def _generate_fault_params(self, channel: int) -> dict[str, Any]:
        """Generate realistic random parameters for fault messages from scenario."""
        if self._ctx:
            return self._ctx.scenario.get_fault_params(channel)
        return _get_scenario().get_fault_params(channel)

"""Service Manager — starts/stops all simulated services, generators, and manages countdown."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Optional

from app.config import (
    COUNTDOWN_ENABLED,
    COUNTDOWN_SPEED,
    COUNTDOWN_START_SECONDS,
    SERVICES,
    ACTIVE_SCENARIO,
)
from app.telemetry import ESBulkClient, OTLPClient

logger = logging.getLogger("nova7.manager")


class ServiceManager:
    """Manages all service instances, log generators, and the mission countdown clock."""

    def __init__(
        self,
        chaos_controller,
        ctx=None,
        otlp_client: OTLPClient | None = None,
    ):
        self.chaos_controller = chaos_controller
        self._ctx = ctx  # ScenarioContext or None
        self.otlp = otlp_client or OTLPClient()
        self.es_bulk = ESBulkClient()
        self.services: dict[str, Any] = {}

        # Countdown state — from context or module-level defaults
        if ctx:
            _countdown = ctx.scenario.countdown_config
            self._countdown_total = (
                _countdown.start_seconds if _countdown.enabled else 600
            )
            self._countdown_speed = _countdown.speed if _countdown.enabled else 1.0
            self._countdown_enabled = _countdown.enabled
            self._countdown_phases = _countdown.phases
        else:
            self._countdown_total = COUNTDOWN_START_SECONDS
            self._countdown_speed = COUNTDOWN_SPEED
            self._countdown_enabled = COUNTDOWN_ENABLED
            self._countdown_phases = {
                "PRE-LAUNCH": (300, 9999),
                "COUNTDOWN": (60, 300),
                "FINAL-COUNTDOWN": (0, 60),
                "LAUNCH": (0, 0),
            }

        self._countdown_remaining = float(self._countdown_total)
        self._countdown_running = False
        self._countdown_thread: Optional[threading.Thread] = None
        self._countdown_lock = threading.Lock()
        self._stop_event = threading.Event()

        # Generator threads
        self._generator_threads: list[threading.Thread] = []

        self._init_services()

    def _init_services(self) -> None:
        """Dynamically load and instantiate services from the active scenario."""
        from app.services.base_service import BaseService

        if self._ctx:
            scenario = self._ctx.scenario
        else:
            import os
            from scenarios import get_scenario

            active = os.environ.get("ACTIVE_SCENARIO", ACTIVE_SCENARIO)
            scenario = get_scenario(active)

        service_classes = scenario.get_service_classes()

        with BaseService._context_lock:
            BaseService.set_context(self._ctx)
            try:
                for cls in service_classes:
                    svc = cls(self.chaos_controller, self.otlp)
                    self.services[svc.SERVICE_NAME] = svc
            finally:
                BaseService.clear_context()

    def start_all(self) -> None:
        for svc in self.services.values():
            svc.start()
        if self._countdown_enabled:
            self._start_countdown_thread()
        self._start_generators()
        logger.info("All %d services + generators started", len(self.services))

    def stop_all(self) -> None:
        self._stop_event.set()
        if self._countdown_thread and self._countdown_thread.is_alive():
            self._countdown_thread.join(timeout=3)
        for t in self._generator_threads:
            t.join(timeout=5)
        for svc in self.services.values():
            svc.stop()
        self.otlp.close()
        self.es_bulk.close()
        logger.info("All services and generators stopped")

    # ── Generators ────────────────────────────────────────────────────

    def _start_generators(self) -> None:
        """Start log/trace/metrics generators as daemon threads."""
        from log_generators.trace_generator import run as run_traces
        from log_generators.host_metrics_generator import run as run_metrics
        from log_generators.nginx_log_generator import run as run_nginx
        from log_generators.mysql_log_generator import run as run_mysql
        from log_generators.k8s_metrics_generator import run as run_k8s
        from log_generators.nginx_metrics_generator import run as run_nginx_metrics
        from log_generators.vpc_flow_generator import run as run_vpc
        from log_generators.jvm_metrics_generator import run as run_jvm
        from log_generators.raw_access_log_generator import run as run_raw_access

        # Build scenario_data dict from context for scenario-dependent generators
        scenario_data = None
        if self._ctx:
            scenario = self._ctx.scenario
            scenario_data = {
                "services": self._ctx.services,
                "channel_registry": self._ctx.channel_registry,
                "namespace": self._ctx.namespace,
                "hosts": scenario.hosts,
                "k8s_clusters": scenario.k8s_clusters,
                "service_topology": scenario.service_topology,
                "entry_endpoints": scenario.entry_endpoints,
                "db_operations": scenario.db_operations,
                "scenario": scenario,
            }

        # Trace generator needs chaos_controller and scenario_data
        trace_args = (self.otlp, self._stop_event, self.chaos_controller)
        trace_kwargs = {"scenario_data": scenario_data} if scenario_data else {}

        # Host metrics generator needs chaos_controller and scenario_data
        host_args = (self.otlp, self._stop_event)
        host_kwargs = {"scenario_data": scenario_data} if scenario_data else {}
        host_kwargs["chaos_controller"] = self.chaos_controller

        # K8s metrics generator needs chaos_controller and scenario_data
        k8s_args = (self.otlp, self._stop_event)
        k8s_kwargs = {"scenario_data": scenario_data} if scenario_data else {}
        k8s_kwargs["chaos_controller"] = self.chaos_controller

        # Common args/kwargs for generators that accept scenario_data
        common_args = (self.otlp, self._stop_event)
        common_kwargs = {"scenario_data": scenario_data} if scenario_data else {}

        # Determine which infra generators to start based on scenario services
        _svc_names = set(scenario_data["services"].keys()) if scenario_data else set()

        # Raw access-log generator uses ESBulkClient instead of OTLPClient
        raw_access_args = (self.es_bulk, self._stop_event)
        raw_access_kwargs = {"scenario_data": scenario_data} if scenario_data else {}

        generators = [
            ("gen-traces", run_traces, trace_args, trace_kwargs),
            ("gen-host-metrics", run_metrics, host_args, host_kwargs),
            ("gen-k8s-metrics", run_k8s, k8s_args, k8s_kwargs),
            ("gen-jvm-metrics", run_jvm, common_args, common_kwargs),
            ("gen-vpc-flow", run_vpc, common_args, common_kwargs),
            ("gen-raw-access", run_raw_access, raw_access_args, raw_access_kwargs),
        ]
        # Only start nginx/mysql generators if their service is in the scenario
        if not _svc_names or "nginx-proxy" in _svc_names:
            generators.append(("gen-nginx", run_nginx, common_args, common_kwargs))
            generators.append(("gen-nginx-metrics", run_nginx_metrics, common_args, common_kwargs))
        if not _svc_names or "mysql-primary" in _svc_names:
            generators.append(("gen-mysql", run_mysql, common_args, common_kwargs))
        for name, fn, args, kwargs in generators:
            t = threading.Thread(
                target=fn,
                args=args,
                kwargs=kwargs,
                name=name,
                daemon=True,
            )
            t.start()
            self._generator_threads.append(t)
            logger.info("Started generator thread: %s", name)

    def get_generator_status(self) -> dict[str, str]:
        """Return status of each generator thread."""
        return {
            t.name: "running" if t.is_alive() else "stopped"
            for t in self._generator_threads
        }

    # ── Countdown ──────────────────────────────────────────────────────

    def _start_countdown_thread(self) -> None:
        self._countdown_thread = threading.Thread(
            target=self._countdown_loop, name="countdown", daemon=True
        )
        self._countdown_thread.start()

    def _countdown_loop(self) -> None:
        last_tick = time.time()
        while not self._stop_event.is_set():
            now = time.time()
            dt = now - last_tick
            last_tick = now

            with self._countdown_lock:
                if self._countdown_running and self._countdown_remaining > 0:
                    self._countdown_remaining -= dt * self._countdown_speed
                    if self._countdown_remaining < 0:
                        self._countdown_remaining = 0

                    # Phase transitions based on countdown_config.phases
                    remaining = self._countdown_remaining
                    phase = "ACTIVE"
                    for p_name, (p_min, p_max) in self._countdown_phases.items():
                        if p_min <= remaining <= p_max:
                            phase = p_name
                            break

                    for svc in self.services.values():
                        svc.set_phase(phase)

            self._stop_event.wait(0.5)

    def countdown_start(self) -> None:
        with self._countdown_lock:
            self._countdown_running = True

    def countdown_pause(self) -> None:
        with self._countdown_lock:
            self._countdown_running = False

    def countdown_reset(self) -> None:
        with self._countdown_lock:
            self._countdown_remaining = float(self._countdown_total)
            self._countdown_running = False

    def countdown_set_speed(self, speed: float) -> None:
        with self._countdown_lock:
            self._countdown_speed = max(0.1, min(100.0, speed))

    def get_countdown(self) -> dict[str, Any]:
        with self._countdown_lock:
            remaining = max(0.0, self._countdown_remaining)
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            return {
                "remaining_seconds": round(remaining, 1),
                "display": f"T-{minutes:02d}:{seconds:02d}",
                "running": self._countdown_running,
                "speed": self._countdown_speed,
                "enabled": self._countdown_enabled,
            }

    def get_all_status(self) -> dict[str, Any]:
        return {name: svc.get_status() for name, svc in self.services.items()}

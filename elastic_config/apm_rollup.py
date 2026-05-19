"""Generic APM rollup data generator — produces synthetic transaction.1m,
service_destination.1m, and service_summary.1m docs from any BaseScenario.

These rollup metrics power:
- APM Services list (transaction counts, latency, error rate)
- APM Service Map (edges between services, dependency nodes)
- ML anomaly detection (latency/throughput/failure_rate detectors)

All definitions are derived from the scenario's services, service_topology,
entry_endpoints, and db_operations properties — no hardcoded service names.
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from scenarios.base import BaseScenario

logger = logging.getLogger("apm-rollup")

# Agent name mapping — matches what the EDOT Collector writes
_AGENT_NAME = {
    "java": "opentelemetry/java",
    "python": "opentelemetry/python",
    "go": "opentelemetry/go",
    "cpp": "opentelemetry/cpp",
    "dotnet": "opentelemetry/dotnet",
    "rust": "opentelemetry/rust",
}

# Runtime attributes per language
_RUNTIME = {
    "java": {"process.runtime.name": "OpenJDK Runtime Environment",
             "process.runtime.version": "21.0.5+11-LTS"},
    "python": {"process.runtime.name": "CPython",
               "process.runtime.version": "3.12.3"},
    "go": {"process.runtime.name": "go",
            "process.runtime.version": "go1.22.4"},
    "cpp": {"process.runtime.name": "gcc",
             "process.runtime.version": "13.2.0"},
    "dotnet": {"process.runtime.name": ".NET",
               "process.runtime.version": "8.0.6"},
    "rust": {"process.runtime.name": "rustc",
             "process.runtime.version": "1.79.0"},
}

SCOPE_NAME = "github.com/open-telemetry/opentelemetry-collector-contrib/connector/signaltometricsconnector"


# ── Internal data structures ──────────────────────────────────────────────

@dataclass
class TxDef:
    """Transaction definition derived from scenario metadata."""
    name: str           # e.g. "POST /api/v1/activate"
    is_root: bool       # True if from entry_endpoints
    baseline_us: float  # derived from topology depth
    rate_fraction: float  # share of traffic


@dataclass
class SdEdge:
    """Service destination edge derived from scenario topology."""
    caller: str
    resource: str        # callee-host:8080 or db-resource-name
    span_name: str       # "POST /endpoint" or "SELECT table"
    target_name: str
    target_type: str     # "http" or "postgresql"
    baseline_us: float


# ── Main generator class ──────────────────────────────────────────────────

class ApmRollupGenerator:
    """Generates synthetic APM rollup data from any BaseScenario."""

    def __init__(
        self,
        scenario: BaseScenario,
        elastic_url: str,
        api_key: str,
    ):
        self.scenario = scenario
        self.elastic_url = elastic_url.rstrip("/")
        self.api_key = api_key
        self._services = scenario.services
        self._namespace = scenario.namespace

        self._instrumented = self._identify_instrumented_services()
        self._tx_defs = self._derive_transaction_defs()
        self._sd_edges = self._derive_service_destination_edges()
        self._baseline_latencies = self._compute_baseline_latencies()

    # ── Derivation from scenario ──────────────────────────────────────

    def _identify_instrumented_services(self) -> list[str]:
        """Services whose subsystem != 'database'. These get transaction/summary docs."""
        return [
            name for name, cfg in self._services.items()
            if cfg.get("subsystem") != "database"
        ]

    def _derive_transaction_defs(self) -> dict[str, list[TxDef]]:
        """Build transaction definitions from entry_endpoints + topology."""
        defs: dict[str, list[TxDef]] = {}
        entry_eps = self.scenario.entry_endpoints
        topology = self.scenario.service_topology

        # Collect callee transactions from topology (internal, non-root)
        callee_txs: dict[str, set[tuple[str, str]]] = {}  # svc -> set of (endpoint, method)
        for caller, calls in topology.items():
            for callee, endpoint, method in calls:
                if callee in self._instrumented:
                    callee_txs.setdefault(callee, set()).add((endpoint, method))

        for svc in self._instrumented:
            txs: list[TxDef] = []

            # Root transactions from entry_endpoints
            if svc in entry_eps:
                eps = entry_eps[svc]
                for i, (path, method) in enumerate(eps):
                    tx_name = f"{method} {path}"
                    # First endpoint gets 60% of traffic, rest split evenly
                    if i == 0:
                        frac = 0.60
                    else:
                        frac = 0.40 / max(1, len(eps) - 1)
                    txs.append(TxDef(
                        name=tx_name,
                        is_root=True,
                        baseline_us=0,  # filled in by _compute_baseline_latencies
                        rate_fraction=frac,
                    ))

            # Internal transactions from being called by upstream services
            if svc in callee_txs:
                for endpoint, method in callee_txs[svc]:
                    tx_name = f"{method} {endpoint}"
                    # Skip if already added as root
                    if any(t.name == tx_name for t in txs):
                        continue
                    txs.append(TxDef(
                        name=tx_name,
                        is_root=False,
                        baseline_us=0,
                        rate_fraction=0.30,  # internal calls
                    ))

            # Normalize rate fractions
            total = sum(t.rate_fraction for t in txs)
            if total > 0:
                for t in txs:
                    t.rate_fraction /= total

            defs[svc] = txs

        return defs

    def _derive_service_destination_edges(self) -> list[SdEdge]:
        """Build SD edges from service_topology + db_operations."""
        edges: list[SdEdge] = []
        topology = self.scenario.service_topology
        db_ops = self.scenario.db_operations

        # HTTP edges from topology (skip database callees — handled by db_operations)
        db_services = {
            name for name, cfg in self._services.items()
            if cfg.get("subsystem") == "database"
        }
        for caller, calls in topology.items():
            if caller not in self._instrumented:
                continue
            for callee, endpoint, method in calls:
                if callee in db_services:
                    continue  # DB deps come from db_operations below
                resource = f"{callee}-host:8080"
                span_name = f"{method} {endpoint}"
                edges.append(SdEdge(
                    caller=caller,
                    resource=resource,
                    span_name=span_name,
                    target_name=resource,
                    target_type="http",
                    baseline_us=0,  # filled in later
                ))

        # Build map: app_service → database_service from topology
        svc_to_db: dict[str, str] = {}
        for caller, calls in topology.items():
            if caller in db_services:
                continue
            for callee, _ep, _method in calls:
                if callee in db_services:
                    svc_to_db[caller] = callee

        # DB edges from db_operations — use DB service name as resource
        for svc, ops in db_ops.items():
            if svc not in self._instrumented:
                continue
            db_svc = svc_to_db.get(svc)
            seen_resources: set[str] = set()
            for op, table, statement in ops:
                # Resource = DB service name (matches ingest pipeline rewrite)
                # Falls back to {namespace}_{table} if no DB service in topology
                resource = db_svc if db_svc else f"{self._namespace}_{table}"
                span_name = f"{op} {table}"
                edge_key = f"{svc}:{resource}:{span_name}"
                if edge_key in seen_resources:
                    continue
                seen_resources.add(edge_key)
                edges.append(SdEdge(
                    caller=svc,
                    resource=resource,
                    span_name=span_name,
                    target_name=resource,
                    target_type="postgresql",
                    baseline_us=0,
                ))

        return edges

    def _compute_baseline_latencies(self) -> dict[str, float]:
        """Compute baseline latency per service based on call graph depth."""
        topology = self.scenario.service_topology

        # Compute depth from leaves
        depths: dict[str, int] = {}

        def _depth(svc: str, visited: set[str]) -> int:
            if svc in depths:
                return depths[svc]
            if svc in visited:
                return 0
            visited.add(svc)
            downstream = topology.get(svc, [])
            if not downstream:
                depths[svc] = 0
                return 0
            max_d = max(_depth(callee, visited) for callee, _, _ in downstream)
            depths[svc] = max_d + 1
            return max_d + 1

        for svc in self._instrumented:
            _depth(svc, set())

        max_depth = max(depths.values()) if depths else 0
        latencies: dict[str, float] = {}
        for svc in self._instrumented:
            d = depths.get(svc, 0)
            if d == 0:
                latencies[svc] = 30_000  # 30ms leaf
            elif d == max_depth:
                latencies[svc] = 150_000  # 150ms entry
            else:
                # Linear interpolation
                frac = d / max(1, max_depth)
                latencies[svc] = 30_000 + frac * 120_000

        # Apply to transaction defs
        for svc, txs in self._tx_defs.items():
            base = latencies.get(svc, 50_000)
            for tx in txs:
                tx.baseline_us = base

        # Apply to SD edges (use callee latency for HTTP, 15ms for DB)
        for edge in self._sd_edges:
            if edge.target_type == "postgresql":
                edge.baseline_us = 15_000  # 15ms DB call
            else:
                # Extract callee from resource (e.g. "activation-service-host:8080")
                callee = edge.resource.replace("-host:8080", "")
                edge.baseline_us = latencies.get(callee, 50_000)

        return latencies

    # ── Document builders ──────────────────────────────────────────────

    def _build_resource_attrs(self, service_name: str) -> dict[str, Any]:
        """Build resource attributes matching the EDOT Collector output."""
        cfg = self._services[service_name]
        lang = cfg.get("language", "python")
        attrs = {
            "agent.name": _AGENT_NAME.get(lang, f"opentelemetry/{lang}"),
            "cloud.availability_zone": cfg["cloud_availability_zone"],
            "cloud.platform": cfg["cloud_platform"],
            "cloud.provider": cfg["cloud_provider"],
            "cloud.region": cfg["cloud_region"],
            "deployment.environment": f"production-{self._namespace}",
            "host.name": f"{service_name}-host",
            "os.type": "linux",
            "service.instance.id": f"{service_name}-001",
            "service.name": service_name,
            "service.version": "1.0.0",
            "signaltometrics.service.instance.id": "cd94ea0b-dbdb-4cfc-b3a2-83bc74357984",
            "telemetry.sdk.language": lang,
            "telemetry.sdk.version": "1.24.0",
        }
        if lang in _RUNTIME:
            attrs.update(_RUNTIME[lang])
        return attrs

    def _build_tx_doc(
        self,
        timestamp: datetime,
        service_name: str,
        tx: TxDef,
        outcome: str,
        count: int,
        mean_latency_us: float,
        rng: random.Random,
    ) -> dict:
        """Build a single transaction.1m rollup document."""
        resource_attrs = self._build_resource_attrs(service_name)
        hist = _make_histogram(mean_latency_us, count, rng)
        total_duration = mean_latency_us * count

        return {
            "@timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "_doc_count": count,
            "_metric_names_hash": hashlib.md5(
                f"{service_name}:{tx.name}:{outcome}:{tx.is_root}".encode()
            ).hexdigest()[:16],
            "attributes": {
                "event.outcome": outcome,
                "metricset.interval": "1m",
                "metricset.name": "transaction",
                "processor.event": "metric",
                "transaction.name": tx.name,
                "transaction.result": "HTTP 2xx" if outcome == "success" else "HTTP 5xx",
                "transaction.root": tx.is_root,
                "transaction.type": "request",
            },
            "data_stream": {
                "dataset": "transaction.1m.otel",
                "namespace": "default",
                "type": "metrics",
            },
            "metrics": {
                "transaction.duration.histogram": hist,
                "transaction.duration.summary": {
                    "sum": total_duration,
                    "value_count": count,
                },
            },
            "resource": {"attributes": resource_attrs},
            "scope": {"name": SCOPE_NAME},
            "unit": "us",
        }

    def _build_sd_doc(
        self,
        timestamp: datetime,
        edge: SdEdge,
        outcome: str,
        count: int,
        total_duration_us: float,
    ) -> dict:
        """Build a single service_destination.1m rollup document."""
        cfg = self._services[edge.caller]
        lang = cfg.get("language", "python")
        resource_attrs = {
            "agent.name": _AGENT_NAME.get(lang, f"opentelemetry/{lang}"),
            "deployment.environment": f"production-{self._namespace}",
            "service.name": edge.caller,
            "signaltometrics.service.instance.id": "cd94ea0b-dbdb-4cfc-b3a2-83bc74357984",
            "telemetry.sdk.language": lang,
        }
        return {
            "@timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "_doc_count": count,
            "attributes": {
                "event.outcome": outcome,
                "metricset.interval": "1m",
                "metricset.name": "service_destination",
                "processor.event": "metric",
                "service.target.name": edge.target_name,
                "service.target.type": edge.target_type,
                "span.destination.service.resource": edge.resource,
                "span.name": edge.span_name,
            },
            "data_stream": {
                "dataset": "service_destination.1m.otel",
                "namespace": "default",
                "type": "metrics",
            },
            "metrics": {
                "span.destination.service.response_time.count": count,
                "span.destination.service.response_time.sum.us": total_duration_us,
            },
            "resource": {"attributes": resource_attrs},
            "scope": {"name": SCOPE_NAME},
            "unit": "us",
        }

    def _build_summary_doc(
        self,
        timestamp: datetime,
        service_name: str,
        count: int,
    ) -> dict:
        """Build a single service_summary.1m rollup document."""
        cfg = self._services[service_name]
        lang = cfg.get("language", "python")
        resource_attrs = {
            "agent.name": _AGENT_NAME.get(lang, f"opentelemetry/{lang}"),
            "deployment.environment": f"production-{self._namespace}",
            "service.name": service_name,
            "signaltometrics.service.instance.id": "cd94ea0b-dbdb-4cfc-b3a2-83bc74357984",
            "telemetry.sdk.language": lang,
        }
        return {
            "@timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "attributes": {
                "metricset.interval": "1m",
                "metricset.name": "service_summary",
                "processor.event": "metric",
            },
            "metrics": {
                "service_summary": count,
            },
            "data_stream": {
                "dataset": "service_summary.1m.otel",
                "namespace": "default",
                "type": "metrics",
            },
            "resource": {"attributes": resource_attrs},
            "scope": {"name": SCOPE_NAME},
        }

    # ── Generation ────────────────────────────────────────────────────

    def generate_all(self, hours: int = 12, seed: int = 42) -> dict[str, int]:
        """Generate and insert all three rollup types. Returns doc counts."""
        counts = {}
        counts["transaction_1m"] = self._generate_transaction_rollups(hours, seed)
        counts["service_destination_1m"] = self._generate_sd_rollups(hours, seed + 1)
        counts["service_summary_1m"] = self._generate_summary_rollups(hours, seed + 2)
        return counts

    def _generate_transaction_rollups(self, hours: int, seed: int) -> int:
        """Generate transaction.1m docs for baseline period."""
        rng = random.Random(seed)
        docs: list[dict] = []
        now = datetime.now(timezone.utc)
        current = now - timedelta(hours=hours)
        end = now
        interval = timedelta(minutes=1)
        base_rate = 5  # requests/min per service

        while current <= end:
            for svc in self._instrumented:
                txs = self._tx_defs.get(svc, [])
                for tx in txs:
                    count = max(1, int(base_rate * tx.rate_fraction))
                    # Baseline: 1% error rate
                    fail_count = max(0, int(count * 0.01))
                    success_count = count - fail_count

                    jitter = rng.uniform(0.90, 1.10)
                    latency = tx.baseline_us * jitter

                    if success_count > 0:
                        docs.append(self._build_tx_doc(
                            current, svc, tx, "success",
                            success_count, latency, rng,
                        ))
                    if fail_count > 0:
                        docs.append(self._build_tx_doc(
                            current, svc, tx, "failure",
                            fail_count, latency * 1.5, rng,
                        ))

            current += interval

        if not docs:
            return 0
        return self._bulk_insert(
            "metrics-transaction.1m.otel-default", docs, "transaction.1m",
        )

    def _generate_sd_rollups(self, hours: int, seed: int) -> int:
        """Generate service_destination.1m docs for baseline period."""
        rng = random.Random(seed)
        docs: list[dict] = []
        now = datetime.now(timezone.utc)
        current = now - timedelta(hours=hours)
        end = now
        interval = timedelta(minutes=1)
        base_count = 3  # calls/min per edge

        while current <= end:
            for edge in self._sd_edges:
                jitter = rng.uniform(0.90, 1.10)
                latency = edge.baseline_us * jitter

                docs.append(self._build_sd_doc(
                    current, edge, "success",
                    base_count, latency * base_count,
                ))

            current += interval

        if not docs:
            return 0
        return self._bulk_insert(
            "metrics-service_destination.1m.otel-default", docs,
            "service_destination.1m",
        )

    def _generate_summary_rollups(self, hours: int, seed: int) -> int:
        """Generate service_summary.1m docs for baseline period."""
        rng = random.Random(seed)
        docs: list[dict] = []
        now = datetime.now(timezone.utc)
        current = now - timedelta(hours=hours)
        end = now
        interval = timedelta(minutes=1)
        base_count = 5

        while current <= end:
            for svc in self._instrumented:
                count = base_count + rng.randint(-1, 1)
                docs.append(self._build_summary_doc(current, svc, max(1, count)))
            current += interval

        if not docs:
            return 0
        return self._bulk_insert(
            "metrics-service_summary.1m.otel-default", docs,
            "service_summary.1m",
        )

    # ── Bulk insert ───────────────────────────────────────────────────

    def _bulk_insert(
        self,
        data_stream: str,
        docs: list[dict],
        label: str,
    ) -> int:
        """Bulk-insert docs into an ES data stream. Returns count inserted."""
        logger.info("Inserting %d %s docs...", len(docs), label)
        headers = {
            "Content-Type": "application/x-ndjson",
            "Authorization": f"ApiKey {self.api_key}",
        }
        inserted = 0

        with httpx.Client(timeout=30.0, verify=True) as client:
            for batch_start in range(0, len(docs), 500):
                batch = docs[batch_start:batch_start + 500]
                lines = []
                for doc in batch:
                    lines.append(json.dumps({"create": {}}))
                    lines.append(json.dumps(doc))
                body = "\n".join(lines) + "\n"

                r = client.post(
                    f"{self.elastic_url}/{data_stream}/_bulk",
                    content=body,
                    headers=headers,
                )
                if r.status_code == 200:
                    result = r.json()
                    items = result.get("items", [])
                    ok = sum(
                        1 for item in items
                        if item.get("create", {}).get("status") in (200, 201)
                    )
                    inserted += ok
                    if result.get("errors"):
                        for item in items:
                            err = item.get("create", {}).get("error")
                            if err:
                                logger.warning(
                                    "%s bulk error: %s", label,
                                    json.dumps(err)[:200],
                                )
                                break
                else:
                    logger.warning(
                        "%s bulk failed: %d %s", label,
                        r.status_code, r.text[:200],
                    )

        logger.info("%s: %d/%d docs inserted", label, inserted, len(docs))
        return inserted


# ── Histogram helper ──────────────────────────────────────────────────────

def _make_histogram(mean_us: float, count: int, rng: random.Random) -> dict:
    """Build a simple histogram with buckets centred around the mean."""
    spread = max(mean_us * 0.3, 1000)
    buckets = min(7, max(1, count))

    if buckets == 1:
        return {"values": [mean_us], "counts": [count]}

    weights = [0.05, 0.10, 0.20, 0.30, 0.20, 0.10, 0.05]
    if buckets < 7:
        start = (7 - buckets) // 2
        weights = weights[start:start + buckets]
        total_w = sum(weights)
        weights = [w / total_w for w in weights]

    values = []
    counts_list = []
    for i in range(buckets):
        frac = (i - buckets // 2) / max(1, buckets // 2)
        val = mean_us + frac * spread + rng.uniform(-spread * 0.05, spread * 0.05)
        values.append(max(1.0, val))
        counts_list.append(max(1, int(count * weights[i])))

    diff = count - sum(counts_list)
    counts_list[buckets // 2] += diff
    return {"values": values, "counts": counts_list}

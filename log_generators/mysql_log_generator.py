#!/usr/bin/env python3
"""MySQL Log Generator — sends mysqlreceiver OTel events and metrics via OTLP.

Emits data matching the mysql_otel content package (discovery.datasets: mysqlreceiver),
which triggers Fleet auto-install and populates the bundled Overview / Performance /
Queries / Availability dashboards.

Signal types emitted:
  - Log events: db.server.query_sample (active queries) and db.server.top_query (digest summary)
  - Metrics: mysql.query.*, mysql.buffer_pool.*, mysql.events_statements_summary_by_digest.*,
             mysql.events_waits_current.timer_wait, mysql.table.*
  - Traces: correlated DB spans for APM Service Map topology (optional, per scenario)

Usage (standalone):
    python3 -m log_generators.mysql_log_generator
"""

from __future__ import annotations

import logging
import os
import random
import secrets
import signal
import threading
import time

from app.telemetry import OTLPClient, _format_attributes, SCHEMA_URL, _now_ns
from app.config import NAMESPACE

_DB_PREFIX = NAMESPACE.replace("-", "_")

SPAN_KIND_CLIENT = 3
STATUS_OK = 1
STATUS_ERROR = 2

MYSQL_SCOPE = (
    "github.com/open-telemetry/opentelemetry-collector-contrib/receiver/mysqlreceiver"
)
SCOPE_VERSION = "0.115.0"

logger = logging.getLogger("mysql-log-generator")

BATCH_INTERVAL_MIN = 2
BATCH_INTERVAL_MAX = 5
BATCH_SIZE_MIN = 3
BATCH_SIZE_MAX = 12

DATABASES = [
    f"{_DB_PREFIX}_telemetry",
    f"{_DB_PREFIX}_mission",
    f"{_DB_PREFIX}_sensors",
    f"{_DB_PREFIX}_audit",
]

TABLES = {
    f"{_DB_PREFIX}_telemetry": [
        "telemetry_readings", "sensor_data", "metric_snapshots",
        "log_entries", "trace_spans",
    ],
    f"{_DB_PREFIX}_mission": [
        "mission_events", "countdown_phases", "launch_parameters",
        "abort_criteria", "hold_records",
    ],
    f"{_DB_PREFIX}_sensors": [
        "sensor_calibrations", "sensor_registry", "calibration_epochs",
        "sensor_thresholds", "validation_results",
    ],
    f"{_DB_PREFIX}_audit": [
        "remediation_log", "escalation_log", "agent_actions",
        "operator_decisions", "safety_assessments",
    ],
}

QUERY_TEMPLATES = [
    ("SELECT", "SELECT * FROM telemetry_readings WHERE timestamp > NOW() - INTERVAL 5 MINUTE AND subsystem = '{subsystem}' ORDER BY timestamp DESC LIMIT 1000"),
    ("SELECT", "SELECT sr.sensor_id, sr.reading, sc.baseline FROM sensor_data sr JOIN sensor_calibrations sc ON sr.sensor_id = sc.sensor_id WHERE sr.timestamp > NOW() - INTERVAL 10 MINUTE AND ABS(sr.reading - sc.baseline) > sc.threshold"),
    ("SELECT", "SELECT subsystem, COUNT(*) as error_count, AVG(severity_number) as avg_severity FROM log_entries WHERE severity_text IN ('ERROR', 'FATAL') AND timestamp > NOW() - INTERVAL 15 MINUTE GROUP BY subsystem HAVING error_count > 10"),
    ("INSERT", "INSERT INTO telemetry_readings (sensor_id, subsystem, reading, unit, timestamp, mission_phase) VALUES ('{sensor_id}', '{subsystem}', {reading}, '{unit}', NOW(), '{phase}')"),
    ("INSERT", "INSERT INTO sensor_calibrations (sensor_id, baseline, threshold, calibration_epoch, updated_at) VALUES ('{sensor_id}', {baseline}, {threshold}, '{epoch}', NOW())"),
    ("UPDATE", "UPDATE sensor_registry SET last_reading = {reading}, last_seen = NOW(), status = '{status}' WHERE sensor_id = '{sensor_id}'"),
    ("UPDATE", "UPDATE mission_events SET status = 'resolved', resolved_at = NOW(), resolution_notes = '{notes}' WHERE event_id = '{event_id}' AND status = 'active'"),
    ("SELECT", "SELECT me.event_id, me.channel, me.subsystem, COUNT(el.id) as cascade_count FROM mission_events me LEFT JOIN escalation_log el ON me.event_id = el.source_event WHERE me.status = 'active' GROUP BY me.event_id, me.channel, me.subsystem ORDER BY cascade_count DESC"),
    ("DELETE", "DELETE FROM metric_snapshots WHERE timestamp < NOW() - INTERVAL 24 HOUR AND archived = 1"),
    ("SELECT", "SELECT t.trace_id, COUNT(s.span_id) as span_count, MAX(s.duration_ms) as max_duration FROM trace_spans s JOIN (SELECT DISTINCT trace_id FROM trace_spans WHERE duration_ms > 5000 AND timestamp > NOW() - INTERVAL 5 MINUTE) t ON s.trace_id = t.trace_id GROUP BY t.trace_id"),
]

SUBSYSTEMS = ["propulsion", "guidance", "communications", "payload", "relay", "ground", "validation", "safety"]
PHASES = ["PRE-LAUNCH", "COUNTDOWN", "LAUNCH", "ASCENT"]

PROCESSLIST_COMMANDS = ["Query", "Execute", "Prepare", "Fetch"]
PROCESSLIST_STATES = [
    "Sending data", "Writing to net", "Sorting result", "init",
    "waiting for handler commit", "System lock", "Waiting for table metadata lock",
]
WAIT_TYPES = [
    "wait/io/file/sql/binlog",
    "wait/io/socket/sql/client_connection",
    "wait/synch/mutex/innodb/buf_pool_mutex",
    "wait/synch/rwlock/innodb/dict_operation_lock",
    "wait/io/file/innodb/innodb_data_file",
]
# Real mysqlreceiver operation/kind values matching the mysql_otel integration dashboards
BUFFER_POOL_OPERATIONS = ["read_requests", "reads", "write_requests", "writes", "flush_pages", "flush_requests"]
BUFFER_POOL_PAGE_KINDS = ["data", "dirty", "free", "misc"]

ROW_OPERATIONS = ["inserted", "deleted", "read", "updated"]
HANDLER_KINDS = [
    "commit", "delete", "discover", "prepare",
    "read_first", "read_key", "read_last", "read_next", "read_prev", "read_rnd", "read_rnd_next",
    "rollback", "savepoint", "savepoint_rollback", "update", "write",
]
NETWORK_IO_KINDS = ["received", "sent"]
LOCK_KINDS = ["immediate", "waited"]
PAGE_OPERATIONS = ["read", "written", "flushed"]
LOG_OPERATIONS = ["waits", "write_requests", "writes"]
DOUBLE_WRITE_KINDS = ["pages_written", "writes"]
CONNECTION_ERROR_KINDS = [
    "accept", "internal", "max_connections", "peer_address",
    "select", "tcpwrap", "aborted", "aborted_clients", "locked",
]
THREAD_KINDS = ["connected", "running", "cached", "created"]


class MySQLMetricState:
    """Tracks cumulative counter values for a MySQL instance."""

    def __init__(self, rng: random.Random):
        self._rng = rng
        self.query_count = rng.randint(500_000, 2_000_000)
        self.slow_count = rng.randint(10_000, 100_000)
        self.client_count = rng.randint(200_000, 1_000_000)
        self.bp_operations = {op: rng.randint(100_000, 5_000_000) for op in BUFFER_POOL_OPERATIONS}
        self.row_operations = {op: rng.randint(1_000_000, 50_000_000) for op in ROW_OPERATIONS}
        self.handlers = {k: rng.randint(100_000, 10_000_000) for k in HANDLER_KINDS}
        self.network_io = {k: rng.randint(100_000_000, 10_000_000_000) for k in NETWORK_IO_KINDS}
        self.locks = {k: rng.randint(10_000, 1_000_000) for k in LOCK_KINDS}
        self.page_operations = {op: rng.randint(100_000, 5_000_000) for op in PAGE_OPERATIONS}
        self.log_operations = {op: rng.randint(10_000, 500_000) for op in LOG_OPERATIONS}
        self.double_writes = {k: rng.randint(10_000, 500_000) for k in DOUBLE_WRITE_KINDS}
        self.connection_errors = {k: rng.randint(0, 500) for k in CONNECTION_ERROR_KINDS}

    def tick(self, rng: random.Random):
        self.query_count += rng.randint(20, 200)
        self.slow_count += rng.randint(0, 5)
        self.client_count += rng.randint(10, 80)
        for op in BUFFER_POOL_OPERATIONS:
            self.bp_operations[op] += rng.randint(100, 2000)
        for op in ROW_OPERATIONS:
            self.row_operations[op] += rng.randint(100, 5000)
        for k in HANDLER_KINDS:
            self.handlers[k] += rng.randint(10, 1000)
        self.network_io["received"] += rng.randint(10_000, 500_000)
        self.network_io["sent"] += rng.randint(10_000, 200_000)
        for k in LOCK_KINDS:
            self.locks[k] += rng.randint(0, 50)
        for op in PAGE_OPERATIONS:
            self.page_operations[op] += rng.randint(10, 500)
        for op in LOG_OPERATIONS:
            self.log_operations[op] += rng.randint(5, 200)
        for k in DOUBLE_WRITE_KINDS:
            self.double_writes[k] += rng.randint(1, 50)
        self.connection_errors["aborted"] += rng.randint(0, 2)
        self.connection_errors["aborted_clients"] += rng.randint(0, 3)


def _build_log_resource(ns: str) -> dict:
    attrs = {
        "service.name": "mysql-primary",
        "service.namespace": ns,
        "service.version": "8.0.36",
        "service.instance.id": "mysql-primary-001",
        "telemetry.sdk.language": "python",
        "telemetry.sdk.name": "opentelemetry",
        "telemetry.sdk.version": "1.24.0",
        "cloud.provider": "gcp",
        "cloud.platform": "gcp_compute_engine",
        "cloud.region": "us-central1",
        "cloud.availability_zone": "us-central1-b",
        "deployment.environment": f"production-{ns}",
        "host.name": f"{ns}-mysql-host",
        "host.architecture": "amd64",
        "os.type": "linux",
        "data_stream.type": "logs",
        "data_stream.dataset": "mysqlreceiver",
        "data_stream.namespace": "default",
    }
    return {"attributes": _format_attributes(attrs), "schemaUrl": SCHEMA_URL}


def _build_metrics_resource(ns: str) -> dict:
    attrs = {
        "service.name": "mysql-primary",
        "service.namespace": ns,
        "service.version": "8.0.36",
        "service.instance.id": "mysql-primary-001",
        "telemetry.sdk.language": "python",
        "telemetry.sdk.name": "opentelemetry",
        "telemetry.sdk.version": "1.24.0",
        "cloud.provider": "gcp",
        "cloud.platform": "gcp_compute_engine",
        "cloud.region": "us-central1",
        "cloud.availability_zone": "us-central1-b",
        "deployment.environment": f"production-{ns}",
        "host.name": f"{ns}-mysql-host",
        "host.architecture": "amd64",
        "os.type": "linux",
        "mysql.instance.endpoint": f"{ns}-mysql-host:3306",
        "data_stream.type": "metrics",
        "data_stream.dataset": "mysqlreceiver",
        "data_stream.namespace": "default",
    }
    return {"attributes": _format_attributes(attrs), "schemaUrl": SCHEMA_URL}


def _build_trace_resource(ns: str) -> dict:
    attrs = {
        "service.name": "mysql-primary",
        "service.namespace": ns,
        "service.version": "8.0.36",
        "service.instance.id": "mysql-primary-001",
        "telemetry.sdk.language": "python",
        "telemetry.sdk.name": "opentelemetry",
        "telemetry.sdk.version": "1.24.0",
        "cloud.provider": "gcp",
        "cloud.platform": "gcp_compute_engine",
        "cloud.region": "us-central1",
        "cloud.availability_zone": "us-central1-b",
        "deployment.environment": f"production-{ns}",
        "host.name": f"{ns}-mysql-host",
        "host.architecture": "amd64",
        "os.type": "linux",
        "data_stream.type": "traces",
        "data_stream.dataset": "generic",
        "data_stream.namespace": "default",
    }
    return {"attributes": _format_attributes(attrs), "schemaUrl": SCHEMA_URL}


def _render_query(template: str, rng: random.Random, db_prefix: str) -> str:
    return template.format(
        subsystem=rng.choice(SUBSYSTEMS),
        sensor_id=f"SEN-{rng.randint(1000, 9999)}",
        reading=round(rng.uniform(0, 1000), 2),
        unit=rng.choice(["K", "PSI", "kg/s", "dB", "ms", "deg"]),
        phase=rng.choice(PHASES),
        baseline=round(rng.uniform(0, 500), 2),
        threshold=round(rng.uniform(1, 50), 2),
        epoch=f"E{rng.randint(100, 999)}",
        status=rng.choice(["NOMINAL", "WARNING", "CRITICAL"]),
        notes=f"Auto-remediated by agent at T-{rng.randint(1, 600)}",
        event_id=f"EVT-{rng.randint(10000, 99999)}",
    )


def _generate_query_sample_event(
    client: OTLPClient,
    rng: random.Random,
    databases: list,
    tables: dict,
    db_prefix: str,
    ns: str,
) -> tuple[dict, dict]:
    """Generate a db.server.query_sample log event and a correlated DB trace span."""
    operation, template = rng.choice(QUERY_TEMPLATES)
    db = rng.choice(databases)
    table = rng.choice(tables[db])
    query = _render_query(template, rng, db_prefix)

    wait_ns = rng.randint(1_000_000, 50_000_000_000)
    duration_ms = max(1, wait_ns // 1_000_000)

    trace_id = secrets.token_hex(16)
    span_id = secrets.token_hex(8)

    attrs = {
        "db.query.text": query,
        "mysql.threads.thread_id": rng.randint(1, 500),
        "user.name": f"{db_prefix}_app",
        "db.namespace": db,
        "mysql.threads.processlist_command": rng.choice(PROCESSLIST_COMMANDS),
        "mysql.threads.processlist_state": rng.choice(PROCESSLIST_STATES),
        "mysql.wait_type": rng.choice(WAIT_TYPES),
        "mysql.events_waits_current.timer_wait": wait_ns,
    }

    severity = "WARN" if duration_ms > 200 else "INFO"
    log_record = client.build_log_record(
        severity=severity,
        body=query,
        attributes=attrs,
        trace_id=trace_id,
        span_id=span_id,
        event_name="db.server.query_sample",
    )

    span_status = STATUS_ERROR if duration_ms > 500 else STATUS_OK
    span = client.build_span(
        name=f"{operation} {table}",
        trace_id=trace_id,
        span_id=span_id,
        kind=SPAN_KIND_CLIENT,
        duration_ms=duration_ms,
        status_code=span_status,
        attributes={
            "db.system": "mysql",
            "db.name": db,
            "db.statement": query,
            "db.operation": operation,
            "db.sql.table": table,
            "net.peer.name": f"{ns}-mysql-host",
            "net.peer.port": 3306,
            "db.user": f"{db_prefix}_app",
        },
    )

    return log_record, span


def _generate_top_query_event(
    client: OTLPClient,
    rng: random.Random,
    databases: list,
    tables: dict,
    db_prefix: str,
) -> dict:
    """Generate a db.server.top_query log event (statement digest summary)."""
    operation, template = rng.choice(QUERY_TEMPLATES)
    db = rng.choice(databases)
    query = _render_query(template, rng, db_prefix)
    digest = secrets.token_hex(16)

    attrs = {
        "db.query.text": query,
        "mysql.events_statements_summary_by_digest.digest": digest,
        "mysql.events_statements_summary_by_digest.count_star": rng.randint(100, 50_000),
        # float so ESQL CASE(... / ..., 0.0) branch types match (both double)
        "mysql.events_statements_summary_by_digest.sum_timer_wait": float(rng.randint(
            1_000_000_000, 500_000_000_000
        )),
        "db.namespace": db,
        "user.name": f"{db_prefix}_app",
    }

    return client.build_log_record(
        severity="INFO",
        body=query,
        attributes=attrs,
        event_name="db.server.top_query",
    )


def _build_cumulative_sum(name: str, unit: str, value: int, attributes: dict | None = None) -> dict:
    now = _now_ns()
    dp: dict = {
        "startTimeUnixNano": str(int(now) - 60_000_000_000),
        "timeUnixNano": now,
        "asInt": str(int(value)),
    }
    if attributes:
        dp["attributes"] = _format_attributes(attributes)
    return {
        "name": name,
        "unit": unit,
        "sum": {"dataPoints": [dp], "aggregationTemporality": 2, "isMonotonic": True},
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


def _generate_mysql_metrics(
    state: MySQLMetricState, tables: dict, rng: random.Random
) -> list[dict]:
    state.tick(rng)
    metrics: list[dict] = []

    # ── Query counters ────────────────────────────────────────────────
    metrics.append(_build_cumulative_sum("mysql.query.count", "{query}", state.query_count))
    metrics.append(_build_cumulative_sum("mysql.query.slow.count", "{query}", state.slow_count))
    metrics.append(_build_cumulative_sum("mysql.query.client.count", "{query}", state.client_count))

    # ── Row operations (rate panels in Overview + Performance) ────────
    for op in ROW_OPERATIONS:
        metrics.append(
            _build_cumulative_sum("mysql.row_operations", "{row}", state.row_operations[op], {"operation": op})
        )

    # ── Handler statistics (Performance dashboard) ───────────────────
    for k in HANDLER_KINDS:
        metrics.append(
            _build_cumulative_sum("mysql.handlers", "{handler}", state.handlers[k], {"kind": k})
        )

    # ── Network I/O (Performance dashboard) ──────────────────────────
    for k in NETWORK_IO_KINDS:
        metrics.append(
            _build_cumulative_sum("mysql.client.network.io", "By", state.network_io[k], {"kind": k})
        )

    # ── Threads (Overview + Availability dashboards) ──────────────────
    connected = rng.randint(10, 200)
    running = rng.randint(1, min(connected, 50))
    cached = rng.randint(0, 20)
    for k, v in [("connected", connected), ("running", running), ("cached", cached), ("created", connected + rng.randint(0, 50))]:
        metrics.append(_build_gauge("mysql.threads", "{thread}", v, {"kind": k}))
    metrics.append(_build_gauge("mysql.max_used_connections", "{connection}", rng.randint(connected, connected + 50)))

    # ── Connection errors (Overview + Availability dashboards) ────────
    for k in CONNECTION_ERROR_KINDS:
        metrics.append(
            _build_cumulative_sum("mysql.connection.errors", "{error}", state.connection_errors[k], {"error": k})
        )

    # ── Buffer pool pages — attribute is "kind", values: data/dirty/free/misc ──
    total_pages = rng.randint(8000, 32000)
    free_pages = rng.randint(100, total_pages // 4)
    dirty_pages = rng.randint(0, total_pages // 10)
    misc_pages = rng.randint(0, 50)
    data_pages = total_pages - free_pages - dirty_pages - misc_pages
    for kind, count in [("data", data_pages), ("dirty", dirty_pages), ("free", free_pages), ("misc", misc_pages)]:
        metrics.append(_build_gauge("mysql.buffer_pool.pages", "{page}", count, {"kind": kind}))

    # Also emit buffer_pool.data_pages with status="dirty" (Availability dirty-pages panel)
    metrics.append(_build_gauge("mysql.buffer_pool.data_pages", "{page}", dirty_pages, {"status": "dirty"}))

    # ── Buffer pool limit/usage (Overview gauge) ──────────────────────
    bp_size_bytes = total_pages * 16384  # 16KB pages
    bp_used_bytes = data_pages * 16384
    metrics.append(_build_gauge("mysql.buffer_pool.limit", "By", bp_size_bytes))
    metrics.append(_build_gauge("mysql.buffer_pool.usage", "By", bp_used_bytes))

    # ── Buffer pool operations — correct operation names for hit ratio ─
    for op in BUFFER_POOL_OPERATIONS:
        metrics.append(
            _build_cumulative_sum("mysql.buffer_pool.operations", "{operation}", state.bp_operations[op], {"operation": op})
        )

    # ── Lock statistics (Performance dashboard) ──────────────────────
    for k in LOCK_KINDS:
        metrics.append(_build_cumulative_sum("mysql.locks", "{lock}", state.locks[k], {"kind": k}))

    # Row locks (gauge: waits count + accumulated wait time in ns)
    row_lock_waits = rng.randint(0, 100)
    row_lock_time = row_lock_waits * rng.randint(1_000_000, 10_000_000)
    metrics.append(_build_gauge("mysql.row_locks", "{lock}", row_lock_waits, {"kind": "waits"}))
    metrics.append(_build_gauge("mysql.row_locks", "ns", row_lock_time, {"kind": "time"}))

    # ── Page operations (Performance dashboard) ───────────────────────
    for op in PAGE_OPERATIONS:
        metrics.append(
            _build_cumulative_sum("mysql.page_operations", "{page}", state.page_operations[op], {"operation": op})
        )

    # ── Log operations (Performance dashboard) ────────────────────────
    for op in LOG_OPERATIONS:
        metrics.append(
            _build_cumulative_sum("mysql.log_operations", "{operation}", state.log_operations[op], {"operation": op})
        )

    # ── Double writes (Performance dashboard) ─────────────────────────
    for k in DOUBLE_WRITE_KINDS:
        metrics.append(
            _build_cumulative_sum("mysql.double_writes", "{write}", state.double_writes[k], {"kind": k})
        )

    # ── events_statements_summary_by_digest ──────────────────────────
    # sum_timer_wait emitted as double so ESQL CASE(..., 0.0) type-checks correctly
    for _ in range(rng.randint(3, 8)):
        digest = secrets.token_hex(16)
        count_star = rng.randint(100, 50_000)
        sum_wait = float(rng.randint(1_000_000_000, 200_000_000_000))
        attrs = {"digest": digest}
        metrics.append(_build_gauge("mysql.events_statements_summary_by_digest.count_star", "{query}", count_star, attrs))
        metrics.append(_build_gauge("mysql.events_statements_summary_by_digest.sum_timer_wait", "ns", sum_wait, attrs))

    # ── events_waits_current.timer_wait ──────────────────────────────
    metrics.append(
        _build_gauge(
            "mysql.events_waits_current.timer_wait", "ns",
            rng.randint(1_000, 5_000_000_000),
            {"wait_type": rng.choice(WAIT_TYPES)},
        )
    )

    # ── Replication metrics (Availability dashboard) ──────────────────
    # Emit 0 — simulated primary has no replica lag
    metrics.append(_build_gauge("mysql.replica.time_behind_source", "s", 0.0))
    metrics.append(_build_gauge("mysql.replica.sql_delay", "s", 0.0))

    # ── Table metrics: size/rows + I/O waits ──────────────────────────
    for db, db_tables in tables.items():
        for tbl in db_tables[:2]:
            data_size = rng.randint(1_000_000, 500_000_000)
            index_size = rng.randint(100_000, data_size // 2)
            row_count = rng.randint(1000, 10_000_000)
            tbl_attrs_data = {"kind": "data", "schema": db, "table": tbl}
            tbl_attrs_idx = {"kind": "index", "schema": db, "table": tbl}
            metrics.append(_build_gauge("mysql.table.size", "By", data_size, tbl_attrs_data))
            metrics.append(_build_gauge("mysql.table.size", "By", index_size, tbl_attrs_idx))
            metrics.append(_build_gauge("mysql.table.rows", "{row}", row_count, tbl_attrs_data))

            # Table I/O wait metrics (Performance dashboard panel 25)
            for op in ("read", "write", "fetch"):
                io_attrs = {"operation": op, "schema": db, "table": tbl}
                wait_time = float(rng.randint(1_000_000, 500_000_000_000))
                wait_count = rng.randint(100, 500_000)
                metrics.append(_build_gauge("mysql.table.io.wait.time", "ns", wait_time, io_attrs))
                metrics.append(_build_gauge("mysql.table.io.wait.count", "{count}", wait_count, io_attrs))

    return metrics


def run(
    client: OTLPClient,
    stop_event: threading.Event,
    scenario_data: dict | None = None,
) -> None:
    """Run MySQL generator loop until stop_event is set."""
    rng = random.Random()

    if scenario_data:
        ns = scenario_data["namespace"]
        db_prefix = ns.replace("-", "_")
    else:
        ns = NAMESPACE
        db_prefix = _DB_PREFIX

    databases = [
        f"{db_prefix}_telemetry",
        f"{db_prefix}_mission",
        f"{db_prefix}_sensors",
        f"{db_prefix}_audit",
    ]
    tables = {
        f"{db_prefix}_telemetry": ["telemetry_readings", "sensor_data", "metric_snapshots", "log_entries", "trace_spans"],
        f"{db_prefix}_mission": ["mission_events", "countdown_phases", "launch_parameters", "abort_criteria", "hold_records"],
        f"{db_prefix}_sensors": ["sensor_calibrations", "sensor_registry", "calibration_epochs", "sensor_thresholds", "validation_results"],
        f"{db_prefix}_audit": ["remediation_log", "escalation_log", "agent_actions", "operator_decisions", "safety_assessments"],
    }

    log_resource = _build_log_resource(ns)
    metrics_resource = _build_metrics_resource(ns)
    trace_resource = _build_trace_resource(ns)

    _emit_traces = True
    if scenario_data and "services" in scenario_data:
        _emit_traces = "mysql-primary" in scenario_data["services"]

    metric_state = MySQLMetricState(rng)

    total_sent = 0
    total_spans = 0
    scrape_count = 0

    logger.info("MySQL generator started (namespace=%s, db_prefix=%s)", ns, db_prefix)

    while not stop_event.is_set():
        batch_size = rng.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)

        # db.server.query_sample events + correlated trace spans
        sample_records = []
        spans = []
        for _ in range(batch_size):
            log_record, span = _generate_query_sample_event(
                client, rng, databases, tables, db_prefix, ns
            )
            sample_records.append(log_record)
            spans.append(span)

        # Send log events with mysqlreceiver scope
        payload = {
            "resourceLogs": [{
                "resource": log_resource,
                "scopeLogs": [{
                    "scope": {"name": MYSQL_SCOPE, "version": SCOPE_VERSION},
                    "logRecords": sample_records,
                }],
            }]
        }
        client._send(f"{client.endpoint}/v1/logs", payload, "mysql-query-samples")

        if spans and _emit_traces:
            client.send_traces(trace_resource, spans)
            total_spans += len(spans)

        # db.server.top_query events (fewer, represent digest summaries)
        top_count = rng.randint(1, 4)
        top_records = [
            _generate_top_query_event(client, rng, databases, tables, db_prefix)
            for _ in range(top_count)
        ]
        top_payload = {
            "resourceLogs": [{
                "resource": log_resource,
                "scopeLogs": [{
                    "scope": {"name": MYSQL_SCOPE, "version": SCOPE_VERSION},
                    "logRecords": top_records,
                }],
            }]
        }
        client._send(f"{client.endpoint}/v1/logs", top_payload, "mysql-top-queries")

        # MySQL metrics (emit every other cycle to reduce volume)
        scrape_count += 1
        if scrape_count % 2 == 0:
            metrics = _generate_mysql_metrics(metric_state, tables, rng)
            metrics_payload = {
                "resourceMetrics": [{
                    "resource": metrics_resource,
                    "scopeMetrics": [{
                        "scope": {"name": MYSQL_SCOPE, "version": SCOPE_VERSION},
                        "metrics": metrics,
                    }],
                }]
            }
            client._send(f"{client.endpoint}/v1/metrics", metrics_payload, "mysql-metrics")

        total_sent += batch_size + top_count
        logger.info(
            "Sent %d query_sample + %d top_query events, %d spans (total=%d)",
            batch_size, top_count, len(spans), total_sent,
        )

        sleep_time = rng.uniform(BATCH_INTERVAL_MIN, BATCH_INTERVAL_MAX)
        stop_event.wait(sleep_time)

    logger.info("MySQL generator stopped. Total: %d events, %d spans", total_sent, total_spans)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

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

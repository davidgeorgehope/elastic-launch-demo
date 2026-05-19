#!/usr/bin/env python3
"""MySQL Log Generator — sends synthetic MySQL slow query & error logs via OTLP.

Imports and reuses the existing OTLPClient from app.telemetry to send
structured MySQL-style log records directly to the Elastic OTLP endpoint.

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
from app.config import SEVERITY_MAP, NAMESPACE

_DB_PREFIX = NAMESPACE.replace("-", "_")

# Span kind constants
SPAN_KIND_CLIENT = 3
STATUS_OK = 1
STATUS_ERROR = 2

logger = logging.getLogger("mysql-log-generator")

# ── Configuration ─────────────────────────────────────────────────────────────
BATCH_INTERVAL_MIN = 2
BATCH_INTERVAL_MAX = 5
BATCH_SIZE_MIN = 3
BATCH_SIZE_MAX = 12

# ── Realistic MySQL data pools ────────────────────────────────────────────────
DATABASES = [f"{_DB_PREFIX}_telemetry", f"{_DB_PREFIX}_mission", f"{_DB_PREFIX}_sensors", f"{_DB_PREFIX}_audit"]

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

SLOW_QUERIES = [
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

ERROR_MESSAGES = [
    ("ERROR", "Got an error reading communication packets: Connection reset by peer"),
    ("ERROR", f"Aborted connection {{conn_id}} to db: '{{db}}' user: '{_DB_PREFIX}_app' host: '{{host}}' (Got timeout reading communication packets)"),
    ("WARNING", "Slave SQL: Error 'Duplicate entry' on query. Default database: '{db}'. Query: '{query}'"),
    ("ERROR", "Too many connections (max_connections=500, current={current})"),
    ("WARNING", f"Aborted connection {{conn_id}} to db: '{{db}}' user: '{_DB_PREFIX}_reader' (Got an error writing communication packets)"),
    ("ERROR", "Lock wait timeout exceeded; try restarting transaction"),
    ("ERROR", "Deadlock found when trying to get lock; try restarting transaction"),
    ("WARNING", "InnoDB: page_cleaner: 1000ms intended loop took {loop_time}ms. The settings might not be optimal."),
    ("ERROR", "Table '{db}.{table}' doesn't exist"),
    ("WARNING", "Slave I/O: Relay log write failure: could not queue event from master, replication lag {lag_seconds}s"),
    ("ERROR", "Disk full (/var/lib/mysql/#{tmpdir}/#sql_{hash}.MYI); waiting for someone to free some space..."),
    ("WARNING", "Sort aborted: Query execution was interrupted for query: {query}"),
]

CLIENT_HOSTS = [
    f"{NAMESPACE}-app-01.internal:52341",
    f"{NAMESPACE}-app-02.internal:48892",
    f"{NAMESPACE}-worker-01.internal:55123",
    f"{NAMESPACE}-worker-02.internal:49001",
    f"{NAMESPACE}-cron.internal:60012",
    f"{NAMESPACE}-agent.internal:51887",
]

# ── Resource builders ─────────────────────────────────────────────────────────
def _build_slowlog_resource() -> dict:
    return {
        "attributes": _format_attributes({
            "service.name": "mysql-primary",
            "service.namespace": NAMESPACE,
            "service.version": "8.0.36",
            "service.instance.id": "mysql-primary-001",
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.version": "1.24.0",
            "cloud.provider": "gcp",
            "cloud.platform": "gcp_compute_engine",
            "cloud.region": "us-central1",
            "cloud.availability_zone": "us-central1-b",
            "deployment.environment": f"production-{NAMESPACE}",
            "host.name": f"{NAMESPACE}-mysql-host",
            "host.architecture": "amd64",
            "os.type": "linux",
            "data_stream.type": "logs",
            "data_stream.dataset": "mysql.slowlog",
            "data_stream.namespace": "default",
        }),
        "schemaUrl": SCHEMA_URL,
    }


def _build_error_resource() -> dict:
    return {
        "attributes": _format_attributes({
            "service.name": "mysql-primary",
            "service.namespace": NAMESPACE,
            "service.version": "8.0.36",
            "service.instance.id": "mysql-primary-001",
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.version": "1.24.0",
            "cloud.provider": "gcp",
            "cloud.platform": "gcp_compute_engine",
            "cloud.region": "us-central1",
            "cloud.availability_zone": "us-central1-b",
            "deployment.environment": f"production-{NAMESPACE}",
            "host.name": f"{NAMESPACE}-mysql-host",
            "host.architecture": "amd64",
            "os.type": "linux",
            "data_stream.type": "logs",
            "data_stream.dataset": "mysql.error",
            "data_stream.namespace": "default",
        }),
        "schemaUrl": SCHEMA_URL,
    }


def _build_trace_resource() -> dict:
    return {
        "attributes": _format_attributes({
            "service.name": "mysql-primary",
            "service.namespace": NAMESPACE,
            "service.version": "8.0.36",
            "service.instance.id": "mysql-primary-001",
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry",
            "telemetry.sdk.version": "1.24.0",
            "cloud.provider": "gcp",
            "cloud.platform": "gcp_compute_engine",
            "cloud.region": "us-central1",
            "cloud.availability_zone": "us-central1-b",
            "deployment.environment": f"production-{NAMESPACE}",
            "host.name": f"{NAMESPACE}-mysql-host",
            "host.architecture": "amd64",
            "os.type": "linux",
            "data_stream.type": "traces",
            "data_stream.dataset": "generic",
            "data_stream.namespace": "default",
        }),
        "schemaUrl": SCHEMA_URL,
    }


# ── Log record generators ────────────────────────────────────────────────────
def _generate_slow_query_log(client: OTLPClient, rng: random.Random,
                             databases: list | None = None,
                             tables: dict | None = None,
                             client_hosts: list | None = None,
                             db_prefix: str | None = None,
                             namespace: str | None = None) -> tuple[dict, dict]:
    _databases = databases or DATABASES
    _tables = tables or TABLES
    _client_hosts = client_hosts or CLIENT_HOSTS
    _db_prefix = db_prefix or _DB_PREFIX
    _ns = namespace or NAMESPACE

    operation, query_template = rng.choice(SLOW_QUERIES)
    db = rng.choice(_databases)
    table = rng.choice(_tables[db])
    subsystem = rng.choice(SUBSYSTEMS)
    phase = rng.choice(PHASES)

    query = query_template.format(
        subsystem=subsystem,
        sensor_id=f"SEN-{rng.randint(1000, 9999)}",
        reading=round(rng.uniform(0, 1000), 2),
        unit=rng.choice(["K", "PSI", "kg/s", "dB", "ms", "deg"]),
        phase=phase,
        baseline=round(rng.uniform(0, 500), 2),
        threshold=round(rng.uniform(1, 50), 2),
        epoch=f"E{rng.randint(100, 999)}",
        status=rng.choice(["NOMINAL", "WARNING", "CRITICAL"]),
        notes=f"Auto-remediated by agent at T-{rng.randint(1, 600)}",
        event_id=f"EVT-{rng.randint(10000, 99999)}",
    )

    # Query time: normalized to fit within trace_generator envelope
    if rng.random() < 0.10:
        query_time_s = round(rng.uniform(0.3, 0.8), 3)
        severity = "ERROR"
    elif rng.random() < 0.25:
        query_time_s = round(rng.uniform(0.05, 0.3), 3)
        severity = "WARN"
    else:
        query_time_s = round(rng.uniform(0.002, 0.05), 3)
        severity = "WARN"

    lock_time_s = round(rng.uniform(0, query_time_s * 0.3), 3)
    rows_sent = rng.randint(0, 10000)
    rows_examined = rng.randint(rows_sent, rows_sent * 100 + 1)
    duration_ns = int(query_time_s * 1_000_000_000)
    host = rng.choice(_client_hosts)

    body = (
        f"# Time: {time.strftime('%Y-%m-%dT%H:%M:%S.000000Z', time.gmtime())}\n"
        f"# User@Host: {_db_prefix}_app[{_db_prefix}_app] @ {host}\n"
        f"# Query_time: {query_time_s}  Lock_time: {lock_time_s}  "
        f"Rows_sent: {rows_sent}  Rows_examined: {rows_examined}\n"
        f"use {db};\n"
        f"{query};"
    )

    # Generate trace/span IDs for correlation
    trace_id = secrets.token_hex(16)
    span_id = secrets.token_hex(8)

    attrs = {
        "db.system": "mysql",
        "db.statement": query,
        "db.operation": operation,
        "db.name": db,
        "db.sql.table": table,
        "event.duration": duration_ns,
        "mysql.slowlog.query_time": query_time_s,
        "mysql.slowlog.lock_time": lock_time_s,
        "mysql.slowlog.rows_sent": rows_sent,
        "mysql.slowlog.rows_examined": rows_examined,
        "client.address": host.split(":")[0],
        "client.port": int(host.split(":")[1]),
        "db.user": f"{_db_prefix}_app",
    }

    log_record = client.build_log_record(
        severity=severity, body=body, attributes=attrs,
        trace_id=trace_id, span_id=span_id,
    )

    # Build a correlated DB span
    span_status = STATUS_ERROR if query_time_s > 0.3 else STATUS_OK
    span = client.build_span(
        name=f"{operation} {table}",
        trace_id=trace_id,
        span_id=span_id,
        kind=SPAN_KIND_CLIENT,
        duration_ms=max(1, int(query_time_s * 1000)),
        status_code=span_status,
        attributes={
            "db.system": "mysql",
            "db.name": db,
            "db.statement": query,
            "db.operation": operation,
            "db.sql.table": table,
            "net.peer.name": f"{_ns}-mysql-host",
            "net.peer.port": 3306,
            "db.user": f"{_db_prefix}_app",
        },
    )

    return log_record, span


def _generate_error_log(client: OTLPClient, rng: random.Random,
                        databases: list | None = None,
                        tables: dict | None = None,
                        client_hosts: list | None = None) -> dict:
    _databases = databases or DATABASES
    _tables = tables or TABLES
    _client_hosts = client_hosts or CLIENT_HOSTS

    severity_text, msg_template = rng.choice(ERROR_MESSAGES)
    db = rng.choice(_databases)
    table = rng.choice(_tables[db])
    host = rng.choice(_client_hosts)

    msg = msg_template.format(
        conn_id=rng.randint(1000, 99999),
        db=db,
        host=host.split(":")[0],
        table=table,
        query=f"INSERT INTO {table} VALUES (...)",
        current=rng.randint(450, 520),
        loop_time=rng.randint(2000, 15000),
        lag_seconds=round(rng.uniform(5, 120), 1),
        tmpdir="tmp",
        hash=f"{rng.randint(0, 0xFFFFFF):06x}",
    )

    body = f"{time.strftime('%Y-%m-%dT%H:%M:%S.000000Z', time.gmtime())} {severity_text} [{rng.randint(1, 50)}] [Server] {msg}"

    attrs = {
        "db.system": "mysql",
        "db.name": db,
        "error.message": msg,
        "event.category": "database",
        "event.type": "error",
        "event.kind": "event",
        "mysql.error.code": rng.choice([1040, 1205, 1213, 1146, 1062, 2013, 2006]),
        "mysql.thread_id": rng.randint(1, 500),
    }

    return client.build_log_record(severity=severity_text, body=body, attributes=attrs)


# ── Run loop (used by ServiceManager and standalone) ──────────────────────────
def run(client: OTLPClient, stop_event: threading.Event, scenario_data: dict | None = None) -> None:
    """Run MySQL log generator loop until stop_event is set."""
    rng = random.Random()

    # Rebuild namespace-dependent data from scenario_data to avoid import-time freezing
    if scenario_data:
        ns = scenario_data["namespace"]
        db_prefix = ns.replace("-", "_")
    else:
        ns = NAMESPACE
        db_prefix = _DB_PREFIX

    databases = [f"{db_prefix}_telemetry", f"{db_prefix}_mission", f"{db_prefix}_sensors", f"{db_prefix}_audit"]
    tables = {
        f"{db_prefix}_telemetry": [
            "telemetry_readings", "sensor_data", "metric_snapshots",
            "log_entries", "trace_spans",
        ],
        f"{db_prefix}_mission": [
            "mission_events", "countdown_phases", "launch_parameters",
            "abort_criteria", "hold_records",
        ],
        f"{db_prefix}_sensors": [
            "sensor_calibrations", "sensor_registry", "calibration_epochs",
            "sensor_thresholds", "validation_results",
        ],
        f"{db_prefix}_audit": [
            "remediation_log", "escalation_log", "agent_actions",
            "operator_decisions", "safety_assessments",
        ],
    }
    client_hosts = [
        f"{ns}-app-01.internal:52341",
        f"{ns}-app-02.internal:48892",
        f"{ns}-worker-01.internal:55123",
        f"{ns}-worker-02.internal:49001",
        f"{ns}-cron.internal:60012",
        f"{ns}-agent.internal:51887",
    ]

    def _build_resource_dynamic(dataset: str, data_stream_type: str = "logs") -> dict:
        return {
            "attributes": _format_attributes({
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
                "data_stream.type": data_stream_type,
                "data_stream.dataset": dataset,
                "data_stream.namespace": "default",
            }),
            "schemaUrl": SCHEMA_URL,
        }

    slowlog_resource = _build_resource_dynamic("mysql.slowlog")
    error_resource = _build_resource_dynamic("mysql.error")
    trace_resource = _build_resource_dynamic("generic", "traces")

    # Only emit traces if mysql-primary is in the scenario's services (avoids
    # disconnected Service Map nodes when the scenario doesn't include it).
    _emit_traces = True
    if scenario_data and "services" in scenario_data:
        _emit_traces = "mysql-primary" in scenario_data["services"]

    total_sent = 0
    total_spans = 0
    deadlock_storm = False

    logger.info("MySQL log generator started (namespace=%s, db_prefix=%s)", ns, db_prefix)

    while not stop_event.is_set():
        batch_size = rng.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)

        # 8% chance of a deadlock/connection storm
        if rng.random() < 0.08:
            deadlock_storm = True
        elif deadlock_storm and rng.random() < 0.5:
            deadlock_storm = False

        # Generate slow query logs + correlated DB trace spans
        slow_records = []
        spans = []
        for _ in range(batch_size):
            log_record, span = _generate_slow_query_log(client, rng, databases, tables, client_hosts, db_prefix, ns)
            slow_records.append(log_record)
            spans.append(span)
        client.send_logs(slowlog_resource, slow_records)

        # Send correlated trace spans (only if mysql-primary is in scenario topology)
        if spans and _emit_traces:
            client.send_traces(trace_resource, spans)
            total_spans += len(spans)

        # Generate error logs (more during storms)
        error_count = rng.randint(3, 8) if deadlock_storm else rng.randint(0, 2)
        if error_count > 0:
            error_records = []
            for _ in range(error_count):
                error_records.append(_generate_error_log(client, rng, databases, tables, client_hosts))
            client.send_logs(error_resource, error_records)

        total_sent += batch_size + error_count
        logger.info(
            "Sent %d slowlog + %d error logs, %d spans (total=%d logs, %d spans)",
            batch_size, error_count, len(spans), total_sent, total_spans,
        )

        sleep_time = rng.uniform(BATCH_INTERVAL_MIN, BATCH_INTERVAL_MAX)
        stop_event.wait(sleep_time)

    logger.info("MySQL log generator stopped. Total: %d logs, %d spans", total_sent, total_spans)


# ── Standalone entry point ────────────────────────────────────────────────────
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

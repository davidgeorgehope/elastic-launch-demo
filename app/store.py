"""DeploymentStore — SQLite persistence for active deployments.

Survives app restarts so active deployments can be restored from the DB
rather than being lost when the process recycles.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
import time
from typing import Any

logger = logging.getLogger("nova7.store")

_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
_DB_PATH = os.path.join(_DB_DIR, "deployments.db")

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS deployments (
    deployment_id   TEXT PRIMARY KEY,
    scenario_id     TEXT NOT NULL,
    otlp_endpoint   TEXT NOT NULL DEFAULT '',
    otlp_api_key    TEXT NOT NULL DEFAULT '',
    elastic_url     TEXT NOT NULL DEFAULT '',
    elastic_api_key TEXT NOT NULL DEFAULT '',
    kibana_url      TEXT NOT NULL DEFAULT '',
    status          TEXT NOT NULL DEFAULT 'active',
    created_at      REAL NOT NULL,
    updated_at      REAL NOT NULL
);
"""


class DeploymentStore:
    """Thread-safe SQLite store for deployment records."""

    def __init__(self, db_path: str | None = None):
        self._db_path = db_path or _DB_PATH
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(_CREATE_TABLE)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def upsert(
        self,
        deployment_id: str,
        scenario_id: str,
        *,
        otlp_endpoint: str = "",
        otlp_api_key: str = "",
        elastic_url: str = "",
        elastic_api_key: str = "",
        kibana_url: str = "",
        status: str = "active",
    ) -> None:
        """Insert or replace a deployment record."""
        now = time.time()
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO deployments
                       (deployment_id, scenario_id, otlp_endpoint, otlp_api_key,
                        elastic_url, elastic_api_key, kibana_url, status,
                        created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        deployment_id,
                        scenario_id,
                        otlp_endpoint,
                        otlp_api_key,
                        elastic_url,
                        elastic_api_key,
                        kibana_url,
                        status,
                        now,
                        now,
                    ),
                )

    def get(self, deployment_id: str) -> dict[str, Any] | None:
        """Return a single deployment record or None."""
        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM deployments WHERE deployment_id = ?",
                    (deployment_id,),
                ).fetchone()
                return dict(row) if row else None

    def get_all_active(self) -> list[dict[str, Any]]:
        """Return all deployments with status='active'."""
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM deployments WHERE status = 'active' ORDER BY created_at",
                ).fetchall()
                return [dict(r) for r in rows]

    def set_status(self, deployment_id: str, status: str) -> None:
        """Update status of a deployment."""
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE deployments SET status = ?, updated_at = ? WHERE deployment_id = ?",
                    (status, time.time(), deployment_id),
                )

    def delete(self, deployment_id: str) -> None:
        """Remove a deployment record entirely."""
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "DELETE FROM deployments WHERE deployment_id = ?",
                    (deployment_id,),
                )


# ── Chaos channel persistence ─────────────────────────────────────────────────

_CREATE_CHAOS_TABLE = """
CREATE TABLE IF NOT EXISTS chaos_channels (
    deployment_id   TEXT NOT NULL,
    channel         INTEGER NOT NULL,
    state           TEXT NOT NULL DEFAULT 'STANDBY',
    mode            TEXT,
    se_name         TEXT,
    session_id      TEXT,
    triggered_at    REAL,
    resolved_at     REAL,
    callback_url    TEXT NOT NULL DEFAULT '',
    user_email      TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (deployment_id, channel)
);
"""

_CREATE_SPIKES_TABLE = """
CREATE TABLE IF NOT EXISTS chaos_spikes (
    deployment_id       TEXT PRIMARY KEY,
    cpu_pct             REAL NOT NULL DEFAULT 0,
    memory_pct          REAL NOT NULL DEFAULT 0,
    k8s_oom_intensity   REAL NOT NULL DEFAULT 0,
    latency_multiplier  REAL NOT NULL DEFAULT 1.0
);
"""


class ChaosStore:
    """Thread-safe SQLite store for chaos channel state (session ownership)."""

    def __init__(self, db_path: str | None = None):
        self._db_path = db_path or _DB_PATH
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(_CREATE_CHAOS_TABLE)
            conn.execute(_CREATE_SPIKES_TABLE)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def upsert_channel(
        self,
        deployment_id: str,
        channel: int,
        *,
        state: str = "ACTIVE",
        mode: str | None = None,
        se_name: str = "",
        session_id: str = "",
        triggered_at: float | None = None,
        resolved_at: float | None = None,
        callback_url: str = "",
        user_email: str = "",
    ) -> None:
        """Insert or replace a chaos channel record."""
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO chaos_channels
                       (deployment_id, channel, state, mode, se_name, session_id,
                        triggered_at, resolved_at, callback_url, user_email)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        deployment_id,
                        channel,
                        state,
                        mode,
                        se_name,
                        session_id,
                        triggered_at,
                        resolved_at,
                        callback_url,
                        user_email,
                    ),
                )

    def resolve_channel(
        self, deployment_id: str, channel: int, resolved_at: float
    ) -> None:
        """Mark a channel as STANDBY."""
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """UPDATE chaos_channels
                       SET state = 'STANDBY', mode = NULL, session_id = NULL,
                           resolved_at = ?, callback_url = '', user_email = ''
                       WHERE deployment_id = ? AND channel = ?""",
                    (resolved_at, deployment_id, channel),
                )

    def get_all_channels(self, deployment_id: str) -> list[dict[str, Any]]:
        """Return all channel records for a deployment."""
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM chaos_channels WHERE deployment_id = ?",
                    (deployment_id,),
                ).fetchall()
                return [dict(r) for r in rows]

    def upsert_spikes(self, deployment_id: str, spikes: dict) -> None:
        """Persist infra spike values for a deployment."""
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO chaos_spikes
                       (deployment_id, cpu_pct, memory_pct, k8s_oom_intensity, latency_multiplier)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        deployment_id,
                        spikes.get("cpu_pct", 0),
                        spikes.get("memory_pct", 0),
                        spikes.get("k8s_oom_intensity", 0),
                        spikes.get("latency_multiplier", 1.0),
                    ),
                )

    def get_spikes(self, deployment_id: str) -> dict | None:
        """Return persisted spike values for a deployment, or None."""
        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM chaos_spikes WHERE deployment_id = ?",
                    (deployment_id,),
                ).fetchone()
                return dict(row) if row else None

    def delete_spikes_for_deployment(self, deployment_id: str) -> None:
        """Remove persisted spike values for a deployment (e.g. on teardown)."""
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "DELETE FROM chaos_spikes WHERE deployment_id = ?",
                    (deployment_id,),
                )

    def delete_channels_for_deployment(self, deployment_id: str) -> None:
        """Remove all persisted chaos rows for a deployment (e.g. on teardown)."""
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "DELETE FROM chaos_channels WHERE deployment_id = ?",
                    (deployment_id,),
                )

    def validate_session(self, deployment_id: str, session_id: str) -> list[int]:
        """Return list of channel IDs owned by this session_id."""
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """SELECT channel FROM chaos_channels
                       WHERE deployment_id = ? AND session_id = ? AND state = 'ACTIVE'""",
                    (deployment_id, session_id),
                ).fetchall()
                return [r["channel"] for r in rows]

    def expire_channels(self, deployment_id: str, max_age: float) -> list[int]:
        """Expire channels older than max_age seconds. Returns expired channel IDs."""
        now = time.time()
        cutoff = now - max_age
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    """SELECT channel FROM chaos_channels
                       WHERE deployment_id = ? AND state = 'ACTIVE'
                         AND triggered_at IS NOT NULL AND triggered_at < ?""",
                    (deployment_id, cutoff),
                ).fetchall()
                expired = [r["channel"] for r in rows]
                if expired:
                    conn.execute(
                        """UPDATE chaos_channels
                            SET state = 'STANDBY', mode = NULL, session_id = NULL,
                                resolved_at = ?, callback_url = '', user_email = ''
                            WHERE deployment_id = ? AND state = 'ACTIVE'
                              AND triggered_at IS NOT NULL AND triggered_at < ?""",
                        (now, deployment_id, cutoff),
                    )
                return expired

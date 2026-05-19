"""Chaos Controller — manages state for 20 independent fault channels."""

from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING, Any

from app.config import CHANNEL_REGISTRY, CHANNEL_TIMEOUT

if TYPE_CHECKING:
    from app.store import ChaosStore

logger = logging.getLogger("nova7.chaos")

# Channel states
STANDBY = "STANDBY"
ACTIVE = "ACTIVE"
RESOLVING = "RESOLVING"

# Maximum fault duration (seconds) — override via CHANNEL_TIMEOUT in .env
MAX_FAULT_DURATION = CHANNEL_TIMEOUT


class ChaosController:
    """Thread-safe chaos channel state management."""

    def __init__(
        self,
        channel_registry: dict[int, dict[str, Any]] | None = None,
        chaos_store: ChaosStore | None = None,
        deployment_id: str = "",
    ):
        self._lock = threading.RLock()
        self._channel_registry = channel_registry or CHANNEL_REGISTRY
        self._store = chaos_store
        self._deployment_id = deployment_id
        self._channels: dict[int, dict[str, Any]] = {}
        for ch_id in self._channel_registry:
            self._channels[ch_id] = {
                "state": STANDBY,
                "mode": None,
                "se_name": None,
                "session_id": None,
                "triggered_at": None,
                "resolved_at": None,
                "callback_url": "",
                "user_email": "",
            }
        self._infra_spikes: dict[str, float] = {
            "cpu_pct": 0,
            "memory_pct": 0,
            "k8s_oom_intensity": 0,
            "latency_multiplier": 1.0,
        }
        # Restore persisted state from SQLite
        self._restore_from_store()

    def _restore_from_store(self) -> None:
        """Hydrate in-memory channel state from SQLite on startup."""
        if not self._store or not self._deployment_id:
            return
        try:
            rows = self._store.get_all_channels(self._deployment_id)
            for row in rows:
                ch_id = row["channel"]
                if ch_id not in self._channels:
                    continue
                self._channels[ch_id]["state"] = row["state"]
                self._channels[ch_id]["mode"] = row["mode"]
                self._channels[ch_id]["se_name"] = row["se_name"]
                self._channels[ch_id]["session_id"] = row["session_id"]
                self._channels[ch_id]["triggered_at"] = row["triggered_at"]
                self._channels[ch_id]["resolved_at"] = row["resolved_at"]
                self._channels[ch_id]["callback_url"] = row["callback_url"] or ""
                self._channels[ch_id]["user_email"] = row["user_email"] or ""
            restored = sum(1 for r in rows if r["state"] == ACTIVE)
            if restored:
                logger.info("Restored %d active chaos channels from SQLite", restored)
                # Recalculate infra spikes from restored ACTIVE channels so that
                # CPU/memory/latency effects survive an app crash and restart.
                self._infra_spikes = {
                    k: (1.0 if k == "latency_multiplier" else 0.0)
                    for k in self._infra_spikes
                }
                for ch_id, ch in self._channels.items():
                    if ch["state"] == ACTIVE:
                        impact = self._channel_registry.get(ch_id, {}).get("infra_impact", {})
                        for key, val in impact.items():
                            if key in self._infra_spikes:
                                self._infra_spikes[key] = max(self._infra_spikes[key], float(val))
            # Overlay any manually-set spike values persisted via the sliders
            persisted_spikes = self._store.get_spikes(self._deployment_id)
            if persisted_spikes:
                for key in self._infra_spikes:
                    if key in persisted_spikes and persisted_spikes[key] is not None:
                        self._infra_spikes[key] = max(
                            self._infra_spikes[key], float(persisted_spikes[key])
                        )
        except Exception:
            logger.exception("Failed to restore chaos channels from SQLite")

    def trigger(
        self,
        channel: int,
        mode: str = "calibration",
        se_name: str = "",
        callback_url: str = "",
        user_email: str = "",
        session_id: str = "",
    ) -> dict[str, Any]:
        if channel not in self._channel_registry:
            return {"error": f"Unknown channel {channel}"}

        with self._lock:
            ch = self._channels[channel]
            if ch["state"] == ACTIVE:
                return {"status": "already_active", "channel": channel}

            ch["state"] = ACTIVE
            ch["mode"] = mode
            ch["se_name"] = se_name
            ch["session_id"] = session_id
            ch["triggered_at"] = time.time()
            ch["resolved_at"] = None
            ch["callback_url"] = callback_url
            ch["user_email"] = user_email

        # Write-through to SQLite
        if self._store and self._deployment_id:
            self._store.upsert_channel(
                self._deployment_id,
                channel,
                state=ACTIVE,
                mode=mode,
                se_name=se_name,
                session_id=session_id,
                triggered_at=ch["triggered_at"],
                callback_url=callback_url,
                user_email=user_email,
            )

        ch_def = self._channel_registry[channel]

        # Auto-apply infrastructure spikes from channel definition
        infra_impact = ch_def.get("infra_impact")
        if infra_impact:
            with self._lock:
                for key, val in infra_impact.items():
                    if key in self._infra_spikes:
                        self._infra_spikes[key] = max(self._infra_spikes[key], float(val))

        logger.info(
            "CHAOS: Channel %d [%s] ACTIVATED (mode=%s, session=%s)",
            channel,
            ch_def["name"],
            mode,
            session_id[:8] if session_id else "none",
        )
        return {
            "status": "triggered",
            "channel": channel,
            "name": ch_def["name"],
            "mode": mode,
        }

    def resolve(
        self,
        channel: int,
        session_id: str = "",
        force: bool = False,
        user_email: str = "",
    ) -> dict[str, Any]:
        if channel not in self._channel_registry:
            return {"error": f"Unknown channel {channel}"}

        with self._lock:
            ch = self._channels[channel]
            if ch["state"] == STANDBY:
                return {"status": "already_standby", "channel": channel}

            # Session ownership check (skip if force=True or channel has no owner)
            if not force and ch["session_id"]:
                session_matches = session_id and ch["session_id"] == session_id
                email_matches = user_email and ch.get("user_email") and ch["user_email"] == user_email
                if not session_matches and not email_matches:
                    return {"error": "session_mismatch", "channel": channel}

            ch["state"] = STANDBY
            ch["mode"] = None
            ch["session_id"] = None
            ch["resolved_at"] = time.time()
            ch["callback_url"] = ""
            ch["user_email"] = ""

            # Recalculate infra spikes from remaining active channels
            self._infra_spikes = {k: (1.0 if k == "latency_multiplier" else 0) for k in self._infra_spikes}
            for ch_id, c in self._channels.items():
                if c["state"] == ACTIVE:
                    impact = self._channel_registry.get(ch_id, {}).get("infra_impact", {})
                    for key, val in impact.items():
                        if key in self._infra_spikes:
                            self._infra_spikes[key] = max(self._infra_spikes[key], float(val))

        # Write-through to SQLite
        if self._store and self._deployment_id:
            self._store.resolve_channel(self._deployment_id, channel, ch["resolved_at"])

        ch_def = self._channel_registry[channel]
        logger.info("CHAOS: Channel %d [%s] RESOLVED", channel, ch_def["name"])
        return {
            "status": "resolved",
            "channel": channel,
            "name": ch_def["name"],
        }

    def _expire_stale(self) -> None:
        """Auto-resolve channels that have been active longer than MAX_FAULT_DURATION.

        Must be called while holding self._lock.
        """
        now = time.time()
        expired_ids: list[int] = []
        for ch_id, ch in self._channels.items():
            if ch["state"] != ACTIVE:
                continue
            if ch["triggered_at"] and (now - ch["triggered_at"]) >= MAX_FAULT_DURATION:
                ch["state"] = STANDBY
                ch["mode"] = None
                ch["session_id"] = None
                ch["resolved_at"] = now
                ch["callback_url"] = ""
                ch["user_email"] = ""
                expired_ids.append(ch_id)
                ch_def = self._channel_registry[ch_id]
                logger.info(
                    "CHAOS: Channel %d [%s] AUTO-EXPIRED after %ds",
                    ch_id,
                    ch_def["name"],
                    MAX_FAULT_DURATION,
                )
        # Persist expiry to SQLite
        if expired_ids and self._store and self._deployment_id:
            self._store.expire_channels(self._deployment_id, MAX_FAULT_DURATION)

    def is_active(self, channel: int) -> bool:
        with self._lock:
            self._expire_stale()
            ch = self._channels.get(channel)
            return ch is not None and ch["state"] == ACTIVE

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            self._expire_stale()
            result = {}
            for ch_id, ch_state in self._channels.items():
                ch_def = self._channel_registry[ch_id]
                result[ch_id] = {
                    "name": ch_def["name"],
                    "subsystem": ch_def["subsystem"],
                    "state": ch_state["state"],
                    "mode": ch_state["mode"],
                    "triggered_at": ch_state["triggered_at"],
                    "session_id": ch_state["session_id"],
                    "user_email": ch_state.get("user_email", ""),
                    "affected_services": ch_def["affected_services"],
                    "description": ch_def["description"],
                }
            return result

    def get_channel_status(self, channel: int) -> dict[str, Any]:
        if channel not in self._channel_registry:
            return {"error": f"Unknown channel {channel}"}
        with self._lock:
            ch_state = self._channels[channel]
            ch_def = self._channel_registry[channel]
            return {
                "channel": channel,
                "name": ch_def["name"],
                "subsystem": ch_def["subsystem"],
                "state": ch_state["state"],
                "mode": ch_state["mode"],
                "se_name": ch_state["se_name"],
                "triggered_at": ch_state["triggered_at"],
                "resolved_at": ch_state["resolved_at"],
                "callback_url": ch_state.get("callback_url", ""),
                "user_email": ch_state.get("user_email", ""),
                "affected_services": ch_def["affected_services"],
                "cascade_services": ch_def["cascade_services"],
                "error_type": ch_def["error_type"],
                "sensor_type": ch_def["sensor_type"],
                "vehicle_section": ch_def["vehicle_section"],
                "description": ch_def["description"],
            }

    def get_channel_metadata(self, channel: int) -> dict[str, str]:
        """Return callback_url and user_email for a channel."""
        with self._lock:
            ch = self._channels.get(channel)
            if ch is None:
                return {"callback_url": "", "user_email": ""}
            return {
                "callback_url": ch.get("callback_url", ""),
                "user_email": ch.get("user_email", ""),
            }

    def validate_session(self, session_id: str, user_email: str = "") -> list[int]:
        """Return list of channel IDs owned by this session_id or user_email."""
        with self._lock:
            self._expire_stale()
            return [
                ch_id
                for ch_id, ch in self._channels.items()
                if ch["state"] == ACTIVE and (
                    ch["session_id"] == session_id
                    or (user_email and ch.get("user_email") and ch["user_email"] == user_email)
                )
            ]

    def get_active_channels(self) -> list[int]:
        with self._lock:
            return [
                ch_id for ch_id, ch in self._channels.items() if ch["state"] == ACTIVE
            ]

    def set_infra_spikes(self, spikes: dict[str, float]) -> None:
        with self._lock:
            for key in self._infra_spikes:
                if key in spikes:
                    self._infra_spikes[key] = float(spikes[key])
        if self._store and self._deployment_id:
            self._store.upsert_spikes(self._deployment_id, self._infra_spikes)

    def get_infra_spikes(self) -> dict[str, float]:
        with self._lock:
            return dict(self._infra_spikes)

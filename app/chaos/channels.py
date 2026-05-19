"""Channel fault logic — maps channels to service effects and cascading behavior.

Uses CHANNEL_REGISTRY from config.py. Services check channel state each telemetry
cycle via base_service.is_channel_active() and emit_fault_logs()/emit_cascade_logs().
"""

from __future__ import annotations

from app.config import CHANNEL_REGISTRY


def get_affected_services(channel: int, registry: dict | None = None) -> list[str]:
    """Return the list of directly affected services for a channel."""
    reg = registry or CHANNEL_REGISTRY
    ch = reg.get(channel)
    return ch["affected_services"] if ch else []


def get_cascade_services(channel: int, registry: dict | None = None) -> list[str]:
    """Return the list of cascade (secondary) services for a channel."""
    reg = registry or CHANNEL_REGISTRY
    ch = reg.get(channel)
    return ch.get("cascade_services", []) if ch else []


def get_channel_by_subsystem(subsystem: str, registry: dict | None = None) -> list[int]:
    """Return all channel IDs that target a given subsystem."""
    reg = registry or CHANNEL_REGISTRY
    return [ch_id for ch_id, ch in reg.items() if ch["subsystem"] == subsystem]


def get_channel_by_error_type(
    error_type: str, registry: dict | None = None
) -> int | None:
    """Find channel ID by its error_type string."""
    reg = registry or CHANNEL_REGISTRY
    for ch_id, ch in reg.items():
        if ch["error_type"] == error_type:
            return ch_id
    return None


def get_channel_summary(channel: int, registry: dict | None = None) -> dict | None:
    """Get a display-friendly summary of a channel."""
    reg = registry or CHANNEL_REGISTRY
    ch = reg.get(channel)
    if not ch:
        return None
    return {
        "channel": channel,
        "name": ch["name"],
        "subsystem": ch["subsystem"],
        "vehicle_section": ch["vehicle_section"],
        "error_type": ch["error_type"],
        "sensor_type": ch["sensor_type"],
        "affected_services": ch["affected_services"],
        "cascade_services": ch.get("cascade_services", []),
        "description": ch["description"],
    }


def get_all_channel_summaries(registry: dict | None = None) -> list[dict]:
    """Get summaries for all 20 channels."""
    reg = registry or CHANNEL_REGISTRY
    return [s for ch_id in sorted(reg.keys()) if (s := get_channel_summary(ch_id, registry=reg)) is not None]

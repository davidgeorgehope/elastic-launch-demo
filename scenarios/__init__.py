"""Scenario registry — discovers and serves scenario implementations."""

from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scenarios.base import BaseScenario

logger = logging.getLogger("scenarios")

# Registry: scenario_id -> BaseScenario instance
_registry: dict[str, BaseScenario] = {}
_loaded = False


def _discover() -> None:
    """Auto-discover all scenario modules under scenarios/*/scenario.py."""
    global _loaded
    if _loaded:
        return

    # Known scenario modules — add new scenarios here
    _scenario_modules = [
        "scenarios.space.scenario",
        "scenarios.fanatics.scenario",
        "scenarios.financial.scenario",
        "scenarios.healthcare.scenario",
        "scenarios.gaming.scenario",
        "scenarios.banking.scenario",
        "scenarios.gcp.scenario",
        "scenarios.claro.scenario",
    ]

    for mod_path in _scenario_modules:
        try:
            mod = importlib.import_module(mod_path)
            scenario = mod.scenario  # Each module exposes a `scenario` instance
            _registry[scenario.scenario_id] = scenario
            logger.debug("Registered scenario: %s", scenario.scenario_id)
        except (ImportError, AttributeError) as e:
            logger.debug("Scenario %s not available: %s", mod_path, e)

    _loaded = True


def get_scenario(scenario_id: str) -> BaseScenario:
    """Get a scenario by ID. Raises KeyError if not found."""
    _discover()
    if scenario_id not in _registry:
        available = ", ".join(_registry.keys()) or "(none)"
        raise KeyError(
            f"Unknown scenario '{scenario_id}'. Available: {available}"
        )
    return _registry[scenario_id]


def list_scenarios() -> list[dict[str, str]]:
    """Return list of available scenarios with metadata for the selector UI."""
    _discover()
    return [
        {
            "id": s.scenario_id,
            "name": s.scenario_name,
            "description": s.scenario_description,
            "namespace": s.namespace,
        }
        for s in _registry.values()
    ]

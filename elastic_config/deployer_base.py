"""Shared types and HTTP helper functions for the scenario deployer."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

import httpx

logger = logging.getLogger("deployer")


# ── Progress reporting ──────────────────────────────────────────────────────

@dataclass
class DeployStep:
    name: str
    status: str = "pending"      # pending | running | ok | failed | skipped
    detail: str = ""
    items_total: int = 0
    items_done: int = 0


@dataclass
class DeployProgress:
    steps: list[DeployStep] = field(default_factory=list)
    finished: bool = False
    error: str = ""
    otlp_endpoint: str = ""

    def to_dict(self) -> dict:
        return {
            "finished": self.finished,
            "error": self.error,
            "otlp_endpoint": self.otlp_endpoint,
            "steps": [
                {
                    "name": s.name,
                    "status": s.status,
                    "detail": s.detail,
                    "items_total": s.items_total,
                    "items_done": s.items_done,
                }
                for s in self.steps
            ],
        }


ProgressCallback = Callable[[DeployProgress], None]


# ── HTTP helpers ────────────────────────────────────────────────────────────

def _kibana_headers(api_key: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "kbn-xsrf": "true",
        "x-elastic-internal-origin": "kibana",
        "Authorization": f"ApiKey {api_key}",
    }


def _es_headers(api_key: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"ApiKey {api_key}",
    }


# ── Retry helper ────────────────────────────────────────────────────────────

# HTTP statuses that warrant a retry: lock contention (409), rate limit (429),
# and 5xx server errors.
_TRANSIENT_STATUSES = {409, 429, 500, 502, 503, 504}


def _retry_http(
    call: Callable[[], httpx.Response],
    *,
    attempts: int = 4,
    base_delay: float = 0.75,
    label: str = "",
) -> Optional[httpx.Response]:
    """Run an HTTP call with exponential-backoff retries on transient failures.

    Retries on httpx timeouts/network errors and on transient HTTP status codes
    (409 conflict from concurrent shared-resource mutation, 429, 5xx).

    Returns the final httpx.Response (which may still be an error status if all
    retries were exhausted), or None if every attempt raised an exception.
    """
    last_resp: Optional[httpx.Response] = None
    for attempt in range(attempts):
        try:
            resp = call()
            if resp.status_code not in _TRANSIENT_STATUSES:
                return resp
            last_resp = resp
            logger.warning(
                "%s returned HTTP %s (attempt %d/%d)",
                label or "request", resp.status_code, attempt + 1, attempts,
            )
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.warning(
                "%s raised %s (attempt %d/%d)",
                label or "request", exc.__class__.__name__, attempt + 1, attempts,
            )
        if attempt < attempts - 1:
            time.sleep(base_delay * (2 ** attempt))
    return last_resp

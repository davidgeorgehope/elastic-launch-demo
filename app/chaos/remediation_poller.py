"""Remediation Poller — polls ES index for remediation commands queued by workflows.

The remediation_action workflow writes to {namespace}-remediation-queue instead of
making an HTTP callback (which fails when the app is behind a firewall). This poller
picks up pending docs, resolves the corresponding fault channel, and marks them processed.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from app.chaos.controller import ChaosController

logger = logging.getLogger("nova7.remediation_poller")

POLL_ACTIVE = 15  # seconds between polls when faults are active
POLL_IDLE = 30  # seconds between polls when no faults
CLEANUP_AGE = 3600  # delete processed docs older than 1 hour


class RemediationPoller:
    """Background thread that polls an ES index for remediation commands."""

    def __init__(
        self,
        *,
        elastic_url: str,
        elastic_api_key: str,
        namespace: str,
        chaos_controller: ChaosController,
        stop_event: threading.Event,
    ):
        self._elastic_url = elastic_url.rstrip("/")
        self._api_key = elastic_api_key
        self._namespace = namespace
        self._chaos = chaos_controller
        self._stop = stop_event
        self._index = f"{namespace}-remediation-queue"
        self._thread: threading.Thread | None = None

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"ApiKey {self._api_key}",
            "Content-Type": "application/json",
        }

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._run, name="remediation-poller", daemon=True
        )
        self._thread.start()
        logger.info("Remediation poller started (index=%s)", self._index)

    def _run(self) -> None:
        """Main poll loop."""
        # Flush any stale pending docs left over from previous runs so they
        # don't immediately resolve newly-injected faults.
        self._flush_stale_pending()

        while not self._stop.is_set():
            active = self._chaos.get_active_channels()
            if active:
                try:
                    self._poll_pending()
                except Exception:
                    logger.exception("Error polling remediation queue")
                self._cleanup_processed()
                interval = POLL_ACTIVE
            else:
                interval = POLL_IDLE

            # Sleep in small increments so we respond to stop_event quickly
            deadline = time.monotonic() + interval
            while time.monotonic() < deadline and not self._stop.is_set():
                time.sleep(1)

        logger.info("Remediation poller stopped")

    def _flush_stale_pending(self) -> None:
        """Mark all existing pending docs as stale on startup.

        Prevents leftover docs from previous app runs from instantly
        resolving newly-injected faults.
        """
        query = {
            "query": {"term": {"status": "pending"}},
            "script": {
                "source": "ctx._source.status = 'stale'; ctx._source.processed_at = System.currentTimeMillis()",
            },
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(
                    f"{self._elastic_url}/{self._index}/_update_by_query",
                    headers=self._headers,
                    json=query,
                )
                if resp.status_code == 404:
                    return
                if resp.status_code < 300:
                    updated = resp.json().get("updated", 0)
                    if updated:
                        logger.info(
                            "Flushed %d stale pending remediation docs on startup",
                            updated,
                        )
        except Exception:
            logger.debug("Failed to flush stale pending docs", exc_info=True)

    def _poll_pending(self) -> None:
        """Search for pending remediation docs and process them."""
        query = {
            "query": {"term": {"status": "pending"}},
            "size": 50,
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                f"{self._elastic_url}/{self._index}/_search",
                headers=self._headers,
                json=query,
            )
            if resp.status_code == 404:
                return  # index doesn't exist yet
            resp.raise_for_status()

            hits = resp.json().get("hits", {}).get("hits", [])
            resolved_channels: set[int] = set()
            for hit in hits:
                self._process_hit(client, hit, resolved_channels)

    def _process_hit(
        self,
        client: httpx.Client,
        hit: dict[str, Any],
        resolved_channels: set[int],
    ) -> None:
        """Resolve a fault channel and mark the doc as processed."""
        doc_id = hit["_id"]
        src = hit.get("_source", {})
        channel_raw = src.get("channel")

        try:
            channel = int(channel_raw)
        except (TypeError, ValueError):
            logger.warning(
                "Invalid channel value in remediation doc %s: %r", doc_id, channel_raw
            )
            self._mark_processed(client, doc_id, error="invalid channel")
            return

        dry_run = src.get("dry_run", True)
        if isinstance(dry_run, str):
            dry_run = dry_run.lower() not in ("false", "0", "no")

        if dry_run:
            logger.info(
                "Remediation doc %s is dry_run — marking processed without resolving",
                doc_id,
            )
            self._mark_processed(client, doc_id, dry_run=True)
            return

        # Skip if channel is not currently active (stale doc) or already
        # resolved in this poll cycle (duplicate from multiple alert firings)
        if not self._chaos.is_active(channel):
            logger.info(
                "Remediation doc %s targets channel %d which is not active — marking stale",
                doc_id,
                channel,
            )
            self._mark_processed(client, doc_id, error="channel not active")
            return

        if channel in resolved_channels:
            logger.info(
                "Remediation doc %s is duplicate for channel %d — already resolved this cycle",
                doc_id,
                channel,
            )
            self._mark_processed(client, doc_id, error="duplicate")
            return

        result = self._chaos.resolve(channel, force=True)
        status = result.get("status", "unknown")
        resolved_channels.add(channel)
        logger.info(
            "Remediation poller resolved channel %d: %s (doc=%s)",
            channel,
            status,
            doc_id,
        )

        self._mark_processed(client, doc_id)

    def _mark_processed(
        self,
        client: httpx.Client,
        doc_id: str,
        *,
        error: str = "",
        dry_run: bool = False,
    ) -> None:
        """Update doc status to 'processed'."""
        update_body: dict[str, Any] = {
            "status": "processed",
            "processed_at": int(time.time() * 1000),
        }
        if error:
            update_body["error"] = error
        if dry_run:
            update_body["dry_run_skipped"] = True

        try:
            client.post(
                f"{self._elastic_url}/{self._index}/_update/{doc_id}",
                headers=self._headers,
                json={"doc": update_body},
            )
        except Exception:
            logger.exception("Failed to mark doc %s as processed", doc_id)

    def _cleanup_processed(self) -> None:
        """Delete processed/stale docs older than CLEANUP_AGE."""
        cutoff_ms = int((time.time() - CLEANUP_AGE) * 1000)
        delete_query = {
            "query": {
                "bool": {
                    "must": [
                        {"terms": {"status": ["processed", "stale"]}},
                        {"range": {"processed_at": {"lt": cutoff_ms}}},
                    ]
                }
            }
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(
                    f"{self._elastic_url}/{self._index}/_delete_by_query",
                    headers=self._headers,
                    json=delete_query,
                )
                if resp.status_code == 404:
                    return
                if resp.status_code < 300:
                    deleted = resp.json().get("deleted", 0)
                    if deleted:
                        logger.info("Cleaned up %d old remediation docs", deleted)
        except Exception:
            logger.debug("Cleanup of processed remediation docs failed", exc_info=True)

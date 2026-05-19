"""StreamsMixin — stream fork, significant events deploy and cleanup methods."""

from __future__ import annotations

import logging

import httpx

from elastic_config.deployer_base import _es_headers, _kibana_headers, _retry_http, ProgressCallback

logger = logging.getLogger("deployer")


class StreamsMixin:

    @property
    def _stream_name(self) -> str:
        return f"logs.otel.{self.ns}"

    @property
    def _ecs_stream_name(self) -> str:
        return f"logs.ecs.{self.ns}"

    @property
    def _ecs_wired_stream(self) -> str:
        """Wired-stream ingest endpoint. All scenarios POST to `logs.ecs/_bulk`;
        the deployer then forks `logs.ecs` into per-scenario partitions."""
        return "logs.ecs"

    def _create_stream(self, client: httpx.Client) -> None:
        """Fork logs.otel into a scenario-specific child stream."""
        resp = client.post(
            f"{self.kibana_url}/api/streams/logs.otel/_fork",
            headers=_kibana_headers(self.api_key),
            json={
                "where": {
                    "field": "resource.attributes.service.namespace",
                    "eq": self.ns,
                },
                "status": "enabled",
                "stream": {
                    "name": self._stream_name,
                },
            },
        )
        if resp.status_code >= 300:
            logger.warning("Stream fork failed (HTTP %s): %s", resp.status_code, resp.text[:500])

    def _create_ecs_stream(self, client: httpx.Client) -> None:
        """Fork the `logs.ecs` wired stream into this scenario's partition
        `logs.ecs.{ns}`, filtered by service.namespace.

        Mirrors how `logs.otel` / `logs.otel.{ns}` are handled. In 9.4+ wired
        streams are enabled by default, so no data-stream PUT is needed — the
        wired-stream endpoint accepts `_bulk` writes directly.
        """
        try:
            resp = client.post(
                f"{self.kibana_url}/api/streams/{self._ecs_wired_stream}/_fork",
                headers=_kibana_headers(self.api_key),
                json={
                    "where": {
                        "field": "service.namespace",
                        "eq": self.ns,
                    },
                    "status": "enabled",
                    "stream": {
                        "name": self._ecs_stream_name,
                    },
                },
            )
            if resp.status_code >= 300:
                logger.warning(
                    "ECS stream fork failed (HTTP %s): %s",
                    resp.status_code, resp.text[:500],
                )
        except Exception as exc:
            logger.warning("ECS stream fork exception (non-fatal): %s", exc)

    def _delete_ecs_stream(self, client: httpx.Client) -> bool:
        """Delete only this scenario's partition. The base wired stream
        `logs.ecs` is managed by Elastic and shared across all scenarios.

        Returns True if the partition is gone (or never existed); False if it
        is still present after retries.
        """
        # 1. Delete the partition Streams entity (mirrors logs.otel teardown).
        resp = _retry_http(
            lambda: client.delete(
                f"{self.kibana_url}/api/streams/{self._ecs_stream_name}",
                headers=_kibana_headers(self.api_key),
            ),
            label=f"delete ECS partition {self._ecs_stream_name}",
        )
        deleted_ok = resp is not None and resp.status_code in (200, 204, 404)
        if not deleted_ok and resp is not None:
            logger.warning(
                "Delete ECS partition stream %s returned HTTP %s after retries",
                self._ecs_stream_name, resp.status_code,
            )

        # 2. Delete this scenario's docs from the wired stream so co-deployed
        #    scenarios aren't affected.
        try:
            client.post(
                f"{self.elastic_url}/{self._ecs_wired_stream}/_delete_by_query",
                headers=_es_headers(self.api_key),
                params={"refresh": "false", "wait_for_completion": "false"},
                json={"query": {"term": {"service.namespace": self.ns}}},
            )
        except Exception as exc:
            logger.info("ECS docs delete-by-query skipped: %s", exc)

        return deleted_ok

    def _deploy_significant_events(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(10)
        step.status = "running"
        notify(self.progress)

        # Delete any existing stream then recreate it clean
        self._delete_stream(client)
        self._create_stream(client)

        # Build bulk operations
        operations = []
        registry = self.scenario.channel_registry
        for ch_num, ch_data in sorted(registry.items()):
            num_str = f"{int(ch_num):02d}"
            error_type = ch_data["error_type"]
            esql_query = (
                f"FROM {self._stream_name},{self._stream_name}.* METADATA _id, _source"
                f' | WHERE body.text LIKE "*{error_type}*" AND severity_text == "ERROR"'
            )
            operations.append({
                "index": {
                    "id": f"{self.ns}-se-ch{num_str}",
                    "title": f"{self.scenario.scenario_name}: SE CH {num_str}: {ch_data['name']}",
                    "description": f"{ch_data.get('subsystem', 'system')} — {error_type}",
                    "esql": {"query": esql_query},
                }
            })

        step.items_total = len(operations)

        if operations:
            resp = client.post(
                f"{self.kibana_url}/api/streams/{self._stream_name}/queries/_bulk",
                headers=_kibana_headers(self.api_key),
                json={"operations": operations},
            )
            if resp.status_code < 300:
                step.items_done = len(operations)
                step.detail = f"Created {len(operations)} stream queries on {self._stream_name}"
            else:
                logger.warning("Significant events bulk create failed: %s", resp.text[:500])
                step.detail = f"Bulk create failed (HTTP {resp.status_code})"

        step.status = "ok" if step.items_done > 0 else "failed"
        notify(self.progress)

    def _delete_stream(self, client: httpx.Client) -> bool:
        """Delete the scenario-specific stream (also removes its significant events).

        Returns True if the stream is gone (deleted or 404), False if still present.
        """
        resp = _retry_http(
            lambda: client.delete(
                f"{self.kibana_url}/api/streams/{self._stream_name}",
                headers=_kibana_headers(self.api_key),
            ),
            label=f"delete stream {self._stream_name}",
        )
        if resp is None:
            return False
        if resp.status_code == 404 or resp.status_code < 300:
            return True
        logger.warning(
            "Failed to delete stream %s after retries: HTTP %s",
            self._stream_name, resp.status_code,
        )
        return False

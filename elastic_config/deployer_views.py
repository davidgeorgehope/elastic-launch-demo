"""DataViewsMixin — data view deploy methods."""

from __future__ import annotations

import urllib.parse

import httpx

from elastic_config.deployer_base import _kibana_headers, _retry_http, ProgressCallback


class DataViewsMixin:

    def _deploy_data_views(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(11)
        step.status = "running"
        notify(self.progress)

        views = [
            # Unified scenario logs view — exec dashboard panels query through
            # this. Includes both the OTel and ECS wired-stream partitions so
            # cross-source queries (e.g. AI Assistant investigations) work.
            {
                "data_view": {
                    "id": f"logs.otel.{self.ns}",
                    "title": (
                        f"logs.otel.{self.ns},logs.otel.{self.ns}.*,"
                        f"logs.ecs.{self.ns},logs.ecs.{self.ns}.*,"
                        "logs-*"
                    ),
                    "name": f"{self.scenario.scenario_name} Logs",
                    "timeFieldName": "@timestamp",
                },
                "override": True,
            },
            # Dedicated ECS partition view — drives the "create a dashboard
            # from this index" Agent Builder skill demo. The visualization
            # skill resolves `logs.ecs.{ns}` to this data view.
            {
                "data_view": {
                    "id": f"logs.ecs.{self.ns}",
                    "title": f"logs.ecs.{self.ns},logs.ecs.{self.ns}.*",
                    "name": f"{self.scenario.scenario_name} Logs (ECS)",
                    "timeFieldName": "@timestamp",
                },
                "override": True,
            },
            # OTel-standard views — required by shipped [OTel] dashboards
            {
                "data_view": {
                    "id": "logs-*",
                    "title": "logs-*",
                    "name": "logs-*",
                    "timeFieldName": "@timestamp",
                },
                "override": True,
            },
            {
                "data_view": {
                    "id": "traces-*",
                    "title": "traces-*",
                    "name": f"{self.scenario.scenario_name} Traces",
                    "timeFieldName": "@timestamp",
                },
                "override": True,
            },
            {
                "data_view": {
                    "id": "metrics-*",
                    "title": "metrics-*",
                    "name": f"{self.scenario.scenario_name} Metrics",
                    "timeFieldName": "@timestamp",
                },
                "override": True,
            },
            # Required by [OTel] Host Details dashboards
            {
                "data_view": {
                    "id": "metrics-hostmetricsreceiver.otel-*",
                    "title": "metrics-hostmetricsreceiver.otel-*",
                    "name": "metrics-hostmetricsreceiver.otel-*",
                    "timeFieldName": "@timestamp",
                },
                "override": True,
            },
        ]

        step.items_total = len(views)
        created = 0
        for view in views:
            resp = client.post(
                f"{self.kibana_url}/api/data_views/data_view",
                headers=_kibana_headers(self.api_key),
                json=view,
            )
            if resp.status_code < 300:
                created += 1
                step.items_done = created
                notify(self.progress)

        step.status = "ok"
        step.detail = f"Created {created} data views"
        notify(self.progress)

    def _cleanup_data_views(self, client: httpx.Client) -> tuple[int, int]:
        """Delete data views belonging to this scenario (matched by name prefix).

        Returns ``(deleted, remaining)`` — remaining > 0 means some views could
        not be removed even after retries (e.g. persistent API errors).
        """
        scenario_prefix = f"{self.scenario.scenario_name} "
        deleted = 0

        def _list_views() -> list[dict]:
            resp = _retry_http(
                lambda: client.get(
                    f"{self.kibana_url}/api/data_views",
                    headers=_kibana_headers(self.api_key),
                ),
                label="list data views",
            )
            if resp is None or resp.status_code >= 300:
                return []
            try:
                return resp.json().get("data_view", [])
            except Exception:
                return []

        for view in _list_views():
            if not view.get("name", "").startswith(scenario_prefix):
                continue
            view_id = view.get("id", "")
            if not view_id:
                continue
            encoded_id = urllib.parse.quote(view_id, safe="")
            r = _retry_http(
                lambda: client.delete(
                    f"{self.kibana_url}/api/data_views/data_view/{encoded_id}",
                    headers=_kibana_headers(self.api_key),
                ),
                label=f"delete data view {view_id}",
            )
            if r is not None and (r.status_code < 300 or r.status_code == 404):
                deleted += 1

        # Verify: count any remaining views still matching this scenario.
        remaining = sum(
            1 for v in _list_views() if v.get("name", "").startswith(scenario_prefix)
        )
        return deleted, remaining

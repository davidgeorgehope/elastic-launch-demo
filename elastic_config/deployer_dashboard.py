"""DashboardMixin — dashboard deploy methods."""

from __future__ import annotations

import logging

import httpx

from elastic_config.deployer_base import _kibana_headers, ProgressCallback

logger = logging.getLogger("deployer")


class DashboardMixin:

    def _deploy_dashboard(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(12)
        step.status = "running"
        notify(self.progress)

        try:
            # Generate scenario-specific dashboard NDJSON dynamically
            from elastic_config.dashboards.generate_exec_dashboard import generate_dashboard_ndjson

            ndjson_str = generate_dashboard_ndjson(self.scenario)

            resp = client.post(
                f"{self.kibana_url}/api/saved_objects/_import?overwrite=true",
                headers={
                    "kbn-xsrf": "true",
                    "Authorization": f"ApiKey {self.api_key}",
                },
                files={"file": ("dashboard.ndjson", ndjson_str.encode(), "application/x-ndjson")},
            )
            if resp.status_code < 300:
                try:
                    data = resp.json()
                    count = data.get("successCount", 0)
                    step.items_total = count
                    step.items_done = count
                    step.detail = f"Imported {count} objects ({self.scenario.scenario_name})"
                except Exception:
                    step.detail = "Dashboard imported"
                step.status = "ok"
            else:
                step.status = "failed"
                step.detail = f"Import failed (HTTP {resp.status_code})"
        except Exception as exc:
            step.status = "failed"
            step.detail = f"Dashboard generation failed: {exc}"
            logger.exception("Dashboard generation failed")

        notify(self.progress)

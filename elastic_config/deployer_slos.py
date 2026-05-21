"""SloMixin — SLO deploy and cleanup methods."""

from __future__ import annotations

import logging

import httpx

from elastic_config.deployer_base import ProgressCallback

logger = logging.getLogger("deployer")


class SloMixin:

    def _deploy_slos(self, client: httpx.Client, notify: ProgressCallback):
        """Create the three standard SLOs via the Kibana SLO API."""
        step = self._step(18)
        step.status = "running"
        notify(self.progress)

        _slo_headers = {
            "Content-Type": "application/json",
            "kbn-xsrf": "true",
            "Authorization": f"ApiKey {self.api_key}",
        }
        _slo_index = "traces-apm*,traces-*.otel-*"

        scenario_name = self.scenario.scenario_name
        slo_definitions = [
            {
                "name": f"{scenario_name}: Availability SLO",
                "description": "Service availability - 95% target, grouped by service name",
                "indicator": {
                    "type": "sli.kql.custom",
                    "params": {
                        "index": _slo_index,
                        "good": "NOT event.outcome:failure",
                        "filter": "processor.event:transaction",
                        "total": "*",
                        "timestampField": "@timestamp",
                    },
                },
                "groupBy": ["service.name"],
                "budgetingMethod": "occurrences",
                "timeWindow": {"duration": "7d", "type": "rolling"},
                "objective": {"target": 0.95},
                "tags": ["auto-created"],
            },
            {
                "name": f"{scenario_name}: Latency SLO",
                "description": "Service latency - 85% of requests under 2s, grouped by service name",
                "indicator": {
                    "type": "sli.kql.custom",
                    "params": {
                        "index": _slo_index,
                        "filter": "processor.event:transaction AND transaction.duration.us:*",
                        "good": "transaction.duration.us <= 2000000",
                        "total": "transaction.duration.us:*",
                        "timestampField": "@timestamp",
                    },
                },
                "groupBy": ["service.name"],
                "budgetingMethod": "occurrences",
                "timeWindow": {"duration": "7d", "type": "rolling"},
                "objective": {"target": 0.85},
                "tags": ["auto-created"],
            },
            {
                "name": f"{scenario_name}: Error Rate SLO",
                "description": "Service error rate - less than 5% errors, grouped by service name",
                "indicator": {
                    "type": "sli.kql.custom",
                    "params": {
                        "index": _slo_index,
                        "filter": "processor.event:transaction",
                        "good": "NOT event.outcome:failure",
                        "total": "*",
                        "timestampField": "@timestamp",
                    },
                },
                "groupBy": ["service.name"],
                "budgetingMethod": "occurrences",
                "timeWindow": {"duration": "7d", "type": "rolling"},
                "objective": {"target": 0.95},
                "tags": ["auto-created"],
            },
        ]

        # Delete any pre-existing SLOs with these names to avoid duplicates
        self._cleanup_slos(client)

        created = 0
        for slo in slo_definitions:
            resp = client.post(
                f"{self.kibana_url}/api/observability/slos",
                headers=_slo_headers,
                json=slo,
            )
            if resp.status_code < 300:
                created += 1
                step.items_done = created
                step.detail = f"Created: {slo['name']}"
            else:
                logger.warning("SLO create failed %s: %s", slo["name"], resp.text)
            notify(self.progress)

        step.status = "ok" if created > 0 else "failed"
        step.detail = f"Created {created}/3 SLOs"
        notify(self.progress)

    def _cleanup_slos(self, client: httpx.Client) -> int:
        """Delete SLOs belonging to this scenario."""
        scenario_name = self.scenario.scenario_name
        _slo_names = {
            f"{scenario_name}: Availability SLO",
            f"{scenario_name}: Latency SLO",
            f"{scenario_name}: Error Rate SLO",
        }
        _headers = {
            "Content-Type": "application/json",
            "kbn-xsrf": "true",
            "Authorization": f"ApiKey {self.api_key}",
        }
        deleted = 0
        try:
            resp = client.get(
                f"{self.kibana_url}/api/observability/slos?perPage=500",
                headers=_headers,
            )
            if resp.status_code >= 300:
                return 0
            for slo in resp.json().get("results", []):
                if slo.get("name") in _slo_names:
                    slo_id = slo.get("id", "")
                    if slo_id:
                        client.delete(
                            f"{self.kibana_url}/api/observability/slos/{slo_id}",
                            headers=_headers,
                        )
                        deleted += 1
        except Exception:
            pass
        return deleted

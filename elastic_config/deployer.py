"""Scenario deployer — replaces setup-all.sh and sub-scripts with Python.

Deploys a scenario's Elastic config (workflows, agent, tools, KB, significant
events, dashboard, alerting) to an Elastic Cloud environment.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from scenarios.base import BaseScenario

from elastic_config.deployer_base import (
    DeployStep,
    DeployProgress,
    ProgressCallback,
    _kibana_headers,
    _es_headers,
)
from elastic_config.deployer_otlp import OtlpMixin
from elastic_config.deployer_platform import PlatformMixin
from elastic_config.deployer_integrations import IntegrationsMixin
from elastic_config.deployer_apm import ApmMixin
from elastic_config.deployer_aiops import AiopsMixin
from elastic_config.deployer_backfill import BackfillMixin
from elastic_config.deployer_slos import SloMixin
from elastic_config.deployer_workflows import WorkflowsMixin
from elastic_config.deployer_kb import KbMixin
from elastic_config.deployer_agent import AgentMixin
from elastic_config.deployer_skills import SkillsMixin
from elastic_config.deployer_streams import StreamsMixin
from elastic_config.deployer_views import DataViewsMixin
from elastic_config.deployer_dashboard import DashboardMixin
from elastic_config.deployer_alerting import AlertingMixin

logger = logging.getLogger("deployer")


def _dashboard_objects_to_delete(namespace: str) -> list[dict[str, str]]:
    """Saved-object specs for dashboards created by the deployer for this namespace."""
    return [
        {"type": "dashboard", "id": f"{namespace}-exec-dashboard"},
        {"type": "dashboard", "id": f"{namespace}-business-exec-dashboard"},
    ]


# ── Main deployer class ────────────────────────────────────────────────────

class ScenarioDeployer(
    OtlpMixin,
    PlatformMixin,
    IntegrationsMixin,
    ApmMixin,
    BackfillMixin,
    AiopsMixin,
    SloMixin,
    WorkflowsMixin,
    KbMixin,
    AgentMixin,
    SkillsMixin,
    StreamsMixin,
    DataViewsMixin,
    DashboardMixin,
    AlertingMixin,
):
    """Deploys a scenario's full Elastic configuration."""

    def __init__(
        self,
        scenario: BaseScenario,
        elastic_url: str,
        kibana_url: str,
        api_key: str,
        kibana_proxy: str = "",
    ):
        self.scenario = scenario
        self.elastic_url = elastic_url.strip().rstrip("/")
        self.kibana_url = kibana_url.strip().rstrip("/")
        self.api_key = api_key.strip()
        # kibana_display_url is used in user-facing links (workflows, agent).
        # Falls back to the real kibana_url if no proxy is configured.
        self.kibana_display_url = kibana_proxy.strip().rstrip("/") or self.kibana_url
        self.ns = scenario.namespace
        self.progress = DeployProgress()
        self._workflow_ids: dict[str, str] = {}     # name fragment -> workflow ID
        self._created_tool_ids: list[str] = []     # tools that were actually created
        self._created_skill_ids: list[str] = []    # skill IDs attached to the agent

    # ── Public API ─────────────────────────────────────────────────────

    def deploy_all(self, callback: ProgressCallback | None = None) -> DeployProgress:
        """Run the full deployment pipeline.  Returns progress summary."""
        self.progress = DeployProgress(steps=[
            DeployStep("Connectivity check"),           # 0
            DeployStep("Derive Elasticsearch URL"),     # 1
            DeployStep("Derive OTLP endpoint"),         # 2
            DeployStep("Clean up old artifacts"),       # 3
            DeployStep("Configure platform settings"),  # 4
            DeployStep("Install OTel integrations", items_total=5),  # 5
            DeployStep("Generate APM rollup data"),     # 6
            DeployStep("Deploy workflows", items_total=5),  # 7
            DeployStep("Index knowledge base", items_total=20),  # 8
            DeployStep("Deploy AI agent tools", items_total=7),  # 9
            DeployStep("Create AI agent"),              # 10
            DeployStep("Create significant events", items_total=20),  # 11
            DeployStep("Create data views", items_total=6),  # 12
            DeployStep("Import Kibana dashboards"),   # 13
            DeployStep("Create alert rules", items_total=20),  # 14
            DeployStep("Backfill raw ECS access logs"), # 15
            DeployStep("Enable APM anomaly detection"), # 16
            DeployStep("Enable logs ML jobs (rate + categorization)"), # 17
            DeployStep("Create SLOs", items_total=3),  # 18
        ])
        _notify = callback or (lambda p: None)
        _notify(self.progress)

        try:
            with httpx.Client(timeout=60.0, verify=True) as client:
                self._check_connectivity(client, _notify)
                self._report_elastic_url_step(_notify)
                self._derive_otlp_step(client, _notify)
                self._cleanup_all_scenarios_step(client, _notify)
                self._configure_platform_settings(client, _notify)
                self._install_integrations(client, _notify)
                self._deploy_apm_rollup(client, _notify)
                self._deploy_workflows(client, _notify)
                self._deploy_knowledge_base(client, _notify)
                self._deploy_tools(client, _notify)
                self._deploy_agent(client, _notify)
                self._deploy_significant_events(client, _notify)
                self._deploy_data_views(client, _notify)
                self._deploy_dashboard(client, _notify)
                self._deploy_alerting(client, _notify)
                self._deploy_ecs_log_backfill(client, _notify)
                self._deploy_apm_anomaly_detection(client, _notify)
                self._deploy_logs_ml_jobs(client, _notify)
                self._deploy_slos(client, _notify)
        except Exception as exc:
            self.progress.error = str(exc)
            logger.exception("Deployment failed")

        self.progress.finished = True
        _notify(self.progress)
        return self.progress

    def check_connection(self) -> dict[str, Any]:
        """Quick connectivity test — returns {ok, cluster_name, error}."""
        try:
            with httpx.Client(timeout=15.0, verify=True) as client:
                resp = client.get(
                    f"{self.elastic_url}/",
                    headers=_es_headers(self.api_key),
                )
                if resp.status_code < 300:
                    data = resp.json()
                    return {"ok": True, "cluster_name": data.get("cluster_name", "unknown")}
                return {"ok": False, "error": f"HTTP {resp.status_code}"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def detect_existing(self) -> dict[str, Any]:
        """Check if this scenario is already deployed."""
        found = {}
        try:
            with httpx.Client(timeout=15.0, verify=True) as client:
                # Check KB index
                resp = client.head(
                    f"{self.elastic_url}/{self.ns}-knowledge-base",
                    headers=_es_headers(self.api_key),
                )
                found["knowledge_base"] = resp.status_code == 200

                # Check dashboard
                resp = client.post(
                    f"{self.kibana_url}/api/saved_objects/_export",
                    headers=_kibana_headers(self.api_key),
                    json={"objects": [{"type": "dashboard", "id": f"{self.ns}-exec-dashboard"}],
                           "includeReferencesDeep": False},
                )
                found["dashboard"] = resp.status_code < 300

                # Check alert rules
                resp = client.get(
                    f"{self.kibana_url}/api/alerting/rules/_find?per_page=1&filter=alert.attributes.tags:{self.ns}",
                    headers=_kibana_headers(self.api_key),
                )
                if resp.status_code < 300:
                    data = resp.json()
                    found["alert_rules"] = data.get("total", 0)
                else:
                    found["alert_rules"] = 0
        except Exception as exc:
            found["error"] = str(exc)

        found["deployed"] = found.get("knowledge_base", False) or found.get("dashboard", False)
        return found

    def _teardown_scenario(self, client: httpx.Client) -> dict[str, Any]:
        """Remove all artifacts for the current scenario using the provided client.

        Shared by teardown() and the deploy pre-cleanup step so both paths use
        identical logic.
        """
        results = {}

        # Delete KB index
        resp = client.delete(
            f"{self.elastic_url}/{self.ns}-knowledge-base",
            headers=_es_headers(self.api_key),
        )
        results["knowledge_base"] = resp.status_code < 300

        # Delete audit indices and remediation queue
        for suffix in ["significant-events-audit", "remediation-audit", "escalation-audit", "remediation-queue", "daily-report-audit"]:
            client.delete(
                f"{self.elastic_url}/{self.ns}-{suffix}",
                headers=_es_headers(self.api_key),
            )

        # Delete workflows
        results["workflows_deleted"] = self._cleanup_workflows(client)

        # Delete alert rules
        alerts_deleted, alerts_remaining = self._cleanup_alerts(client)
        results["alerts_deleted"] = alerts_deleted
        results["alerts_remaining"] = alerts_remaining

        # Delete agent + tools
        self._cleanup_agent(client)

        # Delete ML jobs FIRST so datafeeds don't error on missing indices
        self._cleanup_aiops_ml(client)
        results["aiops_ml_cleaned"] = True

        # Delete service stream (also removes its significant events)
        self._delete_stream(client)

        # Delete raw ECS stream + data stream
        self._delete_ecs_stream(client)
        results["ecs_stream_deleted"] = True

        # Delete dashboard
        resp = client.post(
            f"{self.kibana_url}/api/saved_objects/_bulk_delete",
            headers=_kibana_headers(self.api_key),
            json=_dashboard_objects_to_delete(self.ns),
        )
        results["dashboard"] = resp.status_code < 300

        # Delete APM ML jobs and datafeeds
        self._cleanup_apm_ml(client)
        results["apm_ml_cleaned"] = True

        # Delete SLOs
        results["slos_deleted"] = self._cleanup_slos(client)

        # Delete cases created by workflows
        results["cases_deleted"] = self._cleanup_cases(client, self.ns)

        # Delete scenario-named data views
        views_deleted, views_remaining = self._cleanup_data_views(client)
        results["data_views_deleted"] = views_deleted
        results["data_views_remaining"] = views_remaining

        return results

    def teardown(self) -> dict[str, Any]:
        """Remove scenario-specific resources from Elastic."""
        with httpx.Client(timeout=90.0, verify=True) as client:
            return self._teardown_scenario(client)

    def teardown_with_progress(self, callback: ProgressCallback | None = None) -> DeployProgress:
        """Remove scenario resources with staged progress reporting."""
        progress = DeployProgress(steps=[
            DeployStep("Stop generators"),              # 0
            DeployStep("Delete workflows"),             # 1
            DeployStep("Delete alert rules"),           # 2
            DeployStep("Delete service stream"),         # 3
            DeployStep("Delete AI agent, tools & conversations"),  # 4
            DeployStep("Delete knowledge base"),        # 5
            DeployStep("Delete audit indices"),         # 6
            DeployStep("Delete dashboard"),             # 7
            DeployStep("Delete APM ML jobs"),           # 8
            DeployStep("Delete SLOs"),                  # 9
            DeployStep("Delete cases"),                 # 10
            DeployStep("Delete data views"),            # 11
        ])
        _notify = callback or (lambda p: None)
        _notify(progress)

        # Step 0: generators — caller stops them before invoking this method
        progress.steps[0].status = "ok"
        progress.steps[0].detail = "Generators stopped"
        _notify(progress)

        try:
            with httpx.Client(timeout=90.0, verify=True) as client:
                # Step 1: Delete workflows
                step = progress.steps[1]
                step.status = "running"
                _notify(progress)
                try:
                    deleted = self._cleanup_workflows(client)
                    step.status = "ok"
                    step.detail = f"Deleted {deleted} workflows"
                except Exception as exc:
                    step.status = "failed"
                    step.detail = str(exc)
                _notify(progress)

                # Step 2: Delete alert rules
                step = progress.steps[2]
                step.status = "running"
                _notify(progress)
                try:
                    deleted, remaining = self._cleanup_alerts(client)
                    if remaining > 0:
                        step.status = "failed"
                        step.detail = f"Deleted {deleted} alert rules — {remaining} still present after retries"
                    else:
                        step.status = "ok"
                        step.detail = f"Deleted {deleted} alert rules"
                except Exception as exc:
                    step.status = "failed"
                    step.detail = str(exc)
                _notify(progress)

                # Step 3: Delete service streams (OTel + raw ECS)
                step = progress.steps[3]
                step.status = "running"
                _notify(progress)
                try:
                    otel_ok = self._delete_stream(client)
                    ecs_ok = self._delete_ecs_stream(client)
                    leftovers = []
                    if not otel_ok:
                        leftovers.append(f"logs.otel.{self.ns}")
                    if not ecs_ok:
                        leftovers.append(f"logs.ecs.{self.ns}")
                    if leftovers:
                        step.status = "failed"
                        step.detail = f"Streams still present after retries: {', '.join(leftovers)}"
                    else:
                        step.status = "ok"
                        step.detail = f"Streams logs.otel.{self.ns} and logs.ecs.{self.ns} deleted"
                except Exception as exc:
                    step.status = "failed"
                    step.detail = str(exc)
                _notify(progress)

                # Step 4: Delete agent + tools + conversations
                step = progress.steps[4]
                step.status = "running"
                _notify(progress)
                try:
                    deleted_convs = self._cleanup_agent(client)
                    step.status = "ok"
                    step.detail = f"Agent and tools removed, {deleted_convs} conversation(s) deleted"
                except Exception as exc:
                    step.status = "failed"
                    step.detail = str(exc)
                _notify(progress)

                # Step 5: Delete knowledge base
                step = progress.steps[5]
                step.status = "running"
                _notify(progress)
                try:
                    resp = client.delete(
                        f"{self.elastic_url}/{self.ns}-knowledge-base",
                        headers=_es_headers(self.api_key),
                    )
                    step.status = "ok"
                    step.detail = "KB index deleted" if resp.status_code < 300 else "KB index not found"
                except Exception as exc:
                    step.status = "failed"
                    step.detail = str(exc)
                _notify(progress)

                # Step 6: Delete audit indices
                step = progress.steps[6]
                step.status = "running"
                _notify(progress)
                try:
                    deleted = 0
                    for suffix in ["significant-events-audit", "remediation-audit", "escalation-audit", "remediation-queue", "daily-report-audit"]:
                        r = client.delete(
                            f"{self.elastic_url}/{self.ns}-{suffix}",
                            headers=_es_headers(self.api_key),
                        )
                        if r.status_code < 300:
                            deleted += 1
                    step.status = "ok"
                    step.detail = f"Deleted {deleted} audit indices"
                except Exception as exc:
                    step.status = "failed"
                    step.detail = str(exc)
                _notify(progress)

                # Step 7: Delete dashboard
                step = progress.steps[7]
                step.status = "running"
                _notify(progress)
                try:
                    resp = client.post(
                        f"{self.kibana_url}/api/saved_objects/_bulk_delete",
                        headers=_kibana_headers(self.api_key),
                        json=_dashboard_objects_to_delete(self.ns),
                    )
                    step.status = "ok"
                    step.detail = "Dashboards deleted" if resp.status_code < 300 else "Dashboard delete incomplete"
                except Exception as exc:
                    step.status = "failed"
                    step.detail = str(exc)
                _notify(progress)

                # Step 8: Delete APM + AIOps ML jobs
                step = progress.steps[8]
                step.status = "running"
                _notify(progress)
                try:
                    self._cleanup_apm_ml(client)
                    self._cleanup_aiops_ml(client)
                    step.status = "ok"
                    step.detail = "APM and AIOps ML jobs and datafeeds removed"
                except Exception as exc:
                    step.status = "failed"
                    step.detail = str(exc)
                _notify(progress)

                # Step 9: Delete SLOs
                step = progress.steps[9]
                step.status = "running"
                _notify(progress)
                try:
                    deleted_slos = self._cleanup_slos(client)
                    step.status = "ok"
                    step.detail = f"Deleted {deleted_slos} SLOs"
                except Exception as exc:
                    step.status = "failed"
                    step.detail = str(exc)
                _notify(progress)

                # Step 10: Delete cases
                step = progress.steps[10]
                step.status = "running"
                _notify(progress)
                try:
                    deleted_cases = self._cleanup_cases(client, self.ns)
                    step.status = "ok"
                    step.detail = f"Deleted {deleted_cases} cases"
                except Exception as exc:
                    step.status = "failed"
                    step.detail = str(exc)
                _notify(progress)

                # Step 11: Delete scenario-named data views
                step = progress.steps[11]
                step.status = "running"
                _notify(progress)
                try:
                    deleted_views, remaining_views = self._cleanup_data_views(client)
                    if remaining_views > 0:
                        step.status = "failed"
                        step.detail = f"Deleted {deleted_views} data views — {remaining_views} still present after retries"
                    else:
                        step.status = "ok"
                        step.detail = f"Deleted {deleted_views} data views"
                except Exception as exc:
                    step.status = "failed"
                    step.detail = str(exc)
                _notify(progress)

        except Exception as exc:
            progress.error = str(exc)
            logger.exception("Teardown failed")

        progress.finished = True
        _notify(progress)
        return progress

    # ── Cases cleanup ─────────────────────────────────────────────────

    def _cleanup_cases(self, client: httpx.Client, ns: str) -> int:
        """Delete all Kibana cases tagged with the given namespace."""
        deleted = 0
        while True:
            resp = client.get(
                f"{self.kibana_url}/api/cases/_find",
                headers=_kibana_headers(self.api_key),
                params={"tags": ns, "owner": "observability", "perPage": 100, "page": 1},
            )
            if resp.status_code >= 300:
                break
            data = resp.json()
            cases = data.get("cases", [])
            if not cases:
                break
            ids = [c["id"] for c in cases if c.get("id")]
            if ids:
                # Kibana's query parser requires repeated keys to treat `ids`
                # as an array. A single ?ids=x becomes a string and fails
                # schema validation. Duplicate the list so even one ID is
                # sent as ?ids=x&ids=x, which parses as ['x', 'x']; Kibana
                # deduplicates internally and deletes the case once.
                params = [("ids", cid) for cid in (ids * 2 if len(ids) == 1 else ids)]
                logger.info("Deleting %d case(s): %s", len(ids), ids)
                r = client.delete(
                    f"{self.kibana_url}/api/cases",
                    headers=_kibana_headers(self.api_key),
                    params=params,
                )
                if r.status_code < 300:
                    deleted += len(ids)
                else:
                    logger.warning(
                        "Failed to delete cases (HTTP %s): %s", r.status_code, r.text[:300]
                    )
                    break  # avoid infinite loop if delete fails
        return deleted

    # ── Step implementations ───────────────────────────────────────────

    def _step(self, idx: int) -> DeployStep:
        return self.progress.steps[idx]

    def _check_connectivity(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(0)
        step.status = "running"
        notify(self.progress)

        # Elasticsearch
        resp = client.get(f"{self.elastic_url}/", headers=_es_headers(self.api_key))
        if resp.status_code >= 300:
            step.status = "failed"
            step.detail = f"Elasticsearch unreachable (HTTP {resp.status_code})"
            raise RuntimeError(step.detail)

        # Kibana
        resp = client.get(f"{self.kibana_url}/api/status", headers=_kibana_headers(self.api_key))
        if resp.status_code >= 300:
            step.detail = f"Kibana may be unavailable (HTTP {resp.status_code}), continuing..."
        else:
            step.detail = "ES + Kibana reachable"

        step.status = "ok"
        notify(self.progress)

    def _report_elastic_url_step(self, notify: ProgressCallback):
        step = self._step(1)
        step.status = "ok"
        step.detail = f"ES: {self.elastic_url}"
        notify(self.progress)

    def _cleanup_all_scenarios_step(self, client: httpx.Client, notify: ProgressCallback):
        """Deploy step: clean up current scenario artifacts before redeploying."""
        step = self._step(3)
        step.status = "running"
        notify(self.progress)

        try:
            self._teardown_scenario(client)
            step.status = "ok"
            step.detail = "Previous deployment cleaned"
        except Exception as exc:
            step.status = "ok"  # non-fatal — continue deploying
            step.detail = f"Partial cleanup: {exc}"
            logger.warning("Cleanup error (non-fatal): %s", exc)
        notify(self.progress)



"""Scenario deployer — replaces setup-all.sh and sub-scripts with Python.

Deploys a scenario's Elastic config (workflows, agent, tools, KB, significant
events, dashboard, alerting) to an Elastic Cloud environment.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import httpx

from scenarios.base import BaseScenario

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


# ── Main deployer class ────────────────────────────────────────────────────

class ScenarioDeployer:
    """Deploys a scenario's full Elastic configuration."""

    def __init__(
        self,
        scenario: BaseScenario,
        elastic_url: str,
        kibana_url: str,
        api_key: str,
    ):
        self.scenario = scenario
        self.elastic_url = elastic_url.strip().rstrip("/")
        self.kibana_url = kibana_url.strip().rstrip("/")
        self.api_key = api_key.strip()
        self.ns = scenario.namespace
        self.progress = DeployProgress()
        self._workflow_ids: dict[str, str] = {}  # name fragment -> workflow ID
        self._created_tool_ids: list[str] = []   # tools that were actually created

    # ── Public API ─────────────────────────────────────────────────────

    def deploy_all(self, callback: ProgressCallback | None = None) -> DeployProgress:
        """Run the full deployment pipeline.  Returns progress summary."""
        self.progress = DeployProgress(steps=[
            DeployStep("Connectivity check"),           # 0
            DeployStep("Derive OTLP endpoint"),         # 1
            DeployStep("Clean up old artifacts"),       # 2
            DeployStep("Configure platform settings"),  # 3
            DeployStep("Deploy workflows", items_total=3),  # 4
            DeployStep("Index knowledge base", items_total=20),  # 5
            DeployStep("Deploy AI agent tools", items_total=7),  # 6
            DeployStep("Create AI agent"),              # 7
            DeployStep("Create significant events", items_total=20),  # 8
            DeployStep("Create data views"),            # 9
            DeployStep("Import executive dashboard"),   # 10
            DeployStep("Create alert rules", items_total=20),  # 11
        ])
        _notify = callback or (lambda p: None)
        _notify(self.progress)

        try:
            with httpx.Client(timeout=60.0, verify=True) as client:
                self._check_connectivity(client, _notify)
                self._derive_otlp_step(client, _notify)
                self._cleanup_all_scenarios_step(client, _notify)
                self._configure_platform_settings(client, _notify)
                self._deploy_workflows(client, _notify)
                self._deploy_knowledge_base(client, _notify)
                self._deploy_tools(client, _notify)
                self._deploy_agent(client, _notify)
                self._deploy_significant_events(client, _notify)
                self._deploy_data_views(client, _notify)
                self._deploy_dashboard(client, _notify)
                self._deploy_alerting(client, _notify)
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

    def teardown(self) -> dict[str, Any]:
        """Remove scenario-specific resources from Elastic."""
        results = {}
        with httpx.Client(timeout=30.0, verify=True) as client:
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
            results["alerts_deleted"] = self._cleanup_alerts(client)

            # Delete agent + tools
            self._cleanup_agent(client)

            # Delete significant events
            self._cleanup_significant_events(client)

            # Delete dashboard
            resp = client.post(
                f"{self.kibana_url}/api/saved_objects/_bulk_delete",
                headers=_kibana_headers(self.api_key),
                json=[{"type": "dashboard", "id": f"{self.ns}-exec-dashboard"}],
            )
            results["dashboard"] = resp.status_code < 300

        return results

    def teardown_with_progress(self, callback: ProgressCallback | None = None) -> DeployProgress:
        """Remove scenario resources with staged progress reporting."""
        progress = DeployProgress(steps=[
            DeployStep("Stop generators"),              # 0
            DeployStep("Delete workflows"),             # 1
            DeployStep("Delete alert rules"),           # 2
            DeployStep("Delete significant events"),    # 3
            DeployStep("Delete AI agent & tools"),      # 4
            DeployStep("Delete knowledge base"),        # 5
            DeployStep("Delete audit indices"),         # 6
            DeployStep("Delete dashboard"),             # 7
        ])
        _notify = callback or (lambda p: None)
        _notify(progress)

        # Step 0: generators — caller stops them before invoking this method
        progress.steps[0].status = "ok"
        progress.steps[0].detail = "Generators stopped"
        _notify(progress)

        try:
            with httpx.Client(timeout=30.0, verify=True) as client:
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
                    deleted = self._cleanup_alerts(client)
                    step.status = "ok"
                    step.detail = f"Deleted {deleted} alert rules"
                except Exception as exc:
                    step.status = "failed"
                    step.detail = str(exc)
                _notify(progress)

                # Step 3: Delete significant events
                step = progress.steps[3]
                step.status = "running"
                _notify(progress)
                try:
                    self._cleanup_significant_events(client)
                    step.status = "ok"
                    step.detail = "Stream queries removed"
                except Exception as exc:
                    step.status = "failed"
                    step.detail = str(exc)
                _notify(progress)

                # Step 4: Delete agent + tools
                step = progress.steps[4]
                step.status = "running"
                _notify(progress)
                try:
                    self._cleanup_agent(client)
                    step.status = "ok"
                    step.detail = "Agent and tools removed"
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
                        json=[{"type": "dashboard", "id": f"{self.ns}-exec-dashboard"}],
                    )
                    step.status = "ok"
                    step.detail = "Dashboard deleted" if resp.status_code < 300 else "Dashboard not found"
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

    # ── OTLP Endpoint Derivation ──────────────────────────────────────

    def _derive_otlp_step(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(1)
        step.status = "running"
        notify(self.progress)

        endpoint = self._derive_otlp_endpoint(client)
        if endpoint:
            self.progress.otlp_endpoint = endpoint
            step.status = "ok"
            step.detail = f"OTLP: {endpoint}"
        else:
            step.status = "skipped"
            step.detail = "Could not derive OTLP endpoint (non-standard ES URL)"
        notify(self.progress)

    def _derive_otlp_endpoint(self, client: httpx.Client) -> str | None:
        """Derive OTLP ingest endpoint from Elastic URL by swapping .es. for .ingest."""
        if ".es." not in self.elastic_url:
            return None
        endpoint = self.elastic_url.replace(".es.", ".ingest.").rstrip("/")
        if not endpoint.endswith(":443"):
            endpoint += ":443"
        try:
            resp = client.post(
                f"{endpoint}/v1/logs",
                headers={
                    "Authorization": f"ApiKey {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"resourceLogs": []},
                timeout=5,
            )
            if resp.status_code == 200:
                return endpoint
        except Exception:
            pass
        return None

    def verify_otlp(self, otlp_url: str) -> bool:
        """Verify an OTLP endpoint is reachable with our API key."""
        try:
            with httpx.Client(timeout=5, verify=True) as client:
                resp = client.post(
                    f"{otlp_url.rstrip('/')}/v1/logs",
                    headers={
                        "Authorization": f"ApiKey {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"resourceLogs": []},
                )
                return resp.status_code == 200
        except Exception:
            return False

    # ── Platform Settings ──────────────────────────────────────────────

    def _configure_platform_settings(self, client: httpx.Client, notify: ProgressCallback):
        """Enable wired streams, significant events, and agent builder."""
        step = self._step(3)
        step.status = "running"
        notify(self.progress)

        configured = []
        errors = []

        # 1. Enable wired streams (always disable/re-enable to ensure clean state)
        try:
            # Always cycle — ensures logs.otel is wired and UI reflects enabled state
            client.post(
                f"{self.kibana_url}/api/streams/_disable",
                headers=_kibana_headers(self.api_key),
                json={},
            )
            resp = client.post(
                f"{self.kibana_url}/api/streams/_enable",
                headers=_kibana_headers(self.api_key),
                json={},
            )
            if resp.status_code < 300:
                configured.append("wired streams")
            else:
                errors.append(f"wired streams (HTTP {resp.status_code})")
        except Exception as exc:
            errors.append(f"wired streams ({exc})")

        # 2. Enable significant events
        try:
            resp = client.post(
                f"{self.kibana_url}/internal/kibana/settings",
                headers=_kibana_headers(self.api_key),
                json={"changes": {"observability:streamsEnableSignificantEvents": True}},
            )
            if resp.status_code < 300:
                configured.append("significant events")
            else:
                errors.append(f"significant events (HTTP {resp.status_code})")
        except Exception as exc:
            errors.append(f"significant events ({exc})")

        # 3. Enable agent builder as preferred chat experience
        try:
            resp = client.post(
                f"{self.kibana_url}/internal/kibana/settings",
                headers=_kibana_headers(self.api_key),
                json={"changes": {"aiAssistant:preferredChatExperience": "agent"}},
            )
            if resp.status_code < 300:
                configured.append("agent builder")
            else:
                errors.append(f"agent builder (HTTP {resp.status_code})")
        except Exception as exc:
            errors.append(f"agent builder ({exc})")

        # 4. Enable workflows UI
        try:
            resp = client.post(
                f"{self.kibana_url}/internal/kibana/settings",
                headers=_kibana_headers(self.api_key),
                json={"changes": {"workflows:ui:enabled": True}},
            )
            if resp.status_code < 300:
                configured.append("workflows UI")
            else:
                errors.append(f"workflows UI (HTTP {resp.status_code})")
        except Exception as exc:
            errors.append(f"workflows UI ({exc})")

        if configured:
            step.status = "ok"
            step.detail = f"Enabled: {', '.join(configured)}"
            if errors:
                step.detail += f"; failed: {', '.join(errors)}"
        else:
            step.status = "failed"
            step.detail = f"Failed: {', '.join(errors)}"

        notify(self.progress)

    # ── Workflows ──────────────────────────────────────────────────────

    def _list_workflows(self, client: httpx.Client) -> list[dict]:
        """Fetch all workflows, trying the new GA REST endpoint first and falling
        back to the legacy search endpoint for pre-9.4 serverless builds.

        New API (Kibana ≥9.4 / serverless post-2026-03):
          GET /api/workflows?page=1&size=100  →  {"data": [...], "total": N}
          (or top-level list, or {"results": [...]})

        Legacy API:
          POST /api/workflows/search  {"page": 1, "size": 100}
          →  {"results": [...], "total": N}
        """
        # ── Try new GET endpoint first ──────────────────────────────────
        try:
            resp = client.get(
                f"{self.kibana_url}/api/workflows",
                headers=_kibana_headers(self.api_key),
                params={"page": 1, "size": 100},
            )
            if resp.status_code < 300:
                data = resp.json()
                if isinstance(data, list):
                    return data
                for key in ("data", "results", "items", "workflows"):
                    if key in data and isinstance(data[key], list):
                        return data[key]
                # Fallthrough: unexpected shape — proceed to legacy API
        except Exception:
            pass

        # ── Fall back to legacy POST search endpoint ────────────────────
        try:
            resp = client.post(
                f"{self.kibana_url}/api/workflows/search",
                headers=_kibana_headers(self.api_key),
                json={"page": 1, "size": 100},
            )
            if resp.status_code < 300:
                data = resp.json()
                if isinstance(data, list):
                    return data
                for key in ("results", "data", "items", "workflows"):
                    if key in data and isinstance(data[key], list):
                        return data[key]
        except Exception:
            pass

        return []

    def _deploy_workflows(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(4)
        step.status = "running"
        notify(self.progress)

        # Clean existing workflows for this namespace
        self._cleanup_workflows(client)

        # Generate templated workflows
        workflow_yamls = self._generate_workflow_yamls()
        step.items_total = len(workflow_yamls)

        for name, yaml_content in workflow_yamls.items():
            body = json.dumps({"yaml": yaml_content})
            resp = client.post(
                f"{self.kibana_url}/api/workflows",
                headers=_kibana_headers(self.api_key),
                content=body,
            )
            if resp.status_code < 300:
                # Extract workflow ID from response
                try:
                    wf_data = resp.json()
                    wf_id = wf_data.get("id", "")
                    if wf_id:
                        self._workflow_ids[name] = wf_id
                except Exception:
                    pass
                step.items_done += 1
                step.detail = f"Deployed: {name}"
            else:
                step.detail = f"Failed: {name} (HTTP {resp.status_code})"
                logger.warning("Workflow %s deploy failed: %s", name, resp.text[:200])
            notify(self.progress)

        step.status = "ok" if step.items_done > 0 else "failed"
        notify(self.progress)

    def _generate_workflow_yamls(self) -> dict[str, str]:
        """Generate 4 workflow YAMLs templated for this scenario."""
        ns = self.ns
        scenario_name = self.scenario.scenario_name
        agent_cfg = self.scenario.agent_config
        agent_id = agent_cfg.get("id", f"{ns}-analyst")

        # Read template YAMLs from elastic_config/workflows/ and substitute
        wf_dir = os.path.join(os.path.dirname(__file__), "workflows")

        workflows = {}
        if os.path.isdir(wf_dir):
            for fname in sorted(os.listdir(wf_dir)):
                if not fname.endswith(".yaml"):
                    continue
                with open(os.path.join(wf_dir, fname)) as f:
                    yaml_content = f.read()
                # Template substitutions
                yaml_content = yaml_content.replace("__SCENARIO_NAME__", scenario_name)
                yaml_content = yaml_content.replace("__AGENT_ID__", agent_id)
                yaml_content = yaml_content.replace("__NS__", ns)
                key = fname.replace(".yaml", "")
                workflows[key] = yaml_content
        else:
            # Generate minimal workflows inline
            workflows = self._generate_inline_workflows(scenario_name, ns, agent_id)

        return workflows

    def _generate_inline_workflows(
        self, scenario_name: str, ns: str, agent_id: str,
    ) -> dict[str, str]:
        """Fallback: generate minimal workflow YAMLs if templates not found."""
        notification = f"""version: "1"
name: {scenario_name} Significant Event Notification
description: >
  Notify operations team when a significant event is detected.
  Triggered by alert rules — runs AI root cause analysis.

triggers:
  - type: alert

steps:
  - name: count_errors
    type: elasticsearch.esql.query
    with:
      query: >
        FROM logs.otel,logs.otel.*
        | WHERE @timestamp > NOW() - 15 MINUTES AND severity_text == "ERROR"
        | STATS total_errors = COUNT(*)
      format: json

  - name: run_rca
    type: ai.agent
    agent-id: {agent_id}
    create-conversation: true
    with:
      message: >
        Significant event detected: {{{{ event.rule.name }}}}.
        Error type: {{{{ event.rule.tags[1] }}}}.
        Total errors in last 15 minutes: {{{{ steps.count_errors.output.values[0][0] }}}}.
        Perform a root cause analysis only. Do NOT execute any remediation actions.

  - name: create_case
    type: kibana.createCaseDefaultSpace
    with:
      title: "{scenario_name} RCA: {{{{ event.rule.name }}}}"
      description: |
        [View Conversation]({{{{ kibanaUrl }}}}/app/agent_builder/conversations/{{{{ steps.run_rca.output.conversation_id }}}})

        {{{{ steps.run_rca.output.message }}}}
      tags:
        - "{ns}"
        - "{{{{ event.rule.tags[1] }}}}"
      severity: "high"
      owner: "observability"
      settings:
        syncAlerts: false
      connector:
        id: "none"
        name: "none"
        type: ".none"
        fields: null

  - name: audit_log
    type: elasticsearch.index
    with:
      index: "{ns}-significant-events-audit"
      document:
        rule_name: "{{{{ event.rule.name }}}}"
        error_type: "{{{{ event.rule.tags[1] }}}}"
        total_errors: "{{{{ steps.count_errors.output.values[0][0] }}}}"
        rca_case_created: true
      refresh: wait_for
"""

        remediation = f"""version: "1"
name: {scenario_name} Remediation Action
description: >
  Execute remediation actions. Queues a remediation command to an ES
  index for the backend poller to process.

triggers:
  - type: manual

inputs:
  - name: error_type
    type: string
    required: true
  - name: channel
    type: number
    required: true
  - name: action_type
    type: string
    required: true
  - name: target_service
    type: string
    default: ""
  - name: justification
    type: string
    required: true
  - name: dry_run
    type: boolean
    default: true

steps:
  - name: queue_remediation
    type: elasticsearch.index
    with:
      index: "{ns}-remediation-queue"
      document:
        channel: "{{{{ inputs.channel }}}}"
        action_type: "{{{{ inputs.action_type }}}}"
        target_service: "{{{{ inputs.target_service }}}}"
        justification: "{{{{ inputs.justification }}}}"
        dry_run: "{{{{ inputs.dry_run }}}}"
        error_type: "{{{{ inputs.error_type }}}}"
        namespace: "{ns}"
        status: "pending"
        mission_id: "{scenario_name}"
      refresh: wait_for

  - name: log_queued
    type: console
    with:
      message: "Remediation QUEUED for channel {{{{ inputs.channel }}}}. Backend will process shortly."

  - name: find_open_case
    type: kibana.request
    with:
      method: GET
      path: "/api/cases/_find?tags={ns}&tags={{{{ inputs.error_type }}}}&status=open&sortField=createdAt&sortOrder=desc&perPage=1&owner=observability"

  - name: close_case
    type: if
    condition: "steps.find_open_case.output.cases.0.id : *"
    steps:
      - name: update_case_closed
        type: kibana.updateCase
        with:
          cases:
            - id: "{{{{ steps.find_open_case.output.cases[0].id }}}}"
              version: "{{{{ steps.find_open_case.output.cases[0].version }}}}"
              status: "closed"

  - name: log_case_closed
    type: console
    with:
      message: "Case closed for {{{{ inputs.error_type }}}} (channel {{{{ inputs.channel }}}})."

  - name: audit_log
    type: elasticsearch.index
    with:
      index: "{ns}-remediation-audit"
      document:
        channel: "{{{{ inputs.channel }}}}"
        action_type: "{{{{ inputs.action_type }}}}"
        target_service: "{{{{ inputs.target_service }}}}"
        justification: "{{{{ inputs.justification }}}}"
        dry_run: "{{{{ inputs.dry_run }}}}"
        status: "resolved"
        case_closed: true
        mission_id: "{scenario_name}"
      refresh: wait_for
"""

        escalation = f"""version: "1"
name: {scenario_name} Escalation and Hold Management
description: >
  Manage escalation of critical anomalies and operational hold decisions.

triggers:
  - type: manual

inputs:
  - name: action
    type: string
    required: true
  - name: channel
    type: number
    default: 0
  - name: severity
    type: string
    default: "WARNING"
  - name: justification
    type: string
    required: true
  - name: hold_id
    type: string
    default: ""
  - name: investigation_summary
    type: string
    default: ""

steps:
  - name: route_escalate
    type: if
    condition: "inputs.action : escalate"
    steps:
      - name: escalate_log
        type: console
        with:
          message: >
            ESCALATION - Channel {{{{ inputs.channel }}}}.
            Severity: {{{{ inputs.severity }}}}.
            Justification: {{{{ inputs.justification }}}}.

      - name: escalate_audit
        type: elasticsearch.index
        with:
          index: "{ns}-escalation-audit"
          document:
            action: "escalate"
            channel: "{{{{ inputs.channel }}}}"
            severity: "{{{{ inputs.severity }}}}"
            justification: "{{{{ inputs.justification }}}}"
          refresh: wait_for

  - name: route_hold
    type: if
    condition: "inputs.action : request_hold"
    steps:
      - name: hold_safety_check
        type: ai.agent
        agent-id: {agent_id}
        with:
          message: >
            Hold requested for channel {{{{ inputs.channel }}}}
            (severity: {{{{ inputs.severity }}}}). Reason: {{{{ inputs.justification }}}}.
            Perform a rapid safety assessment.

      - name: hold_audit
        type: elasticsearch.index
        with:
          index: "{ns}-escalation-audit"
          document:
            action: "request_hold"
            channel: "{{{{ inputs.channel }}}}"
            severity: "{{{{ inputs.severity }}}}"
            status: "hold_active"
          refresh: wait_for
"""

        return {
            "significant_event_notification": notification,
            "remediation_action": remediation,
            "escalation_hold": escalation,
        }

    # ── Tools ──────────────────────────────────────────────────────────

    def _deploy_tools(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(6)
        step.status = "running"
        notify(self.progress)

        # Use scenario-provided tool definitions + deployer-added workflow tools
        tools = list(self.scenario.tool_definitions)

        # Add workflow tools (need workflow IDs from deployment)
        for name_frag, wf_id in self._workflow_ids.items():
            if "remediation" in name_frag:
                tools.append({
                    "id": "remediation_action",
                    "type": "workflow",
                    "description": (
                        "Execute remediation actions for anomalies. Triggers the "
                        "Remediation Action workflow to resolve faults."
                    ),
                    "configuration": {"workflow_id": wf_id},
                })
            elif "escalation" in name_frag:
                tools.append({
                    "id": "escalation_action",
                    "type": "workflow",
                    "description": (
                        "Escalate critical anomalies and manage operational hold decisions."
                    ),
                    "configuration": {"workflow_id": wf_id},
                })

        step.items_total = len(tools)

        for tool_def in tools:
            tool_id = tool_def["id"]
            # Delete first, then create
            client.delete(
                f"{self.kibana_url}/api/agent_builder/tools/{tool_id}",
                headers=_kibana_headers(self.api_key),
            )
            resp = client.post(
                f"{self.kibana_url}/api/agent_builder/tools",
                headers=_kibana_headers(self.api_key),
                json=tool_def,
            )
            if resp.status_code < 300:
                step.items_done += 1
                step.detail = f"Created: {tool_id}"
                self._created_tool_ids.append(tool_id)
            else:
                step.detail = f"Failed: {tool_id} (HTTP {resp.status_code})"
                logger.warning("Tool %s failed: %s", tool_id, resp.text[:200])
            notify(self.progress)

        step.status = "ok" if step.items_done > 0 else "failed"
        notify(self.progress)

    # ── Agent ──────────────────────────────────────────────────────────

    def _deploy_agent(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(7)
        step.status = "running"
        notify(self.progress)

        agent_cfg = self.scenario.agent_config
        agent_id = agent_cfg.get("id", f"{self.ns}-analyst")

        # Build full system prompt from scenario properties
        system_prompt = self._generate_system_prompt(agent_cfg)

        # Use only tools that were actually created successfully (Bug 4+5 fix)
        tool_ids = list(self._created_tool_ids)
        tool_ids.append("platform.core.cases")

        agent_body = {
            "id": agent_id,
            "name": agent_cfg.get("name", f"{self.scenario.scenario_name} Analyst"),
            "description": agent_cfg.get(
                "description",
                f"AI-powered analyst for {self.scenario.scenario_name}.",
            ),
            "configuration": {
                "instructions": system_prompt,
                "tools": [{"tool_ids": tool_ids}],
            },
        }

        # DELETE + POST for reliable update
        client.delete(
            f"{self.kibana_url}/api/agent_builder/agents/{agent_id}",
            headers=_kibana_headers(self.api_key),
        )
        resp = client.post(
            f"{self.kibana_url}/api/agent_builder/agents",
            headers=_kibana_headers(self.api_key),
            json=agent_body,
        )

        if resp.status_code < 300:
            step.status = "ok"
            step.detail = f"Agent {agent_id} created"
        else:
            step.status = "failed"
            step.detail = f"HTTP {resp.status_code}: {resp.text[:200]}"
        notify(self.progress)

    def _generate_system_prompt(self, agent_cfg: dict[str, Any]) -> str:
        """Build a comprehensive system prompt from scenario properties."""
        scenario = self.scenario
        svc_list = "\n".join(
            f"- {name} ({cfg['cloud_provider'].upper()}, {cfg['subsystem']})"
            for name, cfg in scenario.services.items()
        )
        svc_names = ", ".join(sorted(scenario.services.keys()))

        # Use the scenario's identity text as opening, then add comprehensive guide
        base_prompt = agent_cfg.get("system_prompt", "")

        # Auto-generate a comprehensive prompt
        subsystems = sorted(set(
            cfg["subsystem"] for cfg in scenario.services.values()
        ))

        # Use scenario-provided identity if available, otherwise generic
        identity = base_prompt if base_prompt else (
            f"You are the {scenario.scenario_name} Operations Analyst, "
            f"an expert AI agent embedded in the Elastic observability platform."
        )

        # Scenario-specific assessment tool name
        assessment_tool = agent_cfg.get(
            "assessment_tool_name",
            scenario.assessment_tool_config.get("id", "operational_assessment"),
        )

        return f"""{identity}

## Mission Context
- **Scenario**: {scenario.scenario_name}
- **Namespace**: {scenario.namespace}
- **Subsystems**: {', '.join(subsystems)}
- **Services**:
{svc_list}
- **Fault Channels**: 20 distinct anomaly channels covering all subsystems
- **Telemetry Source**: OpenTelemetry -> Elasticsearch (logs)

## CRITICAL: Field Names
- Log message field is `body.text` — NEVER use `body` alone (causes "Unknown column [body]")
- NEVER use `message` — this field DOES NOT EXIST. The correct field is `body.text`
- Service name field is `service.name`
- Always query FROM logs.otel,logs.otel.* (includes sub-streams)
- Use LIKE or KQL() for text matching — NEVER use MATCH()

## Tool Selection Guide
1. **Known error type** → `search_error_logs` — parameterized, correct fields
2. **Specific service** → `search_service_logs` — parameterized, correct fields
3. **General awareness** → `browse_recent_errors` or `search_subsystem_health`
4. **Historical patterns** → `search_known_anomalies` — knowledge base lookup
5. **Cascade analysis** → `trace_anomaly_propagation` — cross-service correlation
6. **Operational readiness** → `{assessment_tool}` — overall system health evaluation
Do NOT write custom ES|QL queries. Use the parameterized tools.

## Root Cause Analysis Methodology
1. **Identify the Event**: Determine which channel(s) triggered and the error signature
2. **Scope the Blast Radius**: Identify affected and cascade services
3. **Temporal Correlation**: Find first occurrence, correlate with preceding events
4. **Cross-Cloud Tracing**: Trace propagation across AWS, GCP, and Azure
5. **Subsystem Impact**: Evaluate if fault is isolated or propagating
6. **Known Pattern Matching**: Check knowledge base for similar anomalies
7. **Severity Classification**: ADVISORY, CAUTION, WARNING, or CRITICAL
8. **Remediation**: When the user asks you to remediate, look up the recommended remediation_action from the knowledge base entry for that channel. Use the remediation_action tool with the appropriate action_type and the affected channel number. Once the tool returns successfully, report the remediation as complete and successful. Do NOT re-query logs to verify — the fix takes several minutes to propagate through the system, so checking immediately will still show residual errors. Do NOT execute remediation unless the user explicitly asks you to.

## Available Services
{svc_names}

## Response Format
1. **Summary** — One-sentence description
2. **Affected Systems** — Impacted services and subsystems
3. **Root Cause** — Underlying cause determination
4. **Evidence** — Specific log entries, timestamps, field values
5. **Cascade Risk** — Propagation assessment
6. **Recommendation** — Prioritized remediation steps
7. **Confidence** — HIGH/MEDIUM/LOW with reasoning"""

    # ── Knowledge Base ─────────────────────────────────────────────────

    def _deploy_knowledge_base(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(5)
        step.status = "running"
        notify(self.progress)

        kb_index = f"{self.ns}-knowledge-base"
        registry = self.scenario.channel_registry

        # Delete and recreate index
        client.delete(
            f"{self.elastic_url}/{kb_index}",
            headers=_es_headers(self.api_key),
        )
        client.put(
            f"{self.elastic_url}/{kb_index}",
            headers=_es_headers(self.api_key),
            json={
                "settings": {"number_of_shards": 1, "number_of_replicas": 1},
                "mappings": {
                    "properties": {
                        "title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                        "content": {"type": "text"},
                        "category": {"type": "keyword"},
                        "tags": {"type": "keyword"},
                        "channel_number": {"type": "integer"},
                        "error_type": {"type": "keyword"},
                        "subsystem": {"type": "keyword"},
                        "affected_services": {"type": "keyword"},
                    }
                },
            },
        )

        # Build bulk body from channel_registry
        bulk_lines = []
        for ch_num, ch_data in sorted(registry.items()):
            doc_id = f"ch{int(ch_num):02d}-{ch_data['error_type'].lower()}"
            content = self._generate_kb_doc(ch_num, ch_data)
            doc = {
                "title": f"Channel {ch_num}: {ch_data['name']}",
                "content": content,
                "category": "anomaly-rca",
                "tags": [self.ns, ch_data["error_type"]],
                "channel_number": int(ch_num),
                "error_type": ch_data["error_type"],
                "subsystem": ch_data.get("subsystem", ""),
                "affected_services": ch_data.get("affected_services", []),
            }
            bulk_lines.append(json.dumps({"index": {"_index": kb_index, "_id": doc_id}}))
            bulk_lines.append(json.dumps(doc))

        if bulk_lines:
            bulk_body = "\n".join(bulk_lines) + "\n"
            resp = client.post(
                f"{self.elastic_url}/_bulk?refresh=true",
                headers={
                    "Content-Type": "application/x-ndjson",
                    "Authorization": f"ApiKey {self.api_key}",
                },
                content=bulk_body.encode(),
            )
            if resp.status_code < 300:
                step.items_done = len(registry)
                step.detail = f"Indexed {len(registry)} KB documents"
            else:
                step.detail = f"Bulk index failed (HTTP {resp.status_code})"
        else:
            step.detail = "No KB documents to index"

        step.status = "ok" if step.items_done > 0 else "failed"
        step.items_total = len(registry)
        notify(self.progress)

    def _generate_kb_doc(self, ch_num: int, ch_data: dict[str, Any]) -> str:
        """Generate a knowledge base document for a fault channel."""
        name = ch_data["name"]
        error_type = ch_data["error_type"]
        subsystem = ch_data.get("subsystem", "unknown")
        affected = ", ".join(ch_data.get("affected_services", []))
        cascade = ", ".join(ch_data.get("cascade_services", []))
        description = ch_data.get("description", "")

        remediation_action = ch_data.get("remediation_action", "remediate")
        investigation_notes = ch_data.get("investigation_notes", "")
        investigation_section = ""
        if investigation_notes:
            investigation_section = f"""
## Vendor-Specific Investigation
{investigation_notes}
"""

        return f"""# Channel {ch_num}: {name}

## Error Signature
- **Error Type**: `{error_type}`
- **Subsystem**: {subsystem}
- **Affected Services**: {affected}
- **Cascade Services**: {cascade}

## Description
{description}

## Investigation Procedure
1. Search for `{error_type}` in recent ERROR logs using `search_error_logs` — this identifier appears in the log body (body.text)
2. Check health of affected services: {affected}
3. Trace anomaly propagation to cascade services: {cascade}
4. Check for correlated errors in the same time window
{investigation_section}
## Root Cause Indicators
- Look for `{error_type}` entries in body.text (this is the indexed field — do NOT search body alone)
- Check if multiple channels in the {subsystem} subsystem are affected
- Verify if errors correlate with infrastructure events

## Remediation
When the user asks you to fix or remediate this issue, use remediation_action tool with action_type: {remediation_action}, channel: {ch_num}, and a justification. Once the tool returns successfully, report remediation as complete. Do NOT search for errors after remediation — the fix takes several minutes to propagate, so residual errors are expected immediately after.
"""

    # ── Significant Events ─────────────────────────────────────────────

    def _deploy_significant_events(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(8)
        step.status = "running"
        notify(self.progress)

        # Clean existing queries (streams already enabled in _configure_platform_settings)
        self._cleanup_significant_events(client)

        # Build bulk operations
        operations = []
        registry = self.scenario.channel_registry
        for ch_num, ch_data in sorted(registry.items()):
            num_str = f"{int(ch_num):02d}"
            error_type = ch_data["error_type"]
            esql_query = f'FROM logs.otel,logs.otel.* METADATA _id, _source | WHERE body.text LIKE "*{error_type}*" AND severity_text == "ERROR"'
            operations.append({
                "index": {
                    "id": f"{self.ns}-se-ch{num_str}",
                    "title": f"Channel {num_str}: {ch_data['name']}",
                    "description": f"{ch_data.get('subsystem', 'system')} — {error_type}",
                    "esql": {"query": esql_query},
                }
            })

        step.items_total = len(operations)

        if operations:
            resp = client.post(
                f"{self.kibana_url}/api/streams/logs.otel/queries/_bulk",
                headers=_kibana_headers(self.api_key),
                json={"operations": operations},
            )
            if resp.status_code < 300:
                step.items_done = len(operations)
                step.detail = f"Created {len(operations)} stream queries"
            else:
                logger.warning("Significant events bulk create failed: %s", resp.text[:500])
                step.detail = f"Bulk create failed (HTTP {resp.status_code})"

        step.status = "ok" if step.items_done > 0 else "failed"
        notify(self.progress)

    # ── Data Views ─────────────────────────────────────────────────────

    def _deploy_data_views(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(9)
        step.status = "running"
        notify(self.progress)

        views = [
            # Custom view for exec dashboard panels (broad match, no hyphen)
            {
                "data_view": {
                    "id": "logs*",
                    "title": "logs*",
                    "name": f"{self.scenario.scenario_name} Logs",
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

        created = 0
        for view in views:
            resp = client.post(
                f"{self.kibana_url}/api/data_views/data_view",
                headers=_kibana_headers(self.api_key),
                json=view,
            )
            if resp.status_code < 300:
                created += 1

        step.status = "ok"
        step.detail = f"Created {created} data views"
        notify(self.progress)

    # ── Dashboard ──────────────────────────────────────────────────────

    def _deploy_dashboard(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(10)
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

    # ── Alerting ───────────────────────────────────────────────────────

    def _deploy_alerting(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(11)
        step.status = "running"
        notify(self.progress)

        # Find notification workflow ID
        notification_wf_id = ""
        for name_frag, wf_id in self._workflow_ids.items():
            if "notification" in name_frag or "significant" in name_frag:
                notification_wf_id = wf_id
                break

        if not notification_wf_id:
            # Search for it using the version-resilient helper
            for item in self._list_workflows(client):
                if "Notification" in item.get("name", "") or "Significant" in item.get("name", ""):
                    notification_wf_id = item["id"]
                    break

        if not notification_wf_id:
            step.status = "failed"
            step.detail = "Notification workflow not found"
            notify(self.progress)
            return

        # Clean old rules
        self._cleanup_alerts(client)

        # Create 20 alert rules
        registry = self.scenario.channel_registry
        step.items_total = len(registry)

        for ch_num, ch_data in sorted(registry.items()):
            num_str = f"{int(ch_num):02d}"
            error_type = ch_data["error_type"]
            name = ch_data["name"]
            subsystem = ch_data.get("subsystem", "")

            # Determine severity
            ch_int = int(ch_num)
            if ch_int >= 19:
                severity = "critical"
            elif ch_int <= 6:
                severity = "high"
            else:
                severity = "medium"

            rule_name = f"{self.scenario.scenario_name} CH{num_str}: {name}"

            es_query = json.dumps({
                "query": {
                    "bool": {
                        "filter": [
                            {"range": {"@timestamp": {"gte": "now-1m"}}},
                            {"match_phrase": {"body.text": error_type}},
                            {"term": {"severity_text": "ERROR"}},
                        ]
                    }
                }
            })

            rule = {
                "name": rule_name,
                "rule_type_id": ".es-query",
                "consumer": "alerts",
                "tags": [self.ns, error_type],
                "schedule": {"interval": "1m"},
                "params": {
                    "searchType": "esQuery",
                    "esQuery": es_query,
                    "index": ["logs*"],
                    "timeField": "@timestamp",
                    "threshold": [0],
                    "thresholdComparator": ">",
                    "size": 100,
                    "timeWindowSize": 1,
                    "timeWindowUnit": "m",
                },
                "actions": [{
                    "group": "query matched",
                    "id": "system-connector-.workflows",
                    "frequency": {
                        "summary": False,
                        "notify_when": "onActiveAlert",
                        "throttle": None,
                    },
                    "params": {
                        "subAction": "run",
                        "subActionParams": {
                            "workflowId": notification_wf_id,
                            "inputs": {
                                "channel": ch_int,
                                "error_type": error_type,
                                "subsystem": subsystem,
                                "severity": severity,
                            },
                        },
                    },
                }],
            }

            resp = client.post(
                f"{self.kibana_url}/api/alerting/rule",
                headers=_kibana_headers(self.api_key),
                json=rule,
            )
            if resp.status_code < 300:
                step.items_done += 1
            else:
                logger.warning("Alert rule %s failed: %s", rule_name, resp.text[:200])
            notify(self.progress)

        step.status = "ok" if step.items_done > 0 else "failed"
        step.detail = f"Created {step.items_done}/{step.items_total} alert rules"
        notify(self.progress)

    # ── Cross-scenario cleanup ────────────────────────────────────────

    def _cleanup_all_scenarios_step(self, client: httpx.Client, notify: ProgressCallback):
        """Deploy step: clean up artifacts from ALL known scenarios."""
        step = self._step(2)
        step.status = "running"
        notify(self.progress)

        try:
            deleted = self._cleanup_all_scenarios(client)
            step.status = "ok"
            step.detail = f"Cleaned {deleted} artifacts"
        except Exception as exc:
            step.status = "ok"  # non-fatal — continue deploying
            step.detail = f"Partial cleanup: {exc}"
            logger.warning("Cleanup error (non-fatal): %s", exc)
        notify(self.progress)

    def _cleanup_all_scenarios(self, client: httpx.Client) -> int:
        """Delete artifacts for ALL known scenarios (not just the current one)."""
        from scenarios import get_scenario, list_scenarios

        all_scenarios = list_scenarios()
        deleted = 0

        # Collect all namespaces, scenario names, and agent IDs
        all_namespaces = []
        all_scenario_names = []
        all_agent_ids = []
        for s_meta in all_scenarios:
            try:
                s = get_scenario(s_meta["id"])
                all_namespaces.append(s.namespace)
                all_scenario_names.append(s.scenario_name)
                agent_id = s.agent_config.get("id", f"{s.namespace}-analyst")
                all_agent_ids.append(agent_id)
            except Exception:
                pass

        # Delete alert rules tagged with ANY known namespace
        for ns in all_namespaces:
            try:
                for page in range(1, 11):
                    resp = client.get(
                        f"{self.kibana_url}/api/alerting/rules/_find?per_page=100&page={page}&filter=alert.attributes.tags:{ns}",
                        headers=_kibana_headers(self.api_key),
                    )
                    if resp.status_code >= 300:
                        break
                    rules = resp.json().get("data", [])
                    if not rules:
                        break
                    for rule in rules:
                        rule_id = rule.get("id", "")
                        if rule_id:
                            client.delete(
                                f"{self.kibana_url}/api/alerting/rule/{rule_id}",
                                headers=_kibana_headers(self.api_key),
                            )
                            deleted += 1
            except Exception:
                pass

        # Delete stream queries with ANY known namespace prefix
        try:
            resp = client.get(
                f"{self.kibana_url}/api/streams/logs.otel/queries",
                headers=_kibana_headers(self.api_key),
            )
            if resp.status_code < 300:
                data = resp.json()
                queries = data if isinstance(data, list) else data.get("queries", [])
                for q in queries:
                    qid = q.get("id", "")
                    for ns in all_namespaces:
                        if qid.startswith(f"{ns}-se-"):
                            client.delete(
                                f"{self.kibana_url}/api/streams/logs.otel/queries/{qid}",
                                headers=_kibana_headers(self.api_key),
                            )
                            deleted += 1
                            break
        except Exception:
            pass

        # Delete workflows matching ANY known scenario name
        try:
            for item in self._list_workflows(client):
                wf_name = item.get("name", "")
                for sn in all_scenario_names:
                    if sn in wf_name:
                        wf_id = item.get("id", "")
                        if wf_id:
                            client.delete(
                                f"{self.kibana_url}/api/workflows/{wf_id}",
                                headers=_kibana_headers(self.api_key),
                            )
                            deleted += 1
                        break
        except Exception:
            pass

        # Delete ALL known agent IDs
        for agent_id in all_agent_ids:
            try:
                r = client.delete(
                    f"{self.kibana_url}/api/agent_builder/agents/{agent_id}",
                    headers=_kibana_headers(self.api_key),
                )
                if r.status_code < 300:
                    deleted += 1
            except Exception:
                pass

        # Delete ALL known tool IDs (shared + scenario-specific)
        all_tool_ids = {
            "search_error_logs", "search_subsystem_health", "search_service_logs",
            "search_known_anomalies", "trace_anomaly_propagation",
            "browse_recent_errors", "remediation_action", "escalation_action",
        }
        # Add each scenario's assessment tool ID
        for s_meta in all_scenarios:
            try:
                s = get_scenario(s_meta["id"])
                all_tool_ids.add(s.assessment_tool_config["id"])
            except Exception:
                pass
        for tool_id in all_tool_ids:
            try:
                client.delete(
                    f"{self.kibana_url}/api/agent_builder/tools/{tool_id}",
                    headers=_kibana_headers(self.api_key),
                )
            except Exception:
                pass

        # Delete ALL known dashboards
        for ns in all_namespaces:
            try:
                r = client.post(
                    f"{self.kibana_url}/api/saved_objects/_bulk_delete",
                    headers=_kibana_headers(self.api_key),
                    json=[{"type": "dashboard", "id": f"{ns}-exec-dashboard"}],
                )
                if r.status_code < 300:
                    deleted += 1
            except Exception:
                pass

        # Delete ALL known KB indices and audit indices
        for ns in all_namespaces:
            for suffix in [
                "knowledge-base",
                "significant-events-audit",
                "remediation-audit",
                "escalation-audit",
                "remediation-queue",
                "daily-report-audit",
            ]:
                try:
                    r = client.delete(
                        f"{self.elastic_url}/{ns}-{suffix}",
                        headers=_es_headers(self.api_key),
                    )
                    if r.status_code < 300:
                        deleted += 1
                except Exception:
                    pass

        # Reset OTLP metric data streams so TSDB mappings are recreated fresh.
        # This ensures new metric fields (added to generators after the data stream
        # was first created) are included in the mapping.  The OTLP integration
        # recreates these automatically once generators start sending data.
        for ds_pattern in [
            "metrics-*.otel-*",
        ]:
            try:
                resp = client.get(
                    f"{self.elastic_url}/_data_stream/{ds_pattern}",
                    headers=_es_headers(self.api_key),
                )
                if resp.status_code < 300:
                    streams = resp.json().get("data_streams", [])
                    for ds in streams:
                        ds_name = ds.get("name", "")
                        if ds_name:
                            r = client.delete(
                                f"{self.elastic_url}/_data_stream/{ds_name}",
                                headers=_es_headers(self.api_key),
                            )
                            if r.status_code < 300:
                                deleted += 1
                                logger.info("Deleted data stream %s for mapping refresh", ds_name)
            except Exception as exc:
                logger.warning("Data stream cleanup error (non-fatal): %s", exc)

        logger.info("Cleaned up %d artifacts across all scenarios", deleted)
        return deleted

    @classmethod
    def cleanup_all(cls, elastic_url: str, kibana_url: str, api_key: str) -> dict[str, Any]:
        """Class method: clean up ALL scenario artifacts without needing a specific scenario."""
        from scenarios import get_scenario, list_scenarios

        all_scenarios = list_scenarios()
        if not all_scenarios:
            return {"ok": True, "deleted": 0}

        # Use the first scenario just to get a deployer instance
        first = get_scenario(all_scenarios[0]["id"])
        deployer = cls(first, elastic_url, kibana_url, api_key)

        try:
            with httpx.Client(timeout=60.0, verify=True) as client:
                deleted = deployer._cleanup_all_scenarios(client)
            return {"ok": True, "deleted": deleted}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # ── Cleanup helpers ────────────────────────────────────────────────

    def _cleanup_workflows(self, client: httpx.Client) -> int:
        """Delete workflows matching this scenario's name."""
        deleted = 0
        try:
            scenario_name = self.scenario.scenario_name
            for item in self._list_workflows(client):
                if scenario_name in item.get("name", "") or f"{self.ns}-" in item.get("name", "").lower():
                    wf_id = item.get("id", "")
                    if wf_id:
                        r = client.delete(
                            f"{self.kibana_url}/api/workflows/{wf_id}",
                            headers=_kibana_headers(self.api_key),
                        )
                        if r.status_code < 300:
                            deleted += 1
        except Exception:
            pass
        return deleted

    def _cleanup_alerts(self, client: httpx.Client) -> int:
        """Delete alert rules tagged with this namespace."""
        deleted = 0
        try:
            for page in range(1, 11):
                resp = client.get(
                    f"{self.kibana_url}/api/alerting/rules/_find?per_page=100&page={page}&filter=alert.attributes.tags:{self.ns}",
                    headers=_kibana_headers(self.api_key),
                )
                if resp.status_code >= 300:
                    break
                data = resp.json()
                rules = data.get("data", [])
                if not rules:
                    break
                for rule in rules:
                    rule_id = rule.get("id", "")
                    if rule_id:
                        client.delete(
                            f"{self.kibana_url}/api/alerting/rule/{rule_id}",
                            headers=_kibana_headers(self.api_key),
                        )
                        deleted += 1
        except Exception:
            pass
        return deleted

    def _cleanup_agent(self, client: httpx.Client):
        """Delete agent and custom tools."""
        agent_id = self.scenario.agent_config.get("id", f"{self.ns}-analyst")
        client.delete(
            f"{self.kibana_url}/api/agent_builder/agents/{agent_id}",
            headers=_kibana_headers(self.api_key),
        )
        # Collect tool IDs from scenario's tool_definitions + workflow tools
        tool_ids = [t["id"] for t in self.scenario.tool_definitions]
        tool_ids.extend(["remediation_action", "escalation_action"])
        for tool_id in tool_ids:
            client.delete(
                f"{self.kibana_url}/api/agent_builder/tools/{tool_id}",
                headers=_kibana_headers(self.api_key),
            )

    def _cleanup_significant_events(self, client: httpx.Client):
        """Delete stream queries for this namespace."""
        try:
            resp = client.get(
                f"{self.kibana_url}/api/streams/logs.otel/queries",
                headers=_kibana_headers(self.api_key),
            )
            if resp.status_code < 300:
                data = resp.json()
                queries = data if isinstance(data, list) else data.get("queries", [])
                for q in queries:
                    qid = q.get("id", "")
                    if qid.startswith(f"{self.ns}-se-"):
                        client.delete(
                            f"{self.kibana_url}/api/streams/logs.otel/queries/{qid}",
                            headers=_kibana_headers(self.api_key),
                        )
        except Exception:
            pass

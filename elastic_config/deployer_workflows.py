"""WorkflowsMixin — workflow deploy and cleanup methods."""

from __future__ import annotations

import json
import logging
import os

import httpx

from elastic_config.deployer_base import _kibana_headers, ProgressCallback

logger = logging.getLogger("deployer")


class WorkflowsMixin:

    def _deploy_workflows(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(6)
        step.status = "running"
        notify(self.progress)

        # Clean existing workflows for this namespace
        self._cleanup_workflows(client)

        # Generate templated workflows
        workflow_yamls = self._generate_workflow_yamls()
        step.items_total = len(workflow_yamls)

        for name, yaml_content in workflow_yamls.items():
            resp = self._wf_create(client, yaml_content)
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
        """Generate workflow YAMLs templated for this scenario."""
        ns = self.ns
        scenario_name = self.scenario.scenario_name
        agent_cfg = self.scenario.agent_config
        agent_id = agent_cfg.get("id", f"{ns}-analyst")

        # Read template YAMLs from elastic_config/workflows/ and substitute
        wf_dir = os.path.join(os.path.dirname(__file__), "workflows")

        workflows = {}
        for fname in sorted(os.listdir(wf_dir)):
            if not fname.endswith(".yaml"):
                continue
            with open(os.path.join(wf_dir, fname)) as f:
                yaml_content = f.read()
            # Template substitutions
            yaml_content = yaml_content.replace("__SCENARIO_NAME__", scenario_name)
            yaml_content = yaml_content.replace("__AGENT_ID__", agent_id)
            yaml_content = yaml_content.replace("__NS__", ns)
            yaml_content = yaml_content.replace("__KIBANA_URL__", self.kibana_display_url)
            key = fname.replace(".yaml", "")
            workflows[key] = yaml_content

        return workflows

    def _wf_create(self, client: httpx.Client, yaml_content: str) -> httpx.Response:
        """POST a single workflow. Tries new path first, falls back to old."""
        body = json.dumps({"yaml": yaml_content})
        resp = client.post(
            f"{self.kibana_url}/api/workflows/workflow",
            headers=_kibana_headers(self.api_key),
            content=body,
        )
        if resp.status_code in (404, 405):
            resp = client.post(
                f"{self.kibana_url}/api/workflows",
                headers=_kibana_headers(self.api_key),
                content=body,
            )
        return resp

    def _wf_search(self, client: httpx.Client) -> list:
        """Return all workflow items. Tries new GET path first, falls back to POST search."""
        resp = client.get(
            f"{self.kibana_url}/api/workflows",
            headers=_kibana_headers(self.api_key),
        )
        if resp.status_code in (404, 405):
            resp = client.post(
                f"{self.kibana_url}/api/workflows/search",
                headers=_kibana_headers(self.api_key),
                json={"page": 1, "size": 100},
            )
        if resp.status_code >= 300:
            return []
        data = resp.json()
        return data if isinstance(data, list) else data.get("results", data.get("items", []))

    def _wf_delete(self, client: httpx.Client, wf_id: str) -> httpx.Response:
        """Delete a workflow by ID. Tries new path first, falls back to old."""
        resp = client.delete(
            f"{self.kibana_url}/api/workflows/workflow/{wf_id}",
            headers=_kibana_headers(self.api_key),
        )
        if resp.status_code in (404, 405):
            resp = client.delete(
                f"{self.kibana_url}/api/workflows/{wf_id}",
                headers=_kibana_headers(self.api_key),
            )
        return resp

    def _cleanup_workflows(self, client: httpx.Client) -> int:
        """Delete workflows matching this scenario's name."""
        deleted = 0
        try:
            items = self._wf_search(client)
            scenario_name = self.scenario.scenario_name
            for item in items:
                if scenario_name in item.get("name", "") or f"{self.ns}-" in item.get("name", "").lower():
                    wf_id = item.get("id", "")
                    if wf_id:
                        r = self._wf_delete(client, wf_id)
                        if r.status_code < 300:
                            deleted += 1
        except Exception:
            pass
        return deleted

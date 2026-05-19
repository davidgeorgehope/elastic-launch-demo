"""AgentMixin — tools, agent, and system prompt methods."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from elastic_config.deployer_base import _kibana_headers, ProgressCallback

logger = logging.getLogger("deployer")


class AgentMixin:

    def _deploy_tools(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(8)
        step.status = "running"
        notify(self.progress)

        # Use scenario-provided tool definitions + deployer-added workflow tools
        tools = list(self.scenario.tool_definitions)

        # Add workflow tools (need workflow IDs from deployment)
        for name_frag, wf_id in self._workflow_ids.items():
            if "remediation" in name_frag:
                tools.append({
                    "id": self.scenario.prefixed_tool_id("remediation_action"),
                    "type": "workflow",
                    "description": (
                        "Execute remediation actions for anomalies. Triggers the "
                        "Remediation Action workflow to resolve faults."
                    ),
                    "configuration": {"workflow_id": wf_id},
                })
            elif "escalation" in name_frag:
                tools.append({
                    "id": self.scenario.prefixed_tool_id("escalation_action"),
                    "type": "workflow",
                    "description": (
                        "Escalate critical anomalies and manage operational hold decisions."
                    ),
                    "configuration": {"workflow_id": wf_id},
                })

        skill_defs = self.scenario.skill_definitions
        step.items_total = len(tools) + len(skill_defs)

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

        self._deploy_skills(client, notify)

        step.status = "ok" if step.items_done > 0 else "failed"
        notify(self.progress)

    def _deploy_agent(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(9)
        step.status = "running"
        notify(self.progress)

        agent_cfg = self.scenario.agent_config
        agent_id = agent_cfg.get("id", f"{self.ns}-analyst")

        # Build full system prompt from scenario properties
        system_prompt = self._generate_system_prompt(agent_cfg)

        # Use only tools that were actually created successfully (Bug 4+5 fix)
        tool_ids = list(self._created_tool_ids)
        tool_ids.extend([
            "platform.core.cases",
            "platform.core.resume_workflow_execution",
            "platform.core.get_workflow_execution_status",
            "platform.core.create_visualization",
        ])

        configuration: dict[str, Any] = {
            "instructions": system_prompt,
            "tools": [{"tool_ids": tool_ids}],
        }
        if self._created_skill_ids:
            configuration["skill_ids"] = self._created_skill_ids

        agent_body: dict[str, Any] = {
            "id": agent_id,
            "name": f"{self.scenario.scenario_name}: {agent_cfg.get('name', 'Analyst')}",
            "description": agent_cfg.get(
                "description",
                f"AI-powered analyst for {self.scenario.scenario_name}.",
            ),
            "configuration": configuration,
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

        ns = scenario.namespace
        p_investigation = f"{ns}-investigation-playbook"
        p_channel_runbook = f"{ns}-channel-runbook"
        p_remediation_guide = f"{ns}-remediation-guide"

        return f"""{identity}

## Mission Context
- **Scenario**: {scenario.scenario_name}
- **Namespace**: {scenario.namespace}
- **Kibana URL**: {self.kibana_display_url}
- **Subsystems**: {', '.join(subsystems)}
- **Services**:
{svc_list}
- **Fault Channels**: 20 distinct anomaly channels covering all subsystems
- **Telemetry Source**: OpenTelemetry -> Elasticsearch (logs)

## Skills
- Use **{p_investigation}** for ES|QL investigation, field name guidance, and root cause analysis
- Use **{p_channel_runbook}** to look up fault channel procedures or identify the remediation action_type
- Use **{p_remediation_guide}** before executing any remediation or escalation action
- Use **visualization-creation** to create charts, graphs, or visual breakdowns of data

## Available Services
{svc_names}"""

    def _cleanup_conversations(self, client: httpx.Client) -> int:
        """Delete all Agent Builder conversations belonging to the scenario's agent."""
        agent_id = self.scenario.agent_config.get("id", f"{self.ns}-analyst")
        resp = client.get(
            f"{self.kibana_url}/api/agent_builder/conversations",
            headers=_kibana_headers(self.api_key),
            params={"agent_id": agent_id},
        )
        if resp.status_code >= 300:
            logger.warning("Failed to list conversations: HTTP %s", resp.status_code)
            return 0
        conversations = resp.json().get("results", [])
        deleted = 0
        for conv in conversations:
            r = client.delete(
                f"{self.kibana_url}/api/agent_builder/conversations/{conv['id']}",
                headers=_kibana_headers(self.api_key),
            )
            if r.status_code < 300:
                deleted += 1
            else:
                logger.warning("Failed to delete conversation %s: HTTP %s", conv["id"], r.status_code)
        return deleted

    def _cleanup_agent(self, client: httpx.Client) -> int:
        """Delete agent, custom tools, skills, and conversations. Returns conversation count deleted."""
        agent_id = self.scenario.agent_config.get("id", f"{self.ns}-analyst")
        # Delete conversations before removing the agent
        deleted_convs = self._cleanup_conversations(client)
        # Delete custom skills before removing the agent (avoid 409 Conflict)
        self._cleanup_skills(client)
        client.delete(
            f"{self.kibana_url}/api/agent_builder/agents/{agent_id}",
            headers=_kibana_headers(self.api_key),
        )
        # Collect tool IDs from scenario's tool_definitions + workflow tools
        tool_ids = [t["id"] for t in self.scenario.tool_definitions]
        tool_ids.extend([
            self.scenario.prefixed_tool_id("remediation_action"),
            self.scenario.prefixed_tool_id("escalation_action"),
        ])
        for tool_id in tool_ids:
            client.delete(
                f"{self.kibana_url}/api/agent_builder/tools/{tool_id}",
                headers=_kibana_headers(self.api_key),
            )
        return deleted_convs

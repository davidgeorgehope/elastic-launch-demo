"""Base scenario class and UITheme dataclass — all scenarios implement this interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class UITheme:
    """Visual theme for a scenario's UI pages."""

    # Colors
    bg_primary: str = "#0d1117"  # Main background
    bg_secondary: str = "#161b22"  # Card/panel backgrounds
    bg_tertiary: str = "#21262d"  # Input/accent backgrounds
    accent_primary: str = "#00BFB3"  # Primary accent (buttons, borders)
    accent_secondary: str = "#58a6ff"  # Secondary accent
    text_primary: str = "#e6edf3"  # Main text
    text_secondary: str = "#8b949e"  # Muted text
    text_accent: str = "#00BFB3"  # Highlighted text
    status_nominal: str = "#3fb950"  # Green — healthy
    status_warning: str = "#d29922"  # Amber — degraded
    status_critical: str = "#f85149"  # Red — error
    status_info: str = "#58a6ff"  # Blue — info

    # Typography
    font_family: str = "'Inter', 'Segoe UI', system-ui, sans-serif"
    font_mono: str = "'JetBrains Mono', 'Fira Code', monospace"
    font_size_base: str = "14px"

    # Effects
    scanline_effect: bool = False  # CRT scanline overlay (Space theme)
    glow_effect: bool = False  # Neon glow on accents (Gaming theme)
    grid_background: bool = False  # Subtle grid pattern (Fanatics theme)
    gradient_accent: str = ""  # CSS gradient for accent areas

    # Terminology
    chaos_title: str = "Incident Simulator"
    service_label: str = "Service"  # "Service", "System", "Module"
    channel_label: str = "Channel"  # "Channel", "Scenario", "Incident"

    # CSS custom properties dict (for injection into templates)
    def to_css_vars(self) -> str:
        """Generate CSS custom property declarations."""
        return "\n".join(
            [
                f"  --bg-primary: {self.bg_primary};",
                f"  --bg-secondary: {self.bg_secondary};",
                f"  --bg-tertiary: {self.bg_tertiary};",
                f"  --accent-primary: {self.accent_primary};",
                f"  --accent-secondary: {self.accent_secondary};",
                f"  --text-primary: {self.text_primary};",
                f"  --text-secondary: {self.text_secondary};",
                f"  --text-accent: {self.text_accent};",
                f"  --status-nominal: {self.status_nominal};",
                f"  --status-warning: {self.status_warning};",
                f"  --status-critical: {self.status_critical};",
                f"  --status-info: {self.status_info};",
                f"  --font-family: {self.font_family};",
                f"  --font-mono: {self.font_mono};",
                f"  --font-size-base: {self.font_size_base};",
            ]
        )


@dataclass
class CountdownConfig:
    """Optional countdown timer configuration."""

    enabled: bool = False
    start_seconds: int = 600
    speed: float = 1.0
    phases: dict[str, tuple[int, int]] = field(default_factory=dict)
    # phases maps phase_name -> (min_remaining, max_remaining)
    # e.g. {"PRE-LAUNCH": (300, 9999), "COUNTDOWN": (60, 300), ...}


class BaseScenario(ABC):
    """Abstract base class that all scenarios must implement."""

    # ── Identity ──────────────────────────────────────────────────────

    @property
    @abstractmethod
    def scenario_id(self) -> str:
        """Unique key: 'space', 'fanatics', 'financial', etc."""
        ...

    @property
    @abstractmethod
    def scenario_name(self) -> str:
        """Display name: 'NOVA-7 Space Mission'."""
        ...

    @property
    @abstractmethod
    def scenario_description(self) -> str:
        """Card description for the scenario selector."""
        ...

    @property
    @abstractmethod
    def namespace(self) -> str:
        """ES/telemetry namespace prefix: 'nova7', 'fanatics', etc."""
        ...

    @property
    def scenario_icon(self) -> str:
        """Emoji icon displayed on the scenario selector card."""
        return "🔧"

    @property
    def sort_order(self) -> int:
        """Display order on the scenario selector. Lower numbers appear first. Default 999."""
        return 999

    @property
    def executive_kpi_emitter_service_name(self) -> str | None:
        """`SERVICE_NAME` of the one microservice that emits synthetic `business.*` executive KPI gauges.

        Used by the Kibana Executive dashboard (Lens). Override in each scenario.
        """
        return None

    @property
    def executive_dashboard_intro(self) -> str:
        """Markdown intro shown at the top of the Executive Dashboard. Override in each scenario."""
        svc = self.executive_kpi_emitter_service_name or "executive-service"
        return (
            f"**Executive view** — cross-functional KPIs for {self.scenario_name} "
            f"(synthetic `business.*` from `{svc}`)."
        )

    @property
    def executive_kpi_sections(self) -> list[dict]:
        """KPI tile sections for the Executive Dashboard.

        Each dict: {"header": str, "specs": [(display_title, metrics_field), ...]}
        Override in each scenario with industry-appropriate metrics.
        """
        return []

    @property
    def executive_trend_charts(self) -> list[dict]:
        """Trend line charts for the Executive Dashboard (6, arranged 3×2).

        Each dict: {"title": str, "field": str, "y_label": str}
        Override in each scenario with the most important metrics to trend.
        """
        return []

    # ── Services & Topology ──────────────────────────────────────────

    @property
    @abstractmethod
    def services(self) -> dict[str, dict[str, Any]]:
        """9 service definitions with cloud/region/subsystem/language."""
        ...

    @property
    @abstractmethod
    def channel_registry(self) -> dict[int, dict[str, Any]]:
        """20 fault channels with error types, messages, stack traces."""
        ...

    @property
    @abstractmethod
    def service_topology(self) -> dict[str, list[tuple[str, str, str]]]:
        """Trace call graph: caller -> [(callee, endpoint, method)]."""
        ...

    @property
    @abstractmethod
    def entry_endpoints(self) -> dict[str, list[tuple[str, str]]]:
        """API endpoints per service: service -> [(path, method)]."""
        ...

    @property
    @abstractmethod
    def db_operations(self) -> dict[str, list[tuple[str, str, str]]]:
        """DB operations: service -> [(op, table, statement)]."""
        ...

    # ── Infrastructure ───────────────────────────────────────────────

    @property
    @abstractmethod
    def hosts(self) -> list[dict[str, Any]]:
        """3 host definitions (one per cloud)."""
        ...

    @property
    @abstractmethod
    def k8s_clusters(self) -> list[dict[str, Any]]:
        """3 K8s cluster definitions."""
        ...

    # ── UI & Theme ───────────────────────────────────────────────────

    @property
    @abstractmethod
    def theme(self) -> UITheme:
        """Visual theme configuration."""
        ...

    @property
    def countdown_config(self) -> CountdownConfig:
        """Optional countdown timer. Override if scenario has one."""
        return CountdownConfig(enabled=False)

    @property
    def nominal_label(self) -> str:
        """Status label for 'all clear'. Override for domain jargon (e.g. space uses 'NOMINAL')."""
        return "NORMAL"

    # ── Agent & Elastic Config ───────────────────────────────────────

    @property
    @abstractmethod
    def agent_config(self) -> dict[str, Any]:
        """Agent ID, name, system prompt, and assessment_tool_name for Agent Builder.

        Required keys:
          - id: agent ID (e.g. "finserv-trading-analyst")
          - name: display name (e.g. "Trading Operations Analyst")
          - system_prompt: identity + domain expertise text
          - assessment_tool_name: scenario-specific assessment tool name
            (e.g. "launch_safety_assessment", "trading_risk_assessment")
        """
        ...

    @property
    @abstractmethod
    def assessment_tool_config(self) -> dict[str, Any]:
        """Scenario-specific assessment tool definition.

        Returns a dict with keys: id, description.
        Example for space: {"id": "launch_safety_assessment",
                            "description": "GO/NO-GO launch readiness evaluation..."}
        """
        ...

    def prefixed_tool_id(self, base_id: str) -> str:
        """Stable per-scenario tool id so multiple scenarios can coexist in Agent Builder."""
        p = f"{self.namespace}_"
        if base_id.startswith(p):
            return base_id
        return f"{p}{base_id}"

    @property
    def tool_definitions(self) -> list[dict[str, Any]]:
        """Agent Builder tool configurations — auto-generated from scenario properties.

        Override in a subclass for fully custom tools.  By default generates
        6 generic tools + the scenario-specific assessment tool.
        """
        return self._default_tool_definitions()

    @property
    @abstractmethod
    def knowledge_base_docs(self) -> list[dict[str, Any]]:
        """20 KB documents for agent knowledge base."""
        ...

    # ── Service Classes ──────────────────────────────────────────────

    @abstractmethod
    def get_service_classes(self) -> list[type]:
        """Return list of 9 service implementation classes."""
        ...

    # ── Fault Parameters ─────────────────────────────────────────────

    def get_trace_attributes(self, service_name: str, rng) -> dict:
        """Domain-specific attributes on ALL traces (always present)."""
        return {}

    def get_rca_clues(self, channel: int, service_name: str, rng) -> dict:
        """Partial RCA clues on traces for services in active fault channels.
        Different services get different clues — no single service has full picture."""
        return {}

    def get_correlation_attribute(self, channel: int, is_error: bool, rng) -> dict:
        """Attribute correlated with errors: appears on ~90% of error traces,
        ~5% of healthy traces. Discoverable via Elastic correlation analysis."""
        return {}

    @abstractmethod
    def get_fault_params(self, channel: int) -> dict[str, Any]:
        """Generate realistic random fault parameters for a channel."""
        ...

    # ── Convenience ──────────────────────────────────────────────────

    @property
    def cloud_groups(self) -> dict[str, list[str]]:
        """Group services by cloud provider."""
        groups: dict[str, list[str]] = {}
        for svc_name, svc_cfg in self.services.items():
            provider = svc_cfg["cloud_provider"]
            groups.setdefault(provider, []).append(svc_name)
        return groups

    @property
    def subsystem_groups(self) -> dict[str, list[str]]:
        """Group services by subsystem."""
        groups: dict[str, list[str]] = {}
        for svc_name, svc_cfg in self.services.items():
            sub = svc_cfg["subsystem"]
            groups.setdefault(sub, []).append(svc_name)
        return groups

    @property
    def dashboard_cloud_groups(self) -> list[dict[str, Any]]:
        """Cloud groups for exec dashboard layout (AWS/GCP/Azure columns)."""
        cloud_order = ["aws", "gcp", "azure"]
        x_starts = [0, 16, 33]
        col_widths = [15, 16, 15]
        groups = []
        for i, provider in enumerate(cloud_order):
            svcs = self.cloud_groups.get(provider, [])
            cluster = next(
                (c for c in self.k8s_clusters if c["provider"] == provider), {}
            )
            groups.append(
                {
                    "label": f"**{provider.upper()}** {cluster.get('region', '')}",
                    "services": svcs,
                    "x_start": x_starts[i],
                    "col_width": col_widths[i],
                    "cluster": cluster.get("name", ""),
                }
            )
        return groups

    @property
    def raw_log_profile(self) -> dict[str, Any]:
        """Profile for the raw ECS access-log generator.

        Drives a per-scenario unparsed `logs.ecs.{ns}` stream so SAs can demo
        Streams partition/parsing on the fly and use the visualization-creation
        skill to build dashboards from domain-relatable raw data.

        Override per scenario for industry-appropriate paths, user-id prefix,
        tier field, and the change-point path that spikes during simulated faults.
        """
        return {
            "service_name": f"{self.namespace}-edge-gateway",
            "user_id_prefix": "u",
            "tier_field": "user_tier",
            "tier_values": [("free", 75), ("pro", 20), ("enterprise", 5)],
            "country_weights": {"US": 35, "GB": 12, "DE": 12, "FR": 8, "JP": 8, "IN": 10, "BR": 8, "CA": 7},
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "paths": ["/api/v1/health"],
            "change_point_path": "/api/v1/health",
        }

    @property
    def infra_names(self) -> dict[str, Any]:
        """Standard infrastructure names derived from namespace."""
        ns = self.namespace
        return {
            "nginx_hosts": [f"{ns}-nginx-01", f"{ns}-nginx-02"],
            "nginx_servers": [f"{ns}-proxy-01", f"{ns}-proxy-02"],
            "proxy_host": f"{ns}-proxy-host",
            "mysql_host": f"{ns}-mysql-host",
            "vpc_scope": f"{ns}-vpc-flow-generator",
            "vpc_names": [f"{ns}-vpc-prod", f"{ns}-vpc-staging", f"{ns}-vpc-data"],
            "gcp_account": f"{ns}-project-prod",
            "daemonsets": [f"{ns}-log-collector", f"{ns}-node-exporter"],
            "statefulsets": [f"{ns}-redis", f"{ns}-postgres"],
            "url_domain": f"{ns}.internal",
            "db_prefix": ns.replace("-", "_"),
        }

    # ── Default Tool Generation ──────────────────────────────────────

    def _default_tool_definitions(self) -> list[dict[str, Any]]:
        """Generate the standard 7 agent tools from scenario properties."""
        svc_names = ", ".join(sorted(self.services.keys()))
        kb_index = f"{self.namespace}-knowledge-base"

        registry_values = list(self.channel_registry.values())
        example_error = (
            registry_values[0]["error_type"] if registry_values else "SomeException"
        )

        tools = [
            {
                "id": self.prefixed_tool_id("search_error_logs"),
                "type": "esql",
                "description": (
                    f"Search telemetry logs for a specific error or exception type. "
                    f"Returns the 50 most recent ERROR-level log entries matching the "
                    f"error type. Services: {svc_names}. "
                    f"The error_type parameter is matched against body.text."
                ),
                "configuration": {
                    "query": (
                        f"FROM logs.otel.{self.namespace},logs.otel.{self.namespace}.* "
                        "| WHERE @timestamp > NOW() - 15 MINUTES "
                        'AND body.text LIKE ?error_type AND severity_text == "ERROR" '
                        "| KEEP @timestamp, body.text, service.name, severity_text, event_name "
                        "| SORT @timestamp DESC | LIMIT 50"
                    ),
                    "params": {
                        "error_type": {
                            "description": f"Wildcard pattern for the error type, e.g. *{example_error}*",
                            "type": "string",
                            "optional": False,
                        }
                    },
                },
            },
            {
                "id": self.prefixed_tool_id("search_subsystem_health"),
                "type": "esql",
                "description": (
                    f"Query health status by aggregating recent telemetry. "
                    f"Returns error/warning counts per service. "
                    f"Services: {svc_names}. "
                    f"Log message field: body.text (never use 'body' alone)."
                ),
                "configuration": {
                    "query": (
                        f"FROM logs.otel.{self.namespace},logs.otel.{self.namespace}.* "
                        "| WHERE @timestamp > NOW() - 15 MINUTES "
                        '| STATS error_count = COUNT(*) WHERE severity_text == "ERROR", '
                        'warn_count = COUNT(*) WHERE severity_text == "WARN", '
                        "total = COUNT(*) BY service.name "
                        "| SORT error_count DESC"
                    ),
                    "params": {},
                },
            },
            {
                "id": self.prefixed_tool_id("search_service_logs"),
                "type": "esql",
                "description": (
                    f"Search telemetry logs for a specific service. "
                    f"Returns the 50 most recent ERROR and WARN entries. "
                    f"Available services: {svc_names}."
                ),
                "configuration": {
                    "query": (
                        f"FROM logs.otel.{self.namespace},logs.otel.{self.namespace}.* "
                        "| WHERE @timestamp > NOW() - 15 MINUTES "
                        "AND service.name == ?service_name "
                        'AND severity_text IN ("ERROR", "WARN") '
                        "| KEEP @timestamp, body.text, service.name, severity_text "
                        "| SORT @timestamp DESC | LIMIT 50"
                    ),
                    "params": {
                        "service_name": {
                            "description": f"The service to investigate ({svc_names})",
                            "type": "string",
                            "optional": False,
                        }
                    },
                },
            },
            {
                "id": self.prefixed_tool_id("search_known_anomalies"),
                "type": "index_search",
                "description": (
                    f"Search the knowledge base for documented anomalies, failure "
                    f"patterns, and resolution procedures. Contains RCA guides for "
                    f"all 20 fault channels."
                ),
                "configuration": {
                    "pattern": kb_index,
                },
            },
            {
                "id": self.prefixed_tool_id("trace_anomaly_propagation"),
                "type": "esql",
                "description": (
                    "Trace the propagation path of anomalies across services. "
                    "Shows which services have errors and warnings over time to "
                    "identify cascade chains. "
                    "Log message field: body.text (never use 'body' alone)."
                ),
                "configuration": {
                    "query": (
                        f"FROM logs.otel.{self.namespace},logs.otel.{self.namespace}.* "
                        "| WHERE @timestamp > NOW() - 15 MINUTES "
                        'AND severity_text IN ("ERROR", "WARN") '
                        '| STATS error_count = COUNT(*) WHERE severity_text == "ERROR", '
                        'warn_count = COUNT(*) WHERE severity_text == "WARN" '
                        "BY service.name | SORT error_count DESC"
                    ),
                    "params": {},
                },
            },
            {
                "id": self.prefixed_tool_id("browse_recent_errors"),
                "type": "esql",
                "description": (
                    "Browse all recent ERROR and WARN log entries across all services. "
                    "Use for general situation awareness when you do not yet know the "
                    "specific error type or service."
                ),
                "configuration": {
                    "query": (
                        f"FROM logs.otel.{self.namespace},logs.otel.{self.namespace}.* "
                        "| WHERE @timestamp > NOW() - 15 MINUTES "
                        'AND severity_text IN ("ERROR", "WARN") '
                        "| KEEP @timestamp, body.text, service.name, severity_text "
                        "| SORT @timestamp DESC | LIMIT 50"
                    ),
                    "params": {},
                },
            },
        ]

        # Add scenario-specific assessment tool
        assessment = self.assessment_tool_config
        tools.append(
            {
                "id": self.prefixed_tool_id(assessment["id"]),
                "type": "esql",
                "description": assessment["description"],
                "configuration": {
                    "query": (
                        f"FROM logs.otel.{self.namespace},logs.otel.{self.namespace}.* "
                        "| WHERE @timestamp > NOW() - 15 MINUTES "
                        'AND severity_text IN ("ERROR", "WARN") '
                        '| STATS error_count = COUNT(*) WHERE severity_text == "ERROR", '
                        'warn_count = COUNT(*) WHERE severity_text == "WARN" '
                        "BY service.name | SORT error_count DESC"
                    ),
                    "params": {},
                },
            }
        )

        return tools

    # ── Skill Definitions ────────────────────────────────────────────

    @property
    def builtin_skill_names(self) -> list[str]:
        """Names/IDs of built-in Agent Builder skills to discover and attach."""
        return [
            "visualization-creation",
            "observability.investigation",
            "observability.rca",
        ]

    @property
    def skill_definitions(self) -> list[dict[str, Any]]:
        """Custom skill definitions deployed alongside agent tools."""
        ns = self.namespace
        agent_cfg = self.agent_config
        assessment_tool = self.prefixed_tool_id(agent_cfg.get(
            "assessment_tool_name",
            self.assessment_tool_config.get("id", "operational_assessment"),
        ))
        p_search_error       = self.prefixed_tool_id("search_error_logs")
        p_search_service     = self.prefixed_tool_id("search_service_logs")
        p_browse_recent      = self.prefixed_tool_id("browse_recent_errors")
        p_subsystem_health   = self.prefixed_tool_id("search_subsystem_health")
        p_search_known       = self.prefixed_tool_id("search_known_anomalies")
        p_trace_anomaly      = self.prefixed_tool_id("trace_anomaly_propagation")
        p_remediation_action = self.prefixed_tool_id("remediation_action")
        p_escalation_action  = self.prefixed_tool_id("escalation_action")

        return [
            self._investigation_playbook_skill(
                ns, p_search_error, p_search_service, p_browse_recent,
                p_subsystem_health, p_search_known, p_trace_anomaly, assessment_tool,
            ),
            self._channel_runbook_skill(ns, p_search_known),
            self._remediation_guide_skill(ns, p_remediation_action, p_escalation_action),
        ]

    def _investigation_playbook_skill(
        self,
        ns: str,
        p_search_error: str,
        p_search_service: str,
        p_browse_recent: str,
        p_subsystem_health: str,
        p_search_known: str,
        p_trace_anomaly: str,
        assessment_tool: str,
    ) -> dict[str, Any]:
        # Skill tool_ids capped at 5 per API limit; pick the 5 most-used investigation tools.
        # p_subsystem_health and assessment_tool remain accessible via the agent's tool list.
        tool_ids = [
            p_search_error, p_search_service, p_browse_recent,
            p_search_known, p_trace_anomaly,
        ]
        description = (
            f"Investigate anomalies, errors, and faults in the {self.scenario_name} "
            f"environment. Use this skill to look up error patterns, trace cascade failures "
            f"across services, and perform structured root cause analysis using the correct "
            f"ES|QL field names and parameterized investigation tools."
        )
        content = f"""## CRITICAL: Field Names

- Log message field is `body.text` — NEVER use `body` alone (causes "Unknown column [body]")
- NEVER use `message` — this field does not exist; the correct field is `body.text`
- Service name field is `service.name`
- Always query `FROM logs.otel.{ns},logs.otel.{ns}.*` (includes sub-streams)
- Use `LIKE` or `KQL()` for text matching — NEVER use `MATCH()`

## Tool Selection Guide

1. **Known error type** → `{p_search_error}` — parameterized, returns matching ERROR logs
2. **Specific service** → `{p_search_service}` — parameterized by service name
3. **General awareness** → `{p_browse_recent}` or `{p_subsystem_health}`
4. **Historical patterns** → `{p_search_known}` — knowledge base lookup
5. **Cascade analysis** → `{p_trace_anomaly}` — cross-service propagation
6. **Operational readiness** → `{assessment_tool}` — overall system health

Do NOT write custom ES|QL queries. Use the parameterized tools.

## Root Cause Analysis Methodology

1. **Identify the Event**: Determine which channel(s) triggered and the error signature
2. **Scope the Blast Radius**: Identify affected and cascade services
3. **Temporal Correlation**: Find first occurrence, correlate with preceding events
4. **Cross-Cloud Tracing**: Trace propagation across AWS, GCP, and Azure
5. **Subsystem Impact**: Evaluate if fault is isolated or propagating
6. **Known Pattern Matching**: Check knowledge base for similar anomalies
7. **Severity Classification**: ADVISORY, CAUTION, WARNING, or CRITICAL

## Response Format

1. **Summary** — One-sentence description
2. **Affected Systems** — Impacted services and subsystems
3. **Root Cause** — Underlying cause determination
4. **Evidence** — Specific log entries, timestamps, field values
5. **Cascade Risk** — Propagation assessment
6. **Recommendation** — Prioritized remediation steps
7. **Confidence** — HIGH/MEDIUM/LOW with reasoning
"""
        return {
            "id": f"{ns}-investigation-playbook",
            "name": f"{self.scenario_name} Investigation Playbook",
            "description": description,
            "content": content,
            "tool_ids": tool_ids,
        }

    def _channel_runbook_skill(self, ns: str, p_search_known: str) -> dict[str, Any]:
        registry = self.channel_registry
        description = (
            f"Look up investigation procedures and remediation actions for "
            f"{self.scenario_name} fault channels. Use when you need the documented "
            f"procedure for a specific error type or to identify the correct "
            f"remediation action_type for a channel."
        )
        # Build channel summary table
        rows = []
        for ch_num, ch in sorted(registry.items()):
            rows.append(
                f"| {ch_num} | {ch['name']} | `{ch['error_type']}` "
                f"| {ch.get('remediation_action', 'N/A')} |"
            )
        table = "\n".join(rows)

        # Build per-channel runbook sections inline (avoids referenced_content format issues)
        channel_sections = []
        for ch_num, ch in sorted(registry.items()):
            ch_name = ch["name"]
            error_type = ch["error_type"]
            subsystem = ch.get("subsystem", "unknown")
            affected = ", ".join(ch.get("affected_services", []))
            cascade = ", ".join(ch.get("cascade_services", []))
            description_text = ch.get("description", "")
            remediation_action = ch.get("remediation_action", "remediate")
            investigation_notes = ch.get("investigation_notes", "")
            investigation_section = (
                f"\n**Vendor Investigation:** {investigation_notes}\n"
                if investigation_notes else ""
            )
            channel_sections.append(
                f"### Channel {ch_num}: {ch_name}\n"
                f"- **Error Type**: `{error_type}` — subsystem: {subsystem}\n"
                f"- **Affected**: {affected} | **Cascade**: {cascade}\n"
                f"- **Description**: {description_text}\n"
                f"- **Remediation action_type**: `{remediation_action}` (channel: {ch_num})\n"
                f"{investigation_section}"
            )
        channels_content = "\n".join(channel_sections)

        content = f"""# {self.scenario_name} Fault Channel Reference

Use `{p_search_known}` for dynamic keyword searches across the knowledge base.
The error type appears in `body.text` log entries — search with `LIKE *ERROR_TYPE*`.
The `remediation_action` value below is the `action_type` to pass to the remediation tool.

## Channel Summary

| # | Name | Error Type | Remediation |
|---|------|-----------|-------------|
{table}

## Channel Runbooks

{channels_content}
"""
        return {
            "id": f"{ns}-channel-runbook",
            "name": f"{self.scenario_name} Channel Runbook",
            "description": description,
            "content": content,
            "tool_ids": [p_search_known],
        }

    def _remediation_guide_skill(
        self,
        ns: str,
        p_remediation_action: str,
        p_escalation_action: str,
    ) -> dict[str, Any]:
        description = (
            f"Remediate confirmed anomalies, escalate critical incidents, or manage "
            f"operational holds for {self.scenario_name}. Use after root cause analysis "
            f"to execute remediation, request holds, or escalate. Includes correct "
            f"parameters for remediation and escalation workflow tools."
        )
        content = f"""## Remediation Decision Framework

### When to Remediate
Execute remediation when:
- Root cause is identified and confirmed
- The `action_type` is known (from the channel runbook)
- The user explicitly requests it

### When to Escalate
Use escalation when:
- Severity is CRITICAL and multiple subsystems are affected
- Automated remediation may trigger cascade effects
- A hold decision is needed before proceeding

## How to Remediate

Use `{p_remediation_action}` with these parameters:
- `action_type` — from the channel runbook (e.g. `recalibrate_engine`, `reset_fuel_system`)
- `channel` — the fault channel number (1–20)
- `error_type` — the error type identifier
- `justification` — brief explanation
- `dry_run` — `false` for actual remediation
- `case_id` — **ALWAYS** pass this if you retrieved a case ID earlier in the conversation; never rely on tag-based search to find the case

Once `{p_remediation_action}` returns successfully, report remediation as complete.
Do NOT re-query logs to verify — the fix takes several minutes to propagate through the system.
Do NOT execute remediation unless the user explicitly asks.

## How to Escalate

Use `{p_escalation_action}` with:
- `action` — `"escalate"`, `"request_hold"`, `"resolve"`, or `"request_resume"`
- `channel` — the fault channel number
- `severity` — `"advisory"`, `"caution"`, `"warning"`, or `"critical"`
- `justification` — investigation summary

## HITL Channels (1–15)

State your remediation recommendation and wait for explicit user approval before acting.
Do NOT execute remediation based on the RCA alone.

## Auto-Remediate Channels (16–20)

These channels may be remediated without explicit user approval when the workflow requests it.
"""
        return {
            "id": f"{ns}-remediation-guide",
            "name": f"{self.scenario_name} Remediation Guide",
            "description": description,
            "content": content,
            "tool_ids": [p_remediation_action, p_escalation_action, "platform.core.cases"],
        }

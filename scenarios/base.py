"""Base scenario class and UITheme dataclass — all scenarios implement this interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class UITheme:
    """Visual theme for a scenario's UI pages."""

    # Colors
    bg_primary: str = "#0d1117"         # Main background
    bg_secondary: str = "#161b22"       # Card/panel backgrounds
    bg_tertiary: str = "#21262d"        # Input/accent backgrounds
    accent_primary: str = "#00BFB3"     # Primary accent (buttons, borders)
    accent_secondary: str = "#58a6ff"   # Secondary accent
    text_primary: str = "#e6edf3"       # Main text
    text_secondary: str = "#8b949e"     # Muted text
    text_accent: str = "#00BFB3"        # Highlighted text
    status_nominal: str = "#3fb950"     # Green — healthy
    status_warning: str = "#d29922"     # Amber — degraded
    status_critical: str = "#f85149"    # Red — error
    status_info: str = "#58a6ff"        # Blue — info

    # Typography
    font_family: str = "'Inter', 'Segoe UI', system-ui, sans-serif"
    font_mono: str = "'JetBrains Mono', 'Fira Code', monospace"
    font_size_base: str = "14px"

    # Effects
    scanline_effect: bool = False       # CRT scanline overlay (Space theme)
    glow_effect: bool = False           # Neon glow on accents (Gaming theme)
    grid_background: bool = False       # Subtle grid pattern (Fanatics theme)
    gradient_accent: str = ""           # CSS gradient for accent areas

    # Terminology
    dashboard_title: str = "Operations Dashboard"
    chaos_title: str = "Incident Simulator"
    landing_title: str = "Control Center"
    service_label: str = "Service"      # "Service", "System", "Module"
    channel_label: str = "Channel"      # "Channel", "Scenario", "Incident"

    # CSS custom properties dict (for injection into templates)
    def to_css_vars(self) -> str:
        """Generate CSS custom property declarations."""
        return "\n".join([
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
        ])


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
            groups.append({
                "label": f"**{provider.upper()}** {cluster.get('region', '')}",
                "services": svcs,
                "x_start": x_starts[i],
                "col_width": col_widths[i],
                "cluster": cluster.get("name", ""),
            })
        return groups

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
        example_error = registry_values[0]["error_type"] if registry_values else "SomeException"

        tools = [
            {
                "id": "search_error_logs",
                "type": "esql",
                "description": (
                    f"Search telemetry logs for a specific error or exception type. "
                    f"Returns the 50 most recent ERROR-level log entries matching the "
                    f"error type. Services: {svc_names}. "
                    f"The error_type parameter is matched against body.text."
                ),
                "configuration": {
                    "query": (
                        'FROM logs.otel,logs.otel.* '
                        '| WHERE @timestamp > NOW() - 15 MINUTES '
                        'AND body.text LIKE ?error_type AND severity_text == "ERROR" '
                        '| KEEP @timestamp, body.text, service.name, severity_text, event_name '
                        '| SORT @timestamp DESC | LIMIT 50'
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
                "id": "search_subsystem_health",
                "type": "esql",
                "description": (
                    f"Query health status by aggregating recent telemetry. "
                    f"Returns error/warning counts per service. "
                    f"Services: {svc_names}. "
                    f"Log message field: body.text (never use 'body' alone)."
                ),
                "configuration": {
                    "query": (
                        'FROM logs.otel,logs.otel.* '
                        '| WHERE @timestamp > NOW() - 15 MINUTES '
                        '| STATS error_count = COUNT(*) WHERE severity_text == "ERROR", '
                        'warn_count = COUNT(*) WHERE severity_text == "WARN", '
                        'total = COUNT(*) BY service.name '
                        '| SORT error_count DESC'
                    ),
                    "params": {},
                },
            },
            {
                "id": "search_service_logs",
                "type": "esql",
                "description": (
                    f"Search telemetry logs for a specific service. "
                    f"Returns the 50 most recent ERROR and WARN entries. "
                    f"Available services: {svc_names}."
                ),
                "configuration": {
                    "query": (
                        'FROM logs.otel,logs.otel.* '
                        '| WHERE @timestamp > NOW() - 15 MINUTES '
                        'AND service.name == ?service_name '
                        'AND severity_text IN ("ERROR", "WARN") '
                        '| KEEP @timestamp, body.text, service.name, severity_text '
                        '| SORT @timestamp DESC | LIMIT 50'
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
                "id": "search_known_anomalies",
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
                "id": "trace_anomaly_propagation",
                "type": "esql",
                "description": (
                    "Trace the propagation path of anomalies across services. "
                    "Shows which services have errors and warnings over time to "
                    "identify cascade chains. "
                    "Log message field: body.text (never use 'body' alone)."
                ),
                "configuration": {
                    "query": (
                        'FROM logs.otel,logs.otel.* '
                        '| WHERE @timestamp > NOW() - 15 MINUTES '
                        'AND severity_text IN ("ERROR", "WARN") '
                        '| STATS error_count = COUNT(*) WHERE severity_text == "ERROR", '
                        'warn_count = COUNT(*) WHERE severity_text == "WARN" '
                        'BY service.name | SORT error_count DESC'
                    ),
                    "params": {},
                },
            },
            {
                "id": "browse_recent_errors",
                "type": "esql",
                "description": (
                    "Browse all recent ERROR and WARN log entries across all services. "
                    "Use for general situation awareness when you do not yet know the "
                    "specific error type or service."
                ),
                "configuration": {
                    "query": (
                        'FROM logs.otel,logs.otel.* '
                        '| WHERE @timestamp > NOW() - 15 MINUTES '
                        'AND severity_text IN ("ERROR", "WARN") '
                        '| KEEP @timestamp, body.text, service.name, severity_text '
                        '| SORT @timestamp DESC | LIMIT 50'
                    ),
                    "params": {},
                },
            },
        ]

        # Add scenario-specific assessment tool
        assessment = self.assessment_tool_config
        tools.append({
            "id": assessment["id"],
            "type": "esql",
            "description": assessment["description"],
            "configuration": {
                "query": (
                    'FROM logs.otel,logs.otel.* '
                    '| WHERE @timestamp > NOW() - 15 MINUTES '
                    'AND severity_text IN ("ERROR", "WARN") '
                    '| STATS error_count = COUNT(*) WHERE severity_text == "ERROR", '
                    'warn_count = COUNT(*) WHERE severity_text == "WARN" '
                    'BY service.name | SORT error_count DESC'
                ),
                "params": {},
            },
        })

        return tools

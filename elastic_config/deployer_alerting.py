"""AlertingMixin — alerting deploy and cleanup methods."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import httpx

from elastic_config.deployer_base import _kibana_headers, _retry_http, ProgressCallback

if TYPE_CHECKING:
    from scenarios.base import BaseScenario

logger = logging.getLogger("deployer")


class AlertingMixin:
    # Attributes supplied by ScenarioDeployer at runtime — declared here for type checkers.
    if TYPE_CHECKING:
        kibana_url: str
        api_key: str
        ns: str
        scenario: BaseScenario
        _workflow_ids: dict[str, str]

    def _deploy_alerting(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(14)
        step.status = "running"
        notify(self.progress)

        # Find HITL notification workflow ID
        notification_wf_id = self._workflow_ids.get("significant_event_notification", "")
        auto_remediate_wf_id = self._workflow_ids.get("significant_event_notification_auto_remediate", "")

        if not notification_wf_id or not auto_remediate_wf_id:
            # Search for missing IDs
            try:
                items = self._wf_search(client)
                for item in items:
                    wf_name = item.get("name", "")
                    wf_id = item.get("id", "")
                    if not wf_id:
                        continue
                    if not notification_wf_id and "Auto-Remediate" not in wf_name and (
                        "Notification" in wf_name or "Significant" in wf_name
                    ):
                        notification_wf_id = wf_id
                    elif not auto_remediate_wf_id and "Auto-Remediate" in wf_name and (
                        "Notification" in wf_name or "Significant" in wf_name
                    ):
                        auto_remediate_wf_id = wf_id
            except Exception:
                pass

        if not notification_wf_id:
            step.status = "failed"
            step.detail = "Notification workflow not found"
            notify(self.progress)
            return

        if not auto_remediate_wf_id:
            logger.warning("Auto-remediate workflow not found; channels 16-20 will use HITL workflow")

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

            # Channels 16-20 use auto-remediation; 1-15 remain HITL
            auto_remediate = ch_int >= 16
            if auto_remediate:
                rule_name = f"{self.scenario.scenario_name} CH{num_str}: {name} (Auto-Remediate)"
            else:
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
                # Tag encoding (workflow inputs from alert actions resolve blank,
                # so all per-channel data the workflow needs must live in tags):
                #   tags[0] = namespace
                #   tags[1] = error_type
                #   tags[2] = remediation_action (HITL pauses for approval; auto-remediate skips)
                #   tags[3] = channel number
                "tags": [self.ns, error_type, ch_data.get("remediation_action", ""), str(ch_int)],
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
                            "workflowId": (auto_remediate_wf_id or notification_wf_id) if auto_remediate else notification_wf_id,
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

            resp = _retry_http(
                lambda r=rule: client.post(
                    f"{self.kibana_url}/api/alerting/rule",
                    headers=_kibana_headers(self.api_key),
                    json=r,
                ),
                label=f"create alert rule {rule_name}",
            )
            if resp is not None and resp.status_code < 300:
                step.items_done += 1
            elif resp is not None:
                logger.warning("Alert rule %s failed: %s", rule_name, resp.text[:200])
            notify(self.progress)

        step.status = "ok" if step.items_done > 0 else "failed"
        step.detail = f"Created {step.items_done}/{step.items_total} alert rules"
        notify(self.progress)

    def _cleanup_alerts(self, client: httpx.Client) -> tuple[int, int]:
        """Delete alert rules belonging to this scenario.

        Primary: name-based search (new-style rules named "{scenario_name} CH…").
        Fallback: tag-based search (old-style rules tagged with namespace).

        Returns ``(deleted, remaining)`` — remaining > 0 indicates rules that
        couldn't be removed (e.g. transient API errors despite retries).
        """
        deleted = 0
        deleted_ids: set[str] = set()
        scenario_name = self.scenario.scenario_name

        def _delete_rule(rule_id: str) -> None:
            nonlocal deleted
            if not rule_id or rule_id in deleted_ids:
                return
            resp = _retry_http(
                lambda: client.delete(
                    f"{self.kibana_url}/api/alerting/rule/{rule_id}",
                    headers=_kibana_headers(self.api_key),
                ),
                label=f"delete alert rule {rule_id}",
            )
            if resp is not None and (resp.status_code < 300 or resp.status_code == 404):
                deleted_ids.add(rule_id)
                deleted += 1

        # Primary: name-based (new-style rules named "{scenario_name} CH…")
        for page in range(1, 11):
            resp = _retry_http(
                lambda: client.get(
                    f"{self.kibana_url}/api/alerting/rules/_find",
                    params={"per_page": 100, "page": page, "search_fields": "name", "search": scenario_name},
                    headers=_kibana_headers(self.api_key),
                ),
                label=f"find alerts by name page={page}",
            )
            if resp is None or resp.status_code >= 300:
                break
            try:
                rules = resp.json().get("data", [])
            except Exception:
                break
            if not rules:
                break
            for rule in rules:
                if scenario_name not in rule.get("name", ""):
                    continue
                _delete_rule(rule.get("id", ""))

        # Fallback: tag-based (old-style rules tagged with namespace)
        for page in range(1, 11):
            resp = _retry_http(
                lambda: client.get(
                    f"{self.kibana_url}/api/alerting/rules/_find?per_page=100&page={page}"
                    f"&filter=alert.attributes.tags:{self.ns}",
                    headers=_kibana_headers(self.api_key),
                ),
                label=f"find alerts by tag page={page}",
            )
            if resp is None or resp.status_code >= 300:
                break
            try:
                rules = resp.json().get("data", [])
            except Exception:
                break
            if not rules:
                break
            for rule in rules:
                _delete_rule(rule.get("id", ""))

        # Migration cleanup: pre-refactor rules named "Channel XX: {name}" with no scenario prefix.
        old_names: set[str] = set()
        for ch_num, ch_data in self.scenario.channel_registry.items():
            num_str = f"{int(ch_num):02d}"
            old_names.add(f"Channel {num_str}: {ch_data['name']}")

        if old_names:
            for page in range(1, 11):
                resp = _retry_http(
                    lambda: client.get(
                        f"{self.kibana_url}/api/alerting/rules/_find?per_page=100&page={page}",
                        headers=_kibana_headers(self.api_key),
                    ),
                    label=f"find migration alerts page={page}",
                )
                if resp is None or resp.status_code >= 300:
                    break
                try:
                    rules = resp.json().get("data", [])
                except Exception:
                    break
                if not rules:
                    break
                for rule in rules:
                    if rule.get("name", "") in old_names:
                        _delete_rule(rule.get("id", ""))

        # Verify: count any rules still matching this scenario after cleanup.
        remaining = 0
        verify = _retry_http(
            lambda: client.get(
                f"{self.kibana_url}/api/alerting/rules/_find",
                params={"per_page": 100, "page": 1, "search_fields": "name", "search": scenario_name},
                headers=_kibana_headers(self.api_key),
            ),
            label="verify alerts cleanup",
        )
        if verify is not None and verify.status_code < 300:
            try:
                remaining = sum(
                    1 for r in verify.json().get("data", [])
                    if scenario_name in r.get("name", "")
                )
            except Exception:
                pass

        return deleted, remaining

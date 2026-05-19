"""KbMixin — knowledge base deploy methods."""

from __future__ import annotations

import json
from typing import Any

import httpx

from elastic_config.deployer_base import _es_headers, ProgressCallback


class KbMixin:

    def _deploy_knowledge_base(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(7)
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
1. Search for `{error_type}` in recent ERROR logs using `{self.scenario.prefixed_tool_id("search_error_logs")}` — this identifier appears in the log body (body.text)
2. Check health of affected services: {affected}
3. Trace anomaly propagation to cascade services: {cascade}
4. Check for correlated errors in the same time window
{investigation_section}
## Root Cause Indicators
- Look for `{error_type}` entries in body.text (this is the indexed field — do NOT search body alone)
- Check if multiple channels in the {subsystem} subsystem are affected
- Verify if errors correlate with infrastructure events

## Remediation
When the user asks you to fix or remediate this issue, use `{self.scenario.prefixed_tool_id("remediation_action")}` tool with action_type: {remediation_action}, channel: {ch_num}, and a justification. Once the tool returns successfully, report remediation as complete. Do NOT search for errors after remediation — the fix takes several minutes to propagate, so residual errors are expected immediately after.
"""

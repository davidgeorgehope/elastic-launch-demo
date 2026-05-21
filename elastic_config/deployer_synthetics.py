"""SyntheticsMixin — Kibana Synthetics HTTP monitor deploy and cleanup.

Creates lightweight HTTP monitors for the FCC citizen-facing portals so the
Kibana Synthetics UI (Observability → Synthetics) is populated during demos.
Monitors run from Elastic-managed US locations every 3 minutes.

Only wired in for the FCC scenario (namespace == "fcc").
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from elastic_config.deployer_base import _kibana_headers, _retry_http, ProgressCallback

if TYPE_CHECKING:
    from scenarios.base import BaseScenario

logger = logging.getLogger("deployer")

# ── FCC portal monitors ────────────────────────────────────────────────────────
# Each entry: (display name, URL, expected HTTP status)
_FCC_MONITORS = [
    ("FCC Public Portal",            "https://www.fcc.gov/",                          200),
    ("FCC Consumer Complaint Portal", "https://consumercomplaints.fcc.gov/hc/en-us",  200),
    ("FCC Broadband Map",            "https://broadbandmap.fcc.gov/home",             200),
    ("FCC ULS License Search",       "https://wireless2.fcc.gov/UlsApp/UlsSearch/searchLicense.jsp", 200),
    ("FCC Open Data Portal",         "https://opendata.fcc.gov/",                     200),
]

# Elastic Cloud managed synthetics locations — US East is always available.
_LOCATIONS = [{"id": "us_east", "isServiceManaged": True}]


class SyntheticsMixin:
    if TYPE_CHECKING:
        kibana_url: str
        api_key: str
        ns: str
        scenario: BaseScenario
        progress: object

    # injected by ScenarioDeployer
    def _step(self, index: int):  # noqa: D102 — implemented in ScenarioDeployer
        ...

    def _deploy_synthetics(self, client: httpx.Client, notify: ProgressCallback):
        """Create Synthetics HTTP monitors for the FCC portals."""
        step = self._step(18)
        step.status = "running"
        notify(self.progress)

        # Only create monitors for the FCC scenario.
        if self.ns != "fcc":
            step.status = "skipped"
            step.detail = f"Skipped for namespace '{self.ns}'"
            notify(self.progress)
            return

        headers = _kibana_headers(self.api_key)
        step.items_total = len(_FCC_MONITORS)
        self._cleanup_synthetics(client)

        created = 0
        for name, url, _expected_status in _FCC_MONITORS:
            body = {
                "type": "http",
                "name": name,
                "urls": url,
                "schedule": {"number": "3", "unit": "m"},
                "locations": _LOCATIONS,
                "tags": [self.ns, "citizen-facing", "auto-created"],
                "enabled": True,
            }
            resp = _retry_http(
                lambda b=body: client.post(
                    f"{self.kibana_url}/api/synthetics/monitors",
                    headers=headers,
                    json=b,
                ),
                label=f"create monitor {name}",
            )
            if resp and resp.status_code < 300:
                created += 1
                step.items_done = created
                step.detail = f"Created: {name}"
                logger.info("Synthetics monitor created: %s", name)
            else:
                status = resp.status_code if resp else "no response"
                body_text = resp.text[:200] if resp else ""
                logger.warning("Monitor create failed %s: HTTP %s — %s", name, status, body_text)
            notify(self.progress)

        if created == len(_FCC_MONITORS):
            step.status = "ok"
        elif created > 0:
            step.status = "ok"
        else:
            step.status = "failed"
        step.detail = f"Created {created}/{len(_FCC_MONITORS)} Synthetics monitors"
        notify(self.progress)

    def _cleanup_synthetics(self, client: httpx.Client) -> int:
        """Delete any Synthetics monitors tagged with this scenario's namespace."""
        headers = _kibana_headers(self.api_key)
        deleted = 0
        try:
            resp = client.get(
                f"{self.kibana_url}/api/synthetics/monitors?perPage=500",
                headers=headers,
            )
            if resp.status_code >= 300:
                return 0
            data = resp.json()
            monitors = data if isinstance(data, list) else data.get("monitors", [])
            for monitor in monitors:
                tags = monitor.get("tags", [])
                if self.ns in tags and "auto-created" in tags:
                    monitor_id = monitor.get("config_id") or monitor.get("id", "")
                    if monitor_id:
                        client.delete(
                            f"{self.kibana_url}/api/synthetics/monitors/{monitor_id}",
                            headers=headers,
                        )
                        deleted += 1
        except Exception as exc:
            logger.warning("Synthetics cleanup error: %s", exc)
        return deleted

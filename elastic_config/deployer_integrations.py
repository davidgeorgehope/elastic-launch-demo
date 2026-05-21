"""IntegrationsMixin — install Elastic Fleet/EPM integrations used by the demo."""

from __future__ import annotations

import logging

import httpx

from elastic_config.deployer_base import _kibana_headers, _retry_http, ProgressCallback

logger = logging.getLogger("deployer")

# Latest version is resolved at install time — do not hard-code versions here.
INTEGRATIONS = [
    "kubernetes_otel",
    "aws_vpcflow_otel",
    "gcp_vpcflow_otel",
    "nginx_otel",
    "mysql_otel",
]


class IntegrationsMixin:

    def _install_integrations(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(5)
        step.status = "running"
        step.items_total = len(INTEGRATIONS)
        step.items_done = 0
        notify(self.progress)

        installed, skipped, errors = [], [], []

        for pkg in INTEGRATIONS:
            try:
                info = client.get(
                    f"{self.kibana_url}/api/fleet/epm/packages/{pkg}",
                    headers=_kibana_headers(self.api_key),
                )
                if info.status_code >= 300:
                    errors.append(f"{pkg} (lookup HTTP {info.status_code})")
                    step.items_done += 1
                    notify(self.progress)
                    continue
                item = info.json().get("item") or info.json().get("response") or {}
                latest = item.get("latestVersion")
                current = item.get("version") if item.get("status") == "installed" else None
                if not latest:
                    errors.append(f"{pkg} (no latestVersion in response)")
                    step.items_done += 1
                    notify(self.progress)
                    continue

                if current == latest:
                    skipped.append(f"{pkg}@{latest}")
                else:
                    resp = _retry_http(
                        lambda p=pkg, v=latest: client.post(
                            f"{self.kibana_url}/api/fleet/epm/packages/{p}/{v}",
                            headers=_kibana_headers(self.api_key),
                            json={"force": True},
                        ),
                        label=f"install integration {pkg}",
                    )
                    if resp is not None and resp.status_code < 300:
                        installed.append(f"{pkg}@{latest}")
                    else:
                        code = resp.status_code if resp is not None else "no-response"
                        errors.append(f"{pkg} (install HTTP {code})")
            except Exception as exc:
                errors.append(f"{pkg} ({exc})")

            step.items_done += 1
            notify(self.progress)

        parts = []
        if installed:
            parts.append(f"installed {len(installed)}: {', '.join(installed)}")
        if skipped:
            parts.append(f"already current: {', '.join(skipped)}")
        if errors:
            parts.append(f"failed: {', '.join(errors)}")

        step.detail = "; ".join(parts) or "no integrations configured"
        step.status = "ok" if (installed or skipped) else "failed"
        notify(self.progress)

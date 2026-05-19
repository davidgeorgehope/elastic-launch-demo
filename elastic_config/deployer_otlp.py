"""OtlpMixin — OTLP endpoint derivation methods."""

from __future__ import annotations

import time
import httpx

from elastic_config.deployer_base import _es_headers, ProgressCallback

_OTLP_RETRIES = 4          # attempts (initial + 3 retries)
_OTLP_RETRY_DELAY = 5.0    # seconds between attempts


class OtlpMixin:

    def _derive_otlp_step(self, client: httpx.Client, notify: ProgressCallback):
        step = self._step(2)
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
        """Derive OTLP ingest endpoint using three strategies in priority order:
        1. Cluster settings API (display_name + cloud suffix)
        2. .es. → .ingest. URL swap
        Each candidate is verified with a live OTLP probe before being returned.
        Retries up to _OTLP_RETRIES times to handle newly provisioned clusters
        where the ingest endpoint may not be ready immediately.
        """
        for attempt in range(_OTLP_RETRIES):
            if attempt > 0:
                time.sleep(_OTLP_RETRY_DELAY)

            # Strategy 1: cluster settings API
            endpoint = self._derive_otlp_via_cluster_api(client)
            if endpoint and self._verify_otlp_candidate(client, endpoint):
                return endpoint

            # Strategy 2: .es. → .ingest. swap
            endpoint = self._derive_otlp_via_url_swap()
            if endpoint and self._verify_otlp_candidate(client, endpoint):
                return endpoint

        return None

    def _derive_otlp_via_cluster_api(self, client: httpx.Client) -> str | None:
        """Use /_cluster/settings to build the ingest URL from the cluster display name."""
        try:
            resp = client.get(
                f"{self.elastic_url.rstrip('/')}/_cluster/settings",
                headers=_es_headers(self.api_key),
                params={"include_defaults": "true"},
                timeout=10,
            )
            if resp.status_code >= 300:
                return None
            data = resp.json()
            raw_name = (
                data.get("persistent", {}).get("cluster", {}).get("metadata", {}).get("display_name")
                or data.get("defaults", {}).get("cluster", {}).get("name")
            )
            if not raw_name:
                return None

            # Convert "Name (ID)" → "Name-ID"
            import re
            clean_alias = re.sub(r" \(([^)]+)\)$", r"-\1", raw_name)

            # Extract cloud suffix: everything after the first dot, minus the port
            es_host = self.elastic_url.rstrip("/").split("//")[-1]  # strip scheme
            after_first_dot = es_host.split(".", 1)[1] if "." in es_host else ""
            cloud_suffix = after_first_dot.split(":")[0]  # strip port if present

            if not cloud_suffix:
                return None

            return f"https://{clean_alias}.ingest.{cloud_suffix}:443"
        except Exception:
            return None

    def _derive_otlp_via_url_swap(self) -> str | None:
        """Derive OTLP endpoint by swapping .es. for .ingest. in the ES URL."""
        if ".es." not in self.elastic_url:
            return None
        endpoint = self.elastic_url.replace(".es.", ".ingest.").rstrip("/")
        if not endpoint.endswith(":443"):
            endpoint += ":443"
        return endpoint

    def _verify_otlp_candidate(self, client: httpx.Client, endpoint: str) -> bool:
        """Return True if the endpoint responds to an OTLP probe.

        Any HTTP response (including 4xx) is treated as reachable — it means
        the ingest endpoint exists and is routing traffic.  Only connection
        errors and 5xx (service not yet ready) count as failures, which the
        caller retries for newly provisioned clusters.
        """
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
            return resp.status_code < 500
        except Exception:
            return False

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

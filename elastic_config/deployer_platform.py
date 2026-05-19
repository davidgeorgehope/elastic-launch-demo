"""PlatformMixin — platform settings configuration methods."""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx

from elastic_config.deployer_base import _kibana_headers, _es_headers, ProgressCallback

_SECURITY_DIR = Path(__file__).parent / "security"


class PlatformMixin:

    def _configure_platform_settings(
        self, client: httpx.Client, notify: ProgressCallback
    ):
        """Enable wired streams, significant events, agent builder, and AI docs."""
        step = self._step(4)
        step.status = "running"
        notify(self.progress)

        configured = []
        errors = []

        # 1. Enable wired streams (idempotent — safe to call if already enabled)
        try:
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
        # Use the public /api/kibana/settings endpoint (same one the Advanced Settings UI
        # uses) rather than /internal/kibana/settings, which does not apply this setting.
        try:
            resp = client.post(
                f"{self.kibana_url}/api/kibana/settings",
                headers=_kibana_headers(self.api_key),
                json={
                    "changes": {"observability:streamsEnableSignificantEvents": True}
                },
            )
            if resp.status_code < 300:
                configured.append("significant events")
            else:
                # Fallback to internal API in case the public one isn't available
                resp2 = client.post(
                    f"{self.kibana_url}/internal/kibana/settings",
                    headers=_kibana_headers(self.api_key),
                    json={
                        "changes": {
                            "observability:streamsEnableSignificantEvents": True
                        }
                    },
                )
                if resp2.status_code < 300:
                    configured.append("significant events")
                else:
                    errors.append(
                        f"significant events (HTTP {resp.status_code}/{resp2.status_code})"
                    )
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

        # 4. Install Elastic product documentation (for AI assistant context)
        try:
            resp = client.post(
                f"{self.kibana_url}/internal/product_doc_base/install",
                headers=_kibana_headers(self.api_key),
                json={
                    "inferenceId": ".elser-2-elasticsearch",
                    "resourceType": "product_doc",
                },
            )
            if resp.status_code < 300:
                configured.append("AI docs")
            else:
                errors.append(f"AI docs (HTTP {resp.status_code})")
        except Exception as exc:
            errors.append(f"AI docs ({exc})")

        # 5. Enable workflows UI
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

        # 6. Hide Kibana new-tab announcement popup (9.4.0+ moved this to a global setting)
        try:
            resp = client.post(
                f"{self.kibana_url}/api/kibana/settings",
                headers=_kibana_headers(self.api_key),
                json={"changes": {"hideAnnouncements": True}},
            )
            if resp.status_code < 300:
                configured.append("hide announcements")
            else:
                resp2 = client.post(
                    f"{self.kibana_url}/internal/kibana/settings",
                    headers=_kibana_headers(self.api_key),
                    json={"changes": {"hideAnnouncements": True}},
                )
                if resp2.status_code < 300:
                    configured.append("hide announcements")
                else:
                    errors.append(
                        f"hide announcements (HTTP {resp.status_code}/{resp2.status_code})"
                    )
        except Exception as exc:
            errors.append(f"hide announcements ({exc})")

        # 7 & 8. Create viewer-custom role and guest user (only when KIBANA_RO_PASSWORD is set)
        ro_password = os.getenv("KIBANA_RO_PASSWORD", "").strip()
        if ro_password:
            try:
                role_body = json.loads(
                    (_SECURITY_DIR / "roles" / "viewer-custom.json").read_text()
                )
                role_body.pop("transient_metadata", None)
                resp = client.put(
                    f"{self.elastic_url}/_security/role/viewer-custom",
                    headers=_es_headers(self.api_key),
                    json=role_body,
                )
                if resp.status_code < 300:
                    configured.append("viewer-custom role")
                else:
                    errors.append(f"viewer-custom role (HTTP {resp.status_code})")
            except Exception as exc:
                errors.append(f"viewer-custom role ({exc})")

            try:
                user_body = json.loads(
                    (_SECURITY_DIR / "users" / "guest.json").read_text()
                )
                user_body["password"] = ro_password
                resp = client.put(
                    f"{self.elastic_url}/_security/user/guest",
                    headers=_es_headers(self.api_key),
                    json=user_body,
                )
                if resp.status_code < 300:
                    configured.append("guest user")
                else:
                    errors.append(f"guest user (HTTP {resp.status_code})")
            except Exception as exc:
                errors.append(f"guest user ({exc})")

        if configured:
            step.status = "ok"
            step.detail = f"Enabled: {', '.join(configured)}"
            if errors:
                step.detail += f"; failed: {', '.join(errors)}"
        else:
            step.status = "failed"
            step.detail = f"Failed: {', '.join(errors)}"

        notify(self.progress)

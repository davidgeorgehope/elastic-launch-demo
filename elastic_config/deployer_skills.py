"""SkillsMixin — Agent Builder skill deploy and discovery methods."""

from __future__ import annotations

import logging

import httpx

from elastic_config.deployer_base import _kibana_headers, ProgressCallback

logger = logging.getLogger("deployer")


class SkillsMixin:

    def _discover_builtin_skill_ids(self, client: httpx.Client) -> list[str]:
        """Return IDs of available built-in skills matching the scenario's wanted names."""
        try:
            resp = client.get(
                f"{self.kibana_url}/api/agent_builder/skills",
                headers=_kibana_headers(self.api_key),
                params={"include_plugins": "true"},
            )
            if resp.status_code >= 300:
                logger.warning("Could not list built-in skills: HTTP %s", resp.status_code)
                return []
            body = resp.json()
            skills = body.get("data", body.get("results", []))
            want = set(self.scenario.builtin_skill_names)
            found = []
            for skill in skills:
                skill_id = skill.get("id", "")
                skill_name = skill.get("name", "")
                if skill_id in want or skill_name in want:
                    found.append(skill_id)
            return found
        except Exception as exc:
            logger.warning("Built-in skill discovery failed: %s", exc)
            return []

    def _deploy_skills(self, client: httpx.Client, notify: ProgressCallback):
        """Discover built-in skills and deploy custom skills for this scenario.

        Appends all resolved skill IDs to self._created_skill_ids and
        updates step 8 progress items.
        """
        step = self._step(8)

        builtin_ids = self._discover_builtin_skill_ids(client)
        self._created_skill_ids.extend(builtin_ids)
        if builtin_ids:
            step.detail = f"Attached {len(builtin_ids)} built-in skill(s)"
            notify(self.progress)

        for skill_def in self.scenario.skill_definitions:
            skill_id = skill_def["id"]
            client.delete(
                f"{self.kibana_url}/api/agent_builder/skills/{skill_id}",
                headers=_kibana_headers(self.api_key),
                params={"force": "true"},
            )
            resp = client.post(
                f"{self.kibana_url}/api/agent_builder/skills",
                headers=_kibana_headers(self.api_key),
                json=skill_def,
            )
            if resp.status_code < 300:
                self._created_skill_ids.append(skill_id)
                step.items_done += 1
                step.detail = f"Created skill: {skill_id}"
                logger.info("Created skill: %s", skill_id)
            else:
                step.detail = f"Skill {skill_id} failed: HTTP {resp.status_code}"
                logger.warning(
                    "Skill %s failed: HTTP %s — %s",
                    skill_id, resp.status_code, resp.text[:200],
                )
            notify(self.progress)

    def _cleanup_skills(self, client: httpx.Client) -> int:
        """Delete custom skills created for this scenario. Returns count deleted."""
        deleted = 0
        for skill_def in self.scenario.skill_definitions:
            skill_id = skill_def["id"]
            resp = client.delete(
                f"{self.kibana_url}/api/agent_builder/skills/{skill_id}",
                headers=_kibana_headers(self.api_key),
                params={"force": "true"},
            )
            if resp.status_code < 300:
                deleted += 1
            elif resp.status_code != 404:
                logger.warning(
                    "Failed to delete skill %s: HTTP %s", skill_id, resp.status_code
                )
        return deleted

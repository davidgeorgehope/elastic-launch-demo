"""Cloud Armor WAF service — GCP us-east1. WAF rules, DDoS protection, security policies."""

from __future__ import annotations

import random

from app.services.base_service import BaseService


class CloudArmorWafService(BaseService):
    SERVICE_NAME = "cloud-armor-waf"

    POLICIES = ["gcpnet-waf-policy", "gcpnet-ddos-policy", "gcpnet-edge-policy"]
    RULE_CATEGORIES = ["sqli", "xss", "rce", "lfi", "rfi", "scanner_detection"]

    def generate_telemetry(self) -> None:
        # -- Fault injection --
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Request evaluation --
        policy = random.choice(self.POLICIES)
        total_requests = random.randint(10000, 50000)
        blocked_requests = (
            random.randint(10, 100)
            if not active_channels
            else random.randint(500, 5000)
        )
        allowed_requests = total_requests - blocked_requests

        self.emit_metric("armor.requests_total", float(total_requests), "requests")
        self.emit_metric("armor.requests_blocked", float(blocked_requests), "requests")
        self.emit_metric("armor.requests_allowed", float(allowed_requests), "requests")

        self.emit_log(
            "INFO",
            f"cloud-armor: policy={policy} total={total_requests} "
            f"blocked={blocked_requests} allowed={allowed_requests} "
            f"adaptive_protection=ENABLED",
            {
                "operation": "request_eval",
                "armor.policy": policy,
                "armor.total": total_requests,
                "armor.blocked": blocked_requests,
            },
        )

        # -- DDoS metrics --
        ddos_events = (
            random.randint(0, 1) if not active_channels else random.randint(3, 10)
        )
        attack_volume_mbps = (
            round(random.uniform(0.0, 50.0), 1)
            if not active_channels
            else round(random.uniform(5000.0, 120000.0), 1)
        )
        self.emit_metric("armor.ddos_events", float(ddos_events), "events")
        self.emit_metric("armor.attack_volume_mbps", attack_volume_mbps, "Mbps")

        self.emit_log(
            "INFO",
            f"cloud-armor: ddos_events={ddos_events} attack_volume={attack_volume_mbps}Mbps "
            f"mitigation=ACTIVE policy={policy}",
            {
                "operation": "ddos_status",
                "armor.ddos_events": ddos_events,
                "armor.attack_volume": attack_volume_mbps,
            },
        )

        # -- WAF rule match distribution --
        category = random.choice(self.RULE_CATEGORIES)
        matches = (
            random.randint(0, 20) if not active_channels else random.randint(100, 1000)
        )
        self.emit_metric("armor.rule_matches", float(matches), "matches")

        self.emit_log(
            "INFO",
            f"cloud-armor: waf_category={category} matches={matches} "
            f"action=DENY(403) sensitivity=2 policy={policy}",
            {
                "operation": "waf_rule_stats",
                "armor.waf_category": category,
                "armor.rule_matches": matches,
            },
        )

        # -- Rate limiting --
        rate_limited = (
            random.randint(0, 10) if not active_channels else random.randint(100, 2000)
        )
        self.emit_metric("armor.rate_limited", float(rate_limited), "requests")
        self.emit_log(
            "INFO",
            f"cloud-armor: rate_limited={rate_limited} threshold=1000/min "
            f"conform_action=allow exceed_action=deny(429) policy={policy}",
            {
                "operation": "rate_limit",
                "armor.rate_limited": rate_limited,
            },
        )

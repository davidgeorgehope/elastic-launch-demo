"""Cloud Inventory Scanner service — GCP us-central1-a. Cross-cloud asset discovery and compliance."""

from __future__ import annotations

import random

from app.services.base_service import BaseService


class CloudInventoryScannerService(BaseService):
    SERVICE_NAME = "cloud-inventory-scanner"

    CLOUD_PROVIDERS = ["aws", "gcp", "azure"]

    def generate_telemetry(self) -> None:
        # -- Fault injection --
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # -- Per-cloud scanning --
        for provider in self.CLOUD_PROVIDERS:
            resources_scanned = random.randint(500, 2500)
            orphaned = (
                random.randint(0, 3) if not active_channels else random.randint(5, 25)
            )
            compliance_pct = round(random.uniform(97.0, 100.0), 1)

            self.emit_metric(
                f"cloud_inventory.{provider}.resources_scanned",
                float(resources_scanned),
                "resources",
            )
            self.emit_metric(
                f"cloud_inventory.{provider}.orphaned_count",
                float(orphaned),
                "resources",
            )
            self.emit_metric(
                f"cloud_inventory.{provider}.compliance_pct", compliance_pct, "%"
            )

            self.emit_log(
                "INFO",
                f"cloud-inventory-scan provider={provider} resources_scanned={resources_scanned} "
                f"orphaned={orphaned} compliance={compliance_pct}%",
                {
                    "operation": "cloud_scan",
                    "cloud_inventory.provider": provider,
                    "cloud_inventory.resources": resources_scanned,
                    "cloud_inventory.orphaned": orphaned,
                    "cloud_inventory.compliance": compliance_pct,
                },
            )

        # VPN tunnel health
        tunnel_count = 6
        tunnels_up = tunnel_count if not active_channels else random.randint(3, 5)
        self.emit_metric("cloud_inventory.vpn_tunnels_up", float(tunnels_up), "tunnels")
        self.emit_log(
            "INFO",
            f"cloud-networking vpn-health tunnels_up={tunnels_up}/{tunnel_count} "
            f"status={'nominal' if tunnels_up == tunnel_count else 'degraded'}",
            {
                "operation": "vpn_health",
                "vpn.tunnels_total": tunnel_count,
                "vpn.tunnels_up": tunnels_up,
            },
        )

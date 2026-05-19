"""Risk Calculator service — AWS us-east-1c. Real-time risk and margin computation."""

from __future__ import annotations

import random
import time

from app.services.base_service import BaseService
from scenarios.financial.executive_kpis import emit_executive_business_metrics_if_eligible


class RiskCalculatorService(BaseService):
    SERVICE_NAME = "risk-calculator"

    DESKS = {
        "EQ-FLOW": {"limit_m": 200, "asset_class": "equity"},
        "EQ-PROP": {"limit_m": 100, "asset_class": "equity"},
        "FI-RATES": {"limit_m": 500, "asset_class": "fixed_income"},
        "FX-SPOT": {"limit_m": 300, "asset_class": "fx"},
        "DRV-VOL": {"limit_m": 150, "asset_class": "derivatives"},
    }

    def __init__(self, chaos_controller, otlp_client):
        super().__init__(chaos_controller, otlp_client)
        self._last_var_calc = time.time()
        self._risk_checks = 0

    def generate_telemetry(self) -> None:
        # ── Fault injection ────────────────────────────────────
        active_channels = self.get_active_channels_for_service()
        for ch in active_channels:
            self.emit_fault_logs(ch)

        cascade_channels = self.get_cascade_channels_for_service()
        for ch in cascade_channels:
            self.emit_cascade_logs(ch)

        # ── Normal telemetry ───────────────────────────────────
        self._emit_risk_check()
        self._emit_margin_snapshot()

        if time.time() - self._last_var_calc > 12:
            self._emit_var_calculation()
            self._last_var_calc = time.time()

        # Metrics
        self._risk_checks += 1
        self.emit_metric(
            "risk_calculator.risk_checks", float(self._risk_checks), "checks"
        )
        self.emit_metric(
            "risk_calculator.var_95",
            round(random.uniform(5.0, 25.0), 2),
            "M_USD",
        )
        self.emit_metric(
            "risk_calculator.margin_utilization",
            round(random.uniform(40.0, 85.0), 1),
            "%",
        )

        emit_executive_business_metrics_if_eligible(self)

    def _emit_risk_check(self) -> None:
        desk_name = random.choice(list(self.DESKS.keys()))
        desk = self.DESKS[desk_name]
        exposure_m = round(random.uniform(10, desk["limit_m"] * 0.8), 1)
        utilization = round(exposure_m / desk["limit_m"] * 100, 1)
        self.emit_log(
            "INFO",
            f"[RISK] pre_trade_check desk={desk_name} exposure_m=${exposure_m} limit_m=${desk['limit_m']} utilization={utilization}% asset_class={desk['asset_class']} result=PASS",
            {
                "operation": "risk_check",
                "risk.desk": desk_name,
                "risk.exposure_m": exposure_m,
                "risk.limit_m": desk["limit_m"],
                "risk.utilization_pct": utilization,
                "risk.result": "PASS",
                "risk.asset_class": desk["asset_class"],
            },
        )

    def _emit_margin_snapshot(self) -> None:
        accounts_checked = random.randint(100, 500)
        margin_calls = random.randint(0, 3)
        self.emit_log(
            "INFO",
            f"[RISK] margin_sweep accounts_checked={accounts_checked} calls_pending={margin_calls} status=OK",
            {
                "operation": "margin_sweep",
                "margin.accounts_checked": accounts_checked,
                "margin.calls_pending": margin_calls,
            },
        )

    def _emit_var_calculation(self) -> None:
        var_95 = round(random.uniform(5.0, 25.0), 2)
        var_99 = round(var_95 * 1.5, 2)
        scenarios = random.randint(10000, 50000)
        self.emit_log(
            "INFO",
            f"[RISK] var_calculation var_95=${var_95}M var_99=${var_99}M scenarios={scenarios} status=WITHIN_LIMITS",
            {
                "operation": "var_calculation",
                "var.95_percentile_m": var_95,
                "var.99_percentile_m": var_99,
                "var.scenario_count": scenarios,
                "var.status": "WITHIN_LIMITS",
            },
        )

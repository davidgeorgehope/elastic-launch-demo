"""NOVA-7 Space Mission scenario — orbital insertion mission with rocket propulsion, guidance, communications, and range safety systems."""

from __future__ import annotations

import random
import time
from typing import Any

from scenarios.base import BaseScenario, CountdownConfig, UITheme


class SpaceScenario(BaseScenario):
    """NOVA-7 orbital insertion mission with 9 space systems and 20 fault channels."""

    # ── Identity ──────────────────────────────────────────────────────

    @property
    def scenario_id(self) -> str:
        return "space"

    @property
    def scenario_icon(self) -> str:
        return "🚀"

    @property
    def scenario_name(self) -> str:
        return "NOVA-7 Space Mission"

    @property
    def scenario_description(self) -> str:
        return (
            "Orbital insertion mission with rocket propulsion, guidance, "
            "communications, and range safety systems. NASA-style Mission Control "
            "with countdown clock and 20 fault channels across 9 space systems."
        )

    @property
    def namespace(self) -> str:
        return "nova7"

    @property
    def sort_order(self) -> int:
        return 1

    @property
    def raw_log_profile(self) -> dict[str, Any]:
        return {
            "service_name": "mission-control-api",
            "user_id_prefix": "gs",
            "tier_field": "mission_class",
            "tier_values": [("cubesat", 55), ("geo", 30), ("deep-space", 15)],
            "country_weights": {"US": 50, "DE": 12, "JP": 10, "GB": 8, "FR": 8, "IN": 6, "AU": 6},
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "paths": [
                "/api/v1/telemetry", "/api/v1/orbits/{satellite}",
                "/api/v1/commands", "/api/v1/groundstations",
                "/api/v1/passes", "/api/v1/ephemeris", "/health",
            ],
            "change_point_path": "/api/v1/commands",
        }

    @property
    def executive_kpi_emitter_service_name(self) -> str:
        return "mission-control"

    @property
    def executive_dashboard_intro(self) -> str:
        return (
            "**NOVA-7 program view** — mission assurance, orbital mechanics, ground communications, "
            "and program health KPIs (synthetic `business.*` streams from `mission-control`)."
        )

    @property
    def executive_kpi_sections(self) -> list[dict]:
        return [
            {
                "header": "**Mission assurance** — success probability, uptime, faults, recovery, and health",
                "specs": [
                    ("Mission success probability (%)", "metrics.business.mission_success_probability_pct"),
                    ("Critical system uptime (%)", "metrics.business.critical_system_uptime_pct"),
                    ("Fault events / min", "metrics.business.fault_events_per_min"),
                    ("Autonomous recovery rate (%)", "metrics.business.autonomous_recovery_rate_pct"),
                    ("Telemetry coverage (%)", "metrics.business.telemetry_coverage_pct"),
                    ("Spacecraft health index (0–100)", "metrics.business.spacecraft_health_index_0_100"),
                ],
            },
            {
                "header": "**Orbital mechanics** — trajectory, delta-V, drift, accuracy, fuel, and altitude",
                "specs": [
                    ("Trajectory deviation (m)", "metrics.business.trajectory_deviation_meters"),
                    ("Delta-V remaining (m/s)", "metrics.business.delta_v_budget_remaining_mps"),
                    ("Orbital period drift (ms)", "metrics.business.orbital_period_drift_ms"),
                    ("Maneuver accuracy (%)", "metrics.business.maneuver_accuracy_pct"),
                    ("Station-keeping fuel (%)", "metrics.business.station_keeping_fuel_remaining_pct"),
                    ("Perigee altitude (km)", "metrics.business.perigee_altitude_km"),
                ],
            },
            {
                "header": "**Communications** — downlink rate, uplink latency, contacts, packet loss, and ground",
                "specs": [
                    ("Downlink data rate (Mbps)", "metrics.business.downlink_data_rate_mbps"),
                    ("Uplink latency (ms)", "metrics.business.uplink_latency_ms"),
                    ("Contact window utilization (%)", "metrics.business.contact_window_utilization_pct"),
                    ("Packet loss rate (%)", "metrics.business.packet_loss_rate_pct"),
                    ("Command acceptance rate (%)", "metrics.business.command_acceptance_rate_pct"),
                    ("Ground station availability (%)", "metrics.business.ground_station_availability_pct"),
                ],
            },
            {
                "header": "**Program health** — schedule, readiness, SLA, cost variance, risk, and NPS",
                "specs": [
                    ("Schedule variance (days)", "metrics.business.schedule_variance_days"),
                    ("Launch readiness index (0–100)", "metrics.business.launch_readiness_index_0_100"),
                    ("Contractor SLA compliance (%)", "metrics.business.contractor_sla_compliance_pct"),
                    ("Cost variance (%)", "metrics.business.cost_variance_pct"),
                    ("Risk burn-down rate", "metrics.business.risk_burn_down_rate"),
                    ("Program satisfaction (NPS-like)", "metrics.business.program_net_satisfaction_proxy_nps"),
                ],
            },
        ]

    @property
    def executive_trend_charts(self) -> list[dict]:
        return [
            {"title": "Mission success probability", "field": "metrics.business.mission_success_probability_pct", "y_label": "%"},
            {"title": "Trajectory deviation (m)", "field": "metrics.business.trajectory_deviation_meters", "y_label": "m"},
            {"title": "Downlink data rate (Mbps)", "field": "metrics.business.downlink_data_rate_mbps", "y_label": "Mbps"},
            {"title": "Spacecraft health index", "field": "metrics.business.spacecraft_health_index_0_100", "y_label": "index"},
            {"title": "Delta-V remaining (m/s)", "field": "metrics.business.delta_v_budget_remaining_mps", "y_label": "m/s"},
            {"title": "Fault events / min", "field": "metrics.business.fault_events_per_min", "y_label": "events/min"},
        ]

    # ── Services ──────────────────────────────────────────────────────

    @property
    def services(self) -> dict[str, dict[str, Any]]:
        return {
            "mission-control": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1a",
                "subsystem": "command",
                "language": "python",
            },
            "fuel-system": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1b",
                "subsystem": "propulsion",
                "language": "go",
            },
            "ground-systems": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1c",
                "subsystem": "ground",
                "language": "java",
            },
            "navigation": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "guidance",
                "language": "rust",
            },
            "comms-array": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-b",
                "subsystem": "communications",
                "language": "cpp",
            },
            "payload-monitor": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "payload",
                "language": "python",
            },
            "sensor-validator": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "validation",
                "language": "dotnet",
            },
            "telemetry-relay": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-2",
                "subsystem": "relay",
                "language": "go",
            },
            "range-safety": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "safety",
                "language": "java",
            },
        }

    # ── Channel Registry ──────────────────────────────────────────────

    @property
    def channel_registry(self) -> dict[int, dict[str, Any]]:
        return {
            1: {
                "name": "Thermal Calibration Drift",
                "subsystem": "propulsion",
                "vehicle_section": "engine_bay",
                "error_type": "TCS-DRIFT-CRITICAL",
                "sensor_type": "thermal",
                "affected_services": ["fuel-system", "sensor-validator"],
                "cascade_services": ["mission-control", "range-safety"],
                "description": "Thermal sensor calibration drifts outside acceptable bounds in the engine bay",
                "investigation_notes": (
                    "Root cause: thermocouple junction degradation or reference junction compensation "
                    "failure causes progressive drift in TC-47 readings. Check calibration epoch age — "
                    "epochs older than 4 hours under thermal cycling indicate recalibration is overdue. "
                    "Verify cold-junction compensation circuit on the signal conditioning board (SCB-4). "
                    "Cross-reference with adjacent sensors TC-48/49/50 to isolate single-sensor vs zone-wide drift. "
                    "Remediation: run TCS_RECAL procedure from MCC console, update calibration coefficients "
                    "in the sensor registry, and confirm readings converge within 2.5K tolerance band."
                ),
                "remediation_action": "recalibrate_engine",
                "error_message": "[TCS] TCS-DRIFT-CRITICAL: sensor=TC-47 reading={deviation}K nominal=310.2K deviation=+{deviation}K epoch={epoch}",
                "stack_trace": (
                    "== TELEMETRY FRAME DUMP == TCS THERMAL CONTROL SUBSYSTEM ==\n"
                    "TIMESTAMP: MET+00:04:12.337 | FRAME: 0x4A2F | SEQ: 18442\n"
                    "---------------------------------------------------------------\n"
                    "SENSOR    READING    NOMINAL    DELTA     STATUS\n"
                    "TC-47     {deviation}K     310.2K     +{deviation}K   **CRITICAL**\n"
                    "TC-48     311.4K     310.2K     +1.2K     NOMINAL\n"
                    "TC-49     309.8K     310.2K     -0.4K     NOMINAL\n"
                    "TC-50     310.0K     310.2K     -0.2K     NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "CALIBRATION BASELINE: epoch={epoch} | DRIFT THRESHOLD: 2.5K\n"
                    "TCS-DRIFT-CRITICAL: Sensor TC-47 exceeded drift threshold by +{deviation}K\n"
                    "ACTION: Recalibration required before engine ignition sequence"
                ),
            },
            2: {
                "name": "Fuel Pressure Anomaly",
                "subsystem": "propulsion",
                "vehicle_section": "fuel_tanks",
                "error_type": "PMS-PRESS-ANOMALY",
                "sensor_type": "pressure",
                "affected_services": ["fuel-system", "sensor-validator"],
                "cascade_services": ["mission-control", "range-safety"],
                "description": "Fuel tank pressure readings outside nominal range",
                "investigation_notes": (
                    "Root cause: helium pressurization regulator malfunction or cryogenic propellant "
                    "boil-off exceeding bleed valve capacity. Check He supply bottle pressure (nominal 2840PSI) "
                    "and regulator outlet (nominal 42PSI). If both LOX and RP-1 tanks are affected, suspect "
                    "common-mode regulator failure; if single tank, check individual fill/drain valve seat "
                    "integrity. Review CCTV for visible frost patterns indicating external leak. "
                    "Remediation: switch to backup pressurization regulator (REG-B), verify tank pressure "
                    "stabilizes within 60s, then safe the primary regulator for post-flight inspection."
                ),
                "remediation_action": "reset_fuel_system",
                "error_message": "[PMS] PMS-PRESS-ANOMALY: tank={tank_id} pressure={pressure}PSI nominal={expected_min}-{expected_max}PSI status=OUT_OF_BOUNDS",
                "stack_trace": (
                    "== TELEMETRY FRAME DUMP == PMS PROPULSION MGMT SYSTEM ==\n"
                    "TIMESTAMP: MET+00:04:12.891 | FRAME: 0x4A30 | SEQ: 18443\n"
                    "---------------------------------------------------------------\n"
                    "TANK      PRESSURE   NOM_MIN    NOM_MAX    STATUS\n"
                    "{tank_id}    {pressure}PSI   {expected_min}PSI     {expected_max}PSI     **ANOMALY**\n"
                    "LOX-2     265.3PSI   200PSI     310PSI     NOMINAL\n"
                    "RP1-1     248.7PSI   200PSI     310PSI     NOMINAL\n"
                    "RP1-2     251.2PSI   200PSI     310PSI     NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "PRESSURIZATION SYSTEM: He supply=2840PSI | reg_outlet=42PSI\n"
                    "PMS-PRESS-ANOMALY: Tank {tank_id} reading {pressure}PSI outside bounds\n"
                    "ACTION: Verify pressurization regulator and check for leak indications"
                ),
            },
            3: {
                "name": "Oxidizer Flow Rate Deviation",
                "subsystem": "propulsion",
                "vehicle_section": "engine_bay",
                "error_type": "PMS-OXIDIZER-FLOW",
                "sensor_type": "flow_rate",
                "affected_services": ["fuel-system", "sensor-validator"],
                "cascade_services": ["mission-control"],
                "description": "Oxidizer flow rate deviates from commanded value",
                "investigation_notes": (
                    "Root cause: turbopump cavitation due to LOX inlet temperature rise or inlet pressure "
                    "drop causing the pump to operate off its design curve. Verify LOX inlet temp (-183C nominal) "
                    "and inlet pressure (290PSI nominal). Check turbopump RPM vs commanded — a 0.5% shortfall "
                    "indicates bearing degradation. Inspect main oxidizer valve (MOV) position feedback for "
                    "actuator slop. Cross-check mixture ratio — flow deviation >3% risks engine-rich shutdown. "
                    "Remediation: adjust MOV trim position via PMS_FLOW_TRIM command, verify flow converges "
                    "within 3% tolerance band. If turbopump RPM is low, safe the engine for inspection."
                ),
                "remediation_action": "recalibrate_engine",
                "error_message": "[PMS] PMS-OXIDIZER-FLOW: measured={measured}kg/s commanded={commanded}kg/s delta={delta}% tolerance=3.0%",
                "stack_trace": (
                    "== TELEMETRY FRAME DUMP == PMS OXIDIZER FLOW CONTROLLER ==\n"
                    "TIMESTAMP: MET+00:04:13.112 | FRAME: 0x4A31 | SEQ: 18444\n"
                    "---------------------------------------------------------------\n"
                    "PARAMETER          VALUE      COMMANDED   DELTA\n"
                    "LOX_FLOW_RATE      {measured}kg/s   {commanded}kg/s    {delta}%\n"
                    "LOX_INLET_TEMP     -182.4C    -183.0C     +0.3%\n"
                    "LOX_INLET_PRESS    287.3PSI   290.0PSI    -0.9%\n"
                    "TURBOPUMP_RPM      31420      31500       -0.3%\n"
                    "---------------------------------------------------------------\n"
                    "FLOW TOLERANCE: 3.0% | MEASURED DELTA: {delta}%\n"
                    "PMS-OXIDIZER-FLOW: Flow deviation exceeds tolerance band\n"
                    "ACTION: Check turbopump inlet conditions and valve position feedback"
                ),
            },
            4: {
                "name": "GPS Multipath Interference",
                "subsystem": "guidance",
                "vehicle_section": "avionics",
                "error_type": "GNC-GPS-MULTIPATH",
                "sensor_type": "gps",
                "affected_services": ["navigation", "sensor-validator"],
                "cascade_services": ["mission-control", "range-safety"],
                "description": "GPS receiver detecting multipath signal interference",
                "investigation_notes": (
                    "Root cause: ground-bounce multipath from launch structure or nearby buildings corrupting "
                    "pseudorange measurements on low-elevation satellites. PDOP >6.0 indicates poor satellite "
                    "geometry — check which SVs are flagged for multipath (SNR anomalies on G04, G07, G15). "
                    "Verify antenna choke ring integrity and ground plane clearance. If >3 SVs affected, "
                    "the GPS solution degrades below navigation-grade accuracy. "
                    "Remediation: switch to IMU-primary navigation mode (GNC_NAV_MODE IMU_PRIMARY), mask "
                    "multipath-affected SVs via SVMASK command, and schedule GPS reacquisition after clearing "
                    "the launch structure multipath zone during ascent."
                ),
                "remediation_action": "recalibrate_navigation",
                "error_message": "[GNC] GNC-GPS-MULTIPATH: sv_count={num_satellites} pdop=8.7 threshold=6.0 uncertainty={uncertainty}m",
                "stack_trace": (
                    "== GN&C SYSTEM STATUS == GPS RECEIVER UNIT ==\n"
                    "TIMESTAMP: MET+00:04:14.005 | FRAME: 0x4A32 | SEQ: 18445\n"
                    "---------------------------------------------------------------\n"
                    "SV_ID   EL    AZ     SNR    MULTIPATH   USED\n"
                    "G04     45    127    42.1   YES         NO\n"
                    "G07     62    203    38.7   YES         NO\n"
                    "G09     28    315    44.2   NO          YES\n"
                    "G12     71    089    46.0   NO          YES\n"
                    "G15     33    241    31.4   YES         NO\n"
                    "---------------------------------------------------------------\n"
                    "AFFECTED SVs: {num_satellites} | PDOP: 8.7 (threshold 6.0)\n"
                    "POSITION UNCERTAINTY: {uncertainty}m | SOLUTION: DEGRADED\n"
                    "GNC-GPS-MULTIPATH: Multipath interference degrading navigation solution\n"
                    "ACTION: Switch to IMU-primary navigation mode"
                ),
            },
            5: {
                "name": "IMU Synchronization Loss",
                "subsystem": "guidance",
                "vehicle_section": "avionics",
                "error_type": "GNC-IMU-SYNC-LOSS",
                "sensor_type": "imu",
                "affected_services": ["navigation", "sensor-validator"],
                "cascade_services": ["mission-control", "range-safety"],
                "description": "Inertial measurement unit loses time synchronization",
                "investigation_notes": (
                    "Root cause: GPS 1PPS (one pulse-per-second) signal degradation or OCXO (oven-controlled "
                    "crystal oscillator) aging drift causing the IMU time base to decouple from mission time. "
                    "Check PPS signal integrity at the IMU input connector — signal amplitude <2.5V indicates "
                    "cable or driver failure. Verify OCXO-A temperature stability (nominal 42C +/-0.5C). "
                    "Single-axis drift suggests gyro bias shift on that axis; multi-axis drift points to clock source. "
                    "Remediation: initiate IMU realignment sequence (GNC_IMU_ALIGN), switch PPS source to "
                    "backup (PPS_SELECT GPS_1PPS_B), and verify drift converges below 3.0ms threshold. "
                    "If OCXO drift persists, switch to redundant IMU-B."
                ),
                "remediation_action": "reset_guidance",
                "error_message": "[GNC] GNC-IMU-SYNC-LOSS: axis={axis} drift={drift_ms}ms threshold={threshold_ms}ms sync_state=LOST",
                "stack_trace": (
                    "== GN&C SYSTEM STATUS == IMU SYNCHRONIZATION ==\n"
                    "TIMESTAMP: MET+00:04:14.228 | FRAME: 0x4A33 | SEQ: 18446\n"
                    "---------------------------------------------------------------\n"
                    "AXIS    DRIFT_MS   THRESHOLD   GYRO_BIAS    STATUS\n"
                    "{axis}       {drift_ms}ms    {threshold_ms}ms       +0.0021d/h   **SYNC_LOSS**\n"
                    "Y       0.42ms     3.0ms       -0.0008d/h   NOMINAL\n"
                    "Z       0.18ms     3.0ms       +0.0003d/h   NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "PPS_SOURCE: GPS_1PPS | CLOCK_REF: OCXO-A | TEMP: 42.1C\n"
                    "GNC-IMU-SYNC-LOSS: {axis}-axis clock drift {drift_ms}ms exceeds threshold\n"
                    "ACTION: Initiate IMU realignment sequence, verify PPS signal integrity"
                ),
            },
            6: {
                "name": "Star Tracker Alignment Fault",
                "subsystem": "guidance",
                "vehicle_section": "avionics",
                "error_type": "GNC-STAR-TRACKER-ALIGN",
                "sensor_type": "star_tracker",
                "affected_services": ["navigation", "sensor-validator"],
                "cascade_services": ["mission-control"],
                "description": "Star tracker optical alignment exceeds tolerance",
                "investigation_notes": (
                    "Root cause: boresight error from optical contamination (outgassing deposits on CCD window), "
                    "thermal distortion of the star tracker mounting bracket, or stale star catalog. Only 8/22 "
                    "catalog matches (minimum 12 required) suggests the field of view is shifted or obscured. "
                    "Check CCD temperature (-28.4C nominal, should be <-25C for low dark current). Verify "
                    "no thruster plume impingement on the optics baffle. Review attitude quaternion for sudden "
                    "discontinuities indicating a bracket shift. "
                    "Remediation: run optics bakeout heater cycle (ST_BAKEOUT 60s), reload backup star catalog "
                    "(ST_CATALOG LOAD B), and attempt recalibration (ST_RECAL). If boresight error persists, "
                    "switch to Star Tracker B and flag unit A for ground inspection."
                ),
                "remediation_action": "recalibrate_navigation",
                "error_message": "[GNC] GNC-STAR-TRACKER-ALIGN: boresight_error={error_arcsec}arcsec limit={limit_arcsec}arcsec catalog_match=DEGRADED",
                "stack_trace": (
                    "== GN&C SYSTEM STATUS == STAR TRACKER ASSEMBLY ==\n"
                    "TIMESTAMP: MET+00:04:14.501 | FRAME: 0x4A34 | SEQ: 18447\n"
                    "---------------------------------------------------------------\n"
                    "PARAMETER            VALUE        LIMIT      STATUS\n"
                    "BORESIGHT_ERROR      {error_arcsec}arcsec   {limit_arcsec}arcsec  **FAULT**\n"
                    "CATALOG_MATCHES      8/22         12 min     DEGRADED\n"
                    "CCD_TEMP             -28.4C       -30.0C     NOMINAL\n"
                    "INTEGRATION_TIME     250ms        500ms      NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "ATTITUDE_SOURCE: STAR_TRACKER_A | QUATERNION: [0.707, 0.0, 0.707, 0.0]\n"
                    "GNC-STAR-TRACKER-ALIGN: Boresight error {error_arcsec} arcsec exceeds {limit_arcsec} limit\n"
                    "ACTION: Verify optics cleanliness, attempt recalibration with backup catalog"
                ),
            },
            7: {
                "name": "Flight Termination System Check Failure",
                "subsystem": "safety",
                "vehicle_section": "vehicle_wide",
                "error_type": "RSO-FTS-CHECK-FAIL",
                "sensor_type": "safety_system",
                "affected_services": ["range-safety", "sensor-validator"],
                "cascade_services": ["mission-control"],
                "description": "Flight termination system self-check returning anomalous results",
                "investigation_notes": (
                    "Root cause: FTS self-test failure code (non-zero) indicates a fault in the command decoder, "
                    "safe/arm logic, or destruct initiator continuity circuit. Unit is in SAFED state with both "
                    "inhibits ON — no destruct risk, but a failed FTS is a mandatory launch hold per Range Safety "
                    "requirements. Check command uplink integrity (AES-256 encrypted link must show LOCKED decoder "
                    "status). Battery at 98.2% rules out power issues. Error code mapping: 0x01-0x0F = decoder, "
                    "0x10-0x1F = safe/arm relay, 0x20-0xFF = initiator circuit. "
                    "Remediation: power-cycle the FTS unit (RSO_FTS_POWER {unit} CYCLE), wait 30s for POST "
                    "completion, then re-run self-test (RSO_FTS_SELFTEST {unit}). If error persists, request "
                    "Range Safety Officer approval for FTS unit swap — requires pad access and minimum 2-hour "
                    "recertification window. FTS-B can serve as backup if FTS-A is non-recoverable."
                ),
                "remediation_action": "reset_safety_system",
                "error_message": "[RSO] RSO-FTS-CHECK-FAIL: unit={unit_id} self_test=FAIL code={error_code} arm_state=SAFED",
                "stack_trace": (
                    "== RANGE SAFETY STATUS == FLIGHT TERMINATION SYSTEM ==\n"
                    "TIMESTAMP: MET+00:04:20.001 | FRAME: 0x4A41 | SEQ: 18460\n"
                    "---------------------------------------------------------------\n"
                    "UNIT      SELF_TEST   CODE       ARM_STATE   BATTERY\n"
                    "{unit_id}     FAIL        {error_code}     SAFED       98.2%\n"
                    "FTS-B     PASS        0x00       SAFED       97.8%\n"
                    "---------------------------------------------------------------\n"
                    "COMMAND_LINK: UP | DECODER: LOCKED | ENCRYPT: AES-256\n"
                    "DESTRUCT_SAFE_ARM: SAFE | INHIBIT_1: ON | INHIBIT_2: ON\n"
                    "RSO-FTS-CHECK-FAIL: Unit {unit_id} self-test returned code {error_code}, expected 0x00\n"
                    "ACTION: Recycle FTS power, repeat self-test sequence"
                ),
            },
            8: {
                "name": "X-Band Packet Loss",
                "subsystem": "communications",
                "vehicle_section": "antenna_array",
                "error_type": "COMM-PACKET-LOSS",
                "sensor_type": "packet_integrity",
                "affected_services": ["comms-array", "sensor-validator"],
                "cascade_services": ["telemetry-relay", "mission-control"],
                "description": "X-band data link experiencing excessive packet loss",
                "investigation_notes": (
                    "Root cause: high bit error rate (BER 1.2e-04) causing FEC decoder failures — 847 frames "
                    "uncorrectable out of 2341 correction attempts. This BER level indicates either modulator "
                    "output power degradation, X-band antenna misalignment, or intermodulation interference from "
                    "adjacent RF systems. Check modulator constellation diagram for excessive phase noise. "
                    "Verify X-band antenna boresight alignment and servo tracking loop bandwidth. "
                    "Remediation: switch to backup X-band link (COMM_LINK_SELECT XB-SECONDARY), increase FEC "
                    "coding rate from 7/8 to 3/4 via COMM_FEC_RATE X-BAND 3/4 (trades bandwidth for robustness). "
                    "If antenna misalignment, run COMM_ANTENNA_CAL X-BAND to recalibrate servo offsets."
                ),
                "remediation_action": "reset_comms_link",
                "error_message": "[COMM] COMM-PACKET-LOSS: link={link_id} loss_rate={loss_pct}% threshold={threshold_pct}% frames_dropped=847",
                "stack_trace": (
                    "== LINK BUDGET ANALYSIS == X-BAND DATA LINK ==\n"
                    "TIMESTAMP: MET+00:04:15.221 | FRAME: 0x4A36 | SEQ: 18449\n"
                    "---------------------------------------------------------------\n"
                    "LINK         TX_RATE    RX_RATE    LOSS     STATUS\n"
                    "{link_id}   150Mbps    142Mbps    {loss_pct}%    **DEGRADED**\n"
                    "---------------------------------------------------------------\n"
                    "FEC_CORRECTIONS: 2341 | FEC_FAILURES: 847 | BER: 1.2e-04\n"
                    "THRESHOLD: {threshold_pct}% | MEASURED: {loss_pct}%\n"
                    "COMM-PACKET-LOSS: Packet loss {loss_pct}% exceeds threshold on link {link_id}\n"
                    "ACTION: Check antenna alignment, verify modulator output power"
                ),
            },
            9: {
                "name": "UHF Antenna Pointing Error",
                "subsystem": "communications",
                "vehicle_section": "antenna_array",
                "error_type": "COMM-ANTENNA-POINTING",
                "sensor_type": "antenna_position",
                "affected_services": ["comms-array", "sensor-validator"],
                "cascade_services": ["mission-control"],
                "description": "UHF antenna gimbal pointing error exceeds tolerance",
                "investigation_notes": (
                    "Root cause: gimbal servo controller failing to track TDRSS-W satellite — resolver feedback "
                    "indicates mechanical binding or servo amplifier saturation. Pointing errors in both azimuth "
                    "and elevation suggest the tracking algorithm lost lock, not a single-axis mechanical fault. "
                    "Check gimbal motor current (nominal 2.1A, >3.5A indicates binding). Verify resolver "
                    "calibration date — resolvers drift after thermal cycling. Inspect gimbal cable wrap for "
                    "interference at azimuth limits. "
                    "Remediation: reset gimbal controller (COMM_GIMBAL_RESET UHF-PRIMARY), run resolver "
                    "calibration (COMM_RESOLVER_CAL UHF), then command reacquisition of TDRSS-W target "
                    "(COMM_TRACK TDRSS-W AUTO). If binding persists, switch to UHF-SECONDARY gimbal."
                ),
                "remediation_action": "reconfigure_antenna",
                "error_message": "[COMM] COMM-ANTENNA-POINTING: az_error={az_error}deg el_error={el_error}deg gimbal=UHF-PRIMARY lock=LOST",
                "stack_trace": (
                    "== ANTENNA STATUS DUMP == UHF GIMBAL CONTROLLER ==\n"
                    "TIMESTAMP: MET+00:04:15.445 | FRAME: 0x4A37 | SEQ: 18450\n"
                    "---------------------------------------------------------------\n"
                    "AXIS         CMD       ACTUAL    ERROR     STATUS\n"
                    "AZIMUTH      127.3d    {az_error}d err  {az_error}deg   **FAULT**\n"
                    "ELEVATION    45.8d     {el_error}d err  {el_error}deg   **FAULT**\n"
                    "---------------------------------------------------------------\n"
                    "GIMBAL_TEMP: 38.2C | MOTOR_CURRENT: 2.1A | RESOLVER: VALID\n"
                    "TRACKING_MODE: AUTO | TARGET: TDRSS-W | LOCK: LOST\n"
                    "COMM-ANTENNA-POINTING: Pointing error az={az_error}deg el={el_error}deg\n"
                    "ACTION: Reset gimbal controller, verify resolver calibration"
                ),
            },
            10: {
                "name": "Payload Thermal Excursion",
                "subsystem": "payload",
                "vehicle_section": "payload_bay",
                "error_type": "PLD-THERMAL-EXCURSION",
                "sensor_type": "thermal",
                "affected_services": ["payload-monitor", "sensor-validator"],
                "cascade_services": ["mission-control"],
                "description": "Payload bay temperature outside safe operating range",
                "investigation_notes": (
                    "Root cause: coolant loop flow restriction or heater control circuit stuck-on condition. "
                    "Coolant flow at 2.4L/min is below nominal 3.2L/min — check pump outlet pressure and "
                    "look for air bubbles in the coolant loop (cavitation from improper ground fill). Verify "
                    "MLI (multi-layer insulation) blanket integrity — a torn or displaced blanket on the sun-facing "
                    "side causes rapid thermal excursion. Cross-reference with payload bay zones B/C/D — if only "
                    "one zone affected, suspect local heater controller failure rather than loop-wide issue. "
                    "Remediation: increase coolant pump speed (PLD_COOLANT_FLOW 4.0), disable zone heater if "
                    "stuck-on (PLD_HEATER zone OFF), and monitor temperature convergence over 5-minute window. "
                    "If MLI damage confirmed, notify payload integration team for EVA inspection."
                ),
                "remediation_action": "reset_payload_thermal",
                "error_message": "[PLD] PLD-THERMAL-EXCURSION: zone={zone} temp={temp}C safe_max={safe_max}C delta=+{deviation}C",
                "stack_trace": (
                    "== PAYLOAD CONTROLLER STATUS == THERMAL MANAGEMENT ==\n"
                    "TIMESTAMP: MET+00:04:16.002 | FRAME: 0x4A38 | SEQ: 18451\n"
                    "---------------------------------------------------------------\n"
                    "ZONE    TEMP     SAFE_MIN   SAFE_MAX   STATUS\n"
                    "{zone}       {temp}C   {safe_min}C     {safe_max}C     **EXCURSION**\n"
                    "B       22.1C    -10.0C     45.0C      NOMINAL\n"
                    "C       19.8C    -10.0C     45.0C      NOMINAL\n"
                    "D       24.3C    -10.0C     45.0C      NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "COOLANT_FLOW: 2.4L/min | HEATER_STATE: OFF | MLI_STATUS: INTACT\n"
                    "PLD-THERMAL-EXCURSION: Zone {zone} temperature {temp}C exceeds safe max {safe_max}C\n"
                    "ACTION: Increase coolant flow rate, verify MLI blanket integrity"
                ),
            },
            11: {
                "name": "Payload Vibration Anomaly",
                "subsystem": "payload",
                "vehicle_section": "payload_bay",
                "error_type": "PLD-VIBRATION-LIMIT",
                "sensor_type": "vibration",
                "affected_services": ["payload-monitor", "sensor-validator"],
                "cascade_services": ["mission-control", "range-safety"],
                "description": "Payload vibration levels exceed structural safety margins",
                "investigation_notes": (
                    "Root cause: resonance coupling between the launch vehicle structure and payload isolation "
                    "mounts at the observed frequency. Spectrum peaks at the primary frequency with harmonics at "
                    "88.4Hz and 142.7Hz suggest a structural mode, not random vibration. Check isolation mount "
                    "damper pressure (nominal 48.2PSI) — low pressure indicates a damper gas leak allowing "
                    "resonance transmission. Verify no loose payload adapter bolts (torque spec 45 ft-lb). "
                    "Remediation: activate vibration suppression mode (PLD_VIBRATION_DAMP ACTIVE), increase "
                    "damper pressure via PLD_DAMPER_PRESS +10PSI. If structural resonance confirmed, assess "
                    "whether launch loads will excite this mode — may require launch hold for structural review. "
                    "Log the vibration spectrum for post-flight coupled loads analysis."
                ),
                "remediation_action": "reset_payload_thermal",
                "error_message": "[PLD] PLD-VIBRATION-LIMIT: axis={axis} amplitude={amplitude}g frequency={frequency}Hz limit={limit}g",
                "stack_trace": (
                    "== VIBRATION SPECTRUM DATA == PAYLOAD ACCELEROMETER ==\n"
                    "TIMESTAMP: MET+00:04:16.334 | FRAME: 0x4A39 | SEQ: 18452\n"
                    "---------------------------------------------------------------\n"
                    "AXIS    FREQ_HZ    AMPLITUDE   LIMIT    STATUS\n"
                    "{axis}       {frequency}Hz    {amplitude}g       {limit}g    **EXCEEDED**\n"
                    "Y       45.2Hz     0.42g        1.5g     NOMINAL\n"
                    "Z       31.8Hz     0.67g        1.5g     NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "SPECTRUM_PEAKS: {frequency}Hz({amplitude}g), 88.4Hz(0.31g), 142.7Hz(0.18g)\n"
                    "ISOLATION_MOUNT: ACTIVE | DAMPER_PRESSURE: 48.2PSI\n"
                    "PLD-VIBRATION-LIMIT: {axis}-axis {amplitude}g at {frequency}Hz exceeds {limit}g structural limit\n"
                    "ACTION: Verify isolation mount dampers, check for resonance coupling"
                ),
            },
            12: {
                "name": "Pad Hydraulic Pressure Loss",
                "subsystem": "ground",
                "vehicle_section": "launch_pad",
                "error_type": "GND-HYDRAULIC-PRESS",
                "sensor_type": "hydraulic",
                "affected_services": ["ground-systems", "sensor-validator"],
                "cascade_services": ["mission-control"],
                "description": "Launch pad hydraulic system pressure dropping below minimum",
                "investigation_notes": (
                    "Root cause: hydraulic pump wear or external leak causing system pressure to drop below "
                    "2800PSI minimum. Reservoir level at 78% (nominal >90%) confirms fluid loss. Check filter "
                    "differential pressure (12PSI is borderline — >15PSI indicates clogged filter starving the pump). "
                    "Fluid temperature 42.1C is within limits but elevated — could indicate pump working harder "
                    "to compensate for internal leakage. Inspect hydraulic lines to the holddown clamps and "
                    "umbilical retract mechanisms for visible leaks. "
                    "Remediation: switch to backup hydraulic system (GND_HYD_SELECT HYD-B), isolate the affected "
                    "system (GND_HYD_ISOLATE {system}). Top off reservoir and replace filter element. If pump "
                    "wear suspected, check pump discharge pressure vs RPM curve. Pad operations cannot proceed "
                    "with hydraulic pressure below 2800PSI — holddown clamp release requires 3000PSI minimum."
                ),
                "remediation_action": "reset_ground_systems",
                "error_message": "[GND] GND-HYDRAULIC-PRESS: system={system_id} pressure={pressure}PSI min_required={min_pressure}PSI status=LOW",
                "stack_trace": (
                    "== GROUND SYSTEM DIAGNOSTIC == HYDRAULIC SYSTEM ==\n"
                    "TIMESTAMP: MET+00:04:18.667 | FRAME: 0x4A3E | SEQ: 18457\n"
                    "---------------------------------------------------------------\n"
                    "SYSTEM    PRESSURE   MIN_REQ    FLOW_RATE   STATUS\n"
                    "{system_id}     {pressure}PSI  {min_pressure}PSI   12.4GPM     **LOW_PRESS**\n"
                    "HYD-B     2920PSI    2800PSI    11.8GPM     NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "RESERVOIR_LEVEL: 78% | FLUID_TEMP: 42.1C | FILTER_DP: 12PSI\n"
                    "GND-HYDRAULIC-PRESS: System {system_id} pressure {pressure}PSI below minimum {min_pressure}PSI\n"
                    "ACTION: Check pump operation, inspect for hydraulic leaks"
                ),
            },
            13: {
                "name": "Relay Packet Corruption",
                "subsystem": "relay",
                "vehicle_section": "ground_network",
                "error_type": "RLY-PACKET-CORRUPT",
                "sensor_type": "data_integrity",
                "affected_services": ["telemetry-relay", "sensor-validator"],
                "cascade_services": ["mission-control"],
                "description": "Telemetry packets failing integrity checks during relay",
                "investigation_notes": (
                    "Root cause: burst error pattern on CRC32-C failures indicates physical layer issue — likely "
                    "NIC firmware bug, faulty SFP transceiver, or fiber micro-bend causing intermittent bit errors. "
                    "Burst errors (vs random) rule out EMI and point to a specific link segment. Check NIC "
                    "firmware version against known-good baseline. Inspect SFP optical power levels (TX and RX) "
                    "for the affected route — RX power below -18dBm indicates a dirty connector or damaged fiber. "
                    "Verify no recent rack maintenance that could have disturbed fiber runs. "
                    "Remediation: replace suspect SFP transceiver on the affected route, clean fiber connectors "
                    "with IPA wipes. If NIC firmware is outdated, schedule firmware update (NIC_FW_UPDATE {route}). "
                    "Enable relay packet retransmission (RLY_RETRANSMIT ENABLE) as interim mitigation."
                ),
                "remediation_action": "reset_relay_link",
                "error_message": "[RLY] RLY-PACKET-CORRUPT: route={route_id} corrupted={corrupted_count}/{total_count} crc_fail_rate={corrupted_count}pkt",
                "stack_trace": (
                    "== RELAY DIAGNOSTIC REPORT == INTEGRITY CHECKER ==\n"
                    "TIMESTAMP: MET+00:04:17.228 | FRAME: 0x4A3B | SEQ: 18454\n"
                    "---------------------------------------------------------------\n"
                    "ROUTE       TOTAL    CORRUPT   CRC_FAIL   STATUS\n"
                    "{route_id}   {total_count}     {corrupted_count}        {corrupted_count}         **CORRUPT**\n"
                    "GCP-AZ-01   487      0         0          NOMINAL\n"
                    "AWS-AZ-01   392      1         1          NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "CRC_TYPE: CRC32-C | WINDOW: 60s | ERROR_PATTERN: BURST\n"
                    "RLY-PACKET-CORRUPT: {corrupted_count} of {total_count} packets failed CRC on route {route_id}\n"
                    "ACTION: Check physical layer, verify NIC firmware version"
                ),
            },
            14: {
                "name": "Ground Power Bus Fault",
                "subsystem": "ground",
                "vehicle_section": "launch_pad",
                "error_type": "GND-POWER-BUS-FAULT",
                "sensor_type": "electrical",
                "affected_services": ["ground-systems", "sensor-validator"],
                "cascade_services": ["mission-control", "fuel-system"],
                "description": "Launch pad power bus voltage irregularity detected",
                "investigation_notes": (
                    "Root cause: transformer tap setting drift or load imbalance on the affected power bus. "
                    "Voltage deviation >8% from 120V nominal can cause sensitive avionics to trip undervoltage "
                    "lockout. Check breaker panel for tripped breakers or loose connections — thermal imaging "
                    "recommended on the distribution panel. Verify UPS is online (not on bypass) and generator "
                    "auto-transfer switch is in AUTO mode. Compare bus current draw with other buses — 42.3A vs "
                    "38.7A/41.1A on B/C suggests possible ground fault or excessive load on bus A. "
                    "Remediation: adjust transformer tap setting (GND_TAP_SELECT {bus} +2), reset tripped "
                    "breakers after verifying no short circuit. If persistent, switch critical loads to backup "
                    "bus (GND_BUS_TRANSFER {bus} BACKUP) and dispatch electrical technician to the pad."
                ),
                "remediation_action": "reset_ground_power",
                "error_message": "[GND] GND-POWER-BUS-FAULT: bus={bus_id} voltage={voltage}V nominal={nominal_v}V deviation={deviation_pct}%",
                "stack_trace": (
                    "== GROUND SYSTEM DIAGNOSTIC == POWER DISTRIBUTION ==\n"
                    "TIMESTAMP: MET+00:04:18.002 | FRAME: 0x4A3C | SEQ: 18455\n"
                    "---------------------------------------------------------------\n"
                    "BUS      VOLTAGE   NOMINAL   DEVIATION   CURRENT   STATUS\n"
                    "{bus_id}    {voltage}V   {nominal_v}V   {deviation_pct}%       42.3A     **FAULT**\n"
                    "PWR-B    119.8V    120.0V    0.2%        38.7A     NOMINAL\n"
                    "PWR-C    120.1V    120.0V    0.1%        41.1A     NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "UPS_STATUS: ONLINE | GENERATOR: STANDBY | TRANSFER_SW: AUTO\n"
                    "GND-POWER-BUS-FAULT: Bus {bus_id} voltage {voltage}V deviates {deviation_pct}% from nominal\n"
                    "ACTION: Check breaker panel, verify transformer tap settings"
                ),
            },
            15: {
                "name": "Range Safety Tracking Loss",
                "subsystem": "safety",
                "vehicle_section": "vehicle_wide",
                "error_type": "RSO-TRACKING-LOSS",
                "sensor_type": "radar_tracking",
                "affected_services": ["range-safety", "sensor-validator"],
                "cascade_services": ["mission-control", "navigation"],
                "description": "Range safety radar losing vehicle track",
                "investigation_notes": (
                    "Root cause: tracking radar lost skin-track on the vehicle — track fusion is in COAST mode "
                    "with 72% prediction confidence, meaning the system is dead-reckoning based on last known "
                    "state. RCS (radar cross-section) at 12.4 dBsm is adequate, so loss is likely from antenna "
                    "servo tracking loop dropout, RF interference in the radar band, or physical obstruction "
                    "in the radar line-of-sight. Check for construction cranes, aircraft, or weather in the "
                    "radar corridor. Other radars (RDR-2, RDR-3) still tracking confirms single-radar fault. "
                    "Remediation: command radar reacquisition (RSO_RADAR_REACQ {radar} TARGET VEHICLE), check "
                    "antenna servo error logs for tracking loop faults (RSO_RADAR_SERVO_STATUS {radar}). If "
                    "RF interference suspected, run spectrum analyzer sweep (RSO_SPECTRUM_SCAN {radar} BAND). "
                    "Range Safety requires 2-of-3 radars tracking for launch commit — verify RDR-2/RDR-3 health."
                ),
                "remediation_action": "reset_safety_system",
                "error_message": "[RSO] RSO-TRACKING-LOSS: radar={radar_id} gap={gap_ms}ms max_allowed={max_gap_ms}ms track_state=COAST",
                "stack_trace": (
                    "== RANGE SAFETY STATUS == TRACKING RADAR NETWORK ==\n"
                    "TIMESTAMP: MET+00:04:20.334 | FRAME: 0x4A42 | SEQ: 18461\n"
                    "---------------------------------------------------------------\n"
                    "RADAR     TRACK_GAP   MAX_GAP   RCS_dBsm   STATUS\n"
                    "{radar_id}     {gap_ms}ms    {max_gap_ms}ms    12.4       **TRACK_LOSS**\n"
                    "RDR-2     0ms         250ms     14.1       TRACKING\n"
                    "RDR-3     0ms         250ms     11.8       TRACKING\n"
                    "---------------------------------------------------------------\n"
                    "FUSION_STATE: COAST | PREDICT_CONF: 72% | CORRIDOR: WITHIN\n"
                    "RSO-TRACKING-LOSS: Radar {radar_id} lost track for {gap_ms}ms, max allowed {max_gap_ms}ms\n"
                    "ACTION: Verify radar antenna, check for RF interference"
                ),
            },
            16: {
                "name": "Cross-Cloud Relay Latency",
                "subsystem": "relay",
                "vehicle_section": "ground_network",
                "error_type": "RLY-LATENCY-CRITICAL",
                "sensor_type": "network_latency",
                "affected_services": ["telemetry-relay", "sensor-validator"],
                "cascade_services": ["mission-control", "comms-array"],
                "description": "Cross-cloud telemetry relay latency exceeds acceptable bounds",
                "investigation_notes": (
                    "Root cause: relay buffer saturation at 87% utilization causing queuing delay, compounded by "
                    "342 retransmits indicating packet loss on the inter-cloud link. High buffer utilization "
                    "points to a congestion event — either a telemetry data burst from upstream sensors or a "
                    "bandwidth reduction on the cross-cloud peering link. Check if the affected route has a "
                    "degraded BGP path (longer AS path) or if cloud provider maintenance reduced link capacity. "
                    "42ms jitter on the nominal routes confirms the issue is isolated to the affected hop. "
                    "Remediation: failover to backup route (RLY_ROUTE_FAILOVER {source}->{dest} BACKUP), flush "
                    "relay buffers (RLY_BUFFER_FLUSH), and enable QoS priority tagging for telemetry frames "
                    "(RLY_QOS TELEMETRY HIGH). Monitor latency convergence below 200ms threshold."
                ),
                "remediation_action": "reset_relay_link",
                "error_message": "[RLY] RLY-LATENCY-CRITICAL: hop={source_cloud}->{dest_cloud} latency={latency_ms}ms threshold={threshold_ms_relay}ms",
                "stack_trace": (
                    "== RELAY DIAGNOSTIC REPORT == CROSS-CLOUD ROUTER ==\n"
                    "TIMESTAMP: MET+00:04:17.001 | FRAME: 0x4A3A | SEQ: 18453\n"
                    "---------------------------------------------------------------\n"
                    "ROUTE                LATENCY    THRESHOLD   JITTER    STATUS\n"
                    "{source_cloud}->{dest_cloud}         {latency_ms}ms    {threshold_ms_relay}ms      42ms      **CRITICAL**\n"
                    "gcp->azure           38ms       200ms       5ms       NOMINAL\n"
                    "aws->azure           45ms       200ms       8ms       NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "ROUTE TABLE: 6 active | BUFFER_UTIL: 87% | RETRANSMITS: 342\n"
                    "RLY-LATENCY-CRITICAL: {source_cloud}->{dest_cloud} latency {latency_ms}ms exceeds {threshold_ms_relay}ms\n"
                    "ACTION: Check intermediate hops, consider failover to backup route"
                ),
            },
            17: {
                "name": "Sensor Validation Pipeline Stall",
                "subsystem": "validation",
                "vehicle_section": "ground_network",
                "error_type": "VV-PIPELINE-HALT",
                "sensor_type": "pipeline_health",
                "affected_services": ["sensor-validator"],
                "cascade_services": ["mission-control", "telemetry-relay"],
                "description": "Sensor validation pipeline stalled, readings not being validated",
                "investigation_notes": (
                    "Root cause: JVM garbage collection pressure causing stop-the-world pauses that stall the "
                    "validation pipeline. Heap usage at 89% with GC pause of 120ms confirms the V&V processor "
                    "is thrashing between GC cycles. All 8 worker threads are busy but throughput has collapsed "
                    "because each thread blocks during GC pauses. Queue depth climbing rapidly indicates ingest "
                    "rate exceeds processing capacity during GC storms. Check for memory leaks in the calibration "
                    "correlation stage — retained object count should be <500K per checkpoint. "
                    "Remediation: trigger manual GC compaction (VV_GC_COMPACT), then increase JVM heap size "
                    "(VV_HEAP_RESIZE 12G) to reduce GC frequency. If queue depth exceeds 5000, enable upstream "
                    "backpressure (VV_BACKPRESSURE ENABLE) to prevent data loss. For long-term fix, migrate to "
                    "G1GC with -XX:MaxGCPauseMillis=20 to cap pause times."
                ),
                "remediation_action": "reset_validation_pipeline",
                "error_message": "[VV] VV-PIPELINE-HALT: stage=validation queue_depth={queue_depth} rate={rate}/s threshold={min_rate}/s",
                "stack_trace": (
                    "== VALIDATION PIPELINE STATUS == V&V PROCESSOR ==\n"
                    "TIMESTAMP: MET+00:04:19.001 | FRAME: 0x4A3F | SEQ: 18458\n"
                    "---------------------------------------------------------------\n"
                    "STAGE          QUEUE    RATE      THRESHOLD   STATUS\n"
                    "INGEST         {queue_depth}     {rate}/s    {min_rate}/s     **STALLED**\n"
                    "CALIBRATION    12       52.1/s    50.0/s      NOMINAL\n"
                    "CORRELATION    8        48.7/s    45.0/s      NOMINAL\n"
                    "OUTPUT         3        51.2/s    50.0/s      NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "WORKER_THREADS: 8/8 busy | HEAP_USAGE: 89% | GC_PAUSE: 120ms\n"
                    "VV-PIPELINE-HALT: Processing rate {rate}/s below {min_rate}/s, queue depth {queue_depth}\n"
                    "ACTION: Scale worker pool, investigate upstream data burst"
                ),
            },
            18: {
                "name": "Calibration Epoch Mismatch",
                "subsystem": "validation",
                "vehicle_section": "ground_network",
                "error_type": "VV-EPOCH-DRIFT",
                "sensor_type": "calibration",
                "affected_services": ["sensor-validator"],
                "cascade_services": ["mission-control", "fuel-system", "navigation"],
                "description": "Sensor calibration epoch does not match expected reference",
                "investigation_notes": (
                    "Root cause: clock synchronization failure between the sensor's onboard time reference and "
                    "the ground NTP stratum-1 server. The sensor's calibration table was generated at a different "
                    "epoch than the current mission reference time, causing all calibrated readings to apply stale "
                    "correction coefficients. GPS_UTC reference clock shows LOCKED but the sensor's local RTC "
                    "may have drifted during a power cycle or brown-out event. Delta between actual and expected "
                    "epochs >3600s indicates the sensor missed at least one calibration upload cycle. "
                    "Remediation: force NTP resynchronization on the affected sensor (VV_NTP_SYNC {sensor_id}), "
                    "then reload the current calibration epoch table (VV_EPOCH_RELOAD {sensor_id} FROM_REFERENCE). "
                    "Verify the sensor's RTC battery voltage (>2.8V required). After resync, confirm epoch delta "
                    "is <1s and downstream calibrated readings match cross-check sensors."
                ),
                "remediation_action": "resync_calibration_epoch",
                "error_message": "[VV] VV-EPOCH-DRIFT: sensor={sensor_id} actual_epoch={actual_epoch} expected_epoch={expected_epoch} drift=CRITICAL",
                "stack_trace": (
                    "== VALIDATION PIPELINE STATUS == EPOCH CHECKER ==\n"
                    "TIMESTAMP: MET+00:04:19.334 | FRAME: 0x4A40 | SEQ: 18459\n"
                    "---------------------------------------------------------------\n"
                    "SENSOR        ACTUAL_EPOCH    EXPECTED_EPOCH   DELTA_SEC   STATUS\n"
                    "{sensor_id}   {actual_epoch}       {expected_epoch}        DRIFT       **MISMATCH**\n"
                    "SENS-2001     1738100800      1738100800       0           NOMINAL\n"
                    "SENS-3042     1738100800      1738100800       0           NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "REFERENCE_CLOCK: GPS_UTC | NTP_STRATUM: 1 | SYNC_STATUS: LOCKED\n"
                    "VV-EPOCH-DRIFT: Sensor {sensor_id} epoch {actual_epoch} vs expected {expected_epoch}\n"
                    "ACTION: Re-synchronize sensor calibration tables from reference"
                ),
            },
            19: {
                "name": "S-Band Signal Degradation",
                "subsystem": "communications",
                "vehicle_section": "antenna_array",
                "error_type": "COMM-SIGNAL-DEGRAD",
                "sensor_type": "rf_signal",
                "affected_services": ["comms-array", "sensor-validator"],
                "cascade_services": ["mission-control", "telemetry-relay"],
                "description": "S-band communication signal strength below minimum threshold",
                "investigation_notes": (
                    "Root cause: link budget degradation from reduced EIRP (38.2dBW vs 42.0dBW nominal) combined "
                    "with antenna gain loss (34.1dBi vs 36.0dBi). EIRP drop indicates transmitter power amplifier "
                    "(SSPA) degradation or waveguide loss. Antenna gain loss suggests feed horn misalignment or "
                    "reflector surface distortion. Check atmospheric loss — 0.8dB vs 0.5dB nominal may indicate "
                    "rain fade on the TDRSS link. Verify S-band transponder AGC levels and lock indicator. "
                    "Remediation: increase transmit power via COMM_TX_POWER S-BAND +4dB, switch to backup "
                    "antenna feed if available (COMM_FEED_SELECT S-BAND BACKUP). If rain fade suspected, "
                    "request TDRSS handover to alternate ground station with clearer weather."
                ),
                "remediation_action": "reset_comms_link",
                "error_message": "[COMM] COMM-SIGNAL-DEGRAD: link=S-band eb_no={snr_db}dB threshold={min_snr_db}dB channel={rf_channel}",
                "stack_trace": (
                    "== LINK BUDGET ANALYSIS == S-BAND DOWNLINK ==\n"
                    "TIMESTAMP: MET+00:04:15.003 | FRAME: 0x4A35 | SEQ: 18448\n"
                    "---------------------------------------------------------------\n"
                    "PARAMETER            VALUE      NOMINAL    STATUS\n"
                    "EIRP                 38.2dBW    42.0dBW    DEGRADED\n"
                    "FREE_SPACE_LOSS      -157.3dB   -157.3dB   --\n"
                    "ATMOSPHERIC_LOSS     -0.8dB     -0.5dB     MARGINAL\n"
                    "ANTENNA_GAIN         34.1dBi    36.0dBi    DEGRADED\n"
                    "Eb/No                {snr_db}dB     {min_snr_db}dB     **BELOW_THRESHOLD**\n"
                    "CHANNEL              {rf_channel}        --         --\n"
                    "---------------------------------------------------------------\n"
                    "LINK MARGIN: -{snr_db}dB | REQUIRED: +3.0dB\n"
                    "COMM-SIGNAL-DEGRAD: S-band Eb/No below threshold on channel {rf_channel}\n"
                    "ACTION: Increase transmit power or switch to backup antenna feed"
                ),
            },
            20: {
                "name": "Weather Station Data Gap",
                "subsystem": "ground",
                "vehicle_section": "launch_pad",
                "error_type": "GND-WEATHER-GAP",
                "sensor_type": "weather",
                "affected_services": ["ground-systems", "sensor-validator"],
                "cascade_services": ["mission-control", "range-safety"],
                "description": "Weather monitoring station reporting data gaps",
                "investigation_notes": (
                    "Root cause: RS-422 serial communication link timeout between the weather station and ground "
                    "data system. Gap >15s violates launch commit criteria (LCC) for weather data continuity. "
                    "Check RS-422 cable run for damage (common failure: cable crushed by pad equipment). Verify "
                    "station processor is running (LED status panel on station enclosure). If station is solar-powered, "
                    "check battery voltage — overcast conditions can deplete backup batteries. Compare with "
                    "other stations (WX-SOUTH, WX-EAST, WX-WEST) to rule out ground data system receiver failure. "
                    "Remediation: dispatch field technician to the affected station for physical inspection. "
                    "Restart station processor via remote power cycle (GND_WX_RESET {station}). If RS-422 link "
                    "is down, switch to backup Ethernet path (GND_WX_LINK {station} ETH). Weather LCC waiver "
                    "requires Range Safety Officer approval if gap exceeds 60s."
                ),
                "remediation_action": "reset_ground_systems",
                "error_message": "[GND] GND-WEATHER-GAP: station={station_id} gap={gap_seconds}s max_allowed={max_gap}s link=TIMEOUT",
                "stack_trace": (
                    "== GROUND SYSTEM DIAGNOSTIC == WEATHER NETWORK ==\n"
                    "TIMESTAMP: MET+00:04:18.334 | FRAME: 0x4A3D | SEQ: 18456\n"
                    "---------------------------------------------------------------\n"
                    "STATION     LAST_DATA   GAP_SEC   MAX_GAP   STATUS\n"
                    "{station_id}   {gap_seconds}s ago    {gap_seconds}s       {max_gap}s       **DATA_GAP**\n"
                    "WX-SOUTH    2s ago      2s        15s       NOMINAL\n"
                    "WX-EAST     1s ago      1s        15s       NOMINAL\n"
                    "WX-WEST     3s ago      3s        15s       NOMINAL\n"
                    "---------------------------------------------------------------\n"
                    "NETWORK: 4 stations | PROTOCOL: METAR/SPECI | LINK: RS-422\n"
                    "GND-WEATHER-GAP: Station {station_id} no data for {gap_seconds}s, max allowed {max_gap}s\n"
                    "ACTION: Check station comm link, dispatch field technician"
                ),
            },
        }

    # ── Topology ──────────────────────────────────────────────────────

    @property
    def service_topology(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "mission-control": [
                ("fuel-system", "/api/v1/fuel/status", "GET"),
                ("fuel-system", "/api/v1/fuel/pressure", "GET"),
                ("navigation", "/api/v1/nav/position", "GET"),
                ("navigation", "/api/v1/nav/trajectory", "POST"),
                ("ground-systems", "/api/v1/ground/weather", "GET"),
                ("ground-systems", "/api/v1/ground/power", "GET"),
                ("comms-array", "/api/v1/comms/status", "GET"),
                ("telemetry-relay", "/api/v1/relay/health", "GET"),
            ],
            "navigation": [
                ("sensor-validator", "/api/v1/validate/imu", "POST"),
                ("sensor-validator", "/api/v1/validate/gps", "POST"),
                ("sensor-validator", "/api/v1/validate/star-tracker", "POST"),
            ],
            "fuel-system": [
                ("sensor-validator", "/api/v1/validate/pressure", "POST"),
                ("sensor-validator", "/api/v1/validate/thermal", "POST"),
                ("sensor-validator", "/api/v1/validate/flow-rate", "POST"),
            ],
            "payload-monitor": [
                ("sensor-validator", "/api/v1/validate/vibration", "POST"),
                ("sensor-validator", "/api/v1/validate/payload-thermal", "POST"),
            ],
            "range-safety": [
                ("navigation", "/api/v1/nav/position", "GET"),
                ("comms-array", "/api/v1/comms/tracking", "GET"),
            ],
            "telemetry-relay": [
                ("comms-array", "/api/v1/comms/relay", "POST"),
            ],
        }

    @property
    def entry_endpoints(self) -> dict[str, list[tuple[str, str]]]:
        return {
            "mission-control": [
                ("/api/v1/mission/status", "GET"),
                ("/api/v1/mission/countdown", "GET"),
                ("/api/v1/mission/telemetry", "POST"),
            ],
            "fuel-system": [("/api/v1/fuel/monitor", "POST")],
            "navigation": [("/api/v1/nav/compute", "POST")],
            "ground-systems": [("/api/v1/ground/monitor", "POST")],
            "comms-array": [("/api/v1/comms/poll", "POST")],
            "payload-monitor": [("/api/v1/payload/scan", "POST")],
            "sensor-validator": [("/api/v1/validate/batch", "POST")],
            "telemetry-relay": [("/api/v1/relay/forward", "POST")],
            "range-safety": [("/api/v1/safety/check", "POST")],
        }

    @property
    def db_operations(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "mission-control": [
                ("SELECT", "mission_events", "SELECT * FROM mission_events WHERE phase = ? ORDER BY timestamp DESC LIMIT 100"),
                ("INSERT", "telemetry_readings", "INSERT INTO telemetry_readings (service, metric, value, ts) VALUES (?, ?, ?, NOW())"),
            ],
            "fuel-system": [
                ("SELECT", "sensor_data", "SELECT reading, baseline FROM sensor_data WHERE sensor_type = 'pressure' AND ts > NOW() - INTERVAL 5 MINUTE"),
                ("UPDATE", "sensor_registry", "UPDATE sensor_registry SET last_reading = ?, last_seen = NOW() WHERE sensor_id = ?"),
            ],
            "navigation": [
                ("SELECT", "calibration_epochs", "SELECT epoch, baseline FROM calibration_epochs WHERE sensor_type IN ('imu', 'gps', 'star_tracker')"),
            ],
            "sensor-validator": [
                ("SELECT", "validation_results", "SELECT * FROM validation_results WHERE sensor_id = ? AND validated_at > NOW() - INTERVAL 1 MINUTE"),
                ("INSERT", "validation_results", "INSERT INTO validation_results (sensor_id, result, confidence, validated_at) VALUES (?, ?, ?, NOW())"),
            ],
            "ground-systems": [
                ("SELECT", "weather_stations", "SELECT station_id, temp, wind_speed, visibility FROM weather_stations WHERE last_update > NOW() - INTERVAL 30 SECOND"),
            ],
        }

    # ── Infrastructure ────────────────────────────────────────────────

    @property
    def hosts(self) -> list[dict[str, Any]]:
        return [
            {
                "host.name": "nova7-aws-host-01",
                "host.id": "i-0a1b2c3d4e5f67890",
                "host.arch": "amd64",
                "host.type": "m5.xlarge",
                "host.image.id": "ami-0abcdef1234567890",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8175M CPU @ 2.50GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "4",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.0.1.42", "172.16.0.10"],
                "host.mac": ["0a:1b:2c:3d:4e:5f", "0a:1b:2c:3d:4e:60"],
                "os.type": "linux",
                "os.description": "Amazon Linux 2023.6.20250115",
                "cloud.provider": "aws",
                "cloud.platform": "aws_ec2",
                "cloud.region": "us-east-1",
                "cloud.availability_zone": "us-east-1a",
                "cloud.account.id": "123456789012",
                "cloud.instance.id": "i-0a1b2c3d4e5f67890",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 200 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "nova7-gcp-host-01",
                "host.id": "5649812345678901234",
                "host.arch": "amd64",
                "host.type": "e2-standard-4",
                "host.image.id": "projects/debian-cloud/global/images/debian-12-bookworm-v20250115",
                "host.cpu.model.name": "Intel(R) Xeon(R) CPU @ 2.20GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "7",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.128.0.15", "10.128.0.16"],
                "host.mac": ["42:01:0a:80:00:0f", "42:01:0a:80:00:10"],
                "os.type": "linux",
                "os.description": "Debian GNU/Linux 12 (bookworm)",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "us-central1",
                "cloud.availability_zone": "us-central1-a",
                "cloud.account.id": "nova7-project-prod",
                "cloud.instance.id": "5649812345678901234",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 100 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "nova7-azure-host-01",
                "host.id": "/subscriptions/abc-def/resourceGroups/nova7-rg/providers/Microsoft.Compute/virtualMachines/nova7-vm-01",
                "host.arch": "amd64",
                "host.type": "Standard_D4s_v3",
                "host.image.id": "Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "106",
                "host.cpu.stepping": "6",
                "host.cpu.cache.l2.size": 1310720,
                "host.ip": ["10.1.0.4", "10.1.0.5"],
                "host.mac": ["00:0d:3a:5a:4b:3c", "00:0d:3a:5a:4b:3d"],
                "os.type": "linux",
                "os.description": "Ubuntu 22.04.5 LTS",
                "cloud.provider": "azure",
                "cloud.platform": "azure_vm",
                "cloud.region": "eastus",
                "cloud.availability_zone": "eastus-1",
                "cloud.account.id": "abc-def-ghi-jkl",
                "cloud.instance.id": "nova7-vm-01",
                "cpu_count": 4,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 128 * 1024 * 1024 * 1024,
            },
        ]

    @property
    def k8s_clusters(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "nova7-eks-cluster",
                "provider": "aws",
                "platform": "aws_eks",
                "region": "us-east-1",
                "zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
                "os_description": "Amazon Linux 2",
                "services": ["mission-control", "fuel-system", "ground-systems"],
            },
            {
                "name": "nova7-gke-cluster",
                "provider": "gcp",
                "platform": "gcp_gke",
                "region": "us-central1",
                "zones": ["us-central1-a", "us-central1-b", "us-central1-c"],
                "os_description": "Container-Optimized OS",
                "services": ["navigation", "comms-array", "payload-monitor"],
            },
            {
                "name": "nova7-aks-cluster",
                "provider": "azure",
                "platform": "azure_aks",
                "region": "eastus",
                "zones": ["eastus-1", "eastus-2", "eastus-3"],
                "os_description": "Ubuntu 22.04 LTS",
                "services": ["sensor-validator", "telemetry-relay", "range-safety"],
            },
        ]

    # ── Theme ─────────────────────────────────────────────────────────

    @property
    def theme(self) -> UITheme:
        return UITheme(
            bg_primary="#0a0a0a",
            bg_secondary="#111111",
            bg_tertiary="#1a1a1a",
            accent_primary="#00ff41",
            accent_secondary="#00cc33",
            text_primary="#00ff41",
            text_secondary="#008f11",
            text_accent="#00ff41",
            status_nominal="#00ff41",
            status_warning="#ffaa00",
            status_critical="#ff0040",
            status_info="#00aaff",
            font_family="'JetBrains Mono', 'Fira Code', monospace",
            font_mono="'JetBrains Mono', 'Fira Code', monospace",
            scanline_effect=True,
            chaos_title="Chaos Controller",
            service_label="System",
            channel_label="Channel",
        )

    @property
    def nominal_label(self) -> str:
        return "NOMINAL"

    @property
    def countdown_config(self) -> CountdownConfig:
        return CountdownConfig(
            enabled=True,
            start_seconds=600,
            speed=1.0,
            phases={
                "PRE-LAUNCH": (300, 9999),
                "COUNTDOWN": (60, 300),
                "FINAL-COUNTDOWN": (0, 60),
                "LAUNCH": (0, 0),
            },
        )

    # ── Agent Config ──────────────────────────────────────────────────

    @property
    def agent_config(self) -> dict[str, Any]:
        return {
            "id": "nova7-launch-analyst",
            "name": "Launch Anomaly Analyst",
            "assessment_tool_name": "launch_safety_assessment",
            "system_prompt": (
                "You are the NOVA-7 Launch Anomaly Analyst, an expert AI assistant for "
                "space launch mission operations. You help mission controllers investigate "
                "anomalies, analyze telemetry data, and provide root cause analysis for "
                "fault conditions across 9 space systems. "
                "You have deep expertise in spacecraft propulsion telemetry, GN&C systems, "
                "TDRSS/S-band/X-band communications, payload environmental control, "
                "cross-cloud relay networks, ground support equipment, sensor validation "
                "pipelines, and range safety systems. "
                "When investigating incidents, search for these subsystem identifiers in logs: "
                "Propulsion faults (TCS-DRIFT-CRITICAL, PMS-PRESS-ANOMALY, PMS-OXIDIZER-FLOW), "
                "GN&C faults (GNC-GPS-MULTIPATH, GNC-IMU-SYNC-LOSS, GNC-STAR-TRACKER-ALIGN), "
                "Communications faults (COMM-SIGNAL-DEGRAD, COMM-PACKET-LOSS, COMM-ANTENNA-POINTING), "
                "Payload faults (PLD-THERMAL-EXCURSION, PLD-VIBRATION-LIMIT), "
                "Relay faults (RLY-LATENCY-CRITICAL, RLY-PACKET-CORRUPT), "
                "Ground faults (GND-POWER-BUS-FAULT, GND-WEATHER-GAP, GND-HYDRAULIC-PRESS), "
                "Validation faults (VV-PIPELINE-HALT, VV-EPOCH-DRIFT), "
                "and Range Safety faults (RSO-FTS-CHECK-FAIL, RSO-TRACKING-LOSS). "
                "Log messages are in body.text — NEVER search the body field alone."
            ),
        }

    @property
    def assessment_tool_config(self) -> dict[str, Any]:
        return {
            "id": "launch_safety_assessment",
            "description": (
                "Comprehensive launch safety assessment. Evaluates all "
                "services against launch readiness criteria. Returns data "
                "for GO/NO-GO evaluation. "
                "Log message field: body.text (never use 'body' alone)."
            ),
        }

    @property
    def knowledge_base_docs(self) -> list[dict[str, Any]]:
        return []  # Populated by deployer from channel_registry

    # ── Service Classes ───────────────────────────────────────────────

    def get_service_classes(self) -> list[type]:
        from scenarios.space.services.comms_array import CommsArrayService
        from scenarios.space.services.fuel_system import FuelSystemService
        from scenarios.space.services.ground_systems import GroundSystemsService
        from scenarios.space.services.mission_control import MissionControlService
        from scenarios.space.services.navigation import NavigationService
        from scenarios.space.services.payload_monitor import PayloadMonitorService
        from scenarios.space.services.range_safety import RangeSafetyService
        from scenarios.space.services.sensor_validator import SensorValidatorService
        from scenarios.space.services.telemetry_relay import TelemetryRelayService

        return [
            MissionControlService,
            FuelSystemService,
            GroundSystemsService,
            NavigationService,
            CommsArrayService,
            PayloadMonitorService,
            SensorValidatorService,
            TelemetryRelayService,
            RangeSafetyService,
        ]

    # ── Trace Attributes & RCA ───────────────────────────────────────

    def get_trace_attributes(self, service_name: str, rng) -> dict:
        met_s = int(time.time()) % 86400
        base = {
            "mission.phase": rng.choice(["pre-launch", "countdown", "ascent", "orbital-insertion"]),
            "mission.elapsed_time_s": met_s,
        }
        svc_attrs = {
            "fuel-system": {
                "propulsion.engine_id": rng.choice(["E1-MAIN", "E2-MAIN", "E3-VERNIER"]),
                "propulsion.chamber_pressure_psi": round(rng.uniform(2400, 2650), 1),
            },
            "navigation": {
                "gnc.nav_mode": rng.choice(["GPS_PRIMARY", "IMU_PRIMARY", "STAR_TRACKER", "BLENDED"]),
                "orbit.altitude_km": round(rng.uniform(180, 420), 1),
            },
            "comms-array": {
                "comms.link_type": rng.choice(["S-BAND", "X-BAND", "UHF"]),
                "comms.signal_margin_db": round(rng.uniform(2.0, 12.0), 1),
            },
            "mission-control": {
                "mcc.operator_console": rng.choice(["FLIGHT", "CAPCOM", "GNC", "PROP", "EECOM"]),
                "mcc.telemetry_rate_hz": rng.choice([1, 5, 10, 25]),
            },
            "ground-systems": {
                "ground.pad_id": rng.choice(["LC-39A", "LC-39B", "SLC-40"]),
                "ground.weather_go": rng.choice([True, True, True, False]),
            },
            "payload-monitor": {
                "payload.bay_temp_c": round(rng.uniform(18.0, 28.0), 1),
                "payload.vibration_grms": round(rng.uniform(0.1, 1.2), 2),
            },
            "sensor-validator": {
                "validation.pipeline_stage": rng.choice(["ingest", "calibration", "correlation", "output"]),
                "validation.queue_depth": rng.randint(0, 200),
            },
            "telemetry-relay": {
                "relay.hop_count": rng.randint(1, 4),
                "relay.buffer_pct": round(rng.uniform(10.0, 85.0), 1),
            },
            "range-safety": {
                "safety.fts_arm_state": rng.choice(["SAFED", "SAFED", "SAFED", "ARMED"]),
                "safety.tracking_radars_active": rng.randint(2, 3),
            },
        }
        base.update(svc_attrs.get(service_name, {}))
        return base

    def get_rca_clues(self, channel: int, service_name: str, rng) -> dict:
        clues = {
            1: {  # Thermal Calibration Drift
                "fuel-system": {"thermal.sensor_zone": "engine_bay_sector_7", "thermal.calibration_epoch": "stale"},
                "sensor-validator": {"validation.drift_detected": True, "validation.sensor_id": "TC-47"},
                "mission-control": {"upstream.degraded_subsystem": "propulsion", "telemetry.quality": "degraded"},
                "range-safety": {"safety.propulsion_status": "degraded"},
            },
            2: {  # Fuel Pressure Anomaly
                "fuel-system": {"propulsion.regulator_mode": "REG-A-PRIMARY", "propulsion.he_supply_psi": round(rng.uniform(2700, 2840), 0)},
                "sensor-validator": {"validation.pressure_outlier": True, "validation.tank_id": rng.choice(["LOX-1", "RP1-1"])},
                "mission-control": {"upstream.degraded_subsystem": "propulsion", "telemetry.alert_class": "pressure"},
                "range-safety": {"safety.propulsion_status": "anomalous"},
            },
            3: {  # Oxidizer Flow Rate Deviation
                "fuel-system": {"propulsion.turbopump_rpm": rng.randint(30800, 31200), "propulsion.mov_trim_pct": round(rng.uniform(-5, 5), 1)},
                "sensor-validator": {"validation.flow_delta_pct": round(rng.uniform(3.5, 8.0), 1), "validation.sensor_type": "flow_rate"},
                "mission-control": {"upstream.degraded_subsystem": "propulsion"},
            },
            4: {  # GPS Multipath Interference
                "navigation": {"gnc.sv_masked_count": rng.randint(2, 5), "gnc.pdop": round(rng.uniform(6.5, 12.0), 1)},
                "sensor-validator": {"validation.gps_solution_quality": "degraded", "validation.multipath_svs": rng.choice(["G04,G07,G15", "G07,G15"])},
                "mission-control": {"upstream.degraded_subsystem": "guidance", "telemetry.nav_accuracy": "reduced"},
                "range-safety": {"safety.nav_solution_status": "degraded"},
            },
            5: {  # IMU Synchronization Loss
                "navigation": {"gnc.pps_source": rng.choice(["GPS_1PPS_A", "GPS_1PPS_B"]), "gnc.ocxo_temp_c": round(rng.uniform(41.0, 43.5), 1)},
                "sensor-validator": {"validation.imu_drift_axis": rng.choice(["X", "Y", "Z"]), "validation.clock_delta_ms": round(rng.uniform(3.5, 15.0), 1)},
                "mission-control": {"upstream.degraded_subsystem": "guidance", "telemetry.imu_status": "sync_loss"},
                "range-safety": {"safety.nav_solution_status": "degraded"},
            },
            6: {  # Star Tracker Alignment Fault
                "navigation": {"gnc.st_catalog_matches": rng.randint(5, 11), "gnc.ccd_temp_c": round(rng.uniform(-30, -25), 1)},
                "sensor-validator": {"validation.boresight_error_arcsec": round(rng.uniform(8.0, 40.0), 1), "validation.optics_contamination": rng.choice([True, False])},
                "mission-control": {"upstream.degraded_subsystem": "guidance"},
            },
            7: {  # Flight Termination System Check Failure
                "range-safety": {"safety.fts_error_code": f"0x{rng.randint(1, 255):02X}", "safety.fts_battery_pct": round(rng.uniform(95, 99), 1)},
                "sensor-validator": {"validation.fts_self_test": "FAIL", "validation.decoder_status": rng.choice(["LOCKED", "DEGRADED"])},
                "mission-control": {"upstream.degraded_subsystem": "safety", "telemetry.launch_hold": "FTS"},
            },
            8: {  # X-Band Packet Loss
                "comms-array": {"comms.ber": rng.choice(["1.2e-04", "5.8e-05", "3.1e-04"]), "comms.fec_failure_count": rng.randint(500, 1200)},
                "sensor-validator": {"validation.packet_integrity": "degraded", "validation.link_affected": rng.choice(["XB-PRIMARY", "XB-SECONDARY"])},
                "telemetry-relay": {"relay.x_band_retransmits": rng.randint(100, 500)},
                "mission-control": {"upstream.degraded_subsystem": "communications"},
            },
            9: {  # UHF Antenna Pointing Error
                "comms-array": {"comms.gimbal_motor_current_a": round(rng.uniform(2.5, 4.0), 1), "comms.tracking_target": "TDRSS-W"},
                "sensor-validator": {"validation.pointing_error_deg": round(rng.uniform(1.0, 5.0), 2), "validation.servo_status": "fault"},
                "mission-control": {"upstream.degraded_subsystem": "communications"},
            },
            10: {  # Payload Thermal Excursion
                "payload-monitor": {"payload.coolant_flow_lpm": round(rng.uniform(1.8, 2.6), 1), "payload.heater_state": rng.choice(["OFF", "STUCK_ON"])},
                "sensor-validator": {"validation.thermal_zone_affected": rng.choice(["A", "B"]), "validation.mli_status": rng.choice(["INTACT", "SUSPECT"])},
                "mission-control": {"upstream.degraded_subsystem": "payload"},
            },
            11: {  # Payload Vibration Anomaly
                "payload-monitor": {"payload.damper_pressure_psi": round(rng.uniform(38, 48), 1), "payload.resonance_freq_hz": round(rng.uniform(20, 80), 1)},
                "sensor-validator": {"validation.vibration_exceeded": True, "validation.isolation_mount_status": rng.choice(["ACTIVE", "DEGRADED"])},
                "mission-control": {"upstream.degraded_subsystem": "payload"},
                "range-safety": {"safety.structural_status": "monitor"},
            },
            12: {  # Pad Hydraulic Pressure Loss
                "ground-systems": {"ground.hyd_reservoir_pct": round(rng.uniform(65, 82), 0), "ground.filter_dp_psi": round(rng.uniform(10, 18), 1)},
                "sensor-validator": {"validation.hydraulic_pressure_status": "low", "validation.system_affected": rng.choice(["HYD-A", "HYD-B"])},
                "mission-control": {"upstream.degraded_subsystem": "ground"},
            },
            13: {  # Relay Packet Corruption
                "telemetry-relay": {"relay.crc_fail_pattern": "burst", "relay.sfp_rx_power_dbm": round(rng.uniform(-20, -16), 1)},
                "sensor-validator": {"validation.data_integrity": "compromised", "validation.corrupt_route": rng.choice(["AWS-GCP-01", "GCP-AZ-01"])},
                "mission-control": {"upstream.degraded_subsystem": "relay"},
            },
            14: {  # Ground Power Bus Fault
                "ground-systems": {"ground.bus_current_a": round(rng.uniform(38, 48), 1), "ground.ups_mode": rng.choice(["ONLINE", "BYPASS"])},
                "sensor-validator": {"validation.power_quality": "degraded", "validation.affected_bus": rng.choice(["PWR-A", "PWR-B"])},
                "mission-control": {"upstream.degraded_subsystem": "ground", "telemetry.pad_status": "caution"},
                "fuel-system": {"propulsion.ground_power_status": "unstable"},
            },
            15: {  # Range Safety Tracking Loss
                "range-safety": {"safety.fusion_state": "COAST", "safety.predict_confidence_pct": round(rng.uniform(55, 80), 0)},
                "sensor-validator": {"validation.radar_track_status": "LOST", "validation.affected_radar": rng.choice(["RDR-1", "RDR-2", "RDR-3"])},
                "mission-control": {"upstream.degraded_subsystem": "safety", "telemetry.tracking_status": "degraded"},
                "navigation": {"gnc.external_tracking": "unavailable"},
            },
            16: {  # Cross-Cloud Relay Latency
                "telemetry-relay": {"relay.buffer_utilization_pct": round(rng.uniform(75, 95), 1), "relay.retransmit_count": rng.randint(200, 600)},
                "sensor-validator": {"validation.relay_health": "degraded", "validation.affected_route": rng.choice(["aws->gcp", "gcp->azure", "aws->azure"])},
                "mission-control": {"upstream.degraded_subsystem": "relay", "telemetry.data_freshness": "stale"},
                "comms-array": {"comms.upstream_relay_status": "congested"},
            },
            17: {  # Sensor Validation Pipeline Stall
                "sensor-validator": {"validation.heap_usage_pct": round(rng.uniform(85, 97), 0), "validation.gc_pause_ms": rng.randint(80, 250)},
                "mission-control": {"upstream.degraded_subsystem": "validation", "telemetry.validation_status": "stalled"},
                "telemetry-relay": {"relay.upstream_backpressure": True},
            },
            18: {  # Calibration Epoch Mismatch
                "sensor-validator": {"validation.epoch_delta_s": rng.randint(3600, 86400), "validation.rtc_battery_v": round(rng.uniform(2.2, 2.9), 1)},
                "mission-control": {"upstream.degraded_subsystem": "validation", "telemetry.calibration_status": "stale"},
                "fuel-system": {"propulsion.calibration_confidence": "low"},
                "navigation": {"gnc.calibration_confidence": "low"},
            },
            19: {  # S-Band Signal Degradation
                "comms-array": {"comms.eirp_dbw": round(rng.uniform(35, 39), 1), "comms.antenna_gain_dbi": round(rng.uniform(32, 35), 1)},
                "sensor-validator": {"validation.link_margin_db": round(rng.uniform(-3, 0), 1), "validation.rain_fade_detected": rng.choice([True, False])},
                "mission-control": {"upstream.degraded_subsystem": "communications", "telemetry.comm_status": "degraded"},
                "telemetry-relay": {"relay.s_band_quality": "poor"},
            },
            20: {  # Weather Station Data Gap
                "ground-systems": {"ground.wx_link_type": "RS-422", "ground.station_battery_pct": round(rng.uniform(15, 45), 0)},
                "sensor-validator": {"validation.weather_data_gap_s": rng.randint(20, 120), "validation.station_affected": rng.choice(["WX-NORTH", "WX-SOUTH"])},
                "mission-control": {"upstream.degraded_subsystem": "ground", "telemetry.lcc_weather": "violated"},
                "range-safety": {"safety.weather_lcc_status": "NO-GO"},
            },
        }
        channel_clues = clues.get(channel, {})
        return channel_clues.get(service_name, {})

    def get_correlation_attribute(self, channel: int, is_error: bool, rng) -> dict:
        correlation_attrs = {
            1: ("deployment.config_version", "v2.3.1-canary"),
            2: ("infra.firmware_rev", "fw-4.2.0-rc1"),
            3: ("runtime.gc_policy", "aggressive-g1"),
            4: ("network.dns_resolver", "coredns-v1.11.4-patch2"),
            5: ("infra.ntp_source", "gps-pps-backup"),
            6: ("deployment.image_tag", "star-tracker-v3.1.0-beta"),
            7: ("deployment.fts_firmware", "fts-controller-v5.2.0-rc1"),
            8: ("infra.nic_driver", "ena-2.12.3-unstable"),
            9: ("deployment.servo_fw", "gimbal-ctrl-v2.0.1-rc3"),
            10: ("runtime.jvm_flags", "-XX:+UseZGC -Xmx2g"),
            11: ("infra.mount_revision", "iso-bracket-rev-C"),
            12: ("infra.hyd_pump_model", "parker-pvp48-rebuilt"),
            13: ("infra.sfp_model", "FTRJ1319P1BTL-v2"),
            14: ("infra.ups_firmware", "apc-smart-ups-v4.1.2"),
            15: ("infra.radar_firmware", "rdr-track-v8.1.3-beta"),
            16: ("network.bgp_as_path", "64512-64513-64515"),
            17: ("runtime.heap_config", "jvm-12g-g1gc-experimental"),
            18: ("infra.rtc_crystal", "txco-40mhz-batch-2024Q3"),
            19: ("network.proxy_config", "envoy-v1.28-experimental"),
            20: ("deployment.wx_station_fw", "davis-v3.2.1-patched"),
        }
        attr_key, attr_val = correlation_attrs.get(channel, ("deployment.config_version", "unknown"))
        # 90% on errors, 5% on healthy
        if is_error:
            if rng.random() < 0.90:
                return {attr_key: attr_val}
        else:
            if rng.random() < 0.05:
                return {attr_key: attr_val}
        return {}

    # ── Fault Parameters ──────────────────────────────────────────────

    def get_fault_params(self, channel: int) -> dict[str, Any]:
        return {
            "deviation": round(random.uniform(3.0, 12.0), 1),
            "epoch": int(time.time()) - random.randint(100, 5000),
            "tank_id": random.choice(["LOX-1", "LOX-2", "RP1-1", "RP1-2"]),
            "pressure": round(random.uniform(180, 350), 1),
            "expected_min": 200,
            "expected_max": 310,
            "measured": round(random.uniform(2.0, 8.0), 2),
            "commanded": round(random.uniform(4.0, 6.0), 2),
            "delta": round(random.uniform(4.0, 15.0), 1),
            "num_satellites": random.randint(3, 8),
            "uncertainty": round(random.uniform(5.0, 50.0), 1),
            "drift_ms": round(random.uniform(5.0, 25.0), 1),
            "threshold_ms": 3.0,
            "axis": random.choice(["X", "Y", "Z"]),
            "error_arcsec": round(random.uniform(10.0, 45.0), 1),
            "limit_arcsec": 5.0,
            "snr_db": round(random.uniform(3.0, 8.0), 1),
            "min_snr_db": 12.0,
            "rf_channel": random.choice(["S1", "S2", "S3"]),
            "loss_pct": round(random.uniform(5.0, 25.0), 1),
            "threshold_pct": 2.0,
            "link_id": random.choice(["XB-PRIMARY", "XB-SECONDARY"]),
            "az_error": round(random.uniform(1.0, 5.0), 2),
            "el_error": round(random.uniform(0.5, 3.0), 2),
            "zone": random.choice(["A", "B", "C", "D"]),
            "temp": round(random.uniform(55.0, 85.0), 1),
            "safe_min": -10.0,
            "safe_max": 45.0,
            "amplitude": round(random.uniform(2.0, 8.0), 2),
            "frequency": round(random.uniform(20.0, 200.0), 1),
            "limit": 1.5,
            "source_cloud": random.choice(["aws", "gcp", "azure"]),
            "dest_cloud": random.choice(["aws", "gcp", "azure"]),
            "latency_ms": random.randint(500, 3000),
            "threshold_ms_relay": 200,
            "corrupted_count": random.randint(5, 50),
            "total_count": random.randint(100, 500),
            "route_id": random.choice(["AWS-GCP-01", "GCP-AZ-01", "AWS-AZ-01"]),
            "bus_id": random.choice(["PWR-A", "PWR-B", "PWR-C"]),
            "voltage": round(random.uniform(105, 135), 1),
            "nominal_v": 120.0,
            "deviation_pct": round(random.uniform(8.0, 20.0), 1),
            "station_id": random.choice(["WX-NORTH", "WX-SOUTH", "WX-EAST", "WX-WEST"]),
            "gap_seconds": random.randint(30, 180),
            "max_gap": 15,
            "system_id": random.choice(["HYD-A", "HYD-B"]),
            "min_pressure": 2800,
            "queue_depth": random.randint(500, 5000),
            "rate": round(random.uniform(1.0, 10.0), 1),
            "min_rate": 50.0,
            "sensor_id": f"SENS-{random.randint(1000, 9999)}",
            "actual_epoch": int(time.time()) - random.randint(86400, 604800),
            "expected_epoch": int(time.time()) - 3600,
            "unit_id": random.choice(["FTS-A", "FTS-B"]),
            "error_code": f"0x{random.randint(1, 255):02X}",
            "radar_id": random.choice(["RDR-1", "RDR-2", "RDR-3"]),
            "gap_ms": random.randint(500, 5000),
            "max_gap_ms": 250,
        }


# Module-level instance for registry discovery
scenario = SpaceScenario()

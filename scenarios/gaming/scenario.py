"""Live Gaming Platform scenario — multiplayer gaming infrastructure with live-ops chaos engineering."""

from __future__ import annotations

import random
import time
from typing import Any

from scenarios.base import BaseScenario, CountdownConfig, UITheme


class GamingScenario(BaseScenario):
    """Live multiplayer gaming platform with 9 game services and 20 fault channels."""

    # ── Identity ──────────────────────────────────────────────────────

    @property
    def scenario_id(self) -> str:
        return "gaming"

    @property
    def scenario_icon(self) -> str:
        return "🎮"

    @property
    def scenario_name(self) -> str:
        return "Live Gaming Platform"

    @property
    def scenario_description(self) -> str:
        return (
            "Live multiplayer gaming platform with game servers, matchmaking, "
            "content delivery, chat, leaderboards, authentication, payments, "
            "analytics, and content moderation. Cyberpunk neon command center."
        )

    @property
    def namespace(self) -> str:
        return "gaming"

    @property
    def sort_order(self) -> int:
        return 5

    @property
    def raw_log_profile(self) -> dict[str, Any]:
        return {
            "service_name": "game-api-edge",
            "user_id_prefix": "player",
            "tier_field": "player_tier",
            "tier_values": [("f2p", 80), ("plus", 15), ("vip", 5)],
            "country_weights": {"US": 30, "KR": 15, "JP": 12, "DE": 8, "GB": 8, "BR": 10, "CN": 12, "MX": 5},
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "paths": [
                "/api/v1/match", "/api/v1/leaderboard", "/api/v1/inventory",
                "/api/v1/store", "/api/v1/friends", "/api/v1/chat",
                "/login", "/health",
            ],
            "change_point_path": "/api/v1/match",
        }

    @property
    def executive_kpi_emitter_service_name(self) -> str:
        return "analytics-pipeline"

    @property
    def executive_dashboard_intro(self) -> str:
        return (
            "**Live gaming KPIs** — player engagement, monetization, community, "
            "and live-ops health (synthetic `business.*` from `analytics-pipeline`)."
        )

    @property
    def executive_kpi_sections(self) -> list[dict]:
        return [
            {
                "header": "**Player engagement** — DAU, sessions, duration, matches, quests, and retention",
                "specs": [
                    ("Daily active users", "metrics.business.daily_active_users"),
                    ("Sessions / min", "metrics.business.sessions_per_min"),
                    ("Avg session duration (min)", "metrics.business.avg_session_duration_min"),
                    ("Matches played / min", "metrics.business.matches_played_per_min"),
                    ("Quests completed / min", "metrics.business.quests_completed_per_min"),
                    ("Daily retention rate (%)", "metrics.business.daily_retention_rate_pct"),
                ],
            },
            {
                "header": "**Monetization** — revenue, IAP, battle pass, ARPU, loot, and cosmetics",
                "specs": [
                    ("Revenue (USD/min)", "metrics.business.revenue_usd_per_min"),
                    ("In-app purchases / min", "metrics.business.in_app_purchases_per_min"),
                    ("Battle pass conversions / min", "metrics.business.battle_pass_conversions_per_min"),
                    ("Avg revenue per user (USD)", "metrics.business.avg_revenue_per_user_usd"),
                    ("Loot opens / min", "metrics.business.loot_opens_per_min"),
                    ("Cosmetic sales (USD/min)", "metrics.business.cosmetic_sales_usd_per_min"),
                ],
            },
            {
                "header": "**Community** — chat, shares, toxicity, creators, streaming, and signups",
                "specs": [
                    ("Chat messages / min", "metrics.business.chat_messages_per_min"),
                    ("Social clip shares / min", "metrics.business.social_clip_shares_per_min"),
                    ("Toxic report rate (%)", "metrics.business.toxic_report_rate_pct"),
                    ("Creator uploads / min", "metrics.business.creator_uploads_per_min"),
                    ("Streaming viewers", "metrics.business.streaming_viewers"),
                    ("New registrations / min", "metrics.business.new_registrations_per_min"),
                ],
            },
            {
                "header": "**Live ops health** — server lag, crashes, bugs, churn, NPS, and moderation",
                "specs": [
                    ("Server tick lag (ms)", "metrics.business.server_tick_lag_ms"),
                    ("Crash rate (%)", "metrics.business.crash_rate_pct"),
                    ("Bug reports / min", "metrics.business.player_bug_reports_per_min"),
                    ("Churn risk (0–100)", "metrics.business.churn_risk_index_0_100"),
                    ("Satisfaction proxy (NPS-like)", "metrics.business.net_satisfaction_proxy_nps"),
                    ("Moderation queue size", "metrics.business.content_moderation_queue_size"),
                ],
            },
        ]

    @property
    def executive_trend_charts(self) -> list[dict]:
        return [
            {"title": "Daily active users", "field": "metrics.business.daily_active_users", "y_label": "users"},
            {"title": "Revenue (USD/min)", "field": "metrics.business.revenue_usd_per_min", "y_label": "USD/min"},
            {"title": "Sessions / min", "field": "metrics.business.sessions_per_min", "y_label": "sessions/min"},
            {"title": "Matches played / min", "field": "metrics.business.matches_played_per_min", "y_label": "matches/min"},
            {"title": "In-app purchases / min", "field": "metrics.business.in_app_purchases_per_min", "y_label": "purchases/min"},
            {"title": "Streaming viewers", "field": "metrics.business.streaming_viewers", "y_label": "viewers"},
        ]

    # ── Services ──────────────────────────────────────────────────────

    @property
    def services(self) -> dict[str, dict[str, Any]]:
        return {
            "game-server": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1a",
                "subsystem": "game_engine",
                "language": "cpp",
            },
            "matchmaking-engine": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1b",
                "subsystem": "matchmaking",
                "language": "go",
            },
            "content-delivery": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1c",
                "subsystem": "cdn",
                "language": "rust",
            },
            "chat-service": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "social",
                "language": "java",
            },
            "leaderboard-api": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-b",
                "subsystem": "progression",
                "language": "go",
            },
            "auth-gateway": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "identity",
                "language": "python",
            },
            "payment-processor": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "monetization",
                "language": "dotnet",
            },
            "analytics-pipeline": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-2",
                "subsystem": "analytics",
                "language": "python",
            },
            "moderation-engine": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "trust_safety",
                "language": "java",
            },
        }

    # ── Channel Registry ──────────────────────────────────────────────

    @property
    def channel_registry(self) -> dict[int, dict[str, Any]]:
        return {
            1: {
                "name": "Game State Desync",
                "subsystem": "game_engine",
                "vehicle_section": "game_loop",
                "error_type": "NET-STATE-DESYNC",
                "sensor_type": "state_validator",
                "affected_services": ["game-server", "matchmaking-engine"],
                "cascade_services": ["analytics-pipeline"],
                "description": "Game state diverges between server authoritative state and client prediction, causing rubber-banding and rollback cascades",
                "investigation_notes": (
                    "Root cause: client-side prediction drift exceeds reconciliation threshold due to "
                    "packet loss or jitter spikes on the UDP game channel. The server authoritative state "
                    "and client extrapolation diverge beyond 0.5m, triggering forced rollbacks.\n"
                    "1. Check network quality: run `netstat -su` on game-server pods for UDP packet drops; "
                    "review CloudWatch `NetworkPacketsDropped` for the hosting AZ.\n"
                    "2. Inspect tick alignment: query `FROM logs WHERE body.text LIKE '*NET-STATE-DESYNC*'` "
                    "and correlate `seq` gaps — 2+ ticks behind indicates client CPU starvation or GC pauses.\n"
                    "3. Verify interpolation buffer: if `interp_delay` is <100ms, increase to 150ms to absorb jitter.\n"
                    "4. Remediate: if widespread, issue `reset_game_state` to force all clients to re-download "
                    "authoritative world state and rebuild prediction buffers from scratch.\n"
                    "5. Long-term: audit the client prediction model — consider switching from dead-reckoning "
                    "to hermite interpolation for smoother reconciliation under packet loss."
                ),
                "remediation_action": "reset_game_state",
                "error_message": "[Net] NET-STATE-DESYNC: player={player_id} pos_delta={position_delta}m threshold=0.5m tick={tick_number} match={match_id}",
                "stack_trace": (
                    "=== NET STATE RECONCILIATION DUMP ===\n"
                    "match={match_id}  tick={tick_number}  player={player_id}\n"
                    "----------- server state -----------\n"
                    "  pos  = (1247.32, 45.00, -892.17)\n"
                    "  vel  = (3.41, 0.00, -1.22)\n"
                    "  yaw  = 127.4 deg\n"
                    "  seq  = 48201\n"
                    "----------- client state -----------\n"
                    "  pos  = (1248.87, 45.00, -893.40)  delta={position_delta}m\n"
                    "  vel  = (4.02, 0.00, -1.87)\n"
                    "  yaw  = 128.1 deg\n"
                    "  seq  = 48199  (2 behind)\n"
                    "----------- action -----------------\n"
                    "  FORCE_RECONCILE  rollback_ticks=3  bandwidth_cost=2.4KB\n"
                    "  client_rtt=47ms  jitter=8ms  interp_delay=100ms\n"
                    "NET-STATE-DESYNC: threshold exceeded — forced reconcile for player {player_id}"
                ),
            },
            2: {
                "name": "Physics Simulation Overflow",
                "subsystem": "game_engine",
                "vehicle_section": "physics_engine",
                "error_type": "PHYS-OVERFLOW",
                "sensor_type": "physics_validator",
                "affected_services": ["game-server", "analytics-pipeline"],
                "cascade_services": ["matchmaking-engine"],
                "description": "Physics simulation accumulates floating-point errors causing object positions to overflow into NaN territory",
                "investigation_notes": (
                    "Root cause: the physics integrator uses single-precision floats for velocity accumulation, "
                    "and repeated substep iterations without epsilon clamping allow energy injection from "
                    "collision response to compound exponentially, pushing velocities past simulation limits.\n"
                    "1. Check the entity trace: look at `accel` values in the dump — acceleration >10000 "
                    "indicates a collision solver feedback loop (two overlapping colliders pumping energy).\n"
                    "2. Inspect `penetration_max` — values >0.5m mean the broadphase AABB tree is stale; "
                    "run `/debug physics rebuild_bvh` on the affected zone to force spatial index rebuild.\n"
                    "3. Review substep count: 4 substeps at high entity density causes frame budget overrun; "
                    "reduce to 2 substeps and enable CCD (continuous collision detection) for fast movers.\n"
                    "4. Remediate: issue `reset_physics_engine` to zero all velocities, rebuild the collision "
                    "world, and re-derive positions from the last valid snapshot.\n"
                    "5. Long-term: migrate velocity accumulator to double-precision and add per-substep "
                    "energy conservation checks to detect and break feedback loops before overflow."
                ),
                "remediation_action": "reset_physics_engine",
                "error_message": "[Physics] PHYS-OVERFLOW: entity={entity_id} velocity={velocity} max={max_velocity} zone={zone_id} tick={tick_number}",
                "stack_trace": (
                    "=== PHYSICS ENGINE STATE DUMP ===\n"
                    "tick={tick_number}  zone={zone_id}  substep=4/4\n"
                    "----------- entity {entity_id} -----------\n"
                    "  pos       = (8421.7, 102.3, -3304.9)\n"
                    "  vel       = ({velocity}, 0.0, 0.0)  |v|={velocity}\n"
                    "  max_vel   = {max_velocity}\n"
                    "  accel     = (12842.1, 0.0, -4201.3)\n"
                    "  mass      = 85.0 kg\n"
                    "  collider  = CAPSULE r=0.4 h=1.8\n"
                    "----------- collision candidates --------\n"
                    "  broadphase_pairs = 47\n"
                    "  narrowphase_hits = 3\n"
                    "  penetration_max  = 0.82m (ENT-29481 <-> ENT-30012)\n"
                    "----------- action ----------------------\n"
                    "  CLAMP velocity to {max_velocity}  REWIND substep 3\n"
                    "PHYS-OVERFLOW: entity {entity_id} velocity {velocity} exceeds simulation limit {max_velocity}"
                ),
            },
            3: {
                "name": "Matchmaking Queue Overflow",
                "subsystem": "matchmaking",
                "vehicle_section": "matchmaker_core",
                "error_type": "MM-QUEUE-OVERFLOW",
                "sensor_type": "queue_monitor",
                "affected_services": ["matchmaking-engine", "game-server"],
                "cascade_services": ["auth-gateway", "analytics-pipeline"],
                "description": "Matchmaking queue depth exceeds capacity causing player wait times to spike beyond acceptable thresholds",
                "investigation_notes": (
                    "Root cause: inflow rate (enqueue/s) far exceeds outflow (dequeue/s), typically caused by "
                    "a game server allocation bottleneck — the matchmaker finds groups but cannot place them "
                    "because server provisioning is lagging behind demand.\n"
                    "1. Check server pool: query `kubectl get pods -l app=game-server` on the EKS cluster to "
                    "verify available game server instances; if pool is exhausted, scale the fleet.\n"
                    "2. Review per-tier breakdown: diamond+ queues with 891 waiting is normal, but bronze-silver "
                    "at 4201 indicates a systemic issue, not a thin-population problem.\n"
                    "3. Inspect matchmaker logs for `EXPAND mmr_range` actions — repeated range expansions "
                    "with no matches means the issue is server supply, not rating spread.\n"
                    "4. Remediate: issue `restart_matchmaker` to clear stale queue entries and reset internal "
                    "timers; simultaneously scale game-server pods to increase placement capacity.\n"
                    "5. If region-locked, temporarily relax region constraints to allow cross-region placement "
                    "while new servers spin up."
                ),
                "remediation_action": "restart_matchmaker",
                "error_message": "[MM] MM-QUEUE-OVERFLOW: pool={queue_name} queue={queue_depth} max={max_capacity} wait_p99={wait_time_ms}ms region={region}",
                "stack_trace": (
                    "=== MATCHMAKING QUEUE STATE DUMP ===\n"
                    "pool={queue_name}  region={region}\n"
                    "----------- queue metrics -----------\n"
                    "  depth       = {queue_depth}  (max {max_capacity})\n"
                    "  wait_p50    = 12400ms\n"
                    "  wait_p95    = 87200ms\n"
                    "  wait_p99    = {wait_time_ms}ms\n"
                    "  enqueue/s   = 342\n"
                    "  dequeue/s   = 89\n"
                    "  drain_eta   = NEVER (inflow > outflow)\n"
                    "----------- pool breakdown ----------\n"
                    "  bronze-silver  : 4201 waiting\n"
                    "  gold-platinum  : 2847 waiting\n"
                    "  diamond+       : 891 waiting\n"
                    "----------- action ------------------\n"
                    "  EXPAND mmr_range +200  RELAX region_lock\n"
                    "MM-QUEUE-OVERFLOW: pool {queue_name} saturated at {queue_depth}/{max_capacity}"
                ),
            },
            4: {
                "name": "Skill Rating Calculation Error",
                "subsystem": "matchmaking",
                "vehicle_section": "rating_engine",
                "error_type": "MM-SKILL-RATING-DIVERGE",
                "sensor_type": "rating_validator",
                "affected_services": ["matchmaking-engine", "leaderboard-api"],
                "cascade_services": ["analytics-pipeline"],
                "description": "Skill rating calculation produces invalid MMR values due to edge cases in the Elo/Glicko algorithm implementation",
                "investigation_notes": (
                    "Root cause: a code defect in the Glicko-2 convergence loop — the volatility (sigma) "
                    "iterative solver does not clamp intermediate values, allowing sigma to diverge when "
                    "a player's actual score vastly exceeds expected score (e.g., 0.83 vs 0.41). This "
                    "produces new_mu values outside the valid [0, max_mmr] range.\n"
                    "1. Check convergence iterations: if `convergence_i` approaches max (20), the Illinois "
                    "method is not converging — the tau system constant may be misconfigured.\n"
                    "2. Query affected players: `FROM logs WHERE body.text LIKE '*MM-SKILL-RATING-DIVERGE*'` "
                    "and check how many players have out-of-range MMR in the current season.\n"
                    "3. Validate the Glicko-2 implementation against Mark Glickman's reference paper — "
                    "specifically step 5.1 (volatility estimation) needs a bisection fallback.\n"
                    "4. Remediate: issue `reset_skill_ratings` for affected players to recalculate from "
                    "match history; deploy a hotfix adding sigma clamping (0.3 < sigma < 1.2).\n"
                    "5. The current CLAMP action masks the defect — the algorithm must be fixed to prevent "
                    "incorrect competitive matchmaking downstream."
                ),
                "remediation_action": "reset_skill_ratings",
                "error_message": "[MM] MM-SKILL-RATING-DIVERGE: player={player_id} mmr={mmr_value} valid_range=[0,{max_mmr}] volatility={volatility} match={match_id}",
                "stack_trace": (
                    "=== GLICKO-2 CALCULATION TRACE ===\n"
                    "player={player_id}  match={match_id}\n"
                    "----------- pre-match state ----------\n"
                    "  mu (rating)     = 1847.3\n"
                    "  phi (deviation) = 142.7\n"
                    "  sigma (vol)     = {volatility}\n"
                    "  games_in_period = 14\n"
                    "----------- match result -------------\n"
                    "  opponents       = 5\n"
                    "  actual_score    = 0.83\n"
                    "  expected_score  = 0.41\n"
                    "  k_factor        = 32.0\n"
                    "----------- post-match calc ----------\n"
                    "  new_mu          = {mmr_value}  <<< OUT OF RANGE [0, {max_mmr}]\n"
                    "  new_phi         = 187.2\n"
                    "  new_sigma       = 0.089\n"
                    "  convergence_i   = 12 iterations (max 20)\n"
                    "----------- action -------------------\n"
                    "  CLAMP to valid range  FLAG for manual review\n"
                    "MM-SKILL-RATING-DIVERGE: player {player_id} mmr {mmr_value} outside bounds"
                ),
            },
            5: {
                "name": "CDN Cache Miss Storm",
                "subsystem": "cdn",
                "vehicle_section": "cdn_edge",
                "error_type": "CDN-CACHE-MISS-STORM",
                "sensor_type": "cache_monitor",
                "affected_services": ["content-delivery", "game-server"],
                "cascade_services": ["analytics-pipeline"],
                "description": "Cascading cache misses overwhelm origin servers as hot content expires simultaneously across edge nodes",
                "investigation_notes": (
                    "Root cause: cache TTL alignment — all edge nodes received the same asset bundle version "
                    "at the same time, so TTLs expire simultaneously, causing a thundering herd of origin "
                    "requests. The origin circuit breaker enters HALF_OPEN state under the load spike.\n"
                    "1. Check origin health: verify origin S3/GCS bucket response times in CloudWatch or "
                    "Stackdriver — p99 >500ms confirms origin saturation.\n"
                    "2. Review cache eviction logs: 14,203 evictions/min with only 32.1% warm cache means "
                    "the edge LRU is thrashing; increase edge cache capacity or tier hot assets.\n"
                    "3. Inspect per-asset-group miss rates: textures-hd at 4,201 misses/min is the primary "
                    "driver — pre-warm these via `cdn-cli prefetch --group textures-hd --edges all`.\n"
                    "4. Remediate: issue `purge_cdn_cache` on stale edges and then `reset_cdn_origin` to "
                    "restart origin connection pools; add jittered TTL offsets (TTL + rand(0, 300s)) to "
                    "prevent future synchronized expiration storms.\n"
                    "5. Enable request coalescing on the CDN edge layer so concurrent misses for the same "
                    "asset are collapsed into a single origin fetch."
                ),
                "remediation_action": "purge_cdn_cache",
                "error_message": "[CDN] CDN-CACHE-MISS-STORM: edge={edge_node} hit_rate={cache_hit_rate}% threshold=85% origin_load={origin_load_pct}% asset_group={asset_group}",
                "stack_trace": (
                    "=== CDN EDGE NODE CACHE STATISTICS ===\n"
                    "edge={edge_node}  asset_group={asset_group}\n"
                    "----------- cache metrics -----------\n"
                    "  hit_rate    = {cache_hit_rate}%  (threshold 85%)\n"
                    "  miss_rate   = {origin_load_pct}%\n"
                    "  evictions   = 14,203/min\n"
                    "  warm_pct    = 32.1%\n"
                    "  cold_pct    = 67.9%\n"
                    "----------- origin load -------------\n"
                    "  rps_to_origin   = 8,421\n"
                    "  origin_p99_ms   = 847\n"
                    "  origin_errors   = 127 (circuit_breaker=HALF_OPEN)\n"
                    "  bandwidth_gbps  = 12.4\n"
                    "----------- top miss groups ---------\n"
                    "  textures-hd     : 4,201 misses/min\n"
                    "  models-char     : 2,103 misses/min\n"
                    "  audio-sfx       : 891 misses/min\n"
                    "CDN-CACHE-MISS-STORM: edge {edge_node} hit rate {cache_hit_rate}% below threshold"
                ),
            },
            6: {
                "name": "Asset Bundle Corruption",
                "subsystem": "cdn",
                "vehicle_section": "asset_pipeline",
                "error_type": "CDN-ASSET-CORRUPT",
                "sensor_type": "integrity_checker",
                "affected_services": ["content-delivery", "game-server"],
                "cascade_services": ["moderation-engine"],
                "description": "Game asset bundles fail integrity verification after CDN transfer, causing client crashes on load",
                "investigation_notes": (
                    "Root cause: chunk-level corruption during CDN edge-to-client transfer — TCP resets "
                    "during large bundle downloads cause partial chunk writes that pass length checks but "
                    "fail SHA-256 verification. The corrupt chunk is typically at a TCP segment boundary.\n"
                    "1. Identify the corrupt chunk offset: chunk 23 at offset 92274688 — correlate with "
                    "CDN edge access logs for `tcp_resets` around the transfer timestamp.\n"
                    "2. Verify origin integrity: re-fetch the bundle directly from origin (bypassing CDN) "
                    "with `curl -H 'Cache-Control: no-cache' <origin_url> | sha256sum` to rule out origin "
                    "corruption vs. transit corruption.\n"
                    "3. Check edge node health: if `edge-iad-01` shows elevated tcp_resets across multiple "
                    "bundles, the edge node may have a faulty NIC or be under DDoS.\n"
                    "4. Remediate: issue `reset_cdn_origin` to invalidate the corrupted cached copy on the "
                    "edge node; quarantine the bad bundle hash and force re-download for affected clients.\n"
                    "5. Enable end-to-end chunk checksumming with per-chunk CRC32 verification on the client "
                    "side so corrupted chunks trigger targeted re-fetch instead of full bundle re-download."
                ),
                "remediation_action": "reset_cdn_origin",
                "error_message": "[CDN] CDN-ASSET-CORRUPT: bundle={bundle_id} expected={expected_hash} actual={actual_hash} size={bundle_size_mb}MB version={bundle_version}",
                "stack_trace": (
                    "=== ASSET INTEGRITY VERIFICATION LOG ===\n"
                    "bundle={bundle_id}  version={bundle_version}\n"
                    "----------- checksums ---------------\n"
                    "  expected  = {expected_hash}\n"
                    "  actual    = {actual_hash}\n"
                    "  algorithm = SHA-256\n"
                    "----------- bundle info -------------\n"
                    "  size        = {bundle_size_mb}MB\n"
                    "  chunks      = 48\n"
                    "  chunk_size  = 4MB\n"
                    "  corrupt_chunk = 23 (offset 92274688)\n"
                    "  edge_source   = edge-iad-01\n"
                    "----------- transfer log ------------\n"
                    "  started    = 2026-02-17T14:22:01.847Z\n"
                    "  completed  = 2026-02-17T14:22:04.213Z\n"
                    "  retries    = 1\n"
                    "  tcp_resets = 2\n"
                    "CDN-ASSET-CORRUPT: bundle {bundle_id} checksum mismatch — quarantined"
                ),
            },
            7: {
                "name": "Chat Message Flood",
                "subsystem": "social",
                "vehicle_section": "chat_gateway",
                "error_type": "CHAT-FLOOD-DETECT",
                "sensor_type": "rate_limiter",
                "affected_services": ["chat-service", "moderation-engine"],
                "cascade_services": ["auth-gateway"],
                "description": "Chat channels experiencing message floods that overwhelm rate limiters and moderation pipelines",
                "investigation_notes": (
                    "Root cause: coordinated bot accounts are flooding public chat channels at rates far "
                    "exceeding per-user rate limits — the attack uses distributed bot networks where each "
                    "bot stays just under individual limits but the aggregate overwhelms channel capacity.\n"
                    "1. Check top senders: PLR-482910 and PLR-109284 flagged as BOT_SUSPECT — verify account "
                    "age, friend count, and purchase history via `player-admin lookup <player_id>`.\n"
                    "2. Review moderation queue: {pending_moderation} pending scans with 421 dropped means "
                    "the automod NLP classifier is CPU-saturated; check GPU inference pod health.\n"
                    "3. Inspect rate limiter config: per-user limit may be set correctly but channel-level "
                    "aggregate limit is missing — add `channel_rate_limit` to the chat gateway config.\n"
                    "4. Remediate: issue `restart_chat_service` to reset connection pools and apply updated "
                    "rate limits; then `flush_message_queue` to clear the backed-up moderation pipeline.\n"
                    "5. Ban confirmed bot accounts immediately and enable CAPTCHA challenges for accounts "
                    "younger than 24 hours attempting to post in public channels."
                ),
                "remediation_action": "restart_chat_service",
                "error_message": "[Chat] CHAT-FLOOD-DETECT: channel={channel_id} rate={message_rate}msg/s threshold={rate_limit}msg/s pending_mod={pending_moderation}",
                "stack_trace": (
                    "=== CHAT RATE LIMITER STATE DUMP ===\n"
                    "channel={channel_id}\n"
                    "----------- rate metrics ------------\n"
                    "  current_rate   = {message_rate} msg/s\n"
                    "  threshold      = {rate_limit} msg/s\n"
                    "  burst_window   = 5s\n"
                    "  burst_peak     = {message_rate} msg/s\n"
                    "----------- moderation queue --------\n"
                    "  pending        = {pending_moderation}\n"
                    "  avg_scan_ms    = 12.4\n"
                    "  automod_queue  = 87% full\n"
                    "  dropped_scans  = 421\n"
                    "----------- top senders -------------\n"
                    "  PLR-482910  : 47 msg/s (BOT_SUSPECT)\n"
                    "  PLR-109284  : 31 msg/s (BOT_SUSPECT)\n"
                    "  PLR-773201  : 28 msg/s (NORMAL)\n"
                    "----------- action ------------------\n"
                    "  THROTTLE channel to {rate_limit} msg/s  QUEUE moderation backlog\n"
                    "CHAT-FLOOD-DETECT: channel {channel_id} rate {message_rate}msg/s exceeds threshold"
                ),
            },
            8: {
                "name": "Voice Channel Degradation",
                "subsystem": "social",
                "vehicle_section": "voice_server",
                "error_type": "VOICE-CHANNEL-OVERLOAD",
                "sensor_type": "audio_quality_monitor",
                "affected_services": ["chat-service", "game-server"],
                "cascade_services": ["analytics-pipeline"],
                "description": "Voice chat channels experiencing audio quality degradation with packet loss, jitter, and codec failures",
                "investigation_notes": (
                    "Root cause: voice server CPU saturation at 87.4% causes the audio mixing pipeline to "
                    "miss its 10ms deadline, resulting in packet drops on the UDP voice channel. The server "
                    "downgrades bitrate from 96kbps to 64kbps but this is insufficient under load.\n"
                    "1. Check server resources: `top -p $(pgrep voice-mixer)` to verify CPU usage per thread; "
                    "the mixing thread is single-core bound and needs CPU affinity pinning.\n"
                    "2. Review MOS scores: any stream below 2.0 MOS is unintelligible — those players should "
                    "be migrated to a less-loaded voice server immediately.\n"
                    "3. Inspect FEC recovery rate: 12.3% recovery means FEC is working but insufficient for "
                    "{voice_packet_loss_pct}% loss — consider enabling Opus FEC redundancy mode.\n"
                    "4. Remediate: issue `restart_voice_servers` to rebalance voice channel assignments across "
                    "the server pool; then `reset_codec_pipeline` to force codec renegotiation at optimal "
                    "bitrates for current network conditions.\n"
                    "5. Scale voice server pods horizontally and set max speakers per server to 50 to prevent "
                    "CPU saturation; enable Opus DTX (discontinuous transmission) to reduce idle bandwidth."
                ),
                "remediation_action": "restart_voice_servers",
                "error_message": "[Voice] VOICE-CHANNEL-OVERLOAD: channel={voice_channel_id} loss={voice_packet_loss_pct}% jitter={jitter_ms}ms speakers={active_speakers} codec={codec}",
                "stack_trace": (
                    "=== VOICE SERVER QUALITY METRICS ===\n"
                    "channel={voice_channel_id}  codec={codec}\n"
                    "----------- per-stream stats --------\n"
                    "  stream_count     = {active_speakers}\n"
                    "  packet_loss_avg  = {voice_packet_loss_pct}%\n"
                    "  jitter_avg       = {jitter_ms}ms\n"
                    "  jitter_max       = 287ms\n"
                    "  bitrate          = 64kbps (target 96kbps — downgraded)\n"
                    "  fec_recovery     = 12.3%\n"
                    "----------- worst streams -----------\n"
                    "  PLR-481020  loss=34.2%  jitter=198ms  MOS=1.8\n"
                    "  PLR-229103  loss=28.7%  jitter=154ms  MOS=2.1\n"
                    "  PLR-884712  loss=19.1%  jitter=112ms  MOS=2.6\n"
                    "----------- server state ------------\n"
                    "  cpu_pct     = 87.4%\n"
                    "  mix_latency = 23ms (target 10ms)\n"
                    "  udp_rx_drop = 4.2%\n"
                    "VOICE-CHANNEL-OVERLOAD: channel {voice_channel_id} quality degraded — {voice_packet_loss_pct}% loss"
                ),
            },
            9: {
                "name": "Leaderboard Corruption",
                "subsystem": "progression",
                "vehicle_section": "leaderboard_core",
                "error_type": "LB-DATA-CORRUPT",
                "sensor_type": "consistency_checker",
                "affected_services": ["leaderboard-api", "game-server"],
                "cascade_services": ["analytics-pipeline", "moderation-engine"],
                "description": "Leaderboard sorted set becomes inconsistent due to concurrent score updates causing rank calculation errors",
                "investigation_notes": (
                    "Root cause: concurrent ZADD operations to the Redis sorted set during AOF rewrite cause "
                    "race conditions — two game servers submit score updates for overlapping rank ranges "
                    "without distributed locking, producing rank inversions and NaN entries.\n"
                    "1. Check Redis state: `redis-cli info persistence` — if `aof_rewrite_in_progress=1`, "
                    "the rewrite is contending with writes; defer bulk score updates until rewrite completes.\n"
                    "2. Audit the corruption: rank 42018 score > rank 42017 score is a classic ZADD race; "
                    "NaN at rank 42103 indicates a Lua script received non-numeric input from game server.\n"
                    "3. Verify ZSET cardinality: `ZCARD {leaderboard_id}` should match `total_entries` — "
                    "any mismatch indicates phantom entries from incomplete transaction rollbacks.\n"
                    "4. Remediate: issue `freeze_leaderboard` to block new writes, then `rebuild_leaderboard` "
                    "to reconstruct the sorted set from the transaction log source of truth.\n"
                    "5. Deploy Redlock-based distributed mutex for score update batches and add input "
                    "validation to reject NaN/Infinity scores at the game server API boundary."
                ),
                "remediation_action": "rebuild_leaderboard",
                "error_message": "[LB] LB-DATA-CORRUPT: board={leaderboard_id} affected={corrupt_entries} checksum_fail=true season={season_id}",
                "stack_trace": (
                    "=== LEADERBOARD CONSISTENCY CHECK ===\n"
                    "board={leaderboard_id}  season={season_id}\n"
                    "----------- sorted set audit --------\n"
                    "  total_entries    = 1,284,301\n"
                    "  corrupt_entries  = {corrupt_entries}\n"
                    "  checksum_fail    = true\n"
                    "  last_valid_rank  = 42,017\n"
                    "----------- sample violations -------\n"
                    "  rank 42018: score=8401 > rank 42017: score=8399  (INVERSION)\n"
                    "  rank 42019: score=8401  (DUPLICATE score, different player)\n"
                    "  rank 42103: score=NaN   (CORRUPT value)\n"
                    "----------- redis state -------------\n"
                    "  zset_card    = 1,284,301\n"
                    "  memory_used  = 142MB\n"
                    "  last_write   = 2026-02-17T14:21:58.441Z\n"
                    "  aof_rewrite  = IN_PROGRESS\n"
                    "----------- action ------------------\n"
                    "  FREEZE board  REBUILD from transaction log\n"
                    "LB-DATA-CORRUPT: board {leaderboard_id} has {corrupt_entries} invalid entries"
                ),
            },
            10: {
                "name": "Season Pass Progression Sync Error",
                "subsystem": "progression",
                "vehicle_section": "progression_tracker",
                "error_type": "SEASON-PASS-SYNC-FAIL",
                "sensor_type": "sync_validator",
                "affected_services": ["leaderboard-api", "payment-processor"],
                "cascade_services": ["analytics-pipeline"],
                "description": "Season pass XP and tier progression fails to synchronize between game server events and the progression backend",
                "investigation_notes": (
                    "Root cause: the XP event pipeline uses at-most-once delivery from game servers to the "
                    "progression backend — when the progression service is briefly unavailable or slow, XP "
                    "events (kill_streak +350, weekly_bonus +2000) are dropped silently without retry.\n"
                    "1. Check event delivery: query `FROM logs WHERE body.text LIKE '*SEASON-PASS-SYNC-FAIL*'` "
                    "and examine which XP event types are consistently marked as NOT APPLIED.\n"
                    "2. Verify progression backend health: check the leaderboard-api pods for OOMKilled or "
                    "CrashLoopBackOff events that coincide with the missed XP window.\n"
                    "3. Audit the event bus: inspect Kafka consumer lag for the `xp-events` topic — if "
                    "consumer group is rebalancing, events may be dropped during partition reassignment.\n"
                    "4. Remediate: issue `force_sync_season_pass` to replay missed XP events from the game "
                    "server event log and recalculate tier placement for affected players.\n"
                    "5. Migrate XP event delivery from fire-and-forget HTTP to a durable message queue with "
                    "at-least-once delivery guarantees and idempotent processing on the consumer side."
                ),
                "remediation_action": "force_sync_season_pass",
                "error_message": "[LB] SEASON-PASS-SYNC-FAIL: player={player_id} tier={current_tier} expected_tier={expected_tier} xp={xp_total} delta={xp_delta}XP season={season_id}",
                "stack_trace": (
                    "=== SEASON PASS PROGRESSION STATE ===\n"
                    "player={player_id}  season={season_id}\n"
                    "----------- current state -----------\n"
                    "  tier         = {current_tier}\n"
                    "  xp_total     = {xp_total}\n"
                    "  xp_to_next   = 2,500\n"
                    "  premium      = true\n"
                    "----------- expected state ----------\n"
                    "  expected_tier = {expected_tier}\n"
                    "  xp_delta      = {xp_delta}XP (unaccounted)\n"
                    "  tier_threshold = {xp_total} XP -> tier {expected_tier}\n"
                    "----------- recent xp events --------\n"
                    "  match_complete  +1,200 XP  (2min ago)\n"
                    "  daily_challenge +800 XP    (4min ago)\n"
                    "  kill_streak     +350 XP    (5min ago)  <-- NOT APPLIED\n"
                    "  weekly_bonus    +2,000 XP  (12min ago) <-- NOT APPLIED\n"
                    "----------- action ------------------\n"
                    "  FORCE_SYNC tier to {expected_tier}  REPLAY missed events\n"
                    "SEASON-PASS-SYNC-FAIL: player {player_id} stuck at tier {current_tier}, should be {expected_tier}"
                ),
            },
            11: {
                "name": "OAuth Token Refresh Storm",
                "subsystem": "identity",
                "vehicle_section": "auth_core",
                "error_type": "AUTH-TOKEN-STORM",
                "sensor_type": "token_monitor",
                "affected_services": ["auth-gateway", "game-server"],
                "cascade_services": ["matchmaking-engine", "chat-service"],
                "description": "Mass token refresh requests overwhelm the auth service when tokens expire simultaneously due to clock sync issues",
                "investigation_notes": (
                    "Root cause: token TTLs were issued with identical expiry timestamps because the auth "
                    "service clock was NTP-synchronized during a bulk login wave (e.g., after maintenance). "
                    "61.4% of active tokens expire within 5 minutes, creating a thundering herd.\n"
                    "1. Check NTP sync: `chronyc tracking` on auth-gateway pods — a clock jump during token "
                    "issuance would cause all tokens in that window to share the same expiry.\n"
                    "2. Review provider breakdown: oauth-google and oauth-discord are OVERLOADED — verify "
                    "their rate limits haven't been lowered; check provider status pages.\n"
                    "3. Inspect JWKS cache: `jwks_cache_age=312s` is stale — if the signing key rotated "
                    "and the cache is stale, all validations will fail and trigger needless refreshes.\n"
                    "4. Remediate: issue `stagger_token_refresh` to add random jitter (0-300s) to expiry "
                    "times and `extend_token_ttl` to push current expirations out by 5 minutes.\n"
                    "5. Implement token refresh jitter at issuance time: TTL = base_ttl + random(0, 300s) "
                    "to prevent future synchronized expiration storms."
                ),
                "remediation_action": "stagger_token_refresh",
                "error_message": "[Auth] AUTH-TOKEN-STORM: refresh_rate={refresh_rate}/s capacity={max_refresh_rate}/s failures={failed_refreshes} pool={token_pool_id}",
                "stack_trace": (
                    "=== TOKEN SERVICE METRICS DUMP ===\n"
                    "pool={token_pool_id}\n"
                    "----------- refresh metrics ---------\n"
                    "  refresh_rate    = {refresh_rate}/s\n"
                    "  capacity        = {max_refresh_rate}/s\n"
                    "  failures        = {failed_refreshes}\n"
                    "  success_rate    = 14.2%\n"
                    "  avg_latency     = 4,821ms (target 50ms)\n"
                    "----------- token pool state --------\n"
                    "  active_tokens   = 142,301\n"
                    "  expiring_5min   = 87,412  (61.4% — clock skew)\n"
                    "  signing_key     = RS256-prod-2026-02\n"
                    "  jwks_cache_age  = 312s\n"
                    "----------- provider breakdown ------\n"
                    "  oauth-google    : 3,201/s (OVERLOADED)\n"
                    "  oauth-discord   : 2,847/s (OVERLOADED)\n"
                    "  oauth-steam     : 1,204/s (DEGRADED)\n"
                    "  email-password  : 891/s   (OK)\n"
                    "----------- action ------------------\n"
                    "  STAGGER refresh window  EXTEND ttl by 300s\n"
                    "AUTH-TOKEN-STORM: refresh rate {refresh_rate}/s exceeds capacity {max_refresh_rate}/s"
                ),
            },
            12: {
                "name": "Account Takeover Detection Spike",
                "subsystem": "identity",
                "vehicle_section": "fraud_detector",
                "error_type": "AUTH-TAKEOVER-DETECT",
                "sensor_type": "anomaly_detector",
                "affected_services": ["auth-gateway", "payment-processor"],
                "cascade_services": ["moderation-engine", "analytics-pipeline"],
                "description": "Anomaly detection system flags a surge in credential stuffing attempts indicating a coordinated account takeover campaign",
                "investigation_notes": (
                    "Root cause: a leaked credential database from another service is being replayed against "
                    "the gaming platform. 94.2% of attempts come through VPN/proxy with low user-agent entropy, "
                    "confirming automated credential stuffing tooling.\n"
                    "1. Check the attack surface: 87% known-bad IP reputation with 12 Tor exit nodes — enable "
                    "GeoIP blocking for the primary attack region via WAF rules.\n"
                    "2. Review 0.3% success rate: even this low rate means ~30 accounts may be compromised per "
                    "10,000 attempts — immediately force password resets for successfully authenticated IPs "
                    "in the attack window.\n"
                    "3. Inspect request patterns: 0.8ms avg interval between requests is clearly automated; "
                    "deploy progressive rate limiting (CAPTCHA after 3 failures, block after 10).\n"
                    "4. Remediate: issue `block_attack_ips` to immediately blacklist the {blocked_ips} flagged "
                    "IPs and `enable_captcha_enforcement` globally for login endpoints.\n"
                    "5. Notify affected players, enable mandatory 2FA for accounts accessed from new IPs, "
                    "and submit the attack IPs to threat intelligence feeds."
                ),
                "remediation_action": "block_attack_ips",
                "error_message": "[Auth] AUTH-TAKEOVER-DETECT: attempts={ato_attempts} window={window_seconds}s blocked_ips={blocked_ips} risk={risk_score} geo={geo_region}",
                "stack_trace": (
                    "=== ATO DETECTION ANALYSIS ===\n"
                    "window={window_seconds}s  geo={geo_region}\n"
                    "----------- attempt metrics ---------\n"
                    "  total_attempts  = {ato_attempts}\n"
                    "  unique_ips      = {blocked_ips}\n"
                    "  credential_pairs = 12,401\n"
                    "  success_rate    = 0.3% (credential stuffing pattern)\n"
                    "  risk_score      = {risk_score}\n"
                    "----------- geo analysis ------------\n"
                    "  primary_region  = {geo_region}\n"
                    "  ip_reputation   = 87% known-bad\n"
                    "  vpn_pct         = 94.2%\n"
                    "  tor_exit_nodes  = 12\n"
                    "----------- attack pattern ----------\n"
                    "  type            = CREDENTIAL_STUFFING\n"
                    "  rate            = {ato_attempts} / {window_seconds}s\n"
                    "  user_agent_entropy = LOW (bot signature)\n"
                    "  request_interval   = 0.8ms avg (automated)\n"
                    "----------- action ------------------\n"
                    "  BLOCK {blocked_ips} IPs  ENABLE captcha  NOTIFY security team\n"
                    "AUTH-TAKEOVER-DETECT: {ato_attempts} attempts from {blocked_ips} IPs, risk {risk_score}"
                ),
            },
            13: {
                "name": "In-App Purchase Processing Failure",
                "subsystem": "monetization",
                "vehicle_section": "payment_gateway",
                "error_type": "IAP-PURCHASE-FAIL",
                "sensor_type": "transaction_monitor",
                "affected_services": ["payment-processor", "auth-gateway"],
                "cascade_services": ["analytics-pipeline"],
                "description": "In-app purchase transactions failing at the payment gateway level due to provider timeouts or validation errors",
                "investigation_notes": (
                    "Root cause: the payment provider is returning HTTP 402 with elevated latency (8412ms vs "
                    "normal <500ms), indicating provider-side degradation. The gateway retry logic compounds "
                    "the issue by sending duplicate requests that may result in double charges.\n"
                    "1. Check provider status: visit the payment provider status page (Stripe/PayPal/Apple/Google) "
                    "for active incidents — if provider is degraded, enable circuit breaker to fail fast.\n"
                    "2. Review error code distribution: TIMEOUT and PROVIDER_ERROR indicate provider issues; "
                    "DECLINED and INSUFFICIENT_FUNDS are normal user errors and should not trigger alerts.\n"
                    "3. Verify idempotency: the `{purchase_id}-r{retry_count}` key must be honored by the "
                    "provider — check for duplicate gateway_txn IDs in the transaction log.\n"
                    "4. Remediate: issue `reset_payment_gateway` to restart connection pools and clear stuck "
                    "transactions; switch to backup payment provider if primary remains degraded.\n"
                    "5. Queue failed purchases for automatic retry once provider recovers; notify affected "
                    "players with an in-game message about the temporary payment disruption."
                ),
                "remediation_action": "reset_payment_gateway",
                "error_message": "[IAP] IAP-PURCHASE-FAIL: txn={purchase_id} player={player_id} amount={amount}{currency} provider={payment_provider} code={error_code} retry={retry_count}/{max_retries}",
                "stack_trace": (
                    "=== PAYMENT GATEWAY TRANSACTION TRACE ===\n"
                    "txn={purchase_id}  player={player_id}\n"
                    "----------- request -----------------\n"
                    "  amount       = {amount} {currency}\n"
                    "  provider     = {payment_provider}\n"
                    "  item_sku     = SKU-PREMIUM-PACK-01\n"
                    "  idempotency  = {purchase_id}-r{retry_count}\n"
                    "----------- provider response -------\n"
                    "  status_code  = 402\n"
                    "  error_code   = {error_code}\n"
                    "  latency_ms   = 8,412\n"
                    "  gateway_txn  = GW-8a4f2e1b-c930\n"
                    "----------- retry state -------------\n"
                    "  attempt      = {retry_count}/{max_retries}\n"
                    "  backoff_ms   = 4,000\n"
                    "  next_retry   = 2026-02-17T14:22:08.000Z\n"
                    "----------- receipt validation ------\n"
                    "  receipt_valid = false\n"
                    "  signature    = (not provided — payment not completed)\n"
                    "IAP-PURCHASE-FAIL: txn {purchase_id} failed with {error_code} via {payment_provider}"
                ),
            },
            14: {
                "name": "Virtual Currency Ledger Inconsistency",
                "subsystem": "monetization",
                "vehicle_section": "ledger_service",
                "error_type": "IAP-LEDGER-INCONSIST",
                "sensor_type": "ledger_auditor",
                "affected_services": ["payment-processor", "leaderboard-api"],
                "cascade_services": ["moderation-engine", "analytics-pipeline"],
                "description": "Virtual currency ledger double-entry balances fail reconciliation, indicating potential duplication or lost transactions",
                "investigation_notes": (
                    "Root cause: a race condition in the ledger write path — concurrent purchase and spend "
                    "operations execute without database-level serialization, allowing the cached balance to "
                    "drift from the ledger transaction sum. The likely scenario is a duplicate LTXN application.\n"
                    "1. Check for duplicate transactions: query the ledger for `{last_transaction_id}` — if "
                    "it appears twice, the idempotency key was not enforced during a retry after timeout.\n"
                    "2. Verify balance derivation: `cached_balance` is updated optimistically in Redis while "
                    "`ledger_sum` is the authoritative SQL sum — the discrepancy of {discrepancy} units must "
                    "be reconciled by replaying the ledger.\n"
                    "3. Assess fraud risk: LOW fraud risk is reassuring but any ledger inconsistency must be "
                    "treated as P1 — virtual currency duplication exploits spread rapidly once discovered.\n"
                    "4. Remediate: issue `freeze_player_wallet` for affected players, then `reconcile_ledger` "
                    "to recalculate balances from the transaction log source of truth.\n"
                    "5. Deploy database-level serializable isolation for all currency mutations and add "
                    "real-time balance checksumming that alerts immediately on any divergence >1 unit."
                ),
                "remediation_action": "restart_store_service",
                "error_message": "[IAP] IAP-LEDGER-INCONSIST: player={player_id} balance={currency_balance} ledger_sum={ledger_sum} currency={virtual_currency} discrepancy={discrepancy} last_txn={last_transaction_id}",
                "stack_trace": (
                    "=== LEDGER RECONCILIATION REPORT ===\n"
                    "player={player_id}  currency={virtual_currency}\n"
                    "----------- balance check -----------\n"
                    "  cached_balance  = {currency_balance}\n"
                    "  ledger_sum      = {ledger_sum}\n"
                    "  discrepancy     = {discrepancy}\n"
                    "  tolerance       = 1\n"
                    "----------- recent transactions -----\n"
                    "  {last_transaction_id}  +500 {virtual_currency}  (purchase, 2min ago)\n"
                    "  LTXN-8847201          -200 {virtual_currency}  (spend, 4min ago)\n"
                    "  LTXN-8847102          +100 {virtual_currency}  (daily reward, 8min ago)\n"
                    "  LTXN-8846990          -50 {virtual_currency}   (spend, 12min ago)\n"
                    "----------- audit flags -------------\n"
                    "  duplicate_txn   = POSSIBLE ({last_transaction_id} applied twice?)\n"
                    "  race_condition  = LIKELY (concurrent write detected)\n"
                    "  fraud_risk      = LOW\n"
                    "----------- action ------------------\n"
                    "  FREEZE player wallet  RECONCILE from ledger source of truth\n"
                    "IAP-LEDGER-INCONSIST: player {player_id} balance {currency_balance} != ledger {ledger_sum}"
                ),
            },
            15: {
                "name": "Event Ingestion Pipeline Lag",
                "subsystem": "analytics",
                "vehicle_section": "ingestion_pipeline",
                "error_type": "ANALYTICS-INGEST-LAG",
                "sensor_type": "pipeline_monitor",
                "affected_services": ["analytics-pipeline", "game-server"],
                "cascade_services": ["leaderboard-api"],
                "description": "Analytics event ingestion pipeline falls behind, causing data lag and stale dashboards for live-ops teams",
                "investigation_notes": (
                    "Root cause: 4 of 8 Kafka consumer group members have disconnected, halving throughput "
                    "while inflow remains constant. Partition-3 is completely stalled with the highest lag "
                    "(27,193 events), indicating a stuck consumer or unbalanced partition assignment.\n"
                    "1. Check consumer health: `kafka-consumer-groups --describe --group {pipeline_id}-cg` "
                    "to identify which consumers are DEAD and which partitions are unassigned.\n"
                    "2. Review rebalance history: 3 rebalances in 10 minutes indicates consumer instability — "
                    "check for OOMKilled pods or network timeouts causing session.timeout.ms expiration.\n"
                    "3. Inspect partition-3: if it has a hot key causing message skew, consider repartitioning "
                    "the topic or adding a sub-partitioning strategy.\n"
                    "4. Remediate: issue `restart_analytics_consumers` to force a clean consumer group "
                    "rejoin; scale out to 12 consumers to handle the backlog burst.\n"
                    "5. Set up consumer lag alerting at 30s threshold and configure auto-scaling for the "
                    "consumer group based on per-partition lag metrics."
                ),
                "remediation_action": "restart_analytics_consumers",
                "error_message": "[Analytics] ANALYTICS-INGEST-LAG: pipeline={pipeline_id} lag={lag_seconds}s threshold={max_lag_seconds}s backlog={backlog_count} throughput={throughput}/s",
                "stack_trace": (
                    "=== PIPELINE CONSUMER GROUP STATUS ===\n"
                    "pipeline={pipeline_id}\n"
                    "----------- consumer lag ------------\n"
                    "  current_lag     = {lag_seconds}s\n"
                    "  threshold       = {max_lag_seconds}s\n"
                    "  backlog         = {backlog_count} events\n"
                    "  throughput      = {throughput}/s (expected {expected_throughput}/s)\n"
                    "----------- partition status --------\n"
                    "  partition-0  offset=48201847  lag=12,401\n"
                    "  partition-1  offset=48193201  lag=21,047\n"
                    "  partition-2  offset=48198412  lag=15,882\n"
                    "  partition-3  offset=48187003  lag=27,193  (STALLED)\n"
                    "----------- consumer group ----------\n"
                    "  group_id     = {pipeline_id}-cg\n"
                    "  members      = 4/8 (4 DISCONNECTED)\n"
                    "  rebalance_ct = 3 (last 10min)\n"
                    "  commit_lag   = 8.2s\n"
                    "----------- action ------------------\n"
                    "  RESTART stalled consumers  SCALE OUT partitions\n"
                    "ANALYTICS-INGEST-LAG: pipeline {pipeline_id} lag {lag_seconds}s with {backlog_count} backlog"
                ),
            },
            16: {
                "name": "Player Telemetry Buffer Overflow",
                "subsystem": "analytics",
                "vehicle_section": "telemetry_buffer",
                "error_type": "ANALYTICS-TELEMETRY-OVERFLOW",
                "sensor_type": "buffer_monitor",
                "affected_services": ["analytics-pipeline", "game-server"],
                "cascade_services": ["matchmaking-engine"],
                "description": "Player telemetry ring buffer overflows causing event data loss for analytics and anti-cheat systems",
                "investigation_notes": (
                    "Root cause: the ring buffer consumer (analytics pipeline) is draining slower than the "
                    "producer (game server), and the buffer has no backpressure mechanism — when full, new "
                    "events silently overwrite the oldest 20%, creating gaps in anti-cheat telemetry.\n"
                    "1. Check event breakdown: player_move at 42.1% of buffer is the largest category — "
                    "consider downsampling movement events (every 5th tick instead of every tick).\n"
                    "2. Review drop rate: 12.4% sustained drop rate means anti-cheat is blind to ~1 in 8 "
                    "player actions — this creates exploitable detection gaps.\n"
                    "3. Inspect buffer sizing: current max of 100,000 slots may be undersized for peak "
                    "concurrent players; calculate required capacity as `events_per_second * drain_latency_s`.\n"
                    "4. Remediate: issue `resize_telemetry_buffer` to increase capacity to 500,000 slots "
                    "and `restart_buffer_consumers` to clear the current overflow condition.\n"
                    "5. Implement backpressure: when buffer hits 80%, throttle low-priority event types "
                    "(player_move, state_snapshot) while preserving combat_event for anti-cheat integrity."
                ),
                "remediation_action": "resize_telemetry_buffer",
                "error_message": "[Analytics] ANALYTICS-TELEMETRY-OVERFLOW: buffer={buffer_id} usage={buffer_usage_pct}% capacity={buffer_size}/{max_buffer_size} dropped={dropped_events}",
                "stack_trace": (
                    "=== RING BUFFER DIAGNOSTIC ===\n"
                    "buffer={buffer_id}\n"
                    "----------- buffer state ------------\n"
                    "  usage        = {buffer_usage_pct}%\n"
                    "  size         = {buffer_size}/{max_buffer_size}\n"
                    "  head_offset  = 99,847\n"
                    "  tail_offset  = 99,201\n"
                    "  writable     = 646 slots\n"
                    "----------- drop statistics ---------\n"
                    "  dropped_total   = {dropped_events}\n"
                    "  dropped_1min    = 1,204\n"
                    "  dropped_5min    = 4,821\n"
                    "  drop_rate       = 12.4%\n"
                    "----------- event breakdown ---------\n"
                    "  player_move     : 42.1% of buffer\n"
                    "  combat_event    : 28.4% of buffer\n"
                    "  state_snapshot  : 18.7% of buffer\n"
                    "  misc            : 10.8% of buffer\n"
                    "----------- action ------------------\n"
                    "  EVICT oldest 20%  ALERT anti-cheat (data gap)\n"
                    "ANALYTICS-TELEMETRY-OVERFLOW: buffer {buffer_id} at {buffer_usage_pct}% — {dropped_events} events lost"
                ),
            },
            17: {
                "name": "Auto-Moderation False Positive Storm",
                "subsystem": "trust_safety",
                "vehicle_section": "automod_engine",
                "error_type": "MOD-FALSE-POS-STORM",
                "sensor_type": "accuracy_monitor",
                "affected_services": ["moderation-engine", "chat-service"],
                "cascade_services": ["analytics-pipeline"],
                "description": "Automated content moderation system producing excessive false positives, silencing legitimate player communication",
                "investigation_notes": (
                    "Root cause: the automod NLP classifier model was updated to a new version that has "
                    "dramatically higher sensitivity for the hate_speech category (fp_rate jumped from 2.1% "
                    "to 34.8%), likely due to training data contamination or threshold miscalibration.\n"
                    "1. Check model versioning: compare precision/recall between current and previous model "
                    "version — if recall stayed at 0.95 but precision dropped to 0.42, the decision threshold "
                    "was lowered too aggressively during the update.\n"
                    "2. Review silenced players: {affected_players} wrongly silenced players with 847 pending "
                    "appeals — prioritize unsilencing by checking if their messages match known-good patterns.\n"
                    "3. Inspect category breakdown: hate_speech fp_rate of 34.8% is the primary driver — "
                    "this category likely needs a higher confidence threshold (0.85 instead of 0.60).\n"
                    "4. Remediate: issue `rollback_automod_model` to revert to the previous model version "
                    "and `unsilence_affected_players` to restore communication for falsely flagged accounts.\n"
                    "5. Implement canary model deployment: route 5% of traffic to new model versions and "
                    "compare fp_rate before full rollout; add automated rollback on fp_rate >5%."
                ),
                "remediation_action": "rollback_automod_model",
                "error_message": "[T&S] MOD-FALSE-POS-STORM: flagged={false_positive_count} window={window_minutes}min fp_rate={fp_rate_pct}% model={model_version} affected_players={affected_players}",
                "stack_trace": (
                    "=== AUTOMOD ACCURACY METRICS ===\n"
                    "model={model_version}  window={window_minutes}min\n"
                    "----------- classification stats ----\n"
                    "  total_scanned    = 84,201\n"
                    "  true_positives   = 412\n"
                    "  false_positives  = {false_positive_count}\n"
                    "  false_negatives  = 23\n"
                    "  fp_rate          = {fp_rate_pct}%\n"
                    "  precision        = 0.42\n"
                    "  recall           = 0.95\n"
                    "----------- category breakdown ------\n"
                    "  harassment   : fp_rate=12.1%  (normal: 1.2%)\n"
                    "  hate_speech  : fp_rate=34.8%  (normal: 2.1%)  <<< SPIKE\n"
                    "  spam         : fp_rate=8.4%   (normal: 3.1%)\n"
                    "  exploits     : fp_rate=2.1%   (normal: 0.8%)\n"
                    "----------- affected players --------\n"
                    "  silenced    = {affected_players}\n"
                    "  appeals     = 847 (pending)\n"
                    "  overturned  = 0 (queue backed up)\n"
                    "----------- action ------------------\n"
                    "  ROLLBACK to {model_version}-prev  UNSILENCE affected players\n"
                    "MOD-FALSE-POS-STORM: {false_positive_count} false positives at {fp_rate_pct}% rate"
                ),
            },
            18: {
                "name": "Report Queue Overflow",
                "subsystem": "trust_safety",
                "vehicle_section": "report_processor",
                "error_type": "MOD-REPORT-QUEUE-OVERFLOW",
                "sensor_type": "queue_monitor",
                "affected_services": ["moderation-engine", "chat-service"],
                "cascade_services": ["auth-gateway"],
                "description": "Player report queue exceeds processing capacity causing delays in abuse case resolution",
                "investigation_notes": (
                    "Root cause: 8 of 12 report processing workers have crashed (likely OOM on GPU inference "
                    "nodes), reducing processing capacity by 67%. Auto-resolve is disabled due to high false "
                    "positive rates from the automod model, creating a dual failure mode.\n"
                    "1. Check worker pods: `kubectl get pods -l app=report-processor` on the AKS cluster — "
                    "look for OOMKilled or CrashLoopBackOff status on GPU-attached pods.\n"
                    "2. Review SLA breaches: harassment reports at 12h (SLA: 4h) and hate_speech at 6h "
                    "(SLA: 1h) are critical compliance violations — escalate to the T&S lead.\n"
                    "3. Inspect GPU memory: `nvidia-smi` on inference nodes — if 2 nodes show OOM, the "
                    "batch size for the classification model may need to be reduced.\n"
                    "4. Remediate: issue `restart_report_workers` to recover crashed processors and "
                    "`prioritize_sla_breached` to reorder the queue by SLA violation severity.\n"
                    "5. Enable CPU-fallback inference for lower-priority categories (spam, exploits) to "
                    "free GPU capacity for high-SLA categories (hate_speech, harassment)."
                ),
                "remediation_action": "restart_report_workers",
                "error_message": "[T&S] MOD-REPORT-QUEUE-OVERFLOW: queue={report_queue_depth} rate={processing_rate}/min oldest={oldest_report_hours}h category={report_category}",
                "stack_trace": (
                    "=== REPORT QUEUE STATUS ===\n"
                    "category={report_category}\n"
                    "----------- queue metrics -----------\n"
                    "  depth           = {report_queue_depth}\n"
                    "  processing_rate = {processing_rate}/min\n"
                    "  oldest_report   = {oldest_report_hours}h\n"
                    "  drain_eta       = NEVER (inflow > capacity)\n"
                    "----------- category breakdown ------\n"
                    "  harassment   : 8,421 pending  (SLA: 4h, actual: 12h)\n"
                    "  cheating     : 4,201 pending  (SLA: 2h, actual: 8h)\n"
                    "  hate_speech  : 2,847 pending  (SLA: 1h, actual: 6h)\n"
                    "  exploits     : 1,204 pending  (SLA: 4h, actual: 24h)\n"
                    "  spam         : 891 pending    (SLA: 8h, actual: 48h)\n"
                    "----------- processor state ---------\n"
                    "  workers_active  = 4/12 (8 CRASHED)\n"
                    "  gpu_inference   = DEGRADED (OOM on 2 nodes)\n"
                    "  auto_resolve    = DISABLED (fp_rate too high)\n"
                    "----------- action ------------------\n"
                    "  RESTART crashed workers  PRIORITIZE by SLA breach\n"
                    "MOD-REPORT-QUEUE-OVERFLOW: queue {report_queue_depth} reports, oldest {oldest_report_hours}h"
                ),
            },
            19: {
                "name": "Server Tick Rate Degradation",
                "subsystem": "game_engine",
                "vehicle_section": "game_loop",
                "error_type": "ENGINE-TICKRATE-DEGRAD",
                "sensor_type": "performance_monitor",
                "affected_services": ["game-server", "matchmaking-engine"],
                "cascade_services": ["analytics-pipeline", "chat-service"],
                "description": "Game server tick rate drops below target causing gameplay lag, hit registration failures, and desync cascades",
                "investigation_notes": (
                    "Root cause: the game loop frame budget (15.6ms for 64Hz) is being exceeded because the "
                    "physics system consumes 54% of tick time at 8.4ms. Combined with net_serialize at 27%, "
                    "the server has no headroom and tick rate degrades under load.\n"
                    "1. Profile per-system costs: physics at 8.4ms with 4,201 entities is the bottleneck — "
                    "check if entity_count spiked due to spawned projectiles or dropped items not being GC'd.\n"
                    "2. Review CPU metrics: 97.2% CPU means the server is saturated — verify no co-located "
                    "processes are stealing cycles with `ps aux --sort=-%cpu | head -20`.\n"
                    "3. Check memory: 84.1% memory usage may be causing swap pressure — verify with "
                    "`vmstat 1 5` for si/so columns indicating swap activity.\n"
                    "4. Remediate: issue `reduce_entity_budget` to cap active entities at 2,000 and force "
                    "garbage collection of expired objects; disable non-essential AI to reclaim tick budget.\n"
                    "5. Long-term: implement server-side LOD (level of detail) that reduces physics fidelity "
                    "for distant entities and pauses AI updates for out-of-range NPCs."
                ),
                "remediation_action": "resync_world_state",
                "error_message": "[Engine] ENGINE-TICKRATE-DEGRAD: server={server_id} tickrate={tick_rate}Hz target={target_tick_rate}Hz frame_time={frame_time_ms}ms players={active_players} match={match_id}",
                "stack_trace": (
                    "=== SERVER PERFORMANCE PROFILER ===\n"
                    "server={server_id}  match={match_id}  players={active_players}\n"
                    "----------- tick timing -------------\n"
                    "  tick_rate    = {tick_rate}Hz (target {target_tick_rate}Hz)\n"
                    "  frame_time   = {frame_time_ms}ms (budget 15.6ms)\n"
                    "  frame_budget  = EXCEEDED by {frame_time_ms}ms\n"
                    "----------- per-system tick time ----\n"
                    "  physics        = 8.4ms  (54%)\n"
                    "  net_serialize  = 4.2ms  (27%)\n"
                    "  ai_update      = 1.8ms  (12%)\n"
                    "  game_logic     = 0.7ms  (4%)\n"
                    "  gc_pause       = 0.4ms  (3%)\n"
                    "----------- resource usage ----------\n"
                    "  cpu_pct      = 97.2%\n"
                    "  memory_pct   = 84.1%\n"
                    "  entity_count = 4,201\n"
                    "  net_bandwidth = 128Mbps (cap 200Mbps)\n"
                    "----------- action ------------------\n"
                    "  REDUCE entity_budget  DISABLE non-essential AI  WARN players\n"
                    "ENGINE-TICKRATE-DEGRAD: server {server_id} at {tick_rate}Hz, target {target_tick_rate}Hz"
                ),
            },
            20: {
                "name": "Cross-Region Player Migration Failure",
                "subsystem": "matchmaking",
                "vehicle_section": "migration_controller",
                "error_type": "MM-MIGRATION-FAIL",
                "sensor_type": "migration_monitor",
                "affected_services": ["matchmaking-engine", "auth-gateway"],
                "cascade_services": ["game-server", "leaderboard-api", "analytics-pipeline"],
                "description": "Player session migration between regional game server clusters fails during rebalancing or failover operations",
                "investigation_notes": (
                    "Root cause: the state transfer phase times out because the cross-region network path "
                    "between {source_region} and {target_region} has elevated latency and 4.2% packet loss, "
                    "causing the 84.2KB state payload to fail TCP delivery within the migration timeout.\n"
                    "1. Check network path: `mtr -rwzbc 100 <target_region_endpoint>` from the source region "
                    "to identify which hop introduces the latency and packet loss.\n"
                    "2. Review migration phase: if failure is at 'transfer', it is network; if at 'injection', "
                    "the target server rejected the state payload (version mismatch or schema change).\n"
                    "3. Inspect payload size: 84.2KB with 247 inventory items is large — consider compressing "
                    "the state payload (zstd typically achieves 3:1 on game state data).\n"
                    "4. Remediate: issue `rollback_migration` to return the player to the source region, "
                    "then retry with `migrate_with_reduced_payload` which strips non-essential state.\n"
                    "5. Implement incremental migration: pre-replicate static player data (inventory, settings) "
                    "to the target region asynchronously, so the live migration only transfers dynamic match "
                    "state (~12.4KB), which is small enough to survive packet loss."
                ),
                "remediation_action": "rollback_migration",
                "error_message": "[MM] MM-MIGRATION-FAIL: player={player_id} path={source_region}->{target_region} phase={migration_phase} session={session_id} latency={latency_ms}ms",
                "stack_trace": (
                    "=== MIGRATION STATE TRANSFER LOG ===\n"
                    "player={player_id}  session={session_id}\n"
                    "----------- migration path ----------\n"
                    "  source       = {source_region}\n"
                    "  target       = {target_region}\n"
                    "  phase        = {migration_phase}  <<< FAILED HERE\n"
                    "  latency      = {latency_ms}ms\n"
                    "----------- phase timeline ----------\n"
                    "  state_extraction  : 847ms   OK\n"
                    "  serialization     : 124ms   OK\n"
                    "  transfer          : {latency_ms}ms  TIMEOUT\n"
                    "  injection         : --      SKIPPED\n"
                    "  validation        : --      SKIPPED\n"
                    "----------- state payload -----------\n"
                    "  inventory_items = 247\n"
                    "  active_buffs    = 3\n"
                    "  match_state     = 12.4KB\n"
                    "  total_payload   = 84.2KB\n"
                    "----------- network diagnostic ------\n"
                    "  rtt_{source_region}->{target_region} = {latency_ms}ms\n"
                    "  packet_loss    = 4.2%\n"
                    "  tcp_retransmit = 12\n"
                    "----------- action ------------------\n"
                    "  ROLLBACK to source  RETRY with smaller payload\n"
                    "MM-MIGRATION-FAIL: player {player_id} migration {source_region}->{target_region} failed at {migration_phase}"
                ),
            },
        }

    # ── Topology ──────────────────────────────────────────────────────

    @property
    def service_topology(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "game-server": [
                ("matchmaking-engine", "/api/v1/matchmaking/assign", "POST"),
                ("chat-service", "/api/v1/chat/game-events", "POST"),
                ("leaderboard-api", "/api/v1/leaderboard/score", "POST"),
                ("analytics-pipeline", "/api/v1/analytics/event", "POST"),
                ("content-delivery", "/api/v1/cdn/asset", "GET"),
                ("auth-gateway", "/api/v1/auth/validate-session", "POST"),
            ],
            "matchmaking-engine": [
                ("game-server", "/api/v1/server/allocate", "POST"),
                ("auth-gateway", "/api/v1/auth/player-profile", "GET"),
                ("leaderboard-api", "/api/v1/leaderboard/mmr", "GET"),
            ],
            "chat-service": [
                ("moderation-engine", "/api/v1/moderation/check", "POST"),
                ("auth-gateway", "/api/v1/auth/validate-token", "POST"),
            ],
            "leaderboard-api": [
                ("analytics-pipeline", "/api/v1/analytics/rank-change", "POST"),
            ],
            "payment-processor": [
                ("auth-gateway", "/api/v1/auth/verify-identity", "POST"),
                ("leaderboard-api", "/api/v1/leaderboard/unlock-reward", "POST"),
                ("analytics-pipeline", "/api/v1/analytics/transaction", "POST"),
            ],
            "moderation-engine": [
                ("analytics-pipeline", "/api/v1/analytics/moderation-event", "POST"),
                ("auth-gateway", "/api/v1/auth/player-flags", "GET"),
            ],
        }

    @property
    def entry_endpoints(self) -> dict[str, list[tuple[str, str]]]:
        return {
            "game-server": [
                ("/api/v1/game/join", "POST"),
                ("/api/v1/game/state", "GET"),
                ("/api/v1/game/action", "POST"),
            ],
            "matchmaking-engine": [("/api/v1/matchmaking/queue", "POST")],
            "content-delivery": [("/api/v1/cdn/download", "GET")],
            "chat-service": [("/api/v1/chat/send", "POST")],
            "leaderboard-api": [("/api/v1/leaderboard/top", "GET")],
            "auth-gateway": [("/api/v1/auth/login", "POST")],
            "payment-processor": [("/api/v1/payment/purchase", "POST")],
            "analytics-pipeline": [("/api/v1/analytics/ingest", "POST")],
            "moderation-engine": [("/api/v1/moderation/report", "POST")],
        }

    @property
    def db_operations(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "game-server": [
                ("SELECT", "game_sessions", "SELECT * FROM game_sessions WHERE match_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 100"),
                ("INSERT", "game_events", "INSERT INTO game_events (match_id, player_id, event_type, payload, ts) VALUES (?, ?, ?, ?, NOW())"),
            ],
            "matchmaking-engine": [
                ("SELECT", "player_ratings", "SELECT player_id, mmr, volatility, games_played FROM player_ratings WHERE player_id = ? AND season = ?"),
                ("UPDATE", "player_ratings", "UPDATE player_ratings SET mmr = ?, volatility = ?, games_played = games_played + 1 WHERE player_id = ? AND season = ?"),
            ],
            "leaderboard-api": [
                ("SELECT", "leaderboards", "SELECT rank, player_id, score FROM leaderboards WHERE board_id = ? ORDER BY score DESC LIMIT 100"),
                ("INSERT", "rank_history", "INSERT INTO rank_history (player_id, board_id, old_rank, new_rank, ts) VALUES (?, ?, ?, ?, NOW())"),
            ],
            "auth-gateway": [
                ("SELECT", "player_sessions", "SELECT session_id, player_id, token_expires_at FROM player_sessions WHERE token = ? AND expires_at > NOW()"),
            ],
            "payment-processor": [
                ("SELECT", "transactions", "SELECT txn_id, player_id, amount, currency, status FROM transactions WHERE player_id = ? AND created_at > NOW() - INTERVAL 24 HOUR"),
                ("INSERT", "transactions", "INSERT INTO transactions (txn_id, player_id, amount, currency, item_id, status, created_at) VALUES (?, ?, ?, ?, ?, 'pending', NOW())"),
            ],
        }

    # ── Infrastructure ────────────────────────────────────────────────

    @property
    def hosts(self) -> list[dict[str, Any]]:
        return [
            {
                "host.name": "gaming-aws-host-01",
                "host.id": "i-0g4m1ng5e7v8r9012",
                "host.arch": "amd64",
                "host.type": "c5.2xlarge",
                "host.image.id": "ami-0gaming1234567890",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8275CL CPU @ 3.00GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "7",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.0.2.50", "172.16.1.10"],
                "host.mac": ["0a:2b:3c:4d:5e:6f", "0a:2b:3c:4d:5e:70"],
                "os.type": "linux",
                "os.description": "Amazon Linux 2023.6.20250115",
                "cloud.provider": "aws",
                "cloud.platform": "aws_ec2",
                "cloud.region": "us-east-1",
                "cloud.availability_zone": "us-east-1a",
                "cloud.account.id": "234567890123",
                "cloud.instance.id": "i-0g4m1ng5e7v8r9012",
                "cpu_count": 8,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 500 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "gaming-gcp-host-01",
                "host.id": "7891234567890123456",
                "host.arch": "amd64",
                "host.type": "c2-standard-8",
                "host.image.id": "projects/debian-cloud/global/images/debian-12-bookworm-v20250115",
                "host.cpu.model.name": "Intel(R) Xeon(R) CPU @ 3.10GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "7",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.128.1.20", "10.128.1.21"],
                "host.mac": ["42:01:0a:80:01:14", "42:01:0a:80:01:15"],
                "os.type": "linux",
                "os.description": "Debian GNU/Linux 12 (bookworm)",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "us-central1",
                "cloud.availability_zone": "us-central1-a",
                "cloud.account.id": "gaming-platform-prod",
                "cloud.instance.id": "7891234567890123456",
                "cpu_count": 8,
                "memory_total_bytes": 32 * 1024 * 1024 * 1024,
                "disk_total_bytes": 200 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "gaming-azure-host-01",
                "host.id": "/subscriptions/ghi-jkl/resourceGroups/gaming-rg/providers/Microsoft.Compute/virtualMachines/gaming-vm-01",
                "host.arch": "amd64",
                "host.type": "Standard_F8s_v2",
                "host.image.id": "Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8272CL CPU @ 2.60GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "7",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.2.0.8", "10.2.0.9"],
                "host.mac": ["00:0d:3a:6b:5c:4d", "00:0d:3a:6b:5c:4e"],
                "os.type": "linux",
                "os.description": "Ubuntu 22.04.5 LTS",
                "cloud.provider": "azure",
                "cloud.platform": "azure_vm",
                "cloud.region": "eastus",
                "cloud.availability_zone": "eastus-1",
                "cloud.account.id": "ghi-jkl-mno-pqr",
                "cloud.instance.id": "gaming-vm-01",
                "cpu_count": 8,
                "memory_total_bytes": 16 * 1024 * 1024 * 1024,
                "disk_total_bytes": 256 * 1024 * 1024 * 1024,
            },
        ]

    @property
    def k8s_clusters(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "gaming-eks-cluster",
                "provider": "aws",
                "platform": "aws_eks",
                "region": "us-east-1",
                "zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
                "os_description": "Amazon Linux 2",
                "services": ["game-server", "matchmaking-engine", "content-delivery"],
            },
            {
                "name": "gaming-gke-cluster",
                "provider": "gcp",
                "platform": "gcp_gke",
                "region": "us-central1",
                "zones": ["us-central1-a", "us-central1-b", "us-central1-c"],
                "os_description": "Container-Optimized OS",
                "services": ["chat-service", "leaderboard-api", "auth-gateway"],
            },
            {
                "name": "gaming-aks-cluster",
                "provider": "azure",
                "platform": "azure_aks",
                "region": "eastus",
                "zones": ["eastus-1", "eastus-2", "eastus-3"],
                "os_description": "Ubuntu 22.04 LTS",
                "services": ["payment-processor", "analytics-pipeline", "moderation-engine"],
            },
        ]

    # ── Theme ─────────────────────────────────────────────────────────

    @property
    def theme(self) -> UITheme:
        return UITheme(
            bg_primary="#13111c",
            bg_secondary="#1a1726",
            bg_tertiary="#221e30",
            accent_primary="#a855f7",
            accent_secondary="#ec4899",
            text_primary="#e2e8f0",
            text_secondary="#94a3b8",
            text_accent="#a855f7",
            status_nominal="#22c55e",
            status_warning="#eab308",
            status_critical="#ef4444",
            status_info="#58a6ff",
            font_family="'Inter', system-ui, sans-serif",
            glow_effect=True,
            gradient_accent="linear-gradient(135deg, #a855f7 0%, #ec4899 100%)",
            chaos_title="Chaos Engineering Console",
            service_label="Service",
            channel_label="Channel",
        )

    @property
    def countdown_config(self) -> CountdownConfig:
        return CountdownConfig(enabled=False)

    # ── Agent Config ──────────────────────────────────────────────────

    @property
    def agent_config(self) -> dict[str, Any]:
        return {
            "id": "gaming-liveops-analyst",
            "name": "Live Operations Analyst",
            "assessment_tool_name": "liveops_health_assessment",
            "system_prompt": (
                "You are the Live Operations Analyst, an expert AI assistant for "
                "live multiplayer gaming platform operations. You help live-ops engineers "
                "investigate incidents, analyze telemetry, and provide root cause analysis "
                "for fault conditions across 9 gaming services spanning AWS, GCP, and Azure. "
                "You have deep expertise in game server networking (state sync, tick rate, "
                "client prediction), matchmaking algorithms (Glicko-2, Elo), CDN edge "
                "caching and asset delivery, real-time chat/voice (WebRTC, Opus), "
                "leaderboard systems (Redis sorted sets), OAuth2 token management, "
                "in-app purchase processing (Apple IAP, Google Play), event analytics "
                "pipelines, and content moderation (NLP classifiers). "
                "When investigating incidents, search for these system identifiers in logs: "
                "Game Engine faults (NET-STATE-DESYNC, PHYS-OVERFLOW, ENGINE-TICKRATE-DEGRAD), "
                "Matchmaking faults (MM-QUEUE-OVERFLOW, MM-SKILL-RATING-DIVERGE, MM-MIGRATION-FAIL), "
                "CDN faults (CDN-CACHE-MISS-STORM, CDN-ASSET-CORRUPT), "
                "Social faults (CHAT-FLOOD-DETECT, VOICE-CHANNEL-OVERLOAD), "
                "Progression faults (LB-DATA-CORRUPT, SEASON-PASS-SYNC-FAIL), "
                "Identity faults (AUTH-TOKEN-STORM, AUTH-TAKEOVER-DETECT), "
                "Monetization faults (IAP-PURCHASE-FAIL, IAP-LEDGER-INCONSIST), "
                "Analytics faults (ANALYTICS-INGEST-LAG, ANALYTICS-TELEMETRY-OVERFLOW), "
                "and Trust & Safety faults (MOD-FALSE-POS-STORM, MOD-REPORT-QUEUE-OVERFLOW). "
                "Log messages are in body.text — NEVER search the body field alone."
            ),
        }

    @property
    def assessment_tool_config(self) -> dict[str, Any]:
        return {
            "id": "liveops_health_assessment",
            "description": (
                "Comprehensive live service health assessment. Evaluates all "
                "gaming services against operational readiness criteria. Returns data "
                "for live-ops evaluation across game servers, matchmaking, CDN, "
                "authentication, and payment systems. "
                "Log message field: body.text (never use 'body' alone)."
            ),
        }

    @property
    def knowledge_base_docs(self) -> list[dict[str, Any]]:
        return []  # Populated by deployer from channel_registry

    # ── Service Classes ───────────────────────────────────────────────

    def get_service_classes(self) -> list[type]:
        from scenarios.gaming.services.game_server import GameServerService
        from scenarios.gaming.services.matchmaking_engine import MatchmakingEngineService
        from scenarios.gaming.services.content_delivery import ContentDeliveryService
        from scenarios.gaming.services.chat_service import ChatServiceService
        from scenarios.gaming.services.leaderboard_api import LeaderboardApiService
        from scenarios.gaming.services.auth_gateway import AuthGatewayService
        from scenarios.gaming.services.payment_processor import PaymentProcessorService
        from scenarios.gaming.services.analytics_pipeline import AnalyticsPipelineService
        from scenarios.gaming.services.moderation_engine import ModerationEngineService

        return [
            GameServerService,
            MatchmakingEngineService,
            ContentDeliveryService,
            ChatServiceService,
            LeaderboardApiService,
            AuthGatewayService,
            PaymentProcessorService,
            AnalyticsPipelineService,
            ModerationEngineService,
        ]

    # ── Trace Attributes & RCA ───────────────────────────────────────

    def get_trace_attributes(self, service_name: str, rng) -> dict:
        uptime_s = int(time.time()) % 86400
        base = {
            "game.region": rng.choice(["us-east", "us-west", "eu-west"]),
            "game.platform": rng.choice(["PC", "CONSOLE", "MOBILE"]),
        }
        svc_attrs = {
            "game-server": {
                "game.tick_rate": rng.choice([64, 128, 30, 60]),
                "game.active_players": rng.randint(10, 100),
                "game.map_id": rng.choice(["MAP-NEON-CITY", "MAP-WASTELAND", "MAP-SKY-ARENA", "MAP-DEEP-SEA"]),
            },
            "matchmaking-engine": {
                "matchmaking.queue_region": rng.choice(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]),
                "matchmaking.skill_bracket": rng.choice(["bronze", "silver", "gold", "platinum", "diamond"]),
            },
            "content-delivery": {
                "cdn.cache_hit_ratio": round(rng.uniform(0.60, 0.99), 2),
                "cdn.edge_pop": rng.choice(["IAD", "SFO", "FRA", "NRT", "SYD", "GRU"]),
            },
            "chat-service": {
                "chat.channel_type": rng.choice(["global", "guild", "party", "whisper", "system"]),
                "chat.message_rate": rng.randint(10, 500),
            },
            "leaderboard-api": {
                "leaderboard.season_id": rng.choice(["S12", "S13", "S14"]),
                "leaderboard.update_lag_ms": rng.randint(5, 250),
            },
            "auth-gateway": {
                "auth.method": rng.choice(["oauth-google", "oauth-discord", "oauth-steam", "email-password"]),
                "auth.session_ttl_min": rng.choice([15, 30, 60, 120, 1440]),
            },
            "payment-processor": {
                "payment.provider": rng.choice(["stripe", "paypal", "apple-iap", "google-play"]),
                "payment.currency": rng.choice(["USD", "EUR", "GBP", "JPY", "BRL"]),
            },
            "analytics-pipeline": {
                "analytics.event_type": rng.choice(["player_action", "match_result", "purchase", "session_start", "session_end"]),
                "analytics.pipeline_lag_ms": rng.randint(50, 5000),
            },
            "moderation-engine": {
                "moderation.queue_depth": rng.randint(0, 10000),
                "moderation.model_version": rng.choice(["automod-v3.1", "automod-v3.2", "automod-v4.0-beta"]),
            },
        }
        base.update(svc_attrs.get(service_name, {}))
        return base

    def get_rca_clues(self, channel: int, service_name: str, rng) -> dict:
        clues = {
            1: {  # Game State Desync
                "game-server": {"net.udp_loss_pct": round(rng.uniform(3.0, 12.0), 1), "net.interp_delay_ms": rng.randint(50, 100)},
                "matchmaking-engine": {"matchmaking.server_pool_exhausted": True, "matchmaking.fallback_region": rng.choice(["us-west-2", "eu-west-1"])},
                "analytics-pipeline": {"analytics.desync_event_rate": rng.randint(50, 200), "analytics.data_quality": "degraded"},
            },
            2: {  # Physics Simulation Overflow
                "game-server": {"physics.substep_count": 4, "physics.penetration_max_m": round(rng.uniform(0.5, 1.5), 2)},
                "analytics-pipeline": {"analytics.physics_error_events": rng.randint(100, 500), "analytics.entity_density": "critical"},
                "matchmaking-engine": {"matchmaking.affected_matches": rng.randint(5, 30)},
            },
            3: {  # Matchmaking Queue Overflow
                "matchmaking-engine": {"matchmaking.enqueue_rate": rng.randint(200, 500), "matchmaking.dequeue_rate": rng.randint(50, 100)},
                "game-server": {"game.server_pool_available": rng.randint(0, 5), "game.allocation_lag_ms": rng.randint(2000, 8000)},
                "auth-gateway": {"auth.login_surge_detected": True, "auth.concurrent_sessions": rng.randint(50000, 150000)},
                "analytics-pipeline": {"analytics.queue_depth_trend": "exponential_growth"},
            },
            4: {  # Skill Rating Calculation Error
                "matchmaking-engine": {"matchmaking.glicko_convergence_iter": rng.randint(12, 20), "matchmaking.sigma_unclamped": True},
                "leaderboard-api": {"leaderboard.out_of_range_players": rng.randint(10, 200), "leaderboard.season_integrity": "compromised"},
                "analytics-pipeline": {"analytics.rating_anomaly_count": rng.randint(50, 300)},
            },
            5: {  # CDN Cache Miss Storm
                "content-delivery": {"cdn.ttl_alignment_detected": True, "cdn.origin_rps": rng.randint(5000, 15000)},
                "game-server": {"game.asset_load_timeout_pct": round(rng.uniform(5.0, 30.0), 1), "game.client_crash_rate": round(rng.uniform(0.5, 3.0), 1)},
                "analytics-pipeline": {"analytics.cdn_error_events": rng.randint(1000, 5000)},
            },
            6: {  # Asset Bundle Corruption
                "content-delivery": {"cdn.corrupt_chunk_offset": rng.randint(50000000, 200000000), "cdn.edge_tcp_resets": rng.randint(5, 30)},
                "game-server": {"game.bundle_load_failures": rng.randint(50, 500), "game.client_redownloads": rng.randint(20, 200)},
                "moderation-engine": {"moderation.asset_scan_status": "bypassed"},
            },
            7: {  # Chat Message Flood
                "chat-service": {"chat.bot_suspect_accounts": rng.randint(5, 50), "chat.channel_aggregate_rate": rng.randint(500, 2000)},
                "moderation-engine": {"moderation.automod_cpu_pct": round(rng.uniform(85, 99), 1), "moderation.dropped_scans": rng.randint(100, 1000)},
                "auth-gateway": {"auth.new_account_rate": rng.randint(50, 200), "auth.captcha_challenge_rate": round(rng.uniform(0.1, 5.0), 1)},
            },
            8: {  # Voice Channel Degradation
                "chat-service": {"voice.mixer_cpu_pct": round(rng.uniform(80, 99), 1), "voice.codec_downgrade": True},
                "game-server": {"game.voice_disconnect_count": rng.randint(10, 100), "game.team_comm_degraded": True},
                "analytics-pipeline": {"analytics.voice_quality_events": rng.randint(200, 1000)},
            },
            9: {  # Leaderboard Corruption
                "leaderboard-api": {"leaderboard.redis_aof_rewrite": True, "leaderboard.zadd_race_detected": True},
                "game-server": {"game.rank_display_stale": True, "game.score_submit_retries": rng.randint(3, 10)},
                "analytics-pipeline": {"analytics.rank_anomaly_events": rng.randint(100, 500)},
                "moderation-engine": {"moderation.rank_exploit_check": "inconclusive"},
            },
            10: {  # Season Pass Progression Sync Error
                "leaderboard-api": {"leaderboard.xp_event_delivery": "at-most-once", "leaderboard.missed_xp_events": rng.randint(100, 2000)},
                "payment-processor": {"payment.premium_pass_affected": True, "payment.refund_risk": rng.choice(["low", "medium", "high"])},
                "analytics-pipeline": {"analytics.xp_pipeline_lag_s": rng.randint(30, 300)},
            },
            11: {  # OAuth Token Refresh Storm
                "auth-gateway": {"auth.expiring_tokens_5min_pct": round(rng.uniform(40, 75), 1), "auth.jwks_cache_age_s": rng.randint(200, 600)},
                "game-server": {"game.session_validation_failures": rng.randint(500, 5000), "game.forced_relogin_count": rng.randint(100, 1000)},
                "matchmaking-engine": {"matchmaking.auth_timeout_pct": round(rng.uniform(10, 50), 1)},
                "chat-service": {"chat.disconnected_users": rng.randint(500, 5000)},
            },
            12: {  # Account Takeover Detection Spike
                "auth-gateway": {"auth.credential_stuffing_detected": True, "auth.bad_ip_reputation_pct": round(rng.uniform(70, 95), 1)},
                "payment-processor": {"payment.fraudulent_purchase_attempts": rng.randint(10, 100), "payment.wallet_freeze_count": rng.randint(5, 50)},
                "moderation-engine": {"moderation.ato_flagged_accounts": rng.randint(20, 200)},
                "analytics-pipeline": {"analytics.security_event_surge": True},
            },
            13: {  # In-App Purchase Processing Failure
                "payment-processor": {"payment.provider_latency_ms": rng.randint(3000, 12000), "payment.circuit_breaker_state": rng.choice(["HALF_OPEN", "OPEN"])},
                "auth-gateway": {"auth.purchase_identity_verify": "timeout", "auth.token_valid": True},
                "analytics-pipeline": {"analytics.failed_txn_count": rng.randint(100, 2000)},
            },
            14: {  # Virtual Currency Ledger Inconsistency
                "payment-processor": {"payment.ledger_race_condition": True, "payment.duplicate_txn_suspected": True},
                "leaderboard-api": {"leaderboard.reward_delivery_stalled": True, "leaderboard.affected_players": rng.randint(10, 500)},
                "moderation-engine": {"moderation.fraud_investigation_queued": True},
                "analytics-pipeline": {"analytics.ledger_discrepancy_count": rng.randint(10, 200)},
            },
            15: {  # Event Ingestion Pipeline Lag
                "analytics-pipeline": {"analytics.kafka_consumers_dead": rng.randint(2, 6), "analytics.partition_stalled": rng.choice(["partition-0", "partition-1", "partition-2", "partition-3"])},
                "game-server": {"game.telemetry_buffer_pct": round(rng.uniform(70, 95), 1), "game.event_drop_rate_pct": round(rng.uniform(1, 15), 1)},
                "leaderboard-api": {"leaderboard.rank_update_delay_s": rng.randint(30, 300)},
            },
            16: {  # Player Telemetry Buffer Overflow
                "analytics-pipeline": {"analytics.ring_buffer_writable_slots": rng.randint(100, 1000), "analytics.consumer_drain_lag_ms": rng.randint(500, 5000)},
                "game-server": {"game.anticheat_data_gap": True, "game.movement_events_dropped_pct": round(rng.uniform(5, 25), 1)},
                "matchmaking-engine": {"matchmaking.player_stats_stale": True},
            },
            17: {  # Auto-Moderation False Positive Storm
                "moderation-engine": {"moderation.model_precision": round(rng.uniform(0.30, 0.50), 2), "moderation.hate_speech_fp_rate_pct": round(rng.uniform(20, 45), 1)},
                "chat-service": {"chat.silenced_players": rng.randint(500, 5000), "chat.appeal_queue_depth": rng.randint(200, 2000)},
                "analytics-pipeline": {"analytics.moderation_accuracy_alert": True},
            },
            18: {  # Report Queue Overflow
                "moderation-engine": {"moderation.workers_crashed": rng.randint(4, 10), "moderation.gpu_inference_status": "OOM"},
                "chat-service": {"chat.unmoderated_messages_pct": round(rng.uniform(10, 40), 1), "chat.report_button_clicks": rng.randint(1000, 10000)},
                "auth-gateway": {"auth.flagged_account_backlog": rng.randint(100, 1000)},
            },
            19: {  # Server Tick Rate Degradation
                "game-server": {"game.physics_tick_budget_pct": round(rng.uniform(45, 65), 1), "game.entity_count": rng.randint(3000, 6000)},
                "matchmaking-engine": {"matchmaking.server_health_score": round(rng.uniform(0.2, 0.5), 2), "matchmaking.rebalance_triggered": True},
                "analytics-pipeline": {"analytics.perf_alert_count": rng.randint(50, 200)},
                "chat-service": {"chat.voice_server_colocated": True, "chat.voice_quality_impacted": True},
            },
            20: {  # Cross-Region Player Migration Failure
                "matchmaking-engine": {"matchmaking.migration_timeout_ms": rng.randint(5000, 30000), "matchmaking.cross_region_packet_loss_pct": round(rng.uniform(2, 8), 1)},
                "auth-gateway": {"auth.session_transfer_status": "failed", "auth.token_region_mismatch": True},
                "game-server": {"game.state_payload_kb": round(rng.uniform(40, 120), 1), "game.migration_rollback": True},
                "leaderboard-api": {"leaderboard.cross_region_sync": "stalled"},
                "analytics-pipeline": {"analytics.migration_failure_events": rng.randint(10, 100)},
            },
        }
        channel_clues = clues.get(channel, {})
        return channel_clues.get(service_name, {})

    def get_correlation_attribute(self, channel: int, is_error: bool, rng) -> dict:
        correlation_attrs = {
            1: ("deployment.server_build", "game-server-v7.2.1-canary"),
            2: ("infra.gpu_driver", "nvidia-535.129.03-beta"),
            3: ("deployment.matchmaker_config", "mm-config-v4.1.0-experimental"),
            4: ("runtime.glicko_impl", "glicko2-v3.0.1-unclamped"),
            5: ("deployment.cdn_edge_config", "edge-config-v2.8.0-rc1"),
            6: ("infra.nic_firmware", "mellanox-cx6-fw-22.39.1014"),
            7: ("network.rate_limiter_config", "rl-config-v3.2-relaxed"),
            8: ("infra.audio_codec_lib", "opus-1.4.0-custom-build"),
            9: ("deployment.redis_config", "redis-7.2.4-aof-experimental"),
            10: ("runtime.kafka_consumer_config", "consumer-v2.1.0-at-most-once"),
            11: ("infra.ntp_source", "chrony-4.5-gps-backup"),
            12: ("network.waf_ruleset", "waf-rules-v8.1.0-permissive"),
            13: ("deployment.payment_sdk", "stripe-sdk-v12.1.0-rc2"),
            14: ("runtime.db_isolation_level", "read-committed-optimistic"),
            15: ("infra.kafka_broker_version", "kafka-3.7.0-kraft-unstable"),
            16: ("deployment.ring_buffer_config", "ringbuf-v2.0.0-no-backpressure"),
            17: ("deployment.automod_model", "nlp-classifier-v4.0-beta-sensitive"),
            18: ("infra.gpu_memory_config", "a100-40gb-batch-oversized"),
            19: ("network.routing_policy", "ecmp-4path-asymmetric"),
            20: ("network.cross_region_vpn", "wireguard-v1.0.20241201-mtu1400"),
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
            # Player/session identifiers
            "player_id": f"PLR-{random.randint(100000, 999999)}",
            "session_id": f"SESS-{random.randint(10000000, 99999999)}",
            "match_id": f"MATCH-{random.randint(100000, 999999)}",
            "server_id": f"GS-{random.choice(['US-E', 'US-W', 'EU-W', 'AP-SE'])}-{random.randint(1, 99):02d}",
            # Game state desync
            "position_delta": round(random.uniform(1.0, 25.0), 2),
            "tick_number": random.randint(100000, 9999999),
            # Physics
            "entity_id": f"ENT-{random.randint(10000, 99999)}",
            "velocity": round(random.uniform(1000.0, 999999.0), 1),
            "max_velocity": 500.0,
            "zone_id": random.choice(["ZONE-A1", "ZONE-B2", "ZONE-C3", "ZONE-D4"]),
            # Matchmaking
            "queue_name": random.choice(["ranked-solo", "ranked-duo", "casual-squad", "tournament-5v5"]),
            "queue_depth": random.randint(5000, 50000),
            "max_capacity": 3000,
            "wait_time_ms": random.randint(30000, 300000),
            "region": random.choice(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]),
            # Skill rating
            "mmr_value": random.randint(-500, 10000),
            "max_mmr": 5000,
            "volatility": round(random.uniform(0.01, 2.5), 3),
            # CDN
            "edge_node": random.choice(["edge-iad-01", "edge-lax-02", "edge-fra-01", "edge-nrt-01"]),
            "cache_hit_rate": round(random.uniform(20.0, 75.0), 1),
            "origin_load_pct": round(random.uniform(85.0, 100.0), 1),
            "asset_group": random.choice(["textures-hd", "models-characters", "audio-sfx", "maps-terrain"]),
            # Asset corruption
            "bundle_id": f"BDL-{random.randint(10000, 99999)}",
            "expected_hash": f"sha256:{random.randbytes(8).hex()}",
            "actual_hash": f"sha256:{random.randbytes(8).hex()}",
            "bundle_size_mb": round(random.uniform(50.0, 500.0), 1),
            "bundle_version": f"v{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 99)}",
            # Chat
            "channel_id": random.choice(["global-en", "guild-12345", "match-lobby", "trade-market"]),
            "message_rate": random.randint(500, 5000),
            "rate_limit": 200,
            "pending_moderation": random.randint(1000, 20000),
            # Voice
            "voice_channel_id": f"VC-{random.randint(10000, 99999)}",
            "voice_packet_loss_pct": round(random.uniform(5.0, 35.0), 1),
            "jitter_ms": round(random.uniform(20.0, 150.0), 1),
            "active_speakers": random.randint(2, 25),
            "codec": random.choice(["opus", "g711", "aac"]),
            # Leaderboard
            "leaderboard_id": random.choice(["ranked-global", "seasonal-solo", "guild-wars", "tournament-finals"]),
            "corrupt_entries": random.randint(10, 500),
            "season_id": f"S{random.randint(1, 12)}",
            # Season pass
            "current_tier": random.randint(1, 50),
            "expected_tier": random.randint(51, 100),
            "xp_total": random.randint(50000, 500000),
            "xp_delta": random.randint(1000, 50000),
            # Auth / tokens
            "refresh_rate": random.randint(5000, 50000),
            "max_refresh_rate": 2000,
            "failed_refreshes": random.randint(100, 5000),
            "token_pool_id": random.choice(["pool-primary", "pool-secondary", "pool-failover"]),
            # Account takeover
            "ato_attempts": random.randint(500, 10000),
            "window_seconds": random.randint(60, 300),
            "blocked_ips": random.randint(50, 500),
            "risk_score": round(random.uniform(0.85, 0.99), 2),
            "geo_region": random.choice(["Eastern Europe", "Southeast Asia", "South America", "Unknown VPN"]),
            # Payments
            "purchase_id": f"TXN-{random.randint(10000000, 99999999)}",
            "amount": round(random.uniform(0.99, 99.99), 2),
            "currency": random.choice(["USD", "EUR", "GBP", "JPY"]),
            "payment_provider": random.choice(["stripe", "paypal", "apple_iap", "google_play"]),
            "error_code": random.choice(["TIMEOUT", "DECLINED", "INSUFFICIENT_FUNDS", "FRAUD_HOLD", "PROVIDER_ERROR"]),
            "retry_count": random.randint(1, 5),
            "max_retries": 3,
            # Ledger
            "currency_balance": random.randint(100, 100000),
            "ledger_sum": random.randint(100, 100000),
            "discrepancy": random.randint(1, 5000),
            "virtual_currency": random.choice(["gems", "coins", "credits", "tokens"]),
            "last_transaction_id": f"LTXN-{random.randint(1000000, 9999999)}",
            # Analytics pipeline
            "pipeline_id": random.choice(["events-primary", "events-secondary", "replay-pipeline"]),
            "lag_seconds": round(random.uniform(30.0, 600.0), 1),
            "max_lag_seconds": 10.0,
            "backlog_count": random.randint(50000, 5000000),
            "throughput": random.randint(100, 2000),
            "expected_throughput": 5000,
            # Telemetry buffer
            "buffer_id": random.choice(["buf-player-events", "buf-game-state", "buf-combat-log"]),
            "buffer_usage_pct": round(random.uniform(95.0, 100.0), 1),
            "buffer_size": random.randint(90000, 100000),
            "max_buffer_size": 100000,
            "dropped_events": random.randint(100, 10000),
            "window_seconds_buf": random.randint(30, 300),
            # Moderation
            "false_positive_count": random.randint(100, 5000),
            "window_minutes": random.randint(5, 60),
            "fp_rate_pct": round(random.uniform(15.0, 45.0), 1),
            "model_version": f"automod-v{random.randint(3, 7)}.{random.randint(0, 9)}",
            "affected_players": random.randint(50, 2000),
            # Report queue
            "report_queue_depth": random.randint(5000, 50000),
            "processing_rate": round(random.uniform(5.0, 30.0), 1),
            "oldest_report_hours": round(random.uniform(4.0, 72.0), 1),
            "report_category": random.choice(["harassment", "cheating", "hate_speech", "exploits", "spam"]),
            # Tick rate
            "tick_rate": round(random.uniform(12.0, 45.0), 1),
            "target_tick_rate": 64,
            "frame_time_ms": round(random.uniform(22.0, 83.0), 1),
            "active_players": random.randint(10, 100),
            # Migration
            "source_region": random.choice(["us-east-1", "eu-west-1"]),
            "target_region": random.choice(["us-west-2", "ap-southeast-1"]),
            "migration_phase": random.choice(["state_extraction", "transfer", "injection", "validation"]),
            "latency_ms": random.randint(200, 5000),
        }


# Module-level instance for registry discovery
scenario = GamingScenario()

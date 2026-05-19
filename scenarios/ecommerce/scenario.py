"""Global Commerce Platform scenario — e-commerce marketplace with ad monetization."""

from __future__ import annotations

import random
import time
from typing import Any

from scenarios.base import BaseScenario, CountdownConfig, UITheme


class EcommerceScenario(BaseScenario):
    """Global e-commerce marketplace with storefront, catalog, orders, ads, payments, and fulfillment."""

    # ── Identity ──────────────────────────────────────────────────────

    @property
    def scenario_id(self) -> str:
        return "ecommerce"

    @property
    def scenario_icon(self) -> str:
        return "🛒"

    @property
    def scenario_name(self) -> str:
        return "Global Commerce Platform"

    @property
    def scenario_description(self) -> str:
        return (
            "Global e-commerce marketplace running on multi-cloud infrastructure. "
            "Storefront, personalization, and ad monetization on AWS/GCP, "
            "with payment processing and fulfillment on Azure."
        )

    @property
    def namespace(self) -> str:
        return "ecommerce"

    @property
    def sort_order(self) -> int:
        return 7

    @property
    def raw_log_profile(self) -> dict[str, Any]:
        return {
            "service_name": "storefront-edge",
            "user_id_prefix": "u",
            "tier_field": "user_tier",
            "tier_values": [("free", 75), ("pro", 20), ("enterprise", 5)],
            "country_weights": {"US": 40, "GB": 12, "DE": 10, "FR": 8, "JP": 8, "BR": 10, "CA": 7, "AU": 5},
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "paths": [
                "/checkout", "/api/v2/cart", "/api/v2/orders",
                "/products/{id}", "/search", "/login", "/account", "/health",
            ],
            "change_point_path": "/checkout",
        }

    @property
    def executive_kpi_emitter_service_name(self) -> str:
        return "ad-platform"

    @property
    def executive_dashboard_intro(self) -> str:
        return (
            "**Commerce & advertising KPIs** — revenue, traffic & engagement, fulfillment, "
            "and customer health (synthetic `business.*` from `ad-platform`)."
        )

    @property
    def executive_kpi_sections(self) -> list[dict]:
        return [
            {
                "header": "**Revenue** — GMV, conversion, AOV, ads, subscriptions, and seller fees",
                "specs": [
                    ("GMV (USD/min)", "metrics.business.gmv_usd_per_min"),
                    ("Conversion rate (%)", "metrics.business.conversion_rate_pct"),
                    ("Average order value (USD)", "metrics.business.average_order_value_usd"),
                    ("Ad revenue (USD/min)", "metrics.business.ad_revenue_usd_per_min"),
                    ("Subscription MRR (USD/min)", "metrics.business.subscription_mrr_usd_per_min"),
                    ("Seller fee revenue (USD/min)", "metrics.business.seller_fee_revenue_usd_per_min"),
                ],
            },
            {
                "header": "**Traffic & engagement** — sessions, views, cart, search, and retention",
                "specs": [
                    ("Sessions / min", "metrics.business.sessions_per_min"),
                    ("Page views / min", "metrics.business.page_views_per_min"),
                    ("Cart adds / min", "metrics.business.cart_adds_per_min"),
                    ("Search queries / min", "metrics.business.search_queries_per_min"),
                    ("Content completion (%)", "metrics.business.content_completion_rate_pct"),
                    ("Return visitor (%)", "metrics.business.return_visitor_pct"),
                ],
            },
            {
                "header": "**Fulfillment** — orders, SLA, returns, cancels, same-day, and inventory",
                "specs": [
                    ("Orders placed / min", "metrics.business.orders_placed_per_min"),
                    ("Fulfillment SLA (%)", "metrics.business.fulfillment_sla_pct"),
                    ("Returns / min", "metrics.business.returns_per_min"),
                    ("Cancel rate (%)", "metrics.business.cancel_rate_pct"),
                    ("Same-day eligible (%)", "metrics.business.same_day_eligible_pct"),
                    ("Inventory turn rate", "metrics.business.inventory_turn_rate"),
                ],
            },
            {
                "header": "**Customer health** — CSAT, NPS, churn, email, push, and loyalty",
                "specs": [
                    ("CSAT (0–5)", "metrics.business.csat_score_0_5"),
                    ("Satisfaction proxy (NPS-like)", "metrics.business.net_satisfaction_proxy_nps"),
                    ("Churn risk (0–100)", "metrics.business.churn_risk_index_0_100"),
                    ("Email open rate (%)", "metrics.business.email_open_rate_pct"),
                    ("Push CTR (%)", "metrics.business.push_notification_ctr_pct"),
                    ("Loyalty redeem (pts/min)", "metrics.business.loyalty_points_redeemed_per_min"),
                ],
            },
        ]

    @property
    def executive_trend_charts(self) -> list[dict]:
        return [
            {"title": "GMV trend", "field": "metrics.business.gmv_usd_per_min", "y_label": "USD/min"},
            {"title": "Sessions / min", "field": "metrics.business.sessions_per_min", "y_label": "sessions/min"},
            {"title": "Conversion rate", "field": "metrics.business.conversion_rate_pct", "y_label": "%"},
            {"title": "Orders placed / min", "field": "metrics.business.orders_placed_per_min", "y_label": "orders/min"},
            {"title": "Ad revenue trend", "field": "metrics.business.ad_revenue_usd_per_min", "y_label": "USD/min"},
            {"title": "Churn risk index", "field": "metrics.business.churn_risk_index_0_100", "y_label": "index"},
        ]

    # ── Services ──────────────────────────────────────────────────────

    @property
    def services(self) -> dict[str, dict[str, Any]]:
        return {
            "storefront-gateway": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1a",
                "subsystem": "storefront",
                "language": "python",
            },
            "product-catalog": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1b",
                "subsystem": "catalog",
                "language": "java",
            },
            "order-management": {
                "cloud_provider": "aws",
                "cloud_region": "us-east-1",
                "cloud_platform": "aws_ec2",
                "cloud_availability_zone": "us-east-1c",
                "subsystem": "orders",
                "language": "go",
            },
            "ad-platform": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "advertising",
                "language": "python",
            },
            "recommendation-engine": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-b",
                "subsystem": "personalization",
                "language": "python",
            },
            "inventory-service": {
                "cloud_provider": "gcp",
                "cloud_region": "us-central1",
                "cloud_platform": "gcp_compute_engine",
                "cloud_availability_zone": "us-central1-a",
                "subsystem": "inventory",
                "language": "go",
            },
            "payment-processor": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "payments",
                "language": "dotnet",
            },
            "fulfillment-orchestrator": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-2",
                "subsystem": "fulfillment",
                "language": "java",
            },
            "analytics-pipeline": {
                "cloud_provider": "azure",
                "cloud_region": "eastus",
                "cloud_platform": "azure_vm",
                "cloud_availability_zone": "eastus-1",
                "subsystem": "analytics",
                "language": "python",
            },
        }

    # ── Channel Registry ──────────────────────────────────────────────

    @property
    def channel_registry(self) -> dict[int, dict[str, Any]]:
        return {
            1: {
                "name": "Payment Gateway Timeout",
                "subsystem": "payments",
                "vehicle_section": "checkout_pipeline",
                "error_type": "PAYMENT-GATEWAY-TIMEOUT",
                "sensor_type": "gateway_latency",
                "affected_services": ["payment-processor", "order-management"],
                "cascade_services": ["storefront-gateway", "fulfillment-orchestrator"],
                "description": "Payment gateway connections timing out, causing checkout failures and order drop-off",
                "investigation_notes": (
                    "1. Check payment-processor logs for PAYMENT-GATEWAY-TIMEOUT — note which gateway provider ({payment_provider}) is affected.\n"
                    "2. Query recent error rate: FROM logs.otel.ecommerce.* | WHERE body.text LIKE \"*PAYMENT-GATEWAY-TIMEOUT*\" | STATS count() BY service.name.\n"
                    "3. Verify TLS handshake health — timeouts above {payment_timeout_ms}ms often indicate certificate validation delays or MTU black holes on the path to the provider.\n"
                    "4. Check the payment provider's status page and correlate timing with their reported incidents.\n"
                    "5. Review connection pool exhaustion: if pool_size={pool_size} and active={active_connections}, the pool is saturated — scale horizontally or increase pool size.\n"
                    "6. As an immediate mitigation, route traffic to the secondary gateway provider while the primary recovers."
                ),
                "remediation_action": "restart_payment_gateway",
                "error_message": (
                    "[PaymentProcessor] PAYMENT-GATEWAY-TIMEOUT: provider={payment_provider} "
                    "order_id={order_id} timeout={payment_timeout_ms}ms "
                    "pool_size={pool_size} active={active_connections} retry={retry_count}"
                ),
                "stack_trace": (
                    "System.TimeoutException: PAYMENT-GATEWAY-TIMEOUT\n"
                    "   at PaymentGatewayClient.ChargeAsync(ChargeRequest request)\n"
                    "   at PaymentProcessor.ProcessOrder(OrderId {order_id})\n"
                    "   at CheckoutOrchestrator.CompleteCheckout(SessionId {session_id})\n"
                    "Provider:      {payment_provider}\n"
                    "Timeout (ms):  {payment_timeout_ms}\n"
                    "Pool size:     {pool_size}\n"
                    "Active conns:  {active_connections}\n"
                    "Retry count:   {retry_count}\n"
                    "Last success:  {last_success_sec}s ago"
                ),
            },
            2: {
                "name": "Ad Serving Failure",
                "subsystem": "advertising",
                "vehicle_section": "ad_server",
                "error_type": "ADS-SERVING-FAILURE",
                "sensor_type": "ad_fill_rate",
                "affected_services": ["ad-platform"],
                "cascade_services": ["storefront-gateway", "analytics-pipeline"],
                "description": "Ad serving pipeline failing — impressions drop to zero, causing direct revenue loss reportable to senior leadership",
                "investigation_notes": (
                    "1. Check ad-platform logs for ADS-SERVING-FAILURE — ads.fill_rate_pct near zero is the primary revenue impact signal.\n"
                    "2. Quantify revenue impact: multiply ads.impressions_per_sec (expected ~{expected_impressions}) by ads.cpm_usd ({cpm_usd}) / 1000 to get $/sec loss.\n"
                    "3. Verify the ad decision service is reachable: check for CONNECTION_REFUSED or DNS_RESOLUTION_FAILURE in ad-platform logs.\n"
                    "4. Check ad server process health — OOM kills or core dumps under /var/log/ads/ indicate memory pressure from the creative cache.\n"
                    "5. Review ad targeting index freshness: a stale targeting index (>30min) causes bid requests to return empty, driving fill rate to zero.\n"
                    "6. If the ad server is healthy but fill_rate is low, check demand-side platform (DSP) integrations — a DSP outage reduces available bid inventory."
                ),
                "remediation_action": "restart_ad_server",
                "error_message": (
                    "[AdPlatform] ADS-SERVING-FAILURE: fill_rate={fill_rate_pct}% "
                    "(expected >{expected_fill_pct}%) impressions_lost={impressions_lost} "
                    "revenue_impact_usd={revenue_impact_usd} ad_unit={ad_unit_id} "
                    "error={ad_error_detail}"
                ),
                "stack_trace": (
                    "AdServingException: ADS-SERVING-FAILURE\n"
                    "  at AdDecisionService.serve_ad(placement={ad_unit_id})\n"
                    "  at AdPlatform.handle_bid_request(request_id={bid_request_id})\n"
                    "Fill Rate:       {fill_rate_pct}% (threshold: {expected_fill_pct}%)\n"
                    "Impressions Lost:{impressions_lost}\n"
                    "Revenue Impact:  ${revenue_impact_usd}\n"
                    "Ad Unit:         {ad_unit_id}\n"
                    "Error Detail:    {ad_error_detail}\n"
                    "DSP Status:      DEGRADED\n"
                    "Targeting Index: STALE ({targeting_staleness_min}min)"
                ),
            },
            3: {
                "name": "Search Index Corruption",
                "subsystem": "catalog",
                "vehicle_section": "search_engine",
                "error_type": "CATALOG-INDEX-CORRUPT",
                "sensor_type": "search_index",
                "affected_services": ["product-catalog"],
                "cascade_services": ["storefront-gateway", "recommendation-engine"],
                "description": "Product search index corrupted or partially rebuilt, returning incomplete or incorrect results",
                "investigation_notes": (
                    "1. Check product-catalog logs for CATALOG-INDEX-CORRUPT — note the affected shard ({shard_id}) and document count mismatch.\n"
                    "2. Run an index health check: GET /_cluster/health — red/yellow status with unassigned shards confirms corruption.\n"
                    "3. Check for partial writes during a previous index rebuild: `show index stats` — a rebuild that aborted midway leaves an inconsistent index.\n"
                    "4. Identify affected categories: query `catalog.items_indexed` metric — a drop below {expected_items} items indicates missing documents.\n"
                    "5. Do not trigger a full rebuild during peak traffic — it will consume all indexing throughput and further degrade search latency.\n"
                    "6. Roll back to the last known-good snapshot and replay the indexing changelog from that point forward."
                ),
                "remediation_action": "rebuild_search_index",
                "error_message": (
                    "[ProductCatalog] CATALOG-INDEX-CORRUPT: shard={shard_id} "
                    "expected_docs={expected_items} actual_docs={actual_items} "
                    "delta={doc_delta} affected_categories={affected_categories} "
                    "last_clean_snapshot={snapshot_age_min}m ago"
                ),
                "stack_trace": (
                    "com.ecommerce.catalog.IndexException: CATALOG-INDEX-CORRUPT\n"
                    "\tat com.ecommerce.catalog.SearchIndexManager.validateShard(SearchIndexManager.java:312)\n"
                    "\tat com.ecommerce.catalog.SearchIndexManager.healthCheck(SearchIndexManager.java:245)\n"
                    "\tat com.ecommerce.catalog.CatalogService.serveSearchRequest(CatalogService.java:189)\n"
                    "Shard:           {shard_id}\n"
                    "Expected docs:   {expected_items}\n"
                    "Actual docs:     {actual_items}\n"
                    "Delta:           -{doc_delta}\n"
                    "Affected cats:   {affected_categories}\n"
                    "Snapshot age:    {snapshot_age_min}m"
                ),
            },
            4: {
                "name": "Warehouse Capacity Alert",
                "subsystem": "fulfillment",
                "vehicle_section": "warehouse_management",
                "error_type": "WAREHOUSE-CAPACITY-ALERT",
                "sensor_type": "storage_utilization",
                "affected_services": ["fulfillment-orchestrator", "inventory-service"],
                "cascade_services": ["order-management"],
                "description": "Warehouse storage capacity approaching critical threshold — new inbound shipments being rejected, causing supply chain delays",
                "investigation_notes": (
                    "1. Check fulfillment-orchestrator logs for WAREHOUSE-CAPACITY-ALERT — capacity={capacity_used_pct}% at {warehouse_id}.\n"
                    "2. Identify the capacity drivers: check inventory.items_tracked metric by category — overstocked SKUs consuming disproportionate space.\n"
                    "3. Review inbound shipment schedule: if {inbound_units} units arriving in next 48hrs and capacity is already at {capacity_used_pct}%, overflow is imminent.\n"
                    "4. Prioritize outbound to free space: run velocity analysis on slow-moving SKUs ({slow_sku_count} items with 0 sales in 30 days) for clearance.\n"
                    "5. Activate overflow warehouse at {overflow_facility} — reroute inbound from top {slow_sku_categories} categories to free primary warehouse capacity.\n"
                    "6. Alert merchandising team: if capacity remains critical, new product listings should be paused until space is freed."
                ),
                "remediation_action": "rebalance_warehouse_capacity",
                "error_message": (
                    "[FulfillmentOrchestrator] WAREHOUSE-CAPACITY-ALERT: warehouse={warehouse_id} "
                    "capacity={capacity_used_pct}% ({capacity_used_sqft}/{capacity_total_sqft} sqft) "
                    "inbound_units={inbound_units} slow_skus={slow_sku_count}"
                ),
                "stack_trace": (
                    "com.ecommerce.fulfillment.CapacityException: WAREHOUSE-CAPACITY-ALERT\n"
                    "\tat com.ecommerce.fulfillment.WarehouseManager.checkCapacity(id={warehouse_id})\n"
                    "\tat com.ecommerce.fulfillment.FulfillmentOrchestrator.receiveInbound(asn={asn_id})\n"
                    "Warehouse:         {warehouse_id}\n"
                    "Capacity used:     {capacity_used_pct}% ({capacity_used_sqft}/{capacity_total_sqft} sqft)\n"
                    "Inbound (48h):     {inbound_units} units\n"
                    "Slow SKUs:         {slow_sku_count}\n"
                    "Overflow facility: {overflow_facility}"
                ),
            },
            5: {
                "name": "Checkout Session Storm",
                "subsystem": "storefront",
                "vehicle_section": "session_management",
                "error_type": "SESSION-STORM",
                "sensor_type": "session_pool",
                "affected_services": ["storefront-gateway", "order-management"],
                "cascade_services": ["product-catalog", "analytics-pipeline"],
                "description": "Surge of concurrent checkout sessions exhausting session pool capacity, causing checkout failures during peak traffic",
                "investigation_notes": (
                    "1. Check storefront-gateway logs for SESSION-STORM — active_sessions={active_sessions} vs max_sessions={max_sessions} shows utilization.\n"
                    "2. Identify the traffic source: check storefront.active_sessions metric trend — a sudden spike suggests a flash sale, bot storm, or marketing campaign.\n"
                    "3. Check for sticky session imbalance: if sessions are pinned to specific instances, some nodes may be at 100% while others are idle.\n"
                    "4. Review session TTL settings — sessions not expiring after abandonment keep slots occupied; default 30min TTL is too long for checkout flows.\n"
                    "5. Enable the rate limiter: if requests per IP exceed {rps_threshold}/s, apply throttling to prevent individual clients from monopolizing the pool.\n"
                    "6. As a circuit breaker, redirect overflow traffic to a static 'temporarily busy' page rather than queuing — queued requests timeout and hold slots longer."
                ),
                "remediation_action": "drain_session_pool",
                "error_message": (
                    "[StorefrontGateway] SESSION-STORM: active_sessions={active_sessions}/{max_sessions} "
                    "({session_util_pct}%) new_sessions_rejected={rejected_sessions} "
                    "rps={current_rps} threshold={rps_threshold} "
                    "top_source_ip={top_source_ip}"
                ),
                "stack_trace": (
                    "SessionPoolExhaustedException: SESSION-STORM\n"
                    "  at SessionManager.acquire(pool_id={pool_id})\n"
                    "  at CheckoutController.initSession(request_id={request_id})\n"
                    "Active sessions:    {active_sessions}/{max_sessions} ({session_util_pct}%)\n"
                    "Rejected sessions:  {rejected_sessions}\n"
                    "Current RPS:        {current_rps}\n"
                    "RPS threshold:      {rps_threshold}\n"
                    "Top source IP:      {top_source_ip}\n"
                    "Session TTL:        1800s"
                ),
            },
            6: {
                "name": "Fraud Detection False Positive Spike",
                "subsystem": "payments",
                "vehicle_section": "risk_engine",
                "error_type": "FRAUD-FALSE-POSITIVE",
                "sensor_type": "fraud_score",
                "affected_services": ["payment-processor"],
                "cascade_services": ["order-management", "storefront-gateway"],
                "description": "Fraud model generating excessive false positives, blocking legitimate transactions and degrading conversion rate",
                "investigation_notes": (
                    "1. Check payment-processor logs for FRAUD-FALSE-POSITIVE — false_positive_rate={false_positive_pct}% vs expected <{fp_threshold_pct}%.\n"
                    "2. Review the fraud model version — a recent model update or feature drift (e.g., new geographic pattern) often causes false positive spikes.\n"
                    "3. Identify the common false positive pattern: `show fraud_blocks | group by block_reason` — velocity_check and new_device_fingerprint are the most common.\n"
                    "4. Check if a specific feature is stuck: avg_order_value metric spike or unusual geolocation cluster can push legitimate orders above the fraud threshold.\n"
                    "5. Temporarily raise the fraud score threshold from {fraud_score_threshold} to {fraud_score_threshold_relaxed} to unblock legitimate traffic.\n"
                    "6. Trigger a manual review queue for blocked orders above ${min_manual_review_usd} — these are likely legitimate high-value orders that were incorrectly blocked."
                ),
                "remediation_action": "retune_fraud_model",
                "error_message": (
                    "[PaymentProcessor] FRAUD-FALSE-POSITIVE: blocked_orders={blocked_orders} "
                    "false_positive_rate={false_positive_pct}% threshold={fp_threshold_pct}% "
                    "fraud_score={fraud_score}/{fraud_score_threshold} "
                    "block_reason={block_reason} revenue_held_usd={revenue_held_usd}"
                ),
                "stack_trace": (
                    "FraudBlockException: FRAUD-FALSE-POSITIVE\n"
                    "   at FraudEngine.evaluate(OrderId {order_id}, Score={fraud_score})\n"
                    "   at PaymentProcessor.preAuthorize(CheckoutId {checkout_id})\n"
                    "Blocked orders:      {blocked_orders}\n"
                    "False positive rate: {false_positive_pct}%\n"
                    "Fraud score:         {fraud_score}/{fraud_score_threshold}\n"
                    "Block reason:        {block_reason}\n"
                    "Revenue held:        ${revenue_held_usd}\n"
                    "Model version:       fraud-model-v{fraud_model_version}"
                ),
            },
            7: {
                "name": "Inventory Sync Desync",
                "subsystem": "inventory",
                "vehicle_section": "inventory_replication",
                "error_type": "INVENTORY-SYNC-LAG",
                "sensor_type": "replication_lag",
                "affected_services": ["inventory-service", "order-management"],
                "cascade_services": ["fulfillment-orchestrator", "storefront-gateway"],
                "description": "Inventory replication lag causing overselling — orders accepted for out-of-stock items, leading to cancellations and customer complaints",
                "investigation_notes": (
                    "1. Check inventory-service logs for INVENTORY-SYNC-LAG — sync_lag_ms={sync_lag_ms} vs max acceptable {max_lag_ms}ms.\n"
                    "2. Check the replication consumer group lag: if consumer_lag={consumer_lag} messages, the inventory event stream is backed up.\n"
                    "3. Identify affected SKUs: query `inventory.stockout_rate_pct` metric — SKUs above 5% oversell risk are immediate candidates for a hold.\n"
                    "4. Review the sync writer throughput — if write_throughput_eps={write_throughput_eps} events/sec, a sudden spike in order volume exceeds replication capacity.\n"
                    "5. As an immediate fix, enable pessimistic locking on high-velocity SKUs to prevent overselling at the cost of slightly higher checkout latency.\n"
                    "6. Trigger a full inventory reconciliation: compare order-management committed stock with inventory-service available stock and cancel any excess orders."
                ),
                "remediation_action": "force_inventory_resync",
                "error_message": (
                    "[InventoryService] INVENTORY-SYNC-LAG: sync_lag={sync_lag_ms}ms "
                    "(max {max_lag_ms}ms) consumer_lag={consumer_lag} "
                    "oversell_risk_skus={oversell_risk_skus} "
                    "write_throughput={write_throughput_eps}eps"
                ),
                "stack_trace": (
                    "InventorySyncException: INVENTORY-SYNC-LAG\n"
                    "  at InventoryReplicator.consume(partition={kafka_partition})\n"
                    "  at InventoryService.reconcile(sku_batch={sku_batch_id})\n"
                    "Sync lag:          {sync_lag_ms}ms (max: {max_lag_ms}ms)\n"
                    "Consumer lag:      {consumer_lag} messages\n"
                    "Oversell risk SKUs:{oversell_risk_skus}\n"
                    "Write throughput:  {write_throughput_eps} eps\n"
                    "Kafka partition:   {kafka_partition}"
                ),
            },
            8: {
                "name": "Ad Click Tracking Backlog",
                "subsystem": "advertising",
                "vehicle_section": "click_attribution",
                "error_type": "ADS-CLICK-BACKLOG",
                "sensor_type": "click_queue",
                "affected_services": ["ad-platform", "analytics-pipeline"],
                "cascade_services": ["recommendation-engine"],
                "description": "Click tracking event queue backing up — attribution data delayed, causing ad spend optimization and budget reporting to use stale data",
                "investigation_notes": (
                    "1. Check ad-platform logs for ADS-CLICK-BACKLOG — click_queue_depth={click_queue_depth} vs max {click_queue_max}.\n"
                    "2. Check the click event consumer throughput: if consumer_throughput={consumer_throughput_eps}eps but ingest_rate={ingest_rate_eps}eps, the consumer is too slow.\n"
                    "3. Look for dead-letter queue growth — malformed click events that fail validation keep re-queuing and inflate the backlog count.\n"
                    "4. Review click deduplication logic — a dedup window too large ({dedup_window_sec}s) can cause hash table exhaustion under high click volume.\n"
                    "5. Identify the backpressure source: check analytics-pipeline lag metric — if the pipeline is lagged, click events are waiting for downstream capacity.\n"
                    "6. Scale click consumers horizontally — add {suggested_consumer_count} consumers to the click processing group to reduce backlog within {eta_min}min."
                ),
                "remediation_action": "flush_click_queue",
                "error_message": (
                    "[AdPlatform] ADS-CLICK-BACKLOG: click_queue_depth={click_queue_depth}/{click_queue_max} "
                    "consumer_throughput={consumer_throughput_eps}eps ingest_rate={ingest_rate_eps}eps "
                    "attribution_delay={attribution_delay_min}min dedup_window={dedup_window_sec}s"
                ),
                "stack_trace": (
                    "ClickTrackingException: ADS-CLICK-BACKLOG\n"
                    "  at ClickConsumer.process(queue_depth={click_queue_depth})\n"
                    "  at AttributionEngine.attribute(event_id={click_event_id})\n"
                    "Queue depth:        {click_queue_depth}/{click_queue_max}\n"
                    "Consumer tput:      {consumer_throughput_eps} eps\n"
                    "Ingest rate:        {ingest_rate_eps} eps\n"
                    "Attribution delay:  {attribution_delay_min}min\n"
                    "Dead-letter queue:  {dlq_size} events"
                ),
            },
            9: {
                "name": "Order DB Replication Lag",
                "subsystem": "orders",
                "vehicle_section": "database_cluster",
                "error_type": "ORDER-DB-REPLICATION-LAG",
                "sensor_type": "db_replication",
                "affected_services": ["order-management"],
                "cascade_services": ["payment-processor", "fulfillment-orchestrator"],
                "description": "Order database replica lagging behind primary, causing stale reads for order status queries and payment confirmation lookups",
                "investigation_notes": (
                    "1. Check order-management logs for ORDER-DB-REPLICATION-LAG — replication_lag_ms={replication_lag_ms} vs max {max_replication_lag_ms}ms.\n"
                    "2. Run `SHOW SLAVE STATUS\\G` on the replica — `Seconds_Behind_Master` and `Relay_Log_Space` are key indicators.\n"
                    "3. Check for long-running transactions on the primary: `SELECT * FROM information_schema.innodb_trx WHERE trx_started < NOW() - INTERVAL 30 SECOND` — these block replication.\n"
                    "4. Look at replica I/O thread vs SQL thread: if I/O thread is fast but SQL thread is slow, the replica is I/O-bound not network-bound — check disk throughput.\n"
                    "5. Route order-status reads to the primary temporarily to prevent customers from seeing stale state (order stuck in 'processing' when already shipped).\n"
                    "6. If lag exceeds {failover_threshold_ms}ms, promote the replica to primary and reconfigure clients to prevent prolonged stale-read exposure."
                ),
                "remediation_action": "force_db_failover",
                "error_message": (
                    "[OrderManagement] ORDER-DB-REPLICATION-LAG: replica={replica_host} "
                    "lag={replication_lag_ms}ms (max {max_replication_lag_ms}ms) "
                    "relay_log_space_mb={relay_log_space_mb} "
                    "seconds_behind_master={seconds_behind_master}"
                ),
                "stack_trace": (
                    "DBReplicationException: ORDER-DB-REPLICATION-LAG\n"
                    "  at OrderRepository.readFromReplica(host={replica_host})\n"
                    "  at OrderService.getOrderStatus(order_id={order_id})\n"
                    "Replica:              {replica_host}\n"
                    "Lag:                  {replication_lag_ms}ms\n"
                    "Relay log space:      {relay_log_space_mb}MB\n"
                    "Seconds behind master:{seconds_behind_master}s\n"
                    "I/O thread:           Running\n"
                    "SQL thread:           Running (delayed)"
                ),
            },
            10: {
                "name": "CDN Cache Invalidation Storm",
                "subsystem": "storefront",
                "vehicle_section": "cdn_layer",
                "error_type": "CDN-CACHE-STORM",
                "sensor_type": "cdn_hit_rate",
                "affected_services": ["storefront-gateway", "product-catalog"],
                "cascade_services": ["analytics-pipeline"],
                "description": "Mass cache invalidation flooding origin servers with requests, causing latency spikes and potential origin overload",
                "investigation_notes": (
                    "1. Check storefront-gateway logs for CDN-CACHE-STORM — cache_hit_rate={cache_hit_rate_pct}% drop and origin_rps={origin_rps} spike are the indicators.\n"
                    "2. Identify the invalidation trigger: a bulk price update, product image refresh, or catalog deploy can invalidate thousands of cache keys simultaneously.\n"
                    "3. Check the number of unique invalidation keys: if invalidation_keys={invalidation_keys}, this is a thundering herd — stagger the invalidations.\n"
                    "4. Review origin server CPU — if origin_cpu_pct={origin_cpu_pct}%, the origin is overwhelmed by cache-bypass requests. Enable serve-stale headers to reduce load.\n"
                    "5. Set Cache-Control: stale-while-revalidate on product pages so CDN can serve stale content while revalidating in the background.\n"
                    "6. Rate-limit CDN invalidation API calls to {max_invalidations_per_min}/min to prevent accidental bulk purges from triggering origin storms."
                ),
                "remediation_action": "purge_cdn_cache",
                "error_message": (
                    "[StorefrontGateway] CDN-CACHE-STORM: cache_hit_rate={cache_hit_rate_pct}% "
                    "(normal >{normal_hit_rate_pct}%) origin_rps={origin_rps} "
                    "invalidation_keys={invalidation_keys} "
                    "origin_cpu={origin_cpu_pct}%"
                ),
                "stack_trace": (
                    "CdnCacheException: CDN-CACHE-STORM\n"
                    "  at CdnClient.handleCacheMiss(keys_purged={invalidation_keys})\n"
                    "  at StorefrontGateway.serveProduct(path={request_path})\n"
                    "Cache hit rate:    {cache_hit_rate_pct}% (normal: {normal_hit_rate_pct}%)\n"
                    "Origin RPS:        {origin_rps}\n"
                    "Invalidation keys: {invalidation_keys}\n"
                    "Origin CPU:        {origin_cpu_pct}%\n"
                    "CDN edge nodes:    {cdn_edge_count}"
                ),
            },
            11: {
                "name": "Fulfillment Carrier API Rate Limit",
                "subsystem": "fulfillment",
                "vehicle_section": "carrier_integration",
                "error_type": "CARRIER-RATE-LIMIT",
                "sensor_type": "api_quota",
                "affected_services": ["fulfillment-orchestrator"],
                "cascade_services": ["order-management", "analytics-pipeline"],
                "description": "Carrier API rate limit hit, causing shipping label creation to fail and orders to stall in fulfillment queue",
                "investigation_notes": (
                    "1. Check fulfillment-orchestrator logs for CARRIER-RATE-LIMIT — which carrier ({carrier_name}) and what quota ({api_quota_used}/{api_quota_max}) is affected.\n"
                    "2. Check rate limit reset time: `X-RateLimit-Reset: {rate_limit_reset_epoch}` — the quota resets at that epoch; plan a burst recovery strategy.\n"
                    "3. Review API call distribution: if calls are concentrated in a short window, implement exponential backoff with jitter across the burst.\n"
                    "4. Switch eligible shipments to secondary carrier — if {secondary_carrier} has capacity, reroute to avoid further queue buildup.\n"
                    "5. Check if an upstream order spike is driving the API volume — correlate fulfillment_orders_queued with orders.per_minute metric for causality.\n"
                    "6. Rotate the API key: some carriers bind rate limits per API key — using a second key doubles effective quota until the primary key resets."
                ),
                "remediation_action": "rotate_carrier_api_key",
                "error_message": (
                    "[FulfillmentOrchestrator] CARRIER-RATE-LIMIT: carrier={carrier_name} "
                    "quota={api_quota_used}/{api_quota_max} reset_in={reset_in_sec}s "
                    "queued_labels={queued_labels} secondary_carrier={secondary_carrier}"
                ),
                "stack_trace": (
                    "com.ecommerce.fulfillment.CarrierApiException: CARRIER-RATE-LIMIT\n"
                    "\tat com.ecommerce.fulfillment.CarrierClient.createLabel(carrier={carrier_name})\n"
                    "\tat com.ecommerce.fulfillment.FulfillmentOrchestrator.shipOrder(order_id={order_id})\n"
                    "Carrier:          {carrier_name}\n"
                    "Quota used:       {api_quota_used}/{api_quota_max}\n"
                    "Reset in:         {reset_in_sec}s\n"
                    "Queued labels:    {queued_labels}\n"
                    "Secondary:        {secondary_carrier}\n"
                    "HTTP Status:      429 Too Many Requests"
                ),
            },
            12: {
                "name": "Cart Abandonment Spike",
                "subsystem": "orders",
                "vehicle_section": "checkout_funnel",
                "error_type": "CART-ABANDON-SPIKE",
                "sensor_type": "conversion_rate",
                "affected_services": ["order-management", "storefront-gateway"],
                "cascade_services": ["ad-platform"],
                "description": "Cart abandonment rate spiking abnormally — customers adding items but not completing checkout, indicating friction in the checkout flow",
                "investigation_notes": (
                    "1. Check order-management logs for CART-ABANDON-SPIKE — abandonment_rate={abandonment_rate_pct}% vs baseline {baseline_abandonment_pct}%.\n"
                    "2. Identify the abandonment step: if most abandonment is at payment entry (step 3), payment form errors or slow gateway response are the cause.\n"
                    "3. Check for JavaScript errors in the storefront — a broken payment widget or address validation failure silently blocks checkout completion.\n"
                    "4. Review promo code validation latency: if coupon checks take >{coupon_timeout_ms}ms, customers abandon while waiting for discount confirmation.\n"
                    "5. Correlate with ad-platform metrics — if a recent ad campaign is driving high-intent but low-conversion traffic, the landing page may have a mismatch.\n"
                    "6. Trigger cart recovery emails for sessions with >2min idle time in checkout — historically recovers {recovery_rate_pct}% of abandoned carts."
                ),
                "remediation_action": "optimize_checkout_flow",
                "error_message": (
                    "[OrderManagement] CART-ABANDON-SPIKE: abandonment_rate={abandonment_rate_pct}% "
                    "(baseline {baseline_abandonment_pct}%) abandoned_carts={abandoned_carts} "
                    "revenue_at_risk_usd={revenue_at_risk_usd} "
                    "abandon_step={abandon_step}"
                ),
                "stack_trace": (
                    "CartAbandonmentAlert: CART-ABANDON-SPIKE\n"
                    "  at CheckoutFunnelMonitor.checkAbandonmentRate(window=5min)\n"
                    "  at OrderService.trackCheckoutEvent(session_id={session_id})\n"
                    "Abandonment rate:  {abandonment_rate_pct}% (baseline: {baseline_abandonment_pct}%)\n"
                    "Abandoned carts:   {abandoned_carts}\n"
                    "Revenue at risk:   ${revenue_at_risk_usd}\n"
                    "Abandon step:      {abandon_step}\n"
                    "Time in funnel:    {avg_funnel_time_sec}s avg"
                ),
            },
            13: {
                "name": "Personalization Model Drift",
                "subsystem": "personalization",
                "vehicle_section": "ml_model_serving",
                "error_type": "RECO-MODEL-DRIFT",
                "sensor_type": "model_accuracy",
                "affected_services": ["recommendation-engine", "ad-platform"],
                "cascade_services": ["storefront-gateway"],
                "description": "Recommendation model experiencing feature drift — predictions degrading silently, reducing click-through and conversion rates",
                "investigation_notes": (
                    "1. Check recommendation-engine logs for RECO-MODEL-DRIFT — personalization_hit_rate_pct={hit_rate_pct}% below threshold {hit_rate_threshold_pct}%.\n"
                    "2. Review feature distribution shift: if the input feature distribution has diverged from training data distribution by >{drift_threshold_pct}%, the model is unreliable.\n"
                    "3. Check the model's online metrics (click-through rate, add-to-cart rate) against the A/B test baseline — a >10% degradation is a drift signal.\n"
                    "4. Inspect recent feature pipeline changes — a schema change in user behavior events can silently zero-out key features causing systematic errors.\n"
                    "5. Rollback to the previous stable model version (v{prev_model_version}) while retraining — degraded recommendations are worse than generic ones.\n"
                    "6. Ad-platform targeting also uses recommendation signals — notify the ads team that targeting quality is degraded until the model is retrained."
                ),
                "remediation_action": "rollback_reco_model",
                "error_message": (
                    "[RecommendationEngine] RECO-MODEL-DRIFT: model_version=v{model_version} "
                    "hit_rate={hit_rate_pct}% (threshold {hit_rate_threshold_pct}%) "
                    "feature_drift={drift_score:.2f} prev_stable_version=v{prev_model_version}"
                ),
                "stack_trace": (
                    "ModelDriftException: RECO-MODEL-DRIFT\n"
                    "  at ModelMonitor.checkDrift(model=v{model_version})\n"
                    "  at RecommendationService.serve(user_id={user_id})\n"
                    "Model version:      v{model_version}\n"
                    "Hit rate:           {hit_rate_pct}% (threshold: {hit_rate_threshold_pct}%)\n"
                    "Feature drift score:{drift_score}\n"
                    "Prev stable:        v{prev_model_version}\n"
                    "Affected users/hr:  {affected_users_hr}"
                ),
            },
            14: {
                "name": "Analytics Pipeline Lag",
                "subsystem": "analytics",
                "vehicle_section": "data_pipeline",
                "error_type": "ANALYTICS-PIPELINE-LAG",
                "sensor_type": "pipeline_latency",
                "affected_services": ["analytics-pipeline"],
                "cascade_services": ["ad-platform", "order-management"],
                "description": "Real-time analytics pipeline falling behind — dashboards showing stale data, ad optimization running on outdated metrics",
                "investigation_notes": (
                    "1. Check analytics-pipeline logs for ANALYTICS-PIPELINE-LAG — pipeline_lag_ms={pipeline_lag_ms}ms vs acceptable {max_pipeline_lag_ms}ms.\n"
                    "2. Check consumer group lag on the analytics stream: if consumer_lag={consumer_lag} events, the pipeline is not keeping up with ingest volume.\n"
                    "3. Identify the slow stage: ETL transforms, aggregation, or index writes — each has distinct latency signatures in the pipeline metrics.\n"
                    "4. Check for a data skew issue: if one partition has {hot_partition_events}x more events than others, the partition key is not evenly distributed.\n"
                    "5. Ad-platform's budget optimization queries rely on fresh analytics — with {pipeline_lag_ms}ms lag, spend data is stale and bidding may over- or under-spend.\n"
                    "6. Scale the analytics consumers and increase parallelism on the aggregation step to drain the backlog within {eta_drain_min}min."
                ),
                "remediation_action": "restart_analytics_pipeline",
                "error_message": (
                    "[AnalyticsPipeline] ANALYTICS-PIPELINE-LAG: lag={pipeline_lag_ms}ms "
                    "(max {max_pipeline_lag_ms}ms) consumer_lag={consumer_lag} "
                    "events_per_sec={events_per_sec} hot_partition={hot_partition}"
                ),
                "stack_trace": (
                    "PipelineLagException: ANALYTICS-PIPELINE-LAG\n"
                    "  at StreamConsumer.checkLag(group=analytics-consumer-group)\n"
                    "  at AnalyticsPipeline.processBatch(batch_id={batch_id})\n"
                    "Pipeline lag:      {pipeline_lag_ms}ms\n"
                    "Consumer lag:      {consumer_lag} events\n"
                    "Events/sec:        {events_per_sec}\n"
                    "Hot partition:     {hot_partition}\n"
                    "Stages behind:     etl_transform, aggregation"
                ),
            },
            15: {
                "name": "Catalog Price Sync Failure",
                "subsystem": "catalog",
                "vehicle_section": "pricing_engine",
                "error_type": "CATALOG-PRICE-SYNC",
                "sensor_type": "price_replication",
                "affected_services": ["product-catalog", "inventory-service"],
                "cascade_services": ["order-management"],
                "description": "Product price updates failing to propagate from pricing engine to catalog and inventory — stale prices causing customer disputes",
                "investigation_notes": (
                    "1. Check product-catalog logs for CATALOG-PRICE-SYNC — failed_updates={failed_price_updates}/{total_price_updates} shows scope.\n"
                    "2. Check the pricing event stream consumer: if the consumer is behind by {price_lag_events} events, prices are stale by {price_lag_min}min.\n"
                    "3. Verify no schema mismatch in the pricing event format — a recently deployed pricing service may be emitting events in a new format.\n"
                    "4. Cross-check: if displayed price differs from order-confirmed price by >{price_delta_threshold_pct}%, customer dispute risk is high.\n"
                    "5. Run a forced sync: `catalog-cli sync-prices --source pricing-engine --batch-size 1000` to drain the backlog.\n"
                    "6. Enable price validation at checkout: compare display price to real-time pricing API call — reject if delta exceeds tolerance."
                ),
                "remediation_action": "resync_catalog_prices",
                "error_message": (
                    "[ProductCatalog] CATALOG-PRICE-SYNC: failed_updates={failed_price_updates}/{total_price_updates} "
                    "price_lag={price_lag_min}min consumer_lag={price_lag_events} "
                    "affected_skus={affected_price_skus}"
                ),
                "stack_trace": (
                    "com.ecommerce.catalog.PriceSyncException: CATALOG-PRICE-SYNC\n"
                    "\tat com.ecommerce.catalog.PriceConsumer.applyUpdate(sku={sku_id})\n"
                    "\tat com.ecommerce.catalog.CatalogService.syncPrices(batch={price_batch_id})\n"
                    "Failed updates:    {failed_price_updates}/{total_price_updates}\n"
                    "Price lag:         {price_lag_min}min\n"
                    "Consumer lag:      {price_lag_events} events\n"
                    "Affected SKUs:     {affected_price_skus}"
                ),
            },
            16: {
                "name": "Storefront SSL Certificate Expiry",
                "subsystem": "storefront",
                "vehicle_section": "tls_termination",
                "error_type": "SSL-CERT-EXPIRY",
                "sensor_type": "certificate",
                "affected_services": ["storefront-gateway"],
                "cascade_services": ["order-management", "payment-processor"],
                "description": "TLS certificate for storefront domain expiring soon or expired — browsers will show security warnings and block HTTPS connections",
                "investigation_notes": (
                    "1. Check storefront-gateway logs for SSL-CERT-EXPIRY — cert_days_remaining={cert_days_remaining} days for domain {cert_domain}.\n"
                    "2. Verify current certificate details: `openssl s_client -connect {cert_domain}:443 | openssl x509 -noout -dates` — check NotAfter field.\n"
                    "3. Check auto-renewal status: if using Let's Encrypt/ACME, verify the renewal cron job ran successfully in the last 60 days.\n"
                    "4. Identify all domains covered by this cert (SANs): `openssl x509 -noout -text | grep DNS:` — all listed domains are affected.\n"
                    "5. Payment processor integrations may reject requests if the cert is expired — PCI DSS requires valid TLS for cardholder data environments.\n"
                    "6. Emergency renewal: use `certbot renew --force-renewal --cert-name {cert_domain}` or renew via your CA portal and deploy immediately."
                ),
                "remediation_action": "renew_ssl_certificate",
                "error_message": (
                    "[StorefrontGateway] SSL-CERT-EXPIRY: domain={cert_domain} "
                    "cert_serial={cert_serial} days_remaining={cert_days_remaining} "
                    "issuer={cert_issuer} san_count={cert_san_count} "
                    "auto_renewal_status={auto_renewal_status}"
                ),
                "stack_trace": (
                    "SSLCertificateException: SSL-CERT-EXPIRY\n"
                    "  at TlsTerminator.validateCertificate(domain={cert_domain})\n"
                    "  at StorefrontGateway.handleRequest(host={cert_domain})\n"
                    "Domain:           {cert_domain}\n"
                    "Serial:           {cert_serial}\n"
                    "Days remaining:   {cert_days_remaining}\n"
                    "Issuer:           {cert_issuer}\n"
                    "SANs covered:     {cert_san_count}\n"
                    "Auto-renewal:     {auto_renewal_status}"
                ),
            },
            17: {
                "name": "Ad Budget Cap Reached",
                "subsystem": "advertising",
                "vehicle_section": "budget_controller",
                "error_type": "ADS-BUDGET-CAP",
                "sensor_type": "budget_utilization",
                "affected_services": ["ad-platform"],
                "cascade_services": ["analytics-pipeline"],
                "description": "Ad campaign daily budget cap reached mid-day — ads stop serving before end of business, leaving revenue on the table",
                "investigation_notes": (
                    "1. Check ad-platform logs for ADS-BUDGET-CAP — campaign_id={campaign_id} has exhausted {budget_spent_usd}/{budget_daily_usd}.\n"
                    "2. Determine if this is expected (high-traffic day) or anomalous — compare to same day last week using analytics-pipeline GMV metrics.\n"
                    "3. Check if a bidding automation increased CPCs significantly: if avg_cpc={avg_cpc_usd} vs expected {expected_cpc_usd}, overbidding drained the budget early.\n"
                    "4. Review ad auction win rate: if win_rate={win_rate_pct}% and budget is exhausted, the campaign is competitive and budget needs upward adjustment.\n"
                    "5. Request emergency budget increase from the marketing team — document the incremental revenue opportunity: {hourly_revenue_usd}USD/hr with ads running.\n"
                    "6. Implement dayparting: if conversion rates are higher in afternoon hours, concentrate budget there rather than exhausting it in the morning."
                ),
                "remediation_action": "reset_ad_budget_cap",
                "error_message": (
                    "[AdPlatform] ADS-BUDGET-CAP: campaign_id={campaign_id} "
                    "budget_spent={budget_spent_usd}/{budget_daily_usd} "
                    "avg_cpc={avg_cpc_usd} win_rate={win_rate_pct}% "
                    "hours_remaining={hours_remaining} revenue_opportunity_usd={hourly_revenue_usd}"
                ),
                "stack_trace": (
                    "AdBudgetCapException: ADS-BUDGET-CAP\n"
                    "  at BudgetController.checkCap(campaign={campaign_id})\n"
                    "  at AdPlatform.serveBid(request_id={bid_request_id})\n"
                    "Campaign:          {campaign_id}\n"
                    "Budget spent:      ${budget_spent_usd}/${budget_daily_usd}\n"
                    "Avg CPC:           ${avg_cpc_usd}\n"
                    "Win rate:          {win_rate_pct}%\n"
                    "Hours remaining:   {hours_remaining}\n"
                    "Revenue/hr missed: ${hourly_revenue_usd}"
                ),
            },
            18: {
                "name": "Payment Token Expiry",
                "subsystem": "payments",
                "vehicle_section": "tokenization",
                "error_type": "PAYMENT-TOKEN-EXPIRY",
                "sensor_type": "token_vault",
                "affected_services": ["payment-processor"],
                "cascade_services": ["order-management"],
                "description": "Stored payment tokens expiring for recurring subscribers — subscription renewals and auto-reorders failing silently",
                "investigation_notes": (
                    "1. Check payment-processor logs for PAYMENT-TOKEN-EXPIRY — expired_tokens={expired_tokens} affecting {affected_subscriptions} subscriptions.\n"
                    "2. Identify the token age distribution: tokens older than {token_max_age_days} days are at highest risk — batch renew before they expire.\n"
                    "3. Check if the card network issued a mass BIN (Bank Identification Number) change — this can invalidate thousands of tokens simultaneously.\n"
                    "4. Trigger Account Updater API calls to the card networks — Visa and Mastercard provide automatic card number updates for expiring credentials.\n"
                    "5. For tokens that cannot be auto-renewed, send re-authorization emails to affected customers ({affected_subscriptions} contacts required).\n"
                    "6. Review token refresh policy: tokens should be refreshed 30 days before expiry, not on expiry — adjust the refresh scheduler interval."
                ),
                "remediation_action": "refresh_payment_tokens",
                "error_message": (
                    "[PaymentProcessor] PAYMENT-TOKEN-EXPIRY: expired_tokens={expired_tokens} "
                    "affected_subscriptions={affected_subscriptions} "
                    "revenue_at_risk_usd={subscription_revenue_usd} "
                    "token_age_days={token_max_age_days}"
                ),
                "stack_trace": (
                    "PaymentTokenException: PAYMENT-TOKEN-EXPIRY\n"
                    "   at TokenVault.validateToken(token_id={token_id})\n"
                    "   at PaymentProcessor.chargeSubscription(sub_id={subscription_id})\n"
                    "Expired tokens:       {expired_tokens}\n"
                    "Affected subs:        {affected_subscriptions}\n"
                    "Revenue at risk:      ${subscription_revenue_usd}\n"
                    "Token age (max):      {token_max_age_days} days\n"
                    "Account Updater:      NOT_CONFIGURED"
                ),
            },
            19: {
                "name": "Recommendation Engine OOM",
                "subsystem": "personalization",
                "vehicle_section": "ml_inference",
                "error_type": "RECO-ENGINE-OOM",
                "sensor_type": "heap_memory",
                "affected_services": ["recommendation-engine"],
                "cascade_services": ["storefront-gateway", "product-catalog"],
                "description": "Recommendation model inference process running out of heap memory, crashing and causing fallback to non-personalized results",
                "investigation_notes": (
                    "1. Check recommendation-engine logs for RECO-ENGINE-OOM — heap_used_mb={heap_used_mb} vs heap_max_mb={heap_max_mb} gives the margin.\n"
                    "2. The model embedding cache is likely bloated — check cache_size_mb metric. A cold-start after a pod restart causes aggressive cache backfill.\n"
                    "3. Review the model version: v{model_version} may have a larger embedding dimension than the previous version, requiring more heap.\n"
                    "4. Check GC log — G1GC full GC pauses above 2s indicate the heap is too small for current traffic; target 75% heap utilization.\n"
                    "5. Immediate mitigation: reduce batch_size from {batch_size} to half — this trades throughput for stability under memory pressure.\n"
                    "6. Scale the recommendation-engine horizontally (add pods) and reduce per-instance model cache size to distribute memory load."
                ),
                "remediation_action": "scale_recommendation_engine",
                "error_message": (
                    "[RecommendationEngine] RECO-ENGINE-OOM: heap_used={heap_used_mb}MB "
                    "heap_max={heap_max_mb}MB model_version=v{model_version} "
                    "batch_size={batch_size} cache_size={cache_size_mb}MB gc_pause_ms={gc_pause_ms}"
                ),
                "stack_trace": (
                    "java.lang.OutOfMemoryError: RECO-ENGINE-OOM Java heap space\n"
                    "\tat com.ecommerce.reco.EmbeddingCache.load(EmbeddingCache.java:178)\n"
                    "\tat com.ecommerce.reco.ModelInference.predict(ModelInference.java:234)\n"
                    "\tat com.ecommerce.reco.RecommendationService.getRecs(RecommendationService.java:112)\n"
                    "Heap used:    {heap_used_mb}MB / {heap_max_mb}MB\n"
                    "Model:        v{model_version}\n"
                    "Batch size:   {batch_size}\n"
                    "Cache size:   {cache_size_mb}MB\n"
                    "GC pause:     {gc_pause_ms}ms"
                ),
            },
            20: {
                "name": "Recommendation Cache Eviction",
                "subsystem": "personalization",
                "vehicle_section": "inference_cache",
                "error_type": "RECO-CACHE-EVICTION",
                "sensor_type": "cache_hit_rate",
                "affected_services": ["recommendation-engine"],
                "cascade_services": ["storefront-gateway", "product-catalog"],
                "description": "Recommendation inference cache mass eviction — cold cache forces expensive model re-inference for all users, spiking latency",
                "investigation_notes": (
                    "1. Check recommendation-engine logs for RECO-CACHE-EVICTION — cache_hit_rate={cache_hit_rate_pct}% drop and latency spike are correlated.\n"
                    "2. Identify eviction trigger: a pod restart, memory pressure OOM eviction, or TTL misconfiguration can cause mass eviction.\n"
                    "3. Check inference latency: cold cache drives p99_latency_ms={p99_latency_ms}ms vs warm cache {warm_latency_ms}ms — storefront timeout risk.\n"
                    "4. Enable a cache warm-up strategy: pre-compute recommendations for top {warm_user_count} users by traffic volume before routing traffic to the pod.\n"
                    "5. Review eviction policy: if using LRU, a cache size of {cache_size_mb}MB may be too small for the active user set — increase or switch to LFU.\n"
                    "6. Serve generic (non-personalized) trending products as a fallback while the cache warms — this prevents timeout errors at the cost of relevance."
                ),
                "remediation_action": "warm_recommendation_cache",
                "error_message": (
                    "[RecommendationEngine] RECO-CACHE-EVICTION: cache_hit_rate={cache_hit_rate_pct}% "
                    "(normal >{normal_cache_hit_pct}%) evicted_entries={evicted_entries} "
                    "p99_latency={p99_latency_ms}ms cache_size={cache_size_mb}MB"
                ),
                "stack_trace": (
                    "CacheEvictionException: RECO-CACHE-EVICTION\n"
                    "  at RecommendationCache.get(user_id={user_id})\n"
                    "  at RecommendationService.getRecs(user_id={user_id})\n"
                    "Cache hit rate:    {cache_hit_rate_pct}% (normal: {normal_cache_hit_pct}%)\n"
                    "Evicted entries:   {evicted_entries}\n"
                    "P99 latency:       {p99_latency_ms}ms\n"
                    "Cache size:        {cache_size_mb}MB\n"
                    "Eviction policy:   LRU"
                ),
            },
        }

    # ── Topology ──────────────────────────────────────────────────────

    @property
    def service_topology(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "storefront-gateway": [
                ("product-catalog", "/api/v1/catalog/search", "GET"),
                ("product-catalog", "/api/v1/catalog/product", "GET"),
                ("recommendation-engine", "/api/v1/recommendations/user", "GET"),
                ("order-management", "/api/v1/orders/cart", "POST"),
                ("ad-platform", "/api/v1/ads/placements", "GET"),
            ],
            "product-catalog": [
                ("inventory-service", "/api/v1/inventory/availability", "GET"),
                ("recommendation-engine", "/api/v1/recommendations/similar", "GET"),
            ],
            "order-management": [
                ("payment-processor", "/api/v1/payments/authorize", "POST"),
                ("inventory-service", "/api/v1/inventory/reserve", "POST"),
                ("fulfillment-orchestrator", "/api/v1/fulfillment/create-shipment", "POST"),
            ],
            "ad-platform": [
                ("recommendation-engine", "/api/v1/recommendations/targeting", "GET"),
                ("analytics-pipeline", "/api/v1/analytics/ad-events", "POST"),
            ],
            "recommendation-engine": [
                ("product-catalog", "/api/v1/catalog/product-details", "GET"),
                ("analytics-pipeline", "/api/v1/analytics/user-events", "POST"),
            ],
            "inventory-service": [
                ("fulfillment-orchestrator", "/api/v1/fulfillment/warehouse-stock", "GET"),
                ("analytics-pipeline", "/api/v1/analytics/inventory-events", "POST"),
            ],
            "payment-processor": [
                ("order-management", "/api/v1/orders/payment-confirm", "POST"),
                ("analytics-pipeline", "/api/v1/analytics/payment-events", "POST"),
            ],
            "fulfillment-orchestrator": [
                ("inventory-service", "/api/v1/inventory/update-stock", "POST"),
                ("analytics-pipeline", "/api/v1/analytics/fulfillment-events", "POST"),
            ],
            "analytics-pipeline": [
                ("ad-platform", "/api/v1/ads/metrics-refresh", "POST"),
            ],
        }

    @property
    def entry_endpoints(self) -> dict[str, list[tuple[str, str]]]:
        return {
            "storefront-gateway": [
                ("/api/v1/storefront/home", "GET"),
                ("/api/v1/storefront/search", "GET"),
                ("/api/v1/storefront/checkout", "POST"),
                ("/api/v1/storefront/product", "GET"),
            ],
            "product-catalog": [
                ("/api/v1/catalog/search", "GET"),
                ("/api/v1/catalog/product", "GET"),
                ("/api/v1/catalog/categories", "GET"),
            ],
            "order-management": [
                ("/api/v1/orders/create", "POST"),
                ("/api/v1/orders/status", "GET"),
                ("/api/v1/orders/cart/add", "POST"),
            ],
            "ad-platform": [
                ("/api/v1/ads/serve", "GET"),
                ("/api/v1/ads/click", "POST"),
                ("/api/v1/ads/impression", "POST"),
            ],
            "recommendation-engine": [
                ("/api/v1/recommendations/user", "GET"),
                ("/api/v1/recommendations/similar", "GET"),
            ],
            "inventory-service": [
                ("/api/v1/inventory/availability", "GET"),
                ("/api/v1/inventory/reserve", "POST"),
            ],
            "payment-processor": [
                ("/api/v1/payments/authorize", "POST"),
                ("/api/v1/payments/capture", "POST"),
                ("/api/v1/payments/status", "GET"),
            ],
            "fulfillment-orchestrator": [
                ("/api/v1/fulfillment/create-shipment", "POST"),
                ("/api/v1/fulfillment/tracking", "GET"),
            ],
            "analytics-pipeline": [
                ("/api/v1/analytics/events", "POST"),
                ("/api/v1/analytics/query", "POST"),
            ],
        }

    @property
    def db_operations(self) -> dict[str, list[tuple[str, str, str]]]:
        return {
            "storefront-gateway": [
                ("SELECT", "sessions", "SELECT session_id, user_id, cart_id, created_at FROM sessions WHERE session_id = ? AND expires_at > NOW()"),
                ("INSERT", "page_views", "INSERT INTO page_views (session_id, page_type, product_id, timestamp) VALUES (?, ?, ?, NOW())"),
            ],
            "product-catalog": [
                ("SELECT", "products", "SELECT id, name, price, description, category, stock_status FROM products WHERE status = 'active' AND category = ? ORDER BY relevance_score DESC LIMIT 50"),
                ("SELECT", "product_images", "SELECT product_id, image_url, alt_text FROM product_images WHERE product_id = ? AND primary = true"),
                ("UPDATE", "search_index", "UPDATE search_index SET last_indexed = NOW(), doc_count = ? WHERE shard_id = ?"),
            ],
            "order-management": [
                ("INSERT", "orders", "INSERT INTO orders (user_id, cart_id, total_usd, status, created_at) VALUES (?, ?, ?, 'pending', NOW())"),
                ("SELECT", "orders", "SELECT id, status, total_usd, created_at FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 20"),
                ("UPDATE", "orders", "UPDATE orders SET status = ?, updated_at = NOW() WHERE id = ?"),
                ("SELECT", "cart_items", "SELECT ci.sku, ci.quantity, p.price, p.name FROM cart_items ci JOIN products p ON ci.sku = p.sku WHERE ci.cart_id = ?"),
            ],
            "ad-platform": [
                ("SELECT", "ad_campaigns", "SELECT campaign_id, ad_unit_id, bid_amount, targeting_rules, daily_budget FROM ad_campaigns WHERE status = 'active' AND daily_spend < daily_budget"),
                ("INSERT", "ad_impressions", "INSERT INTO ad_impressions (campaign_id, user_id, ad_unit_id, placement, timestamp) VALUES (?, ?, ?, ?, NOW())"),
                ("UPDATE", "ad_campaigns", "UPDATE ad_campaigns SET daily_spend = daily_spend + ?, impressions = impressions + 1 WHERE campaign_id = ?"),
            ],
            "recommendation-engine": [
                ("SELECT", "user_embeddings", "SELECT user_id, embedding_vector, model_version, computed_at FROM user_embeddings WHERE user_id = ? AND model_version = ?"),
                ("SELECT", "item_embeddings", "SELECT item_id, embedding_vector FROM item_embeddings WHERE item_id IN (?) AND model_version = ?"),
            ],
            "inventory-service": [
                ("SELECT", "inventory", "SELECT sku, available_qty, reserved_qty, warehouse_id FROM inventory WHERE sku = ? FOR SHARE"),
                ("UPDATE", "inventory", "UPDATE inventory SET reserved_qty = reserved_qty + ? WHERE sku = ? AND available_qty - reserved_qty >= ?"),
            ],
            "payment-processor": [
                ("INSERT", "payment_transactions", "INSERT INTO payment_transactions (order_id, provider, amount_usd, status, token_id, created_at) VALUES (?, ?, ?, 'pending', ?, NOW())"),
                ("UPDATE", "payment_transactions", "UPDATE payment_transactions SET status = ?, provider_ref = ?, settled_at = NOW() WHERE id = ?"),
                ("SELECT", "payment_tokens", "SELECT token_id, card_last4, card_brand, expiry_month, expiry_year FROM payment_tokens WHERE user_id = ? AND status = 'active'"),
            ],
            "fulfillment-orchestrator": [
                ("INSERT", "shipments", "INSERT INTO shipments (order_id, warehouse_id, carrier, tracking_number, status, created_at) VALUES (?, ?, ?, ?, 'label_created', NOW())"),
                ("SELECT", "shipments", "SELECT order_id, tracking_number, carrier, status, estimated_delivery FROM shipments WHERE order_id = ?"),
            ],
            "analytics-pipeline": [
                ("INSERT", "analytics_events", "INSERT INTO analytics_events (event_type, user_id, session_id, payload, ingested_at) VALUES (?, ?, ?, ?, NOW())"),
                ("SELECT", "analytics_aggregates", "SELECT metric_name, value, dimensions, window_start, window_end FROM analytics_aggregates WHERE metric_name = ? AND window_start >= ?"),
            ],
        }

    # ── Infrastructure ────────────────────────────────────────────────

    @property
    def hosts(self) -> list[dict[str, Any]]:
        return [
            {
                "host.name": "ecommerce-aws-host-01",
                "host.id": "i-0a1b2c3d4e5f67890",
                "host.arch": "amd64",
                "host.type": "m6i.2xlarge",
                "host.image.id": "ami-0123456789abcdef0",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "106",
                "host.cpu.stepping": "6",
                "host.cpu.cache.l2.size": 1310720,
                "host.ip": ["10.0.1.100", "172.31.0.10"],
                "host.mac": ["0e:1a:2b:3c:4d:5e", "0e:1a:2b:3c:4d:5f"],
                "os.type": "linux",
                "os.description": "Amazon Linux 2023.6.20250115",
                "cloud.provider": "aws",
                "cloud.platform": "aws_ec2",
                "cloud.region": "us-east-1",
                "cloud.availability_zone": "us-east-1a",
                "cloud.account.id": "112233445566",
                "cloud.instance.id": "i-0a1b2c3d4e5f67890",
                "cpu_count": 8,
                "memory_total_bytes": 32 * 1024 * 1024 * 1024,
                "disk_total_bytes": 500 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "ecommerce-gcp-host-01",
                "host.id": "4567890123456789012",
                "host.arch": "amd64",
                "host.type": "n2-standard-8",
                "host.image.id": "projects/debian-cloud/global/images/debian-12-bookworm-v20250115",
                "host.cpu.model.name": "Intel(R) Xeon(R) CPU @ 2.80GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "85",
                "host.cpu.stepping": "7",
                "host.cpu.cache.l2.size": 1048576,
                "host.ip": ["10.128.0.100", "10.128.0.101"],
                "host.mac": ["42:01:0a:80:00:64", "42:01:0a:80:00:65"],
                "os.type": "linux",
                "os.description": "Debian GNU/Linux 12 (bookworm)",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_compute_engine",
                "cloud.region": "us-central1",
                "cloud.availability_zone": "us-central1-a",
                "cloud.account.id": "ecommerce-prod-12345",
                "cloud.instance.id": "4567890123456789012",
                "cpu_count": 8,
                "memory_total_bytes": 32 * 1024 * 1024 * 1024,
                "disk_total_bytes": 500 * 1024 * 1024 * 1024,
            },
            {
                "host.name": "ecommerce-azure-host-01",
                "host.id": "/subscriptions/ec-prod-001/resourceGroups/ecommerce-rg/providers/Microsoft.Compute/virtualMachines/ecommerce-vm-01",
                "host.arch": "amd64",
                "host.type": "Standard_D8s_v5",
                "host.image.id": "Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest",
                "host.cpu.model.name": "Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz",
                "host.cpu.vendor.id": "GenuineIntel",
                "host.cpu.family": "6",
                "host.cpu.model.id": "106",
                "host.cpu.stepping": "6",
                "host.cpu.cache.l2.size": 1310720,
                "host.ip": ["10.1.0.100", "10.1.0.101"],
                "host.mac": ["00:22:48:1a:2b:3c", "00:22:48:1a:2b:3d"],
                "os.type": "linux",
                "os.description": "Ubuntu 22.04.5 LTS",
                "cloud.provider": "azure",
                "cloud.platform": "azure_vm",
                "cloud.region": "eastus",
                "cloud.availability_zone": "eastus-1",
                "cloud.account.id": "ec-prod-001-234-567",
                "cloud.instance.id": "ecommerce-vm-01",
                "cpu_count": 8,
                "memory_total_bytes": 32 * 1024 * 1024 * 1024,
                "disk_total_bytes": 500 * 1024 * 1024 * 1024,
            },
        ]

    @property
    def k8s_clusters(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "ecommerce-eks-cluster",
                "provider": "aws",
                "platform": "aws_eks",
                "region": "us-east-1",
                "zones": ["us-east-1a", "us-east-1b", "us-east-1c"],
                "os_description": "Amazon Linux 2",
                "services": ["storefront-gateway", "product-catalog", "order-management"],
            },
            {
                "name": "ecommerce-gke-cluster",
                "provider": "gcp",
                "platform": "gcp_gke",
                "region": "us-central1",
                "zones": ["us-central1-a", "us-central1-b", "us-central1-c"],
                "os_description": "Container-Optimized OS",
                "services": ["ad-platform", "recommendation-engine", "inventory-service"],
            },
            {
                "name": "ecommerce-aks-cluster",
                "provider": "azure",
                "platform": "azure_aks",
                "region": "eastus",
                "zones": ["eastus-1", "eastus-2", "eastus-3"],
                "os_description": "Ubuntu 22.04 LTS",
                "services": ["payment-processor", "fulfillment-orchestrator", "analytics-pipeline"],
            },
        ]

    # ── Theme ─────────────────────────────────────────────────────────

    @property
    def theme(self) -> UITheme:
        return UITheme(
            bg_primary="#0a0f1e",
            bg_secondary="#111827",
            bg_tertiary="#1f2937",
            accent_primary="#f59e0b",
            accent_secondary="#3b82f6",
            text_primary="#f9fafb",
            text_secondary="#9ca3af",
            text_accent="#f59e0b",
            status_nominal="#10b981",
            status_warning="#f59e0b",
            status_critical="#ef4444",
            status_info="#3b82f6",
            font_family="'Inter', system-ui, sans-serif",
            grid_background=True,
            chaos_title="Incident Simulator",
        )

    @property
    def countdown_config(self) -> CountdownConfig:
        return CountdownConfig(enabled=False)

    # ── Agent Config ──────────────────────────────────────────────────

    @property
    def agent_config(self) -> dict[str, Any]:
        return {
            "id": "ecommerce-ops-analyst",
            "name": "Commerce Operations Analyst",
            "assessment_tool_name": "platform_readiness_assessment",
            "system_prompt": (
                "You are the Commerce Operations Analyst for a global e-commerce platform. "
                "You help engineering and operations teams investigate incidents, analyze telemetry, "
                "and perform root cause analysis across 9 services spanning AWS, GCP, and Azure. "
                "You have deep expertise in e-commerce systems: storefront performance, product catalog search, "
                "order management, ad monetization, ML-powered personalization, payment processing, "
                "inventory management, fulfillment logistics, and real-time analytics pipelines. "
                "You understand that ad revenue is a critical business metric — when ads are not serving, "
                "that is direct, reportable revenue loss. Always quantify business impact alongside technical findings. "
                "When investigating incidents, search for these error identifiers in logs (field: body.text): "
                "payment errors (PAYMENT-GATEWAY-TIMEOUT, FRAUD-FALSE-POSITIVE, PAYMENT-TOKEN-EXPIRY), "
                "ad platform errors (ADS-SERVING-FAILURE, ADS-CLICK-BACKLOG, ADS-BUDGET-CAP), "
                "catalog errors (CATALOG-INDEX-CORRUPT, CATALOG-PRICE-SYNC), "
                "personalization errors (RECO-ENGINE-OOM, RECO-MODEL-DRIFT, RECO-CACHE-EVICTION), "
                "storefront errors (SESSION-STORM, CDN-CACHE-STORM, SSL-CERT-EXPIRY), "
                "order errors (ORDER-DB-REPLICATION-LAG, CART-ABANDON-SPIKE), "
                "inventory errors (INVENTORY-SYNC-LAG), "
                "fulfillment errors (CARRIER-RATE-LIMIT, WAREHOUSE-CAPACITY-ALERT), "
                "analytics errors (ANALYTICS-PIPELINE-LAG). "
                "Log messages are in body.text — NEVER search the body field alone."
            ),
        }

    @property
    def assessment_tool_config(self) -> dict[str, Any]:
        return {
            "id": "platform_readiness_assessment",
            "description": (
                "Comprehensive platform readiness assessment for the global commerce platform. "
                "Evaluates ad serving health, payment processing, order throughput, inventory sync, "
                "and personalization accuracy. Returns business impact metrics (GMV, ad revenue, "
                "conversion rate) alongside infrastructure health. "
                "Log message field: body.text (never use 'body' alone)."
            ),
        }

    @property
    def knowledge_base_docs(self) -> list[dict[str, Any]]:
        return []  # Populated by deployer from channel_registry

    # ── Service Classes ───────────────────────────────────────────────

    def get_service_classes(self) -> list[type]:
        from scenarios.ecommerce.services.storefront_gateway import StorefrontGatewayService
        from scenarios.ecommerce.services.product_catalog import ProductCatalogService
        from scenarios.ecommerce.services.order_management import OrderManagementService
        from scenarios.ecommerce.services.ad_platform import AdPlatformService
        from scenarios.ecommerce.services.recommendation_engine import RecommendationEngineService
        from scenarios.ecommerce.services.inventory_service import InventoryService
        from scenarios.ecommerce.services.payment_processor import PaymentProcessorService
        from scenarios.ecommerce.services.fulfillment_orchestrator import FulfillmentOrchestratorService
        from scenarios.ecommerce.services.analytics_pipeline import AnalyticsPipelineService

        return [
            StorefrontGatewayService,
            ProductCatalogService,
            OrderManagementService,
            AdPlatformService,
            RecommendationEngineService,
            InventoryService,
            PaymentProcessorService,
            FulfillmentOrchestratorService,
            AnalyticsPipelineService,
        ]

    # ── Trace Attributes & RCA ────────────────────────────────────────

    def get_trace_attributes(self, service_name: str, rng) -> dict:
        base = {
            "platform.region": rng.choice(["us-east-1", "us-central1", "eastus"]),
            "platform.traffic_tier": rng.choice(["normal", "normal", "elevated", "peak"]),
            "platform.market": rng.choice(["US", "US", "US", "JP", "EU", "UK"]),
        }
        svc_attrs = {
            "storefront-gateway": {
                "storefront.page_type": rng.choice(["home", "search", "pdp", "cart", "checkout", "confirmation"]),
                "storefront.device": rng.choice(["mobile", "mobile", "desktop", "tablet", "app"]),
                "storefront.session_type": rng.choice(["browse", "search", "checkout", "repeat_purchase"]),
                "storefront.ab_variant": rng.choice(["control", "variant_a", "variant_b"]),
            },
            "product-catalog": {
                "catalog.search_type": rng.choice(["keyword", "category", "filter", "recommendation"]),
                "catalog.result_count": rng.randint(0, 200),
                "catalog.category": rng.choice(["electronics", "apparel", "home", "beauty", "sports", "books"]),
                "catalog.index_version": rng.choice(["v12", "v12", "v12", "v13"]),
            },
            "order-management": {
                "order.channel": rng.choice(["web", "mobile_app", "mobile_web", "api"]),
                "order.payment_method": rng.choice(["credit_card", "debit_card", "paypal", "apple_pay", "google_pay", "buy_now_pay_later"]),
                "order.item_count": rng.randint(1, 8),
                "order.is_prime": rng.choice([True, True, False]),
            },
            "ad-platform": {
                "ads.placement": rng.choice(["homepage_banner", "search_top", "pdp_sidebar", "cart_upsell", "email_retargeting"]),
                "ads.format": rng.choice(["display", "sponsored_product", "video", "native"]),
                "ads.targeting_type": rng.choice(["behavioral", "contextual", "retargeting", "lookalike", "demographic"]),
                "ads.auction_type": rng.choice(["first_price", "second_price", "fixed_cpm"]),
            },
            "recommendation-engine": {
                "reco.algorithm": rng.choice(["collaborative_filter", "content_based", "hybrid", "trending"]),
                "reco.context": rng.choice(["homepage", "pdp_related", "cart_upsell", "post_purchase", "email"]),
                "reco.personalized": rng.choice([True, True, True, False]),
                "reco.model_version": rng.choice(["v8", "v8", "v8", "v9"]),
            },
            "inventory-service": {
                "inventory.warehouse_region": rng.choice(["us-east", "us-west", "us-central", "eu-west"]),
                "inventory.sku_category": rng.choice(["electronics", "apparel", "home", "beauty", "sports"]),
                "inventory.fulfillment_type": rng.choice(["standard", "express", "same_day", "pickup"]),
                "inventory.stock_tier": rng.choice(["in_stock", "in_stock", "low_stock", "backorder"]),
            },
            "payment-processor": {
                "payment.provider": rng.choice(["stripe", "adyen", "braintree", "square"]),
                "payment.currency": rng.choice(["USD", "USD", "USD", "JPY", "EUR", "GBP"]),
                "payment.card_network": rng.choice(["visa", "mastercard", "amex", "discover"]),
                "payment.3ds_required": rng.choice([False, False, True]),
            },
            "fulfillment-orchestrator": {
                "fulfillment.carrier": rng.choice(["fedex", "ups", "usps", "dhl", "amazon_logistics"]),
                "fulfillment.service_level": rng.choice(["standard", "two_day", "overnight", "same_day"]),
                "fulfillment.warehouse_id": rng.choice(["WH-US-NJ-01", "WH-US-OH-02", "WH-US-TX-03", "WH-US-CA-04"]),
                "fulfillment.package_weight_lb": round(rng.uniform(0.2, 25.0), 1),
            },
            "analytics-pipeline": {
                "analytics.event_type": rng.choice(["page_view", "product_view", "add_to_cart", "purchase", "ad_impression", "ad_click"]),
                "analytics.pipeline_stage": rng.choice(["ingest", "transform", "aggregate", "index"]),
                "analytics.consumer_group": rng.choice(["realtime-analytics", "ad-attribution", "inventory-analytics", "fraud-signals"]),
                "analytics.partition": rng.randint(0, 31),
            },
        }
        base.update(svc_attrs.get(service_name, {}))
        return base

    def get_rca_clues(self, channel: int, service_name: str, rng) -> dict:
        clues = {
            1: {  # Payment Gateway Timeout
                "payment-processor": {"payment.gateway_timeout_ms": rng.randint(3000, 15000), "payment.provider_circuit_open": True},
                "order-management": {"order.checkout_failure_rate_pct": round(rng.uniform(15, 60), 1), "order.pending_payment_count": rng.randint(50, 500)},
                "storefront-gateway": {"storefront.checkout_error_rate_pct": round(rng.uniform(10, 45), 1), "storefront.error_page_shown": True},
                "fulfillment-orchestrator": {"fulfillment.pending_payment_orders": rng.randint(20, 200), "fulfillment.hold_queue_depth": rng.randint(10, 100)},
            },
            2: {  # Ad Serving Failure
                "ad-platform": {"ads.fill_rate_pct": round(rng.uniform(0, 5), 1), "ads.ad_server_healthy": False, "ads.dsp_connected": False},
                "storefront-gateway": {"storefront.ad_slots_empty": rng.randint(3, 8), "storefront.fallback_content_served": True},
                "analytics-pipeline": {"analytics.ad_event_backlog": rng.randint(1000, 50000), "analytics.attribution_lag_min": rng.randint(5, 60)},
            },
            3: {  # Search Index Corruption
                "product-catalog": {"catalog.shard_health": "RED", "catalog.missing_docs_pct": round(rng.uniform(5, 40), 1), "catalog.search_accuracy_pct": round(rng.uniform(40, 80), 1)},
                "storefront-gateway": {"storefront.search_zero_results_pct": round(rng.uniform(20, 60), 1), "storefront.search_fallback_active": True},
                "recommendation-engine": {"reco.catalog_data_stale": True, "reco.fallback_to_trending": True},
            },
            4: {  # Warehouse Capacity
                "fulfillment-orchestrator": {"fulfillment.warehouse_capacity_pct": round(rng.uniform(88, 99), 1), "fulfillment.inbound_rejected_count": rng.randint(10, 200)},
                "inventory-service": {"inventory.overflow_sku_count": rng.randint(100, 5000), "inventory.receiving_paused_categories": rng.randint(1, 5)},
                "order-management": {"order.new_listing_hold": True, "order.extended_delivery_estimate": True},
            },
            5: {  # Checkout Session Storm
                "storefront-gateway": {"storefront.session_pool_utilization_pct": round(rng.uniform(90, 100), 1), "storefront.new_sessions_rejected": rng.randint(100, 2000)},
                "order-management": {"order.cart_creation_rate_drop_pct": round(rng.uniform(20, 70), 1), "order.checkout_queue_depth": rng.randint(50, 500)},
                "product-catalog": {"catalog.request_queue_depth": rng.randint(200, 2000), "catalog.p99_latency_ms": rng.randint(2000, 10000)},
                "analytics-pipeline": {"analytics.session_event_spike": True, "analytics.ingest_rate_multiplier": round(rng.uniform(3, 10), 1)},
            },
            6: {  # Fraud False Positive
                "payment-processor": {"payment.fraud_score_threshold_active": True, "payment.false_positive_rate_pct": round(rng.uniform(8, 25), 1)},
                "order-management": {"order.payment_decline_rate_pct": round(rng.uniform(10, 35), 1), "order.legitimate_orders_blocked": rng.randint(50, 500)},
                "storefront-gateway": {"storefront.checkout_decline_shown": True, "storefront.retry_rate_pct": round(rng.uniform(20, 60), 1)},
            },
            7: {  # Inventory Sync Lag
                "inventory-service": {"inventory.consumer_lag_events": rng.randint(5000, 100000), "inventory.sync_lag_ms": rng.randint(30000, 300000)},
                "order-management": {"order.oversell_count": rng.randint(5, 100), "order.stock_check_stale_reads": rng.randint(100, 2000)},
                "fulfillment-orchestrator": {"fulfillment.cancelled_due_to_stockout": rng.randint(10, 100), "fulfillment.manual_review_queue": rng.randint(5, 50)},
                "storefront-gateway": {"storefront.in_stock_inaccuracy_pct": round(rng.uniform(2, 15), 1)},
            },
            8: {  # Ad Click Backlog
                "ad-platform": {"ads.click_queue_depth": rng.randint(10000, 500000), "ads.attribution_delay_min": rng.randint(15, 120)},
                "analytics-pipeline": {"analytics.click_consumer_lag": rng.randint(5000, 100000), "analytics.dlq_depth": rng.randint(100, 5000)},
                "recommendation-engine": {"reco.click_signal_stale": True, "reco.behavioral_features_lag_min": rng.randint(10, 60)},
            },
            9: {  # Order DB Replication Lag
                "order-management": {"db.replica_lag_ms": rng.randint(10000, 120000), "db.stale_reads_detected": True, "db.seconds_behind_master": rng.randint(10, 120)},
                "payment-processor": {"payment.confirmation_stale_reads": rng.randint(10, 100), "payment.duplicate_charge_risk": True},
                "fulfillment-orchestrator": {"fulfillment.order_status_stale": True, "fulfillment.double_ship_risk_orders": rng.randint(1, 20)},
            },
            10: {  # CDN Cache Storm
                "storefront-gateway": {"storefront.cdn_hit_rate_pct": round(rng.uniform(5, 30), 1), "storefront.origin_rps_spike": rng.randint(5000, 50000)},
                "product-catalog": {"catalog.origin_requests_spike": rng.randint(2000, 20000), "catalog.request_coalescing_failures": rng.randint(100, 2000)},
                "analytics-pipeline": {"analytics.page_view_spike_detected": True, "analytics.ingest_backpressure": True},
            },
            11: {  # Carrier Rate Limit
                "fulfillment-orchestrator": {"fulfillment.carrier_429_count": rng.randint(100, 2000), "fulfillment.label_creation_queue_depth": rng.randint(200, 5000)},
                "order-management": {"order.in_fulfillment_stuck_count": rng.randint(50, 500), "order.sla_breach_risk_count": rng.randint(10, 100)},
                "analytics-pipeline": {"analytics.fulfillment_event_lag": True, "analytics.on_time_metric_stale": True},
            },
            12: {  # Cart Abandonment Spike
                "order-management": {"order.abandonment_rate_pct": round(rng.uniform(40, 80), 1), "order.revenue_at_risk_usd": rng.randint(10000, 500000)},
                "storefront-gateway": {"storefront.checkout_step_drop_pct": round(rng.uniform(30, 70), 1), "storefront.error_in_funnel": rng.choice(["payment_form", "address_validation", "coupon_check"])},
                "ad-platform": {"ads.retargeting_triggered": True, "ads.cart_abandonment_audience_size": rng.randint(1000, 50000)},
            },
            13: {  # Model Drift
                "recommendation-engine": {"reco.feature_drift_score": round(rng.uniform(0.3, 0.8), 2), "reco.ctr_delta_pct": round(rng.uniform(-30, -10), 1)},
                "ad-platform": {"ads.targeting_signal_quality_pct": round(rng.uniform(40, 70), 1), "ads.cpc_increase_pct": round(rng.uniform(10, 40), 1)},
                "storefront-gateway": {"storefront.reco_click_rate_drop_pct": round(rng.uniform(15, 45), 1), "storefront.personalization_confidence": "LOW"},
            },
            14: {  # Analytics Pipeline Lag
                "analytics-pipeline": {"analytics.pipeline_lag_ms": rng.randint(60000, 600000), "analytics.consumer_lag_events": rng.randint(50000, 500000)},
                "ad-platform": {"ads.budget_optimization_stale": True, "ads.bid_using_lag_min": rng.randint(10, 120)},
                "order-management": {"order.gmv_dashboard_stale_min": rng.randint(5, 60), "order.realtime_reporting_delayed": True},
            },
            15: {  # Catalog Price Sync
                "product-catalog": {"catalog.stale_price_skus": rng.randint(100, 10000), "catalog.price_lag_min": rng.randint(5, 120)},
                "inventory-service": {"inventory.price_mismatch_count": rng.randint(50, 5000), "inventory.sync_consumer_behind": True},
                "order-management": {"order.price_dispute_risk_count": rng.randint(10, 200), "order.price_validation_failures": rng.randint(5, 100)},
            },
            16: {  # SSL Cert Expiry
                "storefront-gateway": {"tls.cert_days_remaining": rng.randint(0, 7), "tls.browser_warning_triggered": True},
                "order-management": {"order.https_errors_count": rng.randint(10, 500), "order.mixed_content_warnings": rng.randint(5, 50)},
                "payment-processor": {"payment.pci_tls_validation_failed": True, "payment.secure_channel_degraded": True},
            },
            17: {  # Ad Budget Cap
                "ad-platform": {"ads.budget_exhausted": True, "ads.serving_stopped": True, "ads.hours_remaining_today": rng.randint(1, 8)},
                "analytics-pipeline": {"analytics.ad_revenue_drop_detected": True, "analytics.revenue_delta_usd_hr": rng.randint(-5000, -500)},
            },
            18: {  # Payment Token Expiry
                "payment-processor": {"payment.expired_token_count": rng.randint(100, 10000), "payment.subscription_failure_rate_pct": round(rng.uniform(5, 40), 1)},
                "order-management": {"order.subscription_renewal_failures": rng.randint(50, 5000), "order.churn_risk_count": rng.randint(10, 1000)},
            },
            19: {  # Recommendation Engine OOM
                "recommendation-engine": {"reco.heap_utilization_pct": round(rng.uniform(90, 99), 1), "reco.gc_pause_ms": rng.randint(2000, 8000), "reco.serving_fallback": "trending"},
                "storefront-gateway": {"storefront.personalization_disabled": True, "storefront.generic_reco_serving": True},
                "product-catalog": {"catalog.reco_lookup_errors": rng.randint(100, 1000), "catalog.featured_fallback_active": True},
            },
            20: {  # Reco Cache Eviction
                "recommendation-engine": {"reco.cache_hit_rate_pct": round(rng.uniform(2, 20), 1), "reco.cold_inference_p99_ms": rng.randint(3000, 15000)},
                "storefront-gateway": {"storefront.reco_timeout_count": rng.randint(100, 5000), "storefront.fallback_trending_serving": True},
                "product-catalog": {"catalog.featured_request_spike": rng.randint(200, 2000), "catalog.trending_fallback_serving": True},
            },
        }
        return clues.get(channel, {}).get(service_name, {})

    def get_fault_params(self, channel: int) -> dict[str, Any]:
        rng = random.Random(channel + int(time.time()) // 10)
        params: dict[int, dict[str, Any]] = {
            1: {
                "payment_provider": rng.choice(["stripe", "adyen", "braintree"]),
                "order_id": f"ORD-{rng.randint(100000, 999999)}",
                "session_id": f"SESS-{rng.randint(100000, 999999)}",
                "payment_timeout_ms": rng.randint(3000, 15000),
                "pool_size": rng.randint(50, 200),
                "active_connections": rng.randint(48, 200),
                "retry_count": rng.randint(2, 5),
                "last_success_sec": rng.randint(30, 300),
            },
            2: {
                "fill_rate_pct": round(rng.uniform(0, 4), 1),
                "expected_fill_pct": 85,
                "impressions_lost": rng.randint(10000, 500000),
                "revenue_impact_usd": round(rng.uniform(500, 50000), 2),
                "ad_unit_id": f"AU-{rng.randint(1000, 9999)}",
                "bid_request_id": f"BID-{rng.randint(100000, 999999)}",
                "ad_error_detail": rng.choice(["DSP_UNREACHABLE", "TARGETING_INDEX_STALE", "AD_DECISION_TIMEOUT"]),
                "expected_impressions": rng.randint(5000, 20000),
                "cpm_usd": round(rng.uniform(1.5, 8.0), 2),
                "targeting_staleness_min": rng.randint(30, 120),
            },
            3: {
                "shard_id": f"shard-{rng.randint(0, 7)}",
                "expected_items": rng.randint(500000, 2000000),
                "actual_items": rng.randint(100000, 400000),
                "doc_delta": rng.randint(100000, 1600000),
                "affected_categories": rng.choice(["electronics,apparel", "home,beauty", "sports,books", "all_categories"]),
                "snapshot_age_min": rng.randint(60, 480),
            },
            4: {
                "warehouse_id": rng.choice(["WH-US-NJ-01", "WH-US-OH-02", "WH-US-TX-03"]),
                "capacity_used_pct": round(rng.uniform(88, 98), 1),
                "capacity_used_sqft": rng.randint(880000, 980000),
                "capacity_total_sqft": 1000000,
                "inbound_units": rng.randint(5000, 50000),
                "slow_sku_count": rng.randint(500, 10000),
                "slow_sku_categories": rng.choice(["home-decor", "seasonal", "electronics-accessories"]),
                "overflow_facility": rng.choice(["WH-US-PA-OVERFLOW", "WH-US-IN-OVERFLOW"]),
                "asn_id": f"ASN-{rng.randint(10000, 99999)}",
            },
            5: {
                "active_sessions": rng.randint(48000, 55000),
                "max_sessions": 50000,
                "session_util_pct": rng.randint(94, 110),
                "rejected_sessions": rng.randint(100, 5000),
                "current_rps": rng.randint(5000, 20000),
                "rps_threshold": 10000,
                "top_source_ip": f"203.{rng.randint(0,255)}.{rng.randint(0,255)}.{rng.randint(0,255)}",
                "pool_id": f"pool-{rng.randint(1, 4)}",
                "request_id": f"REQ-{rng.randint(100000, 999999)}",
            },
            6: {
                "blocked_orders": rng.randint(50, 1000),
                "false_positive_pct": round(rng.uniform(8, 25), 1),
                "fp_threshold_pct": 2.0,
                "fraud_score": rng.randint(75, 95),
                "fraud_score_threshold": 70,
                "fraud_score_threshold_relaxed": 80,
                "block_reason": rng.choice(["velocity_check", "new_device_fingerprint", "high_value_new_account", "geo_mismatch"]),
                "revenue_held_usd": round(rng.uniform(5000, 100000), 2),
                "order_id": f"ORD-{rng.randint(100000, 999999)}",
                "checkout_id": f"CHK-{rng.randint(100000, 999999)}",
                "fraud_model_version": rng.randint(10, 20),
                "min_manual_review_usd": 500,
            },
            7: {
                "sync_lag_ms": rng.randint(30000, 300000),
                "max_lag_ms": 5000,
                "consumer_lag": rng.randint(5000, 100000),
                "oversell_risk_skus": rng.randint(10, 500),
                "write_throughput_eps": rng.randint(500, 3000),
                "kafka_partition": rng.randint(0, 15),
                "sku_batch_id": f"SKU-BATCH-{rng.randint(1000, 9999)}",
            },
            8: {
                "click_queue_depth": rng.randint(50000, 500000),
                "click_queue_max": 1000000,
                "consumer_throughput_eps": rng.randint(500, 2000),
                "ingest_rate_eps": rng.randint(5000, 20000),
                "attribution_delay_min": rng.randint(15, 120),
                "dedup_window_sec": rng.randint(60, 300),
                "click_event_id": f"CLK-{rng.randint(100000, 999999)}",
                "dlq_size": rng.randint(100, 10000),
                "suggested_consumer_count": rng.randint(5, 20),
                "eta_min": rng.randint(10, 60),
            },
            9: {
                "replica_host": f"order-db-replica-{rng.randint(1, 3)}.us-east-1.internal",
                "replication_lag_ms": rng.randint(10000, 120000),
                "max_replication_lag_ms": 1000,
                "relay_log_space_mb": rng.randint(500, 5000),
                "seconds_behind_master": rng.randint(10, 120),
                "order_id": f"ORD-{rng.randint(100000, 999999)}",
                "failover_threshold_ms": 30000,
            },
            10: {
                "cache_hit_rate_pct": round(rng.uniform(5, 25), 1),
                "normal_hit_rate_pct": 92,
                "origin_rps": rng.randint(5000, 50000),
                "invalidation_keys": rng.randint(10000, 500000),
                "origin_cpu_pct": rng.randint(70, 98),
                "max_invalidations_per_min": 1000,
                "request_path": rng.choice(["/p/12345", "/category/electronics", "/search?q=laptop", "/home"]),
                "cdn_edge_count": rng.randint(50, 200),
            },
            11: {
                "carrier_name": rng.choice(["FedEx", "UPS", "DHL"]),
                "api_quota_used": rng.randint(9800, 10000),
                "api_quota_max": 10000,
                "reset_in_sec": rng.randint(60, 3600),
                "queued_labels": rng.randint(200, 5000),
                "secondary_carrier": rng.choice(["USPS", "OnTrac", "LSO"]),
                "order_id": f"ORD-{rng.randint(100000, 999999)}",
                "rate_limit_reset_epoch": int(time.time()) + rng.randint(60, 3600),
            },
            12: {
                "abandonment_rate_pct": round(rng.uniform(45, 80), 1),
                "baseline_abandonment_pct": 25.0,
                "abandoned_carts": rng.randint(500, 10000),
                "revenue_at_risk_usd": round(rng.uniform(50000, 500000), 2),
                "abandon_step": rng.choice(["payment_entry", "address_input", "shipping_selection", "coupon_validation"]),
                "session_id": f"SESS-{rng.randint(100000, 999999)}",
                "recovery_rate_pct": rng.randint(8, 20),
                "coupon_timeout_ms": rng.randint(3000, 10000),
                "avg_funnel_time_sec": rng.randint(45, 180),
            },
            13: {
                "model_version": rng.randint(8, 12),
                "hit_rate_pct": round(rng.uniform(20, 45), 1),
                "hit_rate_threshold_pct": 60.0,
                "drift_score": round(rng.uniform(0.3, 0.8), 2),
                "prev_model_version": rng.randint(6, 9),
                "user_id": f"USR-{rng.randint(100000, 999999)}",
                "affected_users_hr": rng.randint(10000, 500000),
            },
            14: {
                "pipeline_lag_ms": rng.randint(60000, 600000),
                "max_pipeline_lag_ms": 5000,
                "consumer_lag": rng.randint(50000, 500000),
                "events_per_sec": rng.randint(10000, 100000),
                "hot_partition": f"partition-{rng.randint(0, 31)}",
                "batch_id": f"BATCH-{rng.randint(10000, 99999)}",
                "hot_partition_events": rng.randint(3, 15),
                "eta_drain_min": rng.randint(10, 60),
            },
            15: {
                "failed_price_updates": rng.randint(100, 5000),
                "total_price_updates": rng.randint(5000, 50000),
                "price_lag_min": rng.randint(5, 120),
                "price_lag_events": rng.randint(1000, 50000),
                "affected_price_skus": rng.randint(100, 10000),
                "sku_id": f"SKU-{rng.randint(100000, 999999)}",
                "price_batch_id": f"PRICE-BATCH-{rng.randint(1000, 9999)}",
                "price_delta_threshold_pct": 5.0,
            },
            16: {
                "cert_domain": rng.choice(["shop.example.com", "checkout.example.com", "api.example.com"]),
                "cert_serial": f"{rng.randint(10000000, 99999999):X}",
                "cert_days_remaining": rng.randint(0, 7),
                "cert_issuer": rng.choice(["Let's Encrypt", "DigiCert", "Comodo"]),
                "cert_san_count": rng.randint(3, 15),
                "auto_renewal_status": rng.choice(["FAILED", "NOT_CONFIGURED", "EXPIRED"]),
            },
            17: {
                "campaign_id": f"CAMP-{rng.randint(1000, 9999)}",
                "budget_spent_usd": round(rng.uniform(8000, 10000), 2),
                "budget_daily_usd": 10000.0,
                "avg_cpc_usd": round(rng.uniform(0.8, 3.5), 2),
                "expected_cpc_usd": round(rng.uniform(0.5, 1.5), 2),
                "win_rate_pct": round(rng.uniform(15, 45), 1),
                "hours_remaining": rng.randint(2, 10),
                "hourly_revenue_usd": round(rng.uniform(500, 5000), 2),
                "bid_request_id": f"BID-{rng.randint(100000, 999999)}",
            },
            18: {
                "expired_tokens": rng.randint(100, 10000),
                "affected_subscriptions": rng.randint(50, 5000),
                "subscription_revenue_usd": round(rng.uniform(5000, 500000), 2),
                "token_max_age_days": rng.randint(90, 365),
                "token_id": f"TOK-{rng.randint(100000, 999999)}",
                "subscription_id": f"SUB-{rng.randint(100000, 999999)}",
            },
            19: {
                "heap_used_mb": rng.randint(7500, 9800),
                "heap_max_mb": 10240,
                "model_version": rng.randint(7, 10),
                "batch_size": rng.randint(64, 512),
                "cache_size_mb": rng.randint(4000, 8000),
                "gc_pause_ms": rng.randint(2000, 8000),
            },
            20: {
                "cache_hit_rate_pct": round(rng.uniform(2, 15), 1),
                "normal_cache_hit_pct": 85,
                "evicted_entries": rng.randint(100000, 5000000),
                "p99_latency_ms": rng.randint(3000, 15000),
                "warm_latency_ms": rng.randint(50, 200),
                "cache_size_mb": rng.randint(2048, 8192),
                "user_id": f"USR-{rng.randint(100000, 999999)}",
                "warm_user_count": rng.randint(10000, 100000),
            },
        }
        return params.get(channel, {})

    def get_correlation_attribute(self, channel: int, is_error: bool, rng) -> dict:
        correlations = {
            1: ("payment.gateway_degraded", True),
            2: ("ads.serving_degraded", True),
            3: ("catalog.index_unhealthy", True),
            4: ("fulfillment.warehouse_capacity_critical", True),
            5: ("storefront.session_pressure", True),
            6: ("payment.fraud_model_misfiring", True),
            7: ("inventory.sync_lagging", True),
            8: ("ads.click_backlog_active", True),
            9: ("orders.db_replication_lagging", True),
            10: ("storefront.cdn_cache_cold", True),
            11: ("fulfillment.carrier_throttled", True),
            12: ("orders.abandonment_elevated", True),
            13: ("reco.model_drifting", True),
            14: ("analytics.pipeline_lagging", True),
            15: ("catalog.prices_stale", True),
            16: ("storefront.cert_expiring", True),
            17: ("ads.budget_exhausted", True),
            18: ("payment.tokens_expiring", True),
            19: ("reco.engine_degraded", True),
            20: ("reco.cache_cold", True),
        }
        if channel in correlations:
            key, val = correlations[channel]
            if is_error:
                return {key: val} if rng.random() < 0.90 else {}
            else:
                return {key: val} if rng.random() < 0.05 else {}
        return {}


scenario = EcommerceScenario()

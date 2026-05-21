#!/usr/bin/env python3
"""RUM (Real User Monitoring) generator — emits page-load transactions via OTLP.

Generates browser-side page-load transactions for citizen-facing FCC portals
(consumer complaints, broadband map, ULS license lookup, public datasets, etc.)
so Kibana → Observability → User Experience and APM → RUM views are populated
during the demo.

Each cycle emits page-load transactions with the fields Kibana's
Observability → User Experience UI reads directly:
  - transaction.type = "page-load", agent.name = "rum-js"
  - Core Web Vitals: transaction.marks.agent.{ttfb,fcp,lcp,domInteractive}
    (in seconds), transaction.experience.{cls,fid,tbt,longtask.*}
  - Geo (country_iso_code + region_iso_code) — US-heavy, weighted states
  - User-agent / browser / OS / device breakdown
  - Occasional JS errors (~3% baseline, 8% on chaos-degraded pages)
  - Resource-timing child spans for navigation, fetch, render

Usage (standalone):
    python3 -m log_generators.synthetics_rum_generator
"""

from __future__ import annotations

import logging
import os
import random
import secrets
import signal
import threading
import time

from app.telemetry import OTLPClient, _format_attributes, SCHEMA_URL
from app.config import ACTIVE_SCENARIO, NAMESPACE

logger = logging.getLogger("synthetics-rum-generator")

# ── Configuration ─────────────────────────────────────────────────────────────
BATCH_INTERVAL_MIN = 3
BATCH_INTERVAL_MAX = 6
PAGE_LOADS_PER_CYCLE_MIN = 6
PAGE_LOADS_PER_CYCLE_MAX = 14

SPAN_KIND_INTERNAL = 1
SPAN_KIND_SERVER = 2
SPAN_KIND_CLIENT = 3
STATUS_OK = 1
STATUS_ERROR = 2

# ── FCC citizen-facing portals (RUM services) ─────────────────────────────────
RUM_SERVICES = {
    "fcc-public-portal": {
        "domain": "www.fcc.gov",
        "pages": [
            ("/", "FCC Home"),
            ("/about", "About the FCC"),
            ("/news", "Newsroom"),
            ("/document/daily-business", "Daily Business"),
        ],
    },
    "fcc-complaint-portal": {
        "domain": "consumercomplaints.fcc.gov",
        "pages": [
            ("/hc/en-us", "Consumer Complaints Home"),
            ("/hc/en-us/articles/billing", "File a Billing Complaint"),
            ("/hc/en-us/articles/internet", "File an Internet Complaint"),
            ("/hc/en-us/articles/phone", "File a Phone Complaint"),
            ("/hc/en-us/articles/accessibility", "File an Accessibility Complaint"),
        ],
    },
    "fcc-broadband-map": {
        "domain": "broadbandmap.fcc.gov",
        "pages": [
            ("/home", "Broadband Map Home"),
            ("/location-summary/fixed", "Fixed Broadband at Location"),
            ("/location-summary/mobile", "Mobile Broadband at Location"),
            ("/challenge", "Submit a Coverage Challenge"),
            ("/data-download", "Broadband Data Download"),
        ],
    },
    "fcc-uls-portal": {
        "domain": "wireless2.fcc.gov",
        "pages": [
            ("/UlsApp/UlsSearch/searchLicense.jsp", "ULS License Search"),
            ("/UlsApp/UlsSearch/searchAmateur.jsp", "Amateur Radio License Search"),
            ("/UlsApp/UlsEntry/licManager/login.jsp", "ULS License Manager"),
        ],
    },
    "fcc-data-portal": {
        "domain": "opendata.fcc.gov",
        "pages": [
            ("/datasets/broadband", "Broadband Data Sets"),
            ("/datasets/nors", "NORS Outage Data"),
            ("/datasets/auctions", "Spectrum Auction Results"),
            ("/foia/requests", "FOIA Request Portal"),
        ],
    },
}

# ── Geo profiles (weighted US-heavy) ──────────────────────────────────────────
GEO_PROFILES = [
    ("US", "United States", "VA", "Arlington", 25),
    ("US", "United States", "DC", "Washington", 18),
    ("US", "United States", "CA", "Los Angeles", 12),
    ("US", "United States", "CA", "San Francisco", 8),
    ("US", "United States", "TX", "Houston", 7),
    ("US", "United States", "NY", "New York", 9),
    ("US", "United States", "FL", "Miami", 5),
    ("US", "United States", "IL", "Chicago", 5),
    ("US", "United States", "WA", "Seattle", 4),
    ("US", "United States", "GA", "Atlanta", 3),
    ("US", "United States", "CO", "Denver", 2),
    ("US", "United States", "MA", "Boston", 2),
]

# ── Browser / user agent profiles ─────────────────────────────────────────────
BROWSER_PROFILES = [
    {
        "name": "Chrome", "version": "131.0.6778.85",
        "os": "Mac OS X", "os_version": "14.7.1",
        "device": "Other", "device_type": "desktop",
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "weight": 32,
    },
    {
        "name": "Chrome", "version": "131.0.6778.85",
        "os": "Windows", "os_version": "10",
        "device": "Other", "device_type": "desktop",
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "weight": 28,
    },
    {
        "name": "Safari", "version": "18.1",
        "os": "iOS", "os_version": "18.1",
        "device": "iPhone", "device_type": "mobile",
        "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1",
        "weight": 14,
    },
    {
        "name": "Safari", "version": "18.1",
        "os": "Mac OS X", "os_version": "14.7.1",
        "device": "Other", "device_type": "desktop",
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
        "weight": 8,
    },
    {
        "name": "Edge", "version": "131.0.2903.51",
        "os": "Windows", "os_version": "11",
        "device": "Other", "device_type": "desktop",
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        "weight": 7,
    },
    {
        "name": "Firefox", "version": "133.0",
        "os": "Windows", "os_version": "10",
        "device": "Other", "device_type": "desktop",
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
        "weight": 5,
    },
    {
        "name": "Chrome Mobile", "version": "131.0.6778.85",
        "os": "Android", "os_version": "14",
        "device": "Pixel 8", "device_type": "mobile",
        "ua": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
        "weight": 6,
    },
]

# ── JS errors (occasional, ~3% of sessions) ───────────────────────────────────
JS_ERRORS = [
    ("TypeError", "Cannot read properties of undefined (reading 'session')"),
    ("TypeError", "Cannot read properties of null (reading 'addEventListener')"),
    ("ReferenceError", "dataLayer is not defined"),
    ("Error", "Network request failed"),
    ("SyntaxError", "Unexpected token '<' at position 0"),
    ("RangeError", "Maximum call stack size exceeded"),
]


def _weighted_choice(rng: random.Random, items, weight_key):
    """Pick an item weighted by the given key."""
    weights = [item[weight_key] if isinstance(item, dict) else item[-1] for item in items]
    return rng.choices(items, weights=weights, k=1)[0]


def _gen_trace_id() -> str:
    return secrets.token_hex(16)


def _gen_span_id() -> str:
    return secrets.token_hex(8)


def _gen_client_ip(rng: random.Random) -> str:
    """Generate a realistic-looking public client IP."""
    blocks = [
        (50, 64), (66, 76), (96, 108), (128, 168), (172, 180), (192, 220),
    ]
    a_range = rng.choice(blocks)
    return f"{rng.randint(a_range[0], a_range[1])}.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"


def _build_resource(service_name: str, namespace: str) -> dict:
    """Build an RUM service resource — JS/browser-side."""
    attrs = {
        "service.name": service_name,
        "service.namespace": namespace,
        "service.version": "2026.05",
        "service.environment": f"production-{namespace}",
        "service.framework.name": "Elastic RUM",
        "service.framework.version": "5.16.0",
        "agent.name": "rum-js",
        "agent.version": "5.16.0",
        "telemetry.sdk.language": "javascript",
        "telemetry.sdk.name": "opentelemetry",
        "telemetry.sdk.version": "1.30.0",
        "deployment.environment": f"production-{namespace}",
        "data_stream.type": "traces",
        "data_stream.dataset": "apm.rum",
        "data_stream.namespace": "default",
    }
    return {
        "attributes": _format_attributes(attrs),
        "schemaUrl": SCHEMA_URL,
    }


def _generate_page_load(
    client: OTLPClient,
    service_name: str,
    service_cfg: dict,
    rng: random.Random,
    slow_page_paths: set[str] | None = None,
) -> list[dict]:
    """Generate one page-load transaction with timing breakdown + optional JS error.

    Returns a list of spans (root page-load + child resource-timing spans).
    """
    trace_id = _gen_trace_id()
    root_span_id = _gen_span_id()
    domain = service_cfg["domain"]
    path, page_title = rng.choice(service_cfg["pages"])
    geo = _weighted_choice(rng, GEO_PROFILES, weight_key=-1)
    geo_country_iso, geo_country, geo_region, geo_city, _w = geo
    browser = _weighted_choice(rng, BROWSER_PROFILES, weight_key="weight")
    referrer = rng.choice([
        "https://www.google.com/",
        "https://www.bing.com/",
        "https://duckduckgo.com/",
        f"https://{domain}/",
        "",
        "https://twitter.com/",
    ])

    # Latency profile: mobile and slower pages get worse timings
    is_mobile = browser["device_type"] == "mobile"
    is_slow_page = slow_page_paths and path in slow_page_paths

    if is_slow_page:
        ttfb_ms = rng.randint(800, 2400)
        fcp_ms = ttfb_ms + rng.randint(400, 1200)
        lcp_ms = fcp_ms + rng.randint(800, 3500)
        dom_ms = fcp_ms + rng.randint(200, 800)
        total_ms = lcp_ms + rng.randint(200, 1200)
    elif is_mobile:
        ttfb_ms = rng.randint(220, 680)
        fcp_ms = ttfb_ms + rng.randint(280, 720)
        lcp_ms = fcp_ms + rng.randint(400, 1400)
        dom_ms = fcp_ms + rng.randint(120, 380)
        total_ms = lcp_ms + rng.randint(120, 600)
    else:
        ttfb_ms = rng.randint(80, 320)
        fcp_ms = ttfb_ms + rng.randint(140, 460)
        lcp_ms = fcp_ms + rng.randint(220, 900)
        dom_ms = fcp_ms + rng.randint(80, 240)
        total_ms = lcp_ms + rng.randint(60, 380)

    # JS error rate — 3% baseline, 8% for slow pages
    has_js_error = rng.random() < (0.08 if is_slow_page else 0.03)
    page_status = STATUS_ERROR if has_js_error else STATUS_OK
    http_status = rng.choice([500, 502, 503]) if has_js_error and rng.random() < 0.4 else 200

    # Core Web Vitals — values the Kibana User Experience UI reads directly.
    # CLS (unitless), FID (ms), TBT (ms) — degraded pages get worse vitals.
    if is_slow_page:
        cls = round(rng.uniform(0.10, 0.35), 3)
        fid_ms = round(rng.uniform(120.0, 380.0), 1)
        tbt_ms = round(rng.uniform(400.0, 1400.0), 1)
        longtask_count = rng.randint(6, 18)
        longtask_max_ms = round(rng.uniform(180.0, 520.0), 1)
    elif is_mobile:
        cls = round(rng.uniform(0.0, 0.12), 3)
        fid_ms = round(rng.uniform(20.0, 110.0), 1)
        tbt_ms = round(rng.uniform(80.0, 260.0), 1)
        longtask_count = rng.randint(1, 6)
        longtask_max_ms = round(rng.uniform(60.0, 180.0), 1)
    else:
        cls = round(rng.uniform(0.0, 0.08), 3)
        fid_ms = round(rng.uniform(5.0, 70.0), 1)
        tbt_ms = round(rng.uniform(20.0, 160.0), 1)
        longtask_count = rng.randint(0, 4)
        longtask_max_ms = round(rng.uniform(40.0, 140.0), 1)
    longtask_sum_ms = round(longtask_max_ms * rng.uniform(1.2, 2.4), 1) if longtask_count else 0.0

    page_attrs = {
        "transaction.type": "page-load",
        "transaction.name": f"{page_title}",
        "transaction.duration.us": total_ms * 1000,
        "transaction.result": f"HTTP {http_status // 100}xx",
        "transaction.sampled": True,
        # ── Core Web Vitals (Kibana User Experience UI reads these) ─────────
        "transaction.marks.agent.timeToFirstByte": round(ttfb_ms / 1000.0, 3),
        "transaction.marks.agent.firstContentfulPaint": round(fcp_ms / 1000.0, 3),
        "transaction.marks.agent.largestContentfulPaint": round(lcp_ms / 1000.0, 3),
        "transaction.marks.agent.domInteractive": round(dom_ms / 1000.0, 3),
        "transaction.experience.cls": cls,
        "transaction.experience.fid": fid_ms,
        "transaction.experience.tbt": tbt_ms,
        "transaction.experience.longtask.count": longtask_count,
        "transaction.experience.longtask.sum": longtask_sum_ms,
        "transaction.experience.longtask.max": longtask_max_ms,
        # ── URL / HTTP ──────────────────────────────────────────────────────
        "url.full": f"https://{domain}{path}",
        "url.domain": domain,
        "url.path": path,
        "url.scheme": "https",
        "http.request.method": "GET",
        "http.response.status_code": http_status,
        "http.request.referrer": referrer,
        # ── User agent ──────────────────────────────────────────────────────
        "user_agent.original": browser["ua"],
        "user_agent.name": browser["name"],
        "user_agent.version": browser["version"],
        "user_agent.os.name": browser["os"],
        "user_agent.os.version": browser["os_version"],
        "user_agent.device.name": browser["device"],
        # ── Geo (region_iso_code drives the UX map drill-down) ──────────────
        "client.geo.country_iso_code": geo_country_iso,
        "client.geo.country_name": geo_country,
        "client.geo.region_iso_code": f"{geo_country_iso}-{geo_region}",
        "client.geo.region_name": geo_region,
        "client.geo.city_name": geo_city,
        "client.ip": _gen_client_ip(rng),
        # ── Session / user ──────────────────────────────────────────────────
        "session.id": secrets.token_hex(8),
        "user.id": f"anon-{rng.randint(100000, 999999)}",
    }

    # Optional JS error event on the root span
    events = None
    if has_js_error:
        err_type, err_msg = rng.choice(JS_ERRORS)
        stack = (
            f"{err_type}: {err_msg}\n"
            f"    at HTMLDocument.<anonymous> (https://{domain}/assets/app.js:142:24)\n"
            f"    at e (https://{domain}/assets/app.js:1:18234)\n"
            f"    at Object.dispatch (https://{domain}/assets/vendor.js:8:42117)"
        )
        events = [client.build_exception_event(err_type, err_msg, stack)]

    root_span = client.build_span(
        name=f"{path}",
        trace_id=trace_id,
        span_id=root_span_id,
        kind=SPAN_KIND_SERVER,
        duration_ms=total_ms,
        status_code=page_status,
        attributes=page_attrs,
        events=events,
    )
    spans = [root_span]

    # Child resource-timing spans — the network/asset waterfall
    resources = [
        ("GET /assets/app.js", "resource.script", rng.randint(40, 180)),
        ("GET /assets/vendor.js", "resource.script", rng.randint(60, 240)),
        ("GET /assets/main.css", "resource.stylesheet", rng.randint(20, 90)),
        ("GET /api/v1/session", "resource.xhr", rng.randint(80, 320)),
    ]
    elapsed = ttfb_ms
    for res_name, res_type, res_duration in resources:
        if rng.random() < 0.85:  # 85% of pages load these resources
            res_span_id = _gen_span_id()
            res_span = client.build_span(
                name=res_name,
                trace_id=trace_id,
                span_id=res_span_id,
                parent_span_id=root_span_id,
                kind=SPAN_KIND_CLIENT,
                duration_ms=res_duration,
                status_code=STATUS_OK,
                attributes={
                    "span.type": res_type,
                    "url.full": f"https://{domain}{res_name.split(' ', 1)[1]}",
                    "http.request.method": "GET",
                    "http.response.status_code": 200,
                },
            )
            spans.append(res_span)
            elapsed += res_duration

    return spans


def run(client: OTLPClient, stop_event: threading.Event, chaos_controller=None,
        scenario_data: dict | None = None) -> None:
    """Run the RUM page-load generator until stop_event is set."""
    rng = random.Random()
    namespace = scenario_data["namespace"] if scenario_data else NAMESPACE

    # Pre-build per-service resource attribute blocks
    resources = {svc: _build_resource(svc, namespace) for svc in RUM_SERVICES}

    total_pages = 0
    total_spans = 0
    total_errors = 0

    logger.info(
        "RUM/Synthetics generator started — emitting page-loads for %d portals "
        "(%s)", len(RUM_SERVICES), ", ".join(RUM_SERVICES.keys()),
    )

    while not stop_event.is_set():
        # If any active chaos channels affect the public-facing services, mark
        # corresponding RUM page paths as slow so a fault visibly impacts DEM.
        slow_paths: set[str] = set()
        if chaos_controller:
            active = chaos_controller.get_active_channels()
            if active:
                # When any channel is active, treat the complaint and broadband-map
                # portal home pages as degraded — those are the citizen-facing
                # surfaces most likely to suffer first.
                slow_paths.update({"/hc/en-us", "/home", "/", "/location-summary/fixed"})

        n_pages = rng.randint(PAGE_LOADS_PER_CYCLE_MIN, PAGE_LOADS_PER_CYCLE_MAX)
        batch_by_service: dict[str, list] = {}

        for _ in range(n_pages):
            svc = rng.choice(list(RUM_SERVICES.keys()))
            spans = _generate_page_load(
                client, svc, RUM_SERVICES[svc], rng,
                slow_page_paths=slow_paths or None,
            )
            batch_by_service.setdefault(svc, []).extend(spans)
            # Count errors (root span status_code == 2)
            if spans and spans[0].get("status", {}).get("code") == STATUS_ERROR:
                total_errors += 1

        batch_span_count = 0
        for svc, spans in batch_by_service.items():
            if spans:
                client.send_traces(resources[svc], spans)
                batch_span_count += len(spans)

        total_pages += n_pages
        total_spans += batch_span_count
        logger.info(
            "Sent %d page-loads (%d spans) — total: %d pages, %d spans, %d JS errors",
            n_pages, batch_span_count, total_pages, total_spans, total_errors,
        )

        sleep_time = rng.uniform(BATCH_INTERVAL_MIN, BATCH_INTERVAL_MAX)
        stop_event.wait(sleep_time)

    logger.info(
        "RUM/Synthetics generator stopped. Total: %d page-loads, %d spans, %d JS errors",
        total_pages, total_spans, total_errors,
    )


# ── Standalone entry point ────────────────────────────────────────────────────
def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    client = OTLPClient()
    stop_event = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())
    duration = int(os.environ.get("RUN_DURATION", "60"))
    timer = threading.Timer(duration, stop_event.set)
    timer.daemon = True
    timer.start()
    logger.info("Running for %ds (standalone mode)", duration)
    run(client, stop_event)
    timer.cancel()
    client.close()


if __name__ == "__main__":
    main()

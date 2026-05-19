#!/usr/bin/env python3
"""Raw access-log generator — emits intentionally unparsed CLF-style logs in ECS shape.

Bypasses OTLP and writes directly to Elasticsearch (`logs-ecs.{ns}-default` data
stream) via `_bulk` so the demo can showcase:
  * Streams partition/parsing on the fly (AI-driven Grok inference on `message`)
  * Significant events generated from the freshly parsed fields
  * The Agent Builder `visualization-creation` skill building a dashboard from
    domain-relevant raw data

Paths, user-id prefix, tier field, and the change-point path are scenario-specific
(see each scenario's `raw_log_profile`).

Usage (standalone):
    python3 -m log_generators.raw_access_log_generator
"""

from __future__ import annotations

import logging
import os
import random
import signal
import threading
import time
from datetime import datetime, timezone
from typing import Any

from app.telemetry import ESBulkClient

logger = logging.getLogger("raw-access-log-generator")

# ── Configuration ─────────────────────────────────────────────────────────────
BATCH_INTERVAL_MIN = 2
BATCH_INTERVAL_MAX = 5
BATCH_SIZE_MIN = 5
BATCH_SIZE_MAX = 25

STATUS_WEIGHTS_NORMAL = {
    200: 60, 201: 5, 301: 3, 304: 8,
    400: 5, 401: 3, 403: 2, 404: 8,
    500: 4, 502: 3, 503: 2,
}
STATUS_WEIGHTS_SPIKE = {
    200: 25, 201: 3, 301: 2, 304: 5,
    400: 6, 401: 3, 403: 2, 404: 10,
    500: 18, 502: 14, 503: 12,
}

USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edg/120.0.0.0",
    "curl/8.4.0",
    "python-httpx/0.27.0",
]

# Spike placement — irregular, with long stretches of baseline so ML jobs
# learn a flat "normal" and flag the spikes as anomalies.
#
# Tuning notes from validation against Kibana's logs_ui_analysis ML job:
#   * Periodic spikes (e.g. every 30 min) get absorbed into baseline → no anomalies.
#   * Small spike amplitudes (4x) on top of a moderate baseline (~4500 events/bucket)
#     don't cross ML's adaptive threshold even at 4x — needed 10x to trigger.
#   * 30-min sustained spikes (2 buckets) flag more reliably than single-bucket pops.
#   * The model learns variance from the first spike → subsequent same-amplitude spikes
#     often go undetected. For demo purposes, one clear anomaly is the design point.
SPIKE_DURATION_SECONDS = 30 * 60        # 30-min incidents (spans 2 bucket_spans)
SPIKE_INTERVAL_MIN_SECONDS = 90 * 60    # at least 90 min between spikes
SPIKE_INTERVAL_MAX_SECONDS = 180 * 60   # at most 180 min between spikes
SPIKE_VOLUME_MULTIPLIER = 10            # 10x baseline volume during a spike

# Backfill-specific: place exactly N incidents in the historical window. One
# spike past the model's warm-up window is enough for a clean demo anomaly;
# additional spikes get absorbed into learned variance and rarely score.
BACKFILL_INCIDENT_COUNT = 3


def _weighted_choice(rng: random.Random, weights: dict) -> Any:
    keys = list(weights.keys())
    vals = list(weights.values())
    return rng.choices(keys, weights=vals, k=1)[0]


def _format_clf_timestamp(ts: float) -> str:
    """Common Log Format timestamp, e.g. 09/May/2026:18:42:11 +0000."""
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%d/%b/%Y:%H:%M:%S +0000")


def _iso_timestamp(ts: float) -> str:
    """ISO 8601 millisecond-precision UTC timestamp."""
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(dt.microsecond / 1000):03d}Z"


def _random_ip(rng: random.Random) -> str:
    # Mix of RFC1918 + public-ish IPs; avoids 0/127/255 prefixes
    octet_a = rng.choice([10, 172, 192, 203, 198, 73, 84, 156, 161])
    return f"{octet_a}.{rng.randint(0, 254)}.{rng.randint(0, 254)}.{rng.randint(1, 254)}"


def generate_record(
    profile: dict[str, Any],
    namespace: str,
    rng: random.Random,
    ts: float | None = None,
    spike_active: bool = False,
    spike_country: str | None = None,
) -> dict[str, Any]:
    """Build one ECS-shaped record. `message` is the raw CLF-style body — no
    extracted fields beyond service identity, by design."""
    ts = ts if ts is not None else time.time()
    method = rng.choice(profile["methods"])
    paths = profile["paths"]
    change_path = profile["change_point_path"]

    if spike_active:
        status = _weighted_choice(rng, STATUS_WEIGHTS_SPIKE)
        # 60% of spike traffic hits the change-point path
        path = change_path if rng.random() < 0.6 else rng.choice(paths)
    else:
        status = _weighted_choice(rng, STATUS_WEIGHTS_NORMAL)
        path = rng.choice(paths)

    # Response-time skew: 5xx slow, change-point path slow during spike
    if status >= 500:
        rt_ms = rng.randint(200, 2000)
    elif spike_active and path == change_path:
        rt_ms = rng.randint(400, 1500)
    else:
        rt_ms = rng.randint(5, 800)

    body_bytes = rng.randint(80, 50000) if status < 400 else rng.randint(50, 800)

    user_id = f"{profile['user_id_prefix']}{rng.randint(1, 500):05d}"

    # Geo: 80% concentration on spike_country during spike, otherwise weighted
    country_weights = profile["country_weights"]
    if spike_active and spike_country and rng.random() < 0.8:
        country = spike_country
    else:
        country = _weighted_choice(rng, country_weights)

    tier_values = profile["tier_values"]
    tier = rng.choices(
        [t[0] for t in tier_values], weights=[t[1] for t in tier_values], k=1
    )[0]

    ip = _random_ip(rng)
    ua = rng.choice(USER_AGENTS)
    ts_clf = _format_clf_timestamp(ts)

    message = (
        f'{ip} - {user_id} [{ts_clf}] "{method} {path} HTTP/1.1" {status} {body_bytes} '
        f'rt={rt_ms}ms "{ua}" geo={country} {profile["tier_field"]}={tier}'
    )

    return {
        "@timestamp": _iso_timestamp(ts),
        "message": message,
        "service.name": profile["service_name"],
        "service.namespace": namespace,
    }


def plan_backfill_spike_windows(
    start_ts: float, end_ts: float, count: int = BACKFILL_INCIDENT_COUNT,
    rng: random.Random | None = None,
) -> list[tuple[float, float]]:
    """Place `count` non-overlapping spike windows of SPIKE_DURATION_SECONDS
    in [start_ts, end_ts], with at least SPIKE_INTERVAL_MIN_SECONDS between
    them. Used by the deployer's backfill so the rate ML job sees a few
    well-separated anomalies on an otherwise flat baseline."""
    r = rng or random.Random(0xE15C)
    span = end_ts - start_ts
    buffer = SPIKE_INTERVAL_MIN_SECONDS
    min_gap = SPIKE_INTERVAL_MIN_SECONDS
    duration = SPIKE_DURATION_SECONDS

    usable_start = start_ts + buffer
    usable_end = end_ts - duration - buffer
    if usable_end <= usable_start:
        return []

    # Reject-sample until we have `count` windows with min_gap separation.
    for _ in range(100):
        picks = sorted(r.uniform(usable_start, usable_end) for _ in range(count))
        ok = all(picks[i + 1] - picks[i] >= duration + min_gap for i in range(len(picks) - 1))
        if ok:
            return [(p, p + duration) for p in picks]
    # Fallback: evenly spaced
    step = (usable_end - usable_start) / max(1, count - 1) if count > 1 else 0
    return [(usable_start + i * step, usable_start + i * step + duration) for i in range(count)]


def is_in_spike_window(ts: float, windows: list[tuple[float, float]]) -> bool:
    """Return True if ts falls within any (begin, end) spike window."""
    for begin, end in windows:
        if begin <= ts < end:
            return True
    return False


class LiveSpikeSchedule:
    """Tracks the next spike for the live generator. Spikes are placed at
    irregular intervals (SPIKE_INTERVAL_MIN..MAX seconds apart) so the ML
    model doesn't learn the pattern as 'normal'."""

    def __init__(self, rng: random.Random):
        self._rng = rng
        self._next_spike_start: float | None = None
        self._next_spike_end: float | None = None

    def _schedule_next(self, after: float) -> None:
        gap = self._rng.uniform(SPIKE_INTERVAL_MIN_SECONDS, SPIKE_INTERVAL_MAX_SECONDS)
        self._next_spike_start = after + gap
        self._next_spike_end = self._next_spike_start + SPIKE_DURATION_SECONDS

    def is_spike_active(self, now: float) -> bool:
        if self._next_spike_start is None:
            # Bootstrap: don't spike immediately on startup
            self._schedule_next(now)
            return False
        if now >= self._next_spike_end:
            self._schedule_next(now)
            return False
        return now >= self._next_spike_start


ECS_WIRED_STREAM = "logs.ecs"


def data_stream_for(namespace: str | None = None) -> str:
    """All scenarios POST to the `logs.ecs` wired-stream ingest endpoint.

    In Elastic 9.4+ wired streams replace classic data streams for the
    `logs.otel` / `logs.ecs` namespaces. The deployer forks `logs.ecs` into
    per-scenario partitions `logs.ecs.{ns}` filtered by service.namespace,
    mirroring how `logs.otel` and `logs.otel.{ns}` are handled.
    The `namespace` parameter is kept for API compatibility but ignored.

    See https://www.elastic.co/docs/solutions/observability/streams/wired-streams
    """
    return ECS_WIRED_STREAM


# ── Live run loop ─────────────────────────────────────────────────────────────
def run(
    client: ESBulkClient,
    stop_event: threading.Event,
    scenario_data: dict | None = None,
) -> None:
    """Run the raw access-log generator loop until stop_event is set."""
    rng = random.Random()

    if scenario_data and "scenario" in scenario_data:
        scenario = scenario_data["scenario"]
        namespace = scenario_data["namespace"]
    else:
        from app.config import ACTIVE_SCENARIO
        from scenarios import get_scenario

        scenario = get_scenario(ACTIVE_SCENARIO)
        namespace = scenario.namespace

    profile = scenario.raw_log_profile
    data_stream = data_stream_for(namespace)

    if not client.configured:
        logger.warning(
            "ESBulkClient not configured (missing ELASTIC_URL/ELASTIC_API_KEY); "
            "raw access-log generator will not emit."
        )
        return

    # Pick a country to concentrate traffic on during spikes — the one with the
    # smallest baseline weight, so the demo shows an obvious geographic shift.
    country_weights = profile["country_weights"]
    spike_country = min(country_weights.keys(), key=lambda k: country_weights[k])

    total_sent = 0
    schedule = LiveSpikeSchedule(rng)

    logger.info(
        "Raw access-log generator started (namespace=%s, data_stream=%s, spike_country=%s)",
        namespace, data_stream, spike_country,
    )

    while not stop_event.is_set():
        now = time.time()
        spike_active = schedule.is_spike_active(now)

        base_batch = rng.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)
        batch_size = base_batch * SPIKE_VOLUME_MULTIPLIER if spike_active else base_batch
        docs = [
            generate_record(
                profile, namespace, rng,
                ts=now,
                spike_active=spike_active,
                spike_country=spike_country,
            )
            for _ in range(batch_size)
        ]
        sent = client.send_bulk(data_stream, docs)
        total_sent += sent
        logger.info(
            "Sent %d docs to %s (spike=%s, total=%d)",
            sent, data_stream, "ON" if spike_active else "off", total_sent,
        )

        sleep_time = rng.uniform(BATCH_INTERVAL_MIN, BATCH_INTERVAL_MAX)
        stop_event.wait(sleep_time)

    logger.info("Raw access-log generator stopped. Total: %d docs", total_sent)


# ── Standalone entry point ────────────────────────────────────────────────────
def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    client = ESBulkClient()
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

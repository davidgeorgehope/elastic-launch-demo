#!/usr/bin/env python3
"""Host Metrics Generator — sends system.* metrics for Elastic Infrastructure UI via OTLP.

Generates realistic host metrics matching the OTel hostmetricsreceiver scraper
scope names, so Elastic's Infrastructure UI recognizes them as host metrics.

Generates for 3 hosts (one per cloud: AWS, GCP, Azure) matching the active
scenario's multi-cloud architecture.

Usage (standalone):
    python3 -m log_generators.host_metrics_generator
"""

from __future__ import annotations

import logging
import os
import random
import signal
import threading
import time

from app.telemetry import OTLPClient, _format_attributes, SCHEMA_URL, _now_ns
from app.config import ACTIVE_SCENARIO

logger = logging.getLogger("host-metrics-generator")

# ── Configuration ─────────────────────────────────────────────────────────────
METRICS_INTERVAL = int(os.getenv("METRICS_INTERVAL", "10"))  # seconds between scrapes

# ── OTel hostmetricsreceiver scope names ──────────────────────────────────────
SCRAPER_BASE = "github.com/open-telemetry/opentelemetry-collector-contrib/receiver/hostmetricsreceiver/internal/scraper"
SCRAPERS = {
    "load": f"{SCRAPER_BASE}/loadscraper",
    "cpu": f"{SCRAPER_BASE}/cpuscraper",
    "memory": f"{SCRAPER_BASE}/memoryscraper",
    "disk": f"{SCRAPER_BASE}/diskscraper",
    "filesystem": f"{SCRAPER_BASE}/filesystemscraper",
    "network": f"{SCRAPER_BASE}/networkscraper",
    "processes": f"{SCRAPER_BASE}/processesscraper",
    "process": f"{SCRAPER_BASE}/processscraper",
}

# ── Per-process templates ─────────────────────────────────────────────────────
# Realistic processes running on a K8s node.  Each host gets its own set with
# unique PIDs derived from pid_base + host index offset.
PROCESS_TEMPLATES = [
    {
        "executable.name": "systemd",
        "executable.path": "/usr/lib/systemd/systemd",
        "command": "systemd",
        "command_line": "/usr/lib/systemd/systemd --switched-root --system --deserialize 22",
        "owner": "root",
        "pid_base": 1,
        "cpu_weight": 0.02,
        "mem_bytes_range": (10_000_000, 30_000_000),
        "virtual_bytes_range": (100_000_000, 200_000_000),
        "threads_range": (1, 3),
        "fd_range": (50, 150),
    },
    {
        "executable.name": "containerd",
        "executable.path": "/usr/bin/containerd",
        "command": "containerd",
        "command_line": "/usr/bin/containerd",
        "owner": "root",
        "pid_base": 512,
        "cpu_weight": 0.08,
        "mem_bytes_range": (80_000_000, 200_000_000),
        "virtual_bytes_range": (1_000_000_000, 2_000_000_000),
        "threads_range": (20, 50),
        "fd_range": (200, 500),
    },
    {
        "executable.name": "kubelet",
        "executable.path": "/usr/bin/kubelet",
        "command": "kubelet",
        "command_line": "/usr/bin/kubelet --config=/var/lib/kubelet/config.yaml --kubeconfig=/etc/kubernetes/kubelet.conf",
        "owner": "root",
        "pid_base": 1024,
        "cpu_weight": 0.12,
        "mem_bytes_range": (100_000_000, 300_000_000),
        "virtual_bytes_range": (1_500_000_000, 3_000_000_000),
        "threads_range": (15, 40),
        "fd_range": (300, 800),
    },
    {
        "executable.name": "kube-proxy",
        "executable.path": "/usr/bin/kube-proxy",
        "command": "kube-proxy",
        "command_line": "/usr/bin/kube-proxy --config=/var/lib/kube-proxy/config.conf",
        "owner": "root",
        "pid_base": 1200,
        "cpu_weight": 0.03,
        "mem_bytes_range": (20_000_000, 60_000_000),
        "virtual_bytes_range": (500_000_000, 1_000_000_000),
        "threads_range": (5, 12),
        "fd_range": (30, 100),
    },
    {
        "executable.name": "python3",
        "executable.path": "/usr/bin/python3",
        "command": "python3",
        "command_line": "python3 -m uvicorn app.main:app --host 0.0.0.0 --port 80",
        "owner": "app",
        "pid_base": 2048,
        "cpu_weight": 0.15,
        "mem_bytes_range": (120_000_000, 350_000_000),
        "virtual_bytes_range": (800_000_000, 1_500_000_000),
        "threads_range": (4, 12),
        "fd_range": (60, 200),
    },
    {
        "executable.name": "java",
        "executable.path": "/usr/bin/java",
        "command": "java",
        "command_line": "java -Xmx512m -jar /opt/service/service.jar",
        "owner": "app",
        "pid_base": 3000,
        "cpu_weight": 0.20,
        "mem_bytes_range": (200_000_000, 550_000_000),
        "virtual_bytes_range": (2_000_000_000, 4_000_000_000),
        "threads_range": (30, 80),
        "fd_range": (150, 400),
    },
    {
        "executable.name": "nginx",
        "executable.path": "/usr/sbin/nginx",
        "command": "nginx",
        "command_line": "nginx: worker process",
        "owner": "www-data",
        "pid_base": 4000,
        "cpu_weight": 0.06,
        "mem_bytes_range": (15_000_000, 80_000_000),
        "virtual_bytes_range": (300_000_000, 600_000_000),
        "threads_range": (1, 4),
        "fd_range": (100, 500),
    },
    {
        "executable.name": "otelcol",
        "executable.path": "/usr/bin/otelcol-contrib",
        "command": "otelcol-contrib",
        "command_line": "/usr/bin/otelcol-contrib --config=/etc/otelcol/config.yaml",
        "owner": "otel",
        "pid_base": 5000,
        "cpu_weight": 0.05,
        "mem_bytes_range": (60_000_000, 150_000_000),
        "virtual_bytes_range": (700_000_000, 1_200_000_000),
        "threads_range": (8, 20),
        "fd_range": (50, 200),
    },
    {
        "executable.name": "sshd",
        "executable.path": "/usr/sbin/sshd",
        "command": "sshd",
        "command_line": "sshd: /usr/sbin/sshd -D",
        "owner": "root",
        "pid_base": 800,
        "cpu_weight": 0.01,
        "mem_bytes_range": (5_000_000, 15_000_000),
        "virtual_bytes_range": (80_000_000, 150_000_000),
        "threads_range": (1, 2),
        "fd_range": (10, 30),
    },
    {
        "executable.name": "node",
        "executable.path": "/usr/bin/node",
        "command": "node",
        "command_line": "node /opt/monitoring/index.js",
        "owner": "monitor",
        "pid_base": 6000,
        "cpu_weight": 0.04,
        "mem_bytes_range": (40_000_000, 120_000_000),
        "virtual_bytes_range": (500_000_000, 1_000_000_000),
        "threads_range": (6, 14),
        "fd_range": (30, 100),
    },
]


# ── Host definitions from active scenario ─────────────────────────────────────
def _load_hosts_and_clusters():
    from scenarios import get_scenario

    scn = get_scenario(ACTIVE_SCENARIO)
    cluster_by_provider = {c["provider"]: c["name"] for c in scn.k8s_clusters}
    return scn.hosts, cluster_by_provider


HOSTS, CLUSTER_BY_PROVIDER = _load_hosts_and_clusters()


def _build_host_resource(host_cfg: dict) -> dict:
    """Build OTLP resource for a host with all required Infrastructure UI attributes."""
    attrs = {}
    for key in [
        "host.name",
        "host.id",
        "host.arch",
        "host.type",
        "host.image.id",
        "host.cpu.model.name",
        "host.cpu.vendor.id",
        "host.cpu.family",
        "host.cpu.model.id",
        "host.cpu.stepping",
        "host.cpu.cache.l2.size",
        "os.type",
        "os.description",
        "cloud.provider",
        "cloud.platform",
        "cloud.region",
        "cloud.availability_zone",
        "cloud.account.id",
        "cloud.instance.id",
    ]:
        if key in host_cfg:
            attrs[key] = host_cfg[key]

    cluster_name = CLUSTER_BY_PROVIDER.get(host_cfg.get("cloud.provider"))
    if cluster_name:
        attrs["k8s.cluster.name"] = cluster_name

    attrs["telemetry.sdk.name"] = "opentelemetry"
    attrs["telemetry.sdk.version"] = "1.24.0"
    attrs["telemetry.sdk.language"] = "python"
    # NOTE: Do NOT set data_stream.* attributes here — let the Elastic OTLP
    # endpoint auto-route based on metric names/scope. This is required for
    # the Infrastructure UI to recognize these as host metrics.

    # Format array attributes specially
    formatted = _format_attributes(attrs)

    # Add array-type attributes (host.ip, host.mac)
    for arr_key in ["host.ip", "host.mac"]:
        if arr_key in host_cfg:
            formatted.append(
                {
                    "key": arr_key,
                    "value": {
                        "arrayValue": {
                            "values": [{"stringValue": v} for v in host_cfg[arr_key]]
                        }
                    },
                }
            )

    return {
        "attributes": formatted,
        "schemaUrl": SCHEMA_URL,
    }


# ── Per-host metric state (for cumulative counters) ──────────────────────────
class HostMetricState:
    """Tracks cumulative counter values for a single host."""

    def __init__(
        self, cpu_count: int, mem_total: int, disk_total: int, rng: random.Random
    ):
        self.cpu_count = cpu_count
        self.mem_total = mem_total
        self.disk_total = disk_total
        self._rng = rng
        # Cumulative counters
        self.cpu_time = {
            f"cpu{i}": {
                "user": rng.uniform(1000, 5000),
                "system": rng.uniform(500, 2000),
                "idle": rng.uniform(10000, 50000),
                "wait": rng.uniform(10, 200),
            }
            for i in range(cpu_count)
        }
        self.disk_io_read = rng.uniform(1e9, 5e9)
        self.disk_io_write = rng.uniform(2e9, 10e9)
        self.disk_ops_read = rng.randint(100000, 500000)
        self.disk_ops_write = rng.randint(200000, 800000)
        self.net_io_recv = rng.uniform(5e9, 20e9)
        self.net_io_send = rng.uniform(2e9, 10e9)
        # Additional cumulative counters for OTel dashboard panels
        self.disk_io_time_read = rng.uniform(1000, 10000)  # seconds of IO time
        self.disk_io_time_write = rng.uniform(2000, 15000)
        self.net_packets_recv = rng.randint(5000000, 50000000)
        self.net_packets_send = rng.randint(3000000, 30000000)
        self.net_dropped_recv = rng.randint(0, 500)
        self.net_dropped_send = rng.randint(0, 300)
        self.net_errors_recv = rng.randint(0, 200)
        self.net_errors_send = rng.randint(0, 100)
        self.processes_created = rng.randint(10000, 100000)

    def tick(self):
        """Advance cumulative counters by a realistic amount."""
        rng = self._rng
        for cpu_id in self.cpu_time:
            self.cpu_time[cpu_id]["user"] += rng.uniform(0.5, 3.0)
            self.cpu_time[cpu_id]["system"] += rng.uniform(0.2, 1.5)
            self.cpu_time[cpu_id]["idle"] += rng.uniform(5.0, 9.0)
            self.cpu_time[cpu_id]["wait"] += rng.uniform(0.0, 0.5)
        self.disk_io_read += rng.randint(50000, 5000000)
        self.disk_io_write += rng.randint(100000, 10000000)
        self.disk_ops_read += rng.randint(5, 200)
        self.disk_ops_write += rng.randint(10, 500)
        self.disk_io_time_read += rng.uniform(0.01, 0.5)
        self.disk_io_time_write += rng.uniform(0.02, 1.0)
        self.net_io_recv += rng.randint(100000, 50000000)
        self.net_io_send += rng.randint(50000, 20000000)
        self.net_packets_recv += rng.randint(100, 50000)
        self.net_packets_send += rng.randint(50, 30000)
        self.net_dropped_recv += rng.randint(0, 2)
        self.net_dropped_send += rng.randint(0, 1)
        self.net_errors_recv += rng.randint(0, 1)
        self.net_errors_send += rng.randint(0, 1)
        self.processes_created += rng.randint(1, 10)


class ProcessState:
    """Tracks per-process cumulative counters."""

    def __init__(self, template: dict, host_index: int, rng: random.Random):
        self.template = template
        self.pid = template["pid_base"] + host_index * 100
        self._rng = rng
        w = template["cpu_weight"]
        # Cumulative CPU time (seconds)
        self.cpu_time_user = rng.uniform(100, 5000) * w
        self.cpu_time_system = rng.uniform(50, 2000) * w
        # Cumulative disk I/O (bytes)
        self.disk_read = rng.uniform(1e6, 1e9) * w
        self.disk_write = rng.uniform(1e6, 1e9) * w
        # Cumulative context switches
        self.ctx_voluntary = rng.randint(10000, 500000)
        self.ctx_involuntary = rng.randint(1000, 50000)

    def tick(self):
        rng = self._rng
        w = self.template["cpu_weight"]
        self.cpu_time_user += rng.uniform(0.05, 2.0) * w
        self.cpu_time_system += rng.uniform(0.02, 0.8) * w
        self.disk_read += rng.randint(0, 500000) * w
        self.disk_write += rng.randint(0, 1000000) * w
        self.ctx_voluntary += rng.randint(1, 100)
        self.ctx_involuntary += rng.randint(0, 20)


def _build_sum_metric(
    name: str, value, unit: str, attributes: dict | None = None, is_int: bool = False
) -> dict:
    """Build a cumulative sum metric."""
    now = _now_ns()
    dp: dict = {
        "startTimeUnixNano": str(int(now) - 60_000_000_000),
        "timeUnixNano": now,
    }
    if is_int:
        dp["asInt"] = str(int(value))
    else:
        dp["asDouble"] = float(value)

    if attributes:
        dp["attributes"] = _format_attributes(attributes)

    return {
        "name": name,
        "unit": unit,
        "sum": {
            "dataPoints": [dp],
            "aggregationTemporality": 2,  # cumulative
            "isMonotonic": True,
        },
    }


def _build_gauge_metric(
    name: str, value, unit: str, attributes: dict | None = None, is_int: bool = False
) -> dict:
    """Build a gauge metric."""
    now = _now_ns()
    dp: dict = {"timeUnixNano": now}
    if is_int:
        dp["asInt"] = str(int(value))
    else:
        dp["asDouble"] = float(value)

    if attributes:
        dp["attributes"] = _format_attributes(attributes)

    return {
        "name": name,
        "unit": unit,
        "gauge": {"dataPoints": [dp]},
    }


def _generate_host_metrics(
    state: HostMetricState,
    rng: random.Random,
    cpu_spike_pct: float = 0,
    memory_spike_pct: float = 0,
) -> dict[str, list]:
    """Generate all host metrics grouped by scraper scope name.

    Returns dict mapping scope_name -> list of metric dicts.
    cpu_spike_pct/memory_spike_pct: 0-100 target utilization when spiked.
    """
    state.tick()
    metrics_by_scope: dict[str, list] = {}

    # ── Load metrics ──
    if cpu_spike_pct > 0:
        load_1m = rng.uniform(cpu_spike_pct / 20, cpu_spike_pct / 12)
    else:
        load_1m = rng.uniform(0.5, 4.0)
    load_5m = load_1m * rng.uniform(0.7, 1.1)
    load_15m = load_5m * rng.uniform(0.8, 1.05)
    metrics_by_scope[SCRAPERS["load"]] = [
        _build_gauge_metric("system.cpu.load_average.1m", load_1m, "{thread}"),
        _build_gauge_metric("system.cpu.load_average.5m", load_5m, "{thread}"),
        _build_gauge_metric("system.cpu.load_average.15m", load_15m, "{thread}"),
    ]

    # ── CPU metrics ──
    cpu_metrics = [
        _build_gauge_metric(
            "system.cpu.logical.count", state.cpu_count, "{cpu}", is_int=True
        ),
    ]
    for cpu_id, times in state.cpu_time.items():
        total = sum(times.values())
        for state_name, val in times.items():
            cpu_metrics.append(
                _build_sum_metric(
                    "system.cpu.time",
                    val,
                    "s",
                    attributes={"cpu": cpu_id, "state": state_name},
                )
            )
            # Bias utilization toward spike target when active
            if cpu_spike_pct > 0 and total > 0:
                target = cpu_spike_pct / 100.0
                if state_name == "user":
                    util = target * rng.uniform(0.55, 0.65)
                elif state_name == "system":
                    util = target * rng.uniform(0.25, 0.35)
                elif state_name == "idle":
                    util = max(0.01, 1.0 - target) * rng.uniform(0.8, 1.2)
                else:  # wait
                    util = target * rng.uniform(0.02, 0.08)
            else:
                util = val / total if total > 0 else 0
            cpu_metrics.append(
                _build_gauge_metric(
                    "system.cpu.utilization",
                    util,
                    "1",
                    attributes={"cpu": cpu_id, "state": state_name},
                )
            )
    metrics_by_scope[SCRAPERS["cpu"]] = cpu_metrics

    # ── Memory metrics ──
    if memory_spike_pct > 0:
        mem_used_pct = (memory_spike_pct / 100.0) * rng.uniform(0.95, 1.05)
        mem_used_pct = min(mem_used_pct, 0.97)
        mem_cached_pct = rng.uniform(0.01, 0.03)
        mem_buffered_pct = rng.uniform(0.005, 0.01)
    else:
        mem_used_pct = rng.uniform(0.35, 0.85)
        mem_cached_pct = rng.uniform(0.05, 0.20)
        mem_buffered_pct = rng.uniform(0.01, 0.05)
    mem_free_pct = 1.0 - mem_used_pct - mem_cached_pct - mem_buffered_pct
    if mem_free_pct < 0:
        mem_free_pct = 0.05
        mem_used_pct = 1.0 - mem_free_pct - mem_cached_pct - mem_buffered_pct

    mem_total = state.mem_total
    mem_states = {
        "used": mem_used_pct,
        "free": mem_free_pct,
        "cached": mem_cached_pct,
        "buffered": mem_buffered_pct,
    }
    mem_metrics = []
    for mem_state, pct in mem_states.items():
        mem_metrics.append(
            _build_gauge_metric(
                "system.memory.usage",
                int(mem_total * pct),
                "By",
                attributes={"state": mem_state},
                is_int=True,
            )
        )
        mem_metrics.append(
            _build_gauge_metric(
                "system.memory.utilization",
                pct,
                "1",
                attributes={"state": mem_state},
            )
        )
    # Add slab states for utilization
    for slab_state in ["slab_reclaimable", "slab_unreclaimable"]:
        slab_pct = rng.uniform(0.01, 0.03)
        mem_metrics.append(
            _build_gauge_metric(
                "system.memory.utilization",
                slab_pct,
                "1",
                attributes={"state": slab_state},
            )
        )
    metrics_by_scope[SCRAPERS["memory"]] = mem_metrics

    # ── Disk metrics ──
    disk_metrics = []
    for device in ["sda", "sdb"]:
        disk_metrics.append(
            _build_sum_metric(
                "system.disk.io",
                state.disk_io_read,
                "By",
                attributes={"device": device, "direction": "read"},
            )
        )
        disk_metrics.append(
            _build_sum_metric(
                "system.disk.io",
                state.disk_io_write,
                "By",
                attributes={"device": device, "direction": "write"},
            )
        )
        disk_metrics.append(
            _build_sum_metric(
                "system.disk.operations",
                state.disk_ops_read,
                "{operation}",
                attributes={"device": device, "direction": "read"},
                is_int=True,
            )
        )
        disk_metrics.append(
            _build_sum_metric(
                "system.disk.operations",
                state.disk_ops_write,
                "{operation}",
                attributes={"device": device, "direction": "write"},
                is_int=True,
            )
        )
        # disk.io_time — cumulative seconds spent on IO (OTel dashboard panel)
        disk_metrics.append(
            _build_sum_metric(
                "system.disk.io_time",
                state.disk_io_time_read,
                "s",
                attributes={"device": device, "direction": "read"},
            )
        )
        disk_metrics.append(
            _build_sum_metric(
                "system.disk.io_time",
                state.disk_io_time_write,
                "s",
                attributes={"device": device, "direction": "write"},
            )
        )
    metrics_by_scope[SCRAPERS["disk"]] = disk_metrics

    # ── Filesystem metrics ──
    fs_metrics = []
    disk_total = state.disk_total
    disk_used_pct = rng.uniform(0.20, 0.75)
    reserved_pct = 0.05  # 5% reserved for root, matching real Linux ext4/xfs behavior
    for device, mountpoint, fs_type in [
        ("/dev/sda1", "/", "ext4"),
        ("/dev/sdb1", "/data", "xfs"),
    ]:
        reserved = int(disk_total * reserved_pct)
        used = int(disk_total * disk_used_pct)
        free = disk_total - used - reserved
        fs_metrics.append(
            _build_gauge_metric(
                "system.filesystem.usage",
                used,
                "By",
                attributes={
                    "device": device,
                    "mountpoint": mountpoint,
                    "type": fs_type,
                    "state": "used",
                },
                is_int=True,
            )
        )
        fs_metrics.append(
            _build_gauge_metric(
                "system.filesystem.usage",
                free,
                "By",
                attributes={
                    "device": device,
                    "mountpoint": mountpoint,
                    "type": fs_type,
                    "state": "free",
                },
                is_int=True,
            )
        )
        fs_metrics.append(
            _build_gauge_metric(
                "system.filesystem.usage",
                reserved,
                "By",
                attributes={
                    "device": device,
                    "mountpoint": mountpoint,
                    "type": fs_type,
                    "state": "reserved",
                },
                is_int=True,
            )
        )
        fs_metrics.append(
            _build_gauge_metric(
                "system.filesystem.utilization",
                disk_used_pct,
                "1",
                attributes={
                    "device": device,
                    "mountpoint": mountpoint,
                    "type": fs_type,
                },
            )
        )
    metrics_by_scope[SCRAPERS["filesystem"]] = fs_metrics

    # ── Network metrics ──
    net_metrics = []
    for device in ["eth0", "eth1"]:
        net_metrics.append(
            _build_sum_metric(
                "system.network.io",
                state.net_io_recv,
                "By",
                attributes={"device": device, "direction": "receive"},
            )
        )
        net_metrics.append(
            _build_sum_metric(
                "system.network.io",
                state.net_io_send,
                "By",
                attributes={"device": device, "direction": "transmit"},
            )
        )
        # network.packets — cumulative packet counts (OTel dashboard panel)
        net_metrics.append(
            _build_sum_metric(
                "system.network.packets",
                state.net_packets_recv,
                "{packet}",
                attributes={"device": device, "direction": "receive"},
                is_int=True,
            )
        )
        net_metrics.append(
            _build_sum_metric(
                "system.network.packets",
                state.net_packets_send,
                "{packet}",
                attributes={"device": device, "direction": "transmit"},
                is_int=True,
            )
        )
        # network.dropped — cumulative dropped packet counts (OTel dashboard panel)
        net_metrics.append(
            _build_sum_metric(
                "system.network.dropped",
                state.net_dropped_recv,
                "{packet}",
                attributes={"device": device, "direction": "receive"},
                is_int=True,
            )
        )
        net_metrics.append(
            _build_sum_metric(
                "system.network.dropped",
                state.net_dropped_send,
                "{packet}",
                attributes={"device": device, "direction": "transmit"},
                is_int=True,
            )
        )
        # network.errors — cumulative error counts (OTel dashboard panel)
        net_metrics.append(
            _build_sum_metric(
                "system.network.errors",
                state.net_errors_recv,
                "{error}",
                attributes={"device": device, "direction": "receive"},
                is_int=True,
            )
        )
        net_metrics.append(
            _build_sum_metric(
                "system.network.errors",
                state.net_errors_send,
                "{error}",
                attributes={"device": device, "direction": "transmit"},
                is_int=True,
            )
        )
    # network.connections — TCP connection count by state (OTel dashboard panel)
    tcp_states = {
        "ESTABLISHED": rng.randint(40, 200),
        "TIME_WAIT": rng.randint(5, 50),
        "CLOSE_WAIT": rng.randint(0, 10),
        "LISTEN": rng.randint(10, 30),
        "SYN_SENT": rng.randint(0, 3),
        "SYN_RECV": rng.randint(0, 3),
        "FIN_WAIT1": rng.randint(0, 5),
        "FIN_WAIT2": rng.randint(0, 5),
    }
    for tcp_state, count in tcp_states.items():
        net_metrics.append(
            _build_gauge_metric(
                "system.network.connections",
                count,
                "{connection}",
                attributes={"protocol": "tcp", "state": tcp_state},
                is_int=True,
            )
        )
    metrics_by_scope[SCRAPERS["network"]] = net_metrics

    # ── Process metrics ──
    running_count = rng.randint(1, 8)
    sleeping = rng.randint(50, 200)
    metrics_by_scope[SCRAPERS["processes"]] = [
        _build_gauge_metric(
            "system.processes.count",
            running_count,
            "{process}",
            attributes={"status": "running"},
            is_int=True,
        ),
        _build_gauge_metric(
            "system.processes.count",
            sleeping,
            "{process}",
            attributes={"status": "sleeping"},
            is_int=True,
        ),
        # processes.created — cumulative process creation count (OTel dashboard panel)
        _build_sum_metric(
            "system.processes.created",
            state.processes_created,
            "{process}",
            is_int=True,
        ),
    ]

    return metrics_by_scope


def _send_metrics_with_scopes(
    client: OTLPClient, resource: dict, metrics_by_scope: dict[str, list]
) -> int:
    """Send metrics grouped by scope name. Returns total metric count sent."""
    total = 0
    for scope_name, metrics in metrics_by_scope.items():
        if not metrics:
            continue
        # Build the payload with the specific scope name
        payload = {
            "resourceMetrics": [
                {
                    "resource": resource,
                    "scopeMetrics": [
                        {
                            "scope": {"name": scope_name, "version": "0.115.0"},
                            "metrics": metrics,
                        }
                    ],
                }
            ]
        }
        client._send(f"{client.endpoint}/v1/metrics", payload, "metrics")
        total += len(metrics)
    return total


# ── Per-process metrics ──────────────────────────────────────────────────────


def _build_process_resource(host_cfg: dict, proc_state: ProcessState) -> dict:
    """Build OTLP resource for an individual process (host attrs + process attrs)."""
    t = proc_state.template
    attrs = {}
    # Carry over host identification attributes
    for key in [
        "host.name",
        "host.id",
        "host.arch",
        "os.type",
        "os.description",
        "cloud.provider",
        "cloud.region",
    ]:
        if key in host_cfg:
            attrs[key] = host_cfg[key]

    # Process-specific resource attributes
    attrs["process.pid"] = proc_state.pid
    attrs["process.executable.name"] = t["executable.name"]
    attrs["process.executable.path"] = t["executable.path"]
    attrs["process.command"] = t["command"]
    attrs["process.command_line"] = t["command_line"]
    attrs["process.owner"] = t["owner"]
    attrs["process.parent_pid"] = 1 if proc_state.pid != 1 else 0

    attrs["telemetry.sdk.name"] = "opentelemetry"
    attrs["telemetry.sdk.version"] = "1.24.0"
    attrs["telemetry.sdk.language"] = "python"

    return {
        "attributes": _format_attributes(attrs),
        "schemaUrl": SCHEMA_URL,
    }


def _generate_process_metrics(
    proc_state: ProcessState, rng: random.Random
) -> list[dict]:
    """Generate OTel process.* metrics for a single process."""
    proc_state.tick()
    t = proc_state.template
    metrics = []

    # process.cpu.time — cumulative seconds by state (user, system)
    metrics.append(
        _build_sum_metric(
            "process.cpu.time",
            proc_state.cpu_time_user,
            "s",
            attributes={"state": "user"},
        )
    )
    metrics.append(
        _build_sum_metric(
            "process.cpu.time",
            proc_state.cpu_time_system,
            "s",
            attributes={"state": "system"},
        )
    )

    # process.cpu.utilization — instantaneous ratio (0..1)
    cpu_util = t["cpu_weight"] * rng.uniform(0.3, 1.5)
    cpu_util = min(cpu_util, 1.0)
    metrics.append(_build_gauge_metric("process.cpu.utilization", cpu_util, "1"))

    # process.memory.usage — resident memory (bytes)
    lo, hi = t["mem_bytes_range"]
    metrics.append(
        _build_gauge_metric(
            "process.memory.usage",
            rng.randint(lo, hi),
            "By",
            is_int=True,
        )
    )

    # process.memory.virtual — virtual memory size (bytes)
    lo, hi = t["virtual_bytes_range"]
    metrics.append(
        _build_gauge_metric(
            "process.memory.virtual",
            rng.randint(lo, hi),
            "By",
            is_int=True,
        )
    )

    # process.threads — thread count
    lo, hi = t["threads_range"]
    metrics.append(
        _build_gauge_metric(
            "process.threads",
            rng.randint(lo, hi),
            "{thread}",
            is_int=True,
        )
    )

    # process.open_file_descriptors — open FD count
    lo, hi = t["fd_range"]
    metrics.append(
        _build_gauge_metric(
            "process.open_file_descriptors",
            rng.randint(lo, hi),
            "{count}",
            is_int=True,
        )
    )

    # process.disk.io — cumulative bytes by direction
    metrics.append(
        _build_sum_metric(
            "process.disk.io",
            proc_state.disk_read,
            "By",
            attributes={"direction": "read"},
        )
    )
    metrics.append(
        _build_sum_metric(
            "process.disk.io",
            proc_state.disk_write,
            "By",
            attributes={"direction": "write"},
        )
    )

    # process.context_switches — cumulative by type
    metrics.append(
        _build_sum_metric(
            "process.context_switches",
            proc_state.ctx_voluntary,
            "{count}",
            attributes={"type": "voluntary"},
            is_int=True,
        )
    )
    metrics.append(
        _build_sum_metric(
            "process.context_switches",
            proc_state.ctx_involuntary,
            "{count}",
            attributes={"type": "involuntary"},
            is_int=True,
        )
    )

    return metrics


def _send_process_metrics(
    client: OTLPClient,
    host_cfg: dict,
    proc_states: list[ProcessState],
    rng: random.Random,
) -> int:
    """Generate and send per-process metrics for one host. Returns metric count."""
    scope_name = SCRAPERS["process"]
    resource_metrics = []
    total = 0

    for ps in proc_states:
        metrics = _generate_process_metrics(ps, rng)
        resource_metrics.append(
            {
                "resource": _build_process_resource(host_cfg, ps),
                "scopeMetrics": [
                    {
                        "scope": {"name": scope_name, "version": "0.115.0"},
                        "metrics": metrics,
                    }
                ],
            }
        )
        total += len(metrics)

    if resource_metrics:
        payload = {"resourceMetrics": resource_metrics}
        client._send(f"{client.endpoint}/v1/metrics", payload, "metrics")

    return total


# ── Run loop (used by ServiceManager and standalone) ──────────────────────────
def run(
    client: OTLPClient,
    stop_event: threading.Event,
    scenario_data: dict | None = None,
    chaos_controller=None,
) -> None:
    """Run host metrics generator loop until stop_event is set."""
    rng = random.Random()

    hosts = scenario_data["hosts"] if scenario_data else HOSTS
    # Build cloud_provider -> host_name mapping for targeted spikes
    _host_cloud_map: dict[str, str] = {}
    for h in hosts:
        _host_cloud_map[h["host.name"]] = h.get("cloud.provider", "")
    # Build service -> cloud_provider mapping from scenario_data
    _service_cloud: dict[str, str] = {}
    _channel_registry = {}
    if scenario_data:
        for svc_name, svc_cfg in scenario_data.get("services", {}).items():
            _service_cloud[svc_name] = svc_cfg.get("cloud_provider", "")
        _channel_registry = scenario_data.get("channel_registry", {})

    # Build resources and metric state for each host
    host_resources = []
    host_states = []
    host_proc_states: list[list[ProcessState]] = []
    for host_idx, host_cfg in enumerate(hosts):
        resource = _build_host_resource(host_cfg)
        state = HostMetricState(
            cpu_count=host_cfg["cpu_count"],
            mem_total=host_cfg["memory_total_bytes"],
            disk_total=host_cfg["disk_total_bytes"],
            rng=rng,
        )
        host_resources.append(resource)
        host_states.append(state)
        # Per-process states for this host
        proc_states = [ProcessState(t, host_idx, rng) for t in PROCESS_TEMPLATES]
        host_proc_states.append(proc_states)

    total_metrics = 0
    scrape_count = 0
    proc_count = len(PROCESS_TEMPLATES) * len(hosts)

    logger.info(
        "Host metrics generator started (interval=%ds, hosts=%d, processes=%d)",
        METRICS_INTERVAL,
        len(hosts),
        proc_count,
    )

    while not stop_event.is_set():
        # Determine per-host spike targets from chaos_controller
        spikes = chaos_controller.get_infra_spikes() if chaos_controller else {}
        cpu_pct = spikes.get("cpu_pct", 0)
        mem_pct = spikes.get("memory_pct", 0)

        # Build set of cloud providers with active faults (for targeting)
        spiked_clouds: set[str] = set()
        has_active_faults = False
        if chaos_controller and (cpu_pct > 0 or mem_pct > 0):
            active_channels = chaos_controller.get_active_channels()
            if active_channels:
                has_active_faults = True
                for ch_id in active_channels:
                    ch = _channel_registry.get(ch_id, {})
                    for svc in ch.get("affected_services", []):
                        cloud = _service_cloud.get(svc)
                        if cloud:
                            spiked_clouds.add(cloud)

        batch_metrics = 0
        for host_cfg, resource, state, proc_states in zip(
            hosts,
            host_resources,
            host_states,
            host_proc_states,
        ):
            host_name = host_cfg["host.name"]
            host_cloud = _host_cloud_map.get(host_name, "")
            # Spike this host if: sliders active AND (no faults → spike all, or this host's cloud is affected)
            if (cpu_pct > 0 or mem_pct > 0) and (
                not has_active_faults or host_cloud in spiked_clouds
            ):
                host_cpu = cpu_pct
                host_mem = mem_pct
            else:
                host_cpu = 0
                host_mem = 0

            metrics_by_scope = _generate_host_metrics(
                state, rng, cpu_spike_pct=host_cpu, memory_spike_pct=host_mem
            )
            sent = _send_metrics_with_scopes(client, resource, metrics_by_scope)
            batch_metrics += sent
            # Per-process metrics
            sent = _send_process_metrics(client, host_cfg, proc_states, rng)
            batch_metrics += sent

        scrape_count += 1
        total_metrics += batch_metrics
        logger.info(
            "Scrape %d: sent %d metrics across %d hosts + %d processes (total=%d)",
            scrape_count,
            batch_metrics,
            len(hosts),
            proc_count,
            total_metrics,
        )

        stop_event.wait(METRICS_INTERVAL)

    logger.info(
        "Host metrics generator stopped. Total: %d metrics in %d scrapes",
        total_metrics,
        scrape_count,
    )


# ── Standalone entry point ────────────────────────────────────────────────────
def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

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

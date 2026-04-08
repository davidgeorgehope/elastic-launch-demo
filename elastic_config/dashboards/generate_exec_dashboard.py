#!/usr/bin/env python3
"""
Generate an Executive Dashboard NDJSON file compatible with Kibana 9.4.

Can be used as:
  - Importable function: generate_dashboard_ndjson(scenario) -> str
  - Standalone script: python3 generate_exec_dashboard.py  (defaults to space scenario)

Produces by-value Lens panels using the formBased datasource format that matches
the built-in [OTel] dashboards shipped with Kibana 9.4, including all required
fields: ignoreGlobalFilters, incompleteColumns, sampling, adHocDataViews,
internalReferences, legend, valueLabels.

Layout (48-unit grid): Cloud -> RED -> USE -> APM/Infra -> Detail
  Section 1 — Cloud Provider Overview (y=0..14):
    y=0  h=2:  Cloud group labels (DASHBOARD_MARKDOWN)
    y=2  h=6:  9 Service Health tiles (3 per cloud column)
    y=8  h=6:  K8s tiles per cloud (Node CPU + Node Memory)
  Section 2 — RED Metrics (y=14..34):
    y=14 h=2:  Section header
    y=16 h=6:  KPI tiles (P99/P50 latency, error rate, throughput)
    y=22 h=12: Time series (P99 latency, error rate by service)
  Section 3 — USE Metrics (y=34..54):
    y=34 h=2:  Section header
    y=36 h=6:  KPI tiles (CPU load, disk util, container restarts, net errors)
    y=42 h=12: Time series (CPU load, disk util over time)
  Section 4 — APM & Infrastructure (y=54..86):
    y=54 h=2:  Section header
    y=56 h=6:  KPI tiles (APM throughput, APM errors, NGINX, VPC)
    y=62 h=12: Time series (APM errors by service, log volume)
    y=74 h=12: Time series (NGINX rate, VPC flow)
  Section 5 — Detail (y=86..112):
    y=86  h=2:  Section header
    y=88  h=12: Errors by Service bar, Service Health Heatmap
    y=100 h=12: Node CPU Over Time by cluster, Pod Memory by service
  Section 6 — Significant Event Logs (y=112..128):
    y=112 h=2:  Section header
    y=114 h=14: Significant Event Logs datatable (trace.id, span.id, service)
"""

import json
import os
import uuid

DATA_VIEW_ID_LOGS = "logs*"
DATA_VIEW_ID_TRACES = "traces-*"
DATA_VIEW_ID_METRICS = "metrics-*"


def uid():
    """Generate a random UUID for layer/column IDs."""
    return str(uuid.uuid4())


# ── Reference helpers ────────────────────────────────────────────────

def make_ref(data_view_id, layer_id):
    """Create a data view reference for a given layer."""
    return {
        "id": data_view_id,
        "name": f"indexpattern-datasource-layer-{layer_id}",
        "type": "index-pattern",
    }


# ── Layer / state / panel builders ─────────────────────────────────────────

def make_layer(layer_id, column_order, columns, index_pattern_id=None):
    """Build a formBased layer with all Kibana 9.4 required fields."""
    layer = {
        "columnOrder": column_order,
        "columns": columns,
        "ignoreGlobalFilters": False,
        "incompleteColumns": {},
        "sampling": 1,
    }
    if index_pattern_id:
        layer["indexPatternId"] = index_pattern_id
    return {layer_id: layer}


def make_state(layers_dict, visualization, query="", filters=None):
    """Build the full state object for a Lens panel."""
    return {
        "adHocDataViews": {},
        "datasourceStates": {
            "formBased": {
                "layers": layers_dict,
            },
            "indexpattern": {
                "layers": {},
            },
            "textBased": {
                "layers": {},
            },
        },
        "filters": filters or [],
        "internalReferences": [],
        "query": {"language": "kuery", "query": query},
        "visualization": visualization,
    }


def make_panel(panel_id, grid, title, vis_type, state, references):
    """Build a complete panel object for the dashboard."""
    return {
        "embeddableConfig": {
            "attributes": {
                "references": references,
                "state": state,
                "title": title,
                "type": "lens",
                "visualizationType": vis_type,
                "version": 2,
            },
            "enhancements": {"dynamicActions": {"events": []}},
            "hidePanelTitles": False,
            "syncColors": False,
            "syncCursor": True,
            "syncTooltips": False,
        },
        "gridData": grid,
        "panelIndex": panel_id,
        "type": "lens",
    }


# ── Column helpers ───────────────────────────────────────────────────

def col_count(label="Count", kql_filter=None):
    """Create a count column."""
    col = {
        "customLabel": True,
        "dataType": "number",
        "isBucketed": False,
        "label": label,
        "operationType": "count",
        "params": {"emptyAsNull": True},
        "scale": "ratio",
        "sourceField": "___records___",
    }
    if kql_filter:
        col["filter"] = {"language": "kuery", "query": kql_filter}
    return col


def col_unique_count(source_field, label="Unique"):
    """Create a unique_count column."""
    return {
        "customLabel": True,
        "dataType": "number",
        "isBucketed": False,
        "label": label,
        "operationType": "unique_count",
        "params": {"emptyAsNull": True},
        "scale": "ratio",
        "sourceField": source_field,
    }


def col_date_histogram(interval="30s", label="@timestamp"):
    """Create a date_histogram column."""
    return {
        "customLabel": True,
        "dataType": "date",
        "isBucketed": True,
        "label": label,
        "operationType": "date_histogram",
        "params": {"interval": interval},
        "scale": "interval",
        "sourceField": "@timestamp",
    }


def col_terms(source_field, label, size=10, order_col_id=None):
    """Create a terms column."""
    params = {
        "size": size,
        "orderDirection": "desc",
        "orderBy": {"columnId": order_col_id, "type": "column"} if order_col_id else {"type": "alphabetical"},
        "missingBucket": False,
        "otherBucket": False,
    }
    return {
        "customLabel": True,
        "dataType": "string",
        "isBucketed": True,
        "label": label,
        "operationType": "terms",
        "params": params,
        "scale": "ordinal",
        "sourceField": source_field,
    }


def col_average(source_field, label="Average"):
    """Create an average column for gauge metrics."""
    return {
        "customLabel": True,
        "dataType": "number",
        "isBucketed": False,
        "label": label,
        "operationType": "average",
        "params": {"emptyAsNull": True},
        "scale": "ratio",
        "sourceField": source_field,
    }


def col_last_value(source_field, label="Last Value"):
    """Create a last_value column for KPI tiles."""
    return {
        "customLabel": True,
        "dataType": "number",
        "isBucketed": False,
        "label": label,
        "operationType": "last_value",
        "params": {"sortField": "@timestamp"},
        "scale": "ratio",
        "sourceField": source_field,
    }


def col_percentile(source_field, percentile, label):
    """Create a percentile column."""
    return {
        "customLabel": True,
        "dataType": "number",
        "isBucketed": False,
        "label": label,
        "operationType": "percentile",
        "params": {"percentile": percentile},
        "scale": "ratio",
        "sourceField": source_field,
    }


def col_max(source_field, label="Max"):
    """Create a max column."""
    return {
        "customLabel": True,
        "dataType": "number",
        "isBucketed": False,
        "label": label,
        "operationType": "max",
        "params": {"emptyAsNull": True},
        "scale": "ratio",
        "sourceField": source_field,
    }


def col_formula(formula, label):
    """Create a formula column for computed metrics like error rate %."""
    return {
        "customLabel": True,
        "dataType": "number",
        "isBucketed": False,
        "label": label,
        "operationType": "formula",
        "params": {
            "formula": formula,
            "isFormulaBroken": False,
        },
        "scale": "ratio",
    }


def make_metric_palette(thresholds):
    """Create a custom color palette for lnsMetric threshold-based coloring.

    Args:
        thresholds: list of (color, upper_bound) tuples defining ranges.
            The last upper_bound should be a large sentinel value.
            Example: [("#54B399", 5), ("#D6BF57", 15), ("#E7664C", 9999)]
            Means: green for 0-5, yellow for 5-15, red for 15+
    """
    stops = [{"color": color, "stop": stop} for color, stop in thresholds]
    color_stops = [{"color": thresholds[0][0], "stop": 0}]
    for i in range(1, len(thresholds)):
        color_stops.append({"color": thresholds[i][0], "stop": thresholds[i - 1][1]})

    return {
        "name": "custom",
        "type": "palette",
        "params": {
            "steps": len(thresholds),
            "name": "custom",
            "reverse": False,
            "rangeType": "number",
            "rangeMin": 0,
            "rangeMax": None,
            "progression": "fixed",
            "stops": stops,
            "colorStops": color_stops,
            "continuity": "above",
            "maxSteps": 5,
        },
    }


# ── Threshold palettes for metric tiles ───────────────────────────────────────
# Green → Yellow → Red as values climb
PALETTE_ERRORS = make_metric_palette([
    ("#54B399", 2),     # green: 0-2 errors
    ("#D6BF57", 5),     # yellow: 2-5 errors
    ("#E7664C", 9999),  # red: 5+ errors
])

PALETTE_ERROR_RATE = make_metric_palette([
    ("#54B399", 0.12),  # green: 0-12%
    ("#D6BF57", 0.20),  # yellow: 12-20%
    ("#E7664C", 1.0),   # red: 20%+
])

PALETTE_THROUGHPUT = make_metric_palette([
    ("#54B399", 2000),  # green: normal
    ("#D6BF57", 3500),  # yellow: elevated
    ("#E7664C", 99999), # red: spike
])

PALETTE_LATENCY_P99 = make_metric_palette([
    ("#54B399", 500_000_000),     # green: < 500ms
    ("#D6BF57", 2_000_000_000),   # yellow: 500ms-2s
    ("#E7664C", 999_000_000_000), # red: > 2s
])

PALETTE_LATENCY_P50 = make_metric_palette([
    ("#54B399", 200_000_000),     # green: < 200ms
    ("#D6BF57", 800_000_000),     # yellow: 200ms-800ms
    ("#E7664C", 999_000_000_000), # red: > 800ms
])

PALETTE_CPU = make_metric_palette([
    ("#54B399", 0.40),  # green: < 40%
    ("#D6BF57", 0.60),  # yellow: 40-60%
    ("#E7664C", 1.0),   # red: > 60%
])


# ═══════════════════════════════════════════════════════════════════════════════
# Main generation function
# ═══════════════════════════════════════════════════════════════════════════════

def generate_dashboard_ndjson(scenario) -> str:
    """Generate exec dashboard NDJSON for a given scenario.

    Args:
        scenario: A BaseScenario instance (uses scenario_name, namespace,
                  dashboard_cloud_groups properties).

    Returns:
        NDJSON string ready for Kibana import.
    """
    scenario_name = scenario.scenario_name
    namespace = scenario.namespace
    cloud_groups = scenario.dashboard_cloud_groups
    dashboard_id = f"{namespace}-exec-dashboard"
    error_types = [
        ch["error_type"]
        for ch in scenario.channel_registry.values()
    ]

    return _build_dashboard_ndjson(scenario_name, namespace, cloud_groups, dashboard_id, error_types)


def _build_dashboard_ndjson(
    scenario_name: str,
    namespace: str,
    cloud_groups: list[dict],
    dashboard_id: str,
    error_types: "list[str] | None" = None,
) -> str:
    """Build the full dashboard NDJSON from parameters."""
    TILE_WIDTH = 5

    panels = []

    # ── Section 1: Cloud Provider Overview ───────────────────────────────────

    # Row 0 (y=0, h=2): Cloud Provider Labels (DASHBOARD_MARKDOWN)
    for idx, group in enumerate(cloud_groups):
        pid = f"p_label_{idx}"
        panels.append({
            "type": "DASHBOARD_MARKDOWN",
            "embeddableConfig": {
                "content": group["label"],
            },
            "panelIndex": pid,
            "gridData": {"h": 2, "i": pid, "w": group["col_width"], "x": group["x_start"], "y": 0},
        })

    # Vertical separators between cloud columns
    for sep_x in [15, 32]:
        pid = f"p_sep_{sep_x}"
        panels.append({
            "type": "DASHBOARD_MARKDOWN",
            "embeddableConfig": {
                "content": "",
            },
            "panelIndex": pid,
            "gridData": {"h": 14, "i": pid, "w": 1, "x": sep_x, "y": 0},
        })

    # Row 1 (y=2, h=6): 9 Service Health Tiles
    tile_idx = 0
    for group in cloud_groups:
        for svc_offset, svc_name in enumerate(group["services"]):
            tile_idx += 1
            pid = f"p_svc_{tile_idx}"
            lid = uid()
            cid = uid()
            kql = f'resource.attributes.service.name: "{svc_name}" AND status.code: Error'
            columns = {cid: col_count(label="Errors", kql_filter=kql)}
            layer = make_layer(lid, [cid], columns, DATA_VIEW_ID_TRACES)
            state = make_state(layer, {
                "layerId": lid,
                "layerType": "data",
                "metricAccessor": cid,
                "palette": PALETTE_ERRORS,
                "subtitle": svc_name,
            })
            x = group["x_start"] + svc_offset * TILE_WIDTH
            w = TILE_WIDTH if svc_offset < 2 else (group["col_width"] - 2 * TILE_WIDTH)
            panels.append(make_panel(
                pid,
                {"h": 6, "i": pid, "w": w, "x": x, "y": 2},
                svc_name,
                "lnsMetric",
                state,
                [make_ref(DATA_VIEW_ID_TRACES, lid)],
            ))

    # Row 2 (y=8, h=6): K8s Tiles per Cloud Region
    k8s_tile_idx = 0
    for group in cloud_groups:
        x_base = group["x_start"]
        col_w = group["col_width"]
        left_w = col_w // 2
        right_w = col_w - left_w

        # Node CPU tile (left half of column) — scoped to this cluster
        k8s_tile_idx += 1
        pid = f"p_k8s_{k8s_tile_idx}"
        lid = uid()
        cid = uid()
        columns = {cid: col_average("metrics.k8s.node.cpu.utilization", label="CPU %")}
        layer = make_layer(lid, [cid], columns, DATA_VIEW_ID_METRICS)
        cluster_name = group.get("cluster", "")
        cpu_query = f'resource.attributes.k8s.cluster.name: "{cluster_name}"' if cluster_name else ""
        state = make_state(layer, {
            "layerId": lid,
            "layerType": "data",
            "metricAccessor": cid,
            "palette": PALETTE_CPU,
            "subtitle": "Node CPU",
        }, query=cpu_query)
        panels.append(make_panel(pid,
            {"h": 6, "i": pid, "w": left_w, "x": x_base, "y": 8},
            "Node CPU", "lnsMetric", state, [make_ref(DATA_VIEW_ID_METRICS, lid)]))

        # Node Memory tile (right half of column) — scoped to this cluster
        k8s_tile_idx += 1
        pid = f"p_k8s_{k8s_tile_idx}"
        lid = uid()
        cid = uid()
        columns = {cid: col_average("metrics.k8s.node.memory.utilization", label="Mem %")}
        layer = make_layer(lid, [cid], columns, DATA_VIEW_ID_METRICS)
        mem_query = f'resource.attributes.k8s.cluster.name: "{cluster_name}"' if cluster_name else ""
        state = make_state(layer, {
            "layerId": lid,
            "layerType": "data",
            "metricAccessor": cid,
            "color": "#6092C0",
            "subtitle": "Node Memory",
        }, query=mem_query)
        panels.append(make_panel(pid,
            {"h": 6, "i": pid, "w": right_w, "x": x_base + left_w, "y": 8},
            "Node Memory", "lnsMetric", state, [make_ref(DATA_VIEW_ID_METRICS, lid)]))

    # ── Section 2 (y=14): RED Metrics ──────────────────────────────────────────

    panels.append({
        "type": "DASHBOARD_MARKDOWN",
        "embeddableConfig": {
            "content": "**RED Metrics** Rate \u00b7 Errors \u00b7 Duration",
        },
        "panelIndex": "p_red_label",
        "gridData": {"h": 2, "i": "p_red_label", "w": 48, "x": 0, "y": 14},
    })

    # p30: P99 Latency
    lid = uid()
    cid = uid()
    columns = {cid: col_percentile("duration", 99, "P99 Latency")}
    layer = make_layer(lid, [cid], columns, DATA_VIEW_ID_TRACES)
    state = make_state(layer, {
        "layerId": lid,
        "layerType": "data",
        "metricAccessor": cid,
        "palette": PALETTE_LATENCY_P99,
        "subtitle": "nanoseconds",
    })
    panels.append(make_panel("p30",
        {"h": 6, "i": "p30", "w": 12, "x": 0, "y": 16},
        "P99 Latency", "lnsMetric", state, [make_ref(DATA_VIEW_ID_TRACES, lid)]))

    # p31: P50 Latency
    lid = uid()
    cid = uid()
    columns = {cid: col_percentile("duration", 50, "P50 Latency")}
    layer = make_layer(lid, [cid], columns, DATA_VIEW_ID_TRACES)
    state = make_state(layer, {
        "layerId": lid,
        "layerType": "data",
        "metricAccessor": cid,
        "palette": PALETTE_LATENCY_P50,
        "subtitle": "nanoseconds",
    })
    panels.append(make_panel("p31",
        {"h": 6, "i": "p31", "w": 12, "x": 12, "y": 16},
        "P50 Latency", "lnsMetric", state, [make_ref(DATA_VIEW_ID_TRACES, lid)]))

    # p32: Error Rate
    lid = uid()
    cid = uid()
    columns = {cid: col_formula("count(kql='status.code: Error') / count()", "Error Rate")}
    layer = make_layer(lid, [cid], columns, DATA_VIEW_ID_TRACES)
    state = make_state(layer, {
        "layerId": lid,
        "layerType": "data",
        "metricAccessor": cid,
        "palette": PALETTE_ERROR_RATE,
        "subtitle": "ratio",
    })
    panels.append(make_panel("p32",
        {"h": 6, "i": "p32", "w": 12, "x": 24, "y": 16},
        "Error Rate", "lnsMetric", state, [make_ref(DATA_VIEW_ID_TRACES, lid)]))

    # p33: Throughput
    lid = uid()
    cid = uid()
    columns = {cid: col_count(label="Throughput")}
    layer = make_layer(lid, [cid], columns, DATA_VIEW_ID_TRACES)
    state = make_state(layer, {
        "layerId": lid,
        "layerType": "data",
        "metricAccessor": cid,
        "palette": PALETTE_THROUGHPUT,
        "subtitle": "spans",
    })
    panels.append(make_panel("p33",
        {"h": 6, "i": "p33", "w": 12, "x": 36, "y": 16},
        "Throughput", "lnsMetric", state, [make_ref(DATA_VIEW_ID_TRACES, lid)]))

    # p34: P99 Latency Over Time (area, split by service)
    lid = uid()
    cid_x = uid()
    cid_y = uid()
    cid_split = uid()
    columns = {
        cid_x: col_date_histogram("30s"),
        cid_y: col_percentile("duration", 99, "P99 Latency"),
        cid_split: col_terms("resource.attributes.service.name", "Service", size=9, order_col_id=cid_y),
    }
    layer = make_layer(lid, [cid_x, cid_split, cid_y], columns, DATA_VIEW_ID_TRACES)
    state = make_state(layer, {
        "legend": {"isVisible": True, "position": "right"},
        "valueLabels": "hide",
        "fittingFunction": "None",
        "preferredSeriesType": "area",
        "layers": [{
            "layerId": lid,
            "layerType": "data",
            "seriesType": "area",
            "accessors": [cid_y],
            "xAccessor": cid_x,
            "splitAccessor": cid_split,
        }],
    })
    panels.append(make_panel("p34",
        {"h": 12, "i": "p34", "w": 24, "x": 0, "y": 22},
        "P99 Latency Over Time", "lnsXY", state, [make_ref(DATA_VIEW_ID_TRACES, lid)]))

    # p35: Error Rate by Service (bar_stacked)
    lid = uid()
    cid_x = uid()
    cid_y = uid()
    cid_split = uid()
    columns = {
        cid_x: col_date_histogram("30s"),
        cid_y: col_formula("count(kql='status.code: Error') / count()", "Error Rate"),
        cid_split: col_terms("resource.attributes.service.name", "Service", size=9),
    }
    layer = make_layer(lid, [cid_x, cid_split, cid_y], columns, DATA_VIEW_ID_TRACES)
    state = make_state(layer, {
        "legend": {"isVisible": True, "position": "right"},
        "valueLabels": "hide",
        "fittingFunction": "None",
        "preferredSeriesType": "bar_stacked",
        "layers": [{
            "layerId": lid,
            "layerType": "data",
            "seriesType": "bar_stacked",
            "accessors": [cid_y],
            "xAccessor": cid_x,
            "splitAccessor": cid_split,
        }],
    })
    panels.append(make_panel("p35",
        {"h": 12, "i": "p35", "w": 24, "x": 24, "y": 22},
        "Error Rate by Service", "lnsXY", state, [make_ref(DATA_VIEW_ID_TRACES, lid)]))

    # ── Section 3 (y=34): USE Metrics ──────────────────────────────────────────

    panels.append({
        "type": "DASHBOARD_MARKDOWN",
        "embeddableConfig": {
            "content": "**USE Metrics** Utilization \u00b7 Saturation \u00b7 Errors",
        },
        "panelIndex": "p_use_label",
        "gridData": {"h": 2, "i": "p_use_label", "w": 48, "x": 0, "y": 34},
    })

    # p36: CPU Load (1m)
    lid = uid()
    cid = uid()
    columns = {cid: col_average("metrics.system.cpu.load_average.1m", label="CPU Load")}
    layer = make_layer(lid, [cid], columns, DATA_VIEW_ID_METRICS)
    state = make_state(layer, {
        "layerId": lid,
        "layerType": "data",
        "metricAccessor": cid,
        "color": "#D6BF57",
        "subtitle": "1-min avg",
    })
    panels.append(make_panel("p36",
        {"h": 6, "i": "p36", "w": 12, "x": 0, "y": 36},
        "CPU Load (1m)", "lnsMetric", state, [make_ref(DATA_VIEW_ID_METRICS, lid)]))

    # p37: Disk Utilization
    lid = uid()
    cid = uid()
    columns = {cid: col_average("metrics.system.filesystem.utilization", label="Disk Util")}
    layer = make_layer(lid, [cid], columns, DATA_VIEW_ID_METRICS)
    state = make_state(layer, {
        "layerId": lid,
        "layerType": "data",
        "metricAccessor": cid,
        "color": "#6092C0",
        "subtitle": "filesystem",
    })
    panels.append(make_panel("p37",
        {"h": 6, "i": "p37", "w": 12, "x": 12, "y": 36},
        "Disk Utilization", "lnsMetric", state, [make_ref(DATA_VIEW_ID_METRICS, lid)]))

    # p38: Container Restarts
    lid = uid()
    cid = uid()
    columns = {cid: col_max("metrics.k8s.container.restarts", label="Restarts")}
    layer = make_layer(lid, [cid], columns, DATA_VIEW_ID_METRICS)
    state = make_state(layer, {
        "layerId": lid,
        "layerType": "data",
        "metricAccessor": cid,
        "color": "#E7664C",
        "subtitle": "container restarts",
    })
    panels.append(make_panel("p38",
        {"h": 6, "i": "p38", "w": 12, "x": 24, "y": 36},
        "Container Restarts", "lnsMetric", state, [make_ref(DATA_VIEW_ID_METRICS, lid)]))

    # p39: Network Errors
    lid = uid()
    cid = uid()
    columns = {cid: col_max("metrics.system.network.errors", label="Net Errors")}
    layer = make_layer(lid, [cid], columns, DATA_VIEW_ID_METRICS)
    state = make_state(layer, {
        "layerId": lid,
        "layerType": "data",
        "metricAccessor": cid,
        "color": "#E7664C",
        "subtitle": "network errors",
    })
    panels.append(make_panel("p39",
        {"h": 6, "i": "p39", "w": 12, "x": 36, "y": 36},
        "Network Errors", "lnsMetric", state, [make_ref(DATA_VIEW_ID_METRICS, lid)]))

    # p40: CPU Load Over Time (area, split by host)
    lid = uid()
    cid_x = uid()
    cid_y = uid()
    cid_split = uid()
    columns = {
        cid_x: col_date_histogram("30s"),
        cid_y: col_max("metrics.system.cpu.load_average.1m", label="CPU Load (1m)"),
        cid_split: col_terms("host.name", "Host", size=5, order_col_id=cid_y),
    }
    layer = make_layer(lid, [cid_x, cid_split, cid_y], columns, DATA_VIEW_ID_METRICS)
    state = make_state(layer, {
        "legend": {"isVisible": True, "position": "right"},
        "valueLabels": "hide",
        "fittingFunction": "None",
        "preferredSeriesType": "area",
        "layers": [{
            "layerId": lid,
            "layerType": "data",
            "seriesType": "area",
            "accessors": [cid_y],
            "xAccessor": cid_x,
            "splitAccessor": cid_split,
        }],
    }, query="data_stream.dataset: hostmetricsreceiver.otel")
    panels.append(make_panel("p40",
        {"h": 12, "i": "p40", "w": 24, "x": 0, "y": 42},
        "CPU Load Over Time", "lnsXY", state, [make_ref(DATA_VIEW_ID_METRICS, lid)]))

    # p41: Disk Utilization Over Time (area, split by host)
    lid = uid()
    cid_x = uid()
    cid_y = uid()
    cid_split = uid()
    columns = {
        cid_x: col_date_histogram("30s"),
        cid_y: col_max("metrics.system.filesystem.utilization", label="Disk Utilization"),
        cid_split: col_terms("host.name", "Host", size=5, order_col_id=cid_y),
    }
    layer = make_layer(lid, [cid_x, cid_split, cid_y], columns, DATA_VIEW_ID_METRICS)
    state = make_state(layer, {
        "legend": {"isVisible": True, "position": "right"},
        "valueLabels": "hide",
        "fittingFunction": "None",
        "preferredSeriesType": "area",
        "layers": [{
            "layerId": lid,
            "layerType": "data",
            "seriesType": "area",
            "accessors": [cid_y],
            "xAccessor": cid_x,
            "splitAccessor": cid_split,
        }],
    }, query="data_stream.dataset: hostmetricsreceiver.otel")
    panels.append(make_panel("p41",
        {"h": 12, "i": "p41", "w": 24, "x": 24, "y": 42},
        "Disk Utilization Over Time", "lnsXY", state, [make_ref(DATA_VIEW_ID_METRICS, lid)]))

    # ── Section 4 (y=54): APM & Infrastructure ─────────────────────────────────

    panels.append({
        "type": "DASHBOARD_MARKDOWN",
        "embeddableConfig": {
            "content": "**APM & Infrastructure**",
        },
        "panelIndex": "p_apm_label",
        "gridData": {"h": 2, "i": "p_apm_label", "w": 48, "x": 0, "y": 54},
    })

    # p10: APM Throughput
    lid = uid()
    cid = uid()
    columns = {cid: col_count(label="Transactions")}
    layer = make_layer(lid, [cid], columns, DATA_VIEW_ID_TRACES)
    state = make_state(layer, {
        "layerId": lid,
        "layerType": "data",
        "metricAccessor": cid,
        "color": "#54B399",
        "subtitle": "APM transactions",
    })
    panels.append(make_panel("p10",
        {"h": 6, "i": "p10", "w": 12, "x": 0, "y": 56},
        "APM Throughput", "lnsMetric", state, [make_ref(DATA_VIEW_ID_TRACES, lid)]))

    # p11: APM Error Rate
    lid = uid()
    cid = uid()
    columns = {cid: col_count(label="Errors", kql_filter="status.code: Error")}
    layer = make_layer(lid, [cid], columns, DATA_VIEW_ID_TRACES)
    state = make_state(layer, {
        "layerId": lid,
        "layerType": "data",
        "metricAccessor": cid,
        "color": "#E7664C",
        "subtitle": "APM errors",
    })
    panels.append(make_panel("p11",
        {"h": 6, "i": "p11", "w": 12, "x": 12, "y": 56},
        "APM Error Rate", "lnsMetric", state, [make_ref(DATA_VIEW_ID_TRACES, lid)]))

    # p12: NGINX Requests
    lid = uid()
    cid = uid()
    columns = {cid: col_count(label="Requests")}
    layer = make_layer(lid, [cid], columns, DATA_VIEW_ID_LOGS)
    state = make_state(layer, {
        "layerId": lid,
        "layerType": "data",
        "metricAccessor": cid,
        "color": "#6092C0",
        "subtitle": "NGINX requests",
    }, query="data_stream.dataset: nginx.access.otel")
    panels.append(make_panel("p12",
        {"h": 6, "i": "p12", "w": 12, "x": 24, "y": 56},
        "NGINX Requests", "lnsMetric", state, [make_ref(DATA_VIEW_ID_LOGS, lid)]))

    # p13: VPC Flow Volume
    lid = uid()
    cid = uid()
    columns = {cid: col_count(label="Flows")}
    layer = make_layer(lid, [cid], columns, DATA_VIEW_ID_LOGS)
    state = make_state(layer, {
        "layerId": lid,
        "layerType": "data",
        "metricAccessor": cid,
        "color": "#54B399",
        "subtitle": "VPC flow records",
    }, query='data_stream.dataset: "aws.vpcflow.otel" OR data_stream.dataset: "gcp.vpcflow.otel"')
    panels.append(make_panel("p13",
        {"h": 6, "i": "p13", "w": 12, "x": 36, "y": 56},
        "VPC Flow Volume", "lnsMetric", state, [make_ref(DATA_VIEW_ID_LOGS, lid)]))

    # p14: APM Errors Over Time by Service (bar_stacked)
    lid = uid()
    cid_x = uid()
    cid_y = uid()
    cid_split = uid()
    columns = {
        cid_x: col_date_histogram("30s"),
        cid_y: col_count(label="Errors"),
        cid_split: col_terms("resource.attributes.service.name", "Service", size=9, order_col_id=cid_y),
    }
    layer = make_layer(lid, [cid_x, cid_split, cid_y], columns, DATA_VIEW_ID_TRACES)
    state = make_state(layer, {
        "legend": {"isVisible": True, "position": "right"},
        "valueLabels": "hide",
        "fittingFunction": "None",
        "preferredSeriesType": "bar_stacked",
        "layers": [{
            "layerId": lid,
            "layerType": "data",
            "seriesType": "bar_stacked",
            "accessors": [cid_y],
            "xAccessor": cid_x,
            "splitAccessor": cid_split,
        }],
    }, query="status.code: Error")
    panels.append(make_panel("p14",
        {"h": 12, "i": "p14", "w": 24, "x": 0, "y": 62},
        "APM Errors Over Time by Service", "lnsXY", state, [make_ref(DATA_VIEW_ID_TRACES, lid)]))

    # p15: Log Volume Over Time (area_stacked)
    lid = uid()
    cid_x = uid()
    cid_y = uid()
    columns = {
        cid_x: col_date_histogram("30s"),
        cid_y: col_count(label="Log count"),
    }
    layer = make_layer(lid, [cid_x, cid_y], columns, DATA_VIEW_ID_LOGS)
    state = make_state(layer, {
        "legend": {"isVisible": True, "position": "right"},
        "valueLabels": "hide",
        "fittingFunction": "None",
        "preferredSeriesType": "area_stacked",
        "layers": [{
            "layerId": lid,
            "layerType": "data",
            "seriesType": "area_stacked",
            "accessors": [cid_y],
            "xAccessor": cid_x,
        }],
    })
    panels.append(make_panel("p15",
        {"h": 12, "i": "p15", "w": 24, "x": 24, "y": 62},
        "Log Volume Over Time", "lnsXY", state, [make_ref(DATA_VIEW_ID_LOGS, lid)]))

    # p16: NGINX Request Rate Over Time (area)
    lid = uid()
    cid_x = uid()
    cid_y = uid()
    columns = {
        cid_x: col_date_histogram("30s"),
        cid_y: col_count(label="Requests"),
    }
    layer = make_layer(lid, [cid_x, cid_y], columns, DATA_VIEW_ID_LOGS)
    state = make_state(layer, {
        "legend": {"isVisible": True, "position": "right"},
        "valueLabels": "hide",
        "fittingFunction": "None",
        "preferredSeriesType": "area",
        "layers": [{
            "layerId": lid,
            "layerType": "data",
            "seriesType": "area",
            "accessors": [cid_y],
            "xAccessor": cid_x,
        }],
    }, query="data_stream.dataset: nginx.access.otel")
    panels.append(make_panel("p16",
        {"h": 12, "i": "p16", "w": 24, "x": 0, "y": 74},
        "NGINX Request Rate", "lnsXY", state, [make_ref(DATA_VIEW_ID_LOGS, lid)]))

    # p17: VPC Flow Activity (bar_stacked, split by cloud provider)
    lid = uid()
    cid_x = uid()
    cid_y = uid()
    cid_split = uid()
    columns = {
        cid_x: col_date_histogram("30s"),
        cid_y: col_count(label="Flows"),
        cid_split: col_terms("data_stream.dataset", "Dataset", size=5, order_col_id=cid_y),
    }
    layer = make_layer(lid, [cid_x, cid_split, cid_y], columns, DATA_VIEW_ID_LOGS)
    state = make_state(layer, {
        "legend": {"isVisible": True, "position": "right"},
        "valueLabels": "hide",
        "fittingFunction": "None",
        "preferredSeriesType": "bar_stacked",
        "layers": [{
            "layerId": lid,
            "layerType": "data",
            "seriesType": "bar_stacked",
            "accessors": [cid_y],
            "xAccessor": cid_x,
            "splitAccessor": cid_split,
        }],
    }, query='data_stream.dataset: "aws.vpcflow.otel" OR data_stream.dataset: "gcp.vpcflow.otel"')
    panels.append(make_panel("p17",
        {"h": 12, "i": "p17", "w": 24, "x": 24, "y": 74},
        "VPC Flow Activity", "lnsXY", state, [make_ref(DATA_VIEW_ID_LOGS, lid)]))

    # ── Section 5 (y=86): Detail ───────────────────────────────────────────────

    panels.append({
        "type": "DASHBOARD_MARKDOWN",
        "embeddableConfig": {
            "content": "**Detail**",
        },
        "panelIndex": "p_detail_label",
        "gridData": {"h": 2, "i": "p_detail_label", "w": 48, "x": 0, "y": 86},
    })

    # p18: Errors by Service (bar_horizontal) — from traces
    lid = uid()
    cid_x = uid()
    cid_y = uid()
    columns = {
        cid_x: col_terms("resource.attributes.service.name", "Service", size=10, order_col_id=cid_y),
        cid_y: col_count(label="Error Count", kql_filter="status.code: Error"),
    }
    layer = make_layer(lid, [cid_x, cid_y], columns, DATA_VIEW_ID_TRACES)
    state = make_state(layer, {
        "legend": {"isVisible": True, "position": "right"},
        "valueLabels": "hide",
        "fittingFunction": "None",
        "preferredSeriesType": "bar_horizontal",
        "layers": [{
            "layerId": lid,
            "layerType": "data",
            "seriesType": "bar_horizontal",
            "accessors": [cid_y],
            "xAccessor": cid_x,
        }],
    })
    panels.append(make_panel("p18",
        {"h": 12, "i": "p18", "w": 24, "x": 0, "y": 88},
        "Errors by Service", "lnsXY", state, [make_ref(DATA_VIEW_ID_TRACES, lid)]))

    # p19: Service Health Heatmap — from traces
    lid = uid()
    cid_time = uid()
    cid_svc = uid()
    cid_val = uid()
    columns = {
        cid_time: col_date_histogram("1m"),
        cid_svc: col_terms("resource.attributes.service.name", "Service", size=10, order_col_id=cid_val),
        cid_val: col_count(label="Error Count", kql_filter="status.code: Error"),
    }
    layer = make_layer(lid, [cid_time, cid_svc, cid_val], columns, DATA_VIEW_ID_TRACES)
    state = make_state(layer, {
        "gridConfig": {"isCellLabelVisible": False},
        "shape": "heatmap",
        "layerId": lid,
        "layerType": "data",
        "xAccessor": cid_time,
        "yAccessor": cid_svc,
        "valueAccessor": cid_val,
        "legend": {"isVisible": True, "position": "right"},
    })
    panels.append(make_panel("p19",
        {"h": 12, "i": "p19", "w": 24, "x": 24, "y": 88},
        "Service Health Heatmap", "lnsHeatmap", state, [make_ref(DATA_VIEW_ID_TRACES, lid)]))

    # p24: Node CPU Over Time (area, split by cluster)
    lid = uid()
    cid_x = uid()
    cid_y = uid()
    cid_split = uid()
    columns = {
        cid_x: col_date_histogram("30s"),
        cid_y: col_average("metrics.k8s.node.cpu.utilization", label="CPU Utilization"),
        cid_split: col_terms("resource.attributes.k8s.cluster.name", "Cluster", size=5, order_col_id=cid_y),
    }
    layer = make_layer(lid, [cid_x, cid_split, cid_y], columns, DATA_VIEW_ID_METRICS)
    state = make_state(layer, {
        "legend": {"isVisible": True, "position": "right"},
        "valueLabels": "hide",
        "fittingFunction": "None",
        "preferredSeriesType": "area",
        "layers": [{
            "layerId": lid,
            "layerType": "data",
            "seriesType": "area",
            "accessors": [cid_y],
            "xAccessor": cid_x,
            "splitAccessor": cid_split,
        }],
    })
    panels.append(make_panel("p24",
        {"h": 12, "i": "p24", "w": 24, "x": 0, "y": 100},
        "Node CPU Over Time", "lnsXY", state, [make_ref(DATA_VIEW_ID_METRICS, lid)]))

    # p25: Pod Memory by Service (bar_stacked, split by service)
    lid = uid()
    cid_x = uid()
    cid_y = uid()
    cid_split = uid()
    columns = {
        cid_x: col_date_histogram("30s"),
        cid_y: col_average("metrics.k8s.pod.memory.usage", label="Memory Usage"),
        cid_split: col_terms("resource.attributes.service.name", "Service", size=10, order_col_id=cid_y),
    }
    layer = make_layer(lid, [cid_x, cid_split, cid_y], columns, DATA_VIEW_ID_METRICS)
    state = make_state(layer, {
        "legend": {"isVisible": True, "position": "right"},
        "valueLabels": "hide",
        "fittingFunction": "None",
        "preferredSeriesType": "bar_stacked",
        "layers": [{
            "layerId": lid,
            "layerType": "data",
            "seriesType": "bar_stacked",
            "accessors": [cid_y],
            "xAccessor": cid_x,
            "splitAccessor": cid_split,
        }],
    })
    panels.append(make_panel("p25",
        {"h": 12, "i": "p25", "w": 24, "x": 24, "y": 100},
        "Pod Memory by Service", "lnsXY", state, [make_ref(DATA_VIEW_ID_METRICS, lid)]))

    # ── Section 6 (y=112): Significant Event Logs ───────────────────────────

    panels.append({
        "type": "DASHBOARD_MARKDOWN",
        "embeddableConfig": {
            "content": "**Significant Event Logs** Trace-correlated error logs",
        },
        "panelIndex": "p_se_label",
        "gridData": {"h": 2, "i": "p_se_label", "w": 48, "x": 0, "y": 112},
    })

    # p26: Significant Event Logs (ES|QL datatable with body.text, trace.id, span.id)
    # Build ES|QL WHERE clause matching only configured significant event error types
    if error_types:
        kql_parts = " OR ".join(
            f'body.text: \\"{et}\\"' for et in error_types
        )
        esql_where = f'severity_text == "ERROR" AND KQL("{kql_parts}")'
    else:
        esql_where = 'severity_text == "ERROR"'

    esql_query = (
        f"FROM logs.otel,logs.otel.* "
        f"| WHERE {esql_where} "
        f"| KEEP body.text, trace.id, span.id, service.name, @timestamp "
        f"| SORT @timestamp DESC "
        f"| LIMIT 50"
    )

    lid = uid()
    adhoc_id = uid()  # ad-hoc data view ID for ES|QL

    def _esql_col(field, es_type, col_type):
        return {
            "columnId": uid(),
            "fieldName": field,
            "label": field,
            "customLabel": False,
            "meta": {"esType": es_type, "type": col_type},
        }

    esql_columns = [
        _esql_col("body.text", "text", "string"),
        _esql_col("trace.id", "keyword", "string"),
        _esql_col("span.id", "keyword", "string"),
        _esql_col("service.name", "keyword", "string"),
        _esql_col("@timestamp", "date", "date"),
    ]

    esql_state = {
        "adHocDataViews": {
            adhoc_id: {
                "allowHidden": False,
                "allowNoIndex": False,
                "fieldFormats": {},
                "id": adhoc_id,
                "name": "logs*",
                "runtimeFieldMap": {},
                "sourceFilters": [],
                "timeFieldName": "@timestamp",
                "title": "logs*",
                "type": "esql",
            }
        },
        "datasourceStates": {
            "textBased": {
                "layers": {
                    lid: {
                        "index": adhoc_id,
                        "query": {"esql": esql_query},
                        "columns": esql_columns,
                        "timeField": "@timestamp",
                    }
                }
            },
        },
        "filters": [],
        "internalReferences": [
            {
                "id": adhoc_id,
                "name": f"textBasedLanguages-datasource-layer-{lid}",
                "type": "index-pattern",
            }
        ],
        "query": {"esql": esql_query},
        "visualization": {
            "layerId": lid,
            "layerType": "data",
            "columns": [{"columnId": c["columnId"]} for c in esql_columns],
            "paging": {"enabled": True, "size": 10},
        },
    }

    panels.append(make_panel("p26",
        {"h": 14, "i": "p26", "w": 48, "x": 0, "y": 114},
        "Significant Event Logs", "lnsDatatable", esql_state, []))

    # ── Collect all references from panels ───────────────────────────────────

    all_refs = []
    seen_ref_names = set()
    for panel in panels:
        attrs = panel.get("embeddableConfig", {}).get("attributes", {})
        refs = attrs.get("references", [])
        for ref in refs:
            if ref["name"] not in seen_ref_names:
                all_refs.append(ref)
                seen_ref_names.add(ref["name"])

    # ── Build the dashboard saved object ─────────────────────────────────────

    dashboard = {
        "attributes": {
            "description": (
                f"Executive overview of {scenario_name} telemetry \u2014 "
                f"service health, APM, NGINX, VPC flows, K8s cluster health "
                f"across AWS/GCP/Azure"
            ),
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "query": {"language": "kuery", "query": ""},
                    "filter": [],
                }),
            },
            "panelsJSON": json.dumps(panels),
            "refreshInterval": {"pause": False, "value": 10000},
            "timeFrom": "now-2m",
            "timeRestore": True,
            "timeTo": "now",
            "title": f"{scenario_name} Executive Dashboard",
        },
        "coreMigrationVersion": "8.8.0",
        "id": dashboard_id,
        "managed": False,
        "references": all_refs,
        "type": "dashboard",
        "typeMigrationVersion": "10.3.0",
    }

    return json.dumps(dashboard, separators=(",", ":")) + "\n"


# ═══════════════════════════════════════════════════════════════════════════════
# Standalone CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    from scenarios import get_scenario

    scenario_id = sys.argv[1] if len(sys.argv) > 1 else "space"
    scenario = get_scenario(scenario_id)

    ndjson = generate_dashboard_ndjson(scenario)

    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "exec-dashboard.ndjson",
    )
    with open(output_path, "w") as f:
        f.write(ndjson)

    print(f"Wrote {output_path}")
    print(f"  Scenario: {scenario.scenario_name}")
    print(f"  Dashboard ID: {scenario.namespace}-exec-dashboard")

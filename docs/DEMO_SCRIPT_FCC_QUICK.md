# FCC Demo — Quick Reference Card

**Duration:** 15-20 min | **Scenario:** FCC Communications Resilience | **Trigger:** Channels 7-9 (911 PSAP arc)

---

## Pre-Flight

- [ ] FCC scenario deployed and running 2-3 min
- [ ] APM → Services shows 9 FCC services
- [ ] Synthetics → 5 HTTP monitors green
- [ ] Tabs open: Dashboard · Discover · APM · Synthetics · Streams · Workflows · Chaos UI

---

## Act 1 — Tools Consolidation (~5 min)

**Kibana → Observability → Overview**
> "Mission control — logs, metrics, traces, uptime, anomalies in one view. Not a dashboard on top of six tools — one storage layer, one query language."

**Kibana → Dashboards → FCC Communications Resilience**
> "Regulator KPIs — PSAP availability, WEA delivery latency, broadband coverage, complaint SLA. Same ingest pipeline as the engineering logs. No BI export."

**Kibana → Discover** · Data view: `FCC Communications Resilience Logs` · Filter: `service.name : "outage-reporting"`
> "One click from the executive dashboard to raw 911-outage service logs. Same UI, same query language. That's consolidation."

---

## Act 2 — Distributed Tracing (~3 min)

**APM → Services → `outage-reporting` → Traces → pick a recent trace**
> "9 microservices across AWS, GCP, Azure. One trace, one timeline. PSAP impact request on Azure → EAS gateway on AWS → data-exchange on Azure → spectrum monitor on AWS."

**Click a span → expand metadata**
> "`cloud.provider`, `cloud.region`, `fcc.case_id`, `fcc.carrier_id` — OpenTelemetry-native. When one carrier's traffic is hot and others are fine, this trace tells you instantly."

---

## Act 2.5 — Synthetics (~2 min)

**Kibana → Observability → Synthetics**

Five HTTP monitors hitting live FCC portals every 3 min from US East:
`www.fcc.gov` · `consumercomplaints.fcc.gov` · `broadbandmap.fcc.gov` · `wireless2.fcc.gov` · `opendata.fcc.gov`

> "External probes — no agents on FCC servers, no code changes. If the complaint portal starts returning 500s, Elastic sees it before any citizen calls. For production you'd add browser checks — load the form, fill fields, screenshot on failure."

---

## Act 3 — Logs in Context (~2 min)

**Stay in the Act 2 trace → click "Logs" tab on a span**
> "One click from the trace span to every log line for that exact request. `trace.id` and `span.id` on every log — no copy-paste into a separate tool."

**Filter to `ERROR` severity**
> "Error logs beside the failing span — latency and root cause on one screen."

> "Works backward too — from a log line, pivot to the trace. From a host metric spike, pivot to logs from that host. Trace ↔ log ↔ metric, all linked by shared semantic fields."

---

## Act 3.5 — Metrics (~3 min)

**Kibana → Observability → Infrastructure → Hosts**
> "`fcc-aws-host-01`, `fcc-gcp-host-01`, `fcc-azure-host-01` — CPU, memory, disk, network across three clouds. Same OTLP pipeline as the logs."

**Switch to Kubernetes view**
> "`fcc-eks-cluster` / `fcc-gke-cluster` / `fcc-aks-cluster` — pods, nodes, resource pressure. OOMKill and 911 incident on one screen."

**APM → Services → `outage-reporting`**
> "Golden signals — RPS, p95/p99 latency, error rate. Click a trace span → host chip in metadata → jumps to Infrastructure host view for that exact time window. Trace → metric pivot, no tool-switching."

**Back to exec dashboard**
> "`metrics.business.psap_911_availability_pct`, `metrics.business.wea_delivery_latency_ms` — business KPIs and infra metrics in the same store. That's what 'one platform' means."

---

## Act 4 — Streams (~3 min)

**Kibana → Streams → `logs.ecs.fcc`**
> "Raw FCC API access logs — one text blob per line. Can't query path or status individually yet."

**Add processor → grok pattern**
> "Parse in place. No reindex, no Logstash, no downtime. Every existing record and every new record gets structure applied."

**After partition → Discover with `FCC Communications Resilience Logs (ECS)`**
> "Now queryable by `http.method`, `http.status_code`, `submitter_type`, `url.path`. 5xx by submitter type. NORS latency alert. Raw logs became structured data — live."

---

## Act 5 — Workflows + AI (~5 min)

**Trigger Ch 7:**
```
curl -X POST http://<host>/api/chaos/trigger \
  -H 'Content-Type: application/json' \
  -d '{"channel": 7}'
```

**Watch dashboard** → `outage-reporting` CRITICAL, `eas-gateway` affected, cascade warnings
> "PSAP call-routing failure — Selective Router can't reach primary PSAP, forced overflow. Real NORS-reportable pattern."

**Kibana → Alerts**
> "ES|QL rule detected `FCC-PSAP-CALL-ROUTING-FAIL`. Not 'error rate high' — the rule knows the specific 911 signature."

**Kibana → Workflows → "FCC Communications Resilience Significant Event Notification (Human in the Loop)" → most recent execution**

| Step | What it does | What to say |
|---|---|---|
| 1 — ES|QL log query | Pulls error signatures + affected PSAPs | "Workflow queries logs first — automated context gathering." |
| 2 — ES|QL metrics query | Pulls latency + error rate | "Quantitative context alongside the log narrative." |
| 3 — Create case + notify | Opens Kibana case, pages on-call | "Human loop opens before AI even runs." |
| 4 — `run_rca` (AI agent) | Full RCA with 911 domain knowledge | "Identifies trunk-group exhaustion, traces cascade to `eas-gateway`, classifies NORS reportability, recommends `reroute_psap_overflow`." |
| 5 — `request_remediation` | Agent invokes remediation sub-workflow, pauses for approval | "Operator opens case, sees RCA, clicks Approve. 60 seconds from fault to human holding an approval decision with full AI context." |

**Optional:** trigger Ch 8 or Ch 9 to show the same flow on a different 911 pattern.

---

## Act 5.5 — AIOps (~3 min)

**Kibana → Machine Learning → Anomaly Detection → Anomaly Explorer**
> "ML jobs learned the baseline — request rates, latencies, log volumes — and flag deviations without a rule. Red cell = unusual vs this hour, this day-of-week. No threshold tuning."

**Kibana → Alerts**
> "One root cause → one incident, not fifty pages. Elastic groups related alerts by entity, time, root-cause context. Rules are versioned, tagged, mutable. Noise reduction is operational, not cosmetic."

---

## Closing (1 min)

> "Eight capabilities, one platform: **consolidated** observability · **distributed tracing** · **Synthetics DEM** · **logs in context** · **metrics** (infra + APM + KPIs) · **Streams** · **Workflows + AI** · **AIOps**. Same OTLP. Same Elastic. Regulator, carrier, or 911 provider."

---

## 911 Channels Cheat Sheet

| Ch | Name | Signature | Remediation |
|---:|---|---|---|
| 7 | PSAP Call-Routing Failure | `FCC-PSAP-CALL-ROUTING-FAIL` | `reroute_psap_overflow` |
| 8 | Wireless E911 Handoff Drop | `FCC-CARRIER-HANDOFF-DROP` | `failover_carrier_msc_trunk` |
| 9 | ALI Location Lookup Degraded | `FCC-ALI-LOOKUP-DEGRADED` | `refresh_ali_cache` |

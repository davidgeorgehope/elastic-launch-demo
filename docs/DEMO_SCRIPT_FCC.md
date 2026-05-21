# FCC Demo Script — Elastic Observability Walkthrough

> **Duration:** 15-20 minutes (adjustable)
> **Audience:** FCC, public-safety teams, 911 service providers, telecom regulators
> **Scenario:** FCC Communications Resilience (channels 7-9 are the 911 PSAP arc)
> **Setup:** Deploy the `fcc` scenario from the selector and let it run 2-3 minutes so logs, metrics, and traces accumulate.

---

## Pre-Demo Checklist

- [ ] App is running (`http://<host>/health` returns OK)
- [ ] FCC scenario is deployed (selector at `http://<host>/`)
- [ ] Tabs open: **Dashboard**, **Chaos UI**, **Kibana Discover**, **Kibana APM**, **Kibana Streams**, **Kibana Workflows**
- [ ] Verify alert rules are active in Kibana > Rules
- [ ] Confirm traces are flowing in Kibana > APM > Services (9 FCC services)
- [ ] Confirm 5 Synthetics HTTP monitors are showing green in Kibana > Observability > Synthetics

---

## Data Views Quick Reference

The FCC deployer creates 6 data views. Use these throughout the demo:

| Demo moment | Data view name | ID |
|---|---|---|
| Act 1 Discover, general log queries | **FCC Communications Resilience Logs** | `logs.otel.fcc` |
| Act 2 Discover (traces ad-hoc) | **FCC Communications Resilience Traces** | `traces-*` |
| Act 3.5 Discover (metrics ad-hoc) | **FCC Communications Resilience Metrics** | `metrics-*` |
| Act 4 Streams partitioned output | **FCC Communications Resilience Logs (ECS)** | `logs.ecs.fcc` |

Act 2 (APM Service map), Act 3 (Logs in APM), Act 3.5 (Infrastructure / APM service metrics), and Act 5 (Workflows / Alerts) use dedicated Kibana UIs and don't require data-view selection.

---

## What this script covers

Eight Elastic observability capabilities, told through the FCC 911 reliability story:

1. **Tools consolidation** — one platform for logs, metrics, traces, KPIs, security
2. **Distributed tracing** — request flow across AWS / GCP / Azure
3. **Digital experience monitoring** — Synthetics, the user's view
4. **Logs in context** — trace ↔ log ↔ metric, auto-correlated
5. **Metrics** — infrastructure + APM service + business KPIs, one store
6. **Streams** — parse raw text logs live, no Logstash
7. **Workflows + AI** — alert → AI investigation → automated remediation
8. **AIOps** — ML anomaly detection + alert noise reduction at scale

---

## FCC Challenges & Goals (open the meeting here)

**Duration:** ~5-10 minutes of conversation
**Goal:** Before showing anything, hear FCC's pain in their own words. The demo lands harder when it echoes what they just said back.

### Recommended opener

> "Before I show you anything, I'd love to hear what the FCC's biggest observability and reliability headaches look like today. I'll tune the next 30 minutes to what you call out. Mind if I ask a few questions?"

### Discovery questions (pick 3-4, don't grill)

- **Current tooling** — "What do you use today for logs, metrics, traces, alerting? Any places where the seams between tools cost you time?"
- **Top operational pain** — "When something goes wrong in a citizen-facing system — the consumer complaint portal, broadband availability lookup — what does the response actually look like? Where do you lose time?"
- **911 / public safety reliability** — "How do you currently track PSAP availability, NORS reporting timeliness, or wireless E911 location accuracy? Is the data already in one place?"
- **Broadband data freshness** — "The new Broadband Funding Map and BDC fabric — how confident are you in the freshness of the data citizens see?"
- **AIOps maturity** — "Are you using any ML or AI today for incident response? Where would automation save the most time?"
- **Compliance & retention** — "Any audit, FOIA, or FedRAMP constraints that limit where data can live or how long it must be kept?"

### Listen for these themes, then bias the demo accordingly

| If they say... | Lean into... |
|---|---|
| "Too many tools, hard to correlate" | Act 1 (consolidation), Act 3 (logs in context) |
| "Slow root-cause analysis" | Act 2 (tracing), Act 5 (AI agent) |
| "Citizens see errors before we do" | Act 2.5 (DEM/Synthetics), Act 3.5 (metrics) |
| "Alert fatigue / on-call burnout" | Act 5.5 (AIOps) |
| "Raw logs from legacy apps" | Act 4 (Streams) |
| "Need to demonstrate ROI quickly" | Pilot Scope option 1 (lighthouse) |

### Bridge into the demo

> "Got it — what you're describing aligns well with what I'm about to show. Let me walk you through how Elastic handles [echo their top pain]. We'll spend more time on the parts that matter most to you."

---

## Act 1 — Observability Overview + Tools Consolidation

**Duration:** ~5-6 minutes
**Where:** Kibana → Observability → Overview, then the FCC executive dashboard, then Discover.

### Start with the big picture

Navigate to Kibana → Observability → Overview.

> "This is the Observability Overview page in Kibana — your mission control center. It gives you a real-time, high-level snapshot of the health and performance of your entire environment across infrastructure, applications, and services."

### Highlight the unified view

> "From this single page, you can see metrics, logs, traces, uptime checks, and synthetics results all correlated together. Instead of jumping between multiple monitoring tools, you get a holistic view in one place."

### Walk through the key sections

Point at each panel as you cover it.

- **Service inventory / APM**

  > "Here you can see all the services Elastic is monitoring — their health status, latency, throughput, and error rates. This helps quickly identify which services might be degrading."

- **Infrastructure metrics**

  > "This panel shows aggregated CPU, memory, network, and storage utilization across your infrastructure — whether it's on-prem, cloud, or hybrid."

- **Log volume and trends**

  > "You can spot spikes or anomalies in log ingestion here and drill down directly into the logs for root cause analysis."

- **Uptime and synthetics**

  > "We can see the results of uptime monitors and synthetic transactions to track user journey performance and availability."

- **Alerts and anomalies**

  > "Elastic's ML jobs surface anomalies here — whether in response times, error rates, or infrastructure metrics — so you can take action before users notice."

### Land the tools-consolidation message

> "Most observability stacks today are a patchwork — Datadog for APM, Splunk for logs, Grafana for metrics, PagerDuty for alerts, a separate BI tool for executive KPIs, and a SIEM for security. Six tools, six bills, six query languages, six places your on-call has to look at 3am."

> "Elastic is one platform for all of it — logs, metrics, traces, business KPIs, security, AI investigation — on a single storage layer, with a single query language (ES|QL), and a single UI."

Open the FCC executive dashboard (Kibana → Dashboards → FCC Communications Resilience).

> "This dashboard isn't infra-team metrics — it's regulator KPIs. Broadband availability, PSAP 911 availability, WEA delivery latency, complaint SLA compliance. Same data store, same ingest pipeline as the engineering logs and traces. You're not exporting to a separate BI tool — it's all one platform."

Switch to Kibana Discover. Pick the data view **`FCC Communications Resilience Logs`** (id: `logs.otel.fcc` — the unified view covering both OTel and ECS partitions). Filter to `service.name : "outage-reporting"`.

> "From the executive view I'm one click away from the raw 911-outage-reporting service logs. Same UI, same query language. That's tool consolidation."

---

## Act 2 — Distributed Tracing

**Duration:** ~3-4 minutes
**Where:** Kibana → APM → Services.

> "The FCC platform here is 9 microservices running across AWS, GCP, and Azure. When a 911 call comes in, the request fans out across all three clouds — that's our reality with most carrier and regulator deployments."

Open APM → Services → click `outage-reporting`.

> "Here's the 911 outage-reporting service. Elastic auto-discovered it from OpenTelemetry — zero manual config."

Open Traces → pick a recent trace that spans multiple services.

> "Here's a single end-to-end transaction. The PSAP impact request enters on Azure, calls the EAS gateway on AWS, which calls the data-exchange service on Azure for an ALI lookup, which queries the spectrum monitor on AWS. Four services, three clouds, one trace, one timeline. Click any span — duration, parent, child, attributes."

Click a span, expand metadata.

> "Look at the attributes — cloud.provider, cloud.region, service.name, fcc.case_id, fcc.carrier_id. OpenTelemetry-native. The same trace tells you where it ran, what it touched, and which carrier and FCC case it belongs to. The carrier_id matters — when one carrier's traffic is hot and the others are fine, this trace tells you instantly."

---

## Act 2.5 — Digital Experience Monitoring & Synthetics

**Duration:** ~2 minutes
**Where:** Kibana → Observability → Synthetics.

> "Everything we've shown so far is what's happening inside the platform — requests, traces, services. But the question the FCC actually cares about is different: is the public actually able to use this? Can a consumer file a complaint? Can a state broadband office submit a coverage challenge? Is the carrier filing portal up? That's digital experience — the user's view of your service, not yours."

### Synthetics — proactive monitoring

Open Kibana → Observability → Synthetics.

You should see **5 HTTP monitors** (deployed automatically by the FCC scenario):

| Monitor name | URL |
|---|---|
| FCC Public Portal | `https://www.fcc.gov/` |
| FCC Consumer Complaint Portal | `https://consumercomplaints.fcc.gov/hc/en-us` |
| FCC Broadband Map | `https://broadbandmap.fcc.gov/home` |
| FCC ULS License Search | `https://wireless2.fcc.gov/UlsApp/UlsSearch/searchLicense.jsp` |
| FCC Open Data Portal | `https://opendata.fcc.gov/` |

> "These are synthetic monitors Elastic runs from US East every 3 minutes — hitting the actual live FCC portals. Every check records whether the site returned a successful response and how long it took. No agents on the origin servers, no code changes to FCC's properties — just external probes from Elastic's managed infrastructure."

> "If any of these turn red — the broadband map starts returning 500s, the complaint portal goes down — Elastic sees it before any citizen notices and before any FCC ops team gets a call. That's the proactive half of digital experience."

> "For a real deployment, you'd add browser-level checks too — actually loading the complaint form, filling in fields, verifying the submit button works — with screenshots and network waterfall on failure. HTTP checks tell you the site is up; browser checks tell you it actually works for users."

### Tie back to troubleshooting

> "Synthetics feeds the same alert and workflow engine we'll see in Act 5. A failing synthetic browser test on the consumer complaint portal can trigger the same AI investigation agent — the agent starts from 'the public-facing portal is failing' and works backward into the service traces, the database, the network. End-to-end troubleshooting starts from the user, not from the box."

### Transition

> "Now let's go the other direction — from a service trace, into the logs that explain what each service was doing."

---

## Act 3 — Logs in Context

**Duration:** ~2-3 minutes
**Where:** Stay in the trace from Act 2.

> "Tracing tells you the request shape. Logs tell you what each service was doing. In Elastic, they're linked — automatically."

In the trace span detail, click **"Logs"** tab.

> "From inside the trace, one click — and Elastic gives me every log record from this service, in this time window, for this exact request. No copy-pasting trace IDs into a different tool. The trace_id and span_id are on every log line. That's logs in context."

Filter to severity ERROR (if any).

> "If this trace had an error, the ERROR logs are right here, beside the failing span. You see latency and the reason for it on the same screen."

Then pivot the other direction:

> "And it works backward — from a log line I can pivot straight into the trace it belongs to. From a host metric spike I can pivot to the logs from that host during the spike. Trace ↔ log ↔ metric, all linked by shared semantic conventions."

---

## Act 3.5 — Metrics: Infra + APM + Business KPIs, One Store

**Duration:** ~3-4 minutes
**Where:** Kibana → Observability → Infrastructure → Hosts, then APM service overview, then briefly back to the exec dashboard.

> "In most stacks, metrics live in a different system from logs and traces. Prometheus and Grafana over here, ELK for logs there, APM somewhere else. Three storage backends, three query languages, three places your on-call has to look. In Elastic, every metric — infrastructure, service, business — lives in the same store as your logs and traces."

### Infrastructure metrics

Open Kibana → Observability → Infrastructure → Hosts.

> "Here are the hosts running our FCC platform — `fcc-aws-host-01`, `fcc-gcp-host-01`, `fcc-azure-host-01`. CPU, memory, disk, network — one panel per host across three clouds. Same OTLP pipeline as the application logs."

Switch to Kubernetes view.

> "And here's the container layer — `fcc-eks-cluster` on AWS, `fcc-gke-cluster` on GCP, `fcc-aks-cluster` on Azure. Pods, nodes, namespaces, resource pressure. If a pod is getting OOMKilled at the same time a 911 incident fires, you'd see both signals on one screen."

(Optional) Click VPC flow logs.

> "Network telemetry too — VPC flow logs from all three clouds, indexed and queryable in the same UI."

### APM service metrics

Open APM → Services → click `outage-reporting`.

> "This is the SRE view — requests per minute, latency p95 and p99, error rate, dependencies. The classic golden signals. Same data store, same query language, same UI as everything else we've looked at."

Filter on a specific transaction (e.g. `/api/v1/outages/911`).

> "I can slice by transaction. Here's just the 911 outage endpoint — its baseline RPS, baseline latency. When Ch 7 fires later, this latency line is going to spike, and Elastic's anomaly detection will flag it before a human looks."

### Trace → metric pivot

Inside the APM service view, click a recent trace span → expand the host or container metadata.

> "Same pivot story as logs in context — but for metrics. From a span, I can jump to the host CPU during that exact transaction, or to the container memory pressure on the pod that served it. Trace → metric → log, all linked by `host.name`, `service.name`, `trace.id`. No tool-switching."

### Business KPIs as metrics

Briefly return to the FCC executive dashboard.

> "Remember the executive dashboard from Act 1? Every tile on it is an OTLP gauge — `metrics.business.psap_911_availability_pct`, `metrics.business.wea_delivery_latency_ms`, `metrics.business.broadband_availability_pct`. Operational metrics from the services and business KPIs for leadership, same store, same query language. That's what 'one platform' actually means."

### Transition

> "Now let's look at the messier end of the data spectrum — raw, unstructured logs from legacy systems. That's Streams."

---

## Act 4 — Streams

**Duration:** ~3-4 minutes
**Where:** Kibana → Streams.

> "Not all telemetry shows up as nicely structured OTLP. Most enterprises have decades-old applications emitting raw text logs — nginx access logs, custom app logs, syslog. Elastic Streams is how we handle that."

Open Streams, find the `logs.ecs.fcc` stream (raw access logs from the FCC `fcc-public-api` log generator). The matching Discover data view for the partitioned output is **`FCC Communications Resilience Logs (ECS)`** (id: `logs.ecs.fcc`).

> "This is a stream of raw FCC API access logs. Each line is a single text blob — method, path, status, latency, all jammed together. Right now Elastic just stores it. We can't query the path or the status individually."

Click "Partition" or "Add processor" → grok pattern for an nginx-style line.

> "I want to extract structure. I tell Elastic the grok pattern — it parses every existing record and every new record going forward. No reindex, no downtime, no separate Logstash deployment to manage."

After the partition processes:

> "Now I can query by `http.method`, `http.status_code`, `submitter_type`, `url.path`. I can build a dashboard showing 5xx rate by submitter type. I can alert on `/api/v1/outages/nors` latency. The raw logs became structured data — live, without touching the source application."

Optional: show a partition that pulls out `submitter_type` (consumer / carrier / state / public_safety) so the audience sees a regulator-flavored field.

---

## Act 5 — Workflows: Alert → AI Agent → Remediate

**Duration:** ~5 minutes
**Where:** Chaos UI, then Kibana Alerts, then Kibana Workflows.

> "We've shown collect, correlate, query. Now the part that matters at 3am — what does Elastic do without a human in the loop."

Trigger Channel 7 — PSAP Call-Routing Failure:

```bash
curl -X POST http://<host>/api/chaos/trigger \
  -H 'Content-Type: application/json' \
  -d '{"channel": 7}'
```

> "I just triggered a PSAP call-routing failure. Selective Router can't deliver 911 calls to the primary PSAP, forced overflow to the backup. Real FCC NORS-reportable incident pattern."

Watch the dashboard.

> "Within seconds, outage-reporting goes CRITICAL, eas-gateway is affected, consumer-complaints and data-exchange show cascade warnings."

Switch to Kibana → Alerts.

> "Elastic's ES|QL rules detected `FCC-PSAP-CALL-ROUTING-FAIL` and fired a significant event. Notice — not a generic 'error rate high' alert. The rule knows the specific signature."

Switch to Kibana → Workflows → recent execution.

> "The alert triggered an Elastic Workflow. The workflow is YAML — declarative. Step one: query logs. Step two: invoke our AI agent. Step three: based on the agent's RCA, decide whether to auto-remediate or escalate to a human."

Open the workflow run, expand the agent step.

Which workflow to open
"FCC Communications Resilience Significant Event Notification (Human in the Loop)"

That's the one triggered when you fire Ch 7. Navigate to it in Kibana → Workflows, click the most recent execution.

What the execution shows (step-by-step walkthrough)
The workflow has these steps in order — here's what to say at each one:

Step 1 — ES|QL log query

"First step: the workflow queries the last 30 minutes of logs for the triggering service, pulling error signatures and affected PSAPs."

Step 2 — ES|QL metrics query

"Second step: it pulls latency and error-rate metrics for the same window — gives the agent quantitative context alongside the log narrative."

Step 3 — Create case + notify

"A Kibana case is opened automatically and the on-call gets notified. This happens before the AI even runs — the human loop is already open."

Step 4 — AI agent RCA (run_rca)

"Here's the AI agent. It received the logs, metrics, and the full 911 domain context — Selective Routers, NORS reportability thresholds, PSAP overflow routing. Watch the output: it identifies the trunk-group exhaustion, traces the cascade to eas-gateway, classifies this as NORS-reportable, and recommends reroute_psap_overflow."

Step 5 — Request remediation (request_remediation)

"The workflow sends the RCA back to the agent with one instruction: propose the remediation action. The agent invokes the remediation_action sub-workflow — which pauses here, waiting for a human to approve or deny inside the Kibana case."

Point at the case link in the workflow output.

"The operator opens the case, sees the full RCA, clicks Approve — remediation executes, dashboard goes green. That's the human-in-the-loop. Sixty seconds from fault to a human holding an approval decision, with full AI context."

> "Here's the FCC Communications Operations Analyst — our AI agent. It has tools — parameterized ES|QL queries against our telemetry, a knowledge base with NG911/Selective Router/MSAG documentation. It already knows about NORS reportability thresholds. Watch it work — it identified the Selective Router trunk-group exhaustion, traced the cascade, classified the FCC reportability, and recommended `reroute_psap_overflow`."

Show the final workflow output — RCA summary + remediation action taken.

> "The workflow then called back to our platform's remediation API. The dashboard is going green. An email goes to the duty supervisor with the full RCA. From fault detection to resolution: roughly 60 seconds. No human in the loop unless one is needed."

**Optional second fault** — trigger Ch 8 (Wireless Carrier E911 Handoff Drop) or Ch 9 (ALI Location Lookup Degradation) to show the same flow with a different 911 incident. Reinforces that the agent generalizes across the 911 reliability arc.

---

## Act 5.5 — AIOps: Anomaly Detection & Alert Noise Reduction

**Duration:** ~3-4 minutes
**Where:** Kibana → Machine Learning → Anomaly Detection, then Kibana → Alerts.

> "Act 5 showed one alert, one agent, one remediation. In production you have thousands of alerts a day across hundreds of services. The story changes from 'investigate this' to 'don't drown.' That's AIOps."

### Anomaly detection — find what static rules miss

Open Kibana → Machine Learning → Anomaly Detection → Job Management.

> "Elastic ships with ML jobs that learn the normal pattern of your data — request rates, latencies, log volumes, error counts, transaction durations — and flag deviations without you writing a rule. At scenario launch we deployed several jobs: log rate anomalies, log categorization anomalies, APM latency anomalies."

Open the Anomaly Explorer view.

> "Each row is a job, each column is a time bucket, each cell is a severity score. A red square means 'this is unusual versus what this metric normally looks like at this hour, on this day.' No threshold tuning, no static rules. You don't have to know in advance that NORS submissions spike on Monday morning — the model knows."

### Alert noise reduction — group and correlate

Switch to Kibana → Alerts.

> "Most observability stacks fire one alert per signal. One root cause becomes 50 alerts because 50 downstream services went red. Elastic groups related alerts by entity, time, and root-cause context — so one PSAP routing failure is one incident, not fifty pages."

> "Alert rules are first-class objects — versioned, owned by team, taggable. Mute by tag, route by tag, escalate by tag. The noise reduction is operational, not just visual."

### Tie it together — the full AIOps loop

> "The full AIOps loop you've now seen: ML jobs detect anomalies → significant events fire → workflows trigger → AI agent investigates → automated remediation or human escalation. All instrumented, all auditable, all native to Elastic — no third-party AIOps tool to integrate."

### Transition

> "That's the platform end to end. Let's talk about what this looks like in your environment — and what a pilot might scope to."

---

## Closing

**Duration:** ~1 minute

> "Eight capabilities, one platform:
>
> 1. **Consolidated** — logs, metrics, traces, KPIs, security in one stack
> 2. **Distributed tracing** — request flows across AWS / GCP / Azure with carrier and case context
> 3. **Digital experience monitoring** — Synthetics, troubleshooting that starts from the user
> 4. **Logs in context** — trace ↔ log ↔ metric, auto-correlated
> 5. **Metrics** — infrastructure, APM, and business KPIs in one store, with trace ↔ metric pivot
> 6. **Streams** — parse raw text logs live, no Logstash, no reindex
> 7. **Workflows + AI** — alert → agent investigation → automated remediation, FCC-domain-aware
> 8. **AIOps** — ML anomaly detection + alert noise reduction at scale
>
> Same architecture in production. Same OTLP. Same Elastic. Whether you're a regulator, a carrier, or a 911 service provider — it's the same platform."

---

## Architecture, Pilot Scope & Next Steps (post-demo conversation)

**Duration:** ~10-15 minutes
**Format:** Whiteboard / dialogue, not a script to read verbatim.

### Architecture talking points

- **Deployment model** — Elastic Cloud (managed SaaS in AWS, GCP, or Azure GovCloud regions), or Elastic self-managed if FedRAMP-High or air-gap requirements apply.
- **Ingest** — OTLP-native; existing OpenTelemetry instrumentation flows in unchanged. Elastic Agent / Fleet for infrastructure and traditional sources. Beats and Logstash for legacy ingestion paths.
- **Data residency & compliance** — region pinning, encryption at rest, FedRAMP Moderate on Elastic Cloud for Government, FIPS 140-2 cryptography in Elasticsearch.
- **Scaling & retention** — hot / warm / cold / frozen tiers. Searchable snapshots keep multi-year retention at object-storage cost while remaining queryable.
- **Identity & access** — SSO via SAML / OIDC; role-based access control down to document and field level; full audit logging.

### Pilot scope options (three shapes)

| # | Scope | Timeline | What we'll show |
|---|---|---|---|
| 1 | **Observability lighthouse** | 4-6 weeks | One high-value FCC service end-to-end (e.g., 911 outage reporting): instrument, ingest, dashboards, alerts, one team trained |
| 2 | **Cross-bureau telemetry consolidation** | 8-12 weeks | 3-5 services across bureaus (CGB, OET, PSHSB); cost savings vs incumbent tooling; cross-service traces |
| 3 | **Full reliability stack** | 12-16 weeks | Observability + AIOps + workflows + AI agent for incident response; measured against MTTD, MTTR, alert volume |

### Success criteria — what we'll measure

- **MTTD (Mean Time to Detect)** — baseline vs Elastic-detected.
- **MTTR (Mean Time to Resolve)** — baseline vs Elastic + workflow + AI agent.
- **Alert volume** — alerts/day baseline vs deduped / grouped in Elastic.
- **Tool consolidation** — number of monitoring tools eliminated or candidates for elimination.
- **Coverage** — percentage of in-scope services with end-to-end observability.

### Follow-up items to align on before leaving the room

- Discovery deep-dive on the chosen pilot service (1-2 hours, week +1).
- Architecture review with FCC security / FedRAMP officer if required.
- Schedule pilot kickoff date and identify the FCC team lead.
- Share the Elastic FedRAMP attestation and security questionnaire.

---

## The 911 Channels at a Glance

| Channel | Name | Error Signature | Remediation |
|--------:|------|-----------------|-------------|
| 7 | PSAP Call-Routing Failure | `FCC-PSAP-CALL-ROUTING-FAIL` | `reroute_psap_overflow` |
| 8 | Wireless Carrier E911 Handoff Drop | `FCC-CARRIER-HANDOFF-DROP` | `failover_carrier_msc_trunk` |
| 9 | ALI Location Lookup Degradation | `FCC-ALI-LOOKUP-DEGRADED` | `refresh_ali_cache` |

The other 17 channels (broadband mapping, spectrum, EAS/WEA, consumer complaints, licensing, auctions, NORS, robocalls, public data) remain available for broader regulator-wide demos.

---

## Q&A Talking Points

**"Is the telemetry real OpenTelemetry?"**
> Yes. The services emit OTLP JSON over HTTP directly to Elastic Cloud. The same OTLP protocol works with any OpenTelemetry-compatible source.

**"How does the AI agent know about 911 / PSAP / NORS?"**
> The FCC scenario's agent system prompt includes deep 911 domain context (Selective Routers, MSAG/ALI, NG911 ESInet/ESRP/LIS, wireless E911 Phase II, NORS reportability thresholds). When Ch 7-9 fire, the agent prioritizes them and assesses FCC reportability automatically.

**"What if I want to model carrier-specific incidents?"**
> The fault parameters already carry `carrier_id`, `state`, `county`, `psap_id`, and `outage_id` fields. The scenario can be extended to inject carrier-specific patterns by overriding `get_rca_clues` and `get_fault_params` for the relevant channels.

**"Does Streams replace Logstash?"**
> For most parsing use cases — yes. Streams runs parsing inside Elasticsearch with the same Painless / Grok / Dissect processors. No separate cluster to operate, scale, or upgrade.

**"What gets deployed to Elastic for the FCC scenario?"**
> 6 workflows, 20 alert rules, 20 significant event definitions, 20 KB documents, 12 agent tools, an AI agent (`fcc-communications-analyst`), 6 data views, and the FCC executive dashboard — all auto-configured by the platform deployer.

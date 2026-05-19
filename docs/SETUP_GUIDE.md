# Setup Guide — Full Deployment from Scratch

This guide walks through every step to get the Elastic Observability Demo Platform running, from zero to a fully functional demo environment.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Elastic Cloud Setup](#2-elastic-cloud-setup)
3. [Clone and Install](#3-clone-and-install)
4. [Start the Application](#4-start-the-application)
5. [Deploy a Scenario](#5-deploy-a-scenario)
6. [Verify Telemetry](#6-verify-telemetry)
7. [Run the Demo](#7-run-the-demo)

---

## 1. Prerequisites

### Required

| Requirement | Details |
|-------------|---------|
| Server | EC2 instance (Amazon Linux 2023, Ubuntu, etc.) or any Linux host |
| Python | 3.11+ with pip |
| Elastic Cloud | A deployment with Elasticsearch and Kibana |
| Network | Outbound HTTPS to Elastic Cloud |

### Python Dependencies

```bash
pip install -r requirements.txt
```

Key packages: `fastapi`, `uvicorn`, `httpx[http2]`

### Elastic Cloud Requirements

The demo requires a Serverless or hosted Elastic Cloud deployment with:
- Elasticsearch endpoint URL
- Kibana endpoint URL
- An API key with sufficient permissions (see below)

---

## 2. Elastic Cloud Setup

### Create a Deployment

1. Sign up or log in at [cloud.elastic.co](https://cloud.elastic.co)
2. Create a new deployment (any cloud provider and region)
3. Wait for the deployment to become healthy

### Create an API Key

1. Open Kibana for your deployment
2. Go to **Stack Management** > **Security** > **API Keys**
3. Click **Create API Key**
4. Configure with broad permissions (the demo needs to create indices, data views, rules, workflows, agents, and dashboards):
   ```json
   {
     "superuser": true
   }
   ```
   Or for more restrictive access, the key needs write access to `logs-*`, `metrics-*`, `traces-*` indices, plus Kibana API access for dashboards, rules, workflows, agent builder, and saved objects.
5. Copy the Base64-encoded key

### Collect Your Endpoints

You need three URLs from your Elastic Cloud deployment:

| Value | Where to Find It | Example |
|-------|-------------------|---------|
| Elasticsearch URL | Cloud console > Manage > Elasticsearch endpoint | `https://my-deploy.es.us-central1.gcp.cloud.es.io:443` |
| Kibana URL | Cloud console > Manage > Kibana endpoint | `https://my-deploy.kb.us-central1.gcp.cloud.es.io:443` |
| OTLP Endpoint | Cloud console > Manage > OTLP endpoint | `https://my-deploy.apm.us-central1.gcp.cloud.es.io:443` |

---

## 3. Clone and Install

```bash
git clone <repo-url> elastic-launch-demo
cd elastic-launch-demo
pip install -r requirements.txt
```

> **Note:** No manual `.env` configuration is needed. You will enter your Elastic Cloud credentials through the web UI when deploying a scenario (step 5). The app persists them automatically.

---

## 4. Start the Application

The app runs as a single Python process:

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

To run in the background:

```bash
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 &
```

Verify it is running:

```bash
curl http://localhost:8080/health
```

Expected response:
```json
{"status": "ok"}
```

> **Note:** The app runs on port 8080. There is no hot-reload — restart the process after code changes by killing the existing process and re-launching.

---

## 5. Deploy a Scenario

### Option A: Web UI (Recommended)

1. Open `http://<your-host>/` in a browser
2. The **Scenario Selector** page shows all available industry verticals
3. Choose a scenario (e.g., "NOVA-7 Launch Control" for space)
4. Enter your Elastic Cloud credentials (auto-detected if previously configured)
5. Click **Launch**

The Python deployer will automatically:
- Test connectivity to Elastic Cloud
- Deploy 3 workflows (notification, remediation, escalation)
- Index 20 knowledge base documents (one per fault channel)
- Create 7-8 AI agent tools (ES|QL queries, service checks, etc.)
- Create the AI agent with a scenario-specific system prompt
- Create 20 significant event definitions (ES|QL rules)
- Create required data views (`logs*`, `traces-*`)
- Import the executive dashboard
- Create 20 alert rules with workflow actions

Progress is shown in real-time on the selector page.

### Option B: API

```bash
curl -X POST http://localhost/api/setup/launch \
  -H 'Content-Type: application/json' \
  -d '{
    "scenario_id": "space",
    "elastic_url": "https://your-deploy.es.cloud.es.io:443",
    "elastic_api_key": "your-key",
    "kibana_url": "https://your-deploy.kb.cloud.es.io:443",
    "otlp_endpoint": "https://your-deploy.apm.cloud.es.io:443",
    "otlp_api_key": "your-key"
  }'
```

Monitor progress:

```bash
curl http://localhost/api/setup/progress?deployment_id=<id>
```

---

## 6. Verify Telemetry

### Check Services Are Running

```bash
curl -s http://localhost/api/status | python3 -m json.tool
```

All 9 services should show NOMINAL status.

### Verify Data in Kibana

1. Open Kibana for your deployment
2. Go to **Discover**
3. Select the `logs-*` data view
4. You should see log entries with:
   - `service.name` — the 9 scenario services
   - `severity_text` — INFO, DEBUG, WARN
   - `body.text` — structured log messages
   - `host.name` — simulated hosts

### Verify Metrics

In Kibana Discover with the `metrics-*` data view, look for:
- `system.*` host metrics (CPU, memory, disk, network)
- `k8s.*` Kubernetes metrics (nodes, pods, containers)
- `nginx.*` web server metrics

### Verify Traces

In Kibana **APM** > **Services**, look for the scenario's services with distributed traces.

### Verify Elastic Resources

After deployment, check in Kibana:
- **Observability** > **Streams** — 20 significant event definitions
- **Security** > **Rules** — 20 alert rules
- **Dashboards** — Executive dashboard
- **AI Agent** — Configured agent with tools and KB

---

## 7. Run the Demo

1. Open the dashboard: `http://<host>/dashboard`
2. Open the chaos controller: `http://<host>/chaos`
3. Open Kibana in another tab
4. Follow the [Demo Script](DEMO_SCRIPT.md) talk track

### Quick Test

```bash
# Trigger a fault
curl -X POST http://<host>/api/chaos/trigger \
  -H 'Content-Type: application/json' \
  -d '{"channel": 2}'

# Check status
curl -s http://<host>/api/chaos/status/2

# Resolve
curl -X POST http://<host>/api/remediate/2
```


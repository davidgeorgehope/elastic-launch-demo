# Troubleshooting Guide

Common issues and solutions for the Elastic Observability Demo Platform.

---

## Table of Contents

1. [Application Startup](#1-application-startup)
2. [Scenario Deployment](#2-scenario-deployment)
3. [Telemetry Pipeline](#3-telemetry-pipeline)
4. [Dashboard Issues](#4-dashboard-issues)
5. [Chaos Controller](#5-chaos-controller)
6. [Elastic / Kibana](#6-elastic--kibana)
7. [AI Agent & Workflows](#7-ai-agent--workflows)
8. [Process Management](#8-process-management)

---

## 1. Application Startup

### App does not start

**Symptoms:** `uvicorn` exits with an error or the process does not respond.

**Check:**
```bash
# Is the process running?
ps aux | grep uvicorn

# Try starting manually to see errors
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

**Common causes:**

| Cause | Solution |
|-------|----------|
| Port 8080 already in use | Kill the existing process: `kill $(lsof -t -i:8080)` |
| Missing Python dependency | Run `pip install -r requirements.txt` |
| Missing credentials | Deploy a scenario via the web UI to configure Elastic credentials |
| Import error | Check for syntax errors in app/ or scenarios/ |

### Health check fails

**Symptoms:** `curl http://localhost:8080/health` returns connection refused.

```bash
# Is the process running?
ps aux | grep uvicorn

# Is it listening on port 8080?
ss -tlnp | grep :8080
```

---

## 2. Scenario Deployment

### Deployment fails at connectivity test

**Symptoms:** The deployer fails at step 1 "Test connectivity."

**Causes:**
- Wrong Elasticsearch URL — verify it includes the port (`:443` for cloud)
- Invalid API key — regenerate in Kibana > Stack Management > API Keys
- Network issue — ensure the server can reach Elastic Cloud (check firewall, proxy)

**Test manually:**
```bash
# Use the credentials shown in the scenario selector's auto-detect
curl -s -H "Authorization: ApiKey <your-api-key>" "<your-elastic-url>" | python3 -m json.tool
```

### Deployment fails at a specific step

**Symptoms:** The progress panel shows a specific step failed (e.g., "Deploy workflows" or "Create alert rules").

**Diagnosis:**
- Check the error detail shown in the progress panel
- Check the uvicorn process logs for stack traces
- Common issues:
  - **Workflows fail:** Missing `x-elastic-internal-origin: kibana` header (should be automatic)
  - **Alert rules fail:** API key lacks rule creation permissions
  - **Agent fails:** Agent Builder API not available (requires specific Elastic Cloud tier)
  - **Dashboard fails:** Missing `kbn-xsrf` header or invalid dashboard JSON

### Deployment hangs

**Symptoms:** Progress stops updating and never completes.

**Solutions:**
- Refresh the page and check `/api/setup/progress?deployment_id=<id>`
- Check the uvicorn logs for errors or timeouts
- The AI agent step can take 2-3 minutes — be patient
- If stuck, restart the app process and re-deploy

---

## 3. Telemetry Pipeline

### No data appears in Elastic

**Symptoms:** The app is running but Kibana shows no logs, metrics, or traces.

**Diagnosis:**

1. **Check the app logs** for OTLP send errors:
   ```bash
   # Look for OTLP errors in recent output
   # If running in background, check nohup.out or redirect logs
   ```

2. **Verify OTLP endpoint** — the OTLP endpoint should be the APM/OTLP endpoint from your Elastic Cloud console (not the Elasticsearch endpoint)

3. **Check credentials** — verify the API key is valid and has write permissions to `logs-*`, `metrics-*`, and `traces-*` indices

**Common causes:**

| Cause | Solution |
|-------|----------|
| Wrong OTLP endpoint | Use the OTLP endpoint from Cloud console, not the ES endpoint |
| Invalid API key | Verify the key is base64-encoded and has write permissions |
| Network blocked | Verify outbound HTTPS to Elastic Cloud is allowed |

### Data arrives but fields are missing

**Symptoms:** Logs appear in Kibana but attributes are missing or cannot be searched.

**Important:** OTLP data in Elastic uses passthrough mapping for most `attributes.*` fields. These fields are stored in `_source` but are NOT indexed — they cannot be searched, filtered, or aggregated.

**Indexed fields** (searchable):
- `body.text`, `severity_text`, `service.name`, `host.name`, `@timestamp`

**Not indexed** (stored only):
- `attributes.*`, most `resource.attributes.*` (except `service.name`)

**Workaround:** Use `body.text` for text search:
```
KQL: body.text: "FuelPressureException" AND severity_text: "ERROR"
```

---

## 4. Dashboard Issues

### Dashboard page is blank

**Symptoms:** Navigating to `/dashboard` shows a white page.

**Solutions:**
- Hard refresh (Ctrl+Shift+R)
- Check browser console (F12) for JavaScript errors
- Verify the app is running: `curl http://localhost/health`
- Check that `deployment_id` query parameter is present and valid

### Dashboard does not update in real time

**Symptoms:** Dashboard loads but service statuses are stale.

**Solutions:**
- Check the WebSocket connection in browser console — look for errors on `ws://<host>/ws/dashboard`
- If behind a reverse proxy, ensure it supports WebSocket upgrade
- Refresh the page to re-establish the WebSocket connection

### Dashboard shows wrong theme

**Symptoms:** Colors or terminology do not match the selected scenario.

**Solution:** The theme is injected based on the `deployment_id` parameter. Verify you are using the correct deployment URL from the scenario selector.

---

## 5. Chaos Controller

### Channel trigger has no effect

**Symptoms:** Triggering a channel does not change the dashboard or generate errors.

**Diagnosis:**
```bash
# Check channel status
curl -s http://localhost/api/chaos/status/2 | python3 -m json.tool

# Trigger and check response
curl -s -X POST http://localhost/api/chaos/trigger \
  -H 'Content-Type: application/json' \
  -d '{"channel": 2}' | python3 -m json.tool
```

**Common causes:**

| Cause | Solution |
|-------|----------|
| Channel already active | Resolve it first, then re-trigger |
| Invalid channel number | Must be 1-20 |
| No active deployment | Deploy a scenario first via the selector |

### Channel does not resolve

**Symptoms:** Calling resolve returns success but the channel stays active.

```bash
# Try the remediate endpoint
curl -X POST http://localhost/api/remediate/2

# Check status after
curl -s http://localhost/api/chaos/status/2
```

If the channel is stuck, restarting the app process will clear all channel states.

---

## 6. Elastic / Kibana

### Cannot find data in Discover

**Solutions:**

1. Make sure you have the right data view selected:
   - `logs-*` for logs (managed by OTLP integration)
   - `metrics-*` for metrics
   - `traces-*` for traces
   - `logs*` (custom, created by deployer) for executive dashboard

2. Check the time range includes "now"

3. Verify data exists:
   ```
   GET logs/_count
   ```

### Significant events / alert rules not firing

**Check:**
- Rules are enabled in Kibana > Rules
- Rule schedule is 1 minute (minimum)
- The ES|QL query matches actual field names
- Sufficient error volume has been generated (trigger a fault and wait 1-2 minutes)

### ES|QL query returns no results

**Debug approach — start broad, then narrow:**
```esql
FROM logs,logs.*
| WHERE severity_text == "ERROR"
| LIMIT 10

FROM logs,logs.*
| WHERE KQL("body.text: \"FuelPressureException\" AND severity_text: \"ERROR\"")
| LIMIT 10
```

> **Important:** Use `FROM logs,logs.*` (not just `FROM logs-*`) to include OTLP sub-streams. Use `KQL()` function for text matching on `body.text`.

### Executive dashboard shows no data

**Causes:**
- Missing custom data views (`logs*`, `traces-*`) — the deployer creates these, but verify
- Wrong time range — ensure it covers "now"
- TSDB gauge metrics require `average` for metric tiles and `max` for time series charts

---

## 7. AI Agent & Workflows

### Workflow does not trigger

**Symptoms:** Alert fires but no workflow execution appears.

**Check:**
- The alert rule has a workflow action configured (system connector `.workflows`)
- The workflow exists and has `type: alert` trigger
- Check workflow executions: Kibana > Workflows > Executions

### AI agent times out or fails

**Symptoms:** Workflow execution shows agent step failed.

**Common causes:**

| Cause | Solution |
|-------|----------|
| "Input is too long for requested model" | Search steps before the agent need to return less data — check `size` parameter |
| Agent step timeout | Agent investigation takes 2-3 minutes; ensure workflow timeout is sufficient |
| Agent tools return errors | Verify ES|QL tools work by testing the queries directly in Kibana Dev Tools |
| Agent not found | Re-deploy the scenario to recreate the agent |

### Email notification not sent

**Symptoms:** Workflow completes but no email arrives.

**Check:**
- Email step uses `Elastic-Cloud-SMTP` connector — this is a preconfigured system connector
- Verify the `user_email` is being extracted correctly from the event
- Check workflow execution details for the email step output

---

## 8. Process Management

### Restarting the app

The app does not have hot-reload. After code changes:

```bash
# Find and kill the existing process
kill $(lsof -t -i:8080)

# Restart
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 &
```

### App process dies unexpectedly

**Check:**
- Memory usage — 9 services + 7 generators can use significant memory
- Python exceptions — check nohup.out or stderr logs
- Disk space — SQLite store and Python cache need disk

### Multiple deployments

The platform supports multi-tenancy. Multiple scenarios can run simultaneously, each with their own deployment ID and telemetry pipeline. If you see unexpected behavior, check which deployments are active:

```bash
curl -s http://localhost/api/deployments | python3 -m json.tool
```

---

## Getting Help

If none of the above resolves your issue:

1. **Collect diagnostic info:**
   ```bash
   curl -s http://localhost/health
   curl -s http://localhost/api/status | python3 -m json.tool
   curl -s http://localhost/api/deployments | python3 -m json.tool
   ps aux | grep uvicorn
   python3 --version
   ```

2. **Check app logs** — look for Python tracebacks and OTLP errors

3. **Validate Elastic connectivity:**
   ```bash
   curl -s -H "Authorization: ApiKey <your-api-key>" "<your-elastic-url>/_cluster/health" | python3 -m json.tool
   ```

#!/usr/bin/env bash
#
# validate.sh — Comprehensive validation of the NOVA-7 Elastic Launch Demo.
#
# Checks ES/Kibana connectivity, data indices, agent, tools, dashboard,
# trace data, host metrics, and optional nginx/mysql log generator data.
#
# Uses only serverless-compatible APIs (no _find, no _get for saved objects).
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Load environment ──────────────────────────────────────────────────────────
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# Fall back to SQLite deployment store if env vars are empty
if [[ -z "${ELASTIC_URL:-}" || -z "${ELASTIC_API_KEY:-}" ]]; then
    eval "$(python3 -c "
import sqlite3, os
db = os.path.join('$SCRIPT_DIR', 'data', 'deployments.db')
if os.path.exists(db):
    r = sqlite3.connect(db).execute(\"SELECT elastic_url, elastic_api_key, kibana_url, otlp_endpoint, otlp_api_key FROM deployments WHERE status='active' LIMIT 1\").fetchone()
    if r:
        print(f'ELASTIC_URL={r[0]}')
        print(f'ELASTIC_API_KEY={r[1]}')
        print(f'KIBANA_URL={r[2]}')
        if r[3]: print(f'OTLP_ENDPOINT={r[3]}')
        if r[4]: print(f'OTLP_API_KEY={r[4]}')
" 2>/dev/null || true)"
fi

ELASTIC_URL="${ELASTIC_URL%/}"
KIBANA_URL="${KIBANA_URL%/}"

# ── Helpers ───────────────────────────────────────────────────────────────────
PASS=0
FAIL=0
WARN=0

pass() { echo -e "  \033[0;32mPASS\033[0m  $*"; PASS=$((PASS + 1)); }
fail() { echo -e "  \033[0;31mFAIL\033[0m  $*"; FAIL=$((FAIL + 1)); }
warn() { echo -e "  \033[1;33mWARN\033[0m  $*"; WARN=$((WARN + 1)); }
info() { echo -e "  \033[0;34mINFO\033[0m  $*"; }

es_get() {
    local path="$1"
    curl -s -w "\n%{http_code}" \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        -H "Content-Type: application/json" \
        "${ELASTIC_URL}${path}" 2>/dev/null
}

es_post() {
    local path="$1" body="${2:-}"
    curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        -H "Content-Type: application/json" \
        "${ELASTIC_URL}${path}" \
        ${body:+-d "$body"} 2>/dev/null
}

kb_get() {
    local path="$1"
    curl -s -w "\n%{http_code}" \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        -H "kbn-xsrf: true" \
        -H "x-elastic-internal-origin: kibana" \
        "${KIBANA_URL}${path}" 2>/dev/null
}

kb_post() {
    local path="$1" body="${2:-}"
    curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
        -H "Content-Type: application/json" \
        -H "kbn-xsrf: true" \
        -H "x-elastic-internal-origin: kibana" \
        "${KIBANA_URL}${path}" \
        ${body:+-d "$body"} 2>/dev/null
}

get_count() {
    local index="$1"
    local response
    response=$(es_post "/${index}/_count" '{}')
    local http_code
    http_code=$(echo "$response" | tail -1)
    local body
    body=$(echo "$response" | sed '$d')

    if [[ "$http_code" -ge 200 && "$http_code" -lt 300 ]]; then
        echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('count',0))" 2>/dev/null || echo "0"
    else
        echo "-1"
    fi
}

echo ""
echo "============================================================"
echo "   NOVA-7 Launch Demo — Validation Report"
echo "============================================================"
echo ""

# ── 1. Environment Variables ─────────────────────────────────────────────────
echo "--- Environment ---"
for var in ELASTIC_URL ELASTIC_API_KEY KIBANA_URL OTLP_ENDPOINT OTLP_API_KEY; do
    if [[ -n "${!var:-}" ]]; then
        pass "$var is set"
    else
        fail "$var is NOT set"
    fi
done
echo ""

# ── 2. Cluster Connectivity ──────────────────────────────────────────────────
echo "--- Elasticsearch Connectivity ---"
es_response=$(es_get "/")
es_code=$(echo "$es_response" | tail -1)
es_body=$(echo "$es_response" | sed '$d')

if [[ "$es_code" -ge 200 && "$es_code" -lt 300 ]]; then
    cluster_name=$(echo "$es_body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cluster_name','?'))" 2>/dev/null || echo "?")
    pass "Elasticsearch reachable (cluster: $cluster_name)"
else
    fail "Elasticsearch unreachable (HTTP $es_code)"
fi
echo ""

echo "--- Kibana Connectivity ---"
kb_response=$(kb_get "/api/status")
kb_code=$(echo "$kb_response" | tail -1)

if [[ "$kb_code" -ge 200 && "$kb_code" -lt 300 ]]; then
    pass "Kibana reachable (HTTP $kb_code)"
else
    fail "Kibana unreachable (HTTP $kb_code)"
fi
echo ""

# ── 3. OTel Log Data ─────────────────────────────────────────────────────────
echo "--- OTel Log Data ---"
otel_count=$(get_count "logs")
if [[ "$otel_count" -gt 0 ]]; then
    pass "logs has data ($otel_count docs)"
elif [[ "$otel_count" -eq 0 ]]; then
    warn "logs exists but is empty (run the demo app first)"
else
    warn "logs index not found (run the demo app first)"
fi
echo ""

# ── 4. Knowledge Base ────────────────────────────────────────────────────────
echo "--- Knowledge Base ---"
kb_count=$(get_count "nova7-knowledge-base")
if [[ "$kb_count" -ge 5 ]]; then
    pass "nova7-knowledge-base has $kb_count documents"
elif [[ "$kb_count" -gt 0 ]]; then
    warn "nova7-knowledge-base has only $kb_count documents (expected >= 5)"
elif [[ "$kb_count" -eq 0 ]]; then
    fail "nova7-knowledge-base is empty (run setup-agent-builder.sh)"
else
    fail "nova7-knowledge-base index not found (run setup-agent-builder.sh)"
fi
echo ""

# ── 5. Agent Builder ─────────────────────────────────────────────────────────
echo "--- Agent Builder ---"

# Check agents
agents_response=$(kb_get "/api/agent_builder/agents")
agents_code=$(echo "$agents_response" | tail -1)
agents_body=$(echo "$agents_response" | sed '$d')

if [[ "$agents_code" -ge 200 && "$agents_code" -lt 300 ]]; then
    agent_found=$(echo "$agents_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
agents = data if isinstance(data, list) else data.get('results', data.get('agents', data.get('data', [])))
found = any('nova7' in str(a).lower() or 'NOVA' in str(a) for a in (agents if isinstance(agents, list) else [agents]))
print('yes' if found else 'no')
" 2>/dev/null || echo "unknown")

    if [[ "$agent_found" == "yes" ]]; then
        pass "NOVA-7 agent found in Agent Builder"
    else
        warn "Agent Builder reachable but NOVA-7 agent not found"
    fi
else
    warn "Agent Builder API not accessible (HTTP $agents_code) — may need manual setup"
fi

# Check tools (filter for non-readonly custom tools)
tools_response=$(kb_get "/api/agent_builder/tools")
tools_code=$(echo "$tools_response" | tail -1)
tools_body=$(echo "$tools_response" | sed '$d')

if [[ "$tools_code" -ge 200 && "$tools_code" -lt 300 ]]; then
    tool_count=$(echo "$tools_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tools = data if isinstance(data, list) else data.get('results', data.get('tools', data.get('data', [])))
custom = [t for t in tools if not t.get('readonly', False) and not t.get('is_default', False)]
print(len(custom))
" 2>/dev/null || echo "0")

    if [[ "$tool_count" -ge 7 ]]; then
        pass "Agent Builder has $tool_count custom tools (>= 7 expected)"
    elif [[ "$tool_count" -gt 0 ]]; then
        warn "Agent Builder has $tool_count custom tools (expected >= 7)"
    else
        warn "No custom tools found in Agent Builder"
    fi
else
    warn "Agent Builder tools API not accessible (HTTP $tools_code)"
fi

# Check agent instructions for body.text field name warnings
agent_instructions=$(echo "$agents_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
agents = data if isinstance(data, list) else data.get('results', data.get('agents', data.get('data', [])))
for a in agents:
    if 'nova' in a.get('name','').lower() or 'nova' in a.get('id','').lower():
        print(a.get('configuration', {}).get('instructions', ''))
        break
" 2>/dev/null || echo "")

if echo "$agent_instructions" | grep -q "body.text" && echo "$agent_instructions" | grep -q "NEVER"; then
    pass "Agent prompt has body.text field name warnings (prevents Unknown column [body] bug)"
elif [[ -n "$agent_instructions" ]]; then
    fail "Agent prompt MISSING body.text warnings — will cause ES|QL Unknown column [body] errors"
else
    warn "Could not check agent instructions"
fi

# Check ES|QL tool descriptions mention body.text
if [[ "$tools_code" -ge 200 && "$tools_code" -lt 300 ]]; then
    esql_tools_bodytext=$(echo "$tools_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tools = data if isinstance(data, list) else data.get('results', data.get('tools', data.get('data', [])))
esql_ids = ['esql_telemetry_query', 'search_subsystem_health', 'check_service_status', 'trace_anomaly_propagation', 'launch_safety_assessment']
missing = []
for t in tools:
    if t.get('id', '') in esql_ids:
        if 'body.text' not in t.get('description', ''):
            missing.append(t['id'])
print(','.join(missing) if missing else 'all_ok')
" 2>/dev/null || echo "unknown")

    if [[ "$esql_tools_bodytext" == "all_ok" ]]; then
        pass "All ES|QL tools mention body.text in descriptions"
    else
        fail "ES|QL tools missing body.text warning: $esql_tools_bodytext"
    fi
fi
echo ""

# ── 6. Workflows ─────────────────────────────────────────────────────────────
echo "--- Workflows ---"

wf_search_response=$(kb_post "/api/workflows/search" '{"page":1,"size":100}')
wf_search_code=$(echo "$wf_search_response" | tail -1)
wf_search_body=$(echo "$wf_search_response" | sed '$d')

if [[ "$wf_search_code" -ge 200 && "$wf_search_code" -lt 300 ]]; then
    # Check all 3 NOVA-7 workflows exist and are valid
    wf_check=$(echo "$wf_search_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
expected = {
    'Significant Event Notification': {'found': False, 'valid': False, 'id': '', 'has_alert_trigger': False},
    'Remediation Action': {'found': False, 'valid': False, 'id': '', 'has_callback_url': False},
    'Escalation and Hold Management': {'found': False, 'valid': False, 'id': ''},
}
for item in items:
    name = item.get('name', '')
    for key in expected:
        if key in name:
            expected[key]['found'] = True
            expected[key]['valid'] = item.get('valid', False)
            expected[key]['id'] = item.get('id', '')
            defn = item.get('definition', {}) or {}
            triggers = defn.get('triggers', [])
            if key == 'Significant Event Notification':
                expected[key]['has_alert_trigger'] = any(t.get('type') == 'alert' for t in triggers)
            if key == 'Remediation Action':
                inputs = defn.get('inputs', [])
                expected[key]['has_callback_url'] = any(i.get('name') == 'callback_url' for i in inputs)
for key, val in expected.items():
    print(f'{key}|{val[\"found\"]}|{val[\"valid\"]}|{val[\"id\"]}|{json.dumps(val)}')
" 2>/dev/null || true)

    while IFS='|' read -r wf_name wf_found wf_valid wf_id wf_json; do
        if [[ -z "$wf_name" ]]; then continue; fi
        if [[ "$wf_found" == "True" && "$wf_valid" == "True" ]]; then
            pass "Workflow '$wf_name' exists and is valid (id: ${wf_id})"
        elif [[ "$wf_found" == "True" ]]; then
            fail "Workflow '$wf_name' exists but is NOT valid"
        else
            fail "Workflow '$wf_name' NOT found"
        fi
    done <<< "$wf_check"

    # Check Significant Event Notification has alert trigger
    sen_alert=$(echo "$wf_search_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
for item in items:
    if 'Significant Event Notification' in item.get('name', ''):
        defn = item.get('definition', {}) or {}
        triggers = defn.get('triggers', [])
        print('yes' if any(t.get('type') == 'alert' for t in triggers) else 'no')
        break
" 2>/dev/null || echo "unknown")

    if [[ "$sen_alert" == "yes" ]]; then
        pass "Notification workflow has 'alert' trigger type"
    else
        fail "Notification workflow MISSING 'alert' trigger — alerts won't trigger it"
    fi

    # Check Remediation Action extracts callback_url from event_name
    rem_callback=$(echo "$wf_search_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
for item in items:
    if 'Remediation Action' in item.get('name', ''):
        yaml_str = item.get('yaml', '')
        if 'event_meta.callback_url' in yaml_str and 'json_parse' in yaml_str:
            print('yes'); break
        print('no'); break
" 2>/dev/null || echo "unknown")

    if [[ "$rem_callback" == "yes" ]]; then
        pass "Remediation workflow extracts callback_url from event_name"
    else
        fail "Remediation workflow MISSING callback_url extraction from event_name"
    fi

    # Check Notification workflow has email step with Elastic-Cloud-SMTP
    notif_email=$(echo "$wf_search_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
for item in items:
    if 'Significant Event Notification' in item.get('name', ''):
        yaml_text = item.get('yaml', '')
        has_email_step = 'type: email' in yaml_text
        has_smtp = 'Elastic-Cloud-SMTP' in yaml_text
        print('yes' if (has_email_step and has_smtp) else 'no')
        break
" 2>/dev/null || echo "unknown")

    if [[ "$notif_email" == "yes" ]]; then
        pass "Notification workflow has email step with Elastic-Cloud-SMTP connector"
    else
        fail "Notification workflow MISSING email step with Elastic-Cloud-SMTP"
    fi

    # Check Notification workflow uses var[0] access pattern for parsed event_meta
    notif_var0=$(echo "$wf_search_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
for item in items:
    if 'Significant Event Notification' in item.get('name', ''):
        yaml_text = item.get('yaml', '')
        has_var0 = 'var[0].event_meta' in yaml_text
        has_json_parse = 'json_parse' in yaml_text
        print('yes' if (has_var0 and has_json_parse) else 'no')
        break
" 2>/dev/null || echo "unknown")

    if [[ "$notif_var0" == "yes" ]]; then
        pass "Notification workflow uses var[0].event_meta access + json_parse"
    else
        fail "Notification workflow MISSING var[0] access pattern — email extraction will fail"
    fi

    # Check Notification workflow enrich_context uses wide time window (>= 15m)
    notif_window=$(echo "$wf_search_body" | python3 -c "
import sys, json, re
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
for item in items:
    if 'Significant Event Notification' in item.get('name', ''):
        yaml_text = item.get('yaml', '')
        m = re.search(r'gte:\s*[\"'']?now-(\d+)m[\"'']?', yaml_text)
        if m:
            minutes = int(m.group(1))
            print('yes' if minutes >= 15 else f'no:{minutes}m')
        else:
            print('no:unknown')
        break
" 2>/dev/null || echo "unknown")

    if [[ "$notif_window" == yes* ]]; then
        pass "Notification workflow enrich_context uses >= 15m time window"
    else
        fail "Notification workflow time window too narrow ($notif_window) — may miss logs"
    fi

    # Check Remediation workflow uses /api/chaos/resolve endpoint
    rem_resolve=$(echo "$wf_search_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
for item in items:
    if 'Remediation Action' in item.get('name', ''):
        yaml_text = item.get('yaml', '')
        print('yes' if '/api/chaos/resolve' in yaml_text else 'no')
        break
" 2>/dev/null || echo "unknown")

    if [[ "$rem_resolve" == "yes" ]]; then
        pass "Remediation workflow uses /api/chaos/resolve endpoint"
    else
        fail "Remediation workflow MISSING /api/chaos/resolve — remediation won't work"
    fi

    # Check all workflows are enabled
    wf_disabled=$(echo "$wf_search_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
disabled = [i.get('name','') for i in items if 'NOVA-7' in i.get('name','') and not i.get('enabled', True)]
print(','.join(disabled) if disabled else 'all_enabled')
" 2>/dev/null || echo "unknown")

    if [[ "$wf_disabled" == "all_enabled" ]]; then
        pass "All NOVA-7 workflows are enabled"
    else
        fail "Disabled workflows: $wf_disabled"
    fi
else
    fail "Workflows API not accessible (HTTP $wf_search_code)"
fi
echo ""

# ── 6b. Alert Rules ─────────────────────────────────────────────────────────
echo "--- Alert Rules ---"

alert_response=$(kb_get "/api/alerting/rules/_find?per_page=100&filter=alert.attributes.tags:nova7")
alert_code=$(echo "$alert_response" | tail -1)
alert_body=$(echo "$alert_response" | sed '$d')

if [[ "$alert_code" -ge 200 && "$alert_code" -lt 300 ]]; then
    alert_check=$(echo "$alert_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
rules = data.get('data', [])
nova7_rules = [r for r in rules if r.get('name', '').startswith('NOVA-7 CH')]
wf_rules = [r for r in nova7_rules if any(a.get('connector_type_id') == '.workflows' for a in r.get('actions', []))]
webhook_rules = [r for r in nova7_rules if any(a.get('connector_type_id') == '.webhook' for a in r.get('actions', []))]
print(f'{len(nova7_rules)}|{len(wf_rules)}|{len(webhook_rules)}')
" 2>/dev/null || echo "0|0|0")

    IFS='|' read -r total_rules wf_rules webhook_rules <<< "$alert_check"

    if [[ "$total_rules" -ge 20 ]]; then
        pass "Alert rules: $total_rules NOVA-7 rules found (expected 20)"
    elif [[ "$total_rules" -gt 0 ]]; then
        warn "Alert rules: only $total_rules found (expected 20)"
    else
        fail "No NOVA-7 alert rules found (run setup-alerting.sh)"
    fi

    if [[ "$wf_rules" -ge 20 ]]; then
        pass "All $wf_rules rules use native .workflows connector"
    elif [[ "$wf_rules" -gt 0 ]]; then
        warn "Only $wf_rules rules use .workflows connector ($webhook_rules still on .webhook)"
    else
        fail "No rules using .workflows connector — run setup-alerting.sh"
    fi
else
    warn "Alerting API not accessible (HTTP $alert_code)"
fi
echo ""

# ── 6c. E2E Workflow Test — Trigger fault and verify event_name in logs ─────
echo "--- E2E: Fault Trigger + event_name in Logs ---"

# Trigger a fault on channel 20 (Range Safety) with test metadata
e2e_resolve=$(curl -s -X POST http://localhost/api/chaos/resolve -H "Content-Type: application/json" -d '{"channel": 20}' 2>/dev/null || echo "")
sleep 2
e2e_trigger=$(curl -s -X POST http://localhost/api/chaos/trigger \
  -H "Content-Type: application/json" \
  -d '{"channel": 20, "callback_url": "http://ec2-3-15-164-206.us-east-2.compute.amazonaws.com", "user_email": "david.hope@elastic.co"}' 2>/dev/null || echo "")

if echo "$e2e_trigger" | grep -q '"status":"triggered"' 2>/dev/null; then
    pass "E2E: Fault triggered on channel 20 with callback_url + user_email"

    # Wait for logs to be ingested
    sleep 15

    # Check that event_name field has our metadata in recent logs
    e2e_search=$(es_post "/logs/_search" '{"size":1,"query":{"bool":{"filter":[{"range":{"@timestamp":{"gte":"now-1m"}}},{"match_phrase":{"body.text":"TrackingLossException"}},{"term":{"severity_text":"ERROR"}}]}},"_source":["event_name"]}')
    e2e_search_code=$(echo "$e2e_search" | tail -1)
    e2e_search_body=$(echo "$e2e_search" | sed '$d')

    if [[ "$e2e_search_code" -ge 200 && "$e2e_search_code" -lt 300 ]]; then
        e2e_event_name=$(echo "$e2e_search_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
hits = data.get('hits', {}).get('hits', [])
if hits:
    en = hits[0].get('_source', {}).get('event_name', '')
    print(en)
else:
    print('')
" 2>/dev/null || echo "")

        if echo "$e2e_event_name" | grep -q "callback_url" 2>/dev/null && echo "$e2e_event_name" | grep -q "user_email" 2>/dev/null; then
            pass "E2E: event_name contains callback_url + user_email metadata"
        elif [[ -n "$e2e_event_name" ]]; then
            warn "E2E: event_name present but may be missing fields: $e2e_event_name"
        else
            fail "E2E: event_name is empty — metadata not being injected into fault logs"
        fi
    else
        warn "E2E: Could not search logs (HTTP $e2e_search_code)"
    fi

    # Resolve the test fault
    curl -s -X POST http://localhost/api/chaos/resolve -H "Content-Type: application/json" -d '{"channel": 20}' > /dev/null 2>&1
else
    warn "E2E: Could not trigger fault (app not running?)"
fi
echo ""

# ── 6d. E2E Workflow Execution Tests — Actually run workflows and check status ──
echo "--- E2E: Workflow Execution Tests ---"

# Find workflow IDs
wf_search_response=$(kb_post "/api/workflows/search" '{"page":1,"size":100}')
wf_search_code=$(echo "$wf_search_response" | tail -1)
wf_search_body=$(echo "$wf_search_response" | sed '$d')

if [[ "$wf_search_code" -ge 200 && "$wf_search_code" -lt 300 ]]; then
    # Extract workflow IDs by name
    escalation_wf_id=$(echo "$wf_search_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for w in data.get('results', []):
    if 'Escalation' in w.get('name', ''):
        print(w['id']); break
" 2>/dev/null || echo "")

    remediation_wf_id=$(echo "$wf_search_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for w in data.get('results', []):
    if 'Remediation' in w.get('name', ''):
        print(w['id']); break
" 2>/dev/null || echo "")

    # --- Test Escalation Workflow ---
    if [[ -n "$escalation_wf_id" ]]; then
        esc_run_response=$(kb_post "/api/workflows/${escalation_wf_id}/run" \
            '{"inputs":{"action":"escalate","channel":1,"severity":"ADVISORY","justification":"Validation test - automated escalation check","hold_id":"","investigation_summary":""}}')
        esc_run_code=$(echo "$esc_run_response" | tail -1)
        esc_run_body=$(echo "$esc_run_response" | sed '$d')

        if [[ "$esc_run_code" -ge 200 && "$esc_run_code" -lt 300 ]]; then
            esc_exec_id=$(echo "$esc_run_body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('workflowExecutionId',''))" 2>/dev/null || echo "")
            if [[ -n "$esc_exec_id" ]]; then
                # Wait for completion (escalation is fast — no wait step)
                sleep 12
                esc_status_response=$(kb_get "/api/workflowExecutions/${esc_exec_id}")
                esc_status_code=$(echo "$esc_status_response" | tail -1)
                esc_status_body=$(echo "$esc_status_response" | sed '$d')
                esc_status=$(echo "$esc_status_body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")

                if [[ "$esc_status" == "completed" ]]; then
                    pass "E2E: Escalation workflow executed successfully (status: completed)"
                elif [[ "$esc_status" == "running" ]]; then
                    warn "E2E: Escalation workflow still running after 12s"
                else
                    esc_err=$(echo "$esc_status_body" | python3 -c "
import sys,json
d=json.load(sys.stdin)
e=d.get('error',{})
print(e.get('message','') if isinstance(e,dict) else str(e))
" 2>/dev/null || echo "unknown error")
                    fail "E2E: Escalation workflow failed (status: $esc_status, error: $esc_err)"
                fi
            else
                fail "E2E: Escalation workflow run returned no execution ID"
            fi
        else
            fail "E2E: Escalation workflow run failed (HTTP $esc_run_code)"
        fi
    else
        warn "E2E: Escalation workflow not found — cannot test execution"
    fi

    # --- Test Remediation Workflow ---
    # Remediation needs an active fault with callback_url in event_name logs.
    # Trigger fault on channel 2 first, wait for logs, then run workflow.
    if [[ -n "$remediation_wf_id" ]]; then
        # Get public hostname for callback URL
        REM_TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" 2>/dev/null || echo "")
        REM_HOST=""
        if [[ -n "$REM_TOKEN" ]]; then
            REM_HOST=$(curl -s -H "X-aws-ec2-metadata-token: $REM_TOKEN" http://169.254.169.254/latest/meta-data/public-hostname 2>/dev/null || echo "")
        fi
        if [[ -z "$REM_HOST" ]]; then
            REM_HOST=$(hostname -I | awk '{print $1}')
        fi
        REM_CALLBACK="http://${REM_HOST}"

        # Resolve any existing fault, then trigger fresh
        curl -s -X POST http://localhost/api/chaos/resolve -H "Content-Type: application/json" -d '{"channel": 2}' > /dev/null 2>&1
        sleep 1
        rem_trigger=$(curl -s -X POST http://localhost/api/chaos/trigger \
            -H "Content-Type: application/json" \
            -d "{\"channel\": 2, \"callback_url\": \"${REM_CALLBACK}\", \"user_email\": \"validate@nova7.test\"}" 2>/dev/null || echo "")

        if echo "$rem_trigger" | grep -q '"status":"triggered"' 2>/dev/null; then
            # Wait for fault logs with event_name to be ingested
            sleep 12

            rem_run_response=$(kb_post "/api/workflows/${remediation_wf_id}/run" \
                '{"inputs":{"error_type":"FuelPressureException","channel":2,"action_type":"reset_fuel_system","target_service":"fuel-system","justification":"Validation test - automated remediation check","dry_run":false}}')
        rem_run_code=$(echo "$rem_run_response" | tail -1)
        rem_run_body=$(echo "$rem_run_response" | sed '$d')

        if [[ "$rem_run_code" -ge 200 && "$rem_run_code" -lt 300 ]]; then
            rem_exec_id=$(echo "$rem_run_body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('workflowExecutionId',''))" 2>/dev/null || echo "")
            if [[ -n "$rem_exec_id" ]]; then
                # Remediation has a 30s wait step — need ~45s total
                sleep 45
                rem_status_response=$(kb_get "/api/workflowExecutions/${rem_exec_id}")
                rem_status_code=$(echo "$rem_status_response" | tail -1)
                rem_status_body=$(echo "$rem_status_response" | sed '$d')
                rem_status=$(echo "$rem_status_body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")

                if [[ "$rem_status" == "completed" ]]; then
                    pass "E2E: Remediation workflow executed successfully (status: completed)"
                elif [[ "$rem_status" == "running" ]]; then
                    warn "E2E: Remediation workflow still running after 45s (has 30s wait step)"
                else
                    rem_err=$(echo "$rem_status_body" | python3 -c "
import sys,json
d=json.load(sys.stdin)
e=d.get('error',{})
print(e.get('message','') if isinstance(e,dict) else str(e))
" 2>/dev/null || echo "unknown error")
                    fail "E2E: Remediation workflow failed (status: $rem_status, error: $rem_err)"
                fi
            else
                fail "E2E: Remediation workflow run returned no execution ID"
            fi
        else
            fail "E2E: Remediation workflow run failed (HTTP $rem_run_code)"
        fi
        else
            warn "E2E: Could not trigger fault on channel 2 for remediation test (app not running?)"
        fi
    else
        warn "E2E: Remediation workflow not found — cannot test execution"
    fi
else
    warn "E2E: Could not list workflows (HTTP $wf_search_code) — skipping execution tests"
fi
echo ""

# ── 7. Dashboard (serverless-compatible: uses _export, NOT _get/_find) ───────
echo "--- Executive Dashboard ---"
dash_response=$(kb_post "/api/saved_objects/_export" '{"objects":[{"type":"dashboard","id":"nova7-exec-dashboard"}],"includeReferencesDeep":false}')
dash_code=$(echo "$dash_response" | tail -1)
dash_body=$(echo "$dash_response" | sed '$d')

if [[ "$dash_code" -ge 200 && "$dash_code" -lt 300 ]]; then
    # Check the export response contains the dashboard (not just an error export)
    if echo "$dash_body" | grep -q "nova7-exec-dashboard" 2>/dev/null; then
        pass "NOVA-7 Executive Dashboard exists"
        info "URL: ${KIBANA_URL}/app/dashboards#/view/nova7-exec-dashboard"
    else
        warn "Export returned but dashboard ID not confirmed"
    fi
else
    fail "NOVA-7 Executive Dashboard not found (run setup-exec-dashboard.sh)"
fi
echo ""

# ── 7. Significant Events (Streams Queries) ─────────────────────────────────
echo "--- Significant Events (Streams Queries) ---"

# Discover stream name (same logic as setup-significant-events.sh)
se_stream=""
se_streams_out=$(kb_get "/api/streams" 2>/dev/null) || true
se_streams_code=$(echo "$se_streams_out" | tail -1)
se_streams_body=$(echo "$se_streams_out" | sed '$d')

if [[ "$se_streams_code" -ge 200 && "$se_streams_code" -lt 300 ]] && [[ -n "$se_streams_body" ]]; then
    se_stream=$(echo "$se_streams_body" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    streams = data if isinstance(data, list) else data.get('streams', data.get('results', data.get('data', [])))
    for s in streams:
        name = s.get('name', s) if isinstance(s, dict) else s
        if name in ('logs.otel', 'logs'):
            print(name); exit(0)
except:
    pass
" 2>/dev/null || true)
fi

if [[ -z "$se_stream" ]]; then
    se_stream="logs.otel"
fi

se_response=$(kb_get "/api/streams/${se_stream}/queries")
se_code=$(echo "$se_response" | tail -1)
se_body=$(echo "$se_response" | sed '$d')

if [[ "$se_code" -ge 200 && "$se_code" -lt 300 ]]; then
    se_count=$(echo "$se_body" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    queries = data if isinstance(data, list) else data.get('queries', data.get('results', data.get('data', [])))
    count = sum(1 for q in queries if q.get('id', '').startswith('nova7-se-'))
    print(count)
except:
    print('0')
" 2>/dev/null || echo "0")

    if [[ "$se_count" -ge 20 ]]; then
        pass "Significant Events: $se_count nova7-se-* queries on stream '${se_stream}'"
    elif [[ "$se_count" -gt 0 ]]; then
        warn "Significant Events: only $se_count queries found (expected >= 20)"
    else
        warn "No nova7-se-* queries found on stream '${se_stream}' (run setup-significant-events.sh)"
    fi
else
    warn "Streams Queries API not accessible (HTTP $se_code) — Streams may not be enabled"
fi
echo ""

# ── 8. Trace Data ─────────────────────────────────────────────────────────────
echo "--- Trace Data (APM Service Map) ---"

# Check for traces-* indices
traces_response=$(es_get "/_cat/indices/traces-*?format=json&h=index,docs.count")
traces_code=$(echo "$traces_response" | tail -1)
traces_body=$(echo "$traces_response" | sed '$d')

if [[ "$traces_code" -ge 200 && "$traces_code" -lt 300 ]]; then
    trace_indices=$(echo "$traces_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
total_docs = sum(int(idx.get('docs.count', 0)) for idx in data)
print(f'{len(data)} indices, {total_docs} docs')
" 2>/dev/null || echo "unknown")

    if echo "$traces_body" | python3 -c "import sys,json; data=json.load(sys.stdin); exit(0 if any(int(i.get('docs.count',0))>0 for i in data) else 1)" 2>/dev/null; then
        pass "Trace data exists ($trace_indices)"
    else
        info "Trace indices exist but are empty (run: python3 log_generators/trace_generator.py)"
    fi
else
    info "No traces-* indices found (run: python3 log_generators/trace_generator.py)"
fi
echo ""

# ── 9. Host Metrics ──────────────────────────────────────────────────────────
echo "--- Host Metrics (Infrastructure UI) ---"

# Check for metrics-* indices with system.* metric names
metrics_response=$(es_get "/_cat/indices/metrics-*?format=json&h=index,docs.count")
metrics_code=$(echo "$metrics_response" | tail -1)
metrics_body=$(echo "$metrics_response" | sed '$d')

if [[ "$metrics_code" -ge 200 && "$metrics_code" -lt 300 ]]; then
    metrics_info=$(echo "$metrics_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
total_docs = sum(int(idx.get('docs.count', 0)) for idx in data)
print(f'{len(data)} indices, {total_docs} docs')
" 2>/dev/null || echo "unknown")

    if echo "$metrics_body" | python3 -c "import sys,json; data=json.load(sys.stdin); exit(0 if any(int(i.get('docs.count',0))>0 for i in data) else 1)" 2>/dev/null; then
        pass "Metrics data exists ($metrics_info)"
    else
        info "Metrics indices exist but are empty (run: python3 log_generators/host_metrics_generator.py)"
    fi
else
    info "No metrics-* indices found (run: python3 log_generators/host_metrics_generator.py)"
fi
echo ""

# ── 10. Nginx Log Data ───────────────────────────────────────────────────────
echo "--- Nginx Log Generator Data ---"
nginx_access_count=$(get_count "logs-nginx.access.otel-default")
nginx_error_count=$(get_count "logs-nginx.error.otel-default")

if [[ "$nginx_access_count" -gt 0 ]]; then
    pass "logs-nginx.access.otel-default has $nginx_access_count docs"
else
    info "logs-nginx.access.otel-default not found (start: python3 log_generators/nginx_log_generator.py)"
fi

if [[ "$nginx_error_count" -gt 0 ]]; then
    pass "logs-nginx.error.otel-default has $nginx_error_count docs"
else
    info "logs-nginx.error.otel-default not yet populated"
fi
echo ""

# ── 11. MySQL Log Data ───────────────────────────────────────────────────────
echo "--- MySQL Log Generator Data ---"
mysql_slow_count=$(get_count "logs-mysql.slowlog.otel-default")
mysql_error_count=$(get_count "logs-mysql.error.otel-default")

if [[ "$mysql_slow_count" -gt 0 ]]; then
    pass "logs-mysql.slowlog.otel-default has $mysql_slow_count docs"
else
    info "logs-mysql.slowlog.otel-default not found (start: python3 log_generators/mysql_log_generator.py)"
fi

if [[ "$mysql_error_count" -gt 0 ]]; then
    pass "logs-mysql.error.otel-default has $mysql_error_count docs"
else
    info "logs-mysql.error.otel-default not yet populated"
fi
echo ""

# ── Summary ───────────────────────────────────────────────────────────────────
echo "============================================================"
echo "   Results: ${PASS} PASS / ${FAIL} FAIL / ${WARN} WARN"
echo "============================================================"

if [[ "$FAIL" -gt 0 ]]; then
    echo ""
    echo "Some checks failed. Run the setup scripts to fix:"
    echo "  ./setup-all.sh"
    exit 1
elif [[ "$WARN" -gt 0 ]]; then
    echo ""
    echo "Some checks returned warnings. This is expected if generators"
    echo "haven't been started yet or if certain APIs are not available."
    exit 0
else
    echo ""
    echo "All checks passed!"
    exit 0
fi

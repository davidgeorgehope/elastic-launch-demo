#!/usr/bin/env bash
#
# validate.sh — Validate the Elastic Launch Demo deployment.
#
# Checks ES/Kibana connectivity, data indices, agent, tools, dashboard,
# trace data, host metrics, and optional nginx/mysql log generator data.
#
# Uses only serverless-compatible APIs (no _find, no _get for saved objects).
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Load .env if present ──────────────────────────────────────────────────────
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# ── Load connectivity vars + scenario info from the deployment DB ─────────────
_db_out=$(python3 -c "
import sqlite3, os, sys
db = os.path.join('$SCRIPT_DIR', 'data', 'deployments.db')
if not os.path.exists(db):
    exit(0)
r = sqlite3.connect(db).execute(
    \"SELECT scenario_id, elastic_url, elastic_api_key, kibana_url, otlp_endpoint, otlp_api_key \"
    \"FROM deployments WHERE status='active' LIMIT 1\"
).fetchone()
if not r:
    exit(0)
sid, eu, ak, ku, oe, ok_ = r
if eu:  print(f'_DB_EU={eu}')
if ak:  print(f'_DB_AK={ak}')
if ku:  print(f'_DB_KU={ku}')
if oe:  print(f'_DB_OE={oe}')
if ok_: print(f'_DB_OK={ok_}')
sys.path.insert(0, '$SCRIPT_DIR')
try:
    from scenarios import get_scenario
    s = get_scenario(sid)
    print(f'SCENARIO_NS={s.namespace}')
    print(f'SCENARIO_NAME={s.scenario_name}')
    agent_id = s.agent_config.get('id', s.namespace + '-analyst')
    print(f'AGENT_ID={agent_id}')
except Exception:
    pass
" 2>/dev/null || true)
eval "$_db_out"

ELASTIC_URL="${ELASTIC_URL:-${_DB_EU:-}}"
ELASTIC_API_KEY="${ELASTIC_API_KEY:-${_DB_AK:-}}"
KIBANA_URL="${KIBANA_URL:-${_DB_KU:-}}"
OTLP_ENDPOINT="${OTLP_ENDPOINT:-${_DB_OE:-}}"
OTLP_API_KEY="${OTLP_API_KEY:-${_DB_OK:-}}"
SCENARIO_NS="${SCENARIO_NS:-banking}"
SCENARIO_NAME="${SCENARIO_NAME:-Banking}"
AGENT_ID="${AGENT_ID:-${SCENARIO_NS}-analyst}"

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
echo "   Launch Demo — Validation Report (${SCENARIO_NAME})"
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
info "Scenario: ${SCENARIO_NAME} (ns: ${SCENARIO_NS}, agent: ${AGENT_ID})"
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
    warn "logs exists but is empty (start the demo app generators)"
else
    warn "logs index not found (start the demo app generators)"
fi
echo ""

# ── 4. Knowledge Base ────────────────────────────────────────────────────────
echo "--- Knowledge Base ---"
kb_count=$(get_count "${SCENARIO_NS}-knowledge-base")
if [[ "$kb_count" -ge 5 ]]; then
    pass "${SCENARIO_NS}-knowledge-base has $kb_count documents"
elif [[ "$kb_count" -gt 0 ]]; then
    warn "${SCENARIO_NS}-knowledge-base has only $kb_count documents (expected >= 5)"
elif [[ "$kb_count" -eq 0 ]]; then
    fail "${SCENARIO_NS}-knowledge-base is empty (re-deploy scenario)"
else
    fail "${SCENARIO_NS}-knowledge-base index not found (deploy scenario first)"
fi
echo ""

# ── 5. Agent Builder ─────────────────────────────────────────────────────────
echo "--- Agent Builder ---"

agents_response=$(kb_get "/api/agent_builder/agents")
agents_code=$(echo "$agents_response" | tail -1)
agents_body=$(echo "$agents_response" | sed '$d')

if [[ "$agents_code" -ge 200 && "$agents_code" -lt 300 ]]; then
    agent_found=$(echo "$agents_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
agents = data if isinstance(data, list) else data.get('results', data.get('agents', data.get('data', [])))
target_id = '${AGENT_ID}'
target_ns = '${SCENARIO_NS}'
found = any(
    a.get('id','') == target_id or target_ns in a.get('id','').lower()
    for a in (agents if isinstance(agents, list) else [agents])
)
print('yes' if found else 'no')
" 2>/dev/null || echo "unknown")

    if [[ "$agent_found" == "yes" ]]; then
        pass "Agent '${AGENT_ID}' found in Agent Builder"
    else
        warn "Agent Builder reachable but agent '${AGENT_ID}' not found"
    fi
else
    warn "Agent Builder API not accessible (HTTP $agents_code) — may need manual setup"
fi

# Check tools — expect >= 7 custom (non-readonly) tools
tools_response=$(kb_get "/api/agent_builder/tools")
tools_code=$(echo "$tools_response" | tail -1)
tools_body=$(echo "$tools_response" | sed '$d')

if [[ "$tools_code" -ge 200 && "$tools_code" -lt 300 ]]; then
    tool_count=$(echo "$tools_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tools = data if isinstance(data, list) else data.get('results', data.get('tools', data.get('data', [])))
custom = [t for t in tools if not t.get('readonly', False) and not t.get('is_default', False)]
ns_tools = [t for t in custom if '${SCENARIO_NS}' in t.get('id','')]
print(f'{len(custom)}|{len(ns_tools)}')
" 2>/dev/null || echo "0|0")

    IFS='|' read -r total_tools ns_tools <<< "$tool_count"

    if [[ "$ns_tools" -ge 7 ]]; then
        pass "Agent Builder has $ns_tools ${SCENARIO_NS}-prefixed tools (>= 7 expected)"
    elif [[ "$ns_tools" -gt 0 ]]; then
        warn "Agent Builder has $ns_tools ${SCENARIO_NS}-prefixed tools (expected >= 7)"
    elif [[ "$total_tools" -gt 0 ]]; then
        warn "No ${SCENARIO_NS}-prefixed tools found ($total_tools total custom tools exist)"
    else
        warn "No custom tools found in Agent Builder"
    fi
else
    warn "Agent Builder tools API not accessible (HTTP $tools_code)"
fi

# Check agent instructions reference body.text (prevents Unknown column [body] errors)
agent_instructions=$(echo "$agents_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
agents = data if isinstance(data, list) else data.get('results', data.get('agents', data.get('data', [])))
for a in agents:
    if '${SCENARIO_NS}' in a.get('id','').lower() or '${AGENT_ID}' == a.get('id',''):
        print(a.get('configuration', {}).get('instructions', ''))
        break
" 2>/dev/null || echo "")

if echo "$agent_instructions" | grep -q "body.text" && echo "$agent_instructions" | grep -q "NEVER"; then
    pass "Agent prompt has body.text field name warnings (prevents Unknown column [body] errors)"
elif [[ -n "$agent_instructions" ]]; then
    fail "Agent prompt MISSING body.text warnings — will cause ES|QL Unknown column [body] errors"
else
    warn "Could not check agent instructions"
fi
echo ""

# ── 6. Workflows ─────────────────────────────────────────────────────────────
echo "--- Workflows ---"

wf_search_response=$(kb_get "/api/workflows")
wf_search_code=$(echo "$wf_search_response" | tail -1)
wf_search_body=$(echo "$wf_search_response" | sed '$d')

# Fallback to POST search if GET not supported
if [[ "$wf_search_code" -eq 404 || "$wf_search_code" -eq 405 ]]; then
    wf_search_response=$(kb_post "/api/workflows/search" '{"page":1,"size":100}')
    wf_search_code=$(echo "$wf_search_response" | tail -1)
    wf_search_body=$(echo "$wf_search_response" | sed '$d')
fi

if [[ "$wf_search_code" -ge 200 && "$wf_search_code" -lt 300 ]]; then
    # Check all 3 core workflows exist and are valid
    wf_check=$(echo "$wf_search_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
expected = {
    'Significant Event Notification': {'found': False, 'valid': False, 'id': ''},
    'Remediation Action':             {'found': False, 'valid': False, 'id': ''},
    'Escalation and Hold Management': {'found': False, 'valid': False, 'id': ''},
}
for item in items:
    name = item.get('name', '')
    for key in expected:
        if key in name and '${SCENARIO_NAME}' in name:
            expected[key]['found'] = True
            expected[key]['valid'] = item.get('valid', False)
            expected[key]['id'] = item.get('id', '')
for key, val in expected.items():
    print(f'{key}|{val[\"found\"]}|{val[\"valid\"]}|{val[\"id\"]}')
" 2>/dev/null || true)

    while IFS='|' read -r wf_name wf_found wf_valid wf_id; do
        if [[ -z "$wf_name" ]]; then continue; fi
        if [[ "$wf_found" == "True" && "$wf_valid" == "True" ]]; then
            pass "Workflow '${SCENARIO_NAME} $wf_name' exists and is valid"
        elif [[ "$wf_found" == "True" ]]; then
            fail "Workflow '${SCENARIO_NAME} $wf_name' exists but is NOT valid"
        else
            fail "Workflow '${SCENARIO_NAME} $wf_name' NOT found"
        fi
    done <<< "$wf_check"

    # Check Significant Event Notification has alert trigger
    sen_alert=$(echo "$wf_search_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
for item in items:
    if 'Significant Event Notification' in item.get('name', '') and '${SCENARIO_NAME}' in item.get('name', ''):
        defn = item.get('definition', {}) or {}
        triggers = defn.get('triggers', [])
        print('yes' if any(t.get('type') == 'alert' for t in triggers) else 'no')
        break
" 2>/dev/null || echo "unknown")

    if [[ "$sen_alert" == "yes" ]]; then
        pass "Notification workflow has 'alert' trigger type"
    else
        fail "Notification workflow MISSING 'alert' trigger — alert rules won't fire it"
    fi

    # Check Notification workflow has email step with Elastic-Cloud-SMTP
    notif_email=$(echo "$wf_search_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
for item in items:
    if 'Significant Event Notification' in item.get('name', '') and '${SCENARIO_NAME}' in item.get('name', ''):
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

    # Check Notification workflow uses var[0].event_meta pattern (json_parse for email extraction)
    notif_var0=$(echo "$wf_search_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
for item in items:
    if 'Significant Event Notification' in item.get('name', '') and '${SCENARIO_NAME}' in item.get('name', ''):
        yaml_text = item.get('yaml', '')
        has_var0 = 'var[0].event_meta' in yaml_text
        has_json_parse = 'json_parse' in yaml_text
        print('yes' if (has_var0 and has_json_parse) else 'no')
        break
" 2>/dev/null || echo "unknown")

    if [[ "$notif_var0" == "yes" ]]; then
        pass "Notification workflow uses var[0].event_meta + json_parse for email extraction"
    else
        fail "Notification workflow MISSING var[0].event_meta pattern — email extraction will fail"
    fi

    # Check Notification workflow uses >= 15m time window for error count
    notif_window=$(echo "$wf_search_body" | python3 -c "
import sys, json, re
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
for item in items:
    if 'Significant Event Notification' in item.get('name', '') and '${SCENARIO_NAME}' in item.get('name', ''):
        yaml_text = item.get('yaml', '')
        m = re.search(r'NOW\(\) - (\d+) MINUTES', yaml_text, re.IGNORECASE)
        if not m:
            m = re.search(r'gte.*now-(\d+)m', yaml_text, re.IGNORECASE)
        if m:
            minutes = int(m.group(1))
            print('yes' if minutes >= 15 else f'no:{minutes}m')
        else:
            print('no:unknown')
        break
" 2>/dev/null || echo "unknown")

    if [[ "$notif_window" == yes* ]]; then
        pass "Notification workflow uses >= 15m window for error count"
    else
        fail "Notification workflow time window too narrow ($notif_window) — may miss logs"
    fi

    # Check Remediation workflow has case_id input (for direct case closure)
    rem_caseid=$(echo "$wf_search_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
for item in items:
    if 'Remediation Action' in item.get('name', '') and '${SCENARIO_NAME}' in item.get('name', ''):
        yaml_text = item.get('yaml', '')
        print('yes' if 'case_id' in yaml_text else 'no')
        break
" 2>/dev/null || echo "unknown")

    if [[ "$rem_caseid" == "yes" ]]; then
        pass "Remediation workflow has case_id input (direct case closure)"
    else
        fail "Remediation workflow MISSING case_id input — case closure will rely on tag search only"
    fi

    # Check all scenario workflows are enabled
    wf_disabled=$(echo "$wf_search_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
disabled = [i.get('name','') for i in items if '${SCENARIO_NAME}' in i.get('name','') and not i.get('enabled', True)]
print(','.join(disabled) if disabled else 'all_enabled')
" 2>/dev/null || echo "unknown")

    if [[ "$wf_disabled" == "all_enabled" ]]; then
        pass "All ${SCENARIO_NAME} workflows are enabled"
    elif [[ "$wf_disabled" == "unknown" ]]; then
        warn "Could not check workflow enabled status"
    else
        fail "Disabled workflows: $wf_disabled"
    fi
else
    fail "Workflows API not accessible (HTTP $wf_search_code)"
fi
echo ""

# ── 6b. Alert Rules ──────────────────────────────────────────────────────────
echo "--- Alert Rules ---"

# Search by scenario name in rule name (name-based, not tag-based)
alert_response=$(kb_get "/api/alerting/rules/_find?per_page=100&search_fields=name&search=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${SCENARIO_NAME}'))" 2>/dev/null || echo "${SCENARIO_NAME}")")
alert_code=$(echo "$alert_response" | tail -1)
alert_body=$(echo "$alert_response" | sed '$d')

if [[ "$alert_code" -ge 200 && "$alert_code" -lt 300 ]]; then
    alert_check=$(echo "$alert_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
rules = data.get('data', [])
scenario_rules = [r for r in rules if '${SCENARIO_NAME}' in r.get('name', '')]
wf_rules = [r for r in scenario_rules if any(a.get('connector_type_id') == '.workflows' for a in r.get('actions', []))]
obs_rules = [r for r in scenario_rules if r.get('consumer','') == 'observability']
print(f'{len(scenario_rules)}|{len(wf_rules)}|{len(obs_rules)}')
" 2>/dev/null || echo "0|0|0")

    IFS='|' read -r total_rules wf_rules obs_rules <<< "$alert_check"

    if [[ "$total_rules" -ge 20 ]]; then
        pass "Alert rules: $total_rules '${SCENARIO_NAME}' rules found (expected 20)"
    elif [[ "$total_rules" -gt 0 ]]; then
        warn "Alert rules: only $total_rules found (expected 20)"
    else
        fail "No '${SCENARIO_NAME}' alert rules found (re-deploy alerting step)"
    fi

    if [[ "$wf_rules" -ge 20 ]]; then
        pass "All $wf_rules rules use native .workflows connector"
    elif [[ "$wf_rules" -gt 0 ]]; then
        warn "Only $wf_rules/${total_rules} rules use .workflows connector"
    elif [[ "$total_rules" -gt 0 ]]; then
        fail "No rules using .workflows connector"
    fi

    if [[ "$obs_rules" -ge 20 ]]; then
        pass "All $obs_rules rules use consumer: observability (editable in Observability UI)"
    elif [[ "$obs_rules" -gt 0 && "$total_rules" -gt 0 ]]; then
        warn "Only $obs_rules/${total_rules} rules use consumer: observability (re-deploy alerting to fix)"
    elif [[ "$total_rules" -gt 0 ]]; then
        warn "Rules use consumer: alerts instead of observability — may not be editable in UI"
    fi
else
    warn "Alerting API not accessible (HTTP $alert_code)"
fi
echo ""

# ── 6c. Demo App ─────────────────────────────────────────────────────────────
echo "--- Demo App (Chaos API) ---"

app_response=$(curl -s -w "\n%{http_code}" http://localhost/api/status 2>/dev/null || echo -e "\n000")
app_code=$(echo "$app_response" | tail -1)

if [[ "$app_code" -ge 200 && "$app_code" -lt 300 ]]; then
    pass "Demo app is running (HTTP $app_code)"
elif [[ "$app_code" == "000" ]]; then
    warn "Demo app not reachable at localhost — generators may not be running"
else
    warn "Demo app returned HTTP $app_code"
fi
echo ""

# ── 6d. E2E Workflow Execution Tests ─────────────────────────────────────────
echo "--- E2E: Workflow Execution Tests ---"

wf_exec_response=$(kb_get "/api/workflows")
wf_exec_code=$(echo "$wf_exec_response" | tail -1)
wf_exec_body=$(echo "$wf_exec_response" | sed '$d')

if [[ "$wf_exec_code" -eq 404 || "$wf_exec_code" -eq 405 ]]; then
    wf_exec_response=$(kb_post "/api/workflows/search" '{"page":1,"size":100}')
    wf_exec_code=$(echo "$wf_exec_response" | tail -1)
    wf_exec_body=$(echo "$wf_exec_response" | sed '$d')
fi

if [[ "$wf_exec_code" -ge 200 && "$wf_exec_code" -lt 300 ]]; then
    escalation_wf_id=$(echo "$wf_exec_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
for w in items:
    if 'Escalation' in w.get('name', '') and '${SCENARIO_NAME}' in w.get('name', ''):
        print(w['id']); break
" 2>/dev/null || echo "")

    remediation_wf_id=$(echo "$wf_exec_body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('results', data.get('items', data.get('data', [])))
for w in items:
    if 'Remediation' in w.get('name', '') and '${SCENARIO_NAME}' in w.get('name', ''):
        print(w['id']); break
" 2>/dev/null || echo "")

    # --- Test Escalation Workflow ---
    if [[ -n "$escalation_wf_id" ]]; then
        esc_run_response=$(kb_post "/api/workflows/${escalation_wf_id}/run" \
            '{"inputs":{"action":"escalate","channel":1,"severity":"ADVISORY","justification":"Validation test — automated escalation check","hold_id":"","investigation_summary":""}}')
        esc_run_code=$(echo "$esc_run_response" | tail -1)
        esc_run_body=$(echo "$esc_run_response" | sed '$d')

        if [[ "$esc_run_code" -ge 200 && "$esc_run_code" -lt 300 ]]; then
            esc_exec_id=$(echo "$esc_run_body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('workflowExecutionId',''))" 2>/dev/null || echo "")
            if [[ -n "$esc_exec_id" ]]; then
                sleep 12
                esc_status_response=$(kb_get "/api/workflowExecutions/${esc_exec_id}")
                esc_status=$(echo "$esc_status_response" | sed '$d' | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")

                if [[ "$esc_status" == "completed" ]]; then
                    pass "E2E: Escalation workflow executed successfully (completed)"
                elif [[ "$esc_status" == "running" ]]; then
                    warn "E2E: Escalation workflow still running after 12s"
                else
                    esc_err=$(echo "$esc_status_response" | sed '$d' | python3 -c "
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

    # --- Test Remediation Workflow (dry_run=true) ---
    if [[ -n "$remediation_wf_id" ]]; then
        rem_run_response=$(kb_post "/api/workflows/${remediation_wf_id}/run" \
            '{"inputs":{"error_type":"validation_test","channel":1,"action_type":"validation_check","target_service":"","justification":"Validation test — automated dry-run check","dry_run":true,"case_id":""}}')
        rem_run_code=$(echo "$rem_run_response" | tail -1)
        rem_run_body=$(echo "$rem_run_response" | sed '$d')

        if [[ "$rem_run_code" -ge 200 && "$rem_run_code" -lt 300 ]]; then
            rem_exec_id=$(echo "$rem_run_body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('workflowExecutionId',''))" 2>/dev/null || echo "")
            if [[ -n "$rem_exec_id" ]]; then
                sleep 8
                rem_status_response=$(kb_get "/api/workflowExecutions/${rem_exec_id}")
                rem_status=$(echo "$rem_status_response" | sed '$d' | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")

                if [[ "$rem_status" == "completed" ]]; then
                    pass "E2E: Remediation workflow dry-run executed successfully (completed)"
                elif [[ "$rem_status" == "running" ]]; then
                    warn "E2E: Remediation workflow still running after 8s"
                else
                    rem_err=$(echo "$rem_status_response" | sed '$d' | python3 -c "
import sys,json
d=json.load(sys.stdin)
e=d.get('error',{})
print(e.get('message','') if isinstance(e,dict) else str(e))
" 2>/dev/null || echo "unknown error")
                    fail "E2E: Remediation workflow dry-run failed (status: $rem_status, error: $rem_err)"
                fi
            else
                fail "E2E: Remediation workflow run returned no execution ID"
            fi
        else
            fail "E2E: Remediation workflow run failed (HTTP $rem_run_code)"
        fi
    else
        warn "E2E: Remediation workflow not found — cannot test execution"
    fi
else
    warn "E2E: Could not list workflows (HTTP $wf_exec_code) — skipping execution tests"
fi
echo ""

# ── 7. Executive Dashboard ───────────────────────────────────────────────────
echo "--- Executive Dashboard ---"
dash_response=$(kb_post "/api/saved_objects/_export" "{\"objects\":[{\"type\":\"dashboard\",\"id\":\"${SCENARIO_NS}-exec-dashboard\"}],\"includeReferencesDeep\":false}")
dash_code=$(echo "$dash_response" | tail -1)
dash_body=$(echo "$dash_response" | sed '$d')

if [[ "$dash_code" -ge 200 && "$dash_code" -lt 300 ]]; then
    if echo "$dash_body" | grep -q "${SCENARIO_NS}-exec-dashboard" 2>/dev/null; then
        pass "${SCENARIO_NAME} Executive Dashboard exists"
        info "URL: ${KIBANA_URL}/app/dashboards#/view/${SCENARIO_NS}-exec-dashboard"
    else
        warn "Export returned but dashboard ID not confirmed"
    fi
else
    fail "${SCENARIO_NAME} Executive Dashboard not found (re-deploy scenario)"
fi
echo ""

# ── 8. Significant Events (Streams Queries) ──────────────────────────────────
echo "--- Significant Events (Streams Queries) ---"

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
    count = sum(1 for q in queries if q.get('id', '').startswith('${SCENARIO_NS}-se-'))
    print(count)
except:
    print('0')
" 2>/dev/null || echo "0")

    if [[ "$se_count" -ge 20 ]]; then
        pass "Significant Events: $se_count ${SCENARIO_NS}-se-* queries on stream '${se_stream}'"
    elif [[ "$se_count" -gt 0 ]]; then
        warn "Significant Events: only $se_count queries found (expected >= 20)"
    else
        warn "No ${SCENARIO_NS}-se-* queries found on stream '${se_stream}' (re-deploy scenario)"
    fi
else
    warn "Streams Queries API not accessible (HTTP $se_code) — Streams may not be enabled"
fi
echo ""

# ── 9. Trace Data ─────────────────────────────────────────────────────────────
echo "--- Trace Data (APM Service Map) ---"

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
        info "Trace indices exist but are empty (APM rollup generator hasn't run yet)"
    fi
else
    info "No traces-* indices found (APM rollup not yet generated)"
fi
echo ""

# ── 10. Host Metrics ─────────────────────────────────────────────────────────
echo "--- Host Metrics (Infrastructure UI) ---"

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
        info "Metrics indices exist but are empty"
    fi
else
    info "No metrics-* indices found"
fi
echo ""

# ── 11. Nginx Log Data ───────────────────────────────────────────────────────
echo "--- Nginx Log Generator Data ---"
nginx_access_count=$(get_count "logs-nginx.access.otel-default")
nginx_error_count=$(get_count "logs-nginx.error.otel-default")

if [[ "$nginx_access_count" -gt 0 ]]; then
    pass "logs-nginx.access.otel-default has $nginx_access_count docs"
else
    info "logs-nginx.access.otel-default not found (optional nginx generator)"
fi

if [[ "$nginx_error_count" -gt 0 ]]; then
    pass "logs-nginx.error.otel-default has $nginx_error_count docs"
else
    info "logs-nginx.error.otel-default not yet populated"
fi
echo ""

# ── 12. MySQL Log Data ───────────────────────────────────────────────────────
echo "--- MySQL Log Generator Data ---"
mysql_slow_count=$(get_count "logs-mysql.slowlog.otel-default")
mysql_error_count=$(get_count "logs-mysql.error.otel-default")

if [[ "$mysql_slow_count" -gt 0 ]]; then
    pass "logs-mysql.slowlog.otel-default has $mysql_slow_count docs"
else
    info "logs-mysql.slowlog.otel-default not found (optional mysql generator)"
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
echo "   Scenario: ${SCENARIO_NAME} (${SCENARIO_NS})"
echo "============================================================"

if [[ "$FAIL" -gt 0 ]]; then
    echo ""
    echo "Some checks failed. Re-deploy the scenario from the web UI to fix."
    exit 1
elif [[ "$WARN" -gt 0 ]]; then
    echo ""
    echo "Some checks returned warnings. This is expected if generators"
    echo "haven't been started yet or certain APIs are not available."
    exit 0
else
    echo ""
    echo "All checks passed!"
    exit 0
fi

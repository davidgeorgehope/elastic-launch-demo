"""Elastic Observability Demo Platform — FastAPI entry point."""

from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import (
    ACTIVE_SCENARIO,
    ACTIVE_SCENARIO_LIST,
    ACTIVE_SCENARIO_SET,
    APP_HOST,
    APP_PORT,
    CHANNEL_REGISTRY,
    CHANNEL_TIMEOUT,
    ELASTIC_API_KEY,
    ELASTIC_URL,
    KIBANA_PROXY,
    KIBANA_URL,
    MISSION_ID,
    MISSION_NAME,
    NAMESPACE,
    OTLP_ENDPOINT,
    SERVICES,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
# Suppress noisy httpx request logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("nova7")

# ── Multi-tenancy singletons ──────────────────────────────────────────────────
from app.op_queue import OperationQueue
from app.registry import InstanceRegistry
from app.store import ChaosStore, DeploymentStore

registry = InstanceRegistry()
store = DeploymentStore()
chaos_store = ChaosStore()
op_queue = OperationQueue()


def _queued_step(position: int, total: int) -> dict:
    """Synthetic 'Queued' progress step that mirrors DeployStep.to_dict() shape."""
    return {
        "name": "Queued",
        "status": "running",
        "detail": f"Position {position} of {total} in queue",
        "items_total": 0,
        "items_done": 0,
    }


def _purge_deployment_records(deployment_id: str) -> None:
    """Drop deployment row and any persisted chaos channels for this id."""
    store.delete(deployment_id)
    chaos_store.delete_channels_for_deployment(deployment_id)
    chaos_store.delete_spikes_for_deployment(deployment_id)


# In-memory progress trackers keyed by deployment_id
_deploy_progress: dict[str, dict] = {}
_teardown_progress: dict[str, dict] = {}


def _get_instance(deployment_id: Optional[str] = None):
    """Look up instance by id, or return first active instance as fallback."""
    if deployment_id:
        inst = registry.get(deployment_id)
        if inst:
            return inst
    return registry.first()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """On startup: restore active deployments from SQLite.  On shutdown: stop all."""
    from app.context import ScenarioContext
    from app.instance import ScenarioInstance
    from scenarios import get_scenario

    # Restore previously active deployments
    for rec in store.get_all_active():
        try:
            scenario = get_scenario(rec["scenario_id"])
            ctx = ScenarioContext.from_scenario(
                scenario,
                otlp_endpoint=rec["otlp_endpoint"],
                otlp_api_key=rec["otlp_api_key"],
                elastic_url=rec["elastic_url"],
                elastic_api_key=rec["elastic_api_key"],
                kibana_url=rec["kibana_url"],
            )
            instance = ScenarioInstance(ctx, chaos_store=chaos_store)
            instance.start()
            registry.register(rec["deployment_id"], instance)
            logger.info(
                "Restored deployment: %s (%s)", rec["deployment_id"], rec["scenario_id"]
            )
        except Exception:
            logger.exception("Failed to restore deployment %s", rec["deployment_id"])
            store.set_status(rec["deployment_id"], "error")

    # Auto-deploy from environment variables if credentials AND at least one
    # explicit scenario are provided.  Scenarios already running (restored from
    # SQLite) are skipped.
    if KIBANA_URL and ELASTIC_API_KEY and ACTIVE_SCENARIO_SET:
        from elastic_config.deployer import ScenarioDeployer

        kibana_url = KIBANA_URL.strip().rstrip("/")
        api_key = ELASTIC_API_KEY.strip()
        elastic_url = _derive_elastic_url(kibana_url, api_key, explicit=ELASTIC_URL)

        # Pre-compute an OTLP URL from the ES URL as a last-resort fallback.
        # The deployer probes the endpoint to verify it; if that probe fails the
        # deployer returns an empty otlp_endpoint. This fallback is used in that
        # case so telemetry isn't silently dropped.
        _pre_derived_otlp = ""
        if elastic_url and ".es." in elastic_url:
            _pre_derived_otlp = elastic_url.replace(".es.", ".ingest.").rstrip("/")
            if not _pre_derived_otlp.endswith(":443"):
                _pre_derived_otlp += ":443"

        def _make_auto_deploy(dep_id, s_id, _scenario, _deployer):
            """Factory that binds per-scenario variables for each deploy thread."""
            _scenario_name = _scenario.scenario_name

            def _progress_cb(progress):
                d = progress.to_dict()
                d["scenario_name"] = _scenario_name
                _deploy_progress[dep_id] = d
                steps = d.get("steps") or []
                if steps:
                    last = steps[-1]
                    logger.info(
                        "[auto-deploy:%s] %s — %s%s",
                        dep_id,
                        last.get("name", ""),
                        last.get("status", ""),
                        f" ({last['detail']})" if last.get("detail") else "",
                    )

            def _auto_deploy():
                result = _deployer.deploy_all(callback=_progress_cb)
                # Priority: explicit env var → deployer-verified → pre-derived fallback
                otlp_endpoint = OTLP_ENDPOINT or result.otlp_endpoint or _pre_derived_otlp
                try:
                    ctx = ScenarioContext.from_scenario(
                        _scenario,
                        otlp_endpoint=otlp_endpoint,
                        otlp_api_key=api_key,
                        elastic_url=elastic_url,
                        elastic_api_key=api_key,
                        kibana_url=kibana_url,
                    )
                    instance = ScenarioInstance(ctx, chaos_store=chaos_store)
                    if otlp_endpoint:
                        instance.otlp.reconfigure(otlp_endpoint, api_key)
                    instance.start()
                    registry.register(dep_id, instance)
                    store.upsert(
                        deployment_id=dep_id,
                        scenario_id=s_id,
                        otlp_endpoint=otlp_endpoint,
                        otlp_api_key=api_key,
                        elastic_url=elastic_url,
                        elastic_api_key=api_key,
                        kibana_url=kibana_url,
                    )
                    logger.info("Auto-deploy complete: %s (%s)", dep_id, s_id)
                except Exception:
                    logger.exception("Auto-deploy failed for %s", s_id)

            return _auto_deploy

        def _make_on_position(s_id: str):
            def _on_position(position: int, total: int) -> None:
                entry = _deploy_progress.get(s_id)
                if not entry or entry.get("finished"):
                    return
                steps = entry.get("steps") or []
                if steps and steps[0].get("name") == "Queued":
                    steps[0] = _queued_step(position, total)
                else:
                    entry["steps"] = [_queued_step(position, total)]
            return _on_position

        for scenario_id in ACTIVE_SCENARIO_LIST:
            if registry.get(scenario_id):
                continue  # Already running (restored from SQLite)
            scenario = get_scenario(scenario_id)
            deployer = ScenarioDeployer(scenario, elastic_url, kibana_url, api_key, KIBANA_PROXY)
            logger.info(
                "Auto-deploy triggered from environment variables (scenario=%s)",
                scenario_id,
            )
            _deploy_progress[scenario_id] = {
                "finished": False, "error": "",
                "scenario_id": scenario_id,
                "scenario_name": scenario.scenario_name,
                "steps": [_queued_step(1, 1)],
            }
            op_queue.submit_deploy(
                scenario_id,
                _make_auto_deploy(scenario_id, scenario_id, scenario, deployer),
                _make_on_position(scenario_id),
            )

    yield

    registry.stop_all()
    logger.info("All deployments shut down")


app = FastAPI(
    title="Elastic Observability Demo Platform",
    version="2.0.0",
    lifespan=lifespan,
)

# ── Static file mounts ─────────────────────────────────────────────────────
_base = os.path.dirname(__file__)
app.mount(
    "/chaos/static",
    StaticFiles(directory=os.path.join(_base, "chaos_ui", "static")),
    name="chaos-static",
)
app.mount(
    "/selector/static",
    StaticFiles(directory=os.path.join(_base, "selector", "static")),
    name="selector-static",
)

# ── Scenario helper ──────────────────────────────────────────────────────────


def _get_scenario_for_deployment(deployment_id: Optional[str] = None):
    """Get scenario object from a running instance or fall back to default."""
    inst = _get_instance(deployment_id)
    if inst:
        return inst.ctx.scenario
    from scenarios import get_scenario

    return get_scenario(ACTIVE_SCENARIO)


def _inject_theme(html: str, deployment_id: Optional[str] = None) -> str:
    """Inject active scenario's theme CSS vars and metadata into HTML."""
    inst = _get_instance(deployment_id)
    if inst:
        scenario = inst.ctx.scenario
        mission_id = inst.ctx.mission_id
        kibana = inst.ctx.kibana_url or _get_default_creds()[1]
    else:
        from scenarios import get_scenario

        scenario = get_scenario(ACTIVE_SCENARIO)
        mission_id = MISSION_ID
        kibana = _get_default_creds()[1]

    kibana_display = KIBANA_PROXY or kibana

    theme = scenario.theme

    # Elastic brand CSS — light theme matching the home page. All chaos pages share
    # the same look regardless of scenario. Semantic status colors use Elastic palette.
    css_override = """:root {
  --elastic-blue: #0B64DD;
  --teal: #48EFCF;
  --yellow: #FEC514;
  --light-poppy: #FF957D;
  --pink: #F04E98;
  --dev-blue: #101C3F;
  --bg-primary: #FFFFFF;
  --bg-secondary: #F5F7FA;
  --bg-card: #FFFFFF;
  --border: rgba(16, 28, 63, 0.15);
  --border-card: #101C3F;
  --text-primary: #1C1E23;
  --text-secondary: #343741;
  --text-dim: #69707D;
  --nominal: #48EFCF;
  --advisory: #FEC514;
  --caution: #FF957D;
  --warning: #FEC514;
  --critical: #F04E98;
  --resolve-green: #48EFCF;
  --inject-red: #BD271E;
  --status-nominal: #017D73;
  --status-critical: #BD271E;
}
body { font-family: 'Inter', -apple-system, system-ui, sans-serif; }"""

    if getattr(scenario, "executive_kpi_emitter_service_name", None):
        revenue_dashboard_card = f"""
            <a href="{kibana_display}/app/dashboards#/view/{scenario.namespace}-business-exec-dashboard"
               class="nav-card" target="_blank" rel="noopener">
                <div class="card-body">
                    <div class="card-header">
                        <span class="card-indicator"></span>
                        <span class="card-title">Executive Dashboard</span>
                        <span class="external-icon">&#8599;</span>
                    </div>
                    <div class="card-desc">
                        Senior-leadership KPI deck (audience, monetization, partners, health proxies)
                        \u2014 synthetic OTLP from <code>{scenario.executive_kpi_emitter_service_name}</code>.
                    </div>
                    <span class="card-tag kibana">Kibana</span>
                    <span class="card-tag elastic">Metrics</span>
                </div>
            </a>"""
    else:
        revenue_dashboard_card = ""

    replacements = {
        "<!--THEME_CSS-->": f"<style>{css_override}</style>",
        "DEPLOYMENT_ID_PLACEHOLDER": deployment_id or "",
        "SCENARIO_NAME_PLACEHOLDER": scenario.scenario_name,
        "SCENARIO_ID_PLACEHOLDER": scenario.scenario_id,
        "NAMESPACE_PLACEHOLDER": scenario.namespace,
        "MISSION_ID_PLACEHOLDER": mission_id,
        "CHAOS_TITLE_PLACEHOLDER": theme.chaos_title,
        "KIBANA_URL_PLACEHOLDER": kibana_display,
        "CHANNEL_TIMEOUT_PLACEHOLDER": str(CHANNEL_TIMEOUT),
        "REVENUE_DASHBOARD_CARD_PLACEHOLDER": revenue_dashboard_card,
    }
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)
    return html


# ── Environment ──────────────────────────────────────────────────────────────


def _get_default_creds() -> tuple[str, str, str]:
    """Get (elastic_url, kibana_url, api_key) from first active deployment in store."""
    recs = store.get_all_active()
    if recs:
        r = recs[0]
        return r["elastic_url"], r["kibana_url"], r["elastic_api_key"]
    return "", "", ""


def _derive_elastic_url(kibana_url: str, api_key: str, explicit: str = "") -> str:
    """Derive Elasticsearch URL using three strategies in priority order:
    1. Explicit value (env var or user-supplied)
    2. Fleet outputs API (GET /api/fleet/outputs → default output hosts[0])
    3. .kb. → .es. substitution in the Kibana URL
    """
    if explicit:
        return explicit.strip().rstrip("/")

    # Strategy 2: Fleet outputs API
    try:
        import httpx
        with httpx.Client(timeout=10.0, verify=True) as client:
            resp = client.get(
                f"{kibana_url}/api/fleet/outputs",
                headers={
                    "Authorization": f"ApiKey {api_key}",
                    "kbn-xsrf": "true",
                },
            )
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                for item in items:
                    if item.get("name") == "default":
                        hosts = item.get("hosts", [])
                        if hosts:
                            logger.info("Derived ES URL via Fleet API: %s", hosts[0])
                            return hosts[0].rstrip("/")
                logger.warning("Fleet API returned 200 but no default output found: %s", resp.json())
            else:
                logger.warning("Fleet API returned HTTP %d: %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.warning("Fleet API ES URL derivation failed: %s", exc)

    # Strategy 3: .kb. → .es. substitution
    if ".kb." in kibana_url:
        return kibana_url.replace(".kb.", ".es.")

    logger.warning("Could not derive ES URL from kibana_url=%r (no .kb. and Fleet API failed)", kibana_url)
    return ""


# ── Scenario Selector (new front page) ───────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def selector_page():
    """Scenario selector — choose industry vertical and connect."""
    path = os.path.join(_base, "selector", "static", "index.html")
    with open(path) as f:
        return HTMLResponse(content=f.read())


# ── Health ──────────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    instances = registry.all_instances()
    return {
        "status": "ok",
        "deployments": len(instances),
        "scenarios": [dep_id for dep_id in instances],
    }


# ── Chaos Controller UI ────────────────────────────────────────────────────


@app.get("/chaos", response_class=HTMLResponse)
async def chaos_page(deployment_id: Optional[str] = None):
    path = os.path.join(_base, "chaos_ui", "static", "index.html")
    with open(path) as f:
        html = f.read()
    return HTMLResponse(content=_inject_theme(html, deployment_id))


# ── Scenario API ───────────────────────────────────────────────────────────


@app.get("/api/scenarios")
async def list_scenarios():
    """List all available scenarios."""
    from scenarios import list_scenarios as _list

    return _list()


@app.get("/api/scenario")
async def current_scenario(deployment_id: Optional[str] = None):
    """Return active scenario metadata and theme."""
    scenario = _get_scenario_for_deployment(deployment_id)
    theme = scenario.theme
    return {
        "id": scenario.scenario_id,
        "name": scenario.scenario_name,
        "description": scenario.scenario_description,
        "namespace": scenario.namespace,
        "services": scenario.services,
        "channel_registry": {
            str(k): {
                "name": v["name"],
                "subsystem": v["subsystem"],
                "error_type": v["error_type"],
                "affected_services": v["affected_services"],
                "cascade_services": v["cascade_services"],
                "description": v["description"],
            }
            for k, v in scenario.channel_registry.items()
        },
        "theme": {
            "bg_primary": theme.bg_primary,
            "bg_secondary": theme.bg_secondary,
            "bg_tertiary": theme.bg_tertiary,
            "accent_primary": theme.accent_primary,
            "accent_secondary": theme.accent_secondary,
            "text_primary": theme.text_primary,
            "text_secondary": theme.text_secondary,
            "text_accent": theme.text_accent,
            "status_nominal": theme.status_nominal,
            "status_warning": theme.status_warning,
            "status_critical": theme.status_critical,
            "chaos_title": theme.chaos_title,
            "font_family": theme.font_family,
            "font_mono": theme.font_mono,
            "scanline_effect": theme.scanline_effect,
            "glow_effect": theme.glow_effect,
            "grid_background": theme.grid_background,
            "gradient_accent": theme.gradient_accent,
        },
        "countdown": {
            "enabled": scenario.countdown_config.enabled,
            "start_seconds": scenario.countdown_config.start_seconds,
        },
    }


# ── Deployments API (multi-tenancy) ──────────────────────────────────────────


@app.get("/api/deployments")
async def list_deployments():
    """List all active deployments."""
    instances = registry.all_instances()
    result = []
    for dep_id, inst in instances.items():
        result.append(
            {
                "deployment_id": dep_id,
                "scenario_id": inst.scenario_id,
                "scenario_name": inst.ctx.scenario.scenario_name,
                "namespace": inst.ctx.namespace,
                "running": inst.running,
                "kibana_url": inst.ctx.kibana_url,
                "kibana_display_url": KIBANA_PROXY or inst.ctx.kibana_url,
            }
        )
    return result


@app.post("/api/deployments/{deployment_id}/stop")
async def stop_deployment(deployment_id: str):
    """Stop a specific deployment's generators."""
    inst = registry.get(deployment_id)
    if not inst:
        return JSONResponse(
            status_code=404, content={"error": f"Deployment {deployment_id} not found"}
        )
    inst.stop()
    store.set_status(deployment_id, "stopped")
    return {"status": "stopped", "deployment_id": deployment_id}


@app.delete("/api/deployments/{deployment_id}")
async def remove_deployment(deployment_id: str):
    """Remove a deployment from registry and store."""
    inst = registry.remove(deployment_id)
    if inst:
        inst.stop()
    _purge_deployment_records(deployment_id)
    return {"status": "removed", "deployment_id": deployment_id}


# ── Chaos API ───────────────────────────────────────────────────────────────


@app.post("/api/chaos/trigger")
async def chaos_trigger(body: dict):
    deployment_id = body.get("deployment_id")
    inst = _get_instance(deployment_id)
    if not inst:
        return JSONResponse(status_code=404, content={"error": "No active deployment"})
    channel = int(body.get("channel", 0))
    mode = body.get("mode", "calibration")
    se_name = body.get("se_name", "")
    callback_url = body.get("callback_url", "")
    user_email = body.get("user_email", "")
    session_id = body.get("session_id", "")
    result = inst.chaos_controller.trigger(
        channel,
        mode,
        se_name,
        callback_url,
        user_email,
        session_id=session_id,
    )
    return result


@app.post("/api/chaos/resolve")
async def chaos_resolve(body: dict):
    deployment_id = body.get("deployment_id")
    inst = _get_instance(deployment_id)
    if not inst:
        return JSONResponse(status_code=404, content={"error": "No active deployment"})
    channel = int(body.get("channel", 0))
    session_id = body.get("session_id", "")
    user_email = body.get("user_email", "")
    result = inst.chaos_controller.resolve(channel, session_id=session_id, user_email=user_email)
    if result.get("error") == "session_mismatch":
        return JSONResponse(status_code=403, content=result)
    return result


@app.post("/api/chaos/spikes")
async def set_chaos_spikes(body: dict):
    deployment_id = body.get("deployment_id")
    inst = _get_instance(deployment_id)
    if not inst:
        return JSONResponse(status_code=404, content={"error": "No active deployment"})
    inst.chaos_controller.set_infra_spikes(body)
    return inst.chaos_controller.get_infra_spikes()


@app.get("/api/chaos/spikes")
async def get_chaos_spikes(deployment_id: Optional[str] = None):
    inst = _get_instance(deployment_id)
    if not inst:
        return {
            "cpu_pct": 0,
            "memory_pct": 0,
            "k8s_oom_intensity": 0,
            "latency_multiplier": 1.0,
        }
    return inst.chaos_controller.get_infra_spikes()


@app.get("/api/chaos/status")
async def chaos_status(deployment_id: Optional[str] = None):
    inst = _get_instance(deployment_id)
    if not inst:
        return {}
    return inst.chaos_controller.get_status()


@app.get("/api/chaos/status/{channel}")
async def chaos_channel_status(channel: int, deployment_id: Optional[str] = None):
    inst = _get_instance(deployment_id)
    if not inst:
        return {"error": "No active deployment"}
    return inst.chaos_controller.get_channel_status(channel)


@app.get("/api/chaos/session/validate")
async def chaos_session_validate(session_id: str, deployment_id: Optional[str] = None, user_email: str = ""):
    """Check if a session_id (or user_email fallback) owns any active channels."""
    inst = _get_instance(deployment_id)
    if not inst:
        return {"valid": False, "channels": []}
    channels = inst.chaos_controller.validate_session(session_id, user_email=user_email)
    return {"valid": len(channels) > 0, "channels": channels}


# ── Status API ──────────────────────────────────────────────────────────────


@app.get("/api/status")
async def system_status(deployment_id: Optional[str] = None):
    inst = _get_instance(deployment_id)
    if not inst:
        return {"error": "No active deployment"}
    return {
        "scenario": inst.scenario_id,
        "mission_id": inst.ctx.mission_id,
        "mission_name": inst.ctx.scenario.scenario_name,
        "namespace": inst.ctx.namespace,
        "services": inst.service_manager.get_all_status(),
        "generators": inst.service_manager.get_generator_status(),
        "chaos": inst.chaos_controller.get_status(),
        "countdown": inst.service_manager.get_countdown(),
    }


# ── Countdown Control ──────────────────────────────────────────────────────


@app.post("/api/countdown/start")
async def countdown_start(body: dict = {}):
    inst = _get_instance(body.get("deployment_id") if body else None)
    if not inst:
        return JSONResponse(status_code=404, content={"error": "No active deployment"})
    inst.service_manager.countdown_start()
    return {"status": "started"}


@app.post("/api/countdown/pause")
async def countdown_pause(body: dict = {}):
    inst = _get_instance(body.get("deployment_id") if body else None)
    if not inst:
        return JSONResponse(status_code=404, content={"error": "No active deployment"})
    inst.service_manager.countdown_pause()
    return {"status": "paused"}


@app.post("/api/countdown/reset")
async def countdown_reset(body: dict = {}):
    inst = _get_instance(body.get("deployment_id") if body else None)
    if not inst:
        return JSONResponse(status_code=404, content={"error": "No active deployment"})
    inst.service_manager.countdown_reset()
    return {"status": "reset"}


@app.post("/api/countdown/speed")
async def countdown_speed(body: dict):
    inst = _get_instance(body.get("deployment_id"))
    if not inst:
        return JSONResponse(status_code=404, content={"error": "No active deployment"})
    speed = float(body.get("speed", 1.0))
    inst.service_manager.countdown_set_speed(speed)
    return {"status": "speed_set", "speed": speed}


# ── Remediation endpoint (called by Elastic Workflow) ──────────────────────


@app.post("/api/remediate/{channel}")
async def remediate_channel(channel: int, deployment_id: Optional[str] = None):
    inst = _get_instance(deployment_id)
    if not inst:
        return JSONResponse(status_code=404, content={"error": "No active deployment"})
    result = inst.chaos_controller.resolve(channel, force=True)
    return {"action": "remediated", "channel": channel, **result}


# ── User Info (for auto-populating email) ─────────────────────────────────


@app.get("/api/user/info")
async def user_info(request: Request):
    email = request.headers.get("X-Forwarded-User", "") or os.environ.get(
        "INSTRUQT_USER_EMAIL", ""
    )
    return {"email": email}


# ── Email Notification endpoint (called by Elastic Workflow) ──────────────


@app.post("/api/notify/email")
async def notify_email(body: dict):
    from app.notify.email_handler import send_email

    to = body.get("to", "")
    subject = body.get("subject", "")
    message = body.get("body", "")
    result = await send_email(to, subject, message)
    return result


# ── Daily Update Report ────────────────────────────────────────────────────


@app.post("/api/daily-update")
async def send_daily_update(body: dict):
    """Trigger the Daily Update Report workflow, which uses the AI assistant
    to analyse recent logs/traces and emails a health summary."""
    import httpx as _httpx

    email = body.get("email", "").strip()
    deployment_id = body.get("deployment_id")

    if not email:
        return JSONResponse(status_code=400, content={"error": "Missing email"})

    inst = _get_instance(deployment_id)
    if not inst:
        return JSONResponse(status_code=404, content={"error": "No active deployment"})

    kibana_url = inst.ctx.kibana_url
    api_key = inst.ctx.elastic_api_key
    if not kibana_url or not api_key:
        return JSONResponse(status_code=400, content={"error": "No Kibana credentials"})

    headers = {
        "Content-Type": "application/json",
        "kbn-xsrf": "true",
        "x-elastic-internal-origin": "kibana",
        "Authorization": f"ApiKey {api_key}",
    }

    async with _httpx.AsyncClient(timeout=30) as client:
        # Find the workflow by name — try GET first, fall back to POST search
        search_resp = await client.get(
            f"{kibana_url}/api/workflows",
            headers=headers,
        )
        if search_resp.status_code in (404, 405):
            search_resp = await client.post(
                f"{kibana_url}/api/workflows/search",
                headers=headers,
                json={"page": 1, "size": 100},
            )
        if search_resp.status_code >= 300:
            return JSONResponse(
                status_code=502,
                content={"error": f"Workflow search failed: {search_resp.status_code}"},
            )

        search_data = search_resp.json()
        workflows = search_data if isinstance(search_data, list) else search_data.get("results", search_data.get("items", []))
        wf_id = None
        for wf in workflows:
            if "Daily Update Report" in wf.get("name", ""):
                wf_id = wf["id"]
                break

        if not wf_id:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "Daily Update Report workflow not found — redeploy the scenario"
                },
            )

        # Trigger the workflow — try new path first, fall back to old
        run_resp = await client.post(
            f"{kibana_url}/api/workflows/workflow/{wf_id}/run",
            headers=headers,
            json={"inputs": {"email": email}},
        )
        if run_resp.status_code in (404, 405):
            run_resp = await client.post(
                f"{kibana_url}/api/workflows/{wf_id}/run",
                headers=headers,
                json={"inputs": {"email": email}},
            )
        if run_resp.status_code >= 300:
            return JSONResponse(
                status_code=502,
                content={"error": f"Workflow run failed: {run_resp.status_code}"},
            )

    return {
        "status": "triggered",
        "message": "Daily update report requested — check your email in 2-3 minutes",
        "workflow_id": wf_id,
    }


# ── Setup / Deployer API ───────────────────────────────────────────────────


@app.get("/api/setup/env-creds")
async def env_creds_status():
    """Return whether Elastic credentials are configured via environment variables."""
    return {
        "has_env_creds": bool(KIBANA_URL and ELASTIC_API_KEY),
        "scenario": ACTIVE_SCENARIO,
    }


@app.post("/api/setup/test-connection")
async def test_connection(body: dict):
    """Test connectivity to each component independently."""
    from scenarios import get_scenario as _get_scenario_by_id
    from elastic_config.deployer import ScenarioDeployer
    from elastic_config.deployer_base import _kibana_headers, _es_headers
    import httpx

    kibana_url = body.get("kibana_url", "").strip().rstrip("/")
    api_key = body.get("api_key", "").strip()

    if not kibana_url or not api_key:
        return {"error": "Missing kibana_url or api_key"}

    result = {}

    with httpx.Client(timeout=15.0, verify=True) as client:
        # Test Kibana — use an auth-required endpoint so a bad API key fails
        try:
            resp = client.get(f"{kibana_url}/api/spaces/space", headers=_kibana_headers(api_key))
            result["kibana_ok"] = resp.status_code < 300
            result["kibana_error"] = None if result["kibana_ok"] else f"HTTP {resp.status_code}"
        except Exception as exc:
            result["kibana_ok"] = False
            result["kibana_error"] = str(exc)

        # Derive ES URL and test
        elastic_url = _derive_elastic_url(kibana_url, api_key, explicit=body.get("elastic_url") or "")
        result["elastic_url"] = elastic_url or None

        if elastic_url:
            try:
                resp = client.get(f"{elastic_url}/", headers=_es_headers(api_key))
                if resp.status_code < 300:
                    result["es_ok"] = True
                    result["es_error"] = None
                    result["cluster_name"] = resp.json().get("cluster_name", "unknown")
                else:
                    result["es_ok"] = False
                    result["es_error"] = f"HTTP {resp.status_code}"
            except Exception as exc:
                result["es_ok"] = False
                result["es_error"] = str(exc)

            # Derive and test OTLP
            scenario_id = body.get("scenario_id", ACTIVE_SCENARIO)
            scenario = _get_scenario_by_id(scenario_id)
            deployer = ScenarioDeployer(scenario, elastic_url, kibana_url, api_key)
            explicit_otlp = body.get("otlp_url") or ""
            if explicit_otlp:
                otlp_ok = deployer._verify_otlp_candidate(client, explicit_otlp)
                otlp_url = explicit_otlp if otlp_ok else ""
            else:
                otlp_url = deployer._derive_otlp_endpoint(client) or ""
                otlp_ok = bool(otlp_url)
            result["otlp_ok"] = otlp_ok
            result["otlp_error"] = None if otlp_ok else "Endpoint unreachable"
            result["otlp_endpoint"] = otlp_url or None

    return result


@app.post("/api/setup/launch")
async def launch_setup(body: dict):
    """Launch deployment of a scenario to Elastic.

    Accepts scenario_id + kibana_url + api_key.  Derives ES and OTLP URLs.
    Runs in a background thread. After deployment, creates a ScenarioInstance
    and registers it in the registry + SQLite store.
    """
    from scenarios import get_scenario as _get_scenario_by_id
    from elastic_config.deployer import ScenarioDeployer
    from app.context import ScenarioContext
    from app.instance import ScenarioInstance

    scenario_id = body.get("scenario_id", ACTIVE_SCENARIO)
    _def_elastic, _def_kibana, _def_key = _get_default_creds()
    # Fall back to env vars when the store has no persisted credentials
    if not _def_kibana and KIBANA_URL:
        _def_kibana = KIBANA_URL
    if not _def_key and ELASTIC_API_KEY:
        _def_key = ELASTIC_API_KEY
    if not _def_elastic and ELASTIC_URL:
        _def_elastic = ELASTIC_URL
    kibana_url = body.get("kibana_url", _def_kibana).strip().rstrip("/")
    api_key = body.get("api_key", _def_key).strip()

    elastic_url = _derive_elastic_url(kibana_url, api_key, explicit=body.get("elastic_url") or "") or _def_elastic

    if not kibana_url or not api_key:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing kibana_url or api_key"},
        )

    # Explicit OTLP override from Advanced settings
    explicit_otlp = body.get("otlp_url") or ""

    scenario = _get_scenario_by_id(scenario_id)
    deployer = ScenarioDeployer(scenario, elastic_url, kibana_url, api_key, KIBANA_PROXY)

    # Use scenario_id as deployment_id
    deployment_id = scenario_id

    scenario_name = scenario.scenario_name

    def _progress_cb(progress):
        d = progress.to_dict()
        d["scenario_id"] = scenario_id
        d["scenario_name"] = scenario_name
        _deploy_progress[deployment_id] = d

    def _run():
        # Stop existing instance for this scenario if running
        old_inst = registry.get(deployment_id)
        if old_inst:
            try:
                old_inst.stop()
                logger.info(
                    "Stopped existing instance %s before redeploy", deployment_id
                )
            except Exception as exc:
                logger.warning("Error stopping old instance: %s", exc)

        result = deployer.deploy_all(callback=_progress_cb)

        # Use explicit OTLP override if provided, otherwise use derived
        otlp_endpoint = explicit_otlp or result.otlp_endpoint

        # Create ScenarioContext + ScenarioInstance
        try:
            ctx = ScenarioContext.from_scenario(
                scenario,
                otlp_endpoint=otlp_endpoint or "",
                otlp_api_key=api_key,
                elastic_url=elastic_url,
                elastic_api_key=api_key,
                kibana_url=kibana_url,
            )
            instance = ScenarioInstance(ctx, chaos_store=chaos_store)

            # Reconfigure OTLP if we have an endpoint
            if otlp_endpoint:
                instance.otlp.reconfigure(otlp_endpoint, api_key)
                logger.info(
                    "OTLPClient for %s reconfigured to %s", scenario_id, otlp_endpoint
                )

            instance.start()
            registry.register(deployment_id, instance)

            # Persist to SQLite
            store.upsert(
                deployment_id=deployment_id,
                scenario_id=scenario_id,
                otlp_endpoint=otlp_endpoint or "",
                otlp_api_key=api_key,
                elastic_url=elastic_url,
                elastic_api_key=api_key,
                kibana_url=kibana_url,
            )

            logger.info("Deployment %s (%s) live", deployment_id, scenario_id)
        except Exception as exc:
            logger.exception("Failed to start instance for %s: %s", scenario_id, exc)

    def _on_position(position: int, total: int) -> None:
        entry = _deploy_progress.get(deployment_id)
        if not entry or entry.get("finished"):
            return
        steps = entry.get("steps") or []
        if steps and steps[0].get("name") == "Queued":
            steps[0] = _queued_step(position, total)
        else:
            entry["steps"] = [_queued_step(position, total)]

    existing = _deploy_progress.get(deployment_id)
    if not existing or existing.get("finished"):
        _deploy_progress[deployment_id] = {
            "finished": False, "error": "",
            "scenario_id": scenario_id, "scenario_name": scenario_name,
            "steps": [_queued_step(1, 1)],
        }
    accepted = op_queue.submit_deploy(deployment_id, _run, _on_position)
    if not accepted:
        logger.info("Launch for %s ignored (already active or queued)", deployment_id)

    return {
        "status": "started",
        "scenario": scenario_id,
        "deployment_id": deployment_id,
    }


@app.get("/api/setup/progress")
async def setup_progress(deployment_id: Optional[str] = None):
    """Return current deployment progress."""
    if deployment_id and deployment_id in _deploy_progress:
        return _deploy_progress[deployment_id]
    # Fall back to most recent progress entry
    if _deploy_progress:
        return list(_deploy_progress.values())[-1]
    return {"finished": True, "error": "", "steps": []}


@app.get("/api/setup/active-deploys")
async def active_deploys():
    """Return all deployments currently in progress (auto or manual).

    Ordered: actively running first (in start order), then queued (in queue order).
    The selector UI calls this on page load so it can resume progress panels
    after a browser refresh without losing visibility into running deployments.
    """
    ordered = op_queue.list_ordered("deploy")
    seen = set(ordered)
    # Anything in the progress map that isn't tracked by the queue (e.g., legacy
    # in-flight ops) gets appended at the end so we don't drop it.
    extras = [d for d, p in _deploy_progress.items()
              if not p.get("finished", True) and d not in seen]
    return {
        "deployments": [
            {
                "deployment_id": dep_id,
                "scenario_id": _deploy_progress.get(dep_id, {}).get("scenario_id", dep_id),
                "scenario_name": _deploy_progress.get(dep_id, {}).get("scenario_name", dep_id),
            }
            for dep_id in ordered + extras
            if dep_id in _deploy_progress and not _deploy_progress[dep_id].get("finished", True)
        ]
    }


@app.get("/api/setup/auto-deploy")
async def auto_deploy_status():
    """Return any env-var-triggered auto-deploys that are currently in progress.

    Kept for backward compatibility; the selector UI uses /api/setup/active-deploys.
    """
    deployments = [
        {"deployment_id": s_id}
        for s_id in ACTIVE_SCENARIO_LIST
        if s_id in _deploy_progress and not _deploy_progress[s_id].get("finished", True)
    ]
    return {"deployments": deployments}


@app.get("/api/setup/detect")
async def detect_existing(deployment_id: Optional[str] = None):
    """Check if the active scenario is already deployed to Elastic."""
    from elastic_config.deployer import ScenarioDeployer

    # Try to use credentials from a specific deployment
    inst = _get_instance(deployment_id)
    if inst and inst.ctx.elastic_url and inst.ctx.elastic_api_key:
        elastic_url = inst.ctx.elastic_url
        kibana_url = inst.ctx.kibana_url
        api_key = inst.ctx.elastic_api_key
        scenario = inst.ctx.scenario
    else:
        elastic_url, kibana_url, api_key = _get_default_creds()
        scenario = _get_scenario_for_deployment(deployment_id)

    if not elastic_url or not api_key:
        return {"deployed": False, "error": "No Elastic credentials configured"}

    deployer = ScenarioDeployer(scenario, elastic_url, kibana_url, api_key)
    return deployer.detect_existing()


@app.post("/api/setup/teardown")
async def teardown_setup(body: dict = {}):
    """Remove a scenario's Elastic config (KB, workflows, alerts, etc)."""
    from elastic_config.deployer import ScenarioDeployer

    deployment_id = body.get("deployment_id") if body else None
    inst = _get_instance(deployment_id)

    if inst and inst.ctx.elastic_url and inst.ctx.elastic_api_key:
        elastic_url = inst.ctx.elastic_url
        kibana_url = inst.ctx.kibana_url
        api_key = inst.ctx.elastic_api_key
        scenario = inst.ctx.scenario
    else:
        elastic_url, kibana_url, api_key = _get_default_creds()
        scenario = _get_scenario_for_deployment(deployment_id)

    if not elastic_url or not api_key:
        return JSONResponse(
            status_code=400,
            content={"error": "No Elastic credentials configured"},
        )

    deployer = ScenarioDeployer(scenario, elastic_url, kibana_url, api_key)
    return deployer.teardown()


@app.post("/api/setup/stop-and-teardown")
async def stop_and_teardown(body: dict = {}):
    """Stop generators and remove scenario artifacts from Elastic (async with progress)."""
    from elastic_config.deployer import ScenarioDeployer

    deployment_id = body.get("deployment_id") if body else None

    if not deployment_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="deployment_id is required")

    # If the deploy never started (still queued), cancel it and short-circuit:
    # no Elastic resources to tear down, and we must clear the deploy progress
    # entry so the UI stops polling.
    if op_queue.cancel_deploy(deployment_id):
        logger.info("Cancelled queued deploy %s on teardown request", deployment_id)
        dep = _deploy_progress.get(deployment_id)
        if dep:
            dep["finished"] = True
            dep["error"] = "Cancelled before deployment started"
        _purge_deployment_records(deployment_id)
        _teardown_progress[deployment_id] = {"finished": True, "error": "", "steps": []}
        return {"status": "cancelled", "deployment_id": deployment_id}

    inst = registry.remove(deployment_id)

    if inst and inst.ctx.elastic_url and inst.ctx.elastic_api_key:
        # Stop generators and run teardown together in a background thread so
        # this endpoint returns immediately (inst.stop() can take several seconds).
        deployer = ScenarioDeployer(
            inst.ctx.scenario,
            inst.ctx.elastic_url,
            inst.ctx.kibana_url,
            inst.ctx.elastic_api_key,
        )

        scenario_name = inst.ctx.scenario.scenario_name
        scenario_id = inst.scenario_id

        def _progress_cb(progress):
            d = progress.to_dict()
            d["scenario_id"] = scenario_id
            d["scenario_name"] = scenario_name
            _teardown_progress[deployment_id] = d

        def _run_teardown():
            try:
                inst.stop()
                logger.info("Stopped deployment %s via stop-and-teardown", deployment_id)
            except Exception as exc:
                logger.warning("Error stopping deployment %s: %s", deployment_id, exc)
            deployer.teardown_with_progress(callback=_progress_cb)
            _purge_deployment_records(deployment_id)

        def _on_position(position: int, total: int) -> None:
            entry = _teardown_progress.get(deployment_id)
            if not entry or entry.get("finished"):
                return
            steps = entry.get("steps") or []
            if steps and steps[0].get("name") == "Queued":
                steps[0] = _queued_step(position, total)
            else:
                entry["steps"] = [_queued_step(position, total)]

        _teardown_progress[deployment_id] = {
            "finished": False, "error": "",
            "scenario_id": scenario_id, "scenario_name": scenario_name,
            "steps": [_queued_step(1, 1)],
        }
        op_queue.submit_teardown(deployment_id, _run_teardown, _on_position)
        return {"status": "stopping", "deployment_id": deployment_id}

    # No credentials (or no instance): stop synchronously (fast path) and mark done.
    if inst:
        try:
            inst.stop()
        except Exception as exc:
            logger.warning("Error stopping deployment %s: %s", deployment_id, exc)
    _purge_deployment_records(deployment_id)
    _teardown_progress[deployment_id] = {"finished": True, "error": "", "steps": []}
    return {"status": "stopping", "deployment_id": deployment_id}


@app.get("/api/setup/teardown-progress")
async def teardown_progress(deployment_id: Optional[str] = None):
    """Return current teardown progress."""
    if deployment_id and deployment_id in _teardown_progress:
        return _teardown_progress[deployment_id]
    if _teardown_progress:
        return list(_teardown_progress.values())[-1]
    return {"finished": True, "error": "", "steps": []}


@app.get("/api/setup/active-teardowns")
async def active_teardowns():
    """Return all teardowns that are currently in progress.

    Ordered: actively running first (in start order), then queued (in queue order).
    The selector UI calls this on page load so it can resume progress panels
    after a browser refresh without losing visibility into running teardowns.
    """
    ordered = op_queue.list_ordered("teardown")
    seen = set(ordered)
    extras = [d for d, p in _teardown_progress.items()
              if not p.get("finished", True) and d not in seen]
    return {
        "teardowns": [
            {
                "deployment_id": dep_id,
                "scenario_id": _teardown_progress.get(dep_id, {}).get("scenario_id", dep_id),
                "scenario_name": _teardown_progress.get(dep_id, {}).get("scenario_name", dep_id),
            }
            for dep_id in ordered + extras
            if dep_id in _teardown_progress and not _teardown_progress[dep_id].get("finished", True)
        ]
    }


# ── Run ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=APP_HOST, port=APP_PORT, reload=False)

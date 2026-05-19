// Chaos Controller UI (scenario-aware, session-based ownership)
(function () {
    'use strict';

    let selectedChannel = null;
    let channelData = {};

    // ── Deployment isolation ────────────────────────────────
    const deployId = window.DEPLOYMENT_ID || '';
    const qs = deployId ? '?deployment_id=' + encodeURIComponent(deployId) : '';

    // ── Session-based ownership (namespace-scoped) ──────────
    const ns = window.SCENARIO_NAMESPACE || 'demo';
    const SESSION_KEY = ns + '_chaos_session_id';
    let mySessionId = null;
    let myOwnedChannels = new Set();
    let myEmail = ''; // auto-detected email (from proxy/env), used as session fallback

    function getSessionId() {
        if (mySessionId) return mySessionId;
        try {
            mySessionId = localStorage.getItem(SESSION_KEY) || null;
        } catch { /* ignore */ }
        return mySessionId;
    }

    function generateSessionId() {
        // crypto.randomUUID with fallback
        const id = (crypto.randomUUID && crypto.randomUUID()) ||
            'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
                const r = Math.random() * 16 | 0;
                return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
            });
        mySessionId = id;
        try { localStorage.setItem(SESSION_KEY, id); } catch { /* ignore */ }
        return id;
    }

    function clearSession() {
        mySessionId = null;
        myOwnedChannels.clear();
        try { localStorage.removeItem(SESSION_KEY); } catch { /* ignore */ }
        updateSpikesLock();
    }

    // ── Initialize ────────────────────────────────────────────
    function init() {
        fetchChannels();
        validateSession();
        setInterval(fetchStatus, 2000);
        // Auto-populate email from X-Forwarded-User header; re-validate session with email fallback
        fetch('/api/user/info')
            .then(r => r.json())
            .then(data => {
                if (data.email) {
                    myEmail = data.email;
                    document.getElementById('user-email').value = data.email;
                    validateSession(); // re-run now that we have a detected email
                }
            })
            .catch(() => { /* ignore */ });
    }

    function validateSession() {
        const sid = getSessionId();
        if (!sid && !myEmail) {
            myOwnedChannels.clear();
            updateSpikesLock();
            return;
        }
        const sep = qs ? '&' : '?';
        let url = '/api/chaos/session/validate' + qs + sep + 'session_id=' + encodeURIComponent(sid || '');
        if (myEmail) url += '&user_email=' + encodeURIComponent(myEmail);
        fetch(url)
            .then(r => r.json())
            .then(data => {
                if (data.valid && data.channels && data.channels.length > 0) {
                    myOwnedChannels = new Set(data.channels);
                } else {
                    // Session no longer owns anything — clear it
                    clearSession();
                }
                updateSpikesLock();
            })
            .catch(() => { /* ignore */ });
    }

    function fetchChannels() {
        fetch('/api/chaos/status' + qs)
            .then(r => r.json())
            .then(data => {
                channelData = data;
                populateDropdown(data);
                updateActiveChannels(data);
            })
            .catch(e => console.error('Failed to fetch channels:', e));
    }

    function fetchStatus() {
        fetch('/api/chaos/status' + qs)
            .then(r => r.json())
            .then(data => {
                channelData = data;
                updateActiveChannels(data);
                if (selectedChannel && data[selectedChannel]) {
                    updateChannelInfo(selectedChannel, data[selectedChannel]);
                }
                // Rebuild owned channels set from live data (session or email match)
                const sid = getSessionId();
                if (sid || myEmail) {
                    const newOwned = new Set();
                    for (const [chId, ch] of Object.entries(data)) {
                        if (ch.state !== 'ACTIVE') continue;
                        const sessionMatch = sid && ch.session_id === sid;
                        const emailMatch = myEmail && ch.user_email && ch.user_email === myEmail;
                        if (sessionMatch || emailMatch) {
                            newOwned.add(parseInt(chId));
                        }
                    }
                    myOwnedChannels = newOwned;
                    if (myOwnedChannels.size === 0) {
                        clearSession();
                    }
                }
                updateSpikesLock();
            })
            .catch(() => { /* ignore */ });
    }

    function populateDropdown(data) {
        const select = document.getElementById('channel-select');
        if (select.options.length > 1) return; // already built

        const sortedIds = Object.keys(data).map(Number).sort((a, b) => a - b);
        for (const id of sortedIds) {
            const opt = document.createElement('option');
            opt.value = id;
            const modeLabel = id >= 16 ? ' (Auto-Remediate)' : ' (HITL)';
            opt.textContent = `CH-${String(id).padStart(2, '0')}: ${data[id].name}${modeLabel}`;
            select.appendChild(opt);
        }
    }

    // ── Channel Selection ─────────────────────────────────────
    window.selectChannel = function (value) {
        selectedChannel = value ? parseInt(value) : null;
        const infoEl = document.getElementById('channel-info');
        const btnInject = document.getElementById('btn-inject');
        const btnResolve = document.getElementById('btn-resolve');

        if (!selectedChannel || !channelData[selectedChannel]) {
            infoEl.classList.add('hidden');
            btnInject.disabled = true;
            btnResolve.disabled = true;
            return;
        }

        infoEl.classList.remove('hidden');
        updateChannelInfo(selectedChannel, channelData[selectedChannel]);
    };

    function updateChannelInfo(id, ch) {
        document.getElementById('info-channel').textContent = 'CH-' + String(id).padStart(2, '0');
        document.getElementById('info-name').textContent = ch.name;
        document.getElementById('info-subsystem').textContent = (ch.subsystem || '').toUpperCase();
        document.getElementById('info-section').textContent = (ch.vehicle_section || '').replace(/_/g, ' ').toUpperCase();
        document.getElementById('info-error-type').textContent = ch.error_type || '';
        document.getElementById('info-affected').textContent = (ch.affected_services || []).join(', ');
        document.getElementById('info-description').textContent = ch.description || '';

        const statusEl = document.getElementById('info-status');
        statusEl.textContent = ch.state;
        const styles = getComputedStyle(document.documentElement);
        const critColor = styles.getPropertyValue('--status-critical').trim() || '#ff0000';
        const nomColor = styles.getPropertyValue('--status-nominal').trim() || '#00ff41';
        statusEl.style.color = ch.state === 'ACTIVE' ? critColor : nomColor;

        const btnInject = document.getElementById('btn-inject');
        const btnResolve = document.getElementById('btn-resolve');

        // INJECT: always enabled for STANDBY channels
        btnInject.disabled = ch.state === 'ACTIVE';

        // RESOLVE: only enabled if channel is ACTIVE and we own it (by session or email)
        const sid = getSessionId();
        const isMine = (sid && ch.session_id === sid) || (myEmail && ch.user_email && ch.user_email === myEmail);
        btnResolve.disabled = ch.state !== 'ACTIVE' || !isMine;
    }

    // ── Trigger / Resolve ─────────────────────────────────────
    window.triggerFault = function () {
        if (!selectedChannel) return;
        const mode = document.querySelector('input[name="fault-mode"]:checked').value;
        const userEmail = document.getElementById('user-email').value.trim();
        const callbackUrl = window.location.origin;

        // Generate session_id if we don't have one yet
        const sid = getSessionId() || generateSessionId();

        fetch('/api/chaos/trigger', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                channel: selectedChannel,
                mode: mode,
                se_name: channelData[selectedChannel]?.name || '',
                callback_url: callbackUrl,
                user_email: userEmail,
                session_id: sid,
                deployment_id: deployId || undefined,
            }),
        })
            .then(r => r.json())
            .then(result => {
                if (result.status === 'triggered') {
                    myOwnedChannels.add(selectedChannel);
                    updateSpikesLock();
                }
                fetchStatus();
            })
            .catch(e => console.error('Trigger failed:', e));
    };

    window.resolveFault = function () {
        if (!selectedChannel) return;
        const sid = getSessionId();

        fetch('/api/chaos/resolve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                channel: selectedChannel,
                session_id: sid || '',
                user_email: myEmail || undefined,
                deployment_id: deployId || undefined,
            }),
        })
            .then(r => {
                if (r.status === 403) {
                    r.json().then(d => console.warn('Session mismatch:', d));
                    return null;
                }
                return r.json();
            })
            .then(result => {
                if (!result) return;
                if (result.status === 'resolved') {
                    myOwnedChannels.delete(selectedChannel);
                    if (myOwnedChannels.size === 0) clearSession();
                }
                fetchStatus();
                refreshSpikes();
            })
            .catch(e => console.error('Resolve failed:', e));
    };

    window.resolveChannel = function (channel) {
        const sid = getSessionId();

        fetch('/api/chaos/resolve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                channel: channel,
                session_id: sid || '',
                user_email: myEmail || undefined,
                deployment_id: deployId || undefined,
            }),
        })
            .then(r => {
                if (r.status === 403) {
                    r.json().then(d => console.warn('Session mismatch:', d));
                    return null;
                }
                return r.json();
            })
            .then(result => {
                if (!result) return;
                if (result.status === 'resolved') {
                    myOwnedChannels.delete(channel);
                    if (myOwnedChannels.size === 0) clearSession();
                }
                fetchStatus();
                refreshSpikes();
            })
            .catch(e => console.error('Resolve failed:', e));
    };

    // ── Active Channels Display ───────────────────────────────
    function updateActiveChannels(data) {
        const container = document.getElementById('active-channels');
        const activeIds = Object.keys(data)
            .map(Number)
            .filter(id => data[id].state === 'ACTIVE')
            .sort((a, b) => a - b);

        const sid = getSessionId();

        if (activeIds.length === 0) {
            container.innerHTML = '<div class="no-active">No active faults</div>';
        } else {
            const MAX_DURATION = window.CHANNEL_TIMEOUT || 3600;
            container.innerHTML = activeIds.map(id => {
                const ch = data[id];
                const elapsed = ch.triggered_at ? Math.round((Date.now() / 1000) - ch.triggered_at) : 0;
                const hrs = Math.floor(elapsed / 3600);
                const mins = Math.floor((elapsed % 3600) / 60);
                const secs = elapsed % 60;
                const remaining = Math.max(0, MAX_DURATION - elapsed);
                const remHrs = Math.floor(remaining / 3600);
                const remMins = Math.floor((remaining % 3600) / 60);
                const remSecs = remaining % 60;
                const isMine = (sid && ch.session_id === sid) || (myEmail && ch.user_email && ch.user_email === myEmail);
                const ownerTag = !isMine && ch.session_id
                    ? '<div class="ac-owner-tag">CONTROLLED BY ANOTHER OPERATOR</div>'
                    : '';
                const resolveBtn = isMine
                    ? `<button class="ac-resolve-btn" onclick="resolveChannel(${id})">RESOLVE</button>`
                    : `<button class="ac-resolve-btn" disabled>RESOLVE</button>`;
                const kibanaBase = (window.KIBANA_URL || '').replace(/\/$/, '');
                const alertsUrl = kibanaBase + `/app/observability/alerts?_a=(controlConfigs:!((display_settings:(hide_action_bar:!t),exclude:!f,exists_selected:!f,field_name:kibana.alert.status,selected_options:!(active),title:Status),(display_settings:(hide_action_bar:!f),exclude:!f,exists_selected:!f,field_name:kibana.alert.rule.name,selected_options:!(),title:Rule),(display_settings:(hide_action_bar:!f),exclude:!f,exists_selected:!f,field_name:kibana.alert.group.value,selected_options:!(),title:Group),(display_settings:(hide_action_bar:!f),exclude:!f,exists_selected:!f,field_name:tags,selected_options:!(),title:Tags)),filters:!(),groupings:!(none),kuery:%27%27,rangeFrom:now-2m,rangeTo:now)`;
                const casesUrl = kibanaBase + `/app/observability/cases?cases=(from:now-30d,page:1,perPage:10,sortField:createdAt,sortOrder:desc,to:now)`;
                const kibanaLinks = `<a class="ac-kibana-btn ac-btn-alerts" href="${alertsUrl}" target="_blank" rel="noopener">ALERTS</a>` +
                    `<a class="ac-kibana-btn ac-btn-cases" href="${casesUrl}" target="_blank" rel="noopener">CASES</a>`;
                return `
                    <div class="active-channel-card">
                        <div class="ac-header">
                            <span class="ac-channel">CH-${String(id).padStart(2, '0')}</span>
                            <span class="ac-time">${hrs}h ${mins}m ${secs}s ago</span>
                        </div>
                        <div class="ac-name">${ch.name}</div>
                        <div class="ac-subsystem">${ch.subsystem} | ${(ch.affected_services || []).join(', ')}</div>
                        <div class="ac-expiry">Auto-expires in ${remHrs}h ${remMins}m ${remSecs}s</div>
                        ${ownerTag}
                        <div class="ac-action-row">${resolveBtn}${kibanaLinks}</div>
                    </div>
                `;
            }).join('');
        }

        // Always refresh dropdown to reflect current state
        populateDropdown(data);
    }

    // ── Infrastructure Spikes ─────────────────────────────────
    let spikeDebounceTimer = null;

    function updateSpikesLock() {
        const locked = myOwnedChannels.size === 0;
        const panel = document.querySelector('.spikes-panel');
        if (panel) panel.classList.toggle('locked', locked);
        const duSection = document.querySelector('.daily-update-section');
        if (duSection) duSection.classList.toggle('locked', locked);
    }

    function initSpikes() {
        // Load current spike state
        fetch('/api/chaos/spikes' + qs)
            .then(r => r.json())
            .then(data => {
                setSpikeSlider('spike-cpu', data.cpu_pct || 0, 'spike-cpu-value', formatPct);
                setSpikeSlider('spike-memory', data.memory_pct || 0, 'spike-memory-value', formatPct);
                setSpikeSlider('spike-oom', data.k8s_oom_intensity || 0, 'spike-oom-value', formatPct);
                setSpikeSlider('spike-latency', (data.latency_multiplier || 1.0) * 10, 'spike-latency-value', formatMult);
            })
            .catch(() => { /* ignore */ });

        // Wire up slider events
        wireSlider('spike-cpu', 'spike-cpu-value', formatPct);
        wireSlider('spike-memory', 'spike-memory-value', formatPct);
        wireSlider('spike-oom', 'spike-oom-value', formatPct);
        wireSlider('spike-latency', 'spike-latency-value', formatMult);

        updateSpikesLock();
    }

    function refreshSpikes() {
        fetch('/api/chaos/spikes' + qs)
            .then(r => r.json())
            .then(data => {
                setSpikeSlider('spike-cpu', data.cpu_pct || 0, 'spike-cpu-value', formatPct);
                setSpikeSlider('spike-memory', data.memory_pct || 0, 'spike-memory-value', formatPct);
                setSpikeSlider('spike-oom', data.k8s_oom_intensity || 0, 'spike-oom-value', formatPct);
                setSpikeSlider('spike-latency', (data.latency_multiplier || 1.0) * 10, 'spike-latency-value', formatMult);
            })
            .catch(() => { /* ignore */ });
    }

    function formatPct(val) { return val > 0 ? val + '%' : 'OFF'; }
    function formatMult(val) { return (val / 10).toFixed(1) + 'x'; }

    function setSpikeSlider(sliderId, value, valueId, formatter) {
        const slider = document.getElementById(sliderId);
        const display = document.getElementById(valueId);
        if (!slider || !display) return;
        slider.value = value;
        const formatted = formatter(parseFloat(value));
        display.textContent = formatted;
        const isActive = sliderId === 'spike-latency' ? parseFloat(value) > 10 : parseFloat(value) > 0;
        display.classList.toggle('on', isActive);
        slider.closest('.spike-control').classList.toggle('active', isActive);
    }

    function wireSlider(sliderId, valueId, formatter) {
        const slider = document.getElementById(sliderId);
        if (!slider) return;
        slider.addEventListener('input', function () {
            const val = parseFloat(this.value);
            const display = document.getElementById(valueId);
            display.textContent = formatter(val);
            const isActive = sliderId === 'spike-latency' ? val > 10 : val > 0;
            display.classList.toggle('on', isActive);
            this.closest('.spike-control').classList.toggle('active', isActive);
            debounceSendSpikes();
        });
    }

    function debounceSendSpikes() {
        clearTimeout(spikeDebounceTimer);
        spikeDebounceTimer = setTimeout(sendSpikes, 300);
    }

    function sendSpikes() {
        if (myOwnedChannels.size === 0) return; // locked — no active session
        const cpu = parseFloat(document.getElementById('spike-cpu').value);
        const mem = parseFloat(document.getElementById('spike-memory').value);
        const oom = parseFloat(document.getElementById('spike-oom').value);
        const lat = parseFloat(document.getElementById('spike-latency').value) / 10;

        fetch('/api/chaos/spikes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cpu_pct: cpu,
                memory_pct: mem,
                k8s_oom_intensity: oom,
                latency_multiplier: lat,
                session_id: getSessionId() || '',
                deployment_id: deployId || undefined,
            }),
        })
            .then(r => r.json())
            .catch(e => console.error('Failed to update spikes:', e));
    }

    // ── Daily Update Report ─────────────────────────────────────
    window.sendDailyUpdate = function () {
        const email = (document.getElementById('user-email').value || '').trim();
        if (!email) {
            alert('Please enter an operator email address first.');
            return;
        }

        const btn = document.getElementById('btn-daily-update');
        const statusEl = document.getElementById('update-status');
        btn.disabled = true;
        btn.textContent = 'SENDING...';
        statusEl.textContent = '';
        statusEl.className = 'update-status';

        fetch('/api/daily-update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email, deployment_id: deployId || undefined }),
        })
            .then(r => r.json().then(data => ({ ok: r.ok, data })))
            .then(({ ok, data }) => {
                if (ok) {
                    statusEl.textContent = data.message || 'Report requested — check email in 2-3 min';
                    statusEl.classList.add('success');
                } else {
                    statusEl.textContent = data.error || 'Request failed';
                    statusEl.classList.add('error');
                }
            })
            .catch(() => {
                statusEl.textContent = 'Network error — could not reach server';
                statusEl.classList.add('error');
            })
            .finally(() => {
                btn.disabled = false;
                btn.textContent = 'SEND DAILY UPDATE';
            });
    };

    // ── Start ─────────────────────────────────────────────────
    init();
    initSpikes();
})();

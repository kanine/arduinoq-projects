document.addEventListener('DOMContentLoaded', () => {
    const timingBudgetEl = document.getElementById('timingBudget');

    // Per-sensor element maps
    const sensors = {
        sensor_1: {
            distanceEl:   document.getElementById('s1Distance'),
            onlineEl:     document.getElementById('s1Online'),
            presentEl:    document.getElementById('s1Present'),
            thresholdEl:  document.getElementById('s1Threshold'),
            ageEl:        document.getElementById('s1Age'),
            dataReadyEl:  document.getElementById('s1DataReady'),
            faultTextEl:  document.getElementById('s1FaultText'),
            faultPillEl:  document.getElementById('s1FaultPill'),
            i2cSeenEl:    document.getElementById('s1I2cSeen'),
            initStageEl:  document.getElementById('s1InitStage'),
            lastReadEl:   document.getElementById('s1LastRead'),
            thresholdInput: document.getElementById('s1ThresholdInput'),
            configForm:   document.getElementById('s1ConfigForm'),
            feedbackEl:   document.getElementById('s1ConfigFeedback'),
            lastTick:     null,
            lastSeenAt:   null,
        },
        sensor_2: {
            distanceEl:   document.getElementById('s2Distance'),
            onlineEl:     document.getElementById('s2Online'),
            presentEl:    document.getElementById('s2Present'),
            thresholdEl:  document.getElementById('s2Threshold'),
            ageEl:        document.getElementById('s2Age'),
            dataReadyEl:  document.getElementById('s2DataReady'),
            faultTextEl:  document.getElementById('s2FaultText'),
            faultPillEl:  document.getElementById('s2FaultPill'),
            i2cSeenEl:    document.getElementById('s2I2cSeen'),
            initStageEl:  document.getElementById('s2InitStage'),
            lastReadEl:   document.getElementById('s2LastRead'),
            thresholdInput: document.getElementById('s2ThresholdInput'),
            configForm:   document.getElementById('s2ConfigForm'),
            feedbackEl:   document.getElementById('s2ConfigFeedback'),
            lastTick:     null,
            lastSeenAt:   null,
        },
    };

    function setFaultPill(el, text, level) {
        el.textContent = text;
        el.classList.remove('ok', 'warn', 'neutral');
        el.classList.add(level);
    }

    function renderSensor(sid, data) {
        const els = sensors[sid];
        const now = performance.now();
        let age = null;

        if (typeof data.last_read_ms === 'number') {
            if (data.last_read_ms !== els.lastTick) {
                els.lastTick   = data.last_read_ms;
                els.lastSeenAt = now;
                age = 0;
            } else if (els.lastSeenAt !== null) {
                age = Math.round(now - els.lastSeenAt);
            }
        } else {
            els.lastTick   = null;
            els.lastSeenAt = null;
        }

        const dist = data.distance_mm;
        els.distanceEl.textContent  = typeof dist === 'number' ? String(dist) : '--';
        els.onlineEl.textContent    = data.online ? 'Online' : 'Offline';
        els.presentEl.textContent   = data.object_present ? 'Yes' : 'No';
        els.thresholdEl.textContent = String(data.threshold_mm ?? '--');
        els.ageEl.textContent       = age === null ? '--' : String(age);
        els.dataReadyEl.textContent = data.data_ready ? 'True' : 'False';
        els.faultTextEl.textContent = data.fault || 'No active fault';
        els.i2cSeenEl.textContent   = data.i2c_address_seen ? 'True' : 'False';
        els.initStageEl.textContent = String(data.init_stage ?? 0);
        els.lastReadEl.textContent  = typeof data.last_read_ms === 'number' ? String(data.last_read_ms) : '--';
        els.thresholdInput.value    = String(data.threshold_mm ?? 250);

        if (data.online && !data.fault) {
            setFaultPill(els.faultPillEl, 'Sensor online', 'ok');
        } else if (data.fault) {
            setFaultPill(els.faultPillEl, data.fault, 'warn');
        } else {
            setFaultPill(els.faultPillEl, 'Sensor offline', 'neutral');
        }
    }

    function renderState(tofPayload) {
        const s = tofPayload.sensors || {};
        if (s.sensor_1) renderSensor('sensor_1', s.sensor_1);
        if (s.sensor_2) renderSensor('sensor_2', s.sensor_2);
        if (tofPayload.timing_budget_ms !== undefined) {
            timingBudgetEl.textContent = String(tofPayload.timing_budget_ms);
        }
    }

    async function loadStatus() {
        try {
            const res     = await fetch('/tof/status');
            const payload = await res.json();
            if (payload.ok && payload.tof) {
                renderState(payload.tof);
            }
        } catch (_) {
            // silent — page will retry on next interval
        }
    }

    function makeConfigHandler(sid, els) {
        els.configForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            els.feedbackEl.classList.add('hidden');
            try {
                const res = await fetch('/tof/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ [sid]: { threshold_mm: Number(els.thresholdInput.value) } }),
                });
                const payload = await res.json();
                if (!payload.ok) throw new Error(payload.error || 'Save failed');
                els.feedbackEl.textContent = 'Threshold saved';
                els.feedbackEl.classList.remove('hidden');
                if (payload.status) renderState(payload.status);
            } catch (error) {
                els.feedbackEl.textContent = `Save failed: ${error}`;
                els.feedbackEl.classList.remove('hidden');
            }
        });
    }

    makeConfigHandler('sensor_1', sensors.sensor_1);
    makeConfigHandler('sensor_2', sensors.sensor_2);

    loadStatus();
    setInterval(loadStatus, 500);
});

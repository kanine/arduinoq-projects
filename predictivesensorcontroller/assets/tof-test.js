document.addEventListener('DOMContentLoaded', () => {
    const distanceEl = document.getElementById('tofDistance');
    const onlineEl = document.getElementById('tofOnline');
    const presentEl = document.getElementById('tofPresent');
    const thresholdEl = document.getElementById('tofThreshold');
    const ageEl = document.getElementById('tofAge');
    const timingBudgetEl = document.getElementById('tofTimingBudget');
    const dataReadyEl = document.getElementById('tofDataReady');
    const faultTextEl = document.getElementById('tofFaultText');
    const faultPillEl = document.getElementById('tofFaultPill');
    const healthOnlineEl = document.getElementById('tofHealthOnline');
    const i2cSeenEl = document.getElementById('tofI2cSeen');
    const initStageEl = document.getElementById('tofInitStage');
    const lastReadEl = document.getElementById('tofLastRead');
    const thresholdInput = document.getElementById('tofThresholdInput');
    const configForm = document.getElementById('tofConfigForm');
    const feedbackEl = document.getElementById('tofConfigFeedback');
    let lastSensorReadTick = null;
    let lastSensorReadSeenAt = null;

    function setFaultPill(text, level) {
        faultPillEl.textContent = text;
        faultPillEl.classList.remove('ok', 'warn', 'neutral');
        faultPillEl.classList.add(level);
    }

    function renderState(payload) {
        const tof = payload.tof;
        const health = tof.health || {};
        const distance = tof.distance_mm;
        const now = performance.now();
        let age = null;

        if (typeof tof.last_read_ms === 'number') {
            if (tof.last_read_ms !== lastSensorReadTick) {
                lastSensorReadTick = tof.last_read_ms;
                lastSensorReadSeenAt = now;
                age = 0;
            } else if (lastSensorReadSeenAt !== null) {
                age = Math.round(now - lastSensorReadSeenAt);
            }
        } else {
            lastSensorReadTick = null;
            lastSensorReadSeenAt = null;
        }

        distanceEl.textContent = typeof distance === 'number' ? String(distance) : '--';
        onlineEl.textContent = tof.online ? 'Online' : 'Offline';
        presentEl.textContent = tof.object_present ? 'Yes' : 'No';
        thresholdEl.textContent = String(tof.threshold_mm ?? '--');
        timingBudgetEl.textContent = String(tof.timing_budget_ms ?? '--');
        dataReadyEl.textContent = tof.data_ready ? 'True' : 'False';
        faultTextEl.textContent = tof.fault || 'No active fault';
        healthOnlineEl.textContent = health.online ? 'True' : 'False';
        i2cSeenEl.textContent = (health.i2c_address_seen ?? tof.i2c_address_seen) ? 'True' : 'False';
        initStageEl.textContent = String(health.init_stage ?? tof.init_stage ?? 0);
        lastReadEl.textContent = typeof tof.last_read_ms === 'number' ? String(tof.last_read_ms) : '--';
        ageEl.textContent = age === null ? '--' : String(age);
        thresholdInput.value = String(tof.threshold_mm ?? 250);

        if (tof.online && !tof.fault) {
            setFaultPill('Sensor online', 'ok');
        } else if (tof.fault) {
            setFaultPill(tof.fault, 'warn');
        } else {
            setFaultPill('Sensor offline', 'neutral');
        }
    }

    async function loadStatus() {
        try {
            const res = await fetch('/tof/status');
            const payload = await res.json();
            if (payload.ok && payload.tof) {
                renderState(payload);
                return;
            }
            setFaultPill(payload.error || 'Unable to load status', 'warn');
        } catch (error) {
            setFaultPill(`Request failed: ${error}`, 'warn');
        }
    }

    configForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        feedbackEl.classList.add('hidden');

        try {
            const res = await fetch('/tof/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ threshold_mm: Number(thresholdInput.value) }),
            });
            const payload = await res.json();
            if (!payload.ok) {
                throw new Error(payload.error || 'Save failed');
            }
            feedbackEl.textContent = `Threshold saved: ${payload.threshold_mm} mm`;
            feedbackEl.classList.remove('hidden');
            if (payload.status) {
                renderState({ tof: payload.status });
            }
        } catch (error) {
            feedbackEl.textContent = `Save failed: ${error}`;
            feedbackEl.classList.remove('hidden');
        }
    });

    loadStatus();
    setInterval(loadStatus, 500);
});

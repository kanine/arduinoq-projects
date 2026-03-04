// SPDX-FileCopyrightText: Sonic Sensor App
// SPDX-License-Identifier: MPL-2.0

const elDistance = document.getElementById('distance');
const elPanel = document.getElementById('reading-panel');
const elBadgeRange = document.getElementById('badge-range');
const elBadgeAlert = document.getElementById('badge-alert');
const elBadgeSteady = document.getElementById('badge-steady');
const elStatus = document.getElementById('status-label');
const elTimerPanel = document.getElementById('timer-panel');
const elTimerFill = document.getElementById('timer-fill');
const elCooldownRemaining = document.getElementById('cooldown-remaining');
const elTimeoutInput = document.getElementById('timeout-input');
const elThresholdInput = document.getElementById('threshold-input');
const elSteadyStateBtn = document.getElementById('steady-state-btn');
const elDot = document.getElementById('conn-dot');
const elConnLabel = document.getElementById('conn-label');
const elError = document.getElementById('error-container');
const elHostFile = document.getElementById('host-file-location');
const canvas = document.getElementById('sparkline');
const ctx = canvas.getContext('2d');

const socket = io(`http://${window.location.host}`);

let isConnected = false;
let latestConfig = {
    sensor_timeout_ms: 3000,
    out_of_range_mm: 220,
};

document.addEventListener('DOMContentLoaded', () => {
    if (elHostFile) {
        const appFolder = window.location.pathname.split('/').filter(Boolean)[0] || 'sonic-sensor';
        elHostFile.textContent = `~/${appFolder}`;
    }

    bindConfigInputs();
    initSocket();
});

function bindConfigInputs() {
    elTimeoutInput.addEventListener('input', () => {
        const seconds = Number(elTimeoutInput.value);
        if (Number.isFinite(seconds)) {
            const sensor_timeout_ms = Math.max(200, Math.min(60000, Math.round(seconds * 1000)));
            latestConfig.sensor_timeout_ms = sensor_timeout_ms;
            sendConfigUpdate();
        }
    });

    elThresholdInput.addEventListener('input', () => {
        const threshold = Number(elThresholdInput.value);
        if (Number.isFinite(threshold)) {
            const out_of_range_mm = Math.max(100, Math.min(250, Math.round(threshold)));
            latestConfig.out_of_range_mm = out_of_range_mm;
            sendConfigUpdate();
        }
    });

    elSteadyStateBtn.addEventListener('click', () => {
        if (!isConnected) return;
        socket.emit('set_steady_state', {});
    });
}

function sendConfigUpdate() {
    if (!isConnected) return;
    socket.emit('update_config', latestConfig);
}

function initSocket() {
    socket.on('connect', () => {
        isConnected = true;
        elDot.classList.add('live');
        elConnLabel.textContent = 'live';
        elError.style.display = 'none';
        socket.emit('get_initial_state', {});
        sendConfigUpdate();
    });

    socket.on('disconnect', () => {
        isConnected = false;
        elDot.classList.remove('live');
        elConnLabel.textContent = 'disconnected';
        elError.textContent = 'Connection to the board lost. Please check the connection.';
        elError.style.display = 'block';
    });

    socket.on('sensor_update', (data) => {
        updateUI(data);
    });
}

function updateUI(data) {
    const status = data.status || 'READY';
    const hasReading = Boolean(data.has_reading);
    const mm = data.distance_mm;
    const lastDetectionMm = data.last_detection_mm;
    const timeoutMs = Number(data.sensor_timeout_ms || 0);
    const remainingMs = Number(data.cooldown_remaining_ms || 0);
    const steadyStateCandidate = data.steady_state_candidate_mm;
    const steadyStateConfirmed = data.steady_state_mm;

    if (Number.isFinite(data.sensor_timeout_ms)) {
        latestConfig.sensor_timeout_ms = data.sensor_timeout_ms;
        elTimeoutInput.value = (data.sensor_timeout_ms / 1000).toFixed(1);
    }

    if (Number.isFinite(data.out_of_range_mm)) {
        latestConfig.out_of_range_mm = data.out_of_range_mm;
        elThresholdInput.value = String(data.out_of_range_mm);
    }

    if (Number.isFinite(steadyStateCandidate)) {
        elSteadyStateBtn.textContent = `SET STEADY STATE TO: ${Math.round(steadyStateCandidate)} MM`;
        elSteadyStateBtn.disabled = false;
    } else {
        elSteadyStateBtn.textContent = 'SET STEADY STATE TO: -- MM';
        elSteadyStateBtn.disabled = true;
    }
    elSteadyStateBtn.classList.toggle('confirmed', Number.isFinite(steadyStateConfirmed));

    if (hasReading && mm !== null) {
        elDistance.textContent = String(mm).padStart(4, '0');
    } else {
        elDistance.textContent = '----';
    }

    elStatus.textContent = `STATUS: ${status}`;

    const panelClass = status === 'READY' ? 'state-ready' : status === 'DETECTED' ? 'state-detected' : 'state-cooldown';
    elPanel.className = `reading-panel ${panelClass}`;

    if (status === 'DETECTED') {
        elDistance.className = 'distance state-detected';
    } else if (status === 'COOLDOWN') {
        elDistance.className = 'distance state-cooldown';
    } else if (hasReading) {
        elDistance.className = 'distance state-ready';
    } else {
        elDistance.className = 'distance';
    }

    if ((status === 'DETECTED' || status === 'COOLDOWN') && Number.isFinite(lastDetectionMm)) {
        elBadgeRange.textContent = `DETECTED: ${Math.round(lastDetectionMm)} MM`;
        elBadgeRange.className = 'badge active-green';
    } else {
        elBadgeRange.textContent = 'SEEKING...';
        elBadgeRange.className = 'badge';
    }

    if (status === 'DETECTED') {
        elBadgeAlert.textContent = 'DETECTED';
        elBadgeAlert.className = 'badge active-amber';
    } else if (status === 'COOLDOWN') {
        elBadgeAlert.textContent = 'COOLDOWN';
        elBadgeAlert.className = 'badge active-amber';
    } else {
        elBadgeAlert.textContent = 'READY';
        elBadgeAlert.className = 'badge';
    }

    if (Number.isFinite(steadyStateConfirmed)) {
        elBadgeSteady.textContent = `STEADY: ${Math.round(steadyStateConfirmed)} MM`;
        elBadgeSteady.className = 'badge active-green';
    } else {
        elBadgeSteady.textContent = 'STEADY: -- MM';
        elBadgeSteady.className = 'badge';
    }

    const hasCooldown = status === 'DETECTED' || status === 'COOLDOWN';
    elTimerPanel.classList.toggle('active', hasCooldown);

    const progress = timeoutMs > 0 ? Math.max(0, Math.min(1, remainingMs / timeoutMs)) : 0;
    elTimerFill.style.width = `${(progress * 100).toFixed(1)}%`;
    elCooldownRemaining.textContent = `${(remainingMs / 1000).toFixed(2)}s`;

    drawSparkline(data.history || []);
}

function drawSparkline(history) {
    const dpr = window.devicePixelRatio || 1;
    const W = canvas.offsetWidth * dpr;
    const H = canvas.offsetHeight * dpr;
    canvas.width = W;
    canvas.height = H;

    ctx.clearRect(0, 0, W, H);

    if (history.length < 2) {
        ctx.strokeStyle = 'rgba(30,45,61,1)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, H / 2);
        ctx.lineTo(W, H / 2);
        ctx.stroke();
        return;
    }

    const values = history.map((h) => h.mm);
    const minV = Math.min(...values);
    const maxV = Math.max(...values, minV + 50);
    const range = maxV - minV;

    const toX = (i) => (i / (history.length - 1)) * W;
    const toY = (v) => H - ((v - minV) / range) * H * 0.82 - H * 0.09;

    ctx.strokeStyle = '#1e2d3d';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, H * 0.91);
    ctx.lineTo(W, H * 0.91);
    ctx.stroke();

    const grad = ctx.createLinearGradient(0, 0, 0, H);
    grad.addColorStop(0, 'rgba(0,229,160,0.18)');
    grad.addColorStop(1, 'rgba(0,229,160,0)');

    ctx.beginPath();
    history.forEach((pt, i) => ctx[i === 0 ? 'moveTo' : 'lineTo'](toX(i), toY(pt.mm)));
    ctx.lineTo(W, H);
    ctx.lineTo(0, H);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    ctx.beginPath();
    history.forEach((pt, i) => ctx[i === 0 ? 'moveTo' : 'lineTo'](toX(i), toY(pt.mm)));
    ctx.strokeStyle = 'rgba(0,229,160,0.85)';
    ctx.lineWidth = 1.5 * dpr;
    ctx.lineJoin = 'round';
    ctx.stroke();

    const last = history[history.length - 1];
    ctx.beginPath();
    ctx.arc(toX(history.length - 1), toY(last.mm), 3 * dpr, 0, Math.PI * 2);
    ctx.fillStyle = '#00e5a0';
    ctx.fill();
}

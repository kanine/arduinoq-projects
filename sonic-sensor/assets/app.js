// SPDX-FileCopyrightText: Sonic Sensor App
// SPDX-License-Identifier: MPL-2.0

// ── Element refs ──────────────────────────────────────────────────────────────
const elDistance  = document.getElementById('distance');
const elPanel     = document.getElementById('reading-panel');
const elBadgeRange = document.getElementById('badge-range');
const elBadgeAlert = document.getElementById('badge-alert');
const elDot       = document.getElementById('conn-dot');
const elConnLabel = document.getElementById('conn-label');
const elError     = document.getElementById('error-container');
const elHostFile  = document.getElementById('host-file-location');
const canvas      = document.getElementById('sparkline');
const ctx         = canvas.getContext('2d');

// ── Socket ────────────────────────────────────────────────────────────────────
const socket = io(`http://${window.location.host}`);

document.addEventListener('DOMContentLoaded', () => {
    if (elHostFile) {
        const appFolder = window.location.pathname.split('/').filter(Boolean)[0] || 'sonic-sensor';
        elHostFile.textContent = `~/${appFolder}`;
    }
    initSocket();
});

function initSocket() {
    socket.on('connect', () => {
        elDot.classList.add('live');
        elConnLabel.textContent = 'live';
        elError.style.display = 'none';

        // Ask for current state immediately on connect
        socket.emit('get_initial_state', {});
    });

    socket.on('disconnect', () => {
        elDot.classList.remove('live');
        elConnLabel.textContent = 'disconnected';
        elError.textContent = 'Connection to the board lost. Please check the connection.';
        elError.style.display = 'block';
    });

    socket.on('sensor_update', (data) => {
        updateUI(data);
    });
}

// ── UI update ─────────────────────────────────────────────────────────────────
function updateUI(data) {
    const inRange    = data.in_range;
    const alertActive = data.alert_active;
    const mm         = data.distance_mm;

    // ── Distance value ──
    if (inRange && mm !== null) {
        elDistance.textContent = String(mm).padStart(4, '0');
        elDistance.className   = alertActive ? 'distance state-alert' : 'distance state-inrange';
    } else {
        elDistance.textContent = '----';
        elDistance.className   = 'distance';
    }

    // ── Panel state ──
    if (alertActive) {
        elPanel.className = 'reading-panel state-alert';
    } else if (inRange) {
        elPanel.className = 'reading-panel state-inrange';
    } else {
        elPanel.className = 'reading-panel';
    }

    // ── Range badge ──
    if (inRange) {
        elBadgeRange.textContent = 'IN RANGE';
        elBadgeRange.className   = 'badge active-green';
    } else {
        elBadgeRange.textContent = 'OUT OF RANGE';
        elBadgeRange.className   = 'badge';
    }

    // ── Alert badge ──
    if (alertActive) {
        elBadgeAlert.textContent = 'ALERT ACTIVE';
        elBadgeAlert.className   = 'badge active-amber';
    } else {
        elBadgeAlert.textContent = 'ALERT INACTIVE';
        elBadgeAlert.className   = 'badge';
    }

    // ── Sparkline ──
    drawSparkline(data.history || []);
}

// ── Sparkline renderer ────────────────────────────────────────────────────────
function drawSparkline(history) {
    const dpr = window.devicePixelRatio || 1;
    const W   = canvas.offsetWidth  * dpr;
    const H   = canvas.offsetHeight * dpr;
    canvas.width  = W;
    canvas.height = H;

    ctx.clearRect(0, 0, W, H);

    if (history.length < 2) {
        // Draw empty baseline
        ctx.strokeStyle = 'rgba(30,45,61,1)';
        ctx.lineWidth   = 1;
        ctx.beginPath();
        ctx.moveTo(0, H / 2);
        ctx.lineTo(W, H / 2);
        ctx.stroke();
        return;
    }

    const values = history.map(h => h.mm);
    const minV   = Math.min(...values);
    const maxV   = Math.max(...values, minV + 50); // min 50mm spread to avoid flat line
    const range  = maxV - minV;

    const toX = (i) => (i / (history.length - 1)) * W;
    const toY = (v) => H - ((v - minV) / range) * H * 0.82 - H * 0.09;

    // Grid baseline
    ctx.strokeStyle = '#1e2d3d';
    ctx.lineWidth   = 1;
    ctx.beginPath();
    ctx.moveTo(0, H * 0.91);
    ctx.lineTo(W, H * 0.91);
    ctx.stroke();

    // Filled area
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

    // Line
    ctx.beginPath();
    history.forEach((pt, i) => ctx[i === 0 ? 'moveTo' : 'lineTo'](toX(i), toY(pt.mm)));
    ctx.strokeStyle = 'rgba(0,229,160,0.85)';
    ctx.lineWidth   = 1.5 * dpr;
    ctx.lineJoin    = 'round';
    ctx.stroke();

    // Latest value dot
    const last = history[history.length - 1];
    ctx.beginPath();
    ctx.arc(toX(history.length - 1), toY(last.mm), 3 * dpr, 0, Math.PI * 2);
    ctx.fillStyle = '#00e5a0';
    ctx.fill();
}

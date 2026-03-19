const distanceValue = document.getElementById('distance-value');
const rawValue      = document.getElementById('raw-value');
const themeBtn      = document.getElementById('theme-toggle');
const appNameText   = document.getElementById('app-name-text');
const percentLabel  = document.getElementById('percent-label');
const progressBar   = document.getElementById('progress-bar');
let errorContainer;
let consoleLogToggle;

let currentSettings = { startMeasure: null, windowSeconds: null };

const socket = io(`http://${window.location.host}`);

/* ── Theme ── */
const savedTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', savedTheme);
themeBtn.textContent = savedTheme === 'dark' ? '☀️' : '🌙';

themeBtn.addEventListener('click', () => {
    const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    themeBtn.textContent = next === 'dark' ? '☀️' : '🌙';
});

/* ── Socket ── */
document.addEventListener('DOMContentLoaded', () => {
    errorContainer = document.getElementById('error-container');
    consoleLogToggle = document.getElementById('console-log-toggle');

    const savedLoggingPreference = localStorage.getItem('tof-console-log') === 'true';
    if (consoleLogToggle) {
        consoleLogToggle.checked = savedLoggingPreference;
        consoleLogToggle.addEventListener('change', () => {
            localStorage.setItem('tof-console-log', String(consoleLogToggle.checked));
        });
    }

    const showReadingToggle  = document.getElementById('show-reading-toggle');
    const readingSection     = document.getElementById('reading-section');
    const applyReadingVisibility = (visible) => {
        readingSection.style.display = visible ? 'flex' : 'none';
    };
    const savedReadingPref = localStorage.getItem('filament-show-reading') === 'true';
    showReadingToggle.checked = savedReadingPref;
    applyReadingVisibility(savedReadingPref);
    showReadingToggle.addEventListener('change', () => {
        localStorage.setItem('filament-show-reading', String(showReadingToggle.checked));
        applyReadingVisibility(showReadingToggle.checked);
    });

    socket.on('connect', () => {
        if (errorContainer) errorContainer.style.display = 'none';
    });

    socket.on('distance_update', (msg) => {
        const avg = msg.average;
        const raw = msg.distance;
        const pct = msg.percent;
        const readings = Array.isArray(msg.readings) ? msg.readings : [];
        const appName = typeof msg.app_name === 'string' ? msg.app_name : '';

        // Update progress bar and label
        if (pct !== null && pct !== undefined) {
            const pctRounded = Math.round(pct);
            percentLabel.textContent = `${pctRounded}% Remaining`;
            progressBar.style.width = `${pct}%`;
            if (pct > 50) {
                progressBar.style.backgroundColor = '#22a34a';
            } else if (pct > 20) {
                progressBar.style.backgroundColor = '#e6a817';
            } else {
                progressBar.style.backgroundColor = '#e03131';
            }
        } else {
            percentLabel.textContent = '--% Remaining';
            progressBar.style.width = '0%';
        }

        // Display average as main value
        if (avg === -1 || avg > 4000) {
            distanceValue.textContent = '--';
        } else {
            distanceValue.textContent = avg;
        }

        // Display raw as smaller subtitle if available
        if (raw === -1 || raw > 4000) {
            rawValue.textContent = 'raw: --';
        } else {
            rawValue.textContent = `raw: ${raw} mm`;
        }

        if (appNameText && appName) {
            appNameText.textContent = `app: ${appName}`;
        }

        if (msg.settings) {
            currentSettings = msg.settings;
        }

        // Keep live average visible in settings modal
        const liveAvg = document.getElementById('settings-live-avg');
        if (liveAvg) {
            liveAvg.textContent = (avg !== -1 && avg <= 4000) ? avg : '--';
        }

        if (consoleLogToggle && consoleLogToggle.checked) {
            console.log('ToF 2s batch update', {
                appName,
                percent: pct,
                average: avg,
                raw,
                readings,
            });
        }
    });

    socket.on('disconnect', () => {
        if (errorContainer) {
            errorContainer.textContent = 'Connection to the board lost. Please check the connection.';
            errorContainer.style.display = 'block';
        }
    });

    /* ── Settings modal ── */
    const settingsBtn    = document.getElementById('settings-btn');
    const settingsModal  = document.getElementById('settings-modal');
    const settingsClose  = document.getElementById('settings-close');
    const settingsSave   = document.getElementById('settings-save');
    const inputStart     = document.getElementById('settings-start-measure');
    const inputWindow    = document.getElementById('settings-window');

    socket.on('settings', (msg) => {
        currentSettings = msg;
        if (settingsModal.classList.contains('open')) {
            inputStart.value = msg.startMeasure;
            inputWindow.value = msg.windowSeconds;
        }
    });

    settingsBtn.addEventListener('click', () => {
        // Populate with current known values, then request fresh from backend
        if (currentSettings.startMeasure !== null) inputStart.value = currentSettings.startMeasure;
        if (currentSettings.windowSeconds !== null) inputWindow.value = currentSettings.windowSeconds;
        settingsModal.classList.add('open');
        socket.emit('get_settings', {});
    });

    settingsClose.addEventListener('click', () => settingsModal.classList.remove('open'));
    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) settingsModal.classList.remove('open');
    });

    settingsSave.addEventListener('click', () => {
        const newStart  = parseFloat(inputStart.value);
        const newWindow = parseFloat(inputWindow.value);
        if (!isNaN(newStart) && newStart > 0 && !isNaN(newWindow) && newWindow > 0) {
            socket.emit('settings_update', { startMeasure: newStart, windowSeconds: newWindow });
            settingsModal.classList.remove('open');
        }
    });

    /* ── Wiring modal ── */
    const wiringBtn   = document.getElementById('wiring-btn');
    const wiringModal = document.getElementById('wiring-modal');
    const modalClose  = document.getElementById('modal-close');

    wiringBtn.addEventListener('click', () => wiringModal.classList.add('open'));
    modalClose.addEventListener('click', () => wiringModal.classList.remove('open'));
    wiringModal.addEventListener('click', (e) => {
        if (e.target === wiringModal) wiringModal.classList.remove('open');
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') wiringModal.classList.remove('open');
    });
});

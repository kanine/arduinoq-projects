const distanceValue = document.getElementById('distance-value');
const rawValue      = document.getElementById('raw-value');
const themeBtn      = document.getElementById('theme-toggle');
const appNameText   = document.getElementById('app-name-text');
let errorContainer;
let consoleLogToggle;

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

    socket.on('connect', () => {
        if (errorContainer) errorContainer.style.display = 'none';
    });

    socket.on('distance_update', (msg) => {
        const avg = msg.average;
        const raw = msg.distance;
        const readings = Array.isArray(msg.readings) ? msg.readings : [];
        const appName = typeof msg.app_name === 'string' ? msg.app_name : '';

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

        if (consoleLogToggle && consoleLogToggle.checked) {
            console.log('ToF 2s batch update', {
                appName,
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

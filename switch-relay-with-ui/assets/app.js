const relayToggle = document.getElementById('relay-toggle');
const relayText   = document.getElementById('relay-text');
const indicator   = document.getElementById('indicator');
const themeBtn    = document.getElementById('theme-toggle');
let errorContainer;

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

/* ── UI update ── */
function updateUI(isOn) {
    relayToggle.checked   = isOn;
    relayText.textContent = isOn ? 'RELAY ON' : 'RELAY OFF';
    indicator.className   = 'indicator ' + (isOn ? 'on' : 'off');
}

/* ── Socket ── */
document.addEventListener('DOMContentLoaded', () => {
    errorContainer = document.getElementById('error-container');

    socket.on('connect', () => {
        socket.emit('get_initial_state', {});
        if (errorContainer) errorContainer.style.display = 'none';
    });

    socket.on('relay_status_update', (msg) => updateUI(msg.relay_is_on));

    socket.on('disconnect', () => {
        if (errorContainer) {
            errorContainer.textContent = 'Connection to the board lost. Please check the connection.';
            errorContainer.style.display = 'block';
        }
    });

    relayToggle.addEventListener('change', () => socket.emit('toggle_relay', {}));

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

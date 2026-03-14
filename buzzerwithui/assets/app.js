// SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
//
// SPDX-License-Identifier: MPL-2.0

const buzzerToggle = document.getElementById('buzzer-toggle');
const statusText = document.getElementById('status-text');
let errorContainer;

const intervalSlider = document.getElementById('interval-slider');
const durationSlider = document.getElementById('duration-slider');
const loopsSlider   = document.getElementById('loops-slider');
const intervalValue = document.getElementById('interval-value');
const durationValue = document.getElementById('duration-value');
const loopsValue    = document.getElementById('loops-value');
const durationRow   = document.getElementById('duration-row');
const loopsRow      = document.getElementById('loops-row');

/*
 * Socket initialization. We need it to communicate with the server.
 */
const socket = io(`http://${window.location.host}`);

document.addEventListener('DOMContentLoaded', () => {
    errorContainer = document.getElementById('error-container');
    initSocketIO();

    // Send toggle message when the switch is clicked
    buzzerToggle.addEventListener('change', handleToggleChange);

    // Wiring modal
    const wiringBtn = document.getElementById('wiring-btn');
    const wiringModal = document.getElementById('wiring-modal');
    const modalClose = document.getElementById('modal-close');

    wiringBtn.addEventListener('click', () => wiringModal.classList.add('open'));
    modalClose.addEventListener('click', () => wiringModal.classList.remove('open'));
    wiringModal.addEventListener('click', (e) => {
        if (e.target === wiringModal) wiringModal.classList.remove('open');
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') wiringModal.classList.remove('open');
    });

    // Slider init
    intervalSlider.addEventListener('input', updateSliderUI);
    durationSlider.addEventListener('input', updateSliderUI);
    loopsSlider.addEventListener('input', updateSliderUI);
    updateSliderUI();
});

function initSocketIO() {
    socket.on('connect', () => {
        // Request initial buzzer state on connection
        socket.emit('get_initial_state', {});
        if (errorContainer) {
            errorContainer.style.display = 'none';
            errorContainer.textContent = '';
        }
    });

    socket.on('buzzer_status_update', (message) => {
        updateBuzzerStatus(message);
    });

    socket.on('disconnect', () => {
        if (errorContainer) {
            errorContainer.textContent = 'Connection to the board lost. Please check the connection.';
            errorContainer.style.display = 'block';
        }
    });
}

/*
 * Update the toggle switch and status label based on the server's buzzer state.
 */
function updateBuzzerStatus(status) {
    const isOn = status.buzzer_is_on;
    const hwOn = status.buzzer_hw_on !== undefined ? status.buzzer_hw_on : isOn;
    buzzerToggle.checked = isOn;
    statusText.textContent = isOn ? 'BUZZER ON' : 'BUZZER OFF';
    statusText.className = isOn ? 'status-text status-on' : 'status-text';
    document.getElementById('buzzer-visual').classList.toggle('active', hwOn);
}

/*
 * Send the explicit desired state to the Python backend when the switch changes.
 * Slider values are included so the backend knows the requested pattern.
 */
function handleToggleChange() {
    const intervalSteps = parseInt(intervalSlider.value);
    socket.emit('toggle_buzzer', {
        state:    buzzerToggle.checked,
        interval: intervalSteps * 0.25,
        duration: parseInt(durationSlider.value) * 0.25,
        loops:    parseInt(loopsSlider.value)
    });
}

/*
 * Update slider value labels and enable/disable duration & loops rows.
 * Duration and loops only apply when interval > 0 (pulsed mode).
 */
function updateSliderUI() {
    const steps = parseInt(intervalSlider.value);
    intervalValue.textContent = steps === 0 ? 'Continuous' : `${(steps * 0.25).toFixed(2)} s`;
    durationValue.textContent = `${(parseInt(durationSlider.value) * 0.25).toFixed(2)} s`;
    loopsValue.textContent    = loopsSlider.value;
    const pulsed = steps > 0;
    durationRow.classList.toggle('disabled', !pulsed);
    loopsRow.classList.toggle('disabled', !pulsed);
}

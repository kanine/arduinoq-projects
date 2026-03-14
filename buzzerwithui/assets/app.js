// SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
//
// SPDX-License-Identifier: MPL-2.0

const buzzerToggle = document.getElementById('buzzer-toggle');
const statusText = document.getElementById('status-text');
let errorContainer;

/*
 * Socket initialization. We need it to communicate with the server.
 */
const socket = io(`http://${window.location.host}`);

document.addEventListener('DOMContentLoaded', () => {
    errorContainer = document.getElementById('error-container');
    initSocketIO();

    // Send toggle message when the switch is clicked
    buzzerToggle.addEventListener('change', handleToggleChange);
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
    buzzerToggle.checked = isOn;
    statusText.textContent = isOn ? 'BUZZER ON' : 'BUZZER OFF';
    statusText.className = isOn ? 'status-text status-on' : 'status-text';
}

/*
 * Send the explicit desired state to the Python backend when the switch changes.
 */
function handleToggleChange() {
    socket.emit('toggle_buzzer', { state: buzzerToggle.checked });
}

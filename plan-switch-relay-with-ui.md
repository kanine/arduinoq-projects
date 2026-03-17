# Plan: switch-relay-with-ui

Clone `copy-of-blink-led-with-ui` and adapt it to control a 1-channel relay module via **D8** with a minimal web toggle UI.

---

## Goal

A web page with a single ON/OFF toggle button.
Clicking it sends a Socket.io message → Python MPU → Bridge RPC → MCU sketch → `digitalWrite(8, …)`.
The relay state is reflected back to the UI in real time.

---

## Relay Hardware Notes (condensed)

| Parameter | Value |
|---|---|
| Control pin | D8 (3.3 V output) |
| Trigger current | 5 mA (optocoupler) |
| Trigger polarity | Jumper-selectable — **default assumed: HIGH = relay ON** |
| Max load | AC 250 V / 10 A; DC 30 V / 10 A |
| Terminals | NC, C, NO; Coil+, Coil−, Trigger |
| Isolation | Optocoupler — safe for direct MCU connection |

> Full relay specs are documented in `switch-relay-with-ui/relay-specs.md`.

---

## File Structure to Create

```
switch-relay-with-ui/
├── app.yaml
├── relay-specs.md          ← relay hardware documentation
├── sketch/
│   ├── sketch.ino
│   └── sketch.yaml
├── python/
│   └── main.py
└── assets/
    ├── index.html
    ├── app.js
    └── style.css           ← copy from source; minor label changes only
```

Assets that can be copied verbatim (no logic changes):
- `assets/style.css` — update only the title text if desired
- `assets/` static libs folder (fonts, socket.io, favicon, Arduino logo SVG)

---

## Step-by-Step Implementation

### Step 1 — Create folder skeleton

```
mkdir -p switch-relay-with-ui/{sketch,python,assets}
```

Copy the entire `assets/` subtree from `copy-of-blink-led-with-ui/assets/` (fonts, img, libs, style.css).

---

### Step 2 — `app.yaml`

```yaml
name: Switch Relay with UI
description: Control a 1-channel relay module on D8 via web toggle
ports: []
bricks:
  - arduino:web_ui: {}
icon: 🔌
```

---

### Step 3 — `sketch/sketch.yaml`

Identical to source — no additional libraries needed:

```yaml
profiles:
  default:
    platforms:
      - platform: arduino:zephyr
    libraries:
      - Arduino_RouterBridge (0.2.2)
      - dependency: Arduino_RPClite (0.2.0)
      - dependency: ArxContainer (0.7.0)
      - dependency: ArxTypeTraits (0.3.2)
      - dependency: DebugLog (0.8.4)
      - dependency: MsgPack (0.4.2)
default_profile: default
```

---

### Step 4 — `sketch/sketch.ino`

Key changes from source:
- Replace `LED_BUILTIN` with pin `8`
- Rename RPC function to `set_relay_state`
- `HIGH` = relay ON (matches default jumper position; invert if jumper is set to LOW-trigger)
- No active-low inversion needed (relay is not active-low)

```cpp
#include <Arduino_RouterBridge.h>

void set_relay_state(bool state) {
    digitalWrite(8, state ? HIGH : LOW);
}

void setup() {
    pinMode(8, OUTPUT);
    digitalWrite(8, LOW);   // relay OFF on boot

    Bridge.begin();
    Bridge.provide("set_relay_state", set_relay_state);
}

void loop() {}
```

> `Bridge.provide()` callback is defined **before** `setup()` — required by Bridge rules.

---

### Step 5 — `python/main.py`

Key changes from source:
- Rename state variable to `relay_is_on`
- Rename socket events: `toggle_relay`, `relay_status_update`, `get_initial_state`
- Bridge call targets `set_relay_state`
- Status text: "RELAY ON" / "RELAY OFF"

```python
from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI

relay_is_on = False

def get_relay_status():
    return {
        "relay_is_on": relay_is_on,
        "status_text": "RELAY ON" if relay_is_on else "RELAY OFF"
    }

def toggle_relay(client, data):
    global relay_is_on
    relay_is_on = not relay_is_on
    Bridge.call("set_relay_state", relay_is_on)
    ui.send_message('relay_status_update', get_relay_status())

def on_get_initial_state(client, data):
    ui.send_message('relay_status_update', get_relay_status(), client)

ui = WebUI()
ui.on_message('toggle_relay', toggle_relay)
ui.on_message('get_initial_state', on_get_initial_state)

App.run()
```

---

### Step 6 — `assets/index.html`

Minimal changes from source:
- Title → "Switch Relay"
- Button id → `relay-button`
- Text span id → `relay-text`
- Instruction text → "Click to toggle relay on D8"

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Switch Relay</title>
    <link rel="icon" type="image/png" href="./img/favicon.png">
    <link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
    <div>
        <div class="header">
            <h1 class="arduino-text">Switch Relay</h1>
            <img class="arduino-logo" src="./img/RGB-Arduino-Logo_Color Inline Loop.svg" alt="Arduino Logo">
        </div>
        <div class="container">
            <div class="led-container">
                <button id="relay-button" class="led-off">
                    <span id="relay-text">RELAY OFF</span>
                </button>
            </div>
            <p class="instruction-text">Click to toggle relay on D8</p>
            <div id="error-container" class="error-message" style="display: none;"></div>
        </div>
    </div>
    <script src="libs/socket.io.min.js"></script>
    <script src="app.js"></script>
</body>
</html>
```

---

### Step 7 — `assets/app.js`

Key changes from source:
- All `led` → `relay` in variable names and DOM ids
- Socket events: `toggle_relay`, `relay_status_update`
- `relay_is_on` field from server payload

```javascript
const relayButton = document.getElementById('relay-button');
const relayText = document.getElementById('relay-text');
let errorContainer;

const socket = io(`http://${window.location.host}`);

document.addEventListener('DOMContentLoaded', () => {
    errorContainer = document.getElementById('error-container');
    initSocketIO();
    relayButton.addEventListener('click', () => socket.emit('toggle_relay', {}));
});

function initSocketIO() {
    socket.on('connect', () => {
        socket.emit('get_initial_state', {});
        if (errorContainer) errorContainer.style.display = 'none';
    });

    socket.on('relay_status_update', (message) => {
        const isOn = message.relay_is_on;
        relayButton.className = isOn ? 'led-on' : 'led-off';
        relayText.textContent = isOn ? 'RELAY ON' : 'RELAY OFF';
    });

    socket.on('disconnect', () => {
        if (errorContainer) {
            errorContainer.textContent = 'Connection to the board lost. Please check the connection.';
            errorContainer.style.display = 'block';
        }
    });
}
```

---

### Step 8 — `relay-specs.md`

Create `switch-relay-with-ui/relay-specs.md` with the full relay hardware specifications (see below).

---

### Step 9 — Sync and run

```bash
./bash/sync_to_uno1.sh switch-relay-with-ui
ssh uno1 arduino-app-cli app start "/home/arduino/ArduinoApps/switch-relay-with-ui"
ssh uno1 arduino-app-cli app logs  "/home/arduino/ArduinoApps/switch-relay-with-ui"
```

Confirm the Network URL printed in the logs, then open `http://<board-ip>:7000/` in a browser.

---

## Wiring (ATN-IO v3 summary)

```
[BOARD]
  D8 → Relay Trigger terminal

[POWER]
  Board 5V → Relay Coil+ (VCC)
  Board GND → Relay Coil− (GND)

[NOTES]
  - Jumper set to HIGH-trigger (default)
  - Connect load between NO and C terminals for normally-open operation
  - Do NOT exceed 10 A / 250 VAC on the load side
```

> A full ATN-IO v3 wiring document can be generated with the `atn-io-wiring-notation` skill if needed.

---

## Risks / Decisions

| Item | Decision |
|---|---|
| Trigger polarity | HIGH = ON (jumper default). If jumper is LOW-trigger, invert `state ? HIGH : LOW` in sketch |
| Boot state | Relay OFF (`LOW`) on power-up — safe default |
| Power supply for coil | Board 5 V rail if < 100 mA total draw; otherwise use external 5 V supply |
| Load wiring | Use NO (normally open) terminal for safe-off-on-power-loss behaviour |

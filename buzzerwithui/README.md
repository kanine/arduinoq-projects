# Buzzer with UI

A simple Arduino UNO Q application that lets you turn an active buzzer on or off using a web toggle switch.

## Description

This app exposes a toggle switch in the browser. Flipping the switch sends a WebSocket message to the Python backend running on the MPU, which relays the command over the Router Bridge to the MCU sketch. The sketch sets a GPIO pin HIGH or LOW to activate or deactivate the DFR0032 Digital Buzzer Module.

```
Browser Toggle → WebSocket → Python Backend → Router Bridge → MCU GPIO → DFR0032 Buzzer
```

## Bricks Used

- `web_ui`: Serves the HTML/JS frontend and handles WebSocket communication.

## Hardware and Software Requirements

### Hardware

- Arduino UNO Q (×1)
- DFR0032 Digital Buzzer Module (×1) — DFRobot Gravity 3-pin active buzzer module
- USB-C® cable for power and programming (×1)
- 3 × male–female jumper wires

### Software

- Arduino App Lab

## Wiring

```
ATN-IO v3
Project: Buzzer with UI – DFR0032 on Arduino UNO Q

[BOARD]
TYPE  = Arduino UNO Q
LOGIC = 3.3V
MCU   = STM32U585

[OUTPUTS]
BUZZ_SIG -> D8    # digital signal to DFR0032 S pin

[COMPONENTS]
BUZZ1 = DFR0032, DFRobot Digital Buzzer Module, active, 3.3V–5V

[WIRING]
# ── DFR0032 signal ────────────────────────────────────────────
D8    -> BUZZ1.S      # HIGH = buzzer ON, LOW = buzzer OFF

# ── DFR0032 power ─────────────────────────────────────────────
3.3V  -> BUZZ1.VCC    # module operates at 3.3 V–5 V; 3.3 V compatible with Uno Q GPIO
GND   -> BUZZ1.GND

[NOTES]
# DFR0032 has a built-in NPN transistor driver — no current-limiting resistor required.
# The module's signal threshold is well within the 3.3 V logic level of the UNO Q MCU.
# HIGH on D8 energises the buzzer; LOW silences it.
# Avoid connecting the signal pin to Serial1 (reserved by arduino-router).
```

## How to Use

1. Wire the DFR0032 module as shown above.
2. Deploy and start the app:
   ```bash
   arduino-app-cli app start "/home/arduino/ArduinoApps/buzzerwithui"
   ```
3. Open a browser and navigate to `http://<UNO-Q-IP-ADDRESS>:7000`.
4. Use the toggle switch to turn the buzzer on or off.

## How it Works

### Backend (`python/main.py`)

- `ui = WebUI()` — initialises the web server and WebSocket handler.
- `ui.on_message('toggle_buzzer', toggle_buzzer_state)` — listens for the toggle event from the browser.
- `Bridge.call("set_buzzer_state", buzzer_is_on)` — sends the new state to the MCU sketch via RPC.
- `ui.send_message('buzzer_status_update', ...)` — broadcasts the updated state to all connected browser clients.

### Frontend (`assets/index.html` + `assets/app.js`)

- `socket.emit('toggle_buzzer', {})` — fires when the user flips the toggle switch.
- `socket.on('buzzer_status_update', updateBuzzerStatus)` — receives the confirmed state and updates the switch and label.

### MCU (`sketch/sketch.ino`)

- `Bridge.provide("set_buzzer_state", set_buzzer_state)` — registers the RPC endpoint.
- `set_buzzer_state(bool state)` — writes `HIGH` or `LOW` to pin D8 to drive the DFR0032 module.

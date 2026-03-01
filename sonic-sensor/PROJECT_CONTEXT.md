# Project Context: Sonic Sensor App

> This document provides full context for an agentic coding assistant working on this project.
> It covers hardware, decisions made, code architecture, and outstanding considerations.
> Last updated: 2026-03-01

---

## 1. Project Goal

Build an ultrasonic distance sensor application on an **Arduino Uno Q** that:
- Reads distance from an HC-SR04 sensor
- Applies configurable out-of-range detection and alert timeout logic
- Serves a live web dashboard over WiFi using the Uno Q's built-in App Lab framework
- Pushes real-time sensor updates to connected browsers via WebSocket

---

## 2. Hardware

### Primary Board: Arduino Uno Q
- Dual-core board: **STM32U585** microcontroller (MCU) + **Qualcomm QRB2210** running full **Debian Linux** (MPU)
- GPIO operates at **3.3V logic** — this is critical
- Runs Arduino's **App Lab** framework which bridges MCU (C++ sketch) and MPU (Python/Debian) via an internal RPC bridge library

### Sensor: HC-SR04 Ultrasonic
- Operates at **5V**
- TRIG pin: receives signal from Uno Q D6 — 3.3V output is sufficient to trigger, no issue
- ECHO pin: outputs **5V** back — **this is a problem for the 3.3V Uno Q GPIO**

### ECHO Voltage Divider (REQUIRED)
A resistor voltage divider must be wired on the ECHO line before connecting to D7:

```
HC-SR04 ECHO → [10kΩ] → D7 → [20kΩ] → GND
```

This brings the 5V ECHO signal down to ~3.3V, safe for the Uno Q's GPIO pin.

### Why No Display or Shift Register
The original project (on an Arduino Mega 2560) used:
- 74HC595 shift register to drive segment lines
- 5641AS 4-digit 7-segment display

These were deliberately **dropped** when migrating to the Uno Q because:
- The web dashboard replaces the physical display
- Removing the 74HC595 (a 5V device) eliminates the main 3.3V/5V compatibility concern
- The HC-SR04 ECHO line is the **only remaining 5V compatibility issue**, solved by the voltage divider above

### Pin Assignments
| Signal | Uno Q Pin |
|--------|-----------|
| HC-SR04 TRIG | D6 |
| HC-SR04 ECHO (via divider) | D7 |

---

## 3. Software Architecture

This is an **Arduino App Lab** application. App Lab is Arduino's framework for the Uno Q that bundles MCU sketch code, Python MPU code, and web assets into a single deployable app.

### Folder Structure
```
sonic-sensor-app/
├── app.yaml                  # App Lab manifest
├── README.md                 # Hardware setup and run instructions
├── sketch/
│   ├── sketch.ino            # MCU: reads HC-SR04, exposes get_distance() via Bridge
│   └── sketch.yaml           # Board target and library dependencies
├── python/
│   └── main.py               # MPU: polls Bridge, applies logic, serves WebUI
└── assets/
    ├── index.html            # Dashboard markup
    ├── style.css             # Dark industrial theme
    ├── app.js                # Socket.io client + sparkline chart renderer
    └── libs/
        └── socket.io.min.js  # Bundled — copy from sample-blink-with-ui/assets/libs/
```

### app.yaml
```yaml
name: Sonic Sensor
description: HC-SR04 ultrasonic distance sensor with live web dashboard and alerts
ports: []
bricks:
- arduino:web_ui: {}
icon: 📡
```

### How the Two Sides Communicate
- MCU sketch registers an RPC method: `Bridge.provide("get_distance", get_distance)`
- Python MPU calls it: `Bridge.call("get_distance", False)`
- The Bridge returns `[distance_mm, in_range_flag]`
- Python then pushes updates to the browser via `ui.send_message("sensor_update", payload)`
- Browser receives via `socket.on("sensor_update", ...)` using the bundled socket.io

### WebUI Brick
App Lab's `arduino:web_ui` brick handles all WebSocket/HTTP serving internally.
- Do NOT use Flask, SocketIO, or any external server — the `WebUI` class handles everything
- Import pattern: `from arduino.app_bricks.web_ui import WebUI`
- Message API: `ui.on_message(event, handler)` and `ui.send_message(event, payload, client=None)`
- `App.run()` takes **no arguments** — it is blocking and starts everything
- Dashboard is served on **port 7000**

### Key App Lab API Patterns (confirmed from source + live testing)
```python
from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI

ui = WebUI()
ui.on_message('some_event', handler_fn)     # receive from browser
ui.send_message('some_event', data)         # broadcast to all browsers
ui.send_message('some_event', data, client) # send to one client only
App.run()                                   # blocking, starts the app

# Bridge.call() returns the value directly — not wrapped in a list
mm = int(Bridge.call("get_distance"))
```

```cpp
// sketch.ino MCU side
#include <Arduino_RouterBridge.h>
Bridge.begin();
Bridge.provide("method_name", handler_fn);  // register RPC

// IMPORTANT: Bridge has NO respond() method.
// The handler's RETURN VALUE is automatically sent back to the caller.
// Use typed return values — void functions return nothing to Python.
int get_distance() {
    return lastDistanceMM;   // Python receives this directly as an int
}
```

---

## 4. Configurable Parameters

Set at the top of **both** `sketch/sketch.ino` and `python/main.py`. They must be kept in sync manually.

| Parameter | Default | Location | Description |
|-----------|---------|----------|-------------|
| `OUT_OF_RANGE` | 2000 mm | sketch + python | Readings >= this treated as no target |
| `SENSOR_TIMEOUT` | 3.0 s | python only | Alert stays active this long after last in-range hit |
| `MEASURE_INTERVAL` | 100 ms | sketch | Time between sensor reads |
| `POLL_INTERVAL` | 0.15 s | python | Time between Bridge.call() polls |

---

## 5. Alert Logic

Implemented in `python/main.py`:

- Every in-range reading **restarts** the `SENSOR_TIMEOUT` timer and keeps the alert active
- If no in-range reading arrives within `SENSOR_TIMEOUT` seconds, alert goes inactive
- Out-of-range state: dashboard shows `----`, badges show OUT OF RANGE / ALERT INACTIVE
- In-range state: dashboard shows distance in mm, IN RANGE / ALERT ACTIVE badges illuminate

Distance formula (in sketch): `mm = (echo_duration_us * 343) / 2000`

---

## 6. Demo Mode

`sketch/sketch.ino` includes a `DEMO_MODE` compile flag for testing the full pipeline without hardware attached.

```cpp
// Line 17 of sketch.ino — comment out to enable real sensor
#define DEMO_MODE
```

When `DEMO_MODE` is defined:
- `pulseIn()` is never called (avoids blocking/floating pin issues)
- `pinMode()` setup for TRIG/ECHO is skipped
- A fake reading cycles: ramps 200mm → 1800mm over 8 seconds, then -1 (out of range) for 2 seconds, repeats
- This exercises the full Bridge → Python → WebUI → browser pipeline end to end

To switch to real hardware: comment out `#define DEMO_MODE` — no other changes needed.

---

## 7. sketch.yaml Library Dependencies

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

Note: sub-libraries use `dependency:` prefix — this is the correct App Lab format.

---

## 8. Dashboard (Web UI)

- Dark industrial theme, monospace font (Roboto Mono)
- Live distance reading display (shows `----` when out of range)
- IN RANGE / OUT OF RANGE badge (green when active)
- ALERT ACTIVE / ALERT INACTIVE badge (amber when active)
- Sparkline chart of last 20 readings with gradient fill
- Connection status indicator (live dot)
- Disconnect error message if board connection drops

Socket event flow:
- On connect → browser emits `get_initial_state` → Python sends current state back to that client only
- Every `POLL_INTERVAL` → Python emits `sensor_update` to all connected clients

---

## 9. Board Selection History

The following boards were considered and why the Uno Q was chosen:

| Board | Verdict | Reason |
|-------|---------|--------|
| Arduino Mega 2560 | Original dev board | Used for initial sketch development. No WiFi, no Linux side. Good for hardware testing. |
| Arduino Uno Q | **Selected** | Debian Linux + MCU in one board. App Lab framework. Built-in WiFi. Runs the web dashboard natively. |
| Arduino Uno R4 WiFi | Strong alternative | 5V compatible, drop-in wiring replacement, built-in WiFi, cheaper. Better if display hardware retained. |
| Arduino Uno WiFi Rev2 | Rejected | 8-bit AVR, older generation, twice the price of R4 WiFi for less capability. |

---

## 10. Wiring History & What Was Dropped

The Mega 2560 version used:
- 74HC595 shift register (DATA=D8, LATCH=D9, CLK=D10)
- 5641AS 4-digit 7-segment display (DIG1=D2, DIG2=D3, DIG3=D4, DIG4=D5)
- HC-SR04 (TRIG=D6, ECHO=D7)
- Software multiplexing at 4ms per digit
- Segment table: `{0x3f, 0x06, 0x5b, 0x4f, 0x66, 0x6d, 0x7d, 0x07, 0x7f, 0x6f}` (0–9)

All display hardware was dropped for the Uno Q version. The web dashboard replaces it.

---

## 11. Outstanding Considerations / Known Unknowns

- **Bridge RPC return pattern (CONFIRMED)**: `Bridge.respond()` does not exist. The sketch handler must be a typed function whose **return value** is automatically sent back to Python by the bridge internals. `void` handlers return nothing. Python receives the value directly from `Bridge.call("method")` — not wrapped in a list.
- **Bridge.call() return format (CONFIRMED)**: Python receives a single value directly, e.g. `mm = int(Bridge.call("get_distance"))`. No unpacking needed.
- **App Lab is pre-1.0**: The framework is still early stage. APIs may change between versions. Always check the installed version of `arduino.app_utils` and `arduino.app_bricks.web_ui` against current docs.
- **socket.io.min.js**: Must be copied manually from the sample app — do not use a CDN as the board may not have internet access: `cp ~/ArduinoApps/sample-blink-with-ui/assets/libs/socket.io.min.js ~/ArduinoApps/sonic-sensor-app/assets/libs/`
- **DEMO_MODE must be commented out** before connecting real hardware or readings will be fake.
- **Voltage divider on ECHO is mandatory** before connecting HC-SR04 to a live board.

---

## 12. Running the App

```bash
cd ~/ArduinoApps
arduino-app run sonic-sensor-app
```

Dashboard available at `http://<board-ip>:7000`

To find the board's IP:
```bash
hostname -I
```

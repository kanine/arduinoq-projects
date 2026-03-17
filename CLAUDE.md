# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

This repo lives in a **WSL container on Windows** (not on the board). The board is `uno1` (SSH host alias), accessed remotely.

- **Local repo:** `/home/kanine/arduino-local/uno1/arduinoq-projects/`
- **Remote deploy path:** `/home/arduino/ArduinoApps/<app-name>/` on `uno1`
- **Sync to board:** `./bash/sync_to_uno1.sh [app-name ...]`
- **Board RAM is limited** — keep the repo in WSL, not on the board.

- **Board IP:** varies by LAN — run `ssh uno1 hostname -I` to get the current address
- **Web UI port:** `7000` — apps with the `web_ui` brick are reachable at `http://<board-ip>:7000/`
- **Confirm URL from logs:** `ssh uno1 arduino-app-cli app logs "/home/arduino/ArduinoApps/<app-name>"` prints the exact Network URL on startup

All `arduino-app-cli` commands run on `uno1` via SSH:

```bash
ssh uno1 arduino-app-cli app start "/home/arduino/ArduinoApps/<app-name>"
ssh uno1 arduino-app-cli app stop "/home/arduino/ArduinoApps/<app-name>"
ssh uno1 arduino-app-cli app restart "/home/arduino/ArduinoApps/<app-name>"
ssh uno1 arduino-app-cli app logs "/home/arduino/ArduinoApps/<app-name>"
ssh uno1 arduino-app-cli app list
ssh uno1 sudo reboot   # sudo is available on uno1
```

## Board Architecture

The Arduino Uno Q is a **dual-processor board**:

| Processor | Chip | OS | Handles |
|---|---|---|---|
| MPU | Qualcomm QRB2210 (4× Cortex-A53 @ 2 GHz) | Debian Linux | Python, networking, web UI, high-level logic |
| MCU | STM32U585 (Cortex-M33 @ 160 MHz) | Zephyr OS | Arduino sketches, GPIO, ADC, PWM, SPI, I2C, UART |

All GPIOs are **3.3 V**. Use level shifters for 5 V components.

**I2C buses:**
- `Wire` → header pins SDA/SCL (D20/D21)
- `Wire1` → Qwiic/STEMMA QT connector (I2C4, pins PD13/PD12) — use this for Qwiic sensors

**Reserved — do not use:**
- `Serial1` (MCU/Zephyr) — reserved by `arduino-router`
- `/dev/ttyHS1` (Linux) — reserved by `arduino-router`

**Other peripherals:**
- PWM pins: D3, D5, D6, D9, D10, D11 (fixed 500 Hz)
- SPI: SS=D10, MOSI=D11, MISO=D12, SCK=D13
- 8×13 blue LED matrix (MCU-controlled, `Arduino_LED_Matrix.h`)
- RGB LEDs #3 and #4 are **active low** (`LOW` = ON)

## App Structure

Apps are discovered by the presence of `app.yaml` in their top-level directory.

```
<app-name>/
├── app.yaml          # Metadata + brick declarations (web_ui, dbstorage_sqlstore, etc.)
├── sketch/
│   ├── sketch.ino    # MCU code (C++/Arduino, runs on STM32)
│   └── sketch.yaml   # Platform (arduino:zephyr) + library declarations
├── python/
│   └── main.py       # MPU code (Python, runs on Linux)
├── assets/           # Web UI static files (HTML, CSS, JS) — optional
└── README.md
```

## Build Precedence

When constructing or modifying apps, use this order:

1. Relevant skill(s) from `.agents/`
2. Nearest matching `copy-of-*` project (local clones of official Arduino examples)
3. Other local project folders
4. Official Arduino documentation

Prefer adapting the closest `copy-of-*` project over scaffolding from scratch.

## Bridge / RPC Rules

**MCU side (`sketch.ino`):**
```cpp
#include <Arduino_RouterBridge.h>

int my_value() { return lastVal; }  // define BEFORE setup()

void setup() {
    Bridge.begin();
    Bridge.provide("my_value", my_value);      // runs in high-priority thread — keep short
    Bridge.provide_safe("my_cmd", my_cmd);     // runs in loop() — use for digitalWrite/Serial
}
```

**MPU side (`python/main.py`):**
```python
from arduino.app_utils import App, Bridge

result = Bridge.call("my_value")
App.run(user_loop=loop)
```

**Critical rules:**
- `Bridge.provide()` callbacks: no `Bridge.call()` or `Monitor.print()` inside (deadlock)
- `Bridge.provide_safe()` for anything touching GPIO or Serial
- Probe I2C with `Wire1.beginTransmission(addr)` / `Wire1.endTransmission()` before calling library `begin()`/`init()`
- `Bridge.provide()` functions must be defined before `setup()` (no forward declarations work)
- Use `Monitor.println()` not `Serial.println()` for App Lab console output

## sketch.yaml Pitfalls

- **Never** declare a library in `sketch.yaml` AND include its source files in `sketch/libraries/` — causes duplicate symbol linker errors
- List all `Arduino_RouterBridge` dependencies explicitly: `RPClite`, `ArxContainer`, `ArxTypeTraits`, `DebugLog`, `MsgPack`
- For VL53L1X: use Pololu `VL53L1X (1.3.1)` — Adafruit's version copies source files into the sketch root and always causes duplicates

## Wiring Documentation

Hardware connections must use **ATN-IO v3** format (see `wiring-notation.md`). Sections: `[BOARD]`, `[INPUTS]`, `[OUTPUTS]`, `[COMPONENTS]`, `[WIRING]`, `[POWER]`, `[NOTES]`.

## Skills

All agent skills live in `.agents/skills/<skill-name>/SKILL.md`. Key skills:
- `arduino-uno-q-app-dev/` — app anatomy, bricks, Bridge patterns
- `arduino-app-cli/` — CLI reference and troubleshooting
- `uno-q-vl53l1x-integration/` — VL53L1X ToF sensor patterns
- `arduino-dbstorage-sqlstore/` — SQLStore brick usage
- `web-coder/` — web UI (Socket.io, HTML/CSS/JS)
- `atn-io-wiring-notation/` — ATN-IO v3 wiring file creation and validation

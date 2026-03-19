

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

This repo lives in a **WSL container on Windows** (not on the board). The board is `uno1` (SSH host alias), accessed remotely.

- **Local repo:** `/home/kanine/arduino-local/uno1/`
- **Remote deploy path:** `/home/arduino/ArduinoApps/<app-name>/` on `uno1`
- **Sync to board:** `./bash/sync_to_uno1.sh [app-name ...]`
- **Board RAM is limited** — keep the repo in WSL, not on the board.

- **Board IP:** varies by LAN — run `ssh uno1 hostname -I` to get the current address
- **Web UI port:** `7000` — apps with the `web_ui` brick are reachable at `http://<board-ip>:7000/`
- **Confirm URL from logs:** `ssh uno1 arduino-app-cli app logs "/home/arduino/ArduinoApps/<app-name>" --all` prints the exact Network URL on startup

## Remote Deploy Workflow

The standard remote workflow is:

1. Edit locally in this repo.
2. Sync the app directory to the board:
   ```bash
   ./bash/sync_to_uno1.sh <app-name>
   ```
   Optional preflight:
   ```bash
   ./bash/sync_to_uno1.sh --dry-run <app-name>
   ```
3. Restart the remote app over SSH:
   ```bash
   ssh uno1 arduino-app-cli app restart "/home/arduino/ArduinoApps/<app-name>"
   ```
4. Check status and logs over SSH:
   ```bash
   ssh uno1 arduino-app-cli app list
   ssh uno1 arduino-app-cli app logs "/home/arduino/ArduinoApps/<app-name>" --all
   ```

Notes:
- Always sync from the host repo first; do not edit files directly on the board unless explicitly needed.
- Quote full remote app paths in SSH commands.
- `app restart` recompiles/uploads the sketch and reprovisions the Python container, so it can take a little while.
- During restart, `ssh uno1 arduino-app-cli app list` may briefly show the app as `stopped` even though the restart is still in progress. Wait for the restart command to finish, then check `app list` again.
- Only one app can run at a time. If restart returns `Another App ... Is Running`, stop the currently running app first, then retry restart.
- If you need the exact browser URL, prefer `app logs ... --all` because startup logs print the network address.

All `arduino-app-cli` commands run on `uno1` via SSH:

```bash
ssh uno1 arduino-app-cli app start "/home/arduino/ArduinoApps/<app-name>"
ssh uno1 arduino-app-cli app stop "/home/arduino/ArduinoApps/<app-name>"
ssh uno1 arduino-app-cli app restart "/home/arduino/ArduinoApps/<app-name>"
ssh uno1 arduino-app-cli app logs "/home/arduino/ArduinoApps/<app-name>" --all
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

**Wireless:** WCBN3536A — dual-band Wi-Fi® 5 (2.4/5 GHz) and Bluetooth® 5.1 (connected to MPU).
**Memory:** 2 GB or 4 GB LPDDR4 RAM; 16 GB or 32 GB eMMC storage.

**I2C buses:**
- `Wire` → header pins SDA/SCL (D20/D21)
- `Wire1` → Qwiic/STEMMA QT connector (I2C4, pins PD13/PD12) — use this for Qwiic sensors

**Reserved — do not use:**
- `Serial1` (MCU/Zephyr) — reserved by `arduino-router`
- `/dev/ttyHS1` (Linux) — reserved by `arduino-router`

**Other peripherals:**
- 47× digital pins (22 on UNO headers + 25 on JMISC)
- 6× 14-bit ADC pins (A0–A5); 2× DAC outputs (DAC0/DAC1 on A0/A1)
- PWM pins: D3, D5, D6, D9, D10, D11 (fixed 500 Hz)
- SPI: SS=D10, MOSI=D11, MISO=D12, SCK=D13
- UART: TX=D1 (PB6), RX=D0 (PB7)
- 8×13 blue LED matrix (MCU-controlled, `Arduino_LED_Matrix.h`; supports up to 8 grayscale levels via `matrix.setGrayscaleBits(bits)`)
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

## Official Sample Policy

Only top-level folders prefixed with `copy-of-` are local clones of official Arduino App Lab examples:

- `copy-of-blink-led`
- `copy-of-blink-led-with-ui`
- `copy-of-led-matrix-painter`
- `copy-of-qr-and-barcode-scanner`
- `copy-of-system-resources-logger`
- `copy-of-weather-forecast-on-led-matrix`

Other top-level app folders (e.g. `alphabetmatrix`, `sonic-sensor`) are local workspace projects — useful references, but do not override official sample patterns when a matching `copy-of-*` exists.

When a matching official sample clone exists, give it precedence for: `app.yaml` layout, `python/main.py` lifecycle patterns, `sketch/sketch.ino` Bridge/RPC structure, `assets/` UI integration, naming and data-flow conventions.

## Application Construction Workflow

- Check `.agents/skills/` for matching skills first.
- Inspect the nearest matching `copy-of-*` app before editing or scaffolding code.
- Reuse official sample patterns for file layout, brick choice, Bridge APIs, and UI structure.
- Use non-`copy-of-*` local apps only when no relevant official sample clone exists or when they contain workspace-specific behaviour the user explicitly wants to preserve.
- If no local official sample clone matches, use skill guidance and official Arduino documentation before introducing a new pattern.

## Python (MPU side — `python/main.py`)

- Import from `arduino.app_utils` for board helpers (`App`, `Bridge`, `Leds`, etc.).
- Use `App.run(user_loop=loop)` as the main entry point.
- Interact with Linux system interfaces (e.g. `/sys/class/leds/`) for MPU-controlled LEDs.
- The `arduino-router` service handles MPU↔MCU communication; do **not** open `/dev/ttyHS1` directly.

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

All agent skills live in `.agents/skills/<skill-name>/SKILL.md`. Each skill has its own folder:

```
.agents/skills/<skill-name>/
  SKILL.md              # required
  agents/openai.yaml    # recommended
  references/           # optional
  scripts/              # optional
  assets/               # optional
```

**Key skills:**
- `arduino-uno-q-app-dev/` — app anatomy, bricks, Bridge patterns
- `arduino-app-cli/` — CLI reference and troubleshooting
- `uno-q-vl53l1x-integration/` — VL53L1X ToF sensor patterns
- `arduino-dbstorage-sqlstore/` — SQLStore brick usage
- `web-coder/` — web UI (Socket.io, HTML/CSS/JS)
- `atn-io-wiring-notation/` — ATN-IO v3 wiring file creation and validation
- `arduino-uno-q-examples/` — identify the closest official example family

**Rules:**
- When a task matches an existing skill, read and follow that skill's `SKILL.md` first.
- Load only the needed `references/` files; avoid bulk-loading all references.
- Create new skills only under `.agents/skills/<skill-name>/`. Never duplicate to `.codex/skills` or `.gemini/skills`.
- Keep `SKILL.md` concise; put large details in `references/`.
- Add `agents/openai.yaml` when the skill should be discoverable in skill lists/chips.

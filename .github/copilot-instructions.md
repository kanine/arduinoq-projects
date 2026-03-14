# GitHub Copilot Instructions

## Project Overview

This workspace contains Arduino applications targeting the **Arduino UNO Q** — a new, high-performance single-board computer that combines a Qualcomm® QRB2210 microprocessor (MPU) running Debian Linux with an STMicroelectronics® STM32U585 microcontroller (MCU) running Zephyr OS, all on a single board in the classic UNO form factor.

**Official documentation:** https://docs.arduino.cc/tutorials/uno-q/user-manual/

---

## Board Architecture

The UNO Q has a **dual-processor architecture**:

- **MPU (Qualcomm QRB2210):** Quad-core Arm® Cortex®-A53 @ 2.0 GHz, runs Debian Linux. Handles high-level logic, Python scripts, networking, and Linux services.
- **MCU (STM32U585):** Arm® Cortex®-M33 @ 160 MHz, runs Zephyr OS. Handles real-time control, Arduino sketches, GPIO, ADC, PWM, SPI, I2C, UART.
- **Wireless:** WCBN3536A — dual-band Wi-Fi® 5 (2.4/5 GHz) and Bluetooth® 5.1 (connected to MPU).
- **Memory:** 2 GB or 4 GB LPDDR4 RAM; 16 GB or 32 GB eMMC storage.

---

## App Structure

Each application in this workspace follows this structure:

```
app-name/
  app.yaml          # App metadata and configuration
  python/
    main.py         # Python script runs on the MPU (Qualcomm Linux side)
  sketch/
    sketch.ino      # Arduino sketch runs on the MCU (STM32 Zephyr side)
    sketch.yaml
  assets/           # Web UI assets (HTML, CSS, JS) served from the MPU
```

Apps are developed with **Arduino App Lab** (v0.1.23+) and deployed using `arduino-app-cli`.

---

## Build Precedence

When constructing or modifying Arduino UNO Q applications in this repository, use this order of precedence:

1. Relevant skill(s) from `.agents/`
2. Local official sample clones in top-level folders prefixed with `copy-of-`
3. Other local project folders in this repository
4. Official Arduino documentation.

Do not invent a new app structure or interaction pattern until the relevant skills and the nearest `copy-of-*` project have been checked.

---

## Official Sample Policy

Only top-level folders prefixed with `copy-of-` should be treated as local copies of official Arduino App Lab examples.

Current local official sample clones:

- `copy-of-blink-led`
- `copy-of-led-matrix-painter`
- `copy-of-weather-forecast-on-led-matrix`

Other top-level app folders such as `alphabetmatrix`, `alphabetmatrixadvanced`, `sample-blink-with-ui`, and `sonic-sensor` are local workspace projects. They may still be useful references, but they do not override official sample patterns when a matching `copy-of-*` example exists.

When a matching official sample clone exists, give its code and structure precedence for:

- `app.yaml` layout and brick selection
- `python/main.py` patterns and App Lab lifecycle usage
- `sketch/sketch.ino` Bridge/RPC structure and hardware control patterns
- `assets/` organization and UI integration
- naming, wiring, and data-flow conventions

Prefer adapting the closest `copy-of-*` project with minimal changes rather than creating a fresh implementation from scratch.

---

## Skills (Canonical Location)

All agent skills are consolidated in:

`/.agents/skills/`

Each skill must live in its own folder:

```
.agents/skills/
  <skill-name>/
    SKILL.md              # required
    agents/openai.yaml    # recommended
    references/           # optional
    scripts/              # optional
    assets/               # optional
```

### Skill Usage

- When a task matches an existing skill, read and follow that skill’s `SKILL.md` first.
- Resolve any relative links from `SKILL.md` relative to that skill folder.
- Load only the needed `references/` files; avoid bulk-loading all references.
- For app construction work, combine skills with the nearest matching `copy-of-*` project instead of treating them as alternatives.
- Use `.agents/skills/arduino-uno-q-examples/` to identify the closest official example family before falling back to non-`copy-of-*` local projects.

### Skill Generation / Creation

- Create new skills only under `.agents/skills/<skill-name>/`.
- Keep `SKILL.md` concise and procedural:
  - include YAML frontmatter with `name` and `description`
  - include trigger guidance (when to use)
  - include workflow steps and references to optional files
- Put large details in `references/` instead of bloating `SKILL.md`.
- Add `agents/openai.yaml` when the skill should be discoverable in skill lists/chips.

### Adding or Updating Skills

- Do not add or maintain duplicate skill copies in `.codex/skills` or `.gemini/skills`.
- Any new or updated skill must be added/edited in `.agents/skills/` only.
- If a path reference to old skill locations exists, update it to `.agents/skills/`.

---

## Key Development Guidelines

### Application Construction Workflow

- Start by checking `.agents/skills/` for matching skills.
- Then inspect the nearest matching `copy-of-*` app before editing or scaffolding code.
- Reuse official sample patterns for file layout, brick choice, Bridge APIs, and UI structure.
- Use non-`copy-of-*` local apps only when no relevant official sample clone exists or when they contain workspace-specific behavior the user explicitly wants to preserve.
- If no local official sample clone matches, use the relevant skill guidance and official Arduino documentation before introducing a new pattern.

### Python (MPU side — `python/main.py`)
- Import from `arduino.app_utils` for board-specific helpers (`App`, `Bridge`, `Leds`, etc.).
- Use `App.run(user_loop=loop)` as the main entry point.
- Interact with Linux system interfaces (e.g., `/sys/class/leds/`) for MPU-controlled LEDs.
- The `arduino-router` service handles communication between MPU and MCU; do **not** open `/dev/ttyHS1` directly.

### Arduino Sketch (MCU side — `sketch/sketch.ino`)
- Always `#include <Arduino_RouterBridge.h>` when using Bridge, Monitor, or network features.
- Call `Bridge.begin()` in `setup()` to initialize MPU↔MCU communication.
- Use `Monitor.println()` instead of `Serial.println()` when targeting the App Lab console.
- Use `Bridge.provide()` to expose MCU functions to the MPU (Python) side.
- Use `Bridge.call()` to invoke Python-side functions from the MCU.
- **Do not use `Serial1`** — it is reserved by the `arduino-router` service.
- RGB LEDs #3 and #4 (`LED3_R/G/B`, `LED4_R/G/B`) are **active low** (write `LOW` to turn ON).

### Bridge / RPC Communication
- The Bridge library wraps `Arduino_RPClite` for bidirectional MPU↔MCU RPC.
- `Bridge.provide(name, fn)` — exposes MCU function to Python; runs in a high-priority thread (keep short and thread-safe).
- `Bridge.provide_safe(name, fn)` — executes in the main `loop()` context; use for calls involving `digitalWrite`, `Serial`, etc.
- Do **not** call `Bridge.call()` or `Monitor.print()` inside a `provide()` callback (causes deadlocks).

### Web UI (assets/)
- Static files in `assets/` are served by the MPU and displayed in the App Lab UI.
- Use `socket.io` for real-time communication between the web UI and Python backend.

### Pins & Peripherals
- 47x digital pins (22 on UNO headers + 25 on JMISC) controlled by the STM32 MCU.
- 6x 14-bit ADC pins (A0–A5), 2x DAC outputs (DAC0/DAC1 on A0/A1).
- 6x PWM pins (D3, D5, D6, D9, D10, D11) — PWM frequency is fixed at 500 Hz.
- SPI: SS=D10, MOSI=D11, MISO=D12, SCK=D13.
- I2C: SDA=D20, SCL=D21 (primary `Wire`); Qwiic connector uses I2C4 (`Wire1`, 3.3 V only).
- UART: TX=D1 (PB6), RX=D0 (PB7).

### Onboard LED Matrix
- 8×13 blue LED matrix controlled by the STM32 MCU.
- Use `#include <Arduino_LED_Matrix.h>` and `matrix.begin()` / `matrix.draw(frame)`.
- Supports up to 8 grayscale levels via `matrix.setGrayscaleBits(bits)`.

---

## CLI Reference

```bash
arduino-app-cli app list               # List deployed apps
arduino-app-cli app start <id>         # Start an app
arduino-app-cli app start <path>         # Start an app path
arduino-app-cli app restart <id>       # Restart (or start) an app
arduino-app-cli app restart <path>     # Restart (or start) an app path
arduino-app-cli app stop <id>          # Stop an app
arduino-app-cli app stop <path>        # Stop an app path
arduino-app-cli app logs <id>          # Show Python app logs
arduino-app-cli app logs <path>        # Show Python app logs for a path
arduino-app-cli properties get default # Get startup app
arduino-app-cli properties set default <id>  # Set startup app
```

`<id>` examples: `user:sonic-sensor`, `examples:blink-with-ui`.

`<path>` example cli: 
- `arduino-app-cli app start "/home/arduino/ArduinoApps/test"`
- `arduino-app-cli app stop "/home/arduino/ArduinoApps/test"`

---

## Reserved Resources (Do Not Use)

| Resource | Reserved By |
|---|---|
| `/dev/ttyHS1` (Linux) | `arduino-router` service |
| `Serial1` (MCU/Zephyr) | `arduino-router` service |

---

## Additional Resources

- [UNO Q User Manual](https://docs.arduino.cc/tutorials/uno-q/user-manual/) ← primary reference
- [UNO Q Power Specifications](https://docs.arduino.cc/tutorials/uno-q/power-specification/)
- [Arduino App Lab Documentation](https://docs.arduino.cc/software/app-lab/)
- [Arduino Forum — UNO Q](https://forum.arduino.cc/c/official-hardware/uno-family/uno-q/222)
- [Arduino_RouterBridge Library](https://github.com/arduino-libraries/Arduino_RouterBridge)
- [Arduino Router Service](https://github.com/arduino/arduino-router)
- [Command Line Interface (CLI) Reference](https://docs.arduino.cc/software/app-lab/tutorials/cli/)

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

## Sample Code Fallback Policy

- Treat any top-level project folder in this repository (for example `alphabetmatrix/`, `sample-blink-with-ui/`, `sonic-sensor/`) as containing official Arduino sample code.
- When official documentation or local skills do not provide enough detail for a task, use these project folders as the primary pattern reference for:
  - app structure and configuration
  - Bridge/RPC usage between `python/main.py` and `sketch/sketch.ino`
  - CLI and deployment conventions
  - UI and asset organization
- Prefer adapting patterns from the closest matching sample project before inventing a new structure.

---

## Key Development Guidelines

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
- [Arduino_RouterBridge Library](https://github.com/arduino-libraries/Arduino_RouterBridge/tree/main)
- [Arduino Router Service](https://github.com/arduino/arduino-router)
- [Command Line Interface (CLI) Reference](https://docs.arduino.cc/software/app-lab/tutorials/cli/)

---
name: arduino-uno-q-app-dev
description: Developing applications for the Arduino Uno Q (dual MCU/MPU board). Use this skill when creating or editing apps in `/home/arduino/ArduinoApps`, working with Bricks (`web_ui`, `dbstorage`), or setting up Bridge communication between C++ and Python.
---

# Arduino Uno Q App Development

The Arduino Uno Q features a dual-processor architecture: an **MCU** (Real-time C++) and an **MPU** (Linux Python).

## App Anatomy

An app is a directory in `/home/arduino/ArduinoApps/` with:
- `app.yaml`: Metadata (name, icon) and **Bricks**.
- `sketch/`: MCU project (Arduino `.ino` and `.yaml`).
- `python/`: MPU logic (`main.py`).
- `assets/`: Web dashboard files (HTML/CSS/JS).

## Core Concepts

### Bricks
Bricks provide high-level features like web interfaces or storage.
- **Reference**: See [bricks.md](references/bricks.md) for usage and configuration.
- **Common Bricks**: `arduino:web_ui`, `arduino:dbstorage_sqlstore`.

### Bridge (Communication)
Communication between MCU and MPU is handled via the **Bridge** RPC system.
- **Reference**: See [bridge.md](references/bridge.md) for API details and best practices.
- **Key Pattern**: `Bridge.provide` (C++) and `Bridge.call`/`Bridge.notify` (Python).

### Web UI
Standard web dashboards use `arduino:web_ui`.
- **Backend**: `main.py` uses `ui.expose_api` and `App.run()`.
- **Frontend**: `assets/index.html` connects via Socket.io (using `arduino.app_utils` JS client).

## Workflows

### Creating a New App
1. Run `arduino-app-cli app new "<name>"` to scaffold.
2. Define Bricks in `app.yaml`.
3. Implement `sketch/sketch.ino` (I/O, Bridge providers).
4. Implement `python/main.py` (High-level logic, Bridge calls).

### Leveraging Official Examples
Reference folders starting with `copy-of-` for production-grade patterns:
- **Complex UI/Storage**: `copy-of-led-matrix-painter` (uses multiple bricks and advanced bridge data).
- **Basic Interaction**: `copy-of-blink-led` (cleanest Python-to-MCU example).

## Development Conventions

- **Wiring**: Use **ATN-IO v3** notation in `README.md` or separate `.md` files (see `wiring-notation.md` in root).
- **Safety**: Uno Q GPIOs are **3.3V**. Use voltage dividers for 5V inputs.
- **Performance**: Use `Bridge.notify` for high-frequency updates from Python.
- **MCU loop**: Keep it non-blocking to ensure Bridge responsiveness.

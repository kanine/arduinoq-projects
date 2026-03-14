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

## RGB LEDs

The Uno Q has four RGB LEDs split into two groups by controller, plus an LED matrix and a power LED.

### MPU-controlled — RGB 1 & 2 (Linux `/sys/class/leds/`)

| Designator | Colour | GPIO | Sysfs name |
|------------|--------|------|------------|
| D27301 (RGB 1) | Red | GPIO_41 | `red:user` |
| D27301 (RGB 1) | Green | GPIO_42 | `green:user` |
| D27301 (RGB 1) | Blue | GPIO_60 | `blue:user` |
| D27302 (RGB 2) | Red | GPIO_39 | `red:panic` |
| D27302 (RGB 2) | Green | GPIO_40 | `green:wlan` |
| D27302 (RGB 2) | Blue | GPIO_47 | `blue:bt` |

PWM frequency: ~2 kHz (smooth colour transitions supported via brightness values 0–255).

**RGB LED 2 default role**: indicates system status (panic/WLAN/BT). Writing brightness overrides it for user control, but it resumes system use when the app stops.

Write to sysfs from Python:
```python
with open('/sys/class/leds/red:user/brightness', 'w') as f:
    f.write('255')   # ON
with open('/sys/class/leds/red:user/brightness', 'w') as f:
    f.write('0')     # OFF
```

### MCU-controlled — RGB 3 & 4 (Arduino sketch, active low)

| Designator | Colour | MCU pin | Arduino constant |
|------------|--------|---------|-----------------|
| D27401 (RGB 3) | Red | PH10 | `LED3_R` |
| D27401 (RGB 3) | Green | PH11 | `LED3_G` |
| D27401 (RGB 3) | Blue | PH12 | `LED3_B` |
| D27402 (RGB 4) | Red | PH13 | `LED4_R` |
| D27402 (RGB 4) | Green | PH14 | `LED4_G` |
| D27402 (RGB 4) | Blue | PH15 | `LED4_B` |

Constants are defined in `variant.h` (auto-included). **Do not redefine them** — `PH10` etc. are not valid in the Zephyr Arduino layer; only the named constants work.

**Active low**: `LOW` = ON, `HIGH` = OFF.

```cpp
pinMode(LED3_R, OUTPUT);
digitalWrite(LED3_R, LOW);   // ON
digitalWrite(LED3_R, HIGH);  // OFF
```

### LED matrix — D27001..D27104
8×13 monochrome blue matrix (104 pixels), MCU-controlled via `Arduino_LED_Matrix.h`. Displays the boot logo for ~20–30 seconds on Linux startup. **Do not access the matrix before startup completes** — it can interfere with MCU operation.

### Power LED — D27201
Green indicator tied to the 3.3 V rail. Always on when the board is powered; not user-controllable.

## Development Conventions

- **Wiring**: Use **ATN-IO v3** notation in `README.md` or separate `.md` files (see `wiring-notation.md` in root).
- **Safety**: Uno Q GPIOs are **3.3V**. Use voltage dividers for 5V inputs.
- **Performance**: Use `Bridge.notify` for high-frequency updates from Python.
- **MCU loop**: Keep it non-blocking to ensure Bridge responsiveness.

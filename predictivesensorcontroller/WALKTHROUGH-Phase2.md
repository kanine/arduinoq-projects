# Phase 2: Single VL53L1X Hardware Bring-Up Verification

## Overview
Phase 2 introduced a single live Adafruit VL53L1X sensor into `predictivesensorcontroller` without changing the existing main control page. The goal was to prove hardware communication, live ranging, and a dedicated diagnostics page before attempting multi-sensor prediction logic.

## Components Added
- **MCU TOF sketch (`sketch/sketch.ino`)**: Owns the VL53L1X on the MCU side, initializes the working I2C bus, polls distance readings, and exposes a compact diagnostics RPC surface over Bridge.
- **TOF diagnostics backend (`python/tof_service.py`)**: Reads scalar Bridge values, maps them into a stable `/tof/status` payload, and persists the operator threshold setting.
- **Hardware test page (`assets/tof-test.html`, `assets/tof-test.js`)**: Shows live distance, online state, threshold, I2C visibility, and init state without changing the main predictive control page.
- **Wiring reference (`tof-single-sensor-wiring.md`)**: Documents the bring-up wiring for the single-sensor validation step.
- **Standalone utility app (`/home/kanine/ArduinoProjects/uno1/timeofflightcheck`)**: Minimal serial-only check used to isolate the true working MCU I2C path before applying the fix back into the main app.

## Key Finding
The crucial hardware finding was that the working VL53L1X path on the Uno Q app sketch side uses **`Wire1`**, not the original `Wire` assumption.

What was observed during bring-up:
- The sensor powered up over Qwiic and showed its green LED.
- Initial app versions using `Wire` could not detect `0x29`.
- The standalone `timeofflightcheck` utility succeeded once the sensor logic used `Wire1`.
- After porting that same bus selection and init pattern into `predictivesensorcontroller`, the diagnostics page reported:
  - sensor online
  - valid live distance readings
  - `I2C ACK at 0x29 = True`
  - `Init Stage = 5`
  - no active fault

## Result
Phase 2 succeeded. The Predictive Sensor Controller now has a working live hardware diagnostics page at `/tof-test.html`, and the main control page remains untouched. The project also now has a reusable `timeofflightcheck` utility app for future hardware validation and troubleshooting.

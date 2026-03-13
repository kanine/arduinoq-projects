# Phase 2 Plan: Single VL53L1X Hardware Bring-Up and Diagnostics Page

## Summary

Move `predictivesensorcontroller` from pure simulation into first-hardware validation by adding support for one hardwired Adafruit VL53L1X sensor on the Uno Q, while leaving the current main control page at `/` behaviorally unchanged. This phase is for sensor bring-up and observability only: raw distance and simple presence state will be exposed on a separate diagnostics page so we can verify wiring, I2C communication, reading stability, and threshold behavior before introducing multi-sensor timing logic.

## Key Changes

### Hardware and wiring deliverables
- Add a dedicated wiring document in ATN-IO v3 format for the single-sensor setup.
- Document this exact test wiring as the baseline:
  - Uno Q `3.3V` -> `ADA3967.VIN`
  - Uno Q `GND` -> `ADA3967.GND`
  - Uno Q `SDA` -> `ADA3967.SDA`
  - Uno Q `SCL` -> `ADA3967.SCL`
  - Uno Q `D3` -> `ADA3967.XSHUT`
  - Leave `ADA3967.GPIO` unconnected for this phase
- Include notes in the wiring doc for:
  - remove the protective film before testing
  - use the Uno Q 3.3V I2C side
  - single-sensor phase keeps the default I2C address `0x29`
  - `XSHUT` is wired now for reset control and future multi-sensor expansion

### MCU and Bridge integration
- Add a new `sketch/` for first-time MCU ownership of the sensor.
- MCU responsibilities in this phase:
  - `Bridge.begin()` and `Wire.begin()`
  - initialize the VL53L1X at `0x29`
  - drive `XSHUT` during startup
  - start ranging with a fixed timing budget suitable for bring-up
  - poll readings non-blockingly
  - convert readings into a compact sensor snapshot
- Expose Bridge providers for a minimal diagnostics contract:
  - `get_tof_snapshot`
  - `get_tof_health`
  - `set_tof_test_config`
- Snapshot fields should be flat and stable:
  - `online`
  - `distance_mm`
  - `data_ready`
  - `threshold_mm`
  - `object_present`
  - `timing_budget_ms`
  - `last_read_ms`
  - `fault`

### Python backend and web UI
- Keep the existing main control page and its current APIs intact.
- Extend `python/main.py` with new hardware-test endpoints only; do not change the current simulation endpoints used by the main page.
- Python should call the MCU Bridge providers and expose a dedicated diagnostics API such as:
  - `GET /tof/status`
  - `POST /tof/config`
- Add a new standalone page in `assets/`, served alongside the existing dashboard, for example `/tof-test.html`.
- The hardware test page should show:
  - current distance in mm
  - online/offline state
  - object-present state based on threshold
  - threshold value currently applied
  - last update age
  - fault/health message
- Keep this page read-mostly for bring-up. The only operator control in this phase should be a simple threshold input and save action.

### Testing behavior and limits for this phase
- This page is for one sensor only and does not alter prediction, cycle timing, relay scheduling, or Sensor A/B/C production semantics yet.
- The sensor test flow should treat the attached VL53L1X as a diagnostic device, not yet as official `Sensor A`.
- Polling cadence should be conservative and UI-focused rather than high-frequency streaming.
- If the sensor is missing or initialization fails, the diagnostics API must return a clear fault state instead of crashing the app.

## Public Interfaces

- New MCU Bridge methods:
  - `get_tof_snapshot`
  - `get_tof_health`
  - `set_tof_test_config`
- New MPU HTTP APIs:
  - `GET /tof/status`
  - `POST /tof/config`
- New web entrypoint:
  - `/tof-test.html`
- Existing `/`, `/status`, `/simulate`, `/config`, and `/logs` remain available and unchanged for the current control/simulation workflow.

## Test Plan

- Wiring verification:
  - confirm power and I2C lines match the ATN-IO document
  - confirm the sensor appears online after app start
- Sensor bring-up:
  - verify the MCU reports a valid `distance_mm`
  - verify `online=true` and no fault in idle conditions
  - verify fault reporting when the sensor is disconnected or held in shutdown
- Threshold behavior:
  - move an object into range and confirm `object_present` flips true
  - move it away and confirm it returns false without excessive chatter
  - verify threshold updates from the diagnostics page take effect
- UI isolation:
  - confirm the main control page at `/` still behaves exactly as before
  - confirm the new diagnostics page loads independently and polls only the new hardware endpoint
- Regression checks:
  - confirm simulation mode still works from the existing main page
  - confirm no existing log/config endpoints are broken by the hardware additions

## Assumptions and Defaults

- This phase uses one Adafruit VL53L1X breakout only; no TCA9548A multiplexer is introduced yet.
- The Uno Q exposes standard `3.3V`, `GND`, `SDA`, and `SCL` connections for direct I2C wiring.
- `XSHUT` will be wired to `D3` and actively managed by the MCU; the sensor interrupt pin is not used yet.
- The diagnostics page is intentionally separate from the main page so hardware testing can proceed without disturbing the current simulation/control UI.
- The first implementation target is stable live readings and simple threshold visibility, not prediction logic or relay actuation from real hardware.

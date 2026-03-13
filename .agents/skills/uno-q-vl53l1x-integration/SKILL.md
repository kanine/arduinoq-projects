---
name: uno-q-vl53l1x-integration
description: Use when integrating Adafruit VL53L1X Time-of-Flight sensors into an Arduino Uno Q app with the MCU/MPU split architecture. Apply this skill for Uno Q tasks involving sensor polling in `sketch/`, Bridge RPC or notify design, Python app coordination in `python/main.py`, web dashboard exposure, or converting VL53L1X threshold crossings into higher-level events inside a dual-processor Uno Q application. This skill builds on `$adafruit-vl53l1x`.
---

# Uno Q VL53L1X Integration

Use this skill after `$adafruit-vl53l1x` when the target platform is the Arduino Uno Q. Keep VL53L1X electrical facts and generic sensor usage in the sensor skill; use this skill to decide what runs on the MCU, what runs on the MPU, and how sensor events cross the Bridge.

## Architecture Split

- Put raw sensor ownership on the MCU in `sketch/`:
  - I2C bus initialization
  - `XSHUT` startup sequencing
  - address assignment
  - ranging loop
  - threshold crossing detection
  - timestamp capture
- Put orchestration on the MPU in `python/main.py`:
  - cycle state machine
  - prediction logic
  - configuration persistence
  - dashboard APIs
  - logging and diagnostics
- Use the Bridge boundary for compact event payloads and configuration changes, not for high-volume raw sample streaming.

## Default Workflow

1. Read `$adafruit-vl53l1x` for sensor facts, API patterns, and multi-sensor constraints.
2. Define the sensor topology:
   - sensor count
   - intended positions
   - `XSHUT` pins
   - final I2C addresses
3. Implement MCU bring-up in `sketch/sketch.ino`.
4. Implement MCU threshold crossing logic that emits discrete events.
5. Expose MCU methods with `Bridge.provide` for state reads and configuration updates.
6. Use Python to collect events, calculate speed or predictions, and publish UI state.
7. Store user-editable thresholds, timing budgets, and distances on the MPU side.
8. Reflect only stable, application-level data in the dashboard.

## MCU Responsibilities

- Call `Bridge.begin()` early in `setup()`.
- Register diagnostic `Bridge.provide` handlers before fragile sensor init so RPCs remain reachable during bring-up failures.
- Initialize the confirmed working I2C controller for the board and project; do not assume `Wire` if bring-up testing shows another controller such as `Wire1`.
- Assign unique addresses using `XSHUT` sequencing before normal operation.
- Start ranging and keep the `loop()` non-blocking.
- Convert distance readings into event records such as:
  - `sensor_id`
  - `timestamp_ms` or `timestamp_us`
  - `distance`
  - `event_type`
- Keep the event detector deterministic:
  - threshold
  - hysteresis
  - quiet time
  - sensor enabled state
- Provide RPC methods for:
  - current sensor state snapshot
  - configuration readback
  - configuration update
  - health or fault status

## MPU Responsibilities

- Use `Bridge.call` for occasional reads or configuration changes.
- Use `Bridge.notify` or compact callbacks for frequent event delivery patterns when the design permits.
- Own configuration persistence and validation.
- Translate raw event timestamps into:
  - speed
  - predicted cut time
  - cycle validity
  - operator-visible errors
- Expose the processed state through `ui.expose_api` if the app includes `arduino:web_ui`.

## Bridge Design Rules

- Do not send every raw ranging sample to Python.
- Send threshold crossings or summarized state instead.
- Keep payloads small and flat. In this workspace, scalar RPCs proved more reliable than returning JSON strings from the MCU over Bridge.
- Avoid blocking Bridge traffic with long MCU operations or `delay()`.
- If an RPC must touch mutable sensor state, prefer safe patterns consistent with the Uno Q Bridge guidance.

## File Layout Expectations

- `app.yaml`: define Bricks such as `arduino:web_ui` or storage when needed.
- `sketch/sketch.ino`: sensor bus bring-up, event detector, Bridge providers.
- `python/main.py`: prediction engine, storage, UI API, diagnostics.
- `assets/`: dashboard files if a web UI is present.

## Implementation Pattern

Use this default contract unless the app has a stronger existing convention.

MCU exposes:

- bring-up and diagnostics can start with scalar methods such as `get_distance`, `get_online`, `get_fault_code`, or `get_init_stage`
- higher-level grouped contracts are fine once Bridge behavior is proven on the actual board
- `set_sensor_config`
- `arm_detection`
- `reset_faults`

MCU emits or returns:

- per-sensor presence state
- last event timestamp
- last measured distance
- health flags

MPU owns:

- inter-sensor distance configuration
- prediction formulas
- logging
- UI formatting

## Project Fit

For a predictive cutter workflow on Uno Q:

- Let the MCU decide when each VL53L1X has crossed its configured detection threshold.
- Let the MPU compute speed and relay timing from MCU timestamps.
- Keep relay actuation either on the MCU for tight timing or explicitly justify MPU-side scheduling if timing tolerance allows it.

## References

Load [references/uno-q-vl53l1x-patterns.md](references/uno-q-vl53l1x-patterns.md) for:

- recommended app structure
- Bridge payload shapes
- example sensor event schema
- configuration split between MCU and MPU
- design tradeoffs specific to Uno Q

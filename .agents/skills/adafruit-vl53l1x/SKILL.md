---
name: adafruit-vl53l1x
description: Use when working with Adafruit VL53L1X Time-of-Flight distance sensors, especially for wiring, I2C setup, multi-sensor address assignment with XSHUT, threshold-based object detection, or Arduino/CircuitPython integration. Apply this skill when a task mentions VL53L1X, VL53L1CX, Adafruit product 3967, Time-of-Flight ranging, or converting measured distance into object-presence events.
---

# Adafruit VL53L1X

Use this skill to integrate Adafruit VL53L1X distance sensors into Arduino, CircuitPython, Python, or Uno Q projects. Keep the workflow short in `SKILL.md` and load [references/adafruit-vl53l1x-reference.md](references/adafruit-vl53l1x-reference.md) when exact wiring, limits, or API behavior matters.

## Quick Start

1. Confirm the task type:
   - Single sensor bring-up
   - Multi-sensor bus setup
   - Threshold-based object detection
   - Porting between Arduino and Python/CircuitPython
2. Read the reference file before making hardware assumptions.
3. Prefer I2C polling or interrupt-assisted ranging over treating the board like a simple digital sensor.
4. For multiple sensors on one bus, plan address assignment around `XSHUT`.
5. Convert distance readings into application events using a configured threshold and simple hysteresis.

## Implementation Rules

- Treat the Adafruit breakout as an I2C ranging sensor, not a raw analog or simple HIGH/LOW proximity device.
- Account for the breakout board behavior, not just the bare ST sensor: the Adafruit board includes regulator and level shifting.
- Remove the protective film note into documentation or setup steps when writing bring-up instructions.
- If more than one sensor is present, explicitly document startup sequencing and final I2C addresses.
- When building object-detection logic, define:
  - trigger threshold
  - release threshold or hysteresis
  - sampling interval or timing budget
  - debounce or quiet-time rules in software

## Multi-Sensor Workflow

1. Hold all but one sensor in shutdown with `XSHUT`.
2. Bring sensors up one at a time.
3. Initialize each sensor at default address `0x29`.
4. Change the active sensor to a unique address.
5. Repeat until all sensors are assigned.
6. Start ranging only after the bus map is stable.

Read the reference file for the pin-level facts that justify this sequence.

## Detection Workflow

1. Start from measured distance in `mm` or `cm`.
2. Choose a trigger threshold based on the actual product path and mounting angle.
3. Mark object present when the reading crosses the threshold.
4. Use hysteresis so noisy readings near the threshold do not retrigger.
5. Timestamp the crossing event, not every sample.
6. Keep timing budget and sampling cadence consistent across sensors before calculating speed from multiple trigger points.

## Arduino Guidance

- Use the Adafruit VL53L1X Arduino library and start from the simple test pattern in the reference.
- Keep `Wire` initialization explicit.
- Check sensor status on `begin()`, `startRanging()`, and distance reads.
- Clear interrupts after consuming a reading when using the library's data-ready flow.

## Python And CircuitPython Guidance

- Use the Adafruit CircuitPython VL53L1X library for Linux/Python or CircuitPython targets.
- Set `distance_mode` and `timing_budget` intentionally instead of relying on defaults when timing matters.
- Use `data_ready` checks in read loops and clear the interrupt after consuming data.

## Reference File

Load [references/adafruit-vl53l1x-reference.md](references/adafruit-vl53l1x-reference.md) for:

- board capabilities and operating limits
- pin meanings and voltage notes
- default I2C address and `XSHUT` behavior
- Arduino example API calls
- Python/CircuitPython example behavior
- source links back to Adafruit

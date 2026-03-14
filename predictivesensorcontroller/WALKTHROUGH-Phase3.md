# Phase 3: Two-Sensor VL53L1X Bring-Up and Multi-Sensor Diagnostics

## Overview

Phase 3 extended `predictivesensorcontroller` from the stable single-sensor Phase 2 baseline into a two-sensor shared-bus topology using XSHUT-controlled address assignment. Both VL53L1X sensors are now live on `Wire1`, assigned unique I2C addresses, and independently ranging in Short distance mode at 40ms per measurement. The hardware is bench-tested and confirmed ready for the speed-calculation phase.

## Hardware Bring-Up Process

### Prerequisite: timeofflightconfig utility app

Before touching `predictivesensorcontroller`, a dedicated utility app `timeofflightconfig` was created to validate the two-sensor XSHUT bring-up sequence in complete isolation. This was the key lesson from Phase 3 Attempt 1 — integrating XSHUT logic directly into the main app made it impossible to tell whether failures were hardware or software.

`timeofflightconfig` proved three things in sequence:

1. **Single sensor without XSHUT**: sensor found at `0x29`, address reassigned to `0x30`, confirmed via I2C probe.
2. **Single sensor with XSHUT on D3**: full power-cycle sequence (D3 LOW → HIGH), sensor booted at `0x29`, reassigned to `0x30`, confirmed.
3. **Two sensors with XSHUT on D3 and D4**: sequential bring-up — sensor 1 on D3 assigned `0x30`, then sensor 2 on D4 booted at `0x29` (now free) and assigned `0x31`. Both confirmed via I2C probe. LED solid on.

Only after all three passed was the pattern ported into `predictivesensorcontroller`.

### Wiring

| Connection | Pin |
|---|---|
| Sensor 1 Qwiic → board Qwiic | Wire1 (shared bus) |
| Sensor 2 Qwiic → sensor 1 Qwiic (daisy chain) | Wire1 (shared bus) |
| Sensor 1 XSHUT | D3 (PB0) |
| Sensor 2 XSHUT | D4 (PA12) |

XSHUT wires are permanent — sensors reset to `0x29` on every power cycle and require the sequencing to run again on each app start.

## Components Changed

### MCU (`sketch/sketch.ino`)

- Replaced single-sensor state with per-sensor state variables for S1 and S2.
- `initializeSensors()` runs the proven XSHUT sequence in `setup()`:
  - Both XSHUT LOW → delay → S1 XSHUT HIGH → init at `0x29` → assign `0x30`
  - S2 XSHUT HIGH → init at `0x29` (now free) → assign `0x31`
- `pollSensor()` helper polls each sensor independently in `loop()`.
- Staleness watchdog: if a sensor has not produced a reading for 3 seconds it is marked offline and `reinitSensor()` is called, probing at the assigned address without re-running XSHUT.
- `reset_sensors()` exposed via `Bridge.provide_safe()` — re-runs the full XSHUT sequence on demand from the web UI.
- Distance mode: **Short** (max ~1.3 m, better close-range behaviour).
- Timing budget: **40 ms**. Inter-measurement period: **40 ms** (sensor runs at its minimum cycle time).
- Range status faults (object too close or out of range) no longer take the sensor offline — they return null distance while keeping the sensor online and ranging.

### Python (`python/tof_service.py`)

- Generalised from single-sensor to two-sensor using a `SENSOR_CONFIGS` dict keyed by `"sensor_1"` / `"sensor_2"`.
- `/tof/status` now returns `{ sensors: { sensor_1: {...}, sensor_2: {...} }, timing_budget_ms }`.
- `/tof/config` accepts per-sensor threshold updates: `{ "sensor_1": { "threshold_mm": 200 } }`.
- `/tof/reset` triggers `reset_sensors()` over Bridge and returns the updated status.

### Persistence (`python/store.py`)

- Added `tof_sensor_config` table (TEXT PRIMARY KEY `"sensor_1"` / `"sensor_2"`, `threshold_mm`).
- Existing tables untouched — additive change only, no migration risk.

### Web UI (`assets/tof-test.html`, `assets/tof-test.js`)

- Converted from single-sensor to two-panel layout (side by side on wide screens).
- Each panel shows: distance, online/offline, object present, threshold, read age, fault, I2C ACK, init stage.
- Per-sensor threshold form.
- **Reset Sensors** button in the bus configuration panel — re-runs full XSHUT sequence without rebooting the board.

## Bugs Found and Fixed During Bring-Up

| Bug | Root Cause | Fix |
|---|---|---|
| LED appeared dead on first deploy | `LED_BUILTIN` is active low (`LOW` = ON) — sketch had it inverted | Swapped all `HIGH`/`LOW` values for LED |
| Sensors not found at `0x29` on first run | I2C bus left in bad state from previous Phase 3 experiment sessions | Board reboot cleared state; this is a known Uno Q behaviour |
| Sensors went offline when object placed in front | `FAULT_RANGE_STATUS` was marking the sensor offline — Long mode returns invalid status for close objects | Changed to keep sensor online on range status fault; only mark offline on true timeout |
| Sensors stopped updating after a few minutes | No recovery path when `dataReady()` stalled | Added 3-second staleness watchdog + `reinitSensor()` without XSHUT |
| App crashed first start (Phase 3 Attempt 1) | `create_or_replace_table()` collided with existing primary key on schema change | Used additive new table (`tof_sensor_config`) rather than altering existing one |

## Confirmed Working State

At end of Phase 3 bring-up:

- Both sensors online, init stage 5, no fault
- Readings stable at 150–152 mm on simulated test bench
- Short mode / 40 ms confirmed suitable for the target detection range (< 300 mm)
- Object present threshold detection working per sensor independently
- Reset button tested — re-runs XSHUT sequence and recovers from I2C ACK failures without board reboot
- Both sensors confirmed stable with objects in the beam path

## What Phase 3 Does Not Yet Do

- Speed calculation from inter-sensor timing
- Sensor A / Sensor B production roles (sensors are still diagnostic-only in this phase)
- Integration with the relay or the main control page predictive timing logic

## Next Phase

Phase 4 will map Sensor 1 and Sensor 2 into the production speed-calculation pipeline:

1. Record timestamp when each sensor's `object_present` transitions from false → true
2. Speed = sensor separation distance / (T2 − T1)
3. Feed calculated speed into the existing prediction controller
4. Trigger relay at the calculated cut time

The 40 ms timing budget gives ±40 ms worst-case detection latency per sensor. Speed accuracy improves with sensor separation distance — the further apart they are, the smaller the relative timing error.

# Phase 3 Plan: Two-Sensor VL53L1X Bring-Up and Multi-Sensor Test Configuration

## Summary

Extend `predictivesensorcontroller` from the verified single-sensor Phase 2 setup into a two-sensor shared-bus bring-up phase using two VL53L1X sensors on the proven Uno Q MCU bus (`Wire1`). Phase 3 remains diagnostics-focused: it adds address assignment, per-sensor configuration, and richer test-page controls without changing the main control page or introducing predictive timing behavior yet.

This phase will treat both sensors as hardware-test devices, not yet as official production `Sensor A` / `Sensor B` inputs. The default multi-sensor bring-up plan will reserve `D3` for Sensor 1 `XSHUT` and `D4` for Sensor 2 `XSHUT`.

## Key Changes

### MCU multi-sensor bring-up and address assignment
- Replace the single-sensor MCU state with a two-sensor topology model on `Wire1`.
- Add explicit `XSHUT` sequencing:
  - hold both sensors in shutdown
  - bring up Sensor 1 on `D3`, initialize at `0x29`, reassign to a stable non-default address such as `0x30`
  - bring up Sensor 2 on `D4`, initialize at `0x29`, reassign to a stable non-default address such as `0x31`
  - start continuous ranging only after both addresses are assigned
- Keep the existing proven Phase 2 bus settings:
  - `Wire1.begin()`
  - `Wire1.setClock(400000)`
- Maintain non-blocking polling and per-sensor health tracking.
- Expand MCU diagnostics to expose per-sensor scalar RPCs instead of a single shared sensor state.

### Diagnostics data model and backend APIs
- Generalize the Python TOF service from one sensor to a list of sensors with stable IDs such as `sensor_1` and `sensor_2`.
- Keep scalar Bridge calls on the MCU side and assemble the multi-sensor snapshot in Python.
- Replace the single-threshold-only config model with a multi-sensor diagnostics config model that supports:
  - sensor enabled/disabled
  - sensor label
  - assigned I2C address
  - `XSHUT` pin mapping
  - threshold per sensor
  - timing budget shared default for the test phase
- Add or update diagnostics APIs to support multi-sensor reads and writes, for example:
  - `GET /tof/status` returns all configured sensors plus bus-level status
  - `POST /tof/config` updates per-sensor configuration and active test settings
- Persist this configuration in the existing SQL store so the test page survives reboots and address/topology settings stay visible.

### TOF test page enhancements
- Keep `/tof-test.html` as the dedicated hardware page, but convert it from a single-sensor screen into a multi-sensor diagnostics dashboard.
- Add a per-sensor panel for each active sensor showing:
  - online/offline
  - distance
  - object present
  - threshold
  - I2C ACK / init stage
  - assigned address
  - `XSHUT` pin
- Restore and expand the configuration controls that were intentionally deferred in Phase 2:
  - sensor count selector for current supported topologies
  - per-sensor threshold input
  - per-sensor enabled toggle
  - optional sensor label field
  - visible assigned address and `XSHUT` mapping
- Add a wiring/help modal on the test page that explains:
  - why multiple VL53L1X sensors need `XSHUT` control on a shared bus
  - the default Phase 3 wiring (`D3` and `D4` for `XSHUT`)
  - the startup/address-assignment sequence
  - which pins should remain unconnected in this phase
  - what to do with Qwiic daisy-chaining versus direct wiring
- The modal should be instructional only in Phase 3; it does not perform setup automatically.

### Documentation and hardware guidance
- Add a Phase 3 wiring document or extend the current TOF wiring doc to cover the two-sensor daisy-chain setup.
- Document the validated multi-sensor approach explicitly:
  - shared `Wire1` bus
  - Qwiic daisy-chain for bus continuity
  - separate `XSHUT` lines required for address assignment
  - default addresses after assignment
- Update the walkthrough/docs to record that Phase 3 is still a diagnostics phase and not yet predictive timing integration.

## Public Interfaces

- MCU Bridge surface changes from one sensor to per-sensor scalar diagnostics methods.
- Python diagnostics payload changes from a single `tof` object to a multi-sensor structure with bus-level status and a sensor list/map.
- `POST /tof/config` expands from a single `threshold_mm` input to a multi-sensor config payload.
- `/tof-test.html` remains the diagnostics entrypoint, but its UI becomes multi-sensor aware.
- The main control page `/` and the Phase 1 simulation endpoints remain untouched.

## Test Plan

- Multi-sensor bring-up:
  - verify Sensor 1 and Sensor 2 can be powered on the shared bus and assigned unique addresses
  - confirm both sensors show `online=true` after startup
  - confirm the default address collision is resolved through `XSHUT` sequencing
- Diagnostics API:
  - confirm `/tof/status` returns both sensors with stable IDs, addresses, thresholds, and health flags
  - confirm `/tof/config` updates per-sensor threshold and enabled state without breaking the page
- UI validation:
  - verify the updated `/tof-test.html` shows both sensors independently
  - verify the configuration panel edits the intended sensor only
  - verify the wiring/help modal explains the shared-bus and `XSHUT` requirements clearly
- Failure scenarios:
  - disconnect one sensor and confirm the other still reports correctly
  - hold one `XSHUT` low and confirm the page reports the affected sensor as unavailable without collapsing the whole diagnostics page
  - verify address-assignment failure produces a visible fault state
- Regression checks:
  - confirm the main control page still behaves as before
  - confirm the Phase 2 single-sensor path still works if Phase 3 is configured with only one active sensor
  - confirm the standalone `timeofflightcheck` utility remains usable as an independent hardware validator

## Assumptions and Defaults

- Phase 3 remains diagnostics-only; the two sensors are not yet mapped into production predictive timing logic.
- The default two-sensor `XSHUT` plan is:
  - Sensor 1 `XSHUT` -> `D3`
  - Sensor 2 `XSHUT` -> `D4`
- The shared MCU bus remains `Wire1` at `400 kHz`.
- The address plan should use two stable non-default sensor addresses after startup, such as `0x30` and `0x31`.
- The modal should explain the required electrical setup for multi-sensor shared-bus operation, but Phase 3 will not yet add automatic topology discovery beyond what is needed for the configured two-sensor test setup.

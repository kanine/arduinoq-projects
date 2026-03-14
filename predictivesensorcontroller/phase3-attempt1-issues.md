# Phase 3 Attempt 1 Issues

## Summary

This document records the first attempt to move `predictivesensorcontroller` from the stable Phase 2 single-sensor VL53L1X setup into the Phase 3 two-sensor shared-bus/XSHUT design.

The main outcome:

- Phase 2 single-sensor mode is stable and recoverable.
- Phase 3 software was implemented and deployed successfully.
- Phase 3 hardware bring-up was not successful.
- Reboots were sometimes required to restore live readings even after the code was reverted.

## Stable Baseline Confirmed

The known-good baseline remains the original Phase 2 implementation:

- one VL53L1X sensor
- default address `0x29`
- `Wire1`
- `400 kHz`
- no active `XSHUT` control in code
- `predictivesensorcontroller` and `/tof-test.html` both work in this mode

Observed healthy Phase 2 status after recovery:

- `online: true`
- `data_ready: true`
- `distance_mm` around `1480-1490 mm`
- `i2c_address_seen: true`
- `init_stage: 5`
- no fault

## Wiring Context Used During Attempt

Phase 3 default plan used:

- Sensor 1 `XSHUT -> D3`
- Sensor 2 `XSHUT -> D4`
- shared `3.3V`, `GND`, `SDA`, `SCL`
- Qwiic connection used for the sensor path

Important Uno Q pin mapping note confirmed during the session:

- Arduino digital `D3` maps to MCU pin `PB0`
- Arduino digital `D4` maps to MCU pin `PA12`

This mapping was not the source of the failure. Using `3` and `4` in Arduino code is correct.

## What Was Implemented In Phase 3

The first Phase 3 code attempt added:

- two-sensor MCU topology on `Wire1`
- explicit `XSHUT` sequencing
- assigned addresses `0x30` and `0x31`
- per-sensor Bridge RPC surface
- multi-sensor Python diagnostics service
- persisted multi-sensor TOF config
- two-sensor diagnostics UI
- per-sensor enable/disable support for isolation

The app built and deployed correctly to `uno1`.

## Failure Modes Observed

### 1. Initial Phase 3 DB migration failure

The first Phase 3 startup failed on the Uno Q because the `tof_test_config` schema migration used `create_or_replace_table()` and collided with the existing primary key definition.

Observed error:

- SQLStore refused to change/drop the existing `id` column definition

Resolution:

- changed the migration to additive `ALTER TABLE` behavior instead of `create_or_replace_table()`

After that fix, the app started successfully.

### 2. Two-sensor bring-up failed

With both sensors enabled, the app reached the new `/tof/status` endpoint but reported hardware faults.

Observed faults at different points:

- `No I2C ACK at 0x29 during bring-up`
- later `VL53L1X init failed at 0x29`

This showed the issue was in the hardware bring-up path, not the web UI or container startup.

### 3. Sensor 1 only also failed in Phase 3

We then isolated the topology to:

- `sensor_1 enabled`
- `sensor_2 disabled`

Result:

- still failed in Phase 3
- faults remained in the bring-up path before usable ranging started

This showed the problem was not simply two devices colliding on the bus.

### 4. Disconnecting Sensor 2 did not fix Phase 3

The sensor attached to `D4/XSHUT` was physically disconnected.

Result:

- `sensor_1` still failed in Phase 3

Conclusion:

- the second sensor was not required for the failure to appear

### 5. Disconnecting `D3 -> XSHUT` did not fix Phase 3

We physically removed the `D3 -> XSHUT` connection and retested `sensor_1 only`.

Result:

- Phase 3 still failed

Conclusion:

- the failure was not caused only by the physical presence of the `D3` wire

### 6. Modified Phase 3 single-sensor startup still failed

We then tried to make Phase 3 safer by:

- allowing true independent sensor enable/disable
- skipping active `XSHUT` handling when only one sensor was enabled
- then later trying to reuse the Phase 2 single-sensor init flow inside the Phase 3 code path

Results:

- one version failed with `VL53L1X init failed at 0x29`
- another version failed with `No I2C ACK at 0x29 during bring-up`

Conclusion:

- even when Phase 3 was simplified for one sensor, it still did not behave like the stable original Phase 2 code on real hardware

## Important Runtime/UI Findings

### Page showing `--` was often correct

At several points the TOF test page showed no distance readout.

This was not always a frontend bug. In those cases the backend often really was returning:

- `distance_mm: null`
- `data_ready: false`
- or a bring-up fault

So the page behavior often correctly reflected the live API state.

### D3 connected is safe in Phase 2

In the restored original Phase 2 code:

- `USE_XSHUT = false`
- `D3` is not actively driven by the sketch

Therefore:

- leaving `D3` physically connected is acceptable in the stable Phase 2 baseline

## Recovery Behavior Observed

One important practical finding:

- after some failed Phase 3 testing, reverting the code back to Phase 2 was not always enough to restore sensor readings immediately
- rebooting `uno1` sometimes restored normal Phase 2 operation

Observed pattern:

1. Phase 2 code restored
2. sensor still unavailable or not producing data
3. reboot Uno Q
4. start app again
5. Phase 2 readings return normally

This strongly suggests the board/sensor/Qwiic path can enter a bad runtime state that is not always cleared by app restart alone.

## Current Known-Good State At End Of Session

At the end of this session the system was restored to:

- original Phase 2 code
- single-sensor diagnostics page
- one working VL53L1X sensor
- healthy live readings after a full Uno Q reboot and app restart

Live result at end:

- `distance_mm` approximately `1481-1489 mm`
- `data_ready: true`
- `online: true`
- no fault

## Practical Lessons For Next Attempt

### 1. Preserve a fast rollback path

Keep the original Phase 2 code easy to restore and re-sync.

### 2. Reboot may be required between hardware-mode changes

If the sensor stops producing readings after Phase 3 experiments:

- do not assume code rollback alone is enough
- power cycle or reboot the Uno Q before concluding the hardware path is still broken

### 3. Introduce Phase 3 in smaller increments

Next attempt should likely separate the work into smaller hardware checkpoints:

1. keep stable Phase 2 code untouched
2. create a dedicated experimental bring-up sketch/app variant
3. test only one active `XSHUT`-managed sensor first
4. verify address reassignment works before adding the second sensor
5. only then merge back into `predictivesensorcontroller`

### 4. Treat Qwiic/runtime state as a factor

Because reboot restored the stable path more than once, include explicit power-cycle testing in future bring-up steps.

### 5. Do not assume Phase 3 single-sensor mode is equivalent to Phase 2

Even small startup-path differences can matter on this board/sensor combination.

## Recommended Next Step

For the next Phase 3 attempt:

- start from the restored Phase 2 baseline
- create a smaller experimental branch/change set focused only on one XSHUT-controlled sensor
- validate that single-sensor XSHUT bring-up works before reintroducing the second sensor or the larger diagnostics/config changes

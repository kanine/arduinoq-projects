# Uno Q VL53L1X Patterns

Use this file after loading `$adafruit-vl53l1x` when the task is specifically about integrating the sensor into an Arduino Uno Q app.

## When To Keep Logic On The MCU

Keep logic on the MCU when it is:

- close to hardware timing
- part of I2C sensor bring-up
- dependent on deterministic polling cadence
- needed to timestamp threshold crossings accurately
- controlling relay or GPIO outputs with tight timing

Examples:

- `XSHUT` startup sequencing
- address assignment from default `0x29`
- sensor ranging loop
- threshold crossing detection
- per-sensor debounce or hysteresis

## When To Keep Logic On The MPU

Keep logic on the MPU when it is:

- configuration-heavy
- UI-facing
- storage-backed
- easier to evolve in Python than in the sketch
- tolerant of Bridge round-trip latency

Examples:

- configuration editing
- logging to storage
- dashboard APIs
- cycle analysis
- prediction algorithms

## Recommended Event Schema

Prefer a small event structure over raw sample streaming.

Suggested fields:

- `sensor_id`
- `event_type`
- `timestamp_ms` or `timestamp_us`
- `distance_mm`
- `sequence`

Suggested event types:

- `entered_threshold`
- `left_threshold`
- `fault`
- `sensor_online`

`Inference`: for most manufacturing-style flows, the MPU only needs threshold-entry timestamps and health faults to compute speed and timing.

## Recommended Snapshot Schema

Use a snapshot RPC for dashboard refreshes and diagnostics.

Suggested fields:

- `sensorA_present`
- `sensorB_present`
- `sensorC_present`
- `sensorA_distance_mm`
- `sensorB_distance_mm`
- `sensorC_distance_mm`
- `fault_flags`
- `armed`

`Inference`: on Arduino Uno Q, start bring-up with scalar RPCs if Bridge reliability is still unproven. Assemble larger snapshot payloads on the Python side once the board-specific RPC path is stable.

## Configuration Split

Keep these on the MCU:

- I2C addresses
- pin assignments
- timing budget currently applied
- threshold and hysteresis values actively used in the loop

Keep these on the MPU as the source of truth:

- user-editable thresholds
- named sensor roles
- inter-sensor distances
- validation windows
- relay pulse defaults
- logging retention

`Inference`: persist configuration on the MPU, then push the current active subset down to the MCU at startup or when the user saves changes.

## Bridge Payload Guidance

- Favor flat scalar arguments over nested payloads if the Bridge API surface is simpler that way.
- Prefer scalar return values during first hardware bring-up on Uno Q; a working scalar pattern is a stronger foundation than an elegant but fragile snapshot RPC.
- Batch related settings into one update call when they must change atomically.
- Avoid round-tripping for each sensor sample.
- If the MCU needs to notify Python frequently, aggregate state first.

## Suggested App Skeleton

`app.yaml`

- add `arduino:web_ui` when operator visibility matters
- add storage brick only if logs or persisted config are required

`sketch/sketch.ino`

- initialize Bridge
- register Bridge providers
- initialize the confirmed working I2C controller and sensors
- poll sensors without blocking
- capture crossing events
- manage relay output if timing is tight

`Inference`: in this workspace, a successful single-sensor VL53L1X path on Uno Q used `Wire1` with a `400 kHz` clock and a minimal retrying bring-up loop.

`python/main.py`

- initialize app services
- expose UI APIs
- fetch snapshots
- receive event notifications if used
- compute speed and prediction
- store logs and errors

## Tradeoffs

- MCU-side relay timing is usually the safer default when actuation must happen with low jitter.
- MPU-side scheduling is easier to inspect and change, but latency and scheduling jitter must be justified.
- More Bridge traffic improves observability but reduces headroom.
- More MCU autonomy improves timing but makes app logic harder to iterate.

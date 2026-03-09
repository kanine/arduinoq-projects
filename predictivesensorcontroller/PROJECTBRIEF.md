# Predictive Factory Sensor Controller

## Project Brief & Technical Specification

## 1. Project Name

**Predictive Factory Sensor Controller (PFSC)**

## 2. Target Platform

**Arduino Uno Q**

The Uno Q provides:

- Linux-capable processor
- ~2 GB RAM
- GPIO interface compatible with Arduino ecosystem
- Ethernet / WiFi networking
- USB

The controller must use:

- real-time GPIO inputs
- Linux software stack
- web dashboard

## 3. Project Objective

Develop an industrial-style predictive sensor controller capable of:

- Detecting objects moving along a path
- Measuring speed using multiple sensors
- Predicting when the material reaches the requested cut length
- Triggering a relay output at the calculated time
- Displaying real-time status via a web dashboard
- Logging sensor timing data for diagnostics

Primary use case:

**Extruded filament or product moving past sensors before being cut.**

---

## 4. System Concept

Three sensors detect an object moving away from the cut point. The cut happens at the start of the track, and the relay trigger time is predicted from the measured line speed plus a user-configured target cut length.

```text
Motion Direction ->

[CUT POINT / RELAY] ----distance_cut_to_A---- [SENSOR A] ----50mm---- [SENSOR B] ----50mm---- [SENSOR C] --->

Target length example:
If the user requests 300 mm and Sensor C is 200 mm from the cut point,
the controller predicts when the leading edge will travel the remaining 100 mm
beyond Sensor C, then activates the cutter relay.
```

Workflow:

```text
Sensor A triggered
    |
    v
timestamp recorded

Sensor B triggered
    |
    v
intermediate speed calculated

Sensor C triggered
    |
    v
speed refined using A, B, and C timestamps

Predict future time when the growing length reaches user target
    |
    v
schedule cutter relay trigger

Trigger cut relay
```

## 5. Functional Requirements

### 5.1 Sensor Inputs

System must support:

| Sensor | Function |
| --- | --- |
| Sensor A | Start detection |
| Sensor B | Speed calculation |
| Sensor C | Final speed refinement and validation |

Sensors used for this project:

- Adafruit VL53L1X Time of Flight Distance Sensor
- SparkFun Qwiic Mux Breakout - 8 Channel (TCA9548A) for I2C multiplexing
- One sensor mounted at each detection point: Sensor A, Sensor B, and Sensor C
- Detection is based on measured distance crossing a configured threshold

Sensor interface requirements:

- I2C communication for range measurements
- Per-sensor configuration for distance threshold and timing budget
- Support for selecting the correct I2C multiplexer channel before reading from each VL53L1X sensor

The controller must interpret object presence from distance readings rather than digital `HIGH/LOW` outputs.

### 5.2 Relay Output

Relay output must trigger the cut command.

Requirements:

- pulse duration configurable
- default pulse = `100 ms`
- relay must not retrigger until next valid cycle

### 5.3 Timing Prediction

System must calculate:

```text
speed_AB = distance_AB / (time_B - time_A)
speed_BC = distance_BC / (time_C - time_B)
estimated_speed = distance_AC / (time_C - time_A)
```

Prediction:

```text
distance_cut_to_C = distance_cut_to_A + distance_AB + distance_BC
remaining_length_after_C = target_length - distance_cut_to_C
time_to_cut = remaining_length_after_C / estimated_speed
```

Trigger:

```text
relay_trigger_time = time_C + time_to_cut
```

Notes:

- The cut point is located physically before Sensor A at the start of the track.
- `target_length` is user-configurable, for example `300 mm`.
- The prediction should use all three sensor timestamps for the final speed estimate.
- `validation_enabled` controls strict tolerance/error handling, not whether Sensor C is sampled.
- System should compare `speed_AB` against `speed_BC`. If there is significant acceleration or deceleration during the measurement window, a "Speed Unstable" warning should be flagged.
- If `target_length <= distance_cut_to_C`, the system must raise a configuration or process error instead of scheduling an immediate cut.

### 5.4 Detection Filtering

The controller must implement:

- Debounce filtering adapted for Time of Flight sensors (VL53L1X minimum timing budget is ~20-33ms, limiting maximum object speed)
- Ignore transitions shorter than the minimum sensor sampling period (e.g. `20 ms`)
- Quiet period

After a valid detection:

- ignore new triggers for `500 ms`

Prevents double readings.

### 5.5 Sensor Validation

Sensor C is part of the normal timing model and provides the final upstream timing reference before the cutter.

When `validation_enabled` is true:

- Sensor C must trigger within expected window
- If outside tolerance: raise error

Tolerance:

- `+-20%`

## 6. Configurable Parameters

These parameters must be editable via web UI.

| Parameter | Default |
| --- | --- |
| `distance_cut_to_A` | `100 mm` |
| `distance_AB` | `50 mm` |
| `distance_BC` | `50 mm` |
| `target_length` | `300 mm` |
| `relay_pulse` | `100 ms` |
| `sensor_debounce` | `20 ms` |
| `validation_enabled` | `true` |
| `simulation_mode` | `false` |

*Note: When `simulation_mode` is `true`, the system ignores physical sensor inputs/relay outputs and uses internal stubs to simulate timing logic. The web UI must clearly indicate when this mode is active.*

## 7. Hardware Specification

### Inputs

| Input | Interface |
| --- | --- |
| I2C Multiplexer | `TCA9548A` over `I2C` (Main Bus) |
| Sensor A | `Adafruit VL53L1X` via Mux Channel 0 |
| Sensor B | `Adafruit VL53L1X` via Mux Channel 1 |
| Sensor C | `Adafruit VL53L1X` via Mux Channel 2 |

Sensors expected voltage:

- `3.3V` logic on the Uno Q I2C side
- Sensor power and level handling must match the deployed breakout wiring

Implementation notes:

- Multiple VL53L1X sensors share the same static I2C address (`0x29`), so communication is routed through the 8-Channel TCA9548A I2C Multiplexer.
- Mechanical mounting must keep each sensor aligned with the product path at the configured detection points

### Outputs

| Output | GPIO |
| --- | --- |
| Cut Relay | `GPIO22` |
| LED OK | `GPIO23` |
| LED ERROR | `GPIO24` |

LED behaviour:

| State | LED |
| --- | --- |
| system ready | green |
| prediction active | blue |
| error | red |

## 8. Software Architecture

System consists of three components.

```text
+------------------------+
| MCU Sensor Service     |
+------------------------+

+------------------------+
| Prediction Engine      |
+------------------------+

+------------------------+
| Web UI Backend/API     |
+------------------------+
```

### 8.1 MCU Sensor Service

Language:

- Arduino C++ on the Uno Q MCU

Responsibilities:

- manage I2C multiplexer (TCA9548A) to communicate with individual sensors
- read distance measurements from the VL53L1X sensors over I2C
- detect threshold crossings and timestamp events
- expose sensor state and events to the MPU via Bridge
- execute scheduled relay commands sent from the MPU using hardware timers for precise microsecond activation

Timestamp resolution:

- milliseconds minimum
- microseconds preferred

### 8.2 Prediction Engine

Language:

- Python on the Uno Q MPU

Responsibilities:

- calculate speed and monitor for linear acceleration/deceleration between stages
- calculate predicted trigger time from measured speed and target length
- transmit activation schedule (delay/offset) to MCU for relay triggering
- validate sensor timing
- generate simulated sensor events and mock relay schedules when `simulation_mode` is enabled

Must support:

- multiple cycles per second

### 8.3 Relay Scheduler (MCU side)

Relay must be triggered accurately without OS scheduling jitter.

- The MPU calculates the time until cut (`time_to_cut`)
- The MPU sends command to MCU (e.g., `SCHEDULE_CUT: 1250ms`)
- The MCU implements a non-blocking hardware timer to trigger `GPIO22` precisely at the requested interval.

Example pseudocode (MCU):

```text
on_command_rx(delay_ms):
    hardware_timer.start(delay_ms, activate_relay)
```

### 8.4 Web Dashboard

Stack:

- Python
- JavaScript
- HTML/CSS
- `arduino:web_ui` Brick
- `arduino:dbstorage_sqlstore` Brick for persisted logs and configuration

Chosen approach:

- Python MPU backend for application logic and API exposure
- JavaScript frontend served by the Uno Q web UI stack
- database storage implemented with the `dbstorage_sqlstore` brick pattern used in `copy-of-qr-and-barcode-scanner`

Functions:

- live sensor state (A, B, C clearly displayed as active/inactive)
- live relay state (clearly displayed as active/inactive)
- predicted cut time
- target length configuration
- speed measurement
- configuration editing
- log viewer
- simulation mode toggle and prominent "Simulation Mode Active" indicator

Recommended implementation model:

```text
Browser UI <-> web_ui websocket/API <-> Python backend <-> Router Bridge <-> MCU sketch
```

## 9. API Specification

Endpoint:

```text
GET /api/status
```

Response:

```json
{
  "sensorA": 0,
  "sensorB": 0,
  "sensorC": 0,
  "relay_active": 0,
  "speed_mm_per_s": 320,
  "target_length_mm": 300,
  "next_cut_ms": 120,
  "state": "running",
  "simulation_mode": true
}
```

Endpoint:

```text
POST /api/simulate
```

Payload to trigger a simulated detection cycle (only valid when `simulation_mode` is true):

```json
{
  "simulated_speed_mm_per_s": 300
}
```

Endpoint:

```text
GET /api/log
```

Returns recent detection cycles.

## 10. Data Logging

Log each cycle.

Example entry:

- `timestamp`
- `sensorA_time`
- `sensorB_time`
- `sensorC_time`
- `calculated_speed`
- `target_length`
- `predicted_cut_time`
- `actual_cut_time`

Stored in:

- `SQLStore` from the `arduino.app_bricks.dbstorage_sqlstore` brick
- database file managed by the Uno Q app on the MPU side

Retention:

- last `10000` cycles

Recommended storage pattern:

```python
from arduino.app_bricks.dbstorage_sqlstore import SQLStore

store = SQLStore("predictive-sensor-controller.db")
store.store("cycle_log", entry)
cycles = store.read("cycle_log", order_by="timestamp DESC", limit=100)
```

## 11. Error Conditions

System must detect:

| Condition | Action |
| --- | --- |
| sensor B not triggered | abort cycle |
| speed impossible | raise error |
| speed unstable (acceleration) | warning |
| sensor C outside tolerance | warning |
| relay failure | critical error |

Errors must be visible in dashboard.

## 12. Performance Requirements

| Metric | Target |
| --- | --- |
| prediction accuracy | `+-5 ms` |
| cycle rate | `10+ cycles/sec` |
| dashboard latency | `<100 ms` |

## 13. Security Requirements

Local network only.

Authentication optional but recommended.

## 14. Development Milestones

### Phase 1: Simulation & UI Foundation

- Python Prediction Engine (simulation stubs for sensors/relay)
- Web UI dashboard with sensor/relay state visualization
- API endpoints for configuration and simulation control

### Phase 2: Core Timing Logic

- Speed calculation and prediction math
- Acceleration/deceleration warning logic
- Sensor C validation logic

### Phase 3: MCU Hardware Integration

- I2C Multiplexer and VL53L1X sensor integration
- MCU to MPU bridge communication
- Hardware timer relay scheduling

### Phase 4: Production Polish

- Error detection and logging (SQLStore)
- Performance tuning and UI refinement

## 15. Acceptance Criteria

System must demonstrate:

- correct speed calculation
- correct relay trigger timing
- no double triggers
- dashboard shows real-time data
- error detection works

## 16. Optional Future Features

- Modbus industrial sensors
- Ethernet PLC integration
- predictive maintenance analytics
- machine learning timing optimization
- multi-lane support

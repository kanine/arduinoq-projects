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
- Predicting arrival time at a cutting station
- Triggering a relay output at the calculated time
- Displaying real-time status via a web dashboard
- Logging sensor timing data for diagnostics

Primary use case:

**Extruded filament or product moving past sensors before being cut.**

---

## 4. System Concept

Three sensors detect an object moving past them. The cutter is physically downstream of Sensor C, and the relay trigger time is predicted from the measured line speed plus a user-configured target cut length.

```text
Motion Direction ->

[SENSOR A] ----50mm---- [SENSOR B] ----50mm---- [SENSOR C] --------------------> [CUTTER]

Target length example:
If the user requests 300 mm and Sensor C is 100 mm downstream of Sensor A,
the controller predicts when the product has travelled the remaining 200 mm
after crossing Sensor C, then activates the cutter.
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

Predict future time when measured length reaches user target
    |
    v
schedule relay trigger

Trigger cutter
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
- One sensor mounted at each detection point: Sensor A, Sensor B, and Sensor C
- Detection is based on measured distance crossing a configured threshold

Sensor interface requirements:

- I2C communication for range measurements
- Per-sensor configuration for distance threshold and timing budget
- Support for assigning unique I2C addresses when multiple VL53L1X sensors are present

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
distance_AC = distance_AB + distance_BC
remaining_length_after_C = target_length - distance_AC
time_to_cut = remaining_length_after_C / estimated_speed
```

Trigger:

```text
relay_trigger_time = time_C + time_to_cut
```

Notes:

- The cutter is located physically beyond Sensor C.
- `target_length` is user-configurable, for example `300 mm`.
- The prediction should use all three sensor timestamps for the final speed estimate.
- `validation_enabled` controls strict tolerance/error handling, not whether Sensor C is sampled.
- If `target_length <= distance_AC`, the system must raise a configuration or process error instead of scheduling an immediate cut.

### 5.4 Detection Filtering

The controller must implement:

- Debounce filtering
- Ignore transitions shorter than `10 ms`
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
| `distance_AB` | `50 mm` |
| `distance_BC` | `50 mm` |
| `target_length` | `300 mm` |
| `relay_pulse` | `100 ms` |
| `quiet_time` | `500 ms` |
| `sensor_debounce` | `10 ms` |
| `validation_enabled` | `true` |

## 7. Hardware Specification

### Inputs

| Input | Interface |
| --- | --- |
| Sensor A | `Adafruit VL53L1X` over `I2C` |
| Sensor B | `Adafruit VL53L1X` over `I2C` |
| Sensor C | `Adafruit VL53L1X` over `I2C` |

Sensors expected voltage:

- `3.3V` logic on the Uno Q I2C side
- Sensor power and level handling must match the deployed breakout wiring

Implementation notes:

- Multiple VL53L1X sensors require unique I2C addressing or controlled startup using `XSHUT`
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

- read distance measurements from the VL53L1X sensors over I2C
- detect threshold crossings and timestamp events
- expose sensor state and events to the MPU via Bridge

Timestamp resolution:

- milliseconds minimum
- microseconds preferred

### 8.2 Prediction Engine

Language:

- Python on the Uno Q MPU

Responsibilities:

- calculate speed
- calculate predicted trigger time from measured speed and target length
- schedule relay activation
- validate sensor timing

Must support:

- multiple cycles per second

### 8.3 Relay Scheduler

Relay must be triggered using:

- non-blocking timer

Example pseudocode:

```text
schedule_event(trigger_time, activate_relay)
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

- live sensor state
- predicted cut time
- target length configuration
- speed measurement
- configuration editing
- log viewer

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
  "speed_mm_per_s": 320,
  "target_length_mm": 300,
  "next_cut_ms": 120,
  "state": "running"
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

### Phase 1

- GPIO sensor detection

### Phase 2

- speed calculation

### Phase 3

- relay timing

### Phase 4

- web dashboard

### Phase 5

- error detection and logging

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

# PRD: ESP32 Time-of-Flight Webhook

> Port of `timeofflightwebhook2` (Arduino Uno Q) to a standalone ESP32 with VL53L1X sensor. All logic runs on a single MCU — no Bridge, no MPU/MCU split.

---

## 1. Overview

A standalone ESP32 firmware that:

- Reads distance, range status, and signal quality from a VL53L1X ToF sensor
- Batches readings and POSTs them to a configurable webhook over Wi-Fi
- Accepts optional `config` updates from the server response, applied at runtime without restart
- Provides LED feedback for success, failure, and config updates
- Confirms startup with a 1→2→3 blink sequence

---

## 2. Hardware

| Component | Detail |
|---|---|
| MCU | ESP32 (any variant with Wi-Fi) |
| Sensor | VL53L1X connected via I2C |
| LED | Single LED on a GPIO (configurable; ESP32 built-in LED or external) |

I2C pins are configurable via `config.h` (default: SDA=21, SCL=22 for most ESP32 boards). The VL53L1X library used is **Pololu VL53L1X 1.3.1** — do not substitute Adafruit or SparkFun.

---

## 3. Startup Sequence

On power-up/reset, before connecting to Wi-Fi, the firmware blinks the status LED to confirm it has started:

| Phase | Blinks | Timing |
|---|---|---|
| 1 | 1 blink | 300ms on / 300ms off |
| 2 | 2 blinks | 300ms on / 200ms off × 2 |
| 3 | 3 blinks | 300ms on / 200ms off × 3 |

Pause 500ms between phases. After the sequence completes, proceed with Wi-Fi connection and sensor initialisation.

---

## 4. LED Feedback (Runtime)

| Event | Behaviour |
|---|---|
| Successful POST (`success: true`) | 1 short flash, 120ms |
| POST failed (network error / non-2xx) | 1 short flash, 120ms, repeated 3× (rapid triple-flash) |
| Config update received and applied | Solid on for 500ms |

All feedback is non-blocking — use a `blinkOffAt` pattern (store `millis() + duration`, clear in main loop).

---

## 5. Configuration

All config is defined in `config.h` as compile-time constants. No file system required.

### 5.1 Network

```cpp
#define WIFI_SSID        "your-ssid"
#define WIFI_PASSWORD    "your-password"
#define WEBHOOK_URL      "https://example.com/api/readings"
#define DEVICE_HOST      "esp32-tof"   // reported in payload as "host"
```

### 5.2 Polling

| Field | Type | Default | Description |
|---|---|---|---|
| `polls_per_minute` | float | 300 | How many sensor reads per minute. Determines inter-poll interval: `60000 / polls_per_minute` ms. Minimum enforced: 20ms. |
| `batch_cap` | int | 50 | Number of valid readings to accumulate before sending a batch POST. |

### 5.3 Sensor

| Field | Type | Valid values | Default | Description |
|---|---|---|---|---|
| `distance_mode` | string | `"Short"`, `"Medium"`, `"Long"` | `"Short"` | VL53L1X distance mode. Short = up to ~1.3m, less ambient noise. Long = up to ~4m, more noise. |
| `timing_budget_ms` | int | 15, 20, 33, 50, 100, 200, 500 | 100 | Ranging time budget in milliseconds. Higher = more accurate, slower. |
| `inter_measurement_ms` | int | ≥ timing_budget_ms | 200 | Interval between consecutive measurements in ms. Must be ≥ timing_budget_ms. |
| `roi_width` | int | 4–16 | 4 | ROI width in SPADs. 16 = full FOV. Narrower = tighter beam, less cross-talk. |
| `roi_height` | int | 4–16 | 4 | ROI height in SPADs. |
| `roi_center` | int | 0–255 | 199 | SPAD index of the ROI centre. 199 is optical centre (compensates for lens inversion). |

---

## 6. Outbound Webhook Payload

Method: `POST`
Content-Type: `application/json`
Timeout: 5 seconds

```json
{
  "app": "esp32-tof-webhook",
  "host": "esp32-tof",
  "batch_id": 1,
  "start_time_ms": 1743000000000,
  "end_time_ms":   1743000010000,
  "uptime": "0d 00:01:23",
  "config": {
    "polls_per_minute": 300,
    "poll_ms": 200,
    "batch_cap": 50,
    "sensor": {
      "distance_mode": "Short",
      "timing_budget_ms": 100,
      "inter_measurement_ms": 200,
      "roi_width": 4,
      "roi_height": 4,
      "roi_center": 199
    }
  },
  "readings": [
    {
      "ts_ms": 1743000000000,
      "distance_mm": 312,
      "range_status": 0,
      "signal_mcps": 2.145,
      "ambient_mcps": 0.083
    }
  ]
}
```

### Field reference

| Field | Type | Description |
|---|---|---|
| `app` | string | Fixed identifier: `"esp32-tof-webhook"` |
| `host` | string | Value of `DEVICE_HOST` from config |
| `batch_id` | int | Monotonically incrementing counter, reset on reboot |
| `start_time_ms` | int | Unix timestamp (ms) of the first reading in this batch |
| `end_time_ms` | int | Unix timestamp (ms) of the last reading in this batch |
| `uptime` | string | Time since boot, formatted as `"Xd HH:MM:SS"` |
| `config` | object | Active config at time of send — sensor params that produced these readings |
| `config.poll_ms` | int | Derived: `60000 / polls_per_minute`, minimum 20 |
| `readings[].ts_ms` | int | Unix timestamp (ms) of this reading (from NTP-synced ESP32 clock) |
| `readings[].distance_mm` | int | Distance measurement in mm |
| `readings[].range_status` | int | VL53L1X range status code (0 = valid; see below) |
| `readings[].signal_mcps` | float | Peak signal count rate in MCPS (3 decimal places) |
| `readings[].ambient_mcps` | float | Ambient count rate in MCPS (3 decimal places) |

### Range status codes

| Code | Meaning | Action |
|---|---|---|
| 0 | Valid range | Use reading |
| 1 | Sigma fail | Discard — measurement uncertainty too high |
| 2 | Signal fail | Discard — too little return signal |
| 4 | Out of bounds | Discard — target beyond max range for mode |
| 5 | Hardware fail | Sensor error |
| 6 | Wrap-around | Discard — first reading after mode change |
| 7 | No update | Sensor returned no new data |

Only readings with `range_status == 0` are included in batches (all others are discarded silently).

---

## 7. Server Response

The server must respond with HTTP 200 and a JSON body.

### Minimal response (acknowledge only)

```json
{ "success": true }
```

### Response with config update

The `config` block is optional. Any combination of `polling` and `sensor` sub-blocks may be included; only present keys are updated — absent keys retain their current values.

```json
{
  "success": true,
  "config": {
    "polling": {
      "polls_per_minute": 60,
      "batch_cap": 20
    },
    "sensor": {
      "distance_mode": "Long",
      "timing_budget_ms": 200,
      "inter_measurement_ms": 300,
      "roi_width": 8,
      "roi_height": 8,
      "roi_center": 199
    }
  }
}
```

### Config update validation rules

Applied in firmware before committing any change:

1. `distance_mode` must be one of `"Short"`, `"Medium"`, `"Long"` — unknown strings are ignored
2. `timing_budget_ms` must be one of the valid values: 15, 20, 33, 50, 100, 200, 500 — invalid values are ignored
3. `inter_measurement_ms` must be ≥ `timing_budget_ms` — if not, the entire sensor block is ignored
4. `roi_width` and `roi_height` must be 4–16 — out-of-range values are clamped or ignored
5. `roi_center` must be 0–255
6. `polls_per_minute` must be > 0
7. `batch_cap` must be > 0

When a config update is successfully applied, the firmware triggers the 500ms LED hold. The next outbound batch will reflect the updated `config` block.

---

## 8. Runtime Sensor Reconfiguration

When a server response includes a `sensor` block that passes validation:

1. Stop continuous ranging (`sensor.stopContinuous()`)
2. Apply new distance mode, timing budget, ROI size, ROI center
3. Restart continuous ranging with new inter-measurement period
4. Update the in-memory `sensor_config` struct
5. Trigger 500ms LED hold

This happens in the main loop, not in an interrupt or callback, to avoid race conditions with the ranging data.

---

## 9. Time Synchronisation

The ESP32 must sync to NTP on startup before accepting readings. Use the ESP-IDF `sntp` component or Arduino `configTime()`. If NTP sync fails, retry every 10 seconds. Do not begin batching until time is synchronised — `ts_ms` values must be real Unix timestamps.

NTP server: `pool.ntp.org` (configurable in `config.h`).

---

## 10. Error Handling

| Scenario | Behaviour |
|---|---|
| Wi-Fi disconnected | Attempt reconnect; hold readings in buffer (up to `batch_cap` × 2); trigger rapid triple-flash LED on send failure |
| POST timeout (5s) | Log failure, discard batch, triple-flash LED |
| POST non-2xx response | Log status code, discard batch, triple-flash LED |
| `success: false` in response body | Log, discard config block if present, triple-flash LED |
| Sensor not found on I2C at startup | Retry every 500ms; do not proceed to polling |
| Sensor I2C error mid-run | Mark sensor as not ready, attempt reinit in next loop iteration |

---

## 11. Differences from `timeofflightwebhook2` (Uno Q)

| Aspect | Uno Q (`timeofflightwebhook2`) | ESP32 |
|---|---|---|
| Architecture | Dual-processor: MCU (sketch) + MPU (Python) | Single MCU: all logic in firmware |
| Networking | MPU handles Wi-Fi and HTTP | ESP32 handles Wi-Fi and HTTP directly |
| Config at startup | `config.json` read by Python; sensor params compiled to `sensor_config.h` | All config in `config.h` at compile time |
| Runtime reconfig | Python calls Bridge RPC → MCU pending-apply pattern | Reconfig applied directly in main loop |
| LED colours | RGB (active-low) — red, orange, green | Single LED — blink count/duration encodes meaning |
| Startup sequence | Red 750ms → orange 750ms → green 750ms | 1 blink → 2 blinks → 3 blinks |
| Time source | `time.time()` from Linux MPU | NTP via ESP32 Wi-Fi |
| Uptime | `time.monotonic()` in Python | `millis()` divided into d/h/m/s |
| Library bridge | `Arduino_RouterBridge` | Not applicable |

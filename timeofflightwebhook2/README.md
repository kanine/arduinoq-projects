# Time of Flight Testing

An Arduino Uno Q app for testing VL53L1X sensor parameters. Polls the sensor and POSTs batched readings — including signal quality metrics — to a logging webhook. All sensor parameters and polling behaviour are controlled from `config.json` with no code changes needed between test runs.

---

## How It Works

The MCU continuously ranges the VL53L1X and keeps the most recent distance, range status, and signal metrics in memory. The Python process polls the MCU over Bridge at a configurable rate, accumulates readings for a configurable window, then POSTs the batch as JSON to the webhook. The webhook responds with `{"success": true}` and the app moves on — no server-driven config changes.

Sensor parameters (distance mode, timing budget, ROI) are compiled into the MCU sketch at deploy time via a generated header. Polling parameters (rate, window) are read from `config.json` at Python startup.

---

## Configuration (`config.json`)

Copy `config.json.example` to `config.json` and fill in your values. `config.json` is git-ignored.

```json
{
  "webhook_url": "https://your.webhook/endpoint",
  "host": "my-sensor-node",

  "polling": {
    "polls_per_minute": 30,
    "window_seconds": 30
  },

  "sensor": {
    "distance_mode": "Short",
    "timing_budget_ms": 50,
    "inter_measurement_ms": 50,
    "roi_width": 16,
    "roi_height": 16,
    "roi_center": 199
  }
}
```

### Top-level fields

| Field | Required | Description |
|---|---|---|
| `webhook_url` | Yes | Endpoint that receives each batch POST. Must respond with `{"success": true}`. |
| `host` | No | Label sent in every payload. Falls back to system hostname if omitted. |

### `polling` block

Read by Python at startup. Restart the app to apply changes.

| Field | Default | Description |
|---|---|---|
| `polls_per_minute` | `30` | How many times per minute Python reads the sensor over Bridge. At 30 ppm the poll interval is 2 s. |
| `window_seconds` | `30` | How many seconds of readings are accumulated before a batch is POSTed. |

### `sensor` block

Compiled into the MCU sketch at deploy time via `sketch/sensor_config.h`. **Changing these requires running the generator script before syncing** — see Deployment below.

| Field | Default | Valid values | Description |
|---|---|---|---|
| `distance_mode` | `"Short"` | `"Short"`, `"Medium"`, `"Long"` | Controls max range and ambient light immunity. Short = ~1.3 m, best indoors. Medium = ~3 m. Long = ~4 m, most sensitive to IR noise. |
| `timing_budget_ms` | `50` | `20`, `33`, `50`, `100`, `140`, `200`, `500`, `1000` | Time the sensor spends collecting photons per measurement. Longer budgets reduce jitter but lower update rate. 20 ms is valid for Short mode only. |
| `inter_measurement_ms` | `50` | ≥ `timing_budget_ms` | Time between the start of consecutive measurements. Set equal to `timing_budget_ms` for back-to-back ranging. Increase to save power between readings. |
| `roi_width` | `16` | `4`–`16` | Width of the active SPAD region. Full 16×16 gives ~27° field of view. Narrowing reduces side-lobe sensitivity but also reduces signal. |
| `roi_height` | `16` | `4`–`16` | Height of the active SPAD region. Minimum is 4×4. |
| `roi_center` | `199` | `0`–`255` | SPAD index for the centre of the ROI. 199 is the optical centre (look straight ahead). Shifting the centre moves the FOV in the **opposite** direction due to lens inversion. See `sensor_config.h` or the parameter reference for the full SPAD grid. |

---

## Payload Format

```json
{
  "app": "timeofflighttesting",
  "host": "uno1-tof",
  "batch_id": 1,
  "start_time_ms": 1774742061472,
  "end_time_ms":   1774742089506,
  "uptime": "0d 00:00:28",
  "config": {
    "polls_per_minute": 30.0,
    "window_seconds": 30.0,
    "poll_ms": 2000,
    "batch_cap": 15
  },
  "readings": [
    {
      "ts_ms": 1774742061472,
      "distance_mm": 412,
      "range_status": 0,
      "signal_mcps": 1.23,
      "ambient_mcps": 0.04
    }
  ]
}
```

### Reading fields

| Field | Type | Description |
|---|---|---|
| `distance_mm` | integer | Measured distance in millimetres. Only readings with a non-zero distance are included. |
| `range_status` | integer | Sensor validity code. **0 = valid.** See table below. |
| `signal_mcps` | float | Return signal strength from the target in mega-counts/second. Low values indicate a weak return (dark target, too far, or outside FOV). |
| `ambient_mcps` | float | Background IR level in mega-counts/second. High relative to `signal_mcps` indicates bright ambient IR — consider switching to Short mode. |

### `range_status` codes

| Code | Meaning | Action |
|---|---|---|
| `0` | Valid | Use this reading |
| `1` | Sigma fail | High noise/jitter — target too far or signal too weak |
| `2` | Signal fail | Return signal too weak — target absent, too far, or low reflectance |
| `3` | Min range clipped | Target closer than minimum detectable range (~30–40 mm) |
| `4` | Out of bounds | Phase aliasing — target likely beyond mode's reliable range |
| `5` | Hardware fail | Hardware fault — consider restarting |
| `6` | No wrap check | Normal on the first reading of each session — discard |
| `7` | Wrap target fail | Range aliasing beyond ~5 m boundary |
| `9` | XTalk fail | Cover glass reflection overwhelming signal — XTalk calibration needed |
| `13` | Min range fail | ROI extends beyond SPAD array edge — resize or recentre ROI |

---

## Server Response

The webhook only needs to return:

```json
{"success": true}
```

If `success` is absent or false the batch is logged as unexpected but the app continues running.

---

## App Layout

```
timeofflighttesting/
├── app.yaml
├── config.json                  # Active config (git-ignored)
├── config.json.example          # Template — edit and copy to config.json
├── README.md
├── docs/
│   └── wiring.md                # ATN-IO v3 hardware wiring reference
├── python/
│   └── main.py                  # MPU: polling, batching, HTTP POST
└── sketch/
    ├── sketch.ino                # MCU: VL53L1X sensor + Bridge RPC
    ├── sketch.yaml               # Platform + library declarations
    └── sensor_config.h           # Auto-generated from config.json — do not edit
```

---

## Wiring

Connect the VL53L1X to the Uno Q Qwiic connector using a Qwiic / STEMMA QT cable.

| Board | Sensor |
|---|---|
| Qwiic SDA | SDA |
| Qwiic SCL | SCL |
| 3.3 V (via Qwiic) | VIN |
| GND (via Qwiic) | GND |

The sketch uses `Wire1` (Qwiic, I2C4) at 400 kHz. See `docs/wiring.md` for the full ATN-IO v3 wiring file.

---

## Deployment

### First time

```bash
cp config.json.example config.json
# edit config.json — set webhook_url and your sensor params

python3 scripts/gen_sensor_config.py timeofflighttesting
./scripts/sync_to_uno1.sh timeofflighttesting
ssh uno1 arduino-app-cli app restart "/home/arduino/ArduinoApps/timeofflighttesting"
```

### Changing polling params only (`polls_per_minute`, `window_seconds`)

```bash
# edit config.json polling section
./scripts/sync_to_uno1.sh timeofflighttesting
ssh uno1 arduino-app-cli app restart "/home/arduino/ArduinoApps/timeofflighttesting"
```

### Changing sensor params (`distance_mode`, `timing_budget_ms`, `roi_*`, etc.)

```bash
# edit config.json sensor section
python3 scripts/gen_sensor_config.py timeofflighttesting  # regenerate the header
./scripts/sync_to_uno1.sh timeofflighttesting
ssh uno1 arduino-app-cli app restart "/home/arduino/ArduinoApps/timeofflighttesting"
```

The generator validates your values and will error on invalid combinations (e.g. `inter_measurement_ms` < `timing_budget_ms`).

---

## Monitoring

**Snapshot of all logs:**
```bash
ssh uno1 arduino-app-cli app logs "/home/arduino/ArduinoApps/timeofflighttesting" --all
```

**Live follow:**
```bash
ssh uno1 docker logs -f timeofflighttesting-main-1
```

Expected output once running:
```
[batch] #1 — 15 readings  1774742061472 → 1774742089506  (28.0s)
[batch] 201 ok
```

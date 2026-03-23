# Time of Flight Webhook

An Arduino Uno Q app that polls a VL53L1X Time-of-Flight sensor and periodically POSTs batched distance readings to an external webhook endpoint. The board does no local processing — all analysis, storage, and logic lives on the server.

Adapted from the ESP32 `timeofflightbasic` sketch. The MCU handles I2C and sensor ranging; the MPU handles timestamps, batching, and HTTP POST.

---

## How It Works

The MCU continuously ranges the VL53L1X at 50 ms intervals and keeps the most recent valid distance in memory. The Python process polls the MCU over Bridge at a configurable rate, accumulates readings for a configurable window, then POSTs the full batch as JSON to the webhook URL.

The server response can push back updated `polls_per_minute` and `window_seconds` values, which the app applies immediately without restarting. This allows the server to control the data rate and window length at runtime.

---

## Configuration (`config.json`)

```json
{
  "webhook_url": "https://your.webhook/endpoint"
}
```

Copy `config.json.example` to `config.json` and set `webhook_url` before deploying. `config.json` is git-ignored.

Polling rate and window length default to `30 polls/min` and `30 seconds` and can be overridden by the server response at runtime.

---

## Payload Format

```json
{
  "app": "timeofflightwebhook",
  "host": "485088e6c6ca",
  "batch_id": 1,
  "start_time_ms": 1774253109312,
  "end_time_ms": 1774253137408,
  "uptime": "0d 00:00:28",
  "config": {
    "polls_per_minute": 30.0,
    "window_seconds": 30.0,
    "poll_ms": 2000,
    "batch_cap": 15
  },
  "readings": [
    {"ts_ms": 1774253109312, "distance_mm": 412},
    {"ts_ms": 1774253111318, "distance_mm": 414}
  ]
}
```

| Field | Description |
|---|---|
| `app` | Always `"timeofflightwebhook"` |
| `host` | Board hostname (`socket.gethostname()`) |
| `batch_id` | Incrementing integer, resets on restart |
| `start_time_ms` | Unix timestamp (ms) of the first reading in the batch |
| `end_time_ms` | Unix timestamp (ms) of the last reading in the batch |
| `uptime` | Time since app start, formatted `Dd HH:MM:SS` |
| `config` | Active timing parameters at time of send |
| `readings` | Array of `{ts_ms, distance_mm}` — only valid (non-zero) readings are included |

---

## Server Response

The app reads `polls_per_minute` and `window_seconds` from the `config` field of the server response and applies them immediately if they differ from the current values.

```json
{
  "success": true,
  "config": {
    "polls_per_minute": 240,
    "window_seconds": 10
  }
}
```

`success: true` is required for the response to be accepted. If the field is absent or false the batch is logged as failed but the app continues running.

---

## App Layout

```
timeofflightwebhook/
├── app.yaml
├── config.json           # Webhook URL (git-ignored)
├── config.json.example   # Template — commit this, not config.json
├── README.md
├── docs/
│   └── wiring.md         # ATN-IO v3 hardware wiring reference
├── python/
│   └── main.py           # MPU: polling, batching, HTTP POST
└── sketch/
    ├── sketch.ino         # MCU: VL53L1X sensor + Bridge RPC
    └── sketch.yaml        # Platform + library declarations
```

---

## Wiring

Connect the VL53L1X to the Uno Q Qwiic connector using a Qwiic / STEMMA QT cable — no additional wiring needed.

| Board | Sensor |
|---|---|
| Qwiic SDA | SDA |
| Qwiic SCL | SCL |
| 3.3 V (via Qwiic) | VIN |
| GND (via Qwiic) | GND |

Use `Wire1` (Qwiic, I2C4). The sketch initialises at 400 kHz, Short distance mode (max ~1.3 m), 50 ms timing budget.

See `docs/wiring.md` for the full ATN-IO v3 wiring file.

---

## Deployment

```bash
# 1. Set webhook URL
cp config.json.example config.json
# edit config.json — set webhook_url

# 2. Sync to board
./bash/sync_to_uno1.sh timeofflightwebhook

# 3. Restart
ssh uno1 arduino-app-cli app restart "/home/arduino/ArduinoApps/timeofflightwebhook"

# 4. Check logs
ssh uno1 arduino-app-cli app logs "/home/arduino/ArduinoApps/timeofflightwebhook" --all
```

Expected log output once running:

```
[batch] #1 — 15 readings  1774253109312 → 1774253137408
[batch] 202  response: {'success': True, 'batch_id': 1, ...}
[cfg] updated ppm=240.0 poll_ms=250 window_s=10.0
```

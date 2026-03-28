from arduino.app_utils import *
import time
import socket
import json
import requests
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
# All parameters are read from config.json at startup.
# Copy config.json.example to config.json and set your values before deploying.
# Sensor parameters (distance_mode, timing_budget, ROI) are compiled into the
# sketch via sensor_config.h — run gen_sensor_config.py before syncing to apply
# changes to the sensor section.
_config_path = Path(__file__).resolve().parent.parent / "config.json"
with open(_config_path) as _f:
    _config = json.load(_f)

WEBHOOK_URL      = _config["webhook_url"]
HOST             = _config.get("host") or socket.gethostname()
POLLS_PER_MINUTE = float(_config["polling"]["polls_per_minute"])
WINDOW_SECONDS   = float(_config["polling"]["window_seconds"])

# ── Runtime state ─────────────────────────────────────────────────────────────
readings       = []
batch_id       = 0
start_time     = time.monotonic()
last_poll_time  = 0.0
last_batch_time = time.monotonic()


def format_uptime(elapsed_s):
    s = int(elapsed_s)
    return f"{s // 86400}d {(s % 86400) // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def send_batch():
    global readings, batch_id

    if not readings:
        print("[batch] empty — skipping")
        return

    batch_id += 1
    poll_ms   = max(20, int(60000.0 / POLLS_PER_MINUTE))
    batch_cap = max(1, int(WINDOW_SECONDS * 1000 / poll_ms))

    payload = {
        "app":           "timeofflighttesting",
        "host":          HOST,
        "batch_id":      batch_id,
        "start_time_ms": readings[0]["ts_ms"],
        "end_time_ms":   readings[-1]["ts_ms"],
        "uptime":        format_uptime(time.monotonic() - start_time),
        "config": {
            "polls_per_minute": POLLS_PER_MINUTE,
            "window_seconds":   WINDOW_SECONDS,
            "poll_ms":          poll_ms,
            "batch_cap":        batch_cap,
        },
        "readings": readings,
    }

    duration_s = (readings[-1]["ts_ms"] - readings[0]["ts_ms"]) / 1000.0
    print(f"[batch] #{batch_id} — {len(readings)} readings  "
          f"{readings[0]['ts_ms']} → {readings[-1]['ts_ms']}  ({duration_s:.1f}s)")
    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=5)
        resp.raise_for_status()
        body = resp.json()
        if body.get("success"):
            print(f"[batch] {resp.status_code} ok")
        else:
            print(f"[batch] {resp.status_code} unexpected response: {body}")
    except Exception as exc:
        print(f"[batch] FAILED — {exc}")
        Bridge.notify("blink_red")

    readings = []


def loop():
    global last_poll_time, last_batch_time, readings

    now = time.monotonic()
    poll_interval_s = max(0.02, 60.0 / POLLS_PER_MINUTE)

    if now - last_poll_time >= poll_interval_s:
        last_poll_time = now
        distance = Bridge.call("get_distance")
        status   = Bridge.call("get_range_status")
        signal   = Bridge.call("get_signal_x100")
        ambient  = Bridge.call("get_ambient_x100")

        if distance is not None and distance > 0:
            readings.append({
                "ts_ms":       int(time.time() * 1000),
                "distance_mm": distance,
                "range_status": status,
                "signal_mcps": round(signal / 100.0, 3) if signal is not None else None,
                "ambient_mcps": round(ambient / 100.0, 3) if ambient is not None else None,
            })

    if now - last_batch_time >= WINDOW_SECONDS:
        send_batch()
        last_batch_time = time.monotonic()

    time.sleep(0.01)


App.run(user_loop=loop)

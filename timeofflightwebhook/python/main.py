from arduino.app_utils import *
import time
import socket
import json
import requests
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
# WEBHOOK_URL is loaded from config.json in the app root directory.
# Copy config.json.example to config.json and set your endpoint before deploying.
# POLLS_PER_MINUTE and WINDOW_SECONDS may be updated at runtime by the server.
_config_path = Path(__file__).resolve().parent.parent / "config.json"
with open(_config_path) as _f:
    _config = json.load(_f)

WEBHOOK_URL      = _config["webhook_url"]
HOST             = _config.get("host") or socket.gethostname()
POLLS_PER_MINUTE = 30.0
WINDOW_SECONDS   = 30.0

# ── Runtime state ─────────────────────────────────────────────────────────────
polls_per_minute = POLLS_PER_MINUTE
window_seconds   = WINDOW_SECONDS

readings    = []
batch_id    = 0
start_time  = time.monotonic()

last_poll_time  = 0.0
last_batch_time = time.monotonic()


def apply_server_config(body):
    global polls_per_minute, window_seconds
    cfg = body.get("config", {})
    changed = False
    if "polls_per_minute" in cfg:
        v = float(cfg["polls_per_minute"])
        if v > 0 and v != polls_per_minute:
            polls_per_minute = v
            changed = True
    if "window_seconds" in cfg:
        v = float(cfg["window_seconds"])
        if v > 0 and v != window_seconds:
            window_seconds = v
            changed = True
    if changed:
        poll_ms = max(20, int(60000.0 / polls_per_minute))
        print(f"[cfg] updated ppm={polls_per_minute:.1f} poll_ms={poll_ms} window_s={window_seconds:.1f}")


def format_uptime(elapsed_s):
    s = int(elapsed_s)
    return f"{s // 86400}d {(s % 86400) // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def send_batch():
    global readings, batch_id

    if not readings:
        print("[batch] empty — skipping")
        return

    batch_id += 1
    poll_ms   = max(20, int(60000.0 / polls_per_minute))
    batch_cap = max(1, int(window_seconds * 1000 / poll_ms))

    payload = {
        "app":          "timeofflightwebhook",
        "host":         HOST,
        "batch_id":     batch_id,
        "start_time_ms": readings[0]["ts_ms"],
        "end_time_ms":   readings[-1]["ts_ms"],
        "uptime":        format_uptime(time.monotonic() - start_time),
        "config": {
            "polls_per_minute": polls_per_minute,
            "window_seconds":   window_seconds,
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
        print(f"[batch] {resp.status_code}  response: {body}")
        if body.get("success"):
            apply_server_config(body)
        else:
            print("[batch] no success:true in response")
    except Exception as exc:
        print(f"[batch] FAILED — {exc}")
        Bridge.notify("blink_red")

    readings = []


def loop():
    global last_poll_time, last_batch_time, readings

    now = time.monotonic()
    poll_interval_s = max(0.02, 60.0 / polls_per_minute)

    if now - last_poll_time >= poll_interval_s:
        last_poll_time = now
        distance = Bridge.call("get_distance")
        if distance is not None and distance > 0:
            readings.append({
                "ts_ms":       int(time.time() * 1000),
                "distance_mm": distance,
            })

    if now - last_batch_time >= window_seconds:
        send_batch()
        last_batch_time = time.monotonic()

    time.sleep(0.01)


App.run(user_loop=loop)

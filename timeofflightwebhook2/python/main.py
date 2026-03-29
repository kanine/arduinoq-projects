from arduino.app_utils import *
import time
import socket
import json
import requests
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
# All parameters are read from config.json at startup.
# The webhook response may optionally return a config block to update polling
# and/or sensor parameters at runtime without restarting the app.
_config_path = Path(__file__).resolve().parent.parent / "config.json"
with open(_config_path) as _f:
    _config = json.load(_f)

WEBHOOK_URL = _config["webhook_url"]
HOST        = _config.get("host") or socket.gethostname()

# ── Mutable runtime config (may be updated by server response) ────────────────
polls_per_minute = float(_config["polling"]["polls_per_minute"])
batch_cap        = int(_config["polling"]["batch_cap"])
sensor_config    = dict(_config["sensor"])  # mutable copy

# Distance mode string → VL53L1X DistanceMode enum int (Short=1, Medium=2, Long=3)
MODE_MAP = {"Short": 1, "Medium": 2, "Long": 3}

def poll_ms():
    return max(20, int(60000.0 / polls_per_minute))

# ── Runtime state ─────────────────────────────────────────────────────────────
readings       = []
batch_id       = 0
start_time     = time.monotonic()
last_poll_time = 0.0


def apply_server_config(cfg):
    global polls_per_minute, batch_cap, sensor_config
    changed = []

    # ── Polling params ────────────────────────────────────────────────────────
    polling = cfg.get("polling", {})
    if "polls_per_minute" in polling:
        v = float(polling["polls_per_minute"])
        if v > 0 and v != polls_per_minute:
            polls_per_minute = v
            changed.append(f"polls_per_minute={v:.0f}")
    if "batch_cap" in polling:
        v = int(polling["batch_cap"])
        if v > 0 and v != batch_cap:
            batch_cap = v
            changed.append(f"batch_cap={v}")

    # ── Sensor params ─────────────────────────────────────────────────────────
    sensor = cfg.get("sensor", {})
    if sensor:
        merged = {**sensor_config, **sensor}  # only overwrite provided keys
        mode_str  = merged["distance_mode"]
        budget_ms = int(merged["timing_budget_ms"])
        imp_ms    = int(merged["inter_measurement_ms"])
        roi_w     = int(merged["roi_width"])
        roi_h     = int(merged["roi_height"])
        roi_ctr   = int(merged["roi_center"])

        mode_int = MODE_MAP.get(mode_str)
        if mode_int is None:
            print(f"[cfg] unknown distance_mode '{mode_str}' — skipping sensor update")
        elif imp_ms < budget_ms:
            print(f"[cfg] inter_measurement_ms={imp_ms} < timing_budget_ms={budget_ms} — skipping sensor update")
        else:
            result = Bridge.call("apply_sensor_config",
                                 mode_int, budget_ms, imp_ms, roi_w, roi_h, roi_ctr)
            if result:
                sensor_config = merged
                changed.append(
                    f"sensor(mode={mode_str} tb={budget_ms}ms imp={imp_ms}ms "
                    f"roi={roi_w}x{roi_h} ctr={roi_ctr})"
                )
            else:
                print("[cfg] apply_sensor_config returned false — MCU rejected update")

    if changed:
        print(f"[cfg] updated: {', '.join(changed)}  poll_ms={poll_ms()}")
        Bridge.notify("blink_orange")
    elif polling or sensor:
        print("[cfg] no changes from server config")


def format_uptime(elapsed_s):
    s = int(elapsed_s)
    return f"{s // 86400}d {(s % 86400) // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def send_batch():
    global readings, batch_id

    if not readings:
        return

    batch_id += 1

    payload = {
        "app":           "timeofflightwebhook2",
        "host":          HOST,
        "batch_id":      batch_id,
        "start_time_ms": readings[0]["ts_ms"],
        "end_time_ms":   readings[-1]["ts_ms"],
        "uptime":        format_uptime(time.monotonic() - start_time),
        "config": {
            "polls_per_minute": polls_per_minute,
            "poll_ms":          poll_ms(),
            "batch_cap":        batch_cap,
            "sensor":           sensor_config,
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
            Bridge.notify("blink_green")
            if "config" in body:
                apply_server_config(body["config"])
        else:
            print(f"[batch] {resp.status_code} unexpected response: {body}")
    except Exception as exc:
        print(f"[batch] FAILED — {exc}")
        Bridge.notify("blink_red")

    readings = []


def loop():
    global last_poll_time, readings

    now = time.monotonic()

    if now - last_poll_time >= poll_ms() / 1000.0:
        last_poll_time = now
        distance = Bridge.call("get_distance")
        status   = Bridge.call("get_range_status")
        signal   = Bridge.call("get_signal_x100")
        ambient  = Bridge.call("get_ambient_x100")

        if distance is not None and distance > 0:
            readings.append({
                "ts_ms":        int(time.time() * 1000),
                "distance_mm":  distance,
                "range_status": status,
                "signal_mcps":  round(signal / 100.0, 3) if signal is not None else None,
                "ambient_mcps": round(ambient / 100.0, 3) if ambient is not None else None,
            })

        if len(readings) >= batch_cap:
            send_batch()

    time.sleep(0.01)


App.run(user_loop=loop)

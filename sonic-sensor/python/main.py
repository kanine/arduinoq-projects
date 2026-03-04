# SPDX-FileCopyrightText: Sonic Sensor App
# SPDX-License-Identifier: MPL-2.0

from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI
import threading
import time

# ── Parameters ────────────────────────────────────────────────────────────────
DEFAULT_OUT_OF_RANGE_MM = 220
DEFAULT_SENSOR_TIMEOUT_MS = 3000
POLL_INTERVAL = 0.1
MIN_OUT_OF_RANGE_MM = 100
MAX_OUT_OF_RANGE_MM = 250
MIN_SENSOR_TIMEOUT_MS = 200
MAX_SENSOR_TIMEOUT_MS = 60000
DETECTION_MARGIN_MM = 5
MIN_DROP_MM = 8
DETECTED_HOLD_MS = 350
STEADY_STATE_WINDOW_MS = 1500

# ── State ─────────────────────────────────────────────────────────────────────
state = {
    "distance_mm": None,
    "has_reading": False,
    "status": "READY",
    "sensor_timeout_ms": DEFAULT_SENSOR_TIMEOUT_MS,
    "out_of_range_mm": DEFAULT_OUT_OF_RANGE_MM,
    "cooldown_end_ms": 0,
    "detected_until_ms": 0,
    "last_detection_ms": 0,
    "last_detection_mm": None,
    "detection_count": 0,
    "previous_distance_mm": None,
    "steady_state_mm": None,
    "history": [],
}

state_lock = threading.Lock()


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def now_ms():
    return int(time.time() * 1000)


def compute_recent_average_locked(current_ms, window_ms):
    window_start_ms = current_ms - window_ms
    recent = [point["mm"] for point in state["history"] if point["t"] >= window_start_ms]
    if not recent:
        return None
    return int(round(sum(recent) / len(recent)))


def update_phase_timers_locked(current_ms):
    if state["status"] in ("DETECTED", "COOLDOWN"):
        if current_ms >= state["cooldown_end_ms"]:
            state["status"] = "READY"
            state["cooldown_end_ms"] = 0
            state["detected_until_ms"] = 0
        elif state["status"] == "DETECTED" and current_ms >= state["detected_until_ms"]:
            state["status"] = "COOLDOWN"


def get_state_payload():
    current_ms = now_ms()
    with state_lock:
        update_phase_timers_locked(current_ms)
        cooldown_remaining_ms = max(0, state["cooldown_end_ms"] - current_ms)
        steady_state_candidate_mm = compute_recent_average_locked(current_ms, STEADY_STATE_WINDOW_MS)
        comparison_base_mm = state["steady_state_mm"] if state["steady_state_mm"] is not None else state["out_of_range_mm"]

        return {
            "distance_mm": state["distance_mm"],
            "has_reading": state["has_reading"],
            "status": state["status"],
            "sensor_timeout_ms": state["sensor_timeout_ms"],
            "out_of_range_mm": state["out_of_range_mm"],
            "cooldown_remaining_ms": cooldown_remaining_ms,
            "last_detection_ms": state["last_detection_ms"],
            "last_detection_mm": state["last_detection_mm"],
            "detection_count": state["detection_count"],
            "steady_state_mm": state["steady_state_mm"],
            "steady_state_candidate_mm": steady_state_candidate_mm,
            "comparison_base_mm": comparison_base_mm,
            "history": state["history"][-20:],
        }


def should_trigger_detection(mm, previous_mm, base_mm):
    if mm > (base_mm - DETECTION_MARGIN_MM):
        return False

    if previous_mm is None:
        return True

    crossed_from_ready_zone = previous_mm >= base_mm
    moved_closer = (previous_mm - mm) >= MIN_DROP_MM
    return crossed_from_ready_zone or moved_closer


def trigger_detection_locked(current_ms, mm, comparison_base_mm):
    timeout_ms = state["sensor_timeout_ms"]
    state["status"] = "DETECTED"
    state["cooldown_end_ms"] = current_ms + timeout_ms
    state["detected_until_ms"] = min(state["cooldown_end_ms"], current_ms + DETECTED_HOLD_MS)
    state["last_detection_ms"] = current_ms
    state["last_detection_mm"] = mm
    state["detection_count"] += 1
    print(f"[DETECTION] t_ms={current_ms} distance_mm={mm} base_mm={comparison_base_mm}")


def apply_config_update_locked(data):
    updated = False

    timeout_ms = data.get("sensor_timeout_ms")
    if timeout_ms is not None:
        try:
            timeout_ms = int(timeout_ms)
            timeout_ms = clamp(timeout_ms, MIN_SENSOR_TIMEOUT_MS, MAX_SENSOR_TIMEOUT_MS)
            if timeout_ms != state["sensor_timeout_ms"]:
                state["sensor_timeout_ms"] = timeout_ms
                updated = True
                # Keep active cooldown aligned with updated timeout.
                if state["status"] in ("DETECTED", "COOLDOWN"):
                    state["cooldown_end_ms"] = now_ms() + timeout_ms
        except (TypeError, ValueError):
            pass

    out_of_range_mm = data.get("out_of_range_mm")
    if out_of_range_mm is not None:
        try:
            out_of_range_mm = int(out_of_range_mm)
            out_of_range_mm = clamp(out_of_range_mm, MIN_OUT_OF_RANGE_MM, MAX_OUT_OF_RANGE_MM)
            if out_of_range_mm != state["out_of_range_mm"]:
                state["out_of_range_mm"] = out_of_range_mm
                updated = True
        except (TypeError, ValueError):
            pass

    return updated


def update_from_sensor(mm):
    current_ms = now_ms()
    has_reading = mm >= 0

    with state_lock:
        update_phase_timers_locked(current_ms)

        state["has_reading"] = has_reading
        state["distance_mm"] = mm if has_reading else None

        if has_reading:
            state["history"].append({"t": current_ms, "mm": mm})
            if len(state["history"]) > 60:
                state["history"].pop(0)

        if state["status"] == "READY" and has_reading:
            comparison_base_mm = state["steady_state_mm"] if state["steady_state_mm"] is not None else state["out_of_range_mm"]
            if should_trigger_detection(mm, state["previous_distance_mm"], comparison_base_mm):
                trigger_detection_locked(current_ms, mm, comparison_base_mm)

        state["previous_distance_mm"] = mm if has_reading else None


def on_update_config(client, data):
    with state_lock:
        apply_config_update_locked(data or {})

    ui.send_message("sensor_update", get_state_payload())


def on_set_steady_state(client, data):
    with state_lock:
        current_ms = now_ms()
        steady_state_mm = compute_recent_average_locked(current_ms, STEADY_STATE_WINDOW_MS)
        if steady_state_mm is None and state["distance_mm"] is not None:
            steady_state_mm = state["distance_mm"]
        if steady_state_mm is not None:
            state["steady_state_mm"] = int(steady_state_mm)
            print(f"[STEADY_STATE] confirmed_mm={state['steady_state_mm']}")

    ui.send_message("sensor_update", get_state_payload())


def on_get_initial_state(client, data):
    """Browser connected and requesting current state."""
    ui.send_message("sensor_update", get_state_payload(), client)


# ── Sensor polling loop ───────────────────────────────────────────────────────
def sensor_loop():
    while True:
        try:
            mm = int(Bridge.call("get_distance"))
        except Exception:
            mm = -1

        update_from_sensor(mm)
        ui.send_message("sensor_update", get_state_payload())
        time.sleep(POLL_INTERVAL)


# ── Initialise WebUI ──────────────────────────────────────────────────────────
ui = WebUI()
ui.on_message("get_initial_state", on_get_initial_state)
ui.on_message("update_config", on_update_config)
ui.on_message("set_steady_state", on_set_steady_state)

# Start sensor polling in background thread
t = threading.Thread(target=sensor_loop, daemon=True)
t.start()

# Start the app (blocking)
App.run()

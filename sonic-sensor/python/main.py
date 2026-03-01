# SPDX-FileCopyrightText: Sonic Sensor App
# SPDX-License-Identifier: MPL-2.0

from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI
import threading
import time

# ── Parameters ────────────────────────────────────────────────────────────────
OUT_OF_RANGE   = 2000   # mm  – must match sketch value
SENSOR_TIMEOUT = 3.0    # seconds – how long alert stays active after last in-range hit
POLL_INTERVAL  = 0.15   # seconds between Bridge calls

# ── State ─────────────────────────────────────────────────────────────────────
state = {
    "distance_mm":  None,
    "in_range":     False,
    "alert_active": False,
    "last_hit_time": 0.0,
    "history": [],          # last 20 readings for sparkline [{t, mm}, ...]
}

def get_state_payload():
    return {
        "distance_mm":  state["distance_mm"],
        "in_range":     state["in_range"],
        "alert_active": state["alert_active"],
        "history":      state["history"][-20:],
    }

# ── Sensor polling loop ───────────────────────────────────────────────────────
def sensor_loop():
    while True:
        try:
            result   = Bridge.call("get_distance", False)
            mm       = int(result[0])
            in_range = bool(result[1])
        except Exception:
            mm       = -1
            in_range = False

        now = time.time()

        state["in_range"]    = in_range
        state["distance_mm"] = mm if in_range else None

        if in_range:
            state["alert_active"]  = True
            state["last_hit_time"] = now
            state["history"].append({"t": int(now * 1000), "mm": mm})
            if len(state["history"]) > 60:
                state["history"].pop(0)
        else:
            if state["alert_active"]:
                if now - state["last_hit_time"] >= SENSOR_TIMEOUT:
                    state["alert_active"] = False

        # Push live update to all connected browser clients
        ui.send_message("sensor_update", get_state_payload())

        time.sleep(POLL_INTERVAL)

# ── WebUI message handlers ────────────────────────────────────────────────────
def on_get_initial_state(client, data):
    """Browser connected and requesting current state."""
    ui.send_message("sensor_update", get_state_payload(), client)

# ── Initialise WebUI ──────────────────────────────────────────────────────────
ui = WebUI()
ui.on_message("get_initial_state", on_get_initial_state)

# Start sensor polling in background thread
t = threading.Thread(target=sensor_loop, daemon=True)
t.start()

# Start the app (blocking)
App.run()

from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI
import os
import json
from pathlib import Path
import time

ui = WebUI()

POLL_INTERVAL_SECONDS = 0.1


def detect_app_name():
    app_home = os.environ.get("APP_HOME", "").strip()
    if app_home:
        app_home_name = Path(app_home).name
        if app_home_name:
            return app_home_name

    for candidate in (Path.cwd().name, Path(__file__).resolve().parent.parent.name):
        if candidate and candidate not in {"app", "python"}:
            return candidate

    return "unknown-app"


CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


config = load_config()
START_MEASURE = config["measurements"]["startMeasure"]
WINDOW_SECONDS = config["measurements"]["windowSeconds"]
FULL_RADIUS = config["spool"]["fullRadius"]
CORE_RADIUS = config["spool"]["coreRadius"]
END_MEASURE = START_MEASURE + (FULL_RADIUS - CORE_RADIUS)

APP_NAME = detect_app_name()

readings = []
window_started_at = time.monotonic()
last_distance = -1


def calculate_trimmed_average(samples):
    valid_samples = [sample for sample in samples if sample != -1]
    if not valid_samples:
        return -1

    sorted_samples = sorted(valid_samples)
    sample_count = len(sorted_samples)
    trim_count = int(sample_count * 0.1)

    if trim_count > 0 and sample_count > (trim_count * 2):
        sorted_samples = sorted_samples[trim_count:-trim_count]

    if not sorted_samples:
        return -1

    return round(sum(sorted_samples) / len(sorted_samples))


def calculate_percent(distance):
    if distance == -1 or distance > 4000:
        return None
    frac = (END_MEASURE - distance) / (END_MEASURE - START_MEASURE)
    frac = max(0.0, min(1.0, frac))
    r_current = CORE_RADIUS + (FULL_RADIUS - CORE_RADIUS) * frac
    percent = (r_current**2 - CORE_RADIUS**2) / (FULL_RADIUS**2 - CORE_RADIUS**2) * 100
    return round(max(0.0, min(100.0, percent)), 1)


def handle_settings(client, data):
    global START_MEASURE, WINDOW_SECONDS, END_MEASURE, config

    new_start = data.get("startMeasure")
    new_window = data.get("windowSeconds")

    if new_start is not None:
        START_MEASURE = float(new_start)
        END_MEASURE = START_MEASURE + (FULL_RADIUS - CORE_RADIUS)
        config["measurements"]["startMeasure"] = START_MEASURE

    if new_window is not None:
        WINDOW_SECONDS = float(new_window)
        config["measurements"]["windowSeconds"] = WINDOW_SECONDS

    save_config(config)


def on_get_settings(client, data):
    ui.send_message("settings", {
        "startMeasure": START_MEASURE,
        "windowSeconds": WINDOW_SECONDS,
    }, client)


ui.on_message("settings_update", handle_settings)
ui.on_message("get_settings", on_get_settings)


def loop():
    global readings, window_started_at, last_distance

    distance = Bridge.call("get_distance")
    if distance is not None:
        readings.append(distance)
        last_distance = distance

    now = time.monotonic()
    if (now - window_started_at) >= WINDOW_SECONDS:
        completed_readings = readings[:]
        avg = calculate_trimmed_average(completed_readings)
        ui.send_message("distance_update", {
            "distance": last_distance,
            "average": avg,
            "percent": calculate_percent(avg),
            "readings": completed_readings,
            "app_name": APP_NAME,
            "settings": {
                "startMeasure": START_MEASURE,
                "windowSeconds": WINDOW_SECONDS,
            },
        })
        readings = []
        window_started_at = now

    time.sleep(POLL_INTERVAL_SECONDS)


App.run(user_loop=loop)

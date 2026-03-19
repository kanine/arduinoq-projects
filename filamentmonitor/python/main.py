from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI
import os
import json
from pathlib import Path
import time

ui = WebUI()

WINDOW_SECONDS = 2.0
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


def load_config():
    config_path = Path(__file__).resolve().parent.parent / "config.json"
    with open(config_path) as f:
        return json.load(f)


config = load_config()
START_MEASURE = config["measurements"]["startMeasure"]
END_MEASURE = config["measurements"]["endMeasure"]

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
    range_mm = END_MEASURE - START_MEASURE
    pct = (1 - (distance - START_MEASURE) / range_mm) * 100
    return round(max(0.0, min(100.0, pct)), 1)


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
        })
        readings = []
        window_started_at = now

    time.sleep(POLL_INTERVAL_SECONDS)


App.run(user_loop=loop)

from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI
import time

ui = WebUI()

WINDOW_SECONDS = 2.0
POLL_INTERVAL_SECONDS = 0.1

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


def loop():
    global readings, window_started_at, last_distance

    distance = Bridge.call("get_distance")
    if distance is not None:
        readings.append(distance)
        last_distance = distance

    now = time.monotonic()
    if (now - window_started_at) >= WINDOW_SECONDS:
        completed_readings = readings[:]
        ui.send_message("distance_update", {
            "distance": last_distance,
            "average": calculate_trimmed_average(completed_readings),
            "readings": completed_readings,
        })
        readings = []
        window_started_at = now

    time.sleep(POLL_INTERVAL_SECONDS)


App.run(user_loop=loop)

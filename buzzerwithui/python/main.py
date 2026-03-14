import threading
from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI

buzzer_is_on = False
buzzer_hw_on = False
_pattern_thread = None
_stop_event = threading.Event()


def get_buzzer_status():
    return {
        "buzzer_is_on": buzzer_is_on,
        "buzzer_hw_on": buzzer_hw_on,
        "status_text": "BUZZER ON" if buzzer_is_on else "BUZZER OFF"
    }


def _set_hw(state):
    global buzzer_hw_on
    buzzer_hw_on = state
    Bridge.call("set_buzzer_state", state)
    ui.send_message('buzzer_status_update', get_buzzer_status())


def _stop_pattern():
    global _pattern_thread
    if _pattern_thread and _pattern_thread.is_alive():
        _stop_event.set()
        _pattern_thread.join(timeout=3)
    _stop_event.clear()
    _pattern_thread = None


def _run_pattern(duration, interval, loops):
    global buzzer_is_on
    for i in range(loops):
        if _stop_event.is_set():
            break
        _set_hw(True)
        if _stop_event.wait(duration):
            break
        _set_hw(False)
        if i < loops - 1:
            if _stop_event.wait(interval):
                break
    buzzer_is_on = False
    _set_hw(False)


def toggle_buzzer_state(client, data):
    global buzzer_is_on, _pattern_thread

    _stop_pattern()

    new_state = bool(data.get("state", False))
    duration = float(data.get("duration", 0.25))
    interval = float(data.get("interval", 0.0))
    loops = int(data.get("loops", 1))

    if new_state:
        buzzer_is_on = True
        if interval <= 0:
            _set_hw(True)
        else:
            _pattern_thread = threading.Thread(
                target=_run_pattern,
                args=(duration, interval, loops),
                daemon=True
            )
            _pattern_thread.start()
            ui.send_message('buzzer_status_update', get_buzzer_status())
    else:
        buzzer_is_on = False
        _set_hw(False)


def on_get_initial_state(client, data):
    ui.send_message('buzzer_status_update', get_buzzer_status(), client)


ui = WebUI()
ui.on_message('toggle_buzzer', toggle_buzzer_state)
ui.on_message('get_initial_state', on_get_initial_state)

App.run()

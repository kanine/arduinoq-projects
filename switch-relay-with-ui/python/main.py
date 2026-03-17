from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI

relay_is_on = False

def get_relay_status():
    return {
        "relay_is_on": relay_is_on,
        "status_text": "RELAY ON" if relay_is_on else "RELAY OFF"
    }

def toggle_relay(client, data):
    global relay_is_on
    relay_is_on = not relay_is_on
    Bridge.call("set_relay_state", relay_is_on)
    ui.send_message('relay_status_update', get_relay_status())

def on_get_initial_state(client, data):
    ui.send_message('relay_status_update', get_relay_status(), client)

ui = WebUI()
ui.on_message('toggle_relay', toggle_relay)
ui.on_message('get_initial_state', on_get_initial_state)

App.run()

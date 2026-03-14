from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI

# Global state
buzzer_is_on = False

def get_buzzer_status():
    """Get current buzzer status for the UI."""
    return {
        "buzzer_is_on": buzzer_is_on,
        "status_text": "BUZZER ON" if buzzer_is_on else "BUZZER OFF"
    }

def toggle_buzzer_state(client, data):
    """Set the buzzer to the explicit state sent by the client."""
    global buzzer_is_on
    buzzer_is_on = bool(data.get("state", False))

    # Call the MCU function via Bridge RPC to control the buzzer
    Bridge.call("set_buzzer_state", buzzer_is_on)

    # Broadcast confirmed state to all connected clients so UIs stay in sync
    ui.send_message('buzzer_status_update', get_buzzer_status())

def on_get_initial_state(client, data):
    """Handle client request for initial buzzer state."""
    ui.send_message('buzzer_status_update', get_buzzer_status(), client)

# Initialize WebUI
ui = WebUI()

# Register socket message handlers
ui.on_message('toggle_buzzer', toggle_buzzer_state)
ui.on_message('get_initial_state', on_get_initial_state)

# Start the application
App.run()

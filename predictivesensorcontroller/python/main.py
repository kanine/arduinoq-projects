# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
#
# SPDX-License-Identifier: MPL-2.0

from arduino.app_bricks.web_ui import WebUI
from arduino.app_utils import App, Logger
import store
from controller import PredictionController

logger = Logger("pfsc-main")
ui = WebUI()

logger.info("Initializing Predictive Factory Sensor Controller")
store.init_db()

ctrl = PredictionController()

def get_status():
    """Returns current UI status."""
    return ctrl.get_status()

def trigger_simulation(payload: dict):
    """Start a simulation scenario with a given speed."""
    speed = float(payload.get('simulated_speed_mm_per_s', 300))
    try:
        res = ctrl.trigger_simulation(speed)
        return res
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        return {'error': str(e)}

def update_config(payload: dict):
    """Update runtime configuration."""
    try:
        ctrl.update_config(payload)
        return {"ok": True, "config": ctrl.get_config()}
    except Exception as e:
        return {"error": str(e)}

def get_config():
    """Retrieve runtime configuration."""
    return {"ok": True, "config": ctrl.get_config()}

def get_logs():
    """Retrieve recent cycle logs."""
    logs = store.get_recent_logs(20)
    return {"ok": True, "logs": logs}


# Register API Endpoints
ui.expose_api('GET', '/status', get_status)
ui.expose_api('POST', '/simulate', trigger_simulation)
ui.expose_api('POST', '/config', update_config)
ui.expose_api('GET', '/config', get_config)
ui.expose_api('GET', '/logs', get_logs)

if __name__ == "__main__":
    logger.info("Application loop starting...")
    App.run()

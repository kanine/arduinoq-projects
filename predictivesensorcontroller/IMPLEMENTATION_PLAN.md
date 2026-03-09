# Predictive Factory Sensor Controller - Phase 1 Implementation Plan

This implementation plan focuses on Phase 1 of the Predictive Factory Sensor Controller (PFSC) project: **Simulation & UI Foundation**. The goal is to build the Python backend and web dashboard to simulate the core timing logic and visualize the system state without requiring the physical MCU or sensors yet.

## User Review Required

Please review the proposed architecture and simulation approach.
- Does the separation of the `web` frontend boundaries and `python` backend logic match your expectations for the Uno Q environment?
- Is the proposed `POST /simulate` payload sufficient for your testing needs?

## Proposed Changes

The architecture will closely follow the pattern established in official Arduino Uno Q Brick applications (like `copy-of-led-matrix-painter` and `copy-of-qr-and-barcode-scanner`). We will use the `arduino.app_utils.App`, `arduino.app_bricks.web_ui.WebUI`, and `arduino.app_bricks.dbstorage_sqlstore.SQLStore` modules instead of third-party frameworks like Flask.

### Backend (Python MPU)

The backend will serve the API, manage the state machine, handle simulation logic, and serve the static frontend files.

#### [NEW] `python/main.py`
Main application entry point.
- Imports `arduino.app_utils.App` and `arduino.app_bricks.web_ui.WebUI`.
- Initializes `WebUI()` to serve the frontend (located in the `web` folder according to Arduino conventions).
- Exposes API endpoints using `ui.expose_api('GET', '/status', get_status)` and `ui.expose_api('POST', '/simulate', trigger_simulation)`.
- Calls `App.run()` to start the application loop.

#### [NEW] `python/controller.py`
Core logic and state management.
- Holds the configuration (distances, target length, etc.).
- Manages the current state (`sensorA`, `sensorB`, `sensorC`, `relay_active`).
- Contains the `simulation_mode` flag (defaulting to `True` for Phase 1).
- Implements the math for speed calculation and cut time prediction.
- Handles the simulated timing using Python threading timers or the `arduino.app_utils.Bridge` scheduler (if available) to update state variables at precise future times.

#### [NEW] `python/store.py`
Database persistence.
- Initializes `arduino.app_bricks.dbstorage_sqlstore.SQLStore("pfsc_db")`.
- Exposes functions to `log_cycle(data)` and `get_recent_logs(limit)`.

---

### Frontend (Web Dashboard)

The frontend will provide a visual representation of the system and controls for the simulation.

#### [NEW] `web/index.html`
Main dashboard layout.
- Header with "Simulation Mode Active" indicator.
- Visual representation of the track: Cutter -> Sensor A -> Sensor B -> Sensor C.
- Status indicators for sensors and relay.
- Form to configure parameters (target length, distances).
- "Trigger Simulation" button with speed input.

#### [NEW] `web/style.css`
Styling for the dashboard.
- Clean, industrial look.
- Clear color coding for states (e.g., active sensors light up green, relay flashes red/orange when cutting).

#### [NEW] `web/script.js`
Frontend logic.
- Polls `/status` to update the UI in real-time.
- Handles form submissions for configuration.
- Sends the `POST /simulate` request when the trigger button is clicked.

#### [NEW] `app.yaml`
Arduino Brick manifest.
- Defines the application name and icon.
- Declares the required bricks:
  - `arduino:web_ui: {}`
  - `arduino:dbstorage_sqlstore: {}`

---

## Verification Plan

### Automated Tests
- **Unit Tests (`python/test_controller.py`)**:
    - Write basic tests to verify the math in `controller.py`.
    - Test cut time prediction given a specific speed and target length.

### Manual Verification
- **Run the application**: Execute `python main.py` or deploy via the Arduino UI.
- **Open Dashboard**: Navigate to the local server URL in a browser.
- **Verify UI**: Check that the "Simulation Mode Active" indicator is prominent.
- **Run Simulation Cycle**:
    1. Enter a simulated speed (e.g., 300 mm/s) and click "Trigger Simulation".
    2. Visually verify that Sensor A, B, C, and the Relay activate in the correct sequence and with the visually expected delays on the dashboard.
    3. Verify the calculated speed and predicted cut time update correctly on the UI.
- **Edge Cases**: Try triggering a simulation with a target length shorter than the distance to Sensor C and verify the UI shows the expected error.

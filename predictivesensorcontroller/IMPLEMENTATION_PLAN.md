# Predictive Factory Sensor Controller - Phase 1 Implementation Plan

This implementation plan focuses on Phase 1 of the Predictive Factory Sensor Controller (PFSC) project: **Simulation & UI Foundation**. The goal is to build the Python backend and web dashboard to simulate the core timing logic and visualize the system state without requiring the physical MCU or sensors yet.

## User Review Required

Please review the proposed architecture and simulation approach.
- Are the chosen frameworks for the backend (e.g. Flask/FastAPI) and frontend (Vanilla JS/HTML/CSS or a framework) acceptable? Standard Python `http.server` or a lightweight framework like Flask is common for Arduino MPU projects. For this plan, I am proposing a typical lightweight Python backend (like Flask or `aiohttp`) and a vanilla HTML/JS frontend to keep it simple and aligned with the "web_ui Brick" concept.
- Is the proposed `POST /api/simulate` payload sufficient for your testing needs?

## Proposed Changes

---

### Backend (Python MPU)

The backend will serve the API, manage the state machine, handle simulation logic, and serve the static frontend files.

#### [NEW] `backend/app.py`
Main application entry point.
- Sets up the web server (e.g., Flask or `aiohttp`).
- Serves the static frontend files from `frontend/`.
- Implements the `/api/status` GET endpoint to return current state.
- Implements the `/api/simulate` POST endpoint to trigger a simulation cycle.

#### [NEW] `backend/controller.py`
Core logic and state management.
- Holds the configuration (distances, target length, etc.).
- Manages the current state (`sensorA`, `sensorB`, `sensorC`, `relay_active`).
- Contains the `simulation_mode` flag (defaulting to `True` for Phase 1).
- Implements the math for speed calculation and cut time prediction.
- Handles the simulated timing: when `/api/simulate` is called with a speed, it calculates when sensors B, C, and the Relay should trigger, and uses asynchronous tasks or timers to update the state at those precise future times.

---

### Frontend (Web Dashboard)

The frontend will provide a visual representation of the system and controls for the simulation.

#### [NEW] `frontend/index.html`
Main dashboard layout.
- Header with "Simulation Mode Active" indicator.
- Visual representation of the track: Cutter -> Sensor A -> Sensor B -> Sensor C.
- Status indicators for sensors and relay.
- Form to configure parameters (target length, distances).
- "Trigger Simulation" button with speed input.

#### [NEW] `frontend/style.css`
Styling for the dashboard.
- Clean, industrial look.
- Clear color coding for states (e.g., active sensors light up green, relay flashes red/orange when cutting).

#### [NEW] `frontend/script.js`
Frontend logic.
- Polls `/api/status` (or uses WebSockets) to update the UI in real-time.
- Handles form submissions for configuration.
- Sends the `POST /api/simulate` request when the trigger button is clicked.

---

## Verification Plan

### Automated Tests
- **Unit Tests (`backend/tests/test_controller.py`)**:
    - Write `pytest` scripts to verify the math in `controller.py`.
    - Test speed calculation given specific timestamp intervals.
    - Test cut time prediction given a specific speed and target length.
    - Test validation logic (e.g., error if target length < distance to C).

### Manual Verification
- **Run the backend**: Execute `python3 app.py`.
- **Open Dashboard**: Navigate to the local server URL in a browser.
- **Verify UI**: Check that the "Simulation Mode Active" indicator is prominent.
- **Run Simulation Cycle**:
    1. Enter a simulated speed (e.g., 300 mm/s) and click "Trigger Simulation".
    2. Visually verify that Sensor A, B, C, and the Relay activate in the correct sequence and with the visually expected delays on the dashboard.
    3. Verify the calculated speed and predicted cut time update correctly on the UI.
- **Edge Cases**: Try triggering a simulation with a target length shorter than the distance to Sensor C and verify the UI shows the expected error.

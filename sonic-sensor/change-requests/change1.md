# Change Request: Sonic-Sensor Configuration & Detection Logic

## 1. Overview
The `sonic-sensor` application requires updates to allow user-defined parameters via the web interface and a refined state machine to handle detections and cooldown periods.

---

## 2. New Configuration Settings (Frontend)
The web interface must be updated to include inputs for the following variables. These should be persisted or updated in the application state in real-time.

* **Sensor Timeout**: 
    * **Description**: The duration the system remains in a "Cooldown" state after a detection.
    * **Unit**: Milliseconds (ms) or Seconds (s).
* **Out of Range Threshold**: 
    * **Description**: The maximum distance the sensor considers "Valid/Ready".
    * **Range**: 100mm to 250mm.
    * **Logic**: Any reading below the current value represents a decrease in distance triggers a detection.

---

## 3. Revised Detection Logic & State Machine

The application should transition through the following states:

### Phase A: Ready State
* The sensor monitors distance ($d$).
* The system is "Ready" when $d$ is approximately equal to the **Out of Range** variable.

### Phase B: Detection Event
* **Trigger**: A detection occurs when $d < \text{Out of Range}$.
* **Action**: 
    1.  Log the detection event.
    2.  Immediately transition the UI to a **Timer/Cooldown** state.

### Phase C: Timeout/Cooldown
* **Action**: Start a countdown timer on the web page.
* **Duration**: Set by the **Sensor Timeout** variable.
* **Constraint**: The sensor should ignore new detections until the timer reaches zero.

### Phase D: Reset
* Once the timer expires, the system returns to the **Ready State**.

---

## 4. Technical Requirements

### UI Components
- [ ] Add numeric inputs or sliders for `Sensor Timeout` and `Out of Range`.
- [ ] Implement a visual timer (e.g., a progress bar or digital countdown) that triggers on detection.
- [ ] Add a status indicator label: `STATUS: READY`, `STATUS: DETECTED`, or `STATUS: COOLDOWN`.

### Logic Update
- [ ] Implement the comparison: `if (currentDistance < outOfRangeValue)`.
- [ ] Ensure the "shorter distance" logic is prioritized to prevent false triggers from background noise.
- [ ] Create a non-blocking delay or interrupt-based timer to handle the timeout period.

---

## 5. Success Criteria
1.  Changing settings in the UI updates the sensor behavior without a full app restart.
2.  The timer starts immediately when an object passes in front of the sensor (distance decreases).
3.  The system correctly ignores all input during the "Timeout" period.
4.  The system returns to "Ready" automatically after the timeout
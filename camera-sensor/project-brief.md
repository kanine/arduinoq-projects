# Project Spec: Uno Q Multi-Zone Occupancy & Duration Tracker

## 1. Overview
A Python-based application for the **Arduino Uno Q** using the **App Lab** environment. The application monitors a video feed, identifies if objects are present within three user-defined segments (Zones), and calculates the total duration an object remains within each specific zone.

## 2. Target Hardware & Environment
* **Hardware:** Arduino Uno Q (2025 Model)
* **OS/Runtime:** Debian-based Linux (MPU side) / App Lab
* **Primary Brick:** `arduino.app_bricks.video_objectdetection`
* **Language:** Python 3.x

## 3. Functional Requirements

### 3.1 Spatial Segmentation (Zones)
The application must divide the 640x480 (standard) camera feed into three distinct rectangular regions of interest (ROIs):
* **Zone 1 (Left):** x from 0 to 213
* **Zone 2 (Center):** x from 214 to 426
* **Zone 3 (Right):** x from 427 to 640

### 3.2 Detection Logic
* **Base State:** "Nothing" (The AI model should ideally be trained on a 'Background' class, or use a low-confidence threshold for any non-background object).
* **Event Trigger:** An "Occupancy Start" event is triggered when the center point (x + w/2, y + h/2) of a bounding box enters a zone.
* **Event Resolution:** An "Occupancy End" event is triggered when no objects are detected in that zone for a "grace period" (debounce) of 1.0 seconds.

### 3.3 Temporal Tracking
* Maintain a dictionary/object to track `start_time` for each zone.
* Calculate `duration = current_time - start_time` upon "Occupancy End".
* Log the result to the console/terminal.

## 4. Technical Implementation Details

### 4.1 State Management
```python
zone_states = {
    "zone_1": {"active": False, "start_time": 0, "last_seen": 0},
    "zone_2": {"active": False, "start_time": 0, "last_seen": 0},
    "zone_3": {"active": False, "start_time": 0, "last_seen": 0}
}
```

### 4.2 Core Logic Flow
* Initialize `VideoObjectDetection` brick.

In the `on_detect_all` callback:

* Iterate through all detected objects.
* Determine which zone the object center belongs to based on the x-coordinate.
* Update `last_seen` timestamp for that zone.
* If `active` is `False`, set `active = True` and `start_time = current_time`.
* Implement a background heartbeat to check if `(current_time - last_seen) > 1.0s`.
* If true and the zone was active, calculate total duration and reset state.

## 5. Visual Output
* Print a summary table to the console showing occupancy status.
* Use the Uno Q 8x13 LED Matrix to display the active zone number (`1`, `2`, or `3`).

## 6. Constraints
* **Latency:** The tracking logic must not block the video inference stream.
* **False Positives:** Implement a minimum confidence threshold (`>0.45`) to ignore sensor noise.

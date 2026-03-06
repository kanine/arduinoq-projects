# Arduino Uno Q Workspace

This workspace is dedicated to developing and managing applications for the **Arduino Uno Q**, a dual-processor board featuring an MCU (ATmega/Microcontroller) and an MPU (Linux/Microprocessor).

## Project Overview

The project consists of multiple standalone "Apps," each leveraging the dual-processor architecture to combine real-time hardware control with high-level logic and web interfaces.

### Core Technologies
- **Hardware:** Arduino Uno Q (MCU + MPU).
- **MCU Side:** C++ (Arduino) using `Arduino_RouterBridge` for communication.
- **MPU Side:** Python 3 using `arduino.app_utils` and `Bridge` for RPC.
- **Web UI:** HTML/CSS/JS, often using Socket.io for real-time data streaming from the MPU.
- **Configuration:** `app.yaml` for metadata and "Bricks" (modular functional components like `web_ui`).

### App Structure
Each app directory follows a standard layout:
- `app.yaml`: Metadata, description, and brick configurations.
- `sketch/`: Contains the MCU code (`sketch.ino`) and board/library configuration (`sketch.yaml`).
- `python/`: Contains the MPU logic (`main.py`), typically polling the MCU and handling high-level state.
- `assets/`: (Optional) Web assets (`index.html`, `style.css`, `app.js`) served by the MPU.
- `README.md`: App-specific hardware requirements and parameters.

## Building and Running

The primary tool for managing these apps is the `arduino-app-cli` (aliased as `arduino-app` in some contexts).

### Key Commands
- **Run an App:**
  ```bash
  arduino-app run <app-directory>
  # OR
  arduino-app-cli app start /home/arduino/ArduinoApps/<app-directory>
  ```
- **Stop an App:**
  ```bash
  arduino-app-cli app stop /home/arduino/ArduinoApps/<app-directory>
  ```
- **View Logs:**
  ```bash
  arduino-app-cli app logs /home/arduino/ArduinoApps/<app-directory> --all
  ```
- **List Apps:**
  ```bash
  arduino-app-cli app list
  ```

## Development Conventions

### Communication (The Bridge)
Apps should use the `Bridge` for communication between the MCU and MPU:
- **MCU (C++):**
  ```cpp
  #include <Arduino_RouterBridge.h>
  void setup() {
      Bridge.begin();
      Bridge.provide("my_method", my_method_func);
  }
  ```
- **MPU (Python):**
  ```python
  from arduino.app_utils import *
  result = Bridge.call("my_method")
  ```

### Wiring Documentation (ATN-IO v3)
Hardware connections must be documented using the **ATN-IO v3** (Arduino Text Notation) format, as defined in `wiring-notation.md`. This format separates logical mapping, physical wiring, and components for clarity and machine-parseability.

### Hardware Safety
- **Logic Levels:** The Uno Q GPIOs are **3.3V**. When interfacing with 5V components (like the HC-SR04), use voltage dividers or level shifters for input pins.
- **Power:** Always document whether components are powered via the 5V rail, 3.3V rail, or an external supply.

## Key Files
- `README.md`: General workspace information and useful links.
- `wiring-notation.md`: Comprehensive guide to the ATN-IO v3 wiring documentation standard.
- `.codex/skills/`: Contains specialized agent skills for working with the `arduino-app-cli`.

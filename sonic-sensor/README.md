# Sonic Sensor App

Displays live HC-SR04 ultrasonic distance readings on a web dashboard served directly from the Arduino Uno Q. Includes configurable out-of-range detection and alert timeout logic.

## Hardware

| Component | Connection |
|-----------|-----------|
| HC-SR04 VCC | 5V rail |
| HC-SR04 GND | GND rail |
| HC-SR04 TRIG | D6 |
| HC-SR04 ECHO | Voltage divider → D7 |

### ECHO voltage divider (required)

The HC-SR04 ECHO pin outputs 5V. The Uno Q GPIO is 3.3V. Wire a voltage divider:

```
HC-SR04 ECHO → [10kΩ] → D7 → [20kΩ] → GND
```

This brings 5V down to ~3.3V before it reaches the Uno Q pin.

## Parameters

Edit these values at the top of both `sketch/sketch.ino` and `python/main.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `OUT_OF_RANGE` | 2000 mm | Readings >= this are treated as no target |
| `SENSOR_TIMEOUT` | 3.0 s | How long the alert stays active after the last in-range reading |

## Running

```bash
arduino-app run sonic-sensor
```

Dashboard available at `http://<board-ip>:7000`

## File structure

```
sonic-sensor/
├── app.yaml
├── sketch/
│   ├── sketch.ino      # MCU: reads HC-SR04, exposes get_distance() via Bridge
│   └── sketch.yaml     # Board/library config
├── python/
│   └── main.py         # MPU: polls Bridge, applies alert logic, serves WebUI
└── assets/
    ├── index.html      # Dashboard markup
    ├── style.css       # Dark industrial theme
    ├── app.js          # Socket.io client + sparkline renderer
    └── libs/
        └── socket.io.min.js   # Copy from sample-blink-with-ui/assets/libs/
```

## Note on socket.io.min.js

Copy the bundled file from the sample app rather than pulling from a CDN — the board may not have internet access:

```bash
cp ~/ArduinoApps/sample-blink-with-ui/assets/libs/socket.io.min.js \
   ~/ArduinoApps/sonic-sensor/assets/libs/
```
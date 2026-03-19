# Time of Flight Check

Arduino Uno Q utility app for verifying communication with a single VL53L1X Time-of-Flight sensor and viewing a stabilized distance reading in a small web dashboard.

## Purpose

This app is a focused hardware bring-up tool.

It verifies:
- whether the MCU can see the sensor at `0x29` on the I2C bus
- whether the VL53L1X initializes correctly
- whether live ranging is available
- whether the measured distance is stable over a 2 second sampling window

It does not include:
- multi-sensor address assignment
- prediction logic
- relay handling
- persistent configuration

## Current Behavior

- The MCU reads the VL53L1X over `Wire1` at `400 kHz`.
- The Python backend polls the MCU every `0.1` seconds.
- The web UI updates once every `2` seconds.
- Each displayed value is a trimmed mean over the last 2 second batch:
  - discard the lowest 10% of valid readings
  - discard the highest 10% of valid readings
  - average the remaining readings
- Invalid `-1` readings are excluded from the displayed average.
- The UI also shows the latest raw reading from the same completed batch.
- An optional browser toggle can log each completed 2 second batch to the browser console.

## Proven Finding

For this workspace and board setup, the successful MCU-side VL53L1X path used:
- `Wire1`
- `400 kHz` I2C clock

That finding was then applied back into `predictivesensorcontroller`.

## App Layout

```text
timeofflightcheck/
├── app.yaml
├── README.md
├── assets/
│   ├── app.js
│   ├── index.html
│   └── style.css
├── python/
│   └── main.py
└── sketch/
    ├── sketch.ino
    └── sketch.yaml
```

## LED Meanings

The built-in LED is used as a runtime health indicator:

- fast blink: sketch is starting or scanning
- slow blink: no I2C ACK at `0x29`
- double blink: sensor answered on I2C, but init failed
- solid on: sensor init succeeded and ranging is running

## Wiring Notes

- This utility was used during single-sensor bring-up.
- `XSHUT` is not required for the basic comms test.
- The sensor remains at default address `0x29`.
- Use the Qwiic connector or `Wire1` pin pair on the Uno Q.
- Power the sensor from `3.3V`.

## Web UI Notes

- The web dashboard displays the 2 second trimmed average as the main value.
- The smaller label beneath it shows the latest raw sample captured in that window.
- If `Log each 2s reading batch to browser console` is enabled, the browser console receives:
  - the displayed trimmed average
  - the raw reading
  - the full batch of readings used for that refresh

## When To Use It

Use this app when:
- a new VL53L1X sensor is first connected
- sensor comms are failing in a larger app
- you want to validate the hardware path before adding more application logic
- you want a quick visual check of short-term distance stability

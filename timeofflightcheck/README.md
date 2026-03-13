# Time of Flight Check

Minimal Arduino Uno Q utility app for verifying communication with a single VL53L1X Time-of-Flight sensor before integrating it into a larger App Lab project.

## Purpose

This app exists as a hardware bring-up tool.

It is intentionally narrow:
- no web UI
- no Python backend
- no prediction logic
- no relay handling

It only verifies:
- whether the MCU can see `0x29` on the sensor bus
- whether the VL53L1X initializes correctly
- whether live readings are available

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

## When To Use It

Use this app when:
- a new VL53L1X sensor is first connected
- sensor comms are failing in a larger app
- you want to validate the hardware path before adding more application logic

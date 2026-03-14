# Time of Flight Config

Minimal Arduino Uno Q utility app for reassigning the I2C addresses of two VL53L1X
Time-of-Flight sensors via sequential XSHUT power-cycling.

## Purpose

This app is a hardware checkpoint tool.

It is intentionally narrow:
- no ranging logic
- no web UI
- no database
- no prediction or relay handling

It only does one thing:
- power-cycle two VL53L1X sensors sequentially via individual XSHUT pins
- verify each sensor responds at the default address `0x29` before reassignment
- reassign sensor 1 to `0x30`, sensor 2 to `0x31`
- verify each sensor responds at its new address
- report success or failure via LED blink count and Monitor output

## Why This Exists

During Phase 3 Attempt 1 of `predictivesensorcontroller`, XSHUT-controlled address
reassignment could not be validated in isolation — it was entangled with the full
two-sensor bring-up, diagnostics service, and web UI.

`timeofflightconfig` isolates the address reassignment step so it can be tested and
confirmed independently before it is reintroduced into the main controller app.

## Relationship to timeofflightcheck

`timeofflightcheck` validated: can the MCU see and initialise a VL53L1X at `0x29`?

`timeofflightconfig` validates: can the MCU reassign a VL53L1X from `0x29` to a new address
using XSHUT, and confirm the sensor responds at that new address?

These are sequential hardware checkpoints. `timeofflightconfig` assumes `timeofflightcheck`
has already passed.

## Hardware Requirements

- Two VL53L1X sensors on the Qwiic/STEMMA QT bus (Wire1)
- Sensor 1 XSHUT → D3 (PB0)
- Sensor 2 XSHUT → D4 (PA12)
- Both sensors start at default address `0x29`

## Startup Sequence

1. Pull D3 and D4 LOW — both sensors off
2. Short delay (10 ms)
3. Pull D3 HIGH — sensor 1 boots at `0x29`
4. Probe `0x29`, init, call `setAddress(0x30)`, confirm ACK at `0x30`
5. Pull D4 HIGH — sensor 2 boots at `0x29` (now free since sensor 1 moved to `0x30`)
6. Probe `0x29`, init, call `setAddress(0x31)`, confirm ACK at `0x31`
7. Solid LED + Monitor confirmation

## LED Meanings

Blink count identifies which sensor failed and how:

| Blinks | Meaning |
|---|---|
| Fast ×4 | Starting / sequencing |
| 1 | Sensor 1: no ACK at `0x29` |
| 2 | Sensor 1: init failed |
| 3 | Sensor 1: no ACK at `0x30` after reassignment |
| 4 | Sensor 2: no ACK at `0x29` |
| 5 | Sensor 2: init failed |
| 6 | Sensor 2: no ACK at `0x31` after reassignment |
| Solid on | Both sensors configured — S1=`0x30`, S2=`0x31` |

## App Layout

```text
timeofflightconfig/
├── app.yaml
├── projectbrief.md
└── sketch/
    ├── sketch.ino
    └── sketch.yaml
```

No Python backend. MCU-only app.

## When To Use It

Use this app when:
- setting up a VL53L1X for multi-sensor use for the first time
- validating that XSHUT control works on the current wiring before running Phase 3
- diagnosing whether address reassignment failure is a hardware or software issue
- confirming which address a sensor will respond on after power-on

## Wiring Notes

- Both sensors on the Qwiic bus (Wire1, 400 kHz) — shared SDA/SCL
- Sensor 1 XSHUT → D3 (PB0)
- Sensor 2 XSHUT → D4 (PA12)
- Both sensors VCC → 3.3 V, GND → GND

## Known-Good I2C Path

From timeofflightcheck:
- Bus: `Wire1`
- Clock: `400 kHz`
- Default address: `0x29`

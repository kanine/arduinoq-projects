# Relay Module Specifications

## Overview

1-channel relay board with optocoupler isolation, suitable for controlling AC/DC loads via a microcontroller signal on D8.

## Electrical Ratings

| Parameter | Value |
|---|---|
| Maximum AC load | 250 V / 10 A |
| Maximum DC load | 30 V / 10 A |
| Trigger current | 5 mA |
| Coil supply voltage | 3.3 V DC (from board 3.3 V rail — tested and confirmed working) |

## Terminals

| Terminal | Label | Purpose |
|---|---|---|
| Relay output | NO | Normally Open — load circuit is open when relay is off |
| Relay output | C | Common — one side of the switched load |
| Relay output | NC | Normally Closed — load circuit is closed when relay is off |
| Control input | Coil+ (VCC) | Positive supply for relay coil |
| Control input | Coil− (GND) | Ground for relay coil |
| Control input | Trigger (IN) | Logic signal from MCU (D8) |

## Trigger Polarity (Jumper)

The module has a jumper that selects whether the relay activates on a **HIGH** or **LOW** signal:

- **HIGH trigger (default):** relay ON when D8 = HIGH
- **LOW trigger:** relay ON when D8 = LOW

The sketch in this app is written for **HIGH trigger** (default jumper position). If the jumper is changed to LOW trigger, invert the logic in `sketch.ino`:

```cpp
// LOW-trigger variant — invert the signal
digitalWrite(8, state ? LOW : HIGH);
```

## Isolation

Uses an **optocoupler** between the trigger input and the relay coil circuit. This:

- Protects the MCU I/O port from relay switching transients
- Prevents damage if the control line is broken or floating
- Provides strong driving ability and stable performance

## Safety Notes

- Wire the **load** across **NO** and **C** terminals for normally-open operation (load is off when board is unpowered — safer default).
- Do **not** exceed the rated load (10 A / 250 VAC).
- All GPIOs on the Arduino Uno Q are **3.3 V** — coil VCC and IN trigger both operate at 3.3 V; **tested and confirmed working** at this voltage.
- Use appropriate wire gauge and connectors for the load current.
- The relay has indicator LEDs for power and relay action status.

## Mounting

- Fixed bolt holes on both sides (diameter: 3.1 mm)
- Screw terminals for all connections (relay contacts and control input)

## Applications

General-purpose switching: LED lighting, motors, solenoids, electromagnetic relays, pumps, fans, and other resistive or inductive loads within the rated limits.

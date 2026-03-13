# Adafruit VL53L1X Reference

This file distills the two source references the user supplied:

- Adafruit product page for product `3967`
- Adafruit Learning System guide for `Adafruit VL53L1X Time of Flight Distance Sensor`

Use it when exact sensor facts matter. Treat items labeled `Inference` as derived guidance rather than direct vendor statements.

## Source Links

- Product page: <https://www.adafruit.com/product/3967?srsltid=AfmBOoojfovWcfp71tNem1QAvZYVcDSqJ24pIH7Zu5Dmg9xN3taTI15Q>
- Guide overview: <https://learn.adafruit.com/adafruit-vl53l1x>
- Guide pinouts: <https://learn.adafruit.com/adafruit-vl53l1x/pinouts>
- Guide Arduino page: <https://learn.adafruit.com/adafruit-vl53l1x/arduino>
- Guide Python page: <https://learn.adafruit.com/adafruit-vl53l1x/python-circuitpython>

## Board Facts

- The board is sold as `Adafruit VL53L1X Time of Flight Distance Sensor` and is also referred to as `VL53L1CX`.
- It uses a narrow optical Time-of-Flight measurement rather than sonar-style acoustic ranging.
- Advertised range is about `30 mm` to `4000 mm`.
- Advertised update rate is up to `50 Hz`.
- Typical full field of view is `27 degrees`.
- The breakout exposes `I2C`, `XSHUT`, and `GPIO` pins.
- Default I2C address is `0x29`.
- The breakout includes regulator and level shifting so it can be used with common `3V` or `5V` microcontrollers.
- The `GPIO` interrupt output is `2.8V` logic level output.
- The `XSHUT` pin is logic-level shifted and active low.

## Practical Hardware Notes

- Remove the shipping protective film before first use.
- Power the breakout from the logic-domain supply used by the host board according to the guide examples.
- The product page states I2C up to `400 kHz`.
- STEMMA QT / Qwiic connectors are available for no-solder I2C wiring.
- `Inference`: a powered Qwiic/STEMMA QT connection does not by itself prove the sensor is visible on the same I2C controller the target sketch is using.
- `Inference`: on Arduino Uno Q bring-up, treat bus selection as a first-class diagnostic question and verify the working controller early.

## Multi-Sensor Notes

- All sensors boot at `0x29`.
- The product page states the address can be changed in software by using the shutdown pin to disable other sensors on the same bus.
- `Inference`: for three sensors on one bus, hold two in shutdown, bring one up, assign a new address, then repeat until each sensor has a unique address.
- `Inference`: document the final address map in code comments or configuration because replacement hardware will otherwise collide at boot.

## Arduino API Pattern

The Adafruit guide's Arduino example shows this flow:

1. Include `Adafruit_VL53L1X.h`
2. Construct with `XSHUT` and `IRQ` pins
3. Call `Wire.begin()`
4. Call `begin(0x29, &Wire)`
5. Call `startRanging()`
6. Optionally set timing budget
7. Poll `dataReady()`
8. Read `distance()`
9. Call `clearInterrupt()`

Noted details from the example:

- Valid timing budgets shown are `15`, `20`, `33`, `50`, `100`, `200`, and `500` ms.
- Example wiring for a 5V Arduino-class board connects:
  - `5V` to `VIN`
  - `GND` to `GND`
  - `SCL` to `SCL`
  - `SDA` to `SDA`
  - digital pin `2` to `GPIO`
  - digital pin `3` to `XSHUT`

## Uno Q Bring-Up Notes

- `Inference`: in this workspace, a successful single-sensor VL53L1X bring-up on Arduino Uno Q used `Wire1`, not the initial `Wire` assumption.
- `Inference`: Qwiic power-up was observed before MCU I2C comms were confirmed; direct validation still depended on using the correct MCU bus.
- `Inference`: for first hardware tests on Uno Q, a minimal serial-only sketch is valuable for isolating bus selection and sensor init before adding Bridge or web diagnostics.
- `Inference`: if the preferred vendor Arduino library is unavailable in the board toolchain, choose an installed library with equivalent sensor coverage and validate the API flow on the actual board.

## Python And CircuitPython Pattern

The Adafruit guide shows this flow:

1. Instantiate the sensor on I2C
2. Optionally set `distance_mode`
3. Optionally set `timing_budget`
4. Call `start_ranging()`
5. Wait for `data_ready`
6. Read `distance`
7. Call `clear_interrupt()`

Noted details from the example:

- `distance_mode = 1` corresponds to short mode.
- `distance_mode = 2` corresponds to long mode.
- The example sets `timing_budget = 100`.
- The value printed by the example is in `cm`.

## Object Detection Guidance

- `Inference`: for presence detection, convert distance readings into boolean events using a threshold rather than consuming raw values directly in higher-level control logic.
- `Inference`: add hysteresis between trigger and release thresholds to avoid chatter near the edge of the object.
- `Inference`: when using multiple sensors for speed estimation, keep timing budget consistent across sensors so timestamp skew is easier to reason about.
- `Inference`: if precise trigger timing matters more than full-range accuracy, choose the shortest timing budget that remains stable in the real mounting geometry.

## Fit For The Current Project

For the predictive sensor controller project:

- Use one VL53L1X at each detection point.
- Treat each sensor event as a threshold crossing in the measured distance stream.
- Base speed calculations on the timestamps of those crossings, not on continuously varying distance values.
- Plan the bus and startup logic early because three sensors cannot all remain at the default address.
- Validate the first sensor on the proven Uno Q MCU bus before scaling out to the multi-sensor topology.

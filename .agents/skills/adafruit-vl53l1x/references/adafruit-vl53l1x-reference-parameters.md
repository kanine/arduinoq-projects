# VL53L1X Technical Parameter Reference

Comprehensive reference covering all configurable parameters, status codes, calibration
procedures, ROI/SPAD grid details, interrupt/threshold modes, multi-sensor wiring,
power modes, and library API differences.

Sources: Pololu VL53L1X Arduino library (v1.3.1), ST UM2356/UM2510/UM2555 user
manuals, SparkFun VL53L1X hookup guide, ST community answers, ROS API docs.

---

## 1. Sensor Fundamentals

| Parameter | Value |
|---|---|
| Measurement principle | Time-of-Flight (VCSEL laser, 940 nm) |
| I2C default address | 0x29 (7-bit) |
| I2C max clock | 400 kHz |
| XSHUT polarity | Active LOW (pull LOW = hardware standby) |
| GPIO1 / interrupt | Active LOW by default; can be set active HIGH |
| Logic voltage (GPIO1) | 2.8 V output |
| XSHUT input | Logic-level shifted; accepts 3 V or 5 V |
| Supply voltage (VDD) | 2.6–3.5 V (breakout boards include regulator for 3–5 V hosts) |
| Min range | ~30–40 mm |
| Max range (dark, white target) | ~4000 mm (Long mode, 140 ms+ timing budget) |
| Typical accuracy | ±5 mm |
| Precision (repeatability) | 1 mm |
| Field of view (full 16x16 SPAD) | 27 degrees |
| Update rate | Up to 50 Hz |
| Boot duration | 1.2 ms max |

---

## 2. Distance Modes

Three modes are available. Set with `setDistanceMode()` on Pololu or
`setDistanceModeShort()`/`setDistanceModeLong()` on SparkFun.

| Mode | Pololu Enum | Max Range | Min Timing Budget | Notes |
|---|---|---|---|---|
| Short | `VL53L1X::Short` | ~1.3 m | 20 ms | Best ambient light immunity; best close-range accuracy |
| Medium | `VL53L1X::Medium` | ~3 m | 33 ms | Intermediate; not in all libraries |
| Long | `VL53L1X::Long` | ~4 m | 33 ms | Default; most sensitive to IR noise from sunlight |

SparkFun ULD only exposes Short (mode=1) and Long (mode=2); Medium is not available
in that library.

---

## 3. Timing Budget

The timing budget is the time the sensor spends collecting photons for one
measurement. Longer budgets reduce jitter and extend effective range.

**API (Pololu):** `setMeasurementTimingBudget(uint32_t budget_us)` — value in
microseconds.

**API (SparkFun ULD):** `setTimingBudgetInMs(uint16_t ms)` — value in milliseconds.

**API (Adafruit):** `setTimingBudget(uint16_t ms)` — value in milliseconds.

### Valid Values

| Budget | Supported Modes | Notes |
|---|---|---|
| 15 ms | Short only | Adafruit library accepts it; not recommended |
| 20 ms | Short only | Official documented minimum for Short |
| 33 ms | All modes | Official minimum for Medium and Long |
| 50 ms | All modes | Default in many examples; balanced |
| 100 ms | All modes | Typical for accurate indoor use |
| 140 ms | All modes | Enables full 4 m range in Long mode |
| 200 ms | All modes | High precision; ~5 Hz update rate |
| 500 ms | All modes | Maximum precision; ~2 Hz |
| 1000 ms | All modes | Library maximum (FDA_MAX_TIMING_BUDGET_US) |

The Pololu library enforces a hardware minimum of 4,528 µs (TimingGuard) but
recommends 20,000 µs minimum for reliable operation.

Default set by Pololu library: **50,000 µs (50 ms) with Long mode**.

---

## 4. Inter-Measurement Period (IMP)

Time from the start of one measurement to the start of the next. Controls overall
update rate and allows the sensor to idle between readings.

- Must be **>= timing budget** or the sensor starts the next measurement immediately
  after the previous one completes.
- Setting IMP = 0 (in `startContinuous(0)`) makes the sensor run back-to-back with no
  gap.

**Pololu API:** `startContinuous(uint32_t period_ms)` — sets IMP in milliseconds when
starting continuous mode. No separate `setInterMeasurementPeriod` call.

**SparkFun ULD API:** `setIntermeasurementPeriod(uint16_t ms)` / `getIntermeasurementPeriod()`.

```cpp
// Pololu: start continuous with 100 ms between measurement starts
sensor.startContinuous(100);

// SparkFun ULD: set separately before startRanging()
distanceSensor.setIntermeasurementPeriod(100);
distanceSensor.startRanging();
```

---

## 5. Region of Interest (ROI)

The VL53L1X contains a 16x16 array of 256 SPADs (Single Photon Avalanche Diodes).
The ROI is a rectangular sub-region of that array that the sensor uses for ranging.

### ROI Size

- Minimum: **4x4** SPADs
- Maximum: **16x16** SPADs (full array, default)
- A smaller ROI narrows the field of view (useful to avoid side reflections, spool
  edges, pipe walls).
- The FoV is approximately 27 degrees at 16x16, scaling down proportionally.

**Pololu API:**
```cpp
sensor.setROISize(uint8_t width, uint8_t height);
sensor.getROISize(uint8_t *width, uint8_t *height);
```

**SparkFun ULD API:**
```cpp
distanceSensor.setROI(uint8_t x, uint8_t y, uint8_t opticalCenter);
distanceSensor.getROIX();   // returns width
distanceSensor.getROIY();   // returns height
```

### ROI Center — SPAD Numbering

The sensor uses a specific non-sequential SPAD numbering scheme. The 16x16 grid is
divided into a left half (SPADs 128–255) and a right half (SPADs 0–127), numbered in
column-major order within each half.

**Complete 16x16 SPAD optical center lookup table (row 0 = top):**

```
Col:  0    1    2    3    4    5    6    7    |  8    9   10   11   12   13   14   15
Row 0: 128  136  144  152  160  168  176  184  | 192  200  208  216  224  232  240  248
Row 1: 129  137  145  153  161  169  177  185  | 193  201  209  217  225  233  241  249
Row 2: 130  138  146  154  162  170  178  186  | 194  202  210  218  226  234  242  250
Row 3: 131  139  147  155  163  171  179  187  | 195  203  211  219  227  235  243  251
Row 4: 132  140  148  156  164  172  180  188  | 196  204  212  220  228  236  244  252
Row 5: 133  141  149  157  165  173  181  189  | 197  205  213  221  229  237  245  253
Row 6: 134  142  150  158  166  174  182  190  | 198  206  214  222  230  238  246  254
Row 7: 135  143  151  159  167  175  183  191  | 199  207  215  223  231  239  247  255
Row 8: 127  119  111  103   95   87   79   71  |  63   55   47   39   31   23   15    7
Row 9: 126  118  110  102   94   86   78   70  |  62   54   46   38   30   22   14    6
Row10: 125  117  109  101   93   85   77   69  |  61   53   45   37   29   21   13    5
Row11: 124  116  108  100   92   84   76   68  |  60   52   44   36   28   20   12    4
Row12: 123  115  107   99   91   83   75   67  |  59   51   43   35   27   19   11    3
Row13: 122  114  106   98   90   82   74   66  |  58   50   42   34   26   18   10    2
Row14: 121  113  105   97   89   81   73   65  |  57   49   41   33   25   17    9    1
Row15: 120  112  104   96   88   80   72   64  |  56   48   40   32   24   16    8    0
```

**Default center SPAD: 199** (physical center, row 7 col 15 of the left half — maps to
the upper-right quadrant junction).

**Rules for choosing ROI center:**
- Pick the SPAD that is **above and to the right** of your exact geometric center.
- This matters most for even-dimension ROIs where the center falls between SPADs.
- The optical center is stored in NVM from factory calibration; read it with
  `VL53L1_GetCalibrationData()` if using the full ST API.
- Shifting the center shifts the FOV in the **opposite** direction to the SPAD shift
  due to lens inversion.

**Pololu API:**
```cpp
sensor.setROICenter(uint8_t spadNum);   // default 199
sensor.getROICenter();                   // returns uint8_t
```

**SparkFun ULD API:**
```cpp
// opticalCenter is the SPAD number from the table above
distanceSensor.setROI(4, 4, 199);
```

---

## 6. RangeStatus Values

The `range_status` field of the `RangingData` struct (Pololu) or `getRangeStatus()`
(SparkFun ULD) indicates measurement validity.

### Pololu `RangeStatus` Enum (from VL53L1X.h)

| Code | Enum Name | Meaning |
|---|---|---|
| 0 | `RangeValid` | Valid range — use this reading |
| 1 | `SigmaFail` | High sigma (poor repeatability); target too far or low signal |
| 2 | `SignalFail` | Return signal too weak; target absent, too far, or low reflectance |
| 3 | `RangeValidMinRangeClipped` | Target below minimum detection threshold; reading clipped |
| 4 | `OutOfBoundsFail` | Phase out-of-bounds; sensor aliasing (radar wrap) or invalid zone |
| 5 | `HardwareFail` | Hardware fault |
| 6 | `RangeValidNoWrapCheckFail` | Range is valid BUT wrap-around check has not been completed — always occurs on the **first measurement** in back-to-back mode |
| 7 | `WrapTargetFail` | Wrapped target — phase mismatch between the two VCSEL periods |
| 8 | `ProcessingFail` | Internal algorithm underflow or overflow |
| 9 | `XtalkSignalFail` | Crosstalk signal failure (cover glass reflection overwhelming return) |
| 10 | `SynchronizationInt` | First interrupt when starting back-to-back ranging — not a real measurement |
| 11 | `(MergedPulse)` | Multiple targets merged into one pulse — present in full ST API but not in Pololu enum |
| 13 | `MinRangeFail` | ROI extends beyond SPAD array boundary |
| 255 | `None` | No update / sensor not started |

**SparkFun ULD `getRangeStatus()` returns a compressed subset:**
- 0 = no error
- 1 = signal fail
- 2 = sigma fail
- 7 = wrapped target

**Practical rules:**
- Only trust the distance when `range_status == 0` (RangeValid).
- Status 3 (clipped) is debatable — the distance is physically valid but may be near the minimum range floor.
- Status 6 is normal on the very first reading of every continuous session; discard it.
- Status 4 (out-of-bounds / phase fail) usually means the target is beyond the mode's reliable range, or there is cross-talk.
- Status 9 (xtalk) always means cover glass or close surface reflection is overwhelming the signal.

---

## 7. Signal Rate and Ambient Light Metrics (MCPS)

Available in `ranging_data` struct (Pololu) after every `read()` call.

| Field | Type | Units | Description |
|---|---|---|---|
| `peak_signal_count_rate_MCPS` | `float` | Mega-counts/second | Photon return rate from the target. Low values indicate weak signal. |
| `ambient_count_rate_MCPS` | `float` | Mega-counts/second | Background IR light. High values indicate bright ambient IR (sunlight). |

**SparkFun ULD equivalents (in kcps, not MCPS):**
- `getSignalPerSpad()` — average signal rate per active SPAD in kcps/SPAD
- `getAmbientPerSpad()` — ambient per SPAD in kcps/SPAD
- `getSignalRate()` — combined signal across all active SPADs in kcps
- `getAmbientRate()` — total ambient across all SPADs in kcps
- `getSpadNb()` — count of active SPADs currently enabled

**Default signal and sigma thresholds (SparkFun ULD):**
- Signal threshold: **1024 kcps** — measurements below this signal level are rejected
- Sigma threshold: **15 mm** — measurements with standard deviation above this are rejected

```cpp
// SparkFun ULD: adjust thresholds
distanceSensor.setSignalThreshold(1024);  // kcps, default
distanceSensor.setSigmaThreshold(15);      // mm sigma, default
```

---

## 8. Interrupt and Threshold Detection Modes

The GPIO1 pin is an active-LOW (by default) interrupt output that fires based on
configurable conditions. Used for autonomous low-power triggered ranging.

### Interrupt Polarity

```cpp
// SparkFun ULD
distanceSensor.setInterruptPolarityHigh();  // active HIGH
distanceSensor.setInterruptPolarityLow();   // active LOW (default)
distanceSensor.getInterruptPolarity();      // 0 = low, 1 = high

// Adafruit
vl.setIntPolarity(true);   // true = active HIGH
vl.setIntPolarity(false);  // false = active LOW (default)
```

### Distance Threshold Window Modes (SparkFun ULD)

```cpp
distanceSensor.setDistanceThreshold(uint16_t lowThresh, uint16_t hiThresh, uint8_t window);
```

| Window | Mode Name | Interrupt fires when... |
|---|---|---|
| 0 | Below | distance < lowThresh |
| 1 | Above | distance > hiThresh |
| 2 | Outside window | distance < lowThresh OR distance > hiThresh |
| 3 | Inside window | lowThresh <= distance <= hiThresh |

```cpp
// Example: fire interrupt when object is between 100mm and 300mm
distanceSensor.setDistanceThreshold(100, 300, 3);

// Clear interrupt after consuming the reading
distanceSensor.clearInterrupt();
```

Read back threshold config:
```cpp
distanceSensor.getDistanceThresholdWindow()   // returns window mode (0-3)
distanceSensor.getDistanceThresholdLow()      // returns low threshold in mm
distanceSensor.getDistanceThresholdHigh()     // returns high threshold in mm
```

### Clearing the Interrupt

The interrupt pin stays asserted until explicitly cleared. Always clear after reading.

```cpp
// Pololu — no built-in clearInterrupt; clear via register write:
sensor.writeReg(0x0086, 0x01);   // SYSTEM__INTERRUPT_CLEAR

// SparkFun ULD
distanceSensor.clearInterrupt();

// Adafruit
vl.clearInterrupt();
```

### Autonomous Low-Power Mode

For battery-powered applications, the sensor can range autonomously and assert GPIO1
only when the threshold is met, allowing the host MCU to sleep.

Flow:
1. Configure timing budget and IMP.
2. Configure distance threshold with desired window.
3. Enable interrupt.
4. Call `startRanging()`.
5. Host MCU sleeps; GPIO1 wakes it.
6. Host reads distance, clears interrupt, returns to sleep.

Power at 1 Hz ranging: approximately **65 µA average**.

---

## 9. Calibration

### Offset Calibration

Corrects for systematic distance error. The sensor reads slightly high or low from
its factory defaults based on PCB stack-up and lens variations.

**ST ULD API procedure (SparkFun ULD and Adafruit):**
1. Place a gray (17% reflectance at 940 nm) target at exactly **100 mm** from the
   sensor aperture (some ST docs use 140 mm — SparkFun guide says 100 mm).
2. Call `calibrateOffset(targetDistanceInMm)`.
3. Read back the offset with `getOffset()` (returns int16_t in mm).
4. Store the value in non-volatile storage.
5. On each boot, call `setOffset(storedValue)` after sensor initialization.

```cpp
// SparkFun ULD
distanceSensor.calibrateOffset(100);    // target at 100 mm
int16_t offset = distanceSensor.getOffset();
// store offset...

// On boot:
distanceSensor.setOffset(storedOffset);
```

**Pololu library:** Does NOT include calibration functions. Workaround: use ST
`vl53l1x-st-api-arduino` library or write the offset directly to register
`ALGO__PART_TO_PART_RANGE_OFFSET_MM` (0x001E, 16-bit signed, units of 1/4 mm).

### Crosstalk (XTalk) Calibration

Required when a cover glass or protective window is placed in front of the sensor.
Cover glass reflects laser photons back to the detector, causing "ghost" readings at
short distances and under-ranging at longer distances.

**ST ULD API procedure:**
1. First complete offset calibration.
2. Place the sensor with cover glass facing a clear target > 600 mm away (or pointing
   at a no-object zone — the calibration is for the glass reflection component).
3. Call `calibrateXTalk(targetDistanceInMm)`.
4. Read back value with `getXTalk()` (returns uint16_t in kcps).
5. Store and restore on boot with `setXTalk(storedValue)`.

```cpp
// SparkFun ULD
distanceSensor.calibrateXTalk(600);      // target distance in mm
uint16_t xtalk = distanceSensor.getXTalk();
// store xtalk...

// On boot:
distanceSensor.setXTalk(storedXtalk);
```

**Pololu library:** Does NOT include XTalk calibration. To enable xtalk compensation
via direct registers, use the ST API library instead.

### Temperature Recalibration

The VHV (variable high voltage) calibration must be refreshed if temperature shifts
more than 8°C from the last calibration temperature.

```cpp
// SparkFun ULD
distanceSensor.startTemperatureUpdate();
```

This is also called automatically after stopping/restarting ranging if the full ST
API is used.

---

## 10. Multi-Sensor XSHUT Address Remapping

All VL53L1X sensors power up at address **0x29**. To use multiple sensors on one I2C
bus, assign unique addresses using XSHUT sequencing.

**Addresses are RAM-only — they reset to 0x29 on power cycle.** Repeat this sequence
every boot.

### Procedure (N sensors)

```cpp
// Step 1: Hold ALL sensors in shutdown (XSHUT LOW)
for (int i = 0; i < N_SENSORS; i++) {
    pinMode(xshutPins[i], OUTPUT);
    digitalWrite(xshutPins[i], LOW);
}
delay(10);

// Step 2: Bring sensors up one at a time, assign unique addresses
uint8_t addresses[] = {0x30, 0x31, 0x32};  // chosen addresses (0x30–0x3F typical)
for (int i = 0; i < N_SENSORS; i++) {
    digitalWrite(xshutPins[i], HIGH);
    delay(10);  // wait for sensor boot (1.2 ms min; use 10 ms for margin)
    sensors[i].init();
    sensors[i].setAddress(addresses[i]);
}

// Step 3: All sensors are now on bus at their assigned addresses
```

**Address range:** Technically any valid 7-bit I2C address; avoid 0x29 (default),
0x00 (general call), and any address used by other devices. Range 0x30–0x3F is
conventionally used.

**Pull-up resistors:** If each sensor breakout has its own pull-up resistors enabled,
multiple sensors in parallel will create too-low combined resistance. Disable pull-ups
on all but one breakout, or use external pull-ups with only one set enabled.

---

## 11. Power Modes

| Mode | Condition | Power Consumption |
|---|---|---|
| HW Standby | XSHUT = LOW | Near 0 (only leakage) |
| SW Standby | Initialized, not ranging | ~5–6 µA (2v8 mode adds ~0.6 µA) |
| Idle (between measurements) | Continuous mode, gap between measurements | ~20 µA |
| Active ranging | Laser emitting, counting photons | ~20 mA avg; peaks to 40 mA |
| Autonomous low-power | Ranging at 1 Hz with thresholds | ~65 µA average |

### Software Standby

```cpp
sensor.stopContinuous();   // sensor enters SW standby (Pololu)
// ... wait ...
sensor.startContinuous(period_ms);   // wake up
```

### Hardware Standby

Drive XSHUT LOW. To wake, drive HIGH and wait at least 1.2 ms, then call `init()`
again because boot-up resets address assignment and all configuration registers.

```cpp
digitalWrite(XSHUT_PIN, LOW);    // enter HW standby
// ... wait ...
digitalWrite(XSHUT_PIN, HIGH);
delay(2);
sensor.init();                    // must re-init after HW standby
```

---

## 12. Library Comparison — Pololu vs Adafruit vs SparkFun

### Pololu VL53L1X (v1.3.1) — Recommended for this workspace

- **Architecture:** Standalone C++ class, no ST ULD dependency, all register
  writes inlined. Very small flash/RAM footprint.
- **Recommended for:** Arduino Uno Q projects (per `sketch.yaml` pitfalls — the
  Adafruit library copies source files into the sketch root and causes duplicate
  symbol linker errors).
- **Install name:** `VL53L1X (1.3.1)` by Pololu in Arduino Library Manager.
- **Distance modes:** Short, Medium, Long.
- **Timing budget units:** Microseconds (pass 50000 for 50 ms).
- **ROI:** Supported via `setROISize()` / `setROICenter()` (added v1.3.0).
- **Calibration:** NOT supported. No offset, no xtalk, no cover glass calibration.
- **Thresholds/interrupts:** NOT supported natively. Use direct register writes.
- **MCPS fields:** `peak_signal_count_rate_MCPS` and `ambient_count_rate_MCPS` in
  `ranging_data` struct.
- **Non-blocking read:** `read(false)` — but calling before data ready is undefined.
  Use `dataReady()` first.

```cpp
#include <VL53L1X.h>
VL53L1X sensor;

void setup() {
    Wire1.begin();
    sensor.setBus(&Wire1);
    sensor.setTimeout(500);
    if (!sensor.init()) { /* handle failure */ }
    sensor.setDistanceMode(VL53L1X::Short);
    sensor.setMeasurementTimingBudget(50000);  // 50 ms in µs
    sensor.startContinuous(50);
}

void loop() {
    uint16_t dist_mm = sensor.read();
    // sensor.ranging_data.range_status
    // sensor.ranging_data.peak_signal_count_rate_MCPS
    // sensor.ranging_data.ambient_count_rate_MCPS
}
```

### Adafruit Adafruit_VL53L1X — DO NOT USE on Arduino Uno Q

- **Architecture:** Thin wrapper over ST's full API source. The library copies
  ST C source files (`vl53l1x_*.c`) directly into the Arduino sketch build and
  causes **duplicate symbol linker errors** when combined with other libraries
  that also include the ST driver.
- **Timing budget units:** Milliseconds (pass 50 for 50 ms). Valid values: 15, 20,
  33, 50, 100, 200, 500 ms.
- **Distance modes:** Short and Long only (no Medium in this wrapper).
- **Calibration:** NOT exposed directly; the underlying ST API has it but Adafruit's
  class does not provide convenience wrappers.
- **Interrupts:** `clearInterrupt()`, `setIntPolarity()` available.
- **API methods:** `begin()`, `startRanging()`, `stopRanging()`, `dataReady()`,
  `distance()`, `clearInterrupt()`, `setTimingBudget()`, `getTimingBudget()`,
  `setIntPolarity()`.

### SparkFun SparkFun_VL53L1X (ST ULD wrapper)

- **Architecture:** Thin C++ wrapper over ST's Ultra Lite Driver (ULD). More
  featureful than Pololu but larger footprint.
- **Timing budget units:** Milliseconds.
- **Distance modes:** Short (1) and Long (2) only.
- **ROI:** `setROI(x, y, opticalCenter)` using SPAD table.
- **Calibration:** Full support — `calibrateOffset()`, `calibrateXTalk()`,
  `setOffset()`, `setXTalk()`.
- **Thresholds:** Full `setDistanceThreshold(low, high, window)` support.
- **Signal metrics:** `getSignalPerSpad()`, `getAmbientPerSpad()`, `getSignalRate()`,
  `getAmbientRate()`, `getSpadNb()` — all in kcps.
- **Temperature update:** `startTemperatureUpdate()`.
- **Note:** May also suffer from duplicate symbol issues on some platforms depending
  on how the ULD source is bundled.

---

## 13. Known Limitations and Gotchas

### Wrap-Around / Range Aliasing (Status 4 / 7)

The sensor uses dual VCSEL pulse repetition intervals to detect wrap-around. If a
target is detected at the aliased distance (modulo ~5 m), the sensor returns
`WrapTargetFail` (7) or `OutOfBoundsFail` (4). There is no software fix; the
physical range limit for Long mode is ~4 m before aliasing begins.

### First Measurement Status 6

The first measurement after `startContinuous()` will always return
`RangeValidNoWrapCheckFail` (6) because the wrap-around check requires two
completed measurements. Discard or treat as valid depending on application needs.

### Cover Glass Crosstalk (Status 9)

Any transparent barrier in front of the sensor causes `XtalkSignalFail` (9) or
grossly under-ranging if the barrier reflects enough 940 nm photons. Solution:
run XTalk calibration using the SparkFun ULD or ST API. The Pololu library has
no built-in support for this.

### Minimum Range Floor (~30–40 mm)

The sensor cannot accurately measure closer than about 30–40 mm. Objects this close
or closer return clipped readings (status 3) or incorrect values. Design mounting
geometry with at least 50 mm clearance from the nearest surface.

### ROI Size and False Positives

A large ROI (16x16) sees 27 degrees. Narrow objects or objects not centered in the
beam may partially exit the FOV at distance. Reduce ROI to reduce side-lobe
sensitivity, but also reduce overall signal strength.

### ROI Center Lens Inversion

Shifting ROI center SPAD in one direction shifts the physical FOV in the
**opposite** direction due to the converging lens geometry. If you want to look
slightly to the right, set the center to the left side of the SPAD grid.

### Non-Blocking Read Undefined Behavior (Pololu)

Calling `sensor.read(false)` before `dataReady()` returns true results in
undefined behavior — the struct may contain stale data from the previous
measurement. Always gate non-blocking reads on `dataReady()`.

### I2C Pull-Up Stacking (Multi-Sensor)

Multiple breakout boards each with onboard pull-ups in parallel lower combined
resistance well below 4.7 kΩ, causing I2C bus instability. Remove or disable
onboard pull-ups on all but one breakout, or use a single external set.

### Address Volatility (Multi-Sensor)

Reassigned I2C addresses are RAM-only. Any power cycle, XSHUT toggle, or hardware
reset restores all sensors to 0x29. XSHUT sequencing must run on every boot before
ranging begins.

### Ambient Light Sensitivity in Long Mode

Long mode is highly sensitive to sunlight and strong indoor IR sources. If
`ambient_count_rate_MCPS` is high relative to `peak_signal_count_rate_MCPS`, move
to Short mode or reduce timing budget to lower per-measurement IR accumulation.

### AVR RAM: `rangeStatusToString()`

On AVR-class boards (~2 kB RAM), calling `rangeStatusToString()` consumes 200+ bytes
of RAM. Omit it to save memory.

### Temperature Drift

Calibration degrades if temperature changes more than 8°C from the calibration point.
Call `startTemperatureUpdate()` (SparkFun ULD) if operating across large temperature
swings.

---

## 14. Full Pololu API Quick Reference

```cpp
// Setup
VL53L1X sensor;
sensor.setBus(&Wire1);                          // select I2C bus
sensor.setTimeout(500);                         // ms; 0 = no timeout
bool ok = sensor.init(true);                    // true = 2.8V I/O mode

// Address (for multi-sensor)
sensor.setAddress(0x30);
uint8_t addr = sensor.getAddress();

// Distance mode
sensor.setDistanceMode(VL53L1X::Short);         // Short, Medium, Long
VL53L1X::DistanceMode m = sensor.getDistanceMode();  // returns Short/Medium/Long/Unknown

// Timing budget (microseconds)
sensor.setMeasurementTimingBudget(50000);        // 50 ms
uint32_t tb = sensor.getMeasurementTimingBudget();

// ROI
sensor.setROISize(4, 4);                        // width, height (4-16 each)
sensor.getROISize(&w, &h);
sensor.setROICenter(199);                       // SPAD number from table
uint8_t c = sensor.getROICenter();

// Ranging
sensor.startContinuous(50);                     // period_ms (IMP); 0 = back-to-back
sensor.stopContinuous();
uint16_t dist = sensor.read();                  // blocking by default; returns mm
uint16_t dist = sensor.read(false);             // non-blocking; check dataReady() first
uint16_t dist = sensor.readSingle();            // one-shot measurement
bool ready = sensor.dataReady();

// Status / diagnostics
bool timeout = sensor.timeoutOccurred();
const char* s = VL53L1X::rangeStatusToString(sensor.ranging_data.range_status);

// Data struct (populated after each read())
sensor.ranging_data.range_mm
sensor.ranging_data.range_status                // RangeStatus enum (0-255)
sensor.ranging_data.peak_signal_count_rate_MCPS // float, Mcps
sensor.ranging_data.ambient_count_rate_MCPS     // float, Mcps
sensor.last_status                              // I2C wire status (0 = ok)

// Direct register access (for calibration / interrupt workarounds)
sensor.writeReg(0x001E, value);                 // 8-bit
sensor.writeReg16Bit(0x001E, value);            // 16-bit
sensor.writeReg32Bit(0x001E, value);            // 32-bit
sensor.readReg(0x001E);
sensor.readReg16Bit(0x001E);
sensor.readReg32Bit(0x001E);
```

---

## 15. Key Register Addresses (for direct access workarounds)

| Register Name | Address | Size | Notes |
|---|---|---|---|
| SYSTEM__INTERRUPT_CLEAR | 0x0086 | 8-bit | Write 0x01 to clear GPIO1 interrupt |
| ALGO__PART_TO_PART_RANGE_OFFSET_MM | 0x001E | 16-bit signed | Offset in units of 1/4 mm |
| ROI_CONFIG__USER_ROI_CENTRE_SPAD | — | 8-bit | Written by setROICenter() |
| ROI_CONFIG__USER_ROI_REQUESTED_GLOBAL_XY_SIZE | — | 8-bit | Written by setROISize() |

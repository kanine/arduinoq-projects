# VL53L1X Technical Parameter Reference

**Subject:** Core Configuration for Time of Flight (ToF) Sensing  
**Language:** C++ (Arduino/PlatformIO)

## 1. Timing Budget (TB)

The Timing Budget is the window of time the sensor spends emitting laser pulses and counting returning photons for a single measurement.

- **Logic:** It is a "shutter speed." A longer budget collects more photons, reducing statistical noise (jitter).
- **Trade-off:** Longer budgets provide higher precision but lower frequency (fewer readings per second).

**C++ command:**

```cpp
// Options: 20000 (20ms), 33000, 50000, 100000, 200000, 500000
sensor.setMeasurementTimingBudget(50000);
```

## 2. Distance Mode

Optimizes the internal timing and thresholds for specific physical ranges.

- **Short Mode:** Limited to ~1.3m. Best for high ambient light (indoors/bright rooms) and better close-range accuracy.
- **Long Mode:** Up to 4m. Required for long-distance sensing, but highly sensitive to infrared noise from the sun or bright lights.

**C++ command:**

```cpp
sensor.setDistanceMode(VL53L1X::Short); // or VL53L1X::Long
```

## 3. Region of Interest (ROI) Size and Center

The ROI defines which portion of the 16x16 SPAD (detector) array is active.

- **Size:** Default is 16x16 (27 deg field of view). Minimum is 4x4.
- **Center:** The grid index (0-255). The optical center is 199.
- **Logic:** Reducing ROI narrows the "beam" to avoid detecting obstacles on the side (like the edges of a spool or a narrow pipe).

**C++ command:**

```cpp
sensor.setROISize(4, 4);   // Narrowest possible focus
sensor.setROICenter(199);  // Look straight ahead
```

## 4. Inter-Measurement Period (IMP)

The total time from the start of one measurement to the start of the next.

- **Logic:** Must be $\ge$ Timing Budget. It allows the sensor to "sleep" between readings to save power.

**C++ command:**

```cpp
// Set 100ms between the start of each reading
sensor.setInterMeasurementPeriod(100);
```

## Complete C++ Implementation Example

This script applies a "High Precision Narrow Beam" configuration, ideal for tracking small or moving targets at close range.

```cpp
#include <Wire.h>
#include <VL53L1X.h>

VL53L1X sensor;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000); // Use 400kHz I2C for faster data transfer

  sensor.setTimeout(500);
  if (!sensor.init()) {
    Serial.println("Failed to detect VL53L1X!");
    while (1);
  }

  /* CONFIGURATION */

  // 1. Use Short Mode for better accuracy under 1.3 meters
  sensor.setDistanceMode(VL53L1X::Short);

  // 2. Set Timing Budget to 50ms (Balanced precision/speed)
  // Input is in microseconds
  sensor.setMeasurementTimingBudget(50000);

  // 3. Set ROI to 4x4 to narrow the Field of View
  // This helps ignore background noise or side-reflections
  sensor.setROISize(4, 4);
  sensor.setROICenter(199);

  // 4. Start continuous readings every 50ms
  sensor.startContinuous(50);
}

void loop() {
  // read() returns distance in mm
  uint16_t distance = sensor.read();

  // Optional: Check signal rate to see if target is too "clear" or dark
  // float signalRate = sensor.getSignalRateMCPS();

  if (sensor.timeoutOccurred()) {
    Serial.println("TIMEOUT");
  } else {
    Serial.print("Range: ");
    Serial.print(distance);
    Serial.println(" mm");
  }
}
```

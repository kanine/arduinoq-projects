# FilamentMonitor Implementation Plan (Arduino Uno Q 2025)

## 1. Configuration File (`config.json`)
Store this in your project root. The Python application will parse this to set the scale for the progress bar.

```json
{
  "app_name": "filamentmonitor",
  "version": "1.0.0",
  "measurements": {
    "startMeasure": 220,
    "endMeasure": 350
  },
  "metadata": {
    "unit": "mm",
    "description": "Progress tracking from 220 to 350"
  }
}
```

## 2. Core Logic (Python Component)
The Python backend will read the sensor data from the Arduino Uno Q and calculate the percentage based on the new range (`350 - 220 = 130`).

Mathematical formula:

$$
\text{Percent Remaining} = \left( 1 - \frac{current - startMeasure}{endMeasure - startMeasure} \right) \times 100
$$

Note: This formula assumes `220` is "Full" (100%) and `350` is "Empty" (0%).

## 3. Web Front-End Requirements

### A. Visual Progress Bar
Type: Linear horizontal bar.

Dynamic Styling: The width of the inner bar should be bound to the calculated percentage.

Color Transition: (Optional) Green > 50%, Yellow 20-50%, Red < 20%.

### B. High-Visibility Label
Font Style: Bold, Sans-Serif.

Placement: Centered above or inside the progress bar.

Format: `[Percentage]% Remaining` (e.g., `85% Remaining`).

# Sensor Reading Processing Spec

## Source

VL53L1X Time-of-Flight sensor on Arduino Uno Q (`uno1-tof`), polling at 480 polls/minute in 10-second batches (~77 readings/batch).

---

## Observed Noise Profile (static spool baseline)

| Stat | Value |
|---|---|
| Sample count | 1,750 readings |
| Mean | 65.43 mm |
| Std deviation | 0.92 mm |
| Min | 61 mm |
| Max | 68 mm |
| Dominant values | 65–66 mm (99.5% of readings) |

The sensor is quantisation-limited. Nearly all readings fall within a 4 mm band; isolated outliers (61, 68) occur at <0.1% frequency.

---

## Current Approach — Trimmed Mean (10% each side)

The current implementation drops the top 10% and bottom 10% of readings per batch before averaging.

**Problem 1 — Overkill for this noise profile**

Only ~2% of readings are genuinely outlier material. Trimming 10% each side discards valid readings (e.g. legitimate 64s and 67s) and biases the result toward the cluster centre.

**Problem 2 — Actively harmful during production**

When the spool is winding or unwinding, readings trend monotonically. In a trending dataset the highest readings in a window are the most recent and most predictive of direction. Trimming the top 10% during unwinding (distance increasing) clips the leading edge of the trend — introducing systematic lag and underestimating the rate of change.

---

## Recommended Approach

### Per-batch reduction: use the median

Replace the trimmed mean with the **median** of each batch.

- Immune to the rare 61/68 spikes without discarding any valid readings
- Retains the true centre of the distribution on a static spool
- Does not clip the trend direction during production
- Simpler to reason about and audit

### End prediction: linear regression over windowed medians

At 480 ppm with ±1 mm noise, the trend line across windowed medians will be very clean.

1. Accumulate the median value from each 10-second window.
2. Fit a linear regression over the last N windows (tune N to balance responsiveness vs. smoothness — start with 6–10 windows / 1–2 minutes of data).
3. Extrapolate the fitted line to `core_radius` to predict runout time.

**Why this works well:**

- High cadence means the slope estimate stabilises within seconds of a production speed change.
- Short extrapolation distance near end-of-spool means the prediction tightens as it matters most.
- The main source of prediction error will be production speed changes (acceleration/deceleration), not sensor noise.

---

## Summary of Changes

| | Current | Recommended |
|---|---|---|
| Per-batch reduction | Trimmed mean (±10%) | Median |
| Outlier rejection | Implicit via trim | Inherent in median |
| Trend preservation | Compromised | Preserved |
| End prediction | — | Linear regression on windowed medians |

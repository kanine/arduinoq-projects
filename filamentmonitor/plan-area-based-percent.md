# Plan: Area-Based Filament Percentage Calculation

## Context

The current `calculate_percent()` uses a linear formula — it assumes filament depletes proportionally to the sensor distance change. This is physically wrong: filament wraps around a circular spool, so the amount of material is proportional to the **cross-sectional area** (πr²), not the radius. The "half-full trap": when the sensor reads halfway between startMeasure and endMeasure, only ~39% of filament actually remains, not 50%.

Real spools have a plastic core that occupies dead area at the center. That must be subtracted from both current and total area.

Correct formula (from `thepercentremainingproblem.md`):
```
percent = (r_current² - r_core²) / (R_full² - r_core²) × 100
```

## Geometry

- Sensor distance **increases** as filament depletes.
- `startMeasure` (220mm) = sensor reading when spool is full.
- `endMeasure` is **derived**, not configured: `startMeasure + (fullRadius - coreRadius)` = 220 + (200 - 80) = **340mm**.
- As sensor goes 220 → 340, physical radius goes 200mm → 80mm (linear mapping).

Derivation of `r_current`:
```
frac = (endMeasure - distance) / (endMeasure - startMeasure)   # 1.0=full, 0.0=empty
r_current = coreRadius + (fullRadius - coreRadius) * frac
```

Spot-check:
| Sensor distance | frac | r_current | % remaining |
|---|---|---|---|
| 220 (full) | 1.0 | 200mm | 100% |
| 280 (midpoint) | 0.5 | 140mm | ~39% |
| 340 (empty) | 0.0 | 80mm | 0% |

## Files Changed

- `config.json` — removed `endMeasure` (now derived), added `spool.fullRadius` and `spool.coreRadius`
- `python/main.py` — derives `END_MEASURE`, replaces linear formula with area-based one

No changes to: `sketch/`, `assets/`.

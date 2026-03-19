Because you are winding filament around a circle, the amount of material is not just a straight-line measurement. It is an area problem. As the spool gets thicker, each wrap uses significantly more filament than the one before it.

## The Math: Area vs. Radius
To find the percentage remaining, we do not look only at the radius (`r`). We look at the cross-sectional area of the filament ring. Since the area of a circle is `A = pi r^2`, the relationship between the distance from the core and the amount of material is quadratic, not linear.

If we assume the "empty" state starts at `r = 0` (the very center) and the "full" state is `R = 250 mm`, here is how to calculate the percentage of filament remaining.

### 1. Calculate Total Area (Full)
$$
A_{total} = \pi \times 250^2
$$

### 2. Calculate Current Area
$$
A_{current} = \pi \times r_{current}^2
$$

### 3. Find the Percentage
$$
\text{Percentage} = \left( \frac{r_{current}^2}{R_{full}^2} \right) \times 100
$$

## Why This Matters: The "Half-Full" Trap
If your measurement shows the filament is at `125 mm` (exactly half the distance to the edge), you actually only have `25%` of your filament left, not `50%`.

| Distance from Core (mm) | Percentage of Material Remaining |
| --- | --- |
| 250 mm | 100% |
| 216 mm | 75% |
| 177 mm | 50% (the actual halfway point) |
| 125 mm | 25% |
| 0 mm | 0% |

Note: In the real world, most spools have a physical plastic core (for example, a `50 mm` center). If your "empty" measurement is actually `50 mm` rather than `0 mm`, the formula changes slightly because you have to subtract the hole in the middle from your area calculations.

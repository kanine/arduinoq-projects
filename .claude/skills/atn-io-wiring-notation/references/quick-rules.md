# ATN-IO v3 Quick Rules

## Minimum Structure

```text
ATN-IO v3
Project: <description>

[BOARD]
[WIRING]
```

Only `[BOARD]` and `[WIRING]` are mandatory, but `[COMPONENTS]` is strongly recommended.

## Section Rules

- `[BOARD]`: `KEY = VALUE`
- `[INPUTS]`: `SIGNAL -> PIN`
- `[OUTPUTS]`: `SIGNAL -> PIN`
- `[COMPONENTS]`: `REF = DESCRIPTION`
- `[WIRING]`: `NODE -> NODE -> NODE ...`
- `[POWER]`: `RAIL -> VOLTAGE`
- `[NOTES]`: `# free-form notes`

## Separation Rules

- `[INPUTS]` and `[OUTPUTS]` describe logical mapping only.
- `[WIRING]` describes the physical electrical path.
- Power and ground connections belong in `[WIRING]`, not in `[INPUTS]` or `[OUTPUTS]`.

## Common Node Types

- Board digital pin: `D8`
- Board analog pin: `A0`
- Component terminal: `SONIC1.ECHO`
- IC pin number: `U1.PIN14`
- Bare passive component: `R1`
- Rail: `3.3V`, `5V`, `GND`

## Terminal Naming

Prefer consistent names:

- `.VCC` / `.V+`
- `.GND` / `.V-`
- `.A` / `.K`
- `.TRIG` / `.ECHO`
- `.IN` / `.OUT`
- `.NO` / `.NC` / `.COM`
- `.CLK`, `.DATA`, `.LATCH`
- `.PIN<n>` for ICs when no clearer alias exists

## Validation Checklist

- Header starts with `ATN-IO v3` and `Project:`
- Section order is correct
- Every `REF` in `[WIRING]` exists in `[COMPONENTS]`
- Every current path has a logical return to `GND` or a named rail
- Voltage-sensitive inputs include level-shifting notes where needed
- Reserved pins and special behavior are documented in `[NOTES]`
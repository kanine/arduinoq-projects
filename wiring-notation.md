# ATN-IO v3 – Arduino Text Notation

---

## Purpose

ATN-IO is a human-readable and machine-parseable text format for documenting Arduino and embedded wiring projects.

It separates:

- **Logical mapping** (what signal goes to which pin)
- **Physical wiring** (actual electrical connection path)
- **Components** (resistors, LEDs, sensors, modules)
- **Power rails**

It is designed to be:

- Easy to read and write
- Git-friendly (diff-able, mergeable)
- Deterministic to parse
- Suitable for automated code and BOM generation

---

## File Header

Every ATN-IO v3 file must begin with two header lines before any section:

```
ATN-IO v3
Project: <short project description>
```

Example:
```
ATN-IO v3
Project: HC-SR04 Ultrasonic Meter – Mega 2560
```

---

## Core Principles

1. Logical mapping and physical wiring are **always kept separate**.
2. One instruction per line.
3. `->` means a direct electrical connection in series. Multiple arrows chain nodes.
4. Comments begin with `#` and may appear on their own line or inline.
5. Section headers are `[UPPERCASE]` and appear **at most once** each.
6. Always be explicit about power and ground.
7. Every current path in `[WIRING]` must have a logical return to GND or a rail.

---

## File Structure

Sections must appear in this order:

```
ATN-IO v3
Project: <description>

[BOARD]
[INPUTS]       (optional)
[OUTPUTS]      (optional)
[COMPONENTS]   (optional but recommended)
[WIRING]       (mandatory)
[POWER]        (optional)
[NOTES]        (optional)
```

Only `[BOARD]` and `[WIRING]` are required.

---

## Section Definitions

---

### [BOARD]

Declares the controller and its electrical characteristics.

Format:
```
KEY = VALUE
```

Supported keys:

| Key | Description | Example |
|---|---|---|
| `TYPE` | Board model | `Arduino Mega 2560` |
| `LOGIC` | Logic voltage level | `5V` or `3.3V` |
| `MCU` | (Optional) Microcontroller chip | `ATmega2560` |

Example:
```
[BOARD]
TYPE  = Arduino Mega 2560
LOGIC = 5V
MCU   = ATmega2560
```

---

### [INPUTS]

Maps logical input signal names to board pins, **from the Arduino's perspective**.

Format:
```
SIGNAL_NAME -> PIN
```

Rules:
- One signal per line.
- This is **logical mapping only** — it does NOT describe the full electrical path.
- The full path (sensor power, pull-up/pull-down resistors, etc.) belongs in `[WIRING]`.
- For bidirectional signals (e.g. I2C SDA), use `[INPUTS]` and add a `# bidirectional` comment.

Example:
```
[INPUTS]
ECHO   -> D7       # HC-SR04 echo return
IR1    -> D2
SDA    -> D20      # bidirectional (I2C)
```

---

### [OUTPUTS]

Maps logical output signal names to board pins, **from the Arduino's perspective**.

Format:
```
SIGNAL_NAME -> PIN
```

Rules:
- One signal per line.
- Logical mapping only — physical path belongs in `[WIRING]`.

Example:
```
[OUTPUTS]
TRIG   -> D6
LED1   -> D13
RELAY1 -> D8
DATA   -> D8
LATCH  -> D9
CLK    -> D10
```

---

### [COMPONENTS]

Lists every physical part used in the build, one per line.

Format:
```
REF = DESCRIPTION
```

Rules:
- `REF` must match exactly what is used as a node identifier in `[WIRING]`.
- Include value/model for passive components.
- Use comments for brief clarification of role.

Example:
```
[COMPONENTS]
R1     = 220R              # segment A current limit
R2     = 220R              # segment B current limit
LED1   = LED, RED, 5mm
U1     = 74HC595           # 8-bit shift register
DSP    = 5641AS            # 4-digit 7-segment, common cathode
RELAY1 = SRD-05VDC-SL-C   # 5V relay module
SONIC1 = HC-SR04           # ultrasonic distance sensor
```

This section supports:
- Human documentation
- Automated BOM generation
- Parser validation (undefined REFs become warnings)

---

### [WIRING] (Mandatory)

Defines the **actual physical electrical path** of every connection.

Format:
```
NODE -> NODE -> NODE ...
```

Each `->` is a wire joining two points in series. Chains of three or more nodes represent a series path through passive components (e.g. resistors).

#### Node Types

| Node type | Syntax | Example |
|---|---|---|
| Board digital pin | `D<n>` | `D13`, `D2` |
| Board analog pin | `A<n>` | `A0`, `A3` |
| Component terminal | `REF.TERMINAL` | `LED1.A`, `R1.1` |
| IC pin by number | `REF.PIN<n>` | `U1.PIN14`, `U1.PIN15` |
| Bare component (passive passthrough) | `REF` | `R1` (inline resistor) |
| Power rail | as declared | `5V`, `3.3V`, `GND`, `24V` |

#### Terminal Naming Conventions

Use these standard terminal suffixes consistently:

| Terminal | Meaning | Used for |
|---|---|---|
| `.A` | Anode | Diodes, LEDs |
| `.K` | Cathode | Diodes, LEDs |
| `.VCC` / `.V+` | Positive supply | Modules, sensors |
| `.GND` / `.V-` | Ground | Modules, sensors |
| `.TRIG` | Trigger input | HC-SR04 |
| `.ECHO` | Echo output | HC-SR04 |
| `.IN` | Signal input | Relays, buffers |
| `.OUT` | Signal output | Buffers, sensors |
| `.NO` | Normally Open | Relay contacts |
| `.NC` | Normally Closed | Relay contacts |
| `.COM` | Common | Relay contacts |
| `.CLK` | Clock | SPI, shift registers |
| `.DATA` / `.DS` | Data | Shift registers |
| `.LATCH` / `.STCP` | Latch/strobe | Shift registers |
| `.PIN<n>` | Physical IC pin number | ICs (74HC595, etc.) |
| `.BROWN` / `.BLACK` / `.BLUE` | Wire colour | NPN proximity sensors |

> For ICs with a standard pinout, prefer named terminals (`.DS`, `.SHCP`) when the meaning is clear. Use `.PIN<n>` when no widely known alias exists.

#### Passive Component Shorthand

A bare `REF` with no terminal suffix means the component is an **inline passive passthrough** (both ends connected in series). This is valid only for two-terminal passives like resistors.

```
# Equivalent forms:
D13 -> R1 -> LED1.A     # R1 is an inline resistor (shorthand)
D13 -> R1.1             # explicit pin 1 side
R1.2 -> LED1.A          # explicit pin 2 side
```

Use the shorthand form for clarity where the direction is obvious.

#### Parallel / Shared Rails

When multiple components share a power or ground rail, list each connection on its own line.

```
# Each component gets its own rail connection line
5V  -> U1.PIN16
5V  -> U1.PIN10
5V  -> SONIC1.VCC
GND -> U1.PIN8
GND -> U1.PIN13
GND -> SONIC1.GND
```

#### Grouping with Comments

Use `#` comment lines as visual section dividers inside `[WIRING]` for readability:

```
[WIRING]
# ── Power ────────────────────────────────────────────────────
5V  -> U1.PIN16
GND -> U1.PIN8

# ── Control lines ────────────────────────────────────────────
D8  -> U1.PIN14    # DATA
D10 -> U1.PIN11    # CLK
D9  -> U1.PIN12    # LATCH
```

---

### [POWER]

Declares named power rails or aliases used in the project. Use this to clarify non-obvious rail names or document external supply sources.

Format:
```
RAIL_NAME -> VOLTAGE
```

Example:
```
[POWER]
5V          -> 5V        # Arduino onboard regulator
SENSORS_V+  -> 24V       # External 24V supply for NPN sensors
COMMON_GND  -> GND
```

> If your project only uses the standard `5V` and `GND` Arduino pins, this section can be omitted. Include it when using external supplies or when rail names could be ambiguous.

---

### [NOTES]

Free-form human documentation. Ignored by parsers. Use it for:

- Timing constraints
- Software configuration notes
- Known caveats or errata
- Assembly tips

```
[NOTES]
# Logic level: all peripherals are 5V-compatible with Mega 2560
# TRIG pulse must be >= 10 µs HIGH
# Distance formula: mm = (echo_us * 343) / 2000
# Segment bit order in shift register: bit0=A, bit1=B, ..., bit7=DP
```

---

## Examples

---

### Example 1 – Simple LED Blink

```
ATN-IO v3
Project: Arduino Mega Blink

[BOARD]
TYPE  = Arduino Mega 2560
LOGIC = 5V

[OUTPUTS]
LED1 -> D13

[COMPONENTS]
R1   = 220R
LED1 = LED, RED, 5mm

[WIRING]
D13 -> R1 -> LED1.A
LED1.K -> GND
```

---

### Example 2 – NPN Proximity Sensor (24V)

```
ATN-IO v3
Project: NPN Sensor Input

[BOARD]
TYPE  = Arduino Mega 2560
LOGIC = 5V

[INPUTS]
IR1 -> D2

[COMPONENTS]
IR1 = NPN_SENSOR, 24V, PNP-blocked output

[WIRING]
24V -> IR1.BROWN
IR1.BLACK -> D2
IR1.BLUE  -> GND

[POWER]
SENSORS_V+ -> 24V
```

---

### Example 3 – HC-SR04 + 74HC595 + 4-Digit Display

```
ATN-IO v3
Project: Ultrasonic Distance Meter – HC-SR04 + 5641AS + 74HC595 + Mega 2560

[BOARD]
TYPE  = Arduino Mega 2560
LOGIC = 5V

[INPUTS]
ECHO -> D7

[OUTPUTS]
TRIG  -> D6
DATA  -> D8
CLK   -> D10
LATCH -> D9
DIG1  -> D2
DIG2  -> D3
DIG3  -> D4
DIG4  -> D5

[COMPONENTS]
R1     = 220R    # segment A
R2     = 220R    # segment B
R3     = 220R    # segment C
R4     = 220R    # segment D
R5     = 220R    # segment E
R6     = 220R    # segment F
R7     = 220R    # segment G
R8     = 220R    # segment DP
U1     = 74HC595
DSP    = 5641AS, 4-digit 7-segment, common cathode
SONIC1 = HC-SR04

[WIRING]
# ── 74HC595 power ─────────────────────────────────────────────
5V  -> U1.PIN16            # VCC
GND -> U1.PIN8             # GND
5V  -> U1.PIN10            # MR/SRCLR – must be HIGH (no reset)
GND -> U1.PIN13            # OE       – must be LOW  (outputs enabled)

# ── Arduino -> 74HC595 control lines ──────────────────────────
D8  -> U1.PIN14            # DS   / DATA
D10 -> U1.PIN11            # SHCP / CLK
D9  -> U1.PIN12            # STCP / LATCH

# ── 74HC595 outputs -> resistors -> display segments ──────────
U1.PIN15 -> R1 -> DSP.PIN11    # Q0 -> A
U1.PIN1  -> R2 -> DSP.PIN7     # Q1 -> B
U1.PIN2  -> R3 -> DSP.PIN4     # Q2 -> C
U1.PIN3  -> R4 -> DSP.PIN2     # Q3 -> D
U1.PIN4  -> R5 -> DSP.PIN1     # Q4 -> E
U1.PIN5  -> R6 -> DSP.PIN10    # Q5 -> F
U1.PIN6  -> R7 -> DSP.PIN5     # Q6 -> G
U1.PIN7  -> R8 -> DSP.PIN3     # Q7 -> DP

# ── Digit select (active LOW) ─────────────────────────────────
D2 -> DSP.PIN12                # DIG1 – leftmost
D3 -> DSP.PIN9                 # DIG2
D4 -> DSP.PIN8                 # DIG3
D5 -> DSP.PIN6                 # DIG4 – rightmost

# ── HC-SR04 ───────────────────────────────────────────────────
5V         -> SONIC1.VCC
GND        -> SONIC1.GND
D6         -> SONIC1.TRIG
SONIC1.ECHO -> D7

[NOTES]
# Segment bit order in shift register byte: bit0=A … bit7=DP
# Display common-cathode: digit pin LOW = digit ON, HIGH = digit OFF
# TRIG pulse: 10 µs HIGH; ECHO pulse width proportional to distance
# Distance formula: mm = (echo_us * 343) / 2000
```

---

## Design Rules

1. `[INPUTS]` and `[OUTPUTS]` must contain **only** `NAME -> PIN`. No chains, no power, no resistors.
2. Every component named in `[WIRING]` must be declared in `[COMPONENTS]`.
3. Every current path in `[WIRING]` must end at `GND` or a named power rail.
4. Do not put the same connection on multiple lines unless it is intentional (e.g. shared rail).
5. Use `.PIN<n>` notation for ICs; use named terminals (`.A`, `.K`, `.VCC`) for discrete components and modules.
6. Be explicit about polarity — never leave a diode, relay, or electrolytic capacitor without polarity notation.
7. Keep inline comments short; move longer explanations to `[NOTES]`.

---

## Validation Checklist

Before committing a wiring file, verify:

- [ ] File starts with `ATN-IO v3` and `Project:` header
- [ ] `[BOARD]` declares `TYPE` and `LOGIC`
- [ ] Every REF in `[WIRING]` appears in `[COMPONENTS]`
- [ ] Every pin number in `[INPUTS]`/`[OUTPUTS]` is a valid pin for the declared board
- [ ] Every current path terminates at `GND` or a power rail
- [ ] IC enable/reset/OE control pins are explicitly wired (not left floating)
- [ ] No floating inputs on critical pins (pull-up or pull-down documented)

---

## Recommended Naming Conventions

| Type | Convention | Examples |
|---|---|---|
| Resistors | `R<n>` | `R1`, `R2` |
| Capacitors | `C<n>` | `C1`, `C2` |
| LEDs | `LED<n>` | `LED1`, `LED2` |
| Integrated circuits | `U<n>` | `U1`, `U2` |
| Displays | `DSP` or `DSP<n>` | `DSP`, `DSP1` |
| Relays | `RELAY<n>` | `RELAY1` |
| Ultrasonic sensors | `SONIC<n>` | `SONIC1` |
| IR / proximity sensors | `IR<n>` | `IR1`, `IR2` |
| Generic modules | descriptive prefix + `<n>` | `BT1` (Bluetooth), `LCD1` |
| Power nets | uppercase voltage | `5V`, `3.3V`, `24V`, `GND` |

---

## Why This Format Works

It mirrors industrial wiring practice:

| Layer | ATN-IO section | Industrial equivalent |
|---|---|---|
| Control intent | `[INPUTS]` / `[OUTPUTS]` | I/O list |
| Bill of materials | `[COMPONENTS]` | BOM |
| Electrical connections | `[WIRING]` | Wiring diagram / schematic netlist |
| Supply architecture | `[POWER]` | Power distribution drawing |
| Engineering notes | `[NOTES]` | Revision comments / errata |

This makes ATN-IO files:
- Understandable by humans without a schematic tool
- Parseable by scripts for validation or code generation
- Safe to expand to larger, multi-board systems

---

## Summary

ATN-IO v3 is:
- **Readable** – plain text, no special tooling needed
- **Deterministic** – one way to express each connection type
- **Scalable** – works for a single LED or a 50-component panel
- **Industrial-friendly** – maps naturally to I/O lists and wiring diagrams
- **AI-friendly** – structured enough for automated parsing and generation

It cleanly separates logic from wiring and keeps every electrical path explicit and traceable.
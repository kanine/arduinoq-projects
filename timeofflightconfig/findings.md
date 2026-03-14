# Time of Flight Config — Findings

## Session 1: 2026-03-14

### Outcome

Address reassignment confirmed working.

After a clean board reboot, the sketch successfully:
- detected the sensor at `0x29` on `Wire1`
- initialised the VL53L1X
- reassigned the address to `0x30`
- confirmed I2C ACK at `0x30`

LED result: **solid red** (STATE_OK).

---

### What Was Learned

#### 1. LED_BUILTIN is active low

`LOW` = ON, `HIGH` = OFF. The initial sketch had this inverted, so the LED appeared dead.
Confirmed from `copy-of-blink-led` example sketch.

#### 2. XSHUT must not be driven if not wired

The first version of the sketch unconditionally pulled `XSHUT_PIN` (D3) LOW then HIGH on
every startup. With XSHUT unwired, this had no effect on the sensor — but it still
caused a no-ACK fault because the probe was running before the bus was fully stable.

Resolution: added `USE_XSHUT` compile-time flag (default `false`). The XSHUT power-cycle
sequence is skipped entirely when the flag is `false`.

#### 3. I2C bus / sensor state can survive app restarts

When the app was first deployed (before the reboot), the sensor was not responding at
`0x29` even with `USE_XSHUT false`. The Qwiic bus was likely left in a bad state from
earlier Phase 3 experiments on `predictivesensorcontroller`.

A full board reboot (`ssh uno1 sudo reboot`) cleared the state and the sensor was
immediately found on the next app start.

This matches the pattern documented in
`predictivesensorcontroller/phase3-attempt1-issues.md`:
> rebooting uno1 sometimes restored normal Phase 2 operation

#### 4. Address reassignment works without XSHUT

With `USE_XSHUT false`, the sensor sat at `0x29` from board power-on. The sketch:
1. probed `0x29` — ACK received
2. called `sensor.init()`
3. called `sensor.setAddress(0x30)`
4. probed `0x30` — ACK received

This confirms the Pololu VL53L1X `setAddress()` call works correctly on this board
without needing an XSHUT-controlled power cycle.

---

### Current State

| Item | State |
|---|---|
| Sensor comms at `0x29` | Confirmed working |
| Address reassignment to `0x30` | Confirmed working |
| XSHUT wiring (D3) | Not yet connected |
| `USE_XSHUT` flag | `false` |

---

## Session 2: 2026-03-14 (XSHUT wired)

### Outcome

Full XSHUT power-cycle + address reassignment confirmed working.

XSHUT → D3 wired and verified with a multimeter continuity test. `USE_XSHUT` set to
`true`. On the next app start the sketch ran the full sequence:

1. D3 pulled LOW → sensor powered off (10 ms)
2. D3 pulled HIGH → sensor booted at `0x29` (2 ms)
3. Probed `0x29` → ACK received
4. `sensor.init()` → success
5. `sensor.setAddress(0x30)` called
6. Probed `0x30` → ACK received

LED result: **solid red** (STATE_OK).

### What Was Learned

#### XSHUT control via D3 works correctly

The full XSHUT power-cycle sequence behaves as expected. Pulling D3 LOW powers off the
sensor; pulling HIGH boots it cleanly at `0x29`. Address reassignment then succeeds.

This is the exact sequence needed for two-sensor bring-up in Phase 3 of
`predictivesensorcontroller`.

---

### Current State

| Item | State |
|---|---|
| Sensor comms at `0x29` | Confirmed working |
| Address reassignment to `0x30` | Confirmed working |
| XSHUT wiring (D3) | Connected, continuity verified |
| `USE_XSHUT` flag | `true` |

---

### Next Step

Wire second sensor XSHUT → D4 and extend the sketch to handle two sensors.

---

## Session 3: 2026-03-14 (two-sensor)

### Outcome

Full two-sensor XSHUT sequencing confirmed working.

Both sensors wired:
- Sensor 1 XSHUT → D3 (continuity confirmed)
- Sensor 2 XSHUT → D4 (continuity confirmed, wired with power removed)

Sketch extended to handle sequential bring-up of both sensors. On app start:

1. D3 LOW, D4 LOW — both sensors off
2. D3 HIGH — sensor 1 boots at `0x29`, init OK, reassigned to `0x30`
3. D4 HIGH — sensor 2 boots at `0x29` (free now sensor 1 is at `0x30`), init OK, reassigned to `0x31`

LED result: **solid red** (STATE_OK).

### What Was Learned

#### 4-blink intermediate result was informative

With D4 unwired (sensor 2 XSHUT floating/low), the sketch correctly reached sensor 1
success then faulted on sensor 2 with 4 blinks (no ACK at `0x29`). This confirmed
sensor 1 sequencing was working before sensor 2 was connected.

#### Power must be removed before wiring XSHUT

Wiring was done with power disconnected to avoid risk of the MCU driving D4 LOW into
an unprotected pin.

#### Sequential bring-up works as designed

Because sensor 1 is moved to `0x30` before sensor 2 is released, the `0x29` address
is free when sensor 2 boots. No collision. The pattern is clean and repeatable.

---

### Final State

| Item | State |
|---|---|
| Sensor 1 XSHUT → D3 | Wired, continuity confirmed |
| Sensor 2 XSHUT → D4 | Wired, continuity confirmed |
| Sensor 1 address | `0x30` ✓ |
| Sensor 2 address | `0x31` ✓ |
| Full two-sensor XSHUT sequence | Confirmed working |

---

### Next Step

Hardware checkpoint complete. The two-sensor XSHUT bring-up pattern is proven and
ready to be integrated into `predictivesensorcontroller` Phase 3.

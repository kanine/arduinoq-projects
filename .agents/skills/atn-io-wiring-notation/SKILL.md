---
name: atn-io-wiring-notation
description: Use this skill when creating, editing, reviewing, or validating ATN-IO v3 wiring documents for Arduino and embedded projects. Apply it for requests involving wiring notation files, logical I/O maps, component lists, power rails, or translating prose wiring instructions into ATN-IO.
---

# ATN-IO Wiring Notation

Use this skill when the task is to document wiring in a structured markdown file rather than describe it informally.

## Trigger Guidance

Use this skill when the user asks to:
- create a `*-wiring.md` file for an app or hardware project
- convert README wiring notes into ATN-IO v3 format
- validate or fix an existing ATN-IO wiring file
- separate logical pin mapping from physical wiring paths

Do not use this skill for:
- general code changes unrelated to wiring documentation
- schematic capture in external CAD tools
- runtime debugging unless the result should be written back as ATN-IO

## Workflow

1. Identify the board, logic voltage, MCU, and any voltage-level constraints from the repo context.
2. Extract logical signals only into `[INPUTS]` and `[OUTPUTS]` using `NAME -> PIN` format.
3. List every referenced device, module, and passive component in `[COMPONENTS]`.
4. Write the actual electrical paths in `[WIRING]`, one connection path per line, with explicit power and ground.
5. Add `[POWER]` only when named rails or external supplies need clarification.
6. Add `[NOTES]` for caveats such as level shifting, active-low behavior, reserved pins, or timing requirements.
7. Validate the file against the quick rules before finalizing.

## Output Rules

- Start every file with:

```text
ATN-IO v3
Project: <short description>
```

- Keep section order fixed: `[BOARD]`, `[INPUTS]`, `[OUTPUTS]`, `[COMPONENTS]`, `[WIRING]`, `[POWER]`, `[NOTES]`.
- Keep `[INPUTS]` and `[OUTPUTS]` to logical mapping only.
- Put physical paths, rail connections, and series components only in `[WIRING]`.
- Ensure every component reference used in `[WIRING]` is declared in `[COMPONENTS]`.
- Prefer standard terminal names such as `.VCC`, `.GND`, `.TRIG`, `.ECHO`, `.A`, `.K`, `.IN`, `.OUT`, or module-specific labels such as `.S` when that is the actual silkscreen label.
- For app-local documentation, prefer a standalone file named `<app-name>-wiring.md` unless the user explicitly wants the wiring embedded in a README.

## References

- Quick rules: [references/quick-rules.md](references/quick-rules.md)
- Full specification: [../../../wiring-notation.md](../../../wiring-notation.md)
- Example: [../../../sonic-sensor/sonic-sensor-wiring.md](../../../sonic-sensor/sonic-sensor-wiring.md)
- Example: [../../../predictivesensorcontroller/tof-single-sensor-wiring.md](../../../predictivesensorcontroller/tof-single-sensor-wiring.md)
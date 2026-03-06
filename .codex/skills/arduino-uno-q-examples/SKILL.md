---
name: arduino-uno-q-examples
description: Use this skill when a task involves Arduino UNO Q App Lab example applications, including identifying matching official examples, adapting patterns from local example projects, and handling the fact that this repository contains only a selected subset of official examples.
---

# Arduino UNO Q Example Applications

## Purpose

Use official Arduino App Lab examples as implementation patterns for UNO Q apps, while prioritizing examples already present in this repository.

## Core Rule: Local Subset First

- Treat top-level folders containing `app.yaml` as local example/project candidates.
- Assume this repository contains only a subset of the official examples catalog.
- Before designing a new structure, inspect local projects and reuse the closest pattern.
- If no local project is close enough, consult the official examples catalog in `references/examples-catalog.md` and then adapt from the upstream example source.

## Discovery Workflow

1. Identify available local apps:
   - `find . -maxdepth 2 -name app.yaml`
2. Inspect likely candidates:
   - `sed -n '1,120p' <project>/app.yaml`
   - inspect `<project>/python/main.py`, `<project>/sketch/sketch.ino`, and `assets/` if present.
3. Match by capability:
   - LED matrix behavior
   - web UI behavior
   - sensor input
   - camera/audio/ML pipeline
   - cloud integration
4. Reuse nearest pattern and adjust minimally for the requested task.

## Local vs Official Resolution

- If a local project exists for the requested capability, treat it as the primary pattern source.
- If not, select the nearest official example category from `references/examples-catalog.md` and state that it is an upstream reference not currently cloned here.
- Keep naming and structure compatible with App Lab conventions:
  - `app.yaml`
  - `python/main.py`
  - `sketch/sketch.ino`
  - optional `assets/`

## Known Local Projects in This Repository

Current project-level app folders include:
- `alphabetmatrix`
- `alphabetmatrixadvanced`
- `copy-of-blink-led`
- `copy-of-led-matrix-painter`
- `sample-blink-with-ui`
- `sonic-sensor`

Do not assume these represent the full Arduino examples catalog.

## Output Expectations

When asked to build or modify an example-based app:

1. State which local project pattern you are reusing.
2. If no local pattern matches, state which official example family you are borrowing from.
3. Keep changes aligned with UNO Q/App Lab architecture and `arduino-app-cli` lifecycle commands.

## References

- Official examples tutorial and example families are summarized in `references/examples-catalog.md`.

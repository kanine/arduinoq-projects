# Arduino Uno Q Projects with Agentic Coding

A collection of Arduino Uno Q projects used to prototype hardware ideas, test interaction patterns, and explore agentic coding workflows across multiple AI assistants.

This repository is not a single polished product. It is a working lab for building and iterating on Uno Q applications that combine:
- MCU-side Arduino sketches for real-time control
- MPU-side Python services and web UIs
- reusable agent skills, instructions, and project conventions
- multiple agent runtimes working against the same codebase and documentation

In practice, that means the repo is used both to ship small working experiments and to refine how agents can safely collaborate on embedded, web, and documentation tasks without losing project context.

The main themes are:
- rapid prototyping on the Arduino Uno Q dual-processor architecture
- adapting and extending official App Lab examples
- documenting hardware clearly with ATN-IO v3 wiring files
- capturing repeatable workflows as reusable skills under `.agents/skills/`

Use projects at your own risk. I take no responsibility for any damage or loss of data that may occur as a result of using this code.

## How This Repo Is Used

Projects in this workspace usually follow the Arduino App Lab structure:

```text
app-name/
	app.yaml
	python/
	sketch/
	assets/
```

Typical work in this repo looks like:
- starting from a local `copy-of-*` official sample when one matches
- extending it into a local prototype or experiment
- using shared instructions and skills so different agents follow the same rules
- syncing and testing on a real Uno Q board

The result is a repo that acts as both a project collection and a testbed for agent-assisted development methods.

## Key Documentation

- [PERFORMANCE.md](./PERFORMANCE.md): split-host development model for running agent tooling without overloading the board
- [wiring-notation.md](./wiring-notation.md): canonical ATN-IO v3 wiring notation specification
- [.agents/skills/](./.agents/skills/): reusable skills for Uno Q app development, CLI usage, RouterBridge work, web UI work, and wiring documentation
- [CLAUDE.md](./CLAUDE.md): repository guidance for Claude-based workflows
- [GEMINI.md](./GEMINI.md): repository guidance for Gemini-based workflows
- [.github/copilot-instructions.md](./.github/copilot-instructions.md): repository guidance for Copilot-based workflows

## Skills and Agent Workflow

The shared skill library under `.agents/skills/` is what keeps multi-agent work coherent. Instead of treating each session as a clean slate, the repo captures recurring practices such as:
- Uno Q app structure and Bridge patterns
- App Lab CLI deployment and troubleshooting
- sensor integration workflows
- web UI implementation patterns
- ATN-IO wiring document creation and validation

That setup makes it easier to prototype the same idea through different agents while keeping the implementation patterns, documentation format, and hardware constraints aligned.

## Useful Links

- [Arduino Uno Q User Manual](https://docs.arduino.cc/tutorials/uno-q/user-manual/)
- [Arduino Uno Q App CLI](https://docs.arduino.cc/software/app-lab/tutorials/cli/)
- [Performance & Architecture Guide](./PERFORMANCE.md)
- [ATN-IO Wiring Notation Guide](./wiring-notation.md)

## Credits & Acknowledgments

Sample code from Arduino SRL App Labs is included in this project to provide context.

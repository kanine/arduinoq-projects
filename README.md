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

## Technical Setup

Development is typically done on a separate, more capable machine rather than directly on the Uno Q itself. That is a practical constraint, not just a preference: the Uno Q is excellent for running the app and talking to hardware, but it has limited RAM and CPU headroom for modern agent tooling, language servers, indexing, and multi-agent workflows.

The usual split is:
- source code, editors, terminals, and AI agents run on a host machine
- the Uno Q acts as the deployment and execution target
- agents make local edits on the host, then sync the app to the board and restart it for testing

This keeps the board focused on what it is good at: running the Python service, uploading the MCU sketch, serving the web UI, and interacting with real hardware.

### Sync, Deploy, Restart Workflow

The repo includes [bash/sync_to_uno1.sh](./bash/sync_to_uno1.sh) as the standard example for syncing apps from the host to the board. It uses `rsync` over SSH to copy an app directory into the board's App Lab location under `/home/arduino/ArduinoApps/`.

Typical usage:

```bash
./bash/sync_to_uno1.sh buzzerwithui
ssh uno1 arduino-app-cli app restart "/home/arduino/ArduinoApps/buzzerwithui"
ssh uno1 arduino-app-cli app logs "/home/arduino/ArduinoApps/buzzerwithui" --all
```

The script is effectively wrapping an `rsync` command of this form:

```bash
rsync --archive --compress --human-readable --itemize-changes \
	--omit-dir-times \
	--exclude=.git \
	--exclude=.DS_Store \
	--exclude=__pycache__/ \
	--exclude=*.pyc \
	<local-app-dir>/ uno1:/home/arduino/ArduinoApps/<app-name>/
```

In other words, agents and humans both follow the same basic loop:
- edit locally on the host machine
- sync the changed app to the Uno Q
- restart the app on the board with `arduino-app-cli`
- inspect logs and app status over SSH
- verify behavior against the real hardware

Operational notes:
- Use SSH for all `arduino-app-cli` activity; the host-side sync script only copies files.
- Quote the remote app path in SSH commands.
- Restarts are not instant: `arduino-app-cli app restart` recompiles/uploads the MCU sketch and reprovisions the Python container.
- During that restart window, `ssh uno1 arduino-app-cli app list` can briefly show the app as `stopped` before it returns to `running`.
- For web UI apps, `ssh uno1 arduino-app-cli app logs "/home/arduino/ArduinoApps/<app-name>" --all` is the best way to confirm the exact network URL.

That deployment model is a core part of how this repo supports agentic development without overloading the board itself.

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

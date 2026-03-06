---
name: arduino-app-cli
description: Use this skill when working with Arduino App Lab CLI (`arduino-app-cli`) on Arduino UNO Q boards, especially to connect over ADB/SSH, create or edit apps in `/home/arduino/ArduinoApps`, start/stop apps, inspect logs, list apps/bricks, and run system update or network commands.
---

# Arduino App CLI

## Quick Start

1. Confirm board access method.
2. Connect to the board shell over ADB or SSH.
3. Run `arduino-app-cli` to verify CLI availability.
4. Execute the requested app lifecycle or system command.
5. Verify outcome with `arduino-app-cli app list` and logs when relevant.

## Connection Workflow

### ADB

1. Run `adb devices` and confirm the UNO Q appears.
2. Run `adb shell` to enter the board shell.
3. Run CLI commands inside the shell.

### SSH

1. Ensure first-time App Lab setup is completed (board name, password, Wi-Fi).
2. Connect with `ssh arduino@<boardname>.local`.
3. Run CLI commands in the remote shell.

## App Lifecycle Tasks

### Create App

- Use `arduino-app-cli app new "<app-name>"`.
- Expect project creation under `/home/arduino/ArduinoApps/<app-name>`.

### Edit App Files via Host

- Pull projects: `adb pull /home/arduino/ArduinoApps <local-path>`.
- Push projects: `adb push <local-path> /home/arduino/ArduinoApps`.
- Fix ownership when needed: `adb shell chown -R arduino:arduino /home/arduino/ArduinoApps`.

### Start, Stop, and Observe

- Start: `arduino-app-cli app start "/home/arduino/ArduinoApps/<app-name>"`.
- Stop: `arduino-app-cli app stop "/home/arduino/ArduinoApps/<app-name>"`.
- Logs: `arduino-app-cli app logs /home/arduino/ArduinoApps/<app-name> --all`.
- List: `arduino-app-cli app list`.

### Run Shortcut Targets

- User app: `arduino-app-cli app start user:<app-name>`.
- Example app: `arduino-app-cli app start examples:<example-name>`.

## System and Brick Tasks

- Update: `arduino-app-cli system update`.
- Board name: `arduino-app-cli system set-name "<name>"`.
- Network mode: `arduino-app-cli system network enable` or `disable`.
- Cleanup: `arduino-app-cli system cleanup`.
- Bricks list: `arduino-app-cli brick list`.
- Brick details: `arduino-app-cli brick details arduino:<brick>`.

## Troubleshooting Rules

- If the board is not visible over ADB, retry after waiting up to one minute after USB connection.
- If permission errors occur under `/home/arduino/ArduinoApps`, correct ownership before retrying file sync.
- If app start fails, run `arduino-app-cli app list` and `app logs ... --all` to identify path and runtime issues.

## References

- For command examples and expected behavior, read `references/cli-reference.md`.

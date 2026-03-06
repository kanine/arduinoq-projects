# Arduino App CLI Reference

Source tutorial:
- https://docs.arduino.cc/software/app-lab/tutorials/cli/
- Markdown source: https://raw.githubusercontent.com/arduino/docs-content/main/content/software/app-lab/tutorials/03.cli/apps-lab-cli.md

## Board Access

- `adb devices`
- `adb shell`
- `ssh arduino@<boardname>.local`

## App Commands

- `arduino-app-cli`
- `arduino-app-cli app new "<app-name>"`
- `arduino-app-cli app start "/home/arduino/ArduinoApps/<app-name>"`
- `arduino-app-cli app stop "/home/arduino/ArduinoApps/<app-name>"`
- `arduino-app-cli app logs /home/arduino/ArduinoApps/<app-name> --all`
- `arduino-app-cli app list`
- `arduino-app-cli app start user:<app-name>`
- `arduino-app-cli app start examples:<example-name>`

## File Sync Commands

- `adb pull /home/arduino/ArduinoApps <local-path>`
- `adb push <local-path> /home/arduino/ArduinoApps`
- `adb shell chown -R arduino:arduino /home/arduino/ArduinoApps`

## System Commands

- `arduino-app-cli system update`
- `arduino-app-cli system set-name "<name>"`
- `arduino-app-cli system network enable`
- `arduino-app-cli system network disable`
- `arduino-app-cli system cleanup`

## Brick Commands

- `arduino-app-cli brick list`
- `arduino-app-cli brick details arduino:<brick>`

## Operational Notes

- UNO Q is expected to have `arduino-app-cli` preinstalled.
- App projects are created under `/home/arduino/ArduinoApps`.
- Network mode controls SSH availability on local network.

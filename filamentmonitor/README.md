# Filament Monitor

An Arduino Uno Q app for tracking the remaining material on a feed spool in real time. A VL53L1X Time-of-Flight sensor measures the distance to the top surface of the spool; the app converts that reading into a percentage of material remaining and displays it on a web dashboard accessible from any browser on the local network.

Developed for industrial use on a process line that feeds material from 20 kg spools. The percentage display lets operators see at a glance how much spool life is left without stopping the machine or lifting a spool.

---

## How It Works

### Sensor placement

Mount the VL53L1X above the spool on the **Wire1** (Qwiic) connector, pointing straight down at the centre of the spool surface. The sensor measures the distance between itself and the top layer of material.

- When the spool is **full**, the material stack is tall — the sensor reads a short distance. Set this as `startMeasure` in Settings.
- As the spool is consumed, the stack shrinks and the sensor distance **increases**.
- When the spool is **empty** (bare core), the distance has increased by exactly `fullRadius − coreRadius` mm.

The board does not need to know the empty distance separately — it calculates it from the spool geometry you provide in `config.json`.

### The maths: why it isn't linear

Filament wraps around a circular core, so the amount of material is proportional to **cross-sectional area** (πr²), not radius. Using a linear percentage would significantly overreport remaining material — at the physical midpoint of spool height the machine actually has around 39% left, not 50%.

The app uses the area formula:

```
percent = (r_current² − r_core²) / (R_full² − r_core²) × 100
```

Where `r_current` is derived from the sensor reading by mapping the distance linearly onto the physical radius range.

---

## Configuration (`config.json`)

```json
{
  "measurements": {
    "startMeasure": 220,
    "windowSeconds": 2.0
  },
  "spool": {
    "fullRadius": 200,
    "coreRadius": 80
  }
}
```

| Field | Meaning |
|---|---|
| `startMeasure` | Sensor distance (mm) when the spool is completely full. Measure this with the sensor in its mounted position using the live reading in the Settings modal. |
| `windowSeconds` | Length of each averaging window in seconds. Readings in each window are trimmed (top and bottom 10% discarded) before averaging. |
| `fullRadius` | Physical radius of the spool when full, measured from the spool centre (mm). This is a property of the spool type, not the sensor. |
| `coreRadius` | Physical radius of the bare plastic core when the spool is empty (mm). Also a spool type property. |

`startMeasure` and `windowSeconds` can be changed live from the Settings modal in the UI without restarting the app. Changes are persisted to `config.json` immediately and survive restarts.

`fullRadius` and `coreRadius` describe the physical spool type and rarely need to change. Edit `config.json` directly and redeploy if they do.

---

## Web UI

Open `http://<board-ip>:7000` from any browser on the network.

### Main display

- **Percentage label** — bold, large. Shows `XX% Remaining`.
- **Progress bar** — colour changes with level:
  - Green: above 50%
  - Yellow: 20–50%
  - Red: below 20%

### Toggles

| Toggle | Default | Persists |
|---|---|---|
| Show Reading | Off | Per browser (localStorage) |
| Console Logging | Off | Per browser (localStorage) |

**Show Reading** reveals the trimmed-average distance and the latest raw sample beneath the progress bar. Useful during calibration or troubleshooting; hidden by default so operators see only the percentage.

**Console Logging** sends each completed averaging batch to the browser developer console, including the full set of raw readings from that window. Useful for diagnosing noisy sensor output.

### Settings modal (⚙)

Click the cog icon in the header to open Settings. The modal always shows the **current live average reading** alongside the Start Measure field — use this to calibrate the sensor after mounting or repositioning.

To set `startMeasure` on a new machine:

1. Mount the sensor above a **full spool** in the operating position.
2. Open the Settings modal and wait for the live reading to stabilise.
3. Type that value into the Start Measure field and click **Save**.

---

## Suggested Use Cases

**Production line filament monitoring**
The primary use case. Mount above a 20 kg spool on a process line. The operator dashboard shows remaining percentage at a glance; the colour-coded bar makes low-spool conditions visible from across the floor.

**Multiple machines, one spool type**
Because `startMeasure` is the only machine-specific value, the same app can be deployed to multiple boards. Calibrate the sensor position independently on each machine via the Settings modal. `fullRadius` and `coreRadius` stay the same across all machines using the same spool specification.

**Spool change scheduling**
Set an internal threshold based on shift length or job run time. The yellow band (20–50%) acts as a "prepare a new spool" prompt; red (<20%) as a "change now" indicator.

**Any wound-material spool**
The area-based formula applies to any cylindrical feed spool — wire, rope, ribbon, sleeving, or tube stock — as long as the material winds in uniform layers. Measure `fullRadius` and `coreRadius` for the spool type and set `startMeasure` for the sensor position.

---

## App Layout

```
filamentmonitor/
├── app.yaml
├── config.json           # Spool geometry + runtime settings (persisted)
├── README.md
├── brief.md              # Original feature brief
├── plan-area-based-percent.md
├── thepercentremainingproblem.md
├── assets/
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   └── libs/
│       └── socket.io.min.js
├── python/
│   └── main.py
└── sketch/
    ├── sketch.ino
    └── sketch.yaml
```

---

## Wiring

Connect the VL53L1X to the Uno Q Qwiic connector (Wire1):

| Board | Sensor |
|---|---|
| Qwiic SDA | SDA |
| Qwiic SCL | SCL |
| 3.3 V | VIN |
| GND | GND |

All GPIOs on the Uno Q are 3.3 V. The VL53L1X operates at 3.3 V natively — no level shifting required.

The MCU initialises the sensor at 400 kHz I2C, Long distance mode, 50 ms timing budget, continuous measurement at 50 ms intervals.

---

## Deployment

```bash
# Sync to board
./scripts/sync_to_uno1.sh filamentmonitor

# Restart
ssh uno1 arduino-app-cli app restart "/home/arduino/ArduinoApps/filamentmonitor"

# Check logs
ssh uno1 arduino-app-cli app logs "/home/arduino/ArduinoApps/filamentmonitor" --all
```

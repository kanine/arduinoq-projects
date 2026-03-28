#!/usr/bin/env python3
"""Generate sketch/sensor_config.h from the sensor block in config.json.

Usage:
    python3 scripts/gen_sensor_config.py <app-name>

Example:
    python3 scripts/gen_sensor_config.py timeofflighttesting

Run this before syncing whenever you change the sensor section of config.json.
The generated header is included by sketch.ino and compiled into the MCU firmware.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

MODE_MAP = {
    "Short":  "VL53L1X::Short",
    "Medium": "VL53L1X::Medium",
    "Long":   "VL53L1X::Long",
}

VALID_BUDGETS_MS = {15, 20, 33, 50, 100, 140, 200, 500, 1000}


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <app-name>", file=sys.stderr)
        sys.exit(1)

    app_name = sys.argv[1]
    config_path = REPO_ROOT / app_name / "config.json"
    out_path    = REPO_ROOT / app_name / "sketch" / "sensor_config.h"

    if not config_path.exists():
        print(f"ERROR: {config_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(config_path) as f:
        cfg = json.load(f)

    sensor = cfg.get("sensor", {})

    mode_str = sensor.get("distance_mode", "Short")
    mode_cpp = MODE_MAP.get(mode_str)
    if not mode_cpp:
        print(f"ERROR: distance_mode must be Short, Medium, or Long — got '{mode_str}'",
              file=sys.stderr)
        sys.exit(1)

    tb_ms = int(sensor.get("timing_budget_ms", 50))
    if tb_ms not in VALID_BUDGETS_MS:
        print(f"WARNING: timing_budget_ms={tb_ms} is not in known-valid set {sorted(VALID_BUDGETS_MS)}",
              file=sys.stderr)

    imp_ms = int(sensor.get("inter_measurement_ms", 50))
    if imp_ms < tb_ms:
        print(f"ERROR: inter_measurement_ms={imp_ms} must be >= timing_budget_ms={tb_ms}",
              file=sys.stderr)
        sys.exit(1)

    roi_w = int(sensor.get("roi_width", 16))
    roi_h = int(sensor.get("roi_height", 16))
    if not (4 <= roi_w <= 16 and 4 <= roi_h <= 16):
        print(f"ERROR: roi_width and roi_height must each be 4–16", file=sys.stderr)
        sys.exit(1)

    roi_center = int(sensor.get("roi_center", 199))
    if not (0 <= roi_center <= 255):
        print(f"ERROR: roi_center must be 0–255", file=sys.stderr)
        sys.exit(1)

    header = f"""\
// Auto-generated from config.json — do not edit manually.
// To update: edit the sensor section of config.json, then run:
//   python3 scripts/gen_sensor_config.py {app_name}
// and re-sync + restart the app.

#pragma once

#define SENSOR_DISTANCE_MODE        {mode_cpp}
#define SENSOR_TIMING_BUDGET_US     {tb_ms * 1000}
#define SENSOR_INTER_MEASUREMENT_MS {imp_ms}
#define SENSOR_ROI_WIDTH            {roi_w}
#define SENSOR_ROI_HEIGHT           {roi_h}
#define SENSOR_ROI_CENTER           {roi_center}
"""

    out_path.write_text(header)
    print(f"Generated {out_path.relative_to(REPO_ROOT)}")
    print(f"  distance_mode        = {mode_cpp}")
    print(f"  timing_budget_us     = {tb_ms * 1000}  ({tb_ms} ms)")
    print(f"  inter_measurement_ms = {imp_ms}")
    print(f"  roi_width x height   = {roi_w} x {roi_h}")
    print(f"  roi_center           = {roi_center}")


if __name__ == "__main__":
    main()

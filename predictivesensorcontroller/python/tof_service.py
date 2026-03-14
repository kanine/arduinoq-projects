from arduino.app_utils import Bridge, Logger

import store

logger = Logger("pfsc-tof")

DEFAULT_THRESHOLD_MM = 250
MIN_THRESHOLD_MM     = 30
MAX_THRESHOLD_MM     = 4000

FAULT_MESSAGES = {
    0: "",
    1: "Sensor not initialized",
    2: "No I2C ACK",
    3: "VL53L1X init failed",
    4: "VL53L1X rejected timing budget",
    5: "VL53L1X read timeout",
    6: "VL53L1X range status invalid",
}

# Static topology — matches sketch.ino defines
SENSOR_CONFIGS = {
    "sensor_1": {"prefix": "s1", "address": "0x30", "xshut_pin": "D3"},
    "sensor_2": {"prefix": "s2", "address": "0x31", "xshut_pin": "D4"},
}


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


class ToFDiagnosticsService:
    def __init__(self):
        saved = store.load_tof_sensor_config() or {}
        for sid, cfg in SENSOR_CONFIGS.items():
            saved_thresh = saved.get(sid, {}).get("threshold_mm", DEFAULT_THRESHOLD_MM)
            cfg["threshold_mm"] = clamp(int(saved_thresh), MIN_THRESHOLD_MM, MAX_THRESHOLD_MM)
        self._thresholds_synced = False

    def _sync_thresholds_if_needed(self):
        if self._thresholds_synced:
            return
        try:
            for sid, cfg in SENSOR_CONFIGS.items():
                Bridge.call(f"set_{cfg['prefix']}_threshold", int(cfg["threshold_mm"]))
            self._thresholds_synced = True
        except Exception as exc:
            logger.warning(f"TOF threshold sync failed: {exc}")

    def _get_sensor_status(self, sid: str) -> dict:
        cfg    = SENSOR_CONFIGS[sid]
        prefix = cfg["prefix"]
        try:
            online         = int(Bridge.call(f"get_{prefix}_online")) == 1
            distance_mm    = int(Bridge.call(f"get_{prefix}_distance_mm"))
            data_ready     = int(Bridge.call(f"get_{prefix}_data_ready")) == 1
            threshold_mm   = int(Bridge.call(f"get_{prefix}_threshold_mm"))
            object_present = int(Bridge.call(f"get_{prefix}_object_present")) == 1
            i2c_seen       = int(Bridge.call(f"get_{prefix}_i2c_seen")) == 1
            init_stage     = int(Bridge.call(f"get_{prefix}_init_stage"))
            fault_code     = int(Bridge.call(f"get_{prefix}_fault_code"))
            last_read_ms   = int(Bridge.call(f"get_{prefix}_last_read_ms"))
        except Exception as exc:
            fault = f"Bridge call failed: {exc}"
            logger.warning(f"{sid}: {fault}")
            return {
                "online":           False,
                "distance_mm":      None,
                "data_ready":       False,
                "threshold_mm":     int(cfg["threshold_mm"]),
                "object_present":   False,
                "i2c_address_seen": False,
                "init_stage":       0,
                "last_read_ms":     None,
                "fault":            fault,
                "address":          cfg["address"],
                "xshut_pin":        cfg["xshut_pin"],
            }

        fault = FAULT_MESSAGES.get(fault_code, f"Unknown fault {fault_code}")
        return {
            "online":           online,
            "distance_mm":      None if distance_mm < 0 else distance_mm,
            "data_ready":       data_ready,
            "threshold_mm":     threshold_mm,
            "object_present":   object_present,
            "i2c_address_seen": i2c_seen,
            "init_stage":       init_stage,
            "last_read_ms":     None if last_read_ms <= 0 else last_read_ms,
            "fault":            fault,
            "address":          cfg["address"],
            "xshut_pin":        cfg["xshut_pin"],
        }

    def get_status(self) -> dict:
        self._sync_thresholds_if_needed()
        try:
            timing_budget_ms = int(Bridge.call("get_tof_timing_budget_ms"))
        except Exception:
            timing_budget_ms = 50

        return {
            "sensors": {sid: self._get_sensor_status(sid) for sid in SENSOR_CONFIGS},
            "timing_budget_ms": timing_budget_ms,
        }

    def update_config(self, payload: dict | None) -> dict:
        payload = payload or {}
        for sid, cfg in SENSOR_CONFIGS.items():
            if sid not in payload:
                continue
            threshold_raw = payload[sid].get("threshold_mm", cfg["threshold_mm"])
            try:
                threshold_mm = clamp(int(threshold_raw), MIN_THRESHOLD_MM, MAX_THRESHOLD_MM)
            except (TypeError, ValueError):
                raise ValueError(f"{sid}: threshold_mm must be an integer")
            try:
                Bridge.call(f"set_{cfg['prefix']}_threshold", threshold_mm)
            except Exception as exc:
                self._thresholds_synced = False
                raise RuntimeError(f"Unable to update MCU threshold for {sid}: {exc}") from exc
            cfg["threshold_mm"] = threshold_mm

        store.save_tof_sensor_config(
            {sid: {"threshold_mm": cfg["threshold_mm"]} for sid, cfg in SENSOR_CONFIGS.items()}
        )
        return {"ok": True, "status": self.get_status()}

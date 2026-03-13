from arduino.app_utils import Bridge, Logger

import store

logger = Logger("pfsc-tof")

DEFAULT_THRESHOLD_MM = 250
MIN_THRESHOLD_MM = 30
MAX_THRESHOLD_MM = 4000
FAULT_MESSAGES = {
    0: "",
    1: "Sensor not initialized",
    2: "No I2C ACK at 0x29",
    3: "VL53L1X init failed at 0x29",
    4: "VL53L1X rejected timing budget",
    5: "VL53L1X read timeout",
    6: "VL53L1X range status invalid",
}


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


class ToFDiagnosticsService:
    def __init__(self):
        saved = store.load_tof_test_config() or {}
        self._threshold_mm = clamp(
            int(saved.get("threshold_mm", DEFAULT_THRESHOLD_MM)),
            MIN_THRESHOLD_MM,
            MAX_THRESHOLD_MM,
        )
        self._threshold_synced = False

    def _sync_threshold_if_needed(self):
        if self._threshold_synced:
            return
        try:
            Bridge.call("set_tof_test_config", int(self._threshold_mm))
            self._threshold_synced = True
        except Exception as exc:
            logger.warning(f"TOF threshold sync failed: {exc}")

    def _fallback_status(self, fault: str) -> dict:
        return {
            "online": False,
            "distance_mm": None,
            "data_ready": False,
            "threshold_mm": int(self._threshold_mm),
            "object_present": False,
            "timing_budget_ms": 50,
            "last_read_ms": None,
            "fault": fault,
            "health": {
                "online": False,
                "fault": fault,
                "sensor_address": "0x29",
                "xshut_pin": "optional (reserve D3 for next phase)",
            },
        }

    def get_status(self) -> dict:
        self._sync_threshold_if_needed()
        try:
            online = int(Bridge.call("get_tof_online")) == 1
            distance_mm = int(Bridge.call("get_tof_distance_mm"))
            data_ready = int(Bridge.call("get_tof_data_ready")) == 1
            threshold_mm = int(Bridge.call("get_tof_threshold_mm"))
            object_present = int(Bridge.call("get_tof_object_present")) == 1
            timing_budget_ms = int(Bridge.call("get_tof_timing_budget_ms"))
            last_read_ms = int(Bridge.call("get_tof_last_read_ms"))
            i2c_address_seen = int(Bridge.call("get_tof_i2c_address_seen")) == 1
            last_scan_ms = int(Bridge.call("get_tof_last_scan_ms"))
            init_stage = int(Bridge.call("get_tof_init_stage"))
            fault_code = int(Bridge.call("get_tof_fault_code"))
        except Exception as exc:
            fault = f"Bridge call failed: {exc}"
            logger.warning(fault)
            return self._fallback_status(fault)

        fault = FAULT_MESSAGES.get(fault_code, f"Unknown fault code {fault_code}")
        return {
            "online": online,
            "distance_mm": None if distance_mm < 0 else distance_mm,
            "data_ready": data_ready,
            "threshold_mm": threshold_mm,
            "object_present": object_present,
            "timing_budget_ms": timing_budget_ms,
            "last_read_ms": None if last_read_ms <= 0 else last_read_ms,
            "i2c_address_seen": i2c_address_seen,
            "last_scan_ms": None if last_scan_ms <= 0 else last_scan_ms,
            "init_stage": init_stage,
            "fault": fault,
            "health": {
                "online": online,
                "fault": fault,
                "sensor_address": "0x29",
                "xshut_pin": "optional (reserve D3 for next phase)",
                "i2c_address_seen": i2c_address_seen,
                "last_scan_ms": None if last_scan_ms <= 0 else last_scan_ms,
                "init_stage": init_stage,
            },
        }

    def update_config(self, payload: dict | None) -> dict:
        payload = payload or {}
        threshold_raw = payload.get("threshold_mm", self._threshold_mm)
        try:
            threshold_mm = clamp(int(threshold_raw), MIN_THRESHOLD_MM, MAX_THRESHOLD_MM)
        except (TypeError, ValueError):
            raise ValueError("threshold_mm must be an integer")

        try:
            Bridge.call("set_tof_test_config", threshold_mm)
            self._threshold_synced = True
        except Exception as exc:
            self._threshold_synced = False
            raise RuntimeError(f"Unable to update MCU threshold: {exc}") from exc

        self._threshold_mm = threshold_mm
        store.save_tof_test_config(threshold_mm)
        return {
            "ok": True,
            "threshold_mm": threshold_mm,
            "status": self.get_status(),
        }

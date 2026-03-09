import threading
import time
import logging
import store

logger = logging.getLogger("pfsc-controller")

class PredictionController:
    def __init__(self):
        # Default Configuration
        self.config = {
            "distance_cut_to_A": 100,
            "distance_AB": 50,
            "distance_BC": 50,
            "target_length": 300,
            "simulation_mode": True,
            "validation_enabled": True
        }
        
        # Current State
        self.state = {
            "sensorA": 0,
            "sensorB": 0,
            "sensorC": 0,
            "relay_active": 0,
            "speed_mm_per_s": 0.0,
            "target_length_mm": self.config["target_length"],
            "next_cut_ms": 0,
            "status": "ready"
        }
        
        # Load config from DB if it exists
        saved_config = store.load_config()
        if saved_config:
            self.config.update(saved_config)
            self.state["target_length_mm"] = self.config["target_length"]
        else:
            store.save_config(self.config)

        self._sim_timerA = None
        self._sim_timerB = None
        self._sim_timerC = None
        self._sim_timerRelay = None
        self._sim_timerRelayOff = None

    def get_status(self):
        """Return the current system state."""
        st = self.state.copy()
        st["simulation_mode"] = self.config["simulation_mode"]
        return st
    
    def get_config(self):
        return self.config

    def update_config(self, new_config):
        """Update configuration and persist it."""
        for key in ["distance_cut_to_A", "distance_AB", "distance_BC", "target_length"]:
            if key in new_config:
                self.config[key] = int(new_config[key])
        
        if "simulation_mode" in new_config:
            self.config["simulation_mode"] = bool(new_config["simulation_mode"])
        if "validation_enabled" in new_config:
            self.config["validation_enabled"] = bool(new_config["validation_enabled"])
            
        self.state["target_length_mm"] = self.config["target_length"]
        store.save_config(self.config)
        logger.info(f"Config updated: {self.config}")

    def reset_state(self):
        """Reset the physical state indicators for a new run."""
        self.state["sensorA"] = 0
        self.state["sensorB"] = 0
        self.state["sensorC"] = 0
        self.state["relay_active"] = 0
        self.state["status"] = "running"
        self.state["speed_mm_per_s"] = 0.0

    def trigger_simulation(self, speed_mm_per_s: float):
        """Mock the timeline of an object moving past the sensors."""
        if not self.config["simulation_mode"]:
            raise ValueError("Simulation mode is not active")
        
        if speed_mm_per_s <= 0:
            raise ValueError("Speed must be positive")
            
        # Cancel any pending simulation
        self._cancel_timers()
        self.reset_state()
        self.state["status"] = "simulating"
        
        # Distances
        d_CA = self.config["distance_cut_to_A"]
        d_AB = self.config["distance_AB"]
        d_BC = self.config["distance_BC"]
        target_len = self.config["target_length"]
        
        # Physical check
        d_C_total = d_CA + d_AB + d_BC
        if target_len <= d_C_total:
            self.state["status"] = "error: target < cut-to-C distance"
            logger.error(self.state["status"])
            return {"error": "Target length too short for sensor layout"}

        # Calculate absolute millisecond timestamps based on the speed
        # Assuming cut point is at t=0 for the start of the material (where material starts)
        # Material at Sensor A: has travelled d_CA
        ms_to_A = (d_CA / speed_mm_per_s) * 1000.0
        # Material at Sensor B: has travelled d_CA + d_AB
        ms_to_B = ((d_CA + d_AB) / speed_mm_per_s) * 1000.0
        # Material at Sensor C: has travelled d_CA + d_AB + d_BC
        ms_to_C = ((d_CA + d_AB + d_BC) / speed_mm_per_s) * 1000.0
        # Material Cut trigger: has travelled target_length
        ms_to_Relay = (target_len / speed_mm_per_s) * 1000.0
        
        logger.info(f"Starting simulation at speed {speed_mm_per_s} mm/s.")
        logger.info(f"Scheduled events (ms from start): A:{ms_to_A:.0f}, B:{ms_to_B:.0f}, C:{ms_to_C:.0f}, Cut:{ms_to_Relay:.0f}")

        # The timeline starts from the moment the object triggers A.
        # But for UI simulation purposes, let's say "start" is 0.
        # So we trigger A at ms_to_A from now.
        start_time = time.time()
        
        self.state["next_cut_ms"] = int(ms_to_Relay - ms_to_A) # Estimated time from A
        self.state["speed_mm_per_s"] = speed_mm_per_s

        # Event: Sensor A
        self._sim_timerA = threading.Timer(ms_to_A / 1000.0, self._activate_sensor, args=("sensorA",))
        self._sim_timerA.start()

        # Event: Sensor B
        self._sim_timerB = threading.Timer(ms_to_B / 1000.0, self._activate_sensor, args=("sensorB",))
        self._sim_timerB.start()

        # Event: Sensor C
        self._sim_timerC = threading.Timer(ms_to_C / 1000.0, self._activate_sensor, args=("sensorC",))
        self._sim_timerC.start()

        # Event: Cut Relay
        pulse_ms = 100
        self._sim_timerRelay = threading.Timer(ms_to_Relay / 1000.0, self._activate_relay, args=(speed_mm_per_s,))
        self._sim_timerRelay.start()
        
        # Turn relay off
        self._sim_timerRelayOff = threading.Timer((ms_to_Relay + pulse_ms) / 1000.0, self._deactivate_relay)
        self._sim_timerRelayOff.start()

        return {"ok": True, "message": "Simulation started"}

    def _activate_sensor(self, sensor_name):
        logger.debug(f"{sensor_name} triggered")
        self.state[sensor_name] = 1

    def _activate_relay(self, speed_mm_per_s: float):
        logger.debug("Relay triggered")
        self.state["relay_active"] = 1
        
        # Log the completed cycle with exact relative timestamps at the moment of cut
        metrics = {
            "time_A": 0.0, # The anchor point for this cycle
            "time_B": round(self.config["distance_AB"] / speed_mm_per_s, 2), 
            "time_C": round((self.config["distance_AB"]+self.config["distance_BC"]) / speed_mm_per_s, 2),
            "speed": speed_mm_per_s,
            "target_length": self.config["target_length"],
            "predicted_cut_time": round(self.state["next_cut_ms"] / 1000.0, 2), # sec
            "status": "success"
        }
        store.log_cycle(metrics)

    def _deactivate_relay(self):
        logger.debug("Relay off, cycle complete")
        self.state["relay_active"] = 0
        self.state["status"] = "ready"

    def _cancel_timers(self):
        timers = [self._sim_timerA, self._sim_timerB, self._sim_timerC, self._sim_timerRelay, self._sim_timerRelayOff]
        for t in timers:
            if t is not None:
                t.cancel()

# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
#
# SPDX-License-Identifier: MPL-2.0

from arduino.app_bricks.dbstorage_sqlstore import SQLStore
from typing import Any

DB_NAME = "predictivesensorcontroller"

# Initialize and expose a module-level SQLStore instance
db = SQLStore(database_name=DB_NAME)

def init_db():
    """Start SQLStore and create the logs table."""
    db.start()
    db.create_table(
        "cycle_logs",
        {
            "id": "INTEGER PRIMARY KEY",
            "timestamp": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "sensorA_time": "REAL",
            "sensorB_time": "REAL",
            "sensorC_time": "REAL",
            "calculated_speed": "REAL",
            "target_length": "INTEGER",
            "predicted_cut_time": "REAL",
            "actual_cut_time": "REAL",
            "status": "TEXT" # "success", "error", "warning"
        }
    )
    # Also create a simple config table for persistence across reboots
    db.create_table(
        "config",
        {
            "id": "INTEGER PRIMARY KEY", # only one row
            "distance_cut_to_A": "INTEGER",
            "distance_AB": "INTEGER",
            "distance_BC": "INTEGER",
            "target_length": "INTEGER",
            "simulation_mode": "INTEGER", # 0 or 1
            "validation_enabled": "INTEGER" # 0 or 1
        }
    )
    print(f"[pfsc_store] SQLStore started for {DB_NAME}")

def log_cycle(metrics: dict):
    """Insert a new simulation cycle record into DB."""
    record = {
        "sensorA_time": metrics.get("time_A"),
        "sensorB_time": metrics.get("time_B"),
        "sensorC_time": metrics.get("time_C"),
        "calculated_speed": metrics.get("speed"),
        "target_length": metrics.get("target_length"),
        "predicted_cut_time": metrics.get("predicted_cut_time"),
        "actual_cut_time": metrics.get("predicted_cut_time"), # For now in simulation
        "status": metrics.get("status", "success")
    }
    db.store("cycle_logs", record, create_table=False)

def get_recent_logs(limit: int = 20) -> list[dict[str, Any]]:
    """Return ordered list of cycle records."""
    res = db.read("cycle_logs", order_by="timestamp DESC", limit=limit) or []
    return res

def save_config(config: dict):
    """Save or update system configuration."""
    record = {
        "id": 1,
        "distance_cut_to_A": config.get("distance_cut_to_A", 100),
        "distance_AB": config.get("distance_AB", 50),
        "distance_BC": config.get("distance_BC", 50),
        "target_length": config.get("target_length", 300),
        "simulation_mode": 1 if config.get("simulation_mode", True) else 0,
        "validation_enabled": 1 if config.get("validation_enabled", True) else 0
    }
    # Check if exists
    existing = db.read("config", condition="id=1")
    if existing and len(existing) > 0:
        db.update("config", record, condition="id=1")
    else:
        db.store("config", record, create_table=False)

def load_config() -> dict | None:
    """Load configuration from DB."""
    res = db.read("config", condition="id=1")
    if res and len(res) > 0:
        rec = res[0]
        return {
            "distance_cut_to_A": rec.get("distance_cut_to_A"),
            "distance_AB": rec.get("distance_AB"),
            "distance_BC": rec.get("distance_BC"),
            "target_length": rec.get("target_length"),
            "simulation_mode": bool(rec.get("simulation_mode", 1)),
            "validation_enabled": bool(rec.get("validation_enabled", 1))
        }
    return None

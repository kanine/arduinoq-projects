ATN-IO v3
Project: Predictive Sensor Controller - Single VL53L1X Bring-Up

[BOARD]
TYPE  = Arduino Uno Q
LOGIC = 3.3V
MCU   = STM32U585 + QRB2210

[INPUTS]
SDA        -> SDA    # bidirectional (I2C)
SCL        -> SCL    # bidirectional (I2C)
TOF_XSHUT  -> D3     # optional in this phase; reserved for next phase

[COMPONENTS]
ADA3967 = Adafruit VL53L1X Time of Flight Distance Sensor

[WIRING]
# -- Power --------------------------------------------------------
3.3V -> ADA3967.VIN
GND  -> ADA3967.GND

# -- I2C bus ------------------------------------------------------
SDA -> ADA3967.SDA
SCL -> ADA3967.SCL

# -- Control ------------------------------------------------------
# Optional for this phase:
# D3 -> ADA3967.XSHUT

[NOTES]
# Remove the protective shipping film from the sensor window before first testing.
# This phase uses a single sensor only, so the device remains at the default I2C address 0x29.
# The validated bring-up path for this project uses the MCU sensor bus exposed to the sketch as Wire1.
# Power over Qwiic was confirmed, but Qwiic-only testing did not produce an I2C ACK on the MCU bus during early bring-up.
# Use the wiring and bus combination proven by the working timeofflightcheck utility when repeating diagnostics.
# ADA3967.GPIO is intentionally left unconnected in this phase.
# D3 is reserved for XSHUT in the next phase when explicit reset/address control is needed.

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
# Use the Uno Q 3.3V I2C side for bring-up wiring.
# The Qwiic/STEMMA QT cable alone is sufficient for this phase if you leave XSHUT unconnected.
# ADA3967.GPIO is intentionally left unconnected in this phase.
# D3 is reserved for XSHUT in the next phase when explicit reset/address control is needed.

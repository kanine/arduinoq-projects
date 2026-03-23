ATN-IO v3
Project: timeofflightwebhook — VL53L1X ToF sensor; posts distance_mm batches to webhook

[BOARD]
TYPE  = Arduino Uno Q
LOGIC = 3.3V

[INPUTS]
Qwiic SDA -> Wire1 SDA (I2C4 PD12)
Qwiic SCL -> Wire1 SCL (I2C4 PD13)

[OUTPUTS]
; none

[COMPONENTS]
U1 = Adafruit VL53L1X breakout (ToF distance sensor, I2C addr 0x29)

[WIRING]
; Connect via Qwiic / STEMMA QT cable — carries 3.3V power and I2C
Qwiic -> U1.STEMMA_QT

[POWER]
; Qwiic cable supplies 3.3V from board — no separate power wiring needed

[NOTES]
- Use Wire1 (Qwiic connector, I2C4), not Wire (header pins SDA/SCL)
- Wire1.setClock(400000) — 400 kHz confirmed working in this workspace
- Short distance mode: max ~1.3 m
- Timing budget: 50 ms (setMeasurementTimingBudget(50000) — arg is microseconds)
- XSHUT and GPIO pins on breakout are unused; Qwiic cable holds them in safe states
- WEBHOOK_URL is set in config.json (copy config.json.example, fill in your endpoint)

ATN-IO v3
Project: Switch Relay with UI - Arduino Uno Q + 1-channel optocoupler relay module

[BOARD]
TYPE  = Arduino Uno Q
LOGIC = 3.3V
MCU   = STM32U585 (Cortex-M33) + QRB2210 (Linux MPU)

[INPUTS]
# none — relay is output-only

[OUTPUTS]
RELAY_CTRL -> D8    # HIGH = relay ON (jumper set to HIGH-trigger)

[COMPONENTS]
RLY1 = 1-channel optocoupler relay module (optocoupler-isolated, screw terminals)

[WIRING]
# -- Relay module power -----------------------------------------------
3.3V -> RLY1.VCC    # coil supply — tested and confirmed working at 3.3V

GND  -> RLY1.GND

# -- Relay control signal ---------------------------------------------
D8   -> RLY1.IN     # trigger input — 3.3V HIGH activates relay (tested and confirmed)

# -- Relay load output (wire load between NO and COM for safe default) -
# RLY1.NO  -> LOAD+
# RLY1.COM -> LOAD-

[POWER]
3.3V -> 3.3V    # sourced from Arduino Uno Q on-board 3.3V rail

[NOTES]
# Board GPIO logic is 3.3V. Coil VCC and IN trigger both powered from
# the 3.3V rail — tested and confirmed working on this board.
# No level shifting or external supply required.
#
# Jumper on relay module is set to HIGH-trigger (default factory position).
# HIGH on D8 (3.3V) = relay energised (NO closes, NC opens).
# LOW  on D8 (0V)   = relay de-energised (NO open, NC closed).
# To invert, move the jumper to LOW-trigger and update sketch.ino accordingly.
#
# Optocoupler isolation prevents MCU damage from load-side transients.
# Fault-tolerant: if the control line is broken or floating, relay stays off.
#
# Max load ratings (relay output terminals):
#   AC: 250V / 10A
#   DC:  30V / 10A
#
# Wire load to NO + COM for normally-open operation (safe-off on power loss).
# Reserved: Serial1 (MCU), /dev/ttyHS1 (Linux) — do not use.

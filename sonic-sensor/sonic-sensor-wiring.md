ATN-IO v3
Project: Sonic Sensor - Arduino Uno Q + HC-SR04

[BOARD]
TYPE  = Arduino Uno Q
LOGIC = 3.3V
MCU   = STM32U585 + QRB2210

[INPUTS]
ECHO -> D7    # HC-SR04 echo return, routed through divider

[OUTPUTS]
TRIG -> D6

[COMPONENTS]
SONIC1 = HC-SR04
R1     = 10kR    # top resistor: ECHO to D7
R2     = 20kR    # bottom resistor: D7 to GND

[WIRING]
# -- HC-SR04 power ------------------------------------------------
5V  -> SONIC1.VCC
GND -> SONIC1.GND

# -- HC-SR04 signal lines -----------------------------------------
D6          -> SONIC1.TRIG
SONIC1.ECHO -> R1 -> D7
D7          -> R2 -> GND

[NOTES]
# Uno Q GPIO is 3.3V logic; HC-SR04 ECHO is 5V and must be divided.
# Divider ratio: V_D7 = 5V * (20k / (10k + 20k)) = 3.33V nominal.
# This file separates logical mapping ([INPUTS]/[OUTPUTS]) from physical paths ([WIRING]).

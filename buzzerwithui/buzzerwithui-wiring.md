ATN-IO v3
Project: Buzzer with UI - Arduino Uno Q + DFR0032

[BOARD]
TYPE  = Arduino Uno Q
LOGIC = 3.3V
MCU   = STM32U585 + QRB2210

[OUTPUTS]
BUZZ_SIG -> D8    # active buzzer signal input

[COMPONENTS]
BUZZ1 = DFR0032, DFRobot Gravity Digital Buzzer Module, active, 3.3V-5V

[WIRING]
# -- DFR0032 power -----------------------------------------------
3.3V -> BUZZ1.VCC
GND  -> BUZZ1.GND

# -- DFR0032 signal ----------------------------------------------
D8   -> BUZZ1.S

[NOTES]
# DFR0032 is an active buzzer with an internal oscillator; D8 HIGH turns it on.
# Uno Q GPIO is 3.3V logic, which is compatible with the DFR0032 input threshold.
# Use the module signal pin labeled S; do not connect the buzzer signal to Serial1.
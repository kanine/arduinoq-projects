# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
#
# SPDX-License-Identifier: MPL-2.0

from arduino.app_utils import *
import time

led_state = False

def loop():
    global led_state
    time.sleep(0.333)
    led_state = not led_state
    
    # Call the custom function you registered in the .ino
    Bridge.call("set_green_led", led_state)

App.run(user_loop=loop)
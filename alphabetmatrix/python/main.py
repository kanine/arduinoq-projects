# SPDX-FileCopyrightText: Alphabet Matrix App
# SPDX-License-Identifier: MPL-2.0

from arduino.app_utils import *
import time

# This matches the "Sonic Sensor" structure you confirmed is working
def main():
    print("Alphabet App Started")
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    while True:
        for letter in alphabet:
            # We use the board object to send the character to the MCU
            # The MCU sketch handles the actual 1/0 mapping
            board.write_serial(letter)
            time.sleep(1.0) # One letter per second

if __name__ == "__main__":
    main()
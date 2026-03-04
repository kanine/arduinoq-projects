# SPDX-FileCopyrightText: Full Showcase Conductor
# SPDX-License-Identifier: MPL-2.0

from arduino.app_utils import *
import time

# Dictionary for clean shortcode usage
EMOJI_MAP = {
    ":house:": 128, ":check:": 129, ":cross:": 130, ":heart:": 131, 
    ":smile:": 132, ":dog:": 136, ":logo:": 140, ":scissors:": 145,
    ":warning:": 146, ":stop:": 147, ":gear:": 148
}
# Spinner IDs from ICON_FONT
SPINNER = [141, 142, 143, 144]

def scroll_text(text, speed=0.6):
    """Sends each character of a string to the matrix."""
    for char in text.upper():
        Bridge.call("display_id", ord(char))
        time.sleep(speed)

def loop():
    # --- 1. THE ARDUINO LOGO ---
    Bridge.call("display_id", EMOJI_MAP[":logo:"])
    time.sleep(2.5)

    # --- 2. 5 LETTERS ---
    scroll_text("HELLO", speed=0.7)

    # --- 3. 5 EMOJIS ---
    icons = [":smile:", ":dog:", ":heart:", ":scissors:", ":check:"]
    for icon in icons:
        Bridge.call("display_id", EMOJI_MAP[icon])
        time.sleep(1.2)

    # --- 4. THE ANIMATED SPINNER ---
    # Loop 5 times for a smooth rotation effect
    for _ in range(5):
        for frame_id in SPINNER:
            Bridge.call("display_id", frame_id)
            time.sleep(0.1)

    # --- 5. SCROLLABLE WORD ---
    scroll_text("CUTTING", speed=0.5)
    time.sleep(1.0)

# Start the AppLib runner
App.run(user_loop=loop)
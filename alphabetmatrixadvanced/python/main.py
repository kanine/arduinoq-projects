# SPDX-FileCopyrightText: Full Showcase Conductor (Safe Version)
# SPDX-License-Identifier: MPL-2.0

from arduino.app_utils import *
import time

EMOJI_MAP = {
    ":house:": 128, ":check:": 129, ":cross:": 130, ":heart:": 131, 
    ":smile:": 132, ":dog:": 136, ":logo:": 140, ":scissors:": 145,
    ":warning:": 146, ":stop:": 147, ":gear:": 148
}
SPINNER = [141, 142, 143, 144]

def send_display_id(value):
    """Best-effort display call that tolerates temporary bridge disconnects."""
    try:
        Bridge.call("display_id", value)
        return True
    except Exception as exc:
        print(f"[bridge] display_id failed ({value}): {exc}")
        return False

def safe_send_icon(shortcode):
    """Checks if the code exists before calling the Bridge."""
    if shortcode in EMOJI_MAP:
        return send_display_id(EMOJI_MAP[shortcode])
    else:
        print(f"Error: {shortcode} is not in the library!")
        # Show the warning icon so you know there's a bug in your script
        return send_display_id(EMOJI_MAP[":warning:"])

def scroll_text(text, speed=0.6):
    for char in text.upper():
        if not send_display_id(ord(char)):
            return False
        time.sleep(speed)
    return True

def loop():
    # 1. Using the safe wrapper for the logo
    if not safe_send_icon(":logo:"):
        time.sleep(0.5)
        return
    time.sleep(2.5)

    # 2. Scroll text (already safe because it uses ord())
    if not scroll_text("HELLO", speed=0.7):
        time.sleep(0.5)
        return

    # 3. Using the safe wrapper for a list of icons
    icons = [":smile:", ":dog:", ":heart:", ":scissors:", ":check:"]
    for icon in icons:
        if not safe_send_icon(icon):
            time.sleep(0.5)
            return
        time.sleep(1.2)

    # 4. The Spinner (using raw IDs is fine since they are hardcoded)
    for _ in range(5):
        for frame_id in SPINNER:
            if not send_display_id(frame_id):
                time.sleep(0.5)
                return
            time.sleep(0.1)

    if not scroll_text("CUTTING", speed=0.5):
        time.sleep(0.5)
        return
    time.sleep(1.0)

App.run(user_loop=loop)

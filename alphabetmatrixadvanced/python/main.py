# SPDX-FileCopyrightText: Full Showcase Conductor (Safe Version)
# SPDX-License-Identifier: MPL-2.0

from arduino.app_utils import *
import time
import os
import re

EMOJI_MAP = {
    ":house:": 128, ":check:": 129, ":cross:": 130, ":heart:": 131, 
    ":smile:": 132, ":dog:": 136, ":logo:": 140, ":scissors:": 145,
    ":warning:": 146, ":stop:": 147, ":gear:": 148
}
SPINNER = [141, 142, 143, 144]

_alphabet_font = None

def get_alphabet_font():
    global _alphabet_font
    if _alphabet_font is not None:
        return _alphabet_font
    
    font_path = os.path.join(os.path.dirname(__file__), '../sketch/font.h')
    with open(font_path, 'r') as f:
        text = f.read()

    match = re.search(r'ALPHABET_FONT[^=]+=\s*\{([^;]+)\};', text, re.DOTALL)
    if not match:
        raise ValueError("Could not find ALPHABET_FONT")
    
    block = match.group(1)
    _alphabet_font = []
    for inner in re.finditer(r'\{([^\}]+)\}', block, re.DOTALL):
        nums = [int(x.strip()) for x in inner.group(1).split(',') if x.strip() != '']
        if len(nums) == 104:
            rows = [nums[i*13:(i+1)*13] for i in range(8)]
            _alphabet_font.append(rows)
    return _alphabet_font

def crop_character(char_idx):
    matrix2d = get_alphabet_font()[char_idx]
    min_c = 13
    max_c = -1
    for r in range(8):
        for c in range(13):
            if matrix2d[r][c] > 0:
                min_c = min(min_c, c)
                max_c = max(max_c, c)
    
    if max_c == -1: 
        return [[0]*4 for _ in range(8)]
    
    res = []
    for r in range(8):
        res.append(matrix2d[r][min_c:max_c+1])
    return res

def send_display_frame(frame):
    try:
        Bridge.notify("display_frame", bytes(frame))
        return True
    except Exception as exc:
        print(f"[bridge] display_frame failed: {exc}")
        return False

def send_display_id(value):
    """Best-effort display call that handles high-frequency updates via notify."""
    try:
        Bridge.notify("display_id", value)
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
        return send_display_id(EMOJI_MAP[":warning:"])

def scroll_text(text, speed=0.6):
    buffer = [[] for _ in range(8)]
    
    for char in text.upper():
        if 'A' <= char <= 'Z':
            idx = ord(char) - ord('A')
            lines = crop_character(idx)
        else:
            lines = [[0]*4 for _ in range(8)]
        
        for r in range(8):
            buffer[r].extend(lines[r])
            buffer[r].append(0) # 1 pixel spacing between letters
            
    pad = [0]*13
    for r in range(8):
        buffer[r] = pad + buffer[r] + pad
        
    width = len(buffer[0])
    delay = speed / 13.0
    
    for offset in range(width - 13 + 1):
        frame = []
        for r in range(8):
            frame.extend(buffer[r][offset:offset+13])
        if not send_display_frame(frame):
            return False
        time.sleep(delay)
    return True

def loop():
    # 1. Using the safe wrapper for the logo
    if not safe_send_icon(":logo:"):
        time.sleep(0.5)
        return
    time.sleep(2.5)

    # 2. Scroll text
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

    # 4. The Spinner
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


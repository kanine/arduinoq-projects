# 🅰️ Alphabet Matrix Advanced App for Arduino Uno Q

An advanced character and icon-rendering application designed specifically for the **Arduino Uno Q**. This application displays scrolling text, emojis, and animations on the integrated 8x13 blue LED matrix using a dual-processor architecture.

---

## Architecture Overview

The application utilizes the Uno Q's **Dual-Processor Bridge Architecture** out of the box.

*   **Microprocessor (MPU) - Python**: A Python script (`main.py`) running on the Qualcomm Linux side acts as the conductor. It orchestrates the sequence of emojis, text, and animations, pushing light-weight frame IDs across the `Bridge`.
*   **Microcontroller (MCU) - C++**: The STM32 microcontroller runs `sketch.ino`. It receives frame IDs from the Bridge, performs a high-speed memory copy of the corresponding 104-byte font pattern from `font.h` into a local buffer, and drives the IS31 LED matrix hardware.
*   **LED Driver (IS31)**: Controlled via the `Arduino_LED_Matrix` library, initialized in **3-bit Grayscale Mode** (8 levels of brightness per pixel).
*   **Font Engine**: A custom `font.h` containing `ALPHABET_FONT` and `ICON_FONT` arrays, mapping human-readable patterns directly to physical LED coordinates.

---

## Technical Specifications

*   **Matrix Dimensions**: 8 Rows x 13 Columns (104 total LEDs).
*   **Color Depth**: 3-bit Grayscale (0 = Off, 7 = Max Brightness).
*   **Refresh Logic**: Manual frame loading via `matrix.draw()` to ensure zero "ghosting" or diagonal distortion.
*   **Memory Management**: Font patterns are stored in the MCU's Program Space (Flash) to preserve RAM.

---

## Installation & Setup

### Prerequisites
*   **Hardware**: Arduino Uno Q.
*   **CLI**: `arduino-app-cli` (or `arduino-app`) installed on your system.

### Configuration
1.  **No External Components Required**: This app uses only the built-in LED matrix. 
2.  **MPU Power**: Ensure the **MPU_PWR** slide switch on the board is **ON**.

### Deployment
Use the Arduino App CLI to start the application:

```bash
arduino-app run /home/kanine/ArduinoProjects/alphabetmatrixadvanced
# OR
arduino-app-cli app start /home/kanine/ArduinoProjects/alphabetmatrixadvanced
```

To stop the app:
```bash
arduino-app-cli app stop /home/kanine/ArduinoProjects/alphabetmatrixadvanced
```

---

## Application Logic

### Python Orchestration (`main.py`)
The Python script defines sequences and timings, sending simple byte/int IDs to the MCU via the Bridge:

```python
def scroll_text(text, speed=0.6):
    for char in text.upper():
        Bridge.notify("display_id", ord(char))
        time.sleep(speed)
```

### MCU Rendering (`sketch.ino`)
The MCU exposes a `display_id` callback over the Bridge. When a new ID arrives, it resolves it to either an icon or a letter, and pushes it to the display.

```cpp
void handleMatrix(int id) {
  uint8_t frame[104] = {0};

  if (id >= 128 && id <= 148) { 
    int iconIdx = id - 128;
    memcpy(frame, ICON_FONT[iconIdx], 104);
  } else if (id >= 'A' && id <= 'Z') {
    int letterIdx = id - 'A';
    memcpy(frame, ALPHABET_FONT[letterIdx], 104);
  }
  
  matrix.draw(frame);
}
```

---

## Credits & Acknowledgments

This application’s rendering logic and grayscale initialization were derived from the LED Matrix Painter example provided by Arduino SRL. Special thanks to that project for documenting the `setGrayscaleBits(3)` requirement and the 104-byte `draw()` sequence necessary for the Uno Q hardware.
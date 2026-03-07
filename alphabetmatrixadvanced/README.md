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
The Python script defines sequences and timings. It sends two types of payloads across the Bridge to the C++ sketch:
1.  **Icon IDs (`display_id`)**: Simple integer IDs for hardcoded shapes built into the C++ `ICON_FONT` header.
2.  **Raw Frames (`display_frame`)**: The `scroll_text` function dynamically reads the `ALPHABET_FONT` directly from the C++ `font.h` header, crops the characters, and builds a large memory-padded structure. As the text scrolls right-to-left like a stock ticker, the Python script uses array slicing to chunk the current viewport into a 104-byte array and sends it over to the microcontroller.

```python
def scroll_text(text, speed=0.6):
    # Calculates a sliding window across cropped and spaced alphabet letters
    # Pushes exact 104-byte frames to the C++ MCU to render right-to-left
    Bridge.notify("display_frame", bytes(frame))
```

### MCU Rendering (`sketch.ino`)
The MCU exposes dual callbacks over the Bridge. `handleMatrix(int id)` renders predefined static arrays, while the new `handleFrame(std::vector<uint8_t> frame)` accepts streaming pixel arrays for dynamic animations.

```cpp
void handleFrame(std::vector<uint8_t> frame) {
  if (frame.size() == 104) {
    matrix.draw(frame.data());
  }
}
```

---

## Credits & Acknowledgments

This application’s rendering logic and grayscale initialization were derived from the LED Matrix Painter example provided by Arduino SRL. Special thanks to that project for documenting the `setGrayscaleBits(3)` requirement and the 104-byte `draw()` sequence necessary for the Uno Q hardware.
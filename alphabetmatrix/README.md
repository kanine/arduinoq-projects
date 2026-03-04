# 🅰️ Alphabet Matrix App for Arduino Uno Q

A standalone character-rendering application designed specifically for the **Arduino Uno Q** (October 2025 Release). This application displays a 1-second cycling sequence of the English alphabet on the integrated 8x13 blue LED matrix using a custom-built 104-byte grayscale font engine.

---

## Architecture Overview

The application utilizes a **Dual-Processor Bridge Architecture**. While the Uno Q contains a Qualcomm Linux MPU, this specific version of the app is engineered to run as a high-performance standalone service on the **STM32 Microcontroller (MCU)** side.

### Component Breakdown

* **Microcontroller (MCU)**: Executes the real-time display logic, handles the frame-buffer timing, and manages I2C communication with the LED driver.
* **LED Driver (IS31)**: Controlled via the `Arduino_LED_Matrix` library. It is initialized in **3-bit Grayscale Mode**, allowing for 8 levels of brightness (0-7) per pixel.
* **Font Engine**: A custom `font.h` header containing a static 2D array. This maps human-readable 8x13 grids directly to the physical LED coordinates.



---

## Technical Specifications

* **Matrix Dimensions**: 8 Rows x 13 Columns (104 total LEDs).
* **Color Depth**: 3-bit Grayscale (0 = Off, 7 = Max Brightness).
* **Refresh Logic**: Manual frame loading via `matrix.draw()` to ensure zero "ghosting" or diagonal distortion.
* **Memory Management**: Font data is stored in Program Space (Flash) via `static const` definitions to preserve MCU RAM.

---

## Installation & Setup

### Prerequisites
* **Hardware**: Arduino Uno Q (2025 Revision).
* **Software**: Arduino App Lab or Arduino IDE with the **Arduino Qualcomm Core** (v0.53.1 or higher).

### Configuration
1. **No External Components Required**: This demo uses only the built-in LED matrix. You do not need breadboards, resistors, or external sensors to run this alphabet sequence.
2. **MPU Power**: Ensure the **MPU_PWR** slide switch on the board is set to **ON**, as the Linux side provides the power rail for the matrix peripherals.

### Deployment
1. Create a new project in your IDE.
2. Add a `font.h` file containing the `ALPHABET_FONT[26][104]` array.
3. Upload the `sketch.ino`. The board will immediately begin cycling through A-Z at 1Hz.

---

## Application Logic (`sketch.ino`)

The core loop iterates through ASCII characters 'A' through 'Z'. The `drawLetter()` function performs a high-speed `memcpy` of the 104-byte font segment from `font.h` into a local frame buffer before pushing it to the hardware.

```cpp
void drawLetter(char l) {
  uint8_t frame[FONT_FRAME_SIZE] = {0}; 
  
  if (l >= 'A' && l <= 'Z') {
    const uint8_t letterIndex = static_cast<uint8_t>(l - 'A');
    // Copies the 104-byte pattern from the font table
    memcpy(frame, ALPHABET_FONT[letterIndex], FONT_FRAME_SIZE);
  }
  
  // Renders the buffer using the validated Uno Q draw method
  matrix.draw(frame);
}
```

## Credits & Acknowledgments

This application’s rendering logic and grayscale initialization were derived from the LED Matrix Painter example provided by Arduino SRL. Special thanks to that project for documenting the setGrayscaleBits(3) requirement and the 104-byte draw() sequence necessary for the Uno Q hardware.
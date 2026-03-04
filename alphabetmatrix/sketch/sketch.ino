#include <Arduino_LED_Matrix.h>
#include <string.h>

#include "font.h"

Arduino_LED_Matrix matrix;

// Draw a single uppercase letter (A-Z) from the external font table.
void drawLetter(char l);

void setup() {
  matrix.begin();
  // Matching the LED Painter's required 3-bit initialization
  matrix.setGrayscaleBits(3);
  matrix.clear();
  Serial.begin(115200);
}

void loop() {
  // This loop will cycle through the entire alphabet A-Z
  for (char c = 'A'; c <= 'Z'; c++) {
    drawLetter(c);
    delay(1000); // 1 second per letter
  }
}

void drawLetter(char l) {
  uint8_t frame[FONT_FRAME_SIZE] = {0}; // Start with a blank canvas

  if (l >= 'A' && l <= 'Z') {
    const uint8_t letterIndex = static_cast<uint8_t>(l - 'A');
    memcpy(frame, ALPHABET_FONT[letterIndex], FONT_FRAME_SIZE);
  }

  matrix.draw(frame);
}

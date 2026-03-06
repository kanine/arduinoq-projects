#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>
#include "font.h"

Arduino_LED_Matrix matrix;

// Callback function for Python
void handleMatrix(int id);

void setup() {
  matrix.begin();
  matrix.setGrayscaleBits(3);
  matrix.clear();

  // Initialize bridge and register the display function
  Bridge.begin();
  Bridge.provide("display_id", handleMatrix);
}

void loop() {
  // Let the loop run at full speed for best Bridge performance
}

void handleMatrix(int id) {
  uint8_t frame[96] = {0}; // Standard 12x8 grayscale frame

  if (id >= 128 && id <= 148) { 
    int iconIdx = id - 128;
    // Copy the first 96 bytes (aligned to 12x8 pixels)
    memcpy(frame, ICON_FONT[iconIdx], 96);
  } 
  else if (id >= 'A' && id <= 'Z') {
    int letterIdx = id - 'A';
    memcpy(frame, ALPHABET_FONT[letterIdx], 96);
  }
  
  matrix.draw(frame);
  // Important: No long delays here, let the loop() handle App.process()
}
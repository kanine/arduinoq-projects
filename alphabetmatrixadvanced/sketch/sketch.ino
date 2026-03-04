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
  // Background processing handled by RouterBridge
}

void handleMatrix(int id) {
  uint8_t frame[104] = {0};

  // Logic: 65-90 = A-Z | 128+ = Icons/Emojis
  if (id >= 128) {
    int iconIdx = id - 128;
    if (iconIdx < 21) { 
      memcpy(frame, ICON_FONT[iconIdx], 104);
    }
  } 
  else if (id >= 'A' && id <= 'Z') {
    int letterIdx = id - 'A';
    memcpy(frame, ALPHABET_FONT[letterIdx], 104);
  }

  matrix.draw(frame);
}
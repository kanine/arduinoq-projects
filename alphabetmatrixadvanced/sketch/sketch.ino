#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>
#include <vector>
#include "font.h"

Arduino_LED_Matrix matrix;

// Callback function for Python
void handleMatrix(int id);
void handleFrame(std::vector<uint8_t> frame);

void setup() {
  matrix.begin();
  matrix.setGrayscaleBits(3);
  matrix.clear();

  // Initialize bridge and register the display function
  Bridge.begin();
  Bridge.provide("display_id", handleMatrix);
  Bridge.provide("display_frame", handleFrame);
}

void loop() {
  // Let the loop run at full speed for best Bridge performance
}

void handleMatrix(int id) {
  uint8_t frame[104] = {0}; // Uno Q standard 13x8 grayscale frame

  if (id >= 128 && id <= 148) { 
    int iconIdx = id - 128;
    memcpy(frame, ICON_FONT[iconIdx], 104);
  } 
  else if (id >= 'A' && id <= 'Z') {
    int letterIdx = id - 'A';
    memcpy(frame, ALPHABET_FONT[letterIdx], 104);
  }
  
  matrix.draw(frame);
  // Important: No long delays here, let the loop() handle App.process()
}

void handleFrame(std::vector<uint8_t> frame) {
  if (frame.size() == 104) {
    matrix.draw(frame.data());
  }
}
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
  // IMPORTANT: This 1ms delay prevents the "Broken Pipe" error
  // by giving the background Bridge service time to process messages.
  delay(1);
}

void handleMatrix(int id) {
  uint8_t frame[104] = {0};

  if (id >= 128 && id <= 148) { 
    int iconIdx = id - 128;
    // CRITICAL: Ensure iconIdx doesn't exceed your ICON_FONT size
    memcpy(frame, ICON_FONT[iconIdx], 104);
  } 
  else if (id >= 'A' && id <= 'Z') {
    int letterIdx = id - 'A';
    memcpy(frame, ALPHABET_FONT[letterIdx], 104);
  }
  
  matrix.draw(frame);
  // Important: No long delays here, let the loop() handle App.process()
}
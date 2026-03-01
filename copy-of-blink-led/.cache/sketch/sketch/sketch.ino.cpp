#include <Arduino.h>
#line 1 "/home/arduino/ArduinoApps/copy-of-blink-led/sketch/sketch.ino"
#include <Arduino_AppLib.h> // Ensure this library is included

void setup() {
  // Initialize the App communication first
  App.begin(); 
  
  pinMode(LED3_R, OUTPUT);
  pinMode(LED3_G, OUTPUT);
  
  // Now register the function
  App.registerFunction("set_green_led", handleGreenLED);
  
  // Ensure Red is off (active low check might be needed)
  digitalWrite(LED3_R, LOW); 
}

void loop() {
  // App.process() keeps the bridge alive
  App.process(); 
}

// Function to handle the Python call
void handleGreenLED(bool state) {
  digitalWrite(LED3_G, state ? HIGH : LOW);
}

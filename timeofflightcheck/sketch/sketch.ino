#include "Arduino_RouterBridge.h"
#include "Wire.h"
#include "Adafruit_VL53L1X.h"

Adafruit_VL53L1X vl53;

void setup() {
  Bridge.begin();
  Wire.begin();
  vl53.begin(0x29, &Wire);
  vl53.startRanging();
  vl53.setTimingBudget(50);
  Bridge.provide("get_distance", get_distance);
}

void loop() {}

int get_distance() {
  if (vl53.dataReady()) {
    int16_t d = vl53.distance();
    vl53.clearInterrupt();
    return d;
  }
  return -1;
}
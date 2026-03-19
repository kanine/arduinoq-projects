#include "Arduino_RouterBridge.h"
#include <Wire.h>
#include <VL53L1X.h>

VL53L1X sensor;
int16_t lastDistance = -1;
bool sensorReady = false;

int get_distance() {
  return lastDistance;
}

void setup() {
  Bridge.begin();
  Bridge.provide("get_distance", get_distance);
  Wire1.begin();
  Wire1.setClock(400000);
}

void loop() {
  if (!sensorReady) {
    Wire1.beginTransmission(0x29);
    if (Wire1.endTransmission() != 0) {
      delay(500);
      return;
    }
    sensor.setBus(&Wire1);
    sensor.setTimeout(200);
    if (!sensor.init()) {
      delay(500);
      return;
    }
    sensor.setDistanceMode(VL53L1X::Long);
    sensor.setMeasurementTimingBudget(50000);
    sensor.startContinuous(50);
    sensorReady = true;
  }

  if (sensor.dataReady()) {
    lastDistance = sensor.read(false);
  }
  delay(10);
}

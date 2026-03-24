#include "Arduino_RouterBridge.h"
#include <Wire.h>
#include <VL53L1X.h>

VL53L1X sensor;
int16_t lastDistance = -1;
bool sensorReady = false;

// Non-blocking blink state: millis() timestamp when LEDs should turn off (0 = idle).
static unsigned long blinkOffAt = 0;

int get_distance() {
  return lastDistance;
}

// Blink LED3_R and LED4_R once to signal a failed POST.
// LED3/4 are active low: LOW = ON, HIGH = OFF.
// Uses non-blocking timing — turn-off is handled in loop().
void blink_red() {
  digitalWrite(LED3_R, LOW);
  digitalWrite(LED4_R, LOW);
  blinkOffAt = millis() + 120;
}

void setup() {
  pinMode(LED3_R, OUTPUT);
  digitalWrite(LED3_R, HIGH);
  pinMode(LED4_R, OUTPUT);
  digitalWrite(LED4_R, HIGH);

  Bridge.begin();
  Bridge.provide("get_distance", get_distance);
  Bridge.provide_safe("blink_red", blink_red);
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
    sensor.setDistanceMode(VL53L1X::Short);
    sensor.setMeasurementTimingBudget(50000);
    sensor.startContinuous(50);
    sensorReady = true;
  }

  if (sensor.dataReady()) {
    lastDistance = sensor.read(false);
  }

  if (blinkOffAt && millis() >= blinkOffAt) {
    digitalWrite(LED3_R, HIGH);
    digitalWrite(LED4_R, HIGH);
    blinkOffAt = 0;
  }

  delay(10);
}

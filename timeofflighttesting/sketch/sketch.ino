#include "Arduino_RouterBridge.h"
#include <Wire.h>
#include <VL53L1X.h>
#include "sensor_config.h"  // auto-generated from config.json via gen_sensor_config.py

VL53L1X sensor;
bool sensorReady = false;

// Last sensor reading — updated in loop()
static int16_t  lastDistance   = -1;
static int8_t   lastStatus     = -1;
static int16_t  lastSignalX100  = 0;   // peak_signal_count_rate_MCPS * 100
static int16_t  lastAmbientX100 = 0;   // ambient_count_rate_MCPS * 100

// Non-blocking blink state
static unsigned long blinkOffAt = 0;

int get_distance()    { return lastDistance; }
int get_range_status(){ return lastStatus; }
int get_signal_x100() { return lastSignalX100; }
int get_ambient_x100(){ return lastAmbientX100; }

void blink_red() {
  digitalWrite(LED3_R, LOW);
  digitalWrite(LED4_R, LOW);
  blinkOffAt = millis() + 120;
}

void setup() {
  pinMode(LED3_R, OUTPUT); digitalWrite(LED3_R, HIGH);
  pinMode(LED4_R, OUTPUT); digitalWrite(LED4_R, HIGH);

  Bridge.begin();
  Bridge.provide("get_distance",    get_distance);
  Bridge.provide("get_range_status", get_range_status);
  Bridge.provide("get_signal_x100", get_signal_x100);
  Bridge.provide("get_ambient_x100",get_ambient_x100);
  Bridge.provide_safe("blink_red",  blink_red);

  Wire1.begin();
  Wire1.setClock(400000);
}

void loop() {
  if (!sensorReady) {
    Wire1.beginTransmission(0x29);
    if (Wire1.endTransmission() != 0) { delay(500); return; }

    sensor.setBus(&Wire1);
    sensor.setTimeout(200);
    if (!sensor.init()) { delay(500); return; }

    sensor.setDistanceMode(SENSOR_DISTANCE_MODE);
    sensor.setMeasurementTimingBudget(SENSOR_TIMING_BUDGET_US);
    sensor.setROISize(SENSOR_ROI_WIDTH, SENSOR_ROI_HEIGHT);
    sensor.setROICenter(SENSOR_ROI_CENTER);
    sensor.startContinuous(SENSOR_INTER_MEASUREMENT_MS);
    sensorReady = true;
  }

  if (sensor.dataReady()) {
    sensor.read(false);
    lastDistance    = sensor.ranging_data.range_mm;
    lastStatus      = (int8_t)sensor.ranging_data.range_status;
    lastSignalX100  = (int16_t)(sensor.ranging_data.peak_signal_count_rate_MCPS * 100.0f);
    lastAmbientX100 = (int16_t)(sensor.ranging_data.ambient_count_rate_MCPS    * 100.0f);
  }

  if (blinkOffAt && millis() >= blinkOffAt) {
    digitalWrite(LED3_R, HIGH);
    digitalWrite(LED4_R, HIGH);
    blinkOffAt = 0;
  }

  delay(10);
}

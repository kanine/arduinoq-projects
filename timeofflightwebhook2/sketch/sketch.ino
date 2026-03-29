#include "Arduino_RouterBridge.h"
#include <Wire.h>
#include <VL53L1X.h>
#include "sensor_config.h"  // initial values from config.json via gen_sensor_config.py

VL53L1X sensor;
bool sensorReady = false;

// Last sensor reading — updated in loop()
static int16_t  lastDistance    = -1;
static int8_t   lastStatus      = -1;
static int16_t  lastSignalX100  = 0;
static int16_t  lastAmbientX100 = 0;

// Pending sensor reconfiguration — set by apply_sensor_config(), applied in loop()
static bool     pendingReconfig  = false;
static uint8_t  pendingMode      = SENSOR_DISTANCE_MODE;
static uint32_t pendingBudgetUs  = SENSOR_TIMING_BUDGET_US;
static uint32_t pendingImpMs     = SENSOR_INTER_MEASUREMENT_MS;
static uint8_t  pendingRoiW      = SENSOR_ROI_WIDTH;
static uint8_t  pendingRoiH      = SENSOR_ROI_HEIGHT;
static uint8_t  pendingRoiCenter = SENSOR_ROI_CENTER;

// Non-blocking blink state
static unsigned long blinkOffAt = 0;

int get_distance()     { return lastDistance; }
int get_range_status() { return lastStatus; }
int get_signal_x100()  { return lastSignalX100; }
int get_ambient_x100() { return lastAmbientX100; }

// Called by Python when the server pushes updated sensor config.
// mode: 1=Short, 2=Medium, 3=Long  (matches VL53L1X DistanceMode enum)
// budget_ms: timing budget in milliseconds
// imp_ms: inter-measurement period in milliseconds (must be >= budget_ms)
// roi_w, roi_h: ROI dimensions, 4-16 each
// roi_center: SPAD index 0-255
bool apply_sensor_config(int mode, int budget_ms, int imp_ms,
                         int roi_w, int roi_h, int roi_center) {
    pendingMode      = (uint8_t)mode;
    pendingBudgetUs  = (uint32_t)budget_ms * 1000;
    pendingImpMs     = (uint32_t)imp_ms;
    pendingRoiW      = (uint8_t)roi_w;
    pendingRoiH      = (uint8_t)roi_h;
    pendingRoiCenter = (uint8_t)roi_center;
    pendingReconfig  = true;
    return true;
}

void blink_green() {
    digitalWrite(LED3_G, LOW);
    digitalWrite(LED4_G, LOW);
    blinkOffAt = millis() + 120;
}

void blink_orange() {
    digitalWrite(LED3_R, LOW);
    digitalWrite(LED3_G, LOW);
    digitalWrite(LED4_R, LOW);
    digitalWrite(LED4_G, LOW);
    blinkOffAt = millis() + 500;
}

void blink_red() {
    digitalWrite(LED3_R, LOW);
    digitalWrite(LED4_R, LOW);
    blinkOffAt = millis() + 120;
}

void setup() {
    pinMode(LED3_R, OUTPUT); digitalWrite(LED3_R, HIGH);
    pinMode(LED4_R, OUTPUT); digitalWrite(LED4_R, HIGH);
    pinMode(LED3_G, OUTPUT); digitalWrite(LED3_G, HIGH);
    pinMode(LED4_G, OUTPUT); digitalWrite(LED4_G, HIGH);

    Bridge.begin();
    Bridge.provide("get_distance",             get_distance);
    Bridge.provide("get_range_status",         get_range_status);
    Bridge.provide("get_signal_x100",          get_signal_x100);
    Bridge.provide("get_ambient_x100",         get_ambient_x100);
    Bridge.provide_safe("apply_sensor_config", apply_sensor_config);
    Bridge.provide_safe("blink_green",         blink_green);
    Bridge.provide_safe("blink_orange",        blink_orange);
    Bridge.provide_safe("blink_red",           blink_red);

    Wire1.begin();
    Wire1.setClock(400000);

    // Startup confirmation: red → orange → green
    digitalWrite(LED3_R, LOW);  digitalWrite(LED4_R, LOW);
    delay(750);
    digitalWrite(LED3_R, HIGH); digitalWrite(LED4_R, HIGH);
    delay(200);
    digitalWrite(LED3_R, LOW);  digitalWrite(LED3_G, LOW);
    digitalWrite(LED4_R, LOW);  digitalWrite(LED4_G, LOW);
    delay(750);
    digitalWrite(LED3_R, HIGH); digitalWrite(LED3_G, HIGH);
    digitalWrite(LED4_R, HIGH); digitalWrite(LED4_G, HIGH);
    delay(200);
    digitalWrite(LED3_G, LOW);  digitalWrite(LED4_G, LOW);
    delay(750);
    digitalWrite(LED3_G, HIGH); digitalWrite(LED4_G, HIGH);
}

void loop() {
    if (!sensorReady) {
        Wire1.beginTransmission(0x29);
        if (Wire1.endTransmission() != 0) { delay(500); return; }

        sensor.setBus(&Wire1);
        sensor.setTimeout(200);
        if (!sensor.init()) { delay(500); return; }

        sensor.setDistanceMode((VL53L1X::DistanceMode)pendingMode);
        sensor.setMeasurementTimingBudget(pendingBudgetUs);
        sensor.setROISize(pendingRoiW, pendingRoiH);
        sensor.setROICenter(pendingRoiCenter);
        sensor.startContinuous(pendingImpMs);
        sensorReady = true;
    }

    // Apply a server-pushed sensor config change
    if (pendingReconfig && sensorReady) {
        sensor.stopContinuous();
        sensor.setDistanceMode((VL53L1X::DistanceMode)pendingMode);
        sensor.setMeasurementTimingBudget(pendingBudgetUs);
        sensor.setROISize(pendingRoiW, pendingRoiH);
        sensor.setROICenter(pendingRoiCenter);
        sensor.startContinuous(pendingImpMs);
        pendingReconfig = false;
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
        digitalWrite(LED3_G, HIGH);
        digitalWrite(LED4_G, HIGH);
        blinkOffAt = 0;
    }

    delay(10);
}

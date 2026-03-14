// SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
//
// SPDX-License-Identifier: MPL-2.0

#include <Arduino_RouterBridge.h>
#include <Wire.h>
#include <VL53L1X.h>

// Hardware topology — proven via timeofflightconfig 2026-03-14
#define XSHUT_1  3      // D3 (PB0) → Sensor 1 XSHUT
#define XSHUT_2  4      // D4 (PA12) → Sensor 2 XSHUT
#define ADDR_1   0x30   // Sensor 1 assigned address
#define ADDR_2   0x31   // Sensor 2 assigned address

const int DEFAULT_THRESHOLD_MM       = 250;
const int MIN_THRESHOLD_MM           = 30;
const int MAX_THRESHOLD_MM           = 4000;
const uint16_t TIMING_BUDGET_MS      = 40;
const unsigned long POLL_INTERVAL_MS = 40;
const uint16_t SENSOR_TIMEOUT_MS     = 200;
const unsigned long STALE_TIMEOUT_MS = 3000; // reinit if no new reading for 3 s

enum FaultCode {
  FAULT_NONE            = 0,
  FAULT_NOT_INITIALIZED = 1,
  FAULT_NO_I2C_ACK      = 2,
  FAULT_INIT_FAILED     = 3,
  FAULT_TIMING_BUDGET   = 4,
  FAULT_READ_TIMEOUT    = 5,
  FAULT_RANGE_STATUS    = 6
};

VL53L1X s1, s2;

// Sensor 1 state
bool s1Online        = false;
bool s1DataReady     = false;
bool s1ObjectPresent = false;
int  s1ThresholdMM   = DEFAULT_THRESHOLD_MM;
int  s1DistanceMM    = -1;
unsigned long s1LastReadMS = 0;
bool s1I2cSeen       = false;
int  s1InitStage     = 0;
int  s1FaultCode     = FAULT_NOT_INITIALIZED;

// Sensor 2 state
bool s2Online        = false;
bool s2DataReady     = false;
bool s2ObjectPresent = false;
int  s2ThresholdMM   = DEFAULT_THRESHOLD_MM;
int  s2DistanceMM    = -1;
unsigned long s2LastReadMS = 0;
bool s2I2cSeen       = false;
int  s2InitStage     = 0;
int  s2FaultCode     = FAULT_NOT_INITIALIZED;

// Bridge functions — must be defined before setup()
int get_s1_online()          { return s1Online ? 1 : 0; }
int get_s1_distance_mm()     { return s1DistanceMM; }
int get_s1_data_ready()      { return s1DataReady ? 1 : 0; }
int get_s1_threshold_mm()    { return s1ThresholdMM; }
int get_s1_object_present()  { return s1ObjectPresent ? 1 : 0; }
int get_s1_i2c_seen()        { return s1I2cSeen ? 1 : 0; }
int get_s1_init_stage()      { return s1InitStage; }
int get_s1_fault_code()      { return s1FaultCode; }
unsigned long get_s1_last_read_ms() { return s1LastReadMS; }

int get_s2_online()          { return s2Online ? 1 : 0; }
int get_s2_distance_mm()     { return s2DistanceMM; }
int get_s2_data_ready()      { return s2DataReady ? 1 : 0; }
int get_s2_threshold_mm()    { return s2ThresholdMM; }
int get_s2_object_present()  { return s2ObjectPresent ? 1 : 0; }
int get_s2_i2c_seen()        { return s2I2cSeen ? 1 : 0; }
int get_s2_init_stage()      { return s2InitStage; }
int get_s2_fault_code()      { return s2FaultCode; }
unsigned long get_s2_last_read_ms() { return s2LastReadMS; }

int get_tof_timing_budget_ms() { return TIMING_BUDGET_MS; }

// Triggered by web reset button — re-runs full XSHUT sequence.
// Must be provide_safe (touches GPIO).
int reset_sensors() {
  s1Online = false; s2Online = false;
  initializeSensors();
  return (s1Online && s2Online) ? 1 : 0;
}

int clampThreshold(int v) {
  return max(MIN_THRESHOLD_MM, min(MAX_THRESHOLD_MM, v));
}

int set_s1_threshold(int mm) {
  s1ThresholdMM   = clampThreshold(mm);
  s1ObjectPresent = s1Online && s1DistanceMM >= 0 && s1DistanceMM <= s1ThresholdMM;
  return s1ThresholdMM;
}

int set_s2_threshold(int mm) {
  s2ThresholdMM   = clampThreshold(mm);
  s2ObjectPresent = s2Online && s2DistanceMM >= 0 && s2DistanceMM <= s2ThresholdMM;
  return s2ThresholdMM;
}

bool probeAddress(uint8_t addr) {
  Wire1.beginTransmission(addr);
  return Wire1.endTransmission() == 0;
}

// Sequential XSHUT bring-up — sensor 1 then sensor 2.
// Pattern proven by timeofflightconfig on 2026-03-14.
void initializeSensors() {
  pinMode(XSHUT_1, OUTPUT);
  pinMode(XSHUT_2, OUTPUT);
  digitalWrite(XSHUT_1, LOW);
  digitalWrite(XSHUT_2, LOW);
  delay(10);

  // --- Sensor 1: boot at 0x29, reassign to ADDR_1 ---
  s1InitStage = 0;
  s1FaultCode = FAULT_NOT_INITIALIZED;

  digitalWrite(XSHUT_1, HIGH);
  delay(2);

  s1I2cSeen  = probeAddress(0x29);
  s1InitStage = 1;
  if (!s1I2cSeen) { s1FaultCode = FAULT_NO_I2C_ACK; return; }

  s1.setBus(&Wire1);
  s1.setTimeout(SENSOR_TIMEOUT_MS);
  s1InitStage = 2;
  if (!s1.init()) { s1FaultCode = FAULT_INIT_FAILED; return; }

  s1.setAddress(ADDR_1);
  delay(5);
  s1I2cSeen  = probeAddress(ADDR_1);
  s1InitStage = 3;
  if (!s1I2cSeen) { s1FaultCode = FAULT_NO_I2C_ACK; return; }

  s1.setDistanceMode(VL53L1X::Short);
  s1InitStage = 4;
  if (!s1.setMeasurementTimingBudget((uint32_t)TIMING_BUDGET_MS * 1000UL)) {
    s1FaultCode = FAULT_TIMING_BUDGET; return;
  }
  s1.startContinuous(POLL_INTERVAL_MS);
  s1InitStage = 5;
  s1Online    = true;
  s1FaultCode = FAULT_NONE;

  // --- Sensor 2: boot at 0x29 (now free), reassign to ADDR_2 ---
  s2InitStage = 0;
  s2FaultCode = FAULT_NOT_INITIALIZED;

  digitalWrite(XSHUT_2, HIGH);
  delay(2);

  s2I2cSeen  = probeAddress(0x29);
  s2InitStage = 1;
  if (!s2I2cSeen) { s2FaultCode = FAULT_NO_I2C_ACK; return; }

  s2.setBus(&Wire1);
  s2.setTimeout(SENSOR_TIMEOUT_MS);
  s2InitStage = 2;
  if (!s2.init()) { s2FaultCode = FAULT_INIT_FAILED; return; }

  s2.setAddress(ADDR_2);
  delay(5);
  s2I2cSeen  = probeAddress(ADDR_2);
  s2InitStage = 3;
  if (!s2I2cSeen) { s2FaultCode = FAULT_NO_I2C_ACK; return; }

  s2.setDistanceMode(VL53L1X::Short);
  s2InitStage = 4;
  if (!s2.setMeasurementTimingBudget((uint32_t)TIMING_BUDGET_MS * 1000UL)) {
    s2FaultCode = FAULT_TIMING_BUDGET; return;
  }
  s2.startContinuous(POLL_INTERVAL_MS);
  s2InitStage = 5;
  s2Online    = true;
  s2FaultCode = FAULT_NONE;
}

void setup() {
  Bridge.begin();
  Wire1.begin();
  Wire1.setClock(400000);

  Bridge.provide("get_s1_online",         get_s1_online);
  Bridge.provide("get_s1_distance_mm",    get_s1_distance_mm);
  Bridge.provide("get_s1_data_ready",     get_s1_data_ready);
  Bridge.provide("get_s1_threshold_mm",   get_s1_threshold_mm);
  Bridge.provide("get_s1_object_present", get_s1_object_present);
  Bridge.provide("get_s1_i2c_seen",       get_s1_i2c_seen);
  Bridge.provide("get_s1_init_stage",     get_s1_init_stage);
  Bridge.provide("get_s1_fault_code",     get_s1_fault_code);
  Bridge.provide("get_s1_last_read_ms",   get_s1_last_read_ms);
  Bridge.provide("set_s1_threshold",      set_s1_threshold);

  Bridge.provide("get_s2_online",         get_s2_online);
  Bridge.provide("get_s2_distance_mm",    get_s2_distance_mm);
  Bridge.provide("get_s2_data_ready",     get_s2_data_ready);
  Bridge.provide("get_s2_threshold_mm",   get_s2_threshold_mm);
  Bridge.provide("get_s2_object_present", get_s2_object_present);
  Bridge.provide("get_s2_i2c_seen",       get_s2_i2c_seen);
  Bridge.provide("get_s2_init_stage",     get_s2_init_stage);
  Bridge.provide("get_s2_fault_code",     get_s2_fault_code);
  Bridge.provide("get_s2_last_read_ms",   get_s2_last_read_ms);
  Bridge.provide("set_s2_threshold",      set_s2_threshold);

  Bridge.provide("get_tof_timing_budget_ms", get_tof_timing_budget_ms);
  Bridge.provide_safe("reset_sensors", reset_sensors);

  initializeSensors();
}

void pollSensor(VL53L1X &sensor, bool &online, bool &dataReady,
                bool &objectPresent, int &distanceMM,
                unsigned long &lastReadMS, int &faultCode,
                int thresholdMM, unsigned long now) {
  if (!sensor.dataReady()) {
    dataReady = false;
    return;
  }
  dataReady     = true;
  int dist      = (int)sensor.read(false);

  if (sensor.timeoutOccurred()) {
    // True I2C communication failure — mark offline so reinit runs
    distanceMM    = -1;
    objectPresent = false;
    faultCode     = FAULT_READ_TIMEOUT;
    online        = false;
    return;
  }
  if (sensor.ranging_data.range_status != VL53L1X::RangeValid) {
    // Sensor is ranging but reading is invalid (e.g. object too close for Long mode).
    // Keep online — just report no valid distance this cycle.
    distanceMM    = -1;
    objectPresent = false;
    faultCode     = FAULT_RANGE_STATUS;
    return;
  }
  distanceMM    = dist;
  lastReadMS    = now;
  objectPresent = dist <= thresholdMM;
  faultCode     = FAULT_NONE;
}

// Reinitialise a sensor at its already-assigned address (no XSHUT needed —
// address is retained until power cycle).
bool reinitSensor(VL53L1X &sensor, uint8_t addr,
                  bool &online, bool &dataReady, bool &objectPresent,
                  int &distanceMM, unsigned long &lastReadMS,
                  bool &i2cSeen, int &initStage, int &faultCode) {
  online    = false;
  dataReady = false;
  i2cSeen   = probeAddress(addr);
  initStage = 1;
  if (!i2cSeen) { faultCode = FAULT_NO_I2C_ACK; return false; }

  sensor.setBus(&Wire1);
  sensor.setTimeout(SENSOR_TIMEOUT_MS);
  initStage = 2;
  if (!sensor.init()) { faultCode = FAULT_INIT_FAILED; return false; }

  sensor.setDistanceMode(VL53L1X::Short);
  initStage = 3;
  if (!sensor.setMeasurementTimingBudget((uint32_t)TIMING_BUDGET_MS * 1000UL)) {
    faultCode = FAULT_TIMING_BUDGET; return false;
  }
  sensor.startContinuous(POLL_INTERVAL_MS);
  initStage  = 5;
  online     = true;
  dataReady  = false;
  distanceMM = -1;
  lastReadMS = 0;
  faultCode  = FAULT_NONE;
  return true;
}

void loop() {
  static unsigned long lastPollMS = 0;
  unsigned long now = millis();

  if (now - lastPollMS < POLL_INTERVAL_MS) {
    delay(5);
    return;
  }
  lastPollMS = now;

  // Staleness watchdog — reinit if online but no fresh reading for STALE_TIMEOUT_MS
  if (s1Online && s1LastReadMS > 0 && (now - s1LastReadMS) > STALE_TIMEOUT_MS) {
    s1Online = false;
  }
  if (s2Online && s2LastReadMS > 0 && (now - s2LastReadMS) > STALE_TIMEOUT_MS) {
    s2Online = false;
  }

  if (!s1Online) {
    reinitSensor(s1, ADDR_1, s1Online, s1DataReady, s1ObjectPresent,
                 s1DistanceMM, s1LastReadMS, s1I2cSeen, s1InitStage, s1FaultCode);
  } else {
    pollSensor(s1, s1Online, s1DataReady, s1ObjectPresent,
               s1DistanceMM, s1LastReadMS, s1FaultCode, s1ThresholdMM, now);
  }

  if (!s2Online) {
    reinitSensor(s2, ADDR_2, s2Online, s2DataReady, s2ObjectPresent,
                 s2DistanceMM, s2LastReadMS, s2I2cSeen, s2InitStage, s2FaultCode);
  } else {
    pollSensor(s2, s2Online, s2DataReady, s2ObjectPresent,
               s2DistanceMM, s2LastReadMS, s2FaultCode, s2ThresholdMM, now);
  }

  delay(5);
}

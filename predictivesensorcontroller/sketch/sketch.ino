// SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
//
// SPDX-License-Identifier: MPL-2.0

#include <Arduino_RouterBridge.h>
#include <Wire.h>
#include <VL53L1X.h>

const int XSHUT_PIN = 3;
const bool USE_XSHUT = false;
const int DEFAULT_THRESHOLD_MM = 250;
const int MIN_THRESHOLD_MM = 30;
const int MAX_THRESHOLD_MM = 4000;
const uint16_t TIMING_BUDGET_MS = 50;
const unsigned long POLL_INTERVAL_MS = 60;
const uint16_t SENSOR_TIMEOUT_MS = 200;
const uint8_t SENSOR_ADDRESS = 0x29;

VL53L1X vl53;

bool sensorOnline = false;
bool dataReadyFlag = false;
bool objectPresent = false;
int thresholdMM = DEFAULT_THRESHOLD_MM;
int lastDistanceMM = -1;
unsigned long lastReadMS = 0;
bool i2cAddressSeen = false;
unsigned long lastScanMS = 0;
int lastInitStage = 0;
int faultCode = 1;
String faultMessage = "Sensor not initialized";

enum FaultCode {
  FAULT_NONE = 0,
  FAULT_NOT_INITIALIZED = 1,
  FAULT_NO_I2C_ACK = 2,
  FAULT_INIT_FAILED = 3,
  FAULT_TIMING_BUDGET = 4,
  FAULT_READ_TIMEOUT = 5,
  FAULT_RANGE_STATUS = 6
};

int clampThreshold(int value) {
  if (value < MIN_THRESHOLD_MM) {
    return MIN_THRESHOLD_MM;
  }
  if (value > MAX_THRESHOLD_MM) {
    return MAX_THRESHOLD_MM;
  }
  return value;
}

void setFault(int code, const String &message) {
  faultCode = code;
  faultMessage = message;
  sensorOnline = false;
  dataReadyFlag = false;
  objectPresent = false;
}

bool probeAddress(uint8_t address) {
  Wire.beginTransmission(address);
  return Wire.endTransmission() == 0;
}

void refreshI2CDiagnostics() {
  i2cAddressSeen = probeAddress(SENSOR_ADDRESS);
  lastScanMS = millis();
}

bool initializeSensor() {
  if (USE_XSHUT) {
    pinMode(XSHUT_PIN, OUTPUT);
    digitalWrite(XSHUT_PIN, LOW);
    delay(10);
    digitalWrite(XSHUT_PIN, HIGH);
    delay(10);
  }

  Wire.begin();
  refreshI2CDiagnostics();
  lastInitStage = 1;

  if (!i2cAddressSeen) {
    setFault(FAULT_NO_I2C_ACK, "No I2C ACK at 0x29");
    return false;
  }

  vl53.setBus(&Wire);
  vl53.setTimeout(SENSOR_TIMEOUT_MS);
  lastInitStage = 2;

  if (!vl53.init()) {
    setFault(FAULT_INIT_FAILED, "VL53L1X init failed at 0x29");
    return false;
  }

  lastInitStage = 3;
  vl53.setDistanceMode(VL53L1X::Long);
  if (!vl53.setMeasurementTimingBudget((uint32_t)TIMING_BUDGET_MS * 1000UL)) {
    setFault(FAULT_TIMING_BUDGET, "VL53L1X rejected timing budget");
    return false;
  }
  lastInitStage = 4;
  vl53.startContinuous(POLL_INTERVAL_MS);
  lastInitStage = 5;

  sensorOnline = true;
  dataReadyFlag = false;
  objectPresent = false;
  lastDistanceMM = -1;
  lastReadMS = 0;
  faultCode = FAULT_NONE;
  faultMessage = "";
  return true;
}

int get_tof_online() { return sensorOnline ? 1 : 0; }
int get_tof_distance_mm() { return lastDistanceMM; }
int get_tof_data_ready() { return dataReadyFlag ? 1 : 0; }
int get_tof_threshold_mm() { return thresholdMM; }
int get_tof_object_present() { return objectPresent ? 1 : 0; }
int get_tof_timing_budget_ms() { return TIMING_BUDGET_MS; }
unsigned long get_tof_last_read_ms() { return lastReadMS; }
int get_tof_i2c_address_seen() { return i2cAddressSeen ? 1 : 0; }
unsigned long get_tof_last_scan_ms() { return lastScanMS; }
int get_tof_init_stage() { return lastInitStage; }
int get_tof_fault_code() { return faultCode; }

int set_tof_test_config(int newThresholdMM) {
  thresholdMM = clampThreshold(newThresholdMM);
  objectPresent = sensorOnline && lastDistanceMM >= 0 && lastDistanceMM <= thresholdMM;
  return thresholdMM;
}

void setup() {
  Bridge.begin();

  Bridge.provide("get_tof_online", get_tof_online);
  Bridge.provide("get_tof_distance_mm", get_tof_distance_mm);
  Bridge.provide("get_tof_data_ready", get_tof_data_ready);
  Bridge.provide("get_tof_threshold_mm", get_tof_threshold_mm);
  Bridge.provide("get_tof_object_present", get_tof_object_present);
  Bridge.provide("get_tof_timing_budget_ms", get_tof_timing_budget_ms);
  Bridge.provide("get_tof_last_read_ms", get_tof_last_read_ms);
  Bridge.provide("get_tof_i2c_address_seen", get_tof_i2c_address_seen);
  Bridge.provide("get_tof_last_scan_ms", get_tof_last_scan_ms);
  Bridge.provide("get_tof_init_stage", get_tof_init_stage);
  Bridge.provide("get_tof_fault_code", get_tof_fault_code);
  Bridge.provide("set_tof_test_config", set_tof_test_config);

  initializeSensor();
}

void loop() {
  static unsigned long lastPollMS = 0;
  unsigned long now = millis();

  if (now - lastPollMS < POLL_INTERVAL_MS) {
    delay(5);
    return;
  }
  lastPollMS = now;

  if (!sensorOnline) {
    refreshI2CDiagnostics();
    initializeSensor();
    delay(5);
    return;
  }

  if (!vl53.dataReady()) {
    dataReadyFlag = false;
    delay(5);
    return;
  }

  dataReadyFlag = true;
  int distanceMM = (int)vl53.read(false);

  if (vl53.timeoutOccurred()) {
    lastDistanceMM = -1;
    objectPresent = false;
    setFault(FAULT_READ_TIMEOUT, "VL53L1X read timeout");
    delay(5);
    return;
  }

  if (vl53.ranging_data.range_status != VL53L1X::RangeValid) {
    lastDistanceMM = -1;
    objectPresent = false;
    setFault(FAULT_RANGE_STATUS, String("VL53L1X status: ") + VL53L1X::rangeStatusToString(vl53.ranging_data.range_status));
    delay(5);
    return;
  }

  sensorOnline = true;
  lastDistanceMM = distanceMM;
  lastReadMS = now;
  objectPresent = distanceMM <= thresholdMM;
  faultCode = FAULT_NONE;
  faultMessage = "";
  delay(5);
}

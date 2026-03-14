#include "Arduino_RouterBridge.h"
#include <Wire.h>
#include <VL53L1X.h>

#define XSHUT_1   3      // D3 → Sensor 1 XSHUT (wired, continuity confirmed 2026-03-14)
#define XSHUT_2   4      // D4 → Sensor 2 XSHUT
#define ADDR_1    0x30   // Target address for sensor 1
#define ADDR_2    0x31   // Target address for sensor 2

// LED blink count encodes which sensor failed and how:
//   1 blink  — sensor 1: no ACK at 0x29
//   2 blinks — sensor 1: init failed
//   3 blinks — sensor 1: no ACK at 0x30 after reassignment
//   4 blinks — sensor 2: no ACK at 0x29
//   5 blinks — sensor 2: init failed
//   6 blinks — sensor 2: no ACK at 0x31 after reassignment
//   solid on — both sensors configured successfully

enum State {
  STATE_STARTING,
  STATE_S1_NO_ACK,
  STATE_S1_INIT_FAILED,
  STATE_S1_NO_ACK_NEW,
  STATE_S2_NO_ACK,
  STATE_S2_INIT_FAILED,
  STATE_S2_NO_ACK_NEW,
  STATE_OK
};

VL53L1X sensor1;
VL53L1X sensor2;
State state = STATE_STARTING;

// LED is active low: LOW = ON, HIGH = OFF

void blinkN(int n) {
  for (int i = 0; i < n; i++) {
    digitalWrite(LED_BUILTIN, LOW);  delay(150); // ON
    digitalWrite(LED_BUILTIN, HIGH); delay(150); // OFF
  }
  delay(800);
}

void blinkFast(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_BUILTIN, LOW);  delay(80);  // ON
    digitalWrite(LED_BUILTIN, HIGH); delay(80);  // OFF
  }
}

void setup() {
  Bridge.begin();
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH); // OFF initially (active low)

  blinkFast(4); // signal: starting

  // Pull both XSHUT pins LOW — both sensors off
  pinMode(XSHUT_1, OUTPUT);
  pinMode(XSHUT_2, OUTPUT);
  digitalWrite(XSHUT_1, LOW);
  digitalWrite(XSHUT_2, LOW);
  delay(10);

  Wire1.begin();
  Wire1.setClock(400000);

  // === Sensor 1: boot, init, reassign to 0x30 ===

  digitalWrite(XSHUT_1, HIGH); // sensor 1 on — boots at 0x29
  delay(2);

  Wire1.beginTransmission(0x29);
  if (Wire1.endTransmission() != 0) {
    state = STATE_S1_NO_ACK;
    Monitor.println("FAULT S1: no I2C ACK at 0x29");
    return;
  }

  sensor1.setBus(&Wire1);
  sensor1.setTimeout(200);
  if (!sensor1.init()) {
    state = STATE_S1_INIT_FAILED;
    Monitor.println("FAULT S1: init failed at 0x29");
    return;
  }

  sensor1.setAddress(ADDR_1);
  delay(5);

  Wire1.beginTransmission(ADDR_1);
  if (Wire1.endTransmission() != 0) {
    state = STATE_S1_NO_ACK_NEW;
    Monitor.println("FAULT S1: no ACK at 0x30 after reassignment");
    return;
  }
  Monitor.println("OK S1: sensor 1 responding at 0x30");

  // === Sensor 2: boot, init, reassign to 0x31 ===
  // Sensor 1 is already at 0x30, so 0x29 is free for sensor 2 to boot into.

  digitalWrite(XSHUT_2, HIGH); // sensor 2 on — boots at 0x29
  delay(2);

  Wire1.beginTransmission(0x29);
  if (Wire1.endTransmission() != 0) {
    state = STATE_S2_NO_ACK;
    Monitor.println("FAULT S2: no I2C ACK at 0x29");
    return;
  }

  sensor2.setBus(&Wire1);
  sensor2.setTimeout(200);
  if (!sensor2.init()) {
    state = STATE_S2_INIT_FAILED;
    Monitor.println("FAULT S2: init failed at 0x29");
    return;
  }

  sensor2.setAddress(ADDR_2);
  delay(5);

  Wire1.beginTransmission(ADDR_2);
  if (Wire1.endTransmission() != 0) {
    state = STATE_S2_NO_ACK_NEW;
    Monitor.println("FAULT S2: no ACK at 0x31 after reassignment");
    return;
  }
  Monitor.println("OK S2: sensor 2 responding at 0x31");

  state = STATE_OK;
  digitalWrite(LED_BUILTIN, LOW); // solid ON (active low)
  Monitor.println("SUCCESS: S1=0x30, S2=0x31 — both sensors configured");
  Monitor.println("Power cycle both sensors to reset addresses to 0x29");
}

void loop() {
  switch (state) {
    case STATE_S1_NO_ACK:      blinkN(1); break;
    case STATE_S1_INIT_FAILED: blinkN(2); break;
    case STATE_S1_NO_ACK_NEW:  blinkN(3); break;
    case STATE_S2_NO_ACK:      blinkN(4); break;
    case STATE_S2_INIT_FAILED: blinkN(5); break;
    case STATE_S2_NO_ACK_NEW:  blinkN(6); break;
    case STATE_OK:             delay(1000); break;
    default:                   delay(100);  break;
  }
}

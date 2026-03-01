// SPDX-FileCopyrightText: Sonic Sensor App
// SPDX-License-Identifier: MPL-2.0

// HC-SR04 ultrasonic distance sensor for Arduino Uno Q
// Exposes get_distance() via Bridge RPC for the Python/Linux side.
//
// Wiring:
//   TRIG -> D6
//   ECHO -> D7  ** voltage divider required on ECHO **
//              HC-SR04 ECHO (5V) -> 10kΩ -> D7 -> 20kΩ -> GND
//              This brings 5V down to ~3.3V safe for the Uno Q GPIO.

#include <Arduino_RouterBridge.h>

// ── Demo mode ─────────────────────────────────────────────────────────────────
// Comment out this line when the real HC-SR04 sensor is wired up.
#define DEMO_MODE

// ── Parameters ────────────────────────────────────────────────────────────────
const unsigned int  OUT_OF_RANGE     = 2000;    // mm – readings >= this = no target
const unsigned long MEASURE_INTERVAL = 100;     // ms between sensor reads
const unsigned long ECHO_TIMEOUT_US  = 30000UL; // ~515 cm max, keeps blocking < 30ms

// ── Pins ──────────────────────────────────────────────────────────────────────
const int TRIG = 6;
const int ECHO = 7;

// ── State ─────────────────────────────────────────────────────────────────────
int  lastDistanceMM = -1;  // -1 = out of range
bool inRange        = false;

// ── RPC handler: Python calls get_distance() ──────────────────────────────────
// Returns current reading. Python receives lastDistanceMM and inRange.
void get_distance(bool dummy) {
    Bridge.respond(lastDistanceMM, inRange);
}

// ── Sensor read ───────────────────────────────────────────────────────────────
#ifdef DEMO_MODE
// Cycles through a fake reading pattern so the full pipeline can be tested
// without any hardware attached. Simulates an object approaching then leaving.
// Pattern: ramp 200->1800mm over ~8 s, then jump out of range for ~2 s, repeat.
int readDistanceMM() {
    static unsigned long demoStart = 0;
    if (demoStart == 0) demoStart = millis();

    unsigned long elapsed = (millis() - demoStart) % 10000UL; // 10 s cycle

    if (elapsed < 8000) {
        // Ramp from 200 mm up to 1800 mm
        return (int)(200 + (1600UL * elapsed) / 8000UL);
    } else {
        // Out of range for the last 2 s of the cycle
        return -1;
    }
}
#else
int readDistanceMM() {
    digitalWrite(TRIG, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG, LOW);

    unsigned long duration = pulseIn(ECHO, HIGH, ECHO_TIMEOUT_US);
    if (duration == 0) return -1;

    unsigned long mm = (duration * 343UL) / 2000UL;
    if (mm >= OUT_OF_RANGE) return -1;
    if (mm > 9999) mm = 9999;
    return (int)mm;
}
#endif

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
#ifndef DEMO_MODE
    pinMode(TRIG, OUTPUT);
    pinMode(ECHO, INPUT);
    digitalWrite(TRIG, LOW);
#endif

    Bridge.begin();
    Bridge.provide("get_distance", get_distance);
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
    static unsigned long lastMeasure = 0;
    unsigned long now = millis();

    if (now - lastMeasure >= MEASURE_INTERVAL) {
        lastMeasure     = now;
        int mm          = readDistanceMM();
        lastDistanceMM  = mm;
        inRange         = (mm >= 0);
    }

    delay(10);
}

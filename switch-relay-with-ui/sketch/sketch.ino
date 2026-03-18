#include <Arduino_RouterBridge.h>

void set_relay_state(bool state) {
    digitalWrite(8, state ? HIGH : LOW);
}

void setup() {
    pinMode(8, OUTPUT);
    digitalWrite(8, LOW);   // relay OFF on boot

    Bridge.begin();
    Bridge.provide("set_relay_state", set_relay_state);
}

void loop() {}

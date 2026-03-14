#include <Arduino_RouterBridge.h>

const int BUZZER_PIN = 8;

void set_buzzer_state(bool state) {
    digitalWrite(BUZZER_PIN, state ? HIGH : LOW);
}

void setup() {
    pinMode(BUZZER_PIN, OUTPUT);
    // Start with the buzzer OFF
    digitalWrite(BUZZER_PIN, LOW);

    Bridge.begin();
    Bridge.provide_safe("set_buzzer_state", set_buzzer_state);
}

void loop() {}

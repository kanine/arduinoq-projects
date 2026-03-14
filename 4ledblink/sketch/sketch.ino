#include <Arduino_RouterBridge.h>

// LED3_R, LED3_G, LED3_B, LED4_R, LED4_G, LED4_B are defined in variant.h
// via DIGITAL_PIN_GPIOS_FIND_NODE — active low: LOW = ON, HIGH = OFF

const pin_size_t ALL_PINS[] = { LED3_R, LED3_G, LED3_B, LED4_R, LED4_G, LED4_B };
const int PIN_COUNT  = 6;

void allOff() {
    for (int i = 0; i < PIN_COUNT; i++) {
        digitalWrite(ALL_PINS[i], HIGH);
    }
}

// Colour sequence: Red → Green → Blue → repeat
// Each phase holds for STEP_MS milliseconds
const unsigned long STEP_MS = 500;

void setup() {
    for (int i = 0; i < PIN_COUNT; i++) {
        pinMode(ALL_PINS[i], OUTPUT);
    }
    allOff();
    Bridge.begin();
}

void loop() {
    static uint8_t  phase     = 0;
    static unsigned long lastMS = 0;
    unsigned long now = millis();

    if (now - lastMS < STEP_MS) return;
    lastMS = now;

    allOff();
    switch (phase) {
        case 0:  // Red
            digitalWrite(LED3_R, LOW);
            digitalWrite(LED4_R, LOW);
            break;
        case 1:  // Green
            digitalWrite(LED3_G, LOW);
            digitalWrite(LED4_G, LOW);
            break;
        case 2:  // Blue
            digitalWrite(LED3_B, LOW);
            digitalWrite(LED4_B, LOW);
            break;
    }
    phase = (phase + 1) % 3;
}

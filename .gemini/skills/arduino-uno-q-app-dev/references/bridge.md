# Arduino Uno Q Bridge Communication

The **Bridge** is the primary communication layer between the **MCU** (sketch) and the **MPU** (python). It operates as a Remote Procedure Call (RPC) system over the internal serial/mailbox interface.

## MCU (Sketch) Setup

In the Arduino sketch (`sketch.ino`), you must provide functions that the Python MPU can call.

```cpp
#include <Arduino_RouterBridge.h>

void setup() {
  Bridge.begin();
  
  // Register functions
  Bridge.provide("get_data", get_data_func);
  Bridge.provide("set_state", set_state_func);
}

// Function signature: can return values (int, float, bool, etc.) or take arguments.
int get_data_func() {
  return analogRead(A0);
}

void set_state_func(bool on) {
  digitalWrite(LED_BUILTIN, on ? HIGH : LOW);
}
```

## MPU (Python) Setup

In the Python script (`main.py`), you can call or notify the MCU.

```python
from arduino.app_utils import Bridge

# Bridge.call is SYNCHRONOUS (blocks until MCU responds)
value = Bridge.call("get_data")

# Bridge.notify is ASYNCHRONOUS (fire-and-forget, non-blocking)
# Recommended for high-frequency updates or when response is not needed.
Bridge.notify("set_state", True)
```

## Best Practices

1. **Avoid `delay()` in MCU `loop()`**: The Bridge service needs to process the serial buffer. Use `millis()` based timing instead.
2. **Synchronous overhead**: `Bridge.call` has a round-trip latency. For real-time updates (e.g., animations, high-speed polling), prefer `Bridge.notify`.
3. **Data limits**: Keep the payload sizes reasonable. Large arrays should be sent carefully or split.
4. **Initialization**: Always call `Bridge.begin()` in `setup()` before `Bridge.provide()`.

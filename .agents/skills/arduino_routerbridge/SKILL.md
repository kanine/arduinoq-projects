---
name: arduino_routerbridge
description: Communication between the Arduino Uno Q MCU and the MPU using the Arduino_RouterBridge library. Covers Bridge initialization, RPC calls, providing methods, and notifying.
---

# Arduino_RouterBridge Skill

The `Arduino_RouterBridge` library is a wrapper of `Arduino_RPClite` specifically designed for the Arduino UNO Q. It provides a better UX and API for sketches to communicate with the CPU Host running the GOLANG router.

Including `Arduino_RouterBridge.h` gives the user access to a `Bridge` object that can be used both as an RPC client and/or server to execute and serve RPCs to/from the CPU Host.

## 1. Initialization
The `Bridge` object is pre-defined on `Serial1`. Include the header and initialize the Bridge in the `setup()` function.

```cpp
#include <Arduino_RouterBridge.h>

void setup() {
    Bridge.begin();
    // ...
}
```

## 2. Providing RPC Methods
The MCU can provide methods that the MPU (Python) can call.
- **`Bridge.provide`**: Thread-unsafe. Methods are served in an update callback, whose execution is granted in a separate thread.
- **`Bridge.provide_safe`**: Thread-safe. Execution is granted in the main loop thread where `update_safe` is called. By design, users cannot access `.update_safe()` freely.

```cpp
bool set_led(bool state) {
    digitalWrite(LED_BUILTIN, state);
    return state;
}

String greet() {
    return String("Hello Friend");
}

void setup() {
    Bridge.begin();
    
    // Check if provision was successful
    if (!Bridge.provide("set_led", set_led)) {
        Monitor.println("Error providing method: set_led");
    }
    
    Bridge.provide_safe("greet", greet);
}
```

## 3. Calling RPC Methods
The MCU can call RPC methods provided by the MPU.
- `Bridge.call` is non-blocking and returns an `RpcCall` async object.
- `RpcCall` implements a blocking `.result(res)` method that waits for the RPC response and returns `true` if it returned with no errors.
- `.result` returns the value exactly once; subsequent calls return an error condition.

```cpp
void loop() {
    float sum;
    
    // Standard chained call
    if (!Bridge.call("add", 1.0, 2.0).result(sum)) {
        Monitor.println("Error calling method: add");
    }

    // Async call structure
    RpcCall async_rpc = Bridge.call("add", 3.0, 4.5);
    if (!async_rpc.result(sum)) {
        Monitor.println("Error calling method: add");
        Monitor.print("Error code: ");
        Monitor.println(async_rpc.getErrorCode());
        Monitor.print("Error message: ");
        Monitor.println(async_rpc.getErrorMessage());
    }
    
    // Implicit boolean cast. Used when expecting a fallback nil result
    if (!Bridge.call("send_greeting", "Hello Friend")) {
        Monitor.println("Error calling method: send_greeting");
    }
}
```

## 4. Notifications
Use `Bridge.notify` when no result is expected from the opposite side (e.g., None, null, void, nil). Notification is executed immediately.

```cpp
void loop() {
    Bridge.notify("signal", 200);
}
```

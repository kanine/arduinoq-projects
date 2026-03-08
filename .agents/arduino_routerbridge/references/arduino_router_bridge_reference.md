# ARDUINO_ROUTER_BRIDGE_REFERENCE.md

This document summarizes the `Arduino_RouterBridge` library used for communication between the MCU (Arduino) and MPU (Linux/Python) on boards like the Arduino UNO Q.

---

## Core Bridge Methods

### 1. Initialization
`Bridge.begin()`
* **Purpose:** Initializes the RPC (Remote Procedure Call) stack and the dedicated Serial interface.
* **Usage:** Must be called in `setup()`. It is recommended to call this before other `begin()` methods.

### 2. Sending Data (MCU → MPU)

| Method | Type | Description |
| :--- | :--- | :--- |
| **`Bridge.notify("method", params...)`** | Asynchronous | **Fire-and-forget.** Sends data to the MPU and returns immediately. Does NOT wait for a reply. Best for high-frequency telemetry. |
| **`Bridge.call("method", params...)`** | Synchronous | **Request-Response.** Sends a request and expects a return value. Returns an `RpcCall` object. |

### 3. Receiving Requests (MPU → MCU)

| Method | Safety | Description |
| :--- | :--- | :--- |
| **`Bridge.provide("name", function)`** | Standard | Allows Linux to trigger an Arduino function. Runs in a background thread. |
| **`Bridge.provide_safe("name", function)`** | Thread-Safe | Preferred method. Queues the request to be executed safely during the main Arduino loop to avoid data corruption. |

---

## Code Examples

### Example: Using `notify` for Telemetry
```cpp
void loop() {
  int sensorValue = analogRead(A0);
  // Send data to a Python script on the Linux side
  Bridge.notify("log_sensor", sensorValue);
  delay(100); // Small delay to prevent buffer overflow
}
```

### Example: Using call for Data Requests

```cpp
void loop() {
  float cpuTemp;
  auto request = Bridge.call("get_linux_stats");

  // .result() blocks until the MPU answers
  if (request.result(cpuTemp)) {
    Serial.print("Linux CPU Temp: ");
    Serial.println(cpuTemp);
  } else {
    Serial.println("Request failed!");
  }
  delay(5000);
}
```

### Example: Using provide_safe to receive commands

```cpp
bool ledControl(bool status) {
  digitalWrite(LED_BUILTIN, status ? HIGH : LOW);
  return true; // Return 'true' to Linux to confirm success
}

void setup() {
  Bridge.begin();
  pinMode(LED_BUILTIN, OUTPUT);
  // Register the function so Python can call it
  Bridge.provide_safe("set_led", ledControl);
}
```

### Important Considerations
* **Serialization:** Data is automatically packed using MessagePack.
* **Non-Blocking:** `Bridge.call` starts non-blocking, but calling `.result()` on the returned object will block execution until a response arrives or times out.
* **Buffer Limits:** If using `Bridge.notify` too rapidly, you may overflow the UART buffer. Always include a small `delay()` or timing logic.
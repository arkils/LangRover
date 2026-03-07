# ESP32 Firmware for LangRover

## Overview

The ESP32 microcontroller acts as a hardware abstraction layer between the Raspberry Pi and the robot's motors and sensors. It receives commands via USB CDC serial and controls the hardware directly using its GPIO pins.

**Dual-Core Architecture**: The firmware leverages both ESP32 cores for optimal performance:
- **Core 0**: Handles serial communication and motor control
- **Core 1**: Continuously reads sensors and updates world state

This design ensures motors respond instantly while sensors update autonomously in the background.

## Architecture

```
Raspberry Pi → [USB Serial] → ESP32 Core 0 (Motors + Commands)
                                  ↕ (Thread-Safe Mutex)
                              ESP32 Core 1 (Sensors + State)
                                  ↓
                              [GPIO] → Motors/Sensors
```

## Hardware Connections

### Motor Drivers (2x TB6612FNG)

The TB6612FNG is a dual motor driver capable of controlling 2 DC motors per board. It offers:
- **Higher current**: 1.2A continuous per channel (3.2A peak)
- **Better efficiency**: Lower voltage drop than L293D
- **Built-in protection**: Thermal shutdown and overcurrent protection
- **Separate PWM control**: Each motor has its own PWM input

**TB6612FNG Driver 1 (Front Motors)**
- **Front Left Motor (Channel A):**
  - AIN1: GPIO 25
  - AIN2: GPIO 26
  - PWMA: GPIO 27
- **Front Right Motor (Channel B):**
  - BIN1: GPIO 14
  - BIN2: GPIO 12
  - PWMB: GPIO 13
- **Control:**
  - STBY (Standby): GPIO 21 (must be HIGH to enable)
  - VM (Motor Power): 6-12V DC
  - VCC (Logic Power): 3.3V from ESP32

**TB6612FNG Driver 2 (Rear Motors)**
- **Rear Left Motor (Channel A):**
  - AIN1: GPIO 33
  - AIN2: GPIO 32
  - PWMA: GPIO 15
- **Rear Right Motor (Channel B):**
  - BIN1: GPIO 5
  - BIN2: GPIO 4
  - PWMB: GPIO 2
- **Control:**
  - STBY (Standby): GPIO 22 (must be HIGH to enable)
  - VM (Motor Power): 6-12V DC
  - VCC (Logic Power): 3.3V from ESP32

### Ultrasonic Sensors (4x HC-SR04)

ECHO pins are wired to input-only GPIOs (34, 35, 36, 39), which are receive-only
by hardware design — no accidental output drive, no PWM interference.

- **Front Sensor**: TRIG GPIO 23, ECHO GPIO 34 (input-only)
- **Left Sensor**:  TRIG GPIO 18, ECHO GPIO 35 (input-only)
- **Right Sensor**: TRIG GPIO 17, ECHO GPIO 36 (input-only)
- **Rear Sensor**:  TRIG GPIO 16, ECHO GPIO 39 (input-only)

## Communication Protocol

### Serial Configuration
- **Baud Rate**: 115200
- **Data Format**: 8N1 (8 data bits, no parity, 1 stop bit)
- **Protocol**: JSON strings terminated with `\n`

### Commands (Raspberry Pi → ESP32)

#### Motor Commands

**Move Forward:**
```json
{"cmd": "motor", "action": "forward", "speed": 70, "duration": 1.5}
```
- `speed`: 0-100 (percentage)
- `duration`: seconds (optional, omit for continuous)

**Move Backward:**
```json
{"cmd": "motor", "action": "backward", "speed": 70, "duration": 1.5}
```

**Turn Left:**
```json
{"cmd": "motor", "action": "turn_left", "speed": 70, "duration": 0.5}
```

**Turn Right:**
```json
{"cmd": "motor", "action": "turn_right", "speed": 70, "duration": 0.5}
```

**Stop:**
```json
{"cmd": "motor", "action": "stop"}
```

#### Sensor Commands

**Read Single Ultrasonic Sensor:**
```json
{"cmd": "sensor", "type": "ultrasonic", "id": "front"}
```
- Valid IDs: `"front"`, `"left"`, `"right"`, `"rear"`, `"all"`

**Read All Sensors:**
```json
{"cmd": "sensor", "type": "ultrasonic", "id": "all"}
```
or omit the `"id"` field entirely

#### System Commands

**Ping (connection test):**
```json
{"cmd": "ping"}
```

### Responses (ESP32 → Raspberry Pi)

#### Acknowledgment
```json
{"type": "ack", "status": "ok"}
{"type": "ack", "status": "error", "message": "Motor timeout"}
```

#### Sensor Data

**Single Sensor Response:**
```json
{"type": "sensor", "id": "front", "distance": 45.2}
```
- `distance`: centimeters (float)

**All Sensors State (Auto-broadcast every 500ms from Core 1):**
```json
{"type": "sensor_state", "front": 45.2, "left": 23.1, "right": 18.5, "rear": 102.3, "timestamp": 12345}
```
- All distances in centimeters (float)
- `timestamp`: milliseconds since ESP32 boot

#### Pong
```json
{"type": "pong"}
```

#### Error
```json
{"type": "error", "message": "Invalid command"}
```

## Arduino/PlatformIO Setup

### Required Libraries
- **ArduinoJson** (v6.x or v7.x): For JSON parsing and generation
- **ESP32 Core**: Built-in support for GPIO, PWM, and Serial

### Installation Options

#### Option 1: Arduino IDE
1. Install Arduino IDE 2.x
2. Add ESP32 board support:
   - Go to File → Preferences
   - Add to "Additional Board Manager URLs": 
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
3. Install ESP32 boards via Board Manager
4. Install ArduinoJson library via Library Manager
5. Select board: "ESP32 Dev Module" or your specific ESP32 board

#### Option 2: PlatformIO (Recommended)
1. Install VS Code and PlatformIO extension
2. Create new project with ESP32 board
3. Add to `platformio.ini`:
   ```ini
   [env:esp32dev]
   platform = espressif32
   board = esp32dev
   framework = arduino
   lib_deps = 
       bblanchon/ArduinoJson@^7.0.0
   monitor_speed = 115200
   ```

### Firmware Implementation Structure

#### Dual-Core Architecture

```cpp
// Required includes
#include <Arduino.h>
#include <ArduinoJson.h>

// Thread-safe sensor state structure
struct SensorState {
  float frontDistance;
  float leftDistance;
  float rightDistance;
  float rearDistance;
  unsigned long lastUpdateTime;
};

volatile SensorState sensorState;
SemaphoreHandle_t sensorMutex;  // FreeRTOS mutex for thread-safety
TaskHandle_t sensorTaskHandle;  // Core 1 task handle

// Motor control functions (Core 0)
void motorForward(int speed, float duration);
void motorBackward(int speed, float duration);
void motorTurnLeft(int speed, float duration);
void motorTurnRight(int speed, float duration);
void motorStop();

// Sensor reading functions (Core 1)
float readUltrasonicDistance(int trigPin, int echoPin);
void updateSensorState(float front, float left, float right, float rear);
void getSensorState(float* front, float* left, float* right, float* rear);

// Serial communication functions (Core 0)
void processCommand(JsonDocument& doc);
void sendResponse(const char* type, JsonDocument& data);
void sendAllSensorData();

// Setup and loops
void setup() {
    Serial.begin(115200);
    
    // Create mutex for thread-safe sensor access
    sensorMutex = xSemaphoreCreateMutex();
    
    // Initialize GPIO pins
    setupMotors();
    setupSensors();
    
    // Create sensor task on Core 1
    xTaskCreatePinnedToCore(
        sensorTask,      // Function
        "SensorTask",    // Name
        4096,            // Stack size
        NULL,            // Parameters
        1,               // Priority
        &sensorTaskHandle,
        1                // Core 1
    );
}

// Core 0: Serial communication and motor control
void loop() {
    // Read and process JSON commands
    // Execute motor operations
    // Send responses
}

// Core 1: Continuous sensor reading
void sensorTask(void* parameter) {
    while(1) {
        // Read all sensors
        // Update shared state with mutex protection
        // Periodically broadcast sensor data
        vTaskDelay(10 / portTICK_PERIOD_MS);
    }
}
```

## Implementation Checklist

### Hardware Setup
- [ ] Connect ESP32 to Raspberry Pi via USB
- [ ] Wire motor controllers to ESP32 GPIO
- [ ] Wire ultrasonic sensors to ESP32 GPIO
- [ ] Power ESP32 appropriately (via USB or external 5V)
- [ ] Test individual motors and sensors

### Firmware Development
- [ ] Set up development environment (Arduino IDE or PlatformIO)
- [ ] Install required libraries (ArduinoJson)
- [ ] Implement pin definitions
- [ ] Implement motor control functions
- [ ] Implement sensor reading functions
- [ ] Implement JSON command parser
- [ ] Implement JSON response generator
- [ ] Add error handling and timeouts
- [ ] Test each function individually

### Integration Testing
- [ ] Upload firmware to ESP32
- [ ] Connect to Raspberry Pi
- [ ] Test serial communication (ping/pong)
- [ ] Test motor commands
- [ ] Test sensor readings
- [ ] Test error conditions
- [ ] Verify timing and responsiveness

## Motor Control Logic

### TB6612FNG Truth Table

| IN1 | IN2 | PWM | Motor Action |
|-----|-----|-----|--------------|
| H   | L   | PWM | Forward (CW) |
| L   | H   | PWM | Reverse (CCW)|
| L   | L   | PWM | Short brake  |
| H   | H   | PWM | Short brake  |
| X   | X   | 0   | Stop (coast) |

**Note**: STBY pin must be HIGH for motor operation. When LOW, all motors are disabled.

### Forward Movement
```
All 4 motors: Forward direction
FL: AIN1=HIGH, AIN2=LOW, PWMA=speed
FR: BIN1=HIGH, BIN2=LOW, PWMB=speed
RL: AIN1=HIGH, AIN2=LOW, PWMA=speed
RR: BIN1=HIGH, BIN2=LOW, PWMB=speed
```

### Backward Movement
```
All 4 motors: Backward direction
FL: AIN1=LOW, AIN2=HIGH, PWMA=speed
FR: BIN1=LOW, BIN2=HIGH, PWMB=speed
RL: AIN1=LOW, AIN2=HIGH, PWMA=speed
RR: BIN1=LOW, BIN2=HIGH, PWMB=speed
```

### Turn Left (Tank Turn)
```
Left motors: Backward
Right motors: Forward
FL: AIN1=LOW, AIN2=HIGH, PWMA=speed
FR: BIN1=HIGH, BIN2=LOW, PWMB=speed
RL: AIN1=LOW, AIN2=HIGH, PWMA=speed
RR: BIN1=HIGH, BIN2=LOW, PWMB=speed
```

### Turn Right (Tank Turn)
```
Left motors: Forward
Right motors: Backward
FL: AIN1=HIGH, AIN2=LOW, PWMA=speed
FR: BIN1=LOW, BIN2=HIGH, PWMB=speed
RL: AIN1=HIGH, AIN2=LOW, PWMA=speed
RR: BIN1=LOW, BIN2=HIGH, PWMB=speed
```

### Stop
```
Short brake mode (fastest stop)
All motors: Both IN pins LOW
FL: AIN1=LOW, AIN2=LOW
FR: BIN1=LOW, BIN2=LOW
RL: AIN1=LOW, AIN2=LOW
RR: BIN1=LOW, BIN2=LOW
PWM: 0% (optional, brake works regardless)
```

## Dual-Core Processing

### Core 0: Command Processing & Motor Control
- Runs the standard Arduino `loop()` function
- Handles incoming serial commands
- Processes JSON parsing
- Executes motor movements
- Reads sensor data from cached state (no blocking)
- Priority: Fast command response

### Core 1: Sensor Monitoring (Background Task)
- Runs `sensorTask()` in an infinite FreeRTOS task
- Continuously reads all 4 ultrasonic sensors
- Updates every 100ms (10Hz update rate)
- Auto-broadcasts sensor state every 500ms
- Uses mutex for thread-safe data sharing
- Priority: Consistent world state updates

### Thread-Safe Data Sharing
```cpp
// Core 1 writes (with mutex protection)
void updateSensorState(float front, float left, float right, float rear) {
  if (xSemaphoreTake(sensorMutex, portMAX_DELAY) == pdTRUE) {
    sensorState.frontDistance = front;
    sensorState.leftDistance = left;
    sensorState.rightDistance = right;
    sensorState.rearDistance = rear;
    sensorState.lastUpdateTime = millis();
    xSemaphoreGive(sensorMutex);
  }
}

// Core 0 reads (with mutex protection)
void getSensorState(float* front, float* left, float* right, float* rear) {
  if (xSemaphoreTake(sensorMutex, portMAX_DELAY) == pdTRUE) {
    *front = sensorState.frontDistance;
    *left = sensorState.leftDistance;
    *right = sensorState.rightDistance;
    *rear = sensorState.rearDistance;
    xSemaphoreGive(sensorMutex);
  }
}
```

## Ultrasonic Sensor Reading

### HC-SR04 Timing
1. Send 10μs HIGH pulse to TRIG pin
2. Wait for ECHO pin to go HIGH
3. Measure time until ECHO pin goes LOW
4. Calculate distance: `distance_cm = (pulse_duration_us * 0.0343) / 2`

### Timeout Handling
- Maximum wait time: 30ms per sensor (30000μs timeout)
- Return -1.0 if no echo received or out of range
- Valid range: 2cm - 400cm
- 10ms delay between sensor readings to avoid interference

## Performance Benefits

### Single-Core vs Dual-Core

**Single-Core (Traditional):**
- Motor command → Wait for sensor read → Response (blocking)
- Sensor reads only when requested
- Total latency: Command processing + sensor reading time
- Intermittent world state updates

**Dual-Core (Current Implementation):**
- Motor command → Instant response (no blocking)
- Sensors continuously update at 10Hz
- Auto-broadcast of sensor state every 500ms
- Core 0 latency: Command processing only
- Core 1 latency: Independent of commands
- Better real-time performance and responsiveness

### Key Advantages
1. **Lower Latency**: Motor commands execute immediately
2. **Higher Throughput**: Both operations run simultaneously
3. **Consistent Updates**: Sensors refresh at regular intervals
4. **Better Awareness**: Always have fresh sensor data without polling
5. **Scalability**: Can add more sensor types to Core 1 without affecting Core 0

## Safety Considerations

1. **Motor Timeout**: If duration is specified, ensure motors stop after that time
2. **Emergency Stop**: Implement immediate stop on command
3. **Watchdog**: Consider implementing a watchdog timer to reset if Pi stops communicating
4. **Power Protection**: Ensure motor drivers have proper power supply and don't overload ESP32
5. **Error Recovery**: Handle invalid commands gracefully
6. **Thread Safety**: Always use mutex when accessing shared sensor data between cores

## Troubleshooting

### ESP32 Not Detected
- Check USB cable (must support data, not just power)
- Install CH340/CP210x drivers if needed
- Try different USB port
- Check `dmesg` on Linux or Device Manager on Windows

### No Serial Communication
- Verify baud rate (115200)
- Check JSON format (must end with `\n`)
- Use Serial Monitor to debug
- Ensure ESP32 firmware is running

### Motors Not Working
- Check power supply to motor drivers (VM pin - 6-12V)
- **Verify STBY pins are HIGH** (critical for TB6612FNG)
- Verify GPIO connections
- Test motors directly with ESP32 GPIO
- Check motor driver connections (AIN1/AIN2, BIN1/BIN2, PWMA/PWMB)
- Ensure VCC is connected to 3.3V from ESP32

### Sensor Readings Incorrect
- Verify sensor wiring (TRIG/ECHO not swapped)
- Check for 5V power to sensors
- Ensure clear path for ultrasonic waves
- Test sensors individually

## Reference Implementation

See `esp32_firmware_template.ino` for a complete reference implementation.

## Additional Resources

- [ESP32 GPIO Reference](https://randomnerdtutorials.com/esp32-pinout-reference-gpios/)
- [TB6612FNG Motor Driver Datasheet](https://www.sparkfun.com/datasheets/Robotics/TB6612FNG.pdf)
- [TB6612FNG Breakout Board Guide](https://learn.sparkfun.com/tutorials/tb6612fng-hookup-guide)
- [HC-SR04 Ultrasonic Sensor](https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf)
- [ArduinoJson Documentation](https://arduinojson.org/)
- [ESP32 Arduino Core](https://github.com/espressif/arduino-esp32)

# ESP32 Firmware for LangRover

## Overview

The ESP32 microcontroller acts as a hardware abstraction layer between the Raspberry Pi and the robot's motors and sensors. It receives commands via USB CDC serial and controls the hardware directly using its GPIO pins.

## Architecture

```
Raspberry Pi → [USB Serial] → ESP32 → [GPIO] → Motors/Sensors
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
  - STBY (Standby): GPIO 19 (must be HIGH to enable)
  - VM (Motor Power): 6-12V DC
  - VCC (Logic Power): 3.3V from ESP32

### Ultrasonic Sensors (4x HC-SR04)

- **Front Sensor**: TRIG GPIO 23, ECHO GPIO 22
- **Left Sensor**: TRIG GPIO 19, ECHO GPIO 18
- **Right Sensor**: TRIG GPIO 17, ECHO GPIO 16
- **Rear Sensor**: TRIG GPIO 4, ECHO GPIO 2

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

**Read Ultrasonic Sensor:**
```json
{"cmd": "sensor", "type": "ultrasonic", "id": "front"}
```
- Valid IDs: `"front"`, `"left"`, `"right"`, `"rear"`

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
```json
{"type": "sensor", "id": "front", "distance": 45.2}
```
- `distance`: centimeters (float)

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

```cpp
// Required includes
#include <Arduino.h>
#include <ArduinoJson.h>

// Pin definitions (from pins.py)
// ... define all GPIO pins ...

// Motor control functions
void motorForward(int speed, float duration);
void motorBackward(int speed, float duration);
void motorTurnLeft(int speed, float duration);
void motorTurnRight(int speed, float duration);
void motorStop();

// Sensor reading functions
float readUltrasonicDistance(int trigPin, int echoPin);

// Serial communication functions
void processCommand(JsonDocument& doc);
void sendResponse(const char* type, JsonDocument& data);

// Setup and loop
void setup() {
    Serial.begin(115200);
    // Initialize GPIO pins
    // ...
}

void loop() {
    // Read and process JSON commands
    // Execute motor/sensor operations
    // Send responses
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

## Ultrasonic Sensor Reading

### HC-SR04 Timing
1. Send 10μs HIGH pulse to TRIG pin
2. Wait for ECHO pin to go HIGH
3. Measure time until ECHO pin goes LOW
4. Calculate distance: `distance_cm = (pulse_duration_us * 0.0343) / 2`

### Timeout Handling
- Maximum wait time: 500ms
- Return error/None if no echo received
- Valid range: 2cm - 400cm

## Safety Considerations

1. **Motor Timeout**: If duration is specified, ensure motors stop after that time
2. **Emergency Stop**: Implement immediate stop on command
3. **Watchdog**: Consider implementing a watchdog timer to reset if Pi stops communicating
4. **Power Protection**: Ensure motor drivers have proper power supply and don't overload ESP32
5. **Error Recovery**: Handle invalid commands gracefully

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

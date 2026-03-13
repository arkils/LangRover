# LangRover TB6612FNG Motor Driver Setup

## Overview

LangRover uses an ESP32-based hardware architecture where the Raspberry Pi handles high-level intelligence (LLM, vision, decision-making) and the ESP32 manages real-time hardware control via TB6612FNG motor drivers and HC-SR04 ultrasonic sensors.

## Architecture

```
Raspberry Pi 5 (Brain)
  - Python application
  - LLM decision making
  - Vision processing
       ↓
  USB Serial (JSON)
       ↓
ESP32 (Hardware Controller)
  - Arduino firmware
  - Real-time motor control
  - Sensor reading
       ↓
  GPIO Pins
       ↓
Motors & Sensors
  - 4x DC Motors via TB6612FNG
  - 4x HC-SR04 Ultrasonic
```

## Benefits

1. **Real-time Control**: ESP32 handles time-critical motor and sensor operations
2. **Isolation**: Protects Raspberry Pi from electrical noise and hardware failures
3. **Reliability**: ESP32 can continue safety operations even if Pi crashes
4. **Simplicity**: Clean JSON protocol makes system easy to understand and extend
5. **Safety**: Hardware-level emergency stop capabilities via standby pins

## Core Components

### Key System Files

1. **`hardware/esp32_serial.py`**
   - ESP32 USB serial communication handler
   - JSON command/response protocol
   - Motor and sensor command methods
   - Background read thread for responses

2. **`ESP32_FIRMWARE.md`**
   - Complete ESP32 firmware documentation
   - Hardware connection details
   - Communication protocol specification
   - Setup and troubleshooting guide

3. **`esp32_firmware_template/esp32_firmware_template.ino`**
   - Ready-to-use Arduino firmware for ESP32
   - Motor control implementation with TB6612FNG
   - Sensor reading implementation
   - JSON command parser

### Hardware Abstraction

1. **`hardware/motors.py`**
   - Communicates with ESP32 via JSON protocol
   - MotorController class for movement commands
   - API: `move_forward()`, `move_backward()`, `turn_left()`, `turn_right()`, `stop()`

2. **`hardware/sensors.py`**
   - Communicates with ESP32 via JSON protocol
   - SensorArray class for distance readings
   - API: `read_front()`, `read_left()`, `read_right()`, `read_rear()`, `read_all()`

3. **`hardware/pins.py`**
   - ESP32 GPIO pin configuration
   - TB6612FNG motor driver pins
   - HC-SR04 ultrasonic sensor pins

4. **`config.py`**
   - ESP32_SERIAL_PORT configuration (default: `/dev/ttyACM0`)
   - ESP32_BAUDRATE configuration (default: `115200`)
   - Added ESP32_BAUDRATE configuration
   - Updated comments to reflect new architecture

5. **`requirements.txt`**
   - Added `pyserial>=3.5` (required)
   - Removed RPi.GPIO requirement (no longer needed)
   - Updated comments

6. **`ARCHITECTURE.md`**
   - Added hardware architecture overview
   - Added ESP32 communication protocol section
   - Updated deployment architecture diagram
   - Added ESP32 hardware stack visualization

## Configuration

### Environment Variables

Add these to your `.env` file or environment:

```bash
# ESP32 Serial Port
ESP32_SERIAL_PORT=/dev/ttyACM0  # Linux/Raspberry Pi
# ESP32_SERIAL_PORT=COM3         # Windows

# ESP32 Baud Rate (default: 115200)
ESP32_BAUDRATE=115200
```

### Python Dependencies

Install the new dependency:

```bash
pip install pyserial
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Hardware Setup

### 1. ESP32 Connections

**To Raspberry Pi:**
- Connect ESP32 to Pi via USB cable (must support data)
- ESP32 will appear as `/dev/ttyACM0` (Linux) or `COM3` (Windows)

**To Motor Drivers:**
- See `ESP32_FIRMWARE.md` for complete wiring diagram
- Front motors: GPIO 25, 26, 14, 12 (enable GPIO 27)
- Rear motors: GPIO 33, 32, 5, 15 (enable GPIO 13)

**To Ultrasonic Sensors:**
- Front: TRIG 23, ECHO 34 (input-only GPIO)
- Left:  TRIG 18, ECHO 35 (input-only GPIO)
- Right: TRIG 17, ECHO 36 (input-only GPIO)
- Rear:  TRIG 16, ECHO 39 (input-only GPIO)

### 2. ESP32 Firmware Upload

**Using Arduino IDE:**
1. Install Arduino IDE 2.x
2. Add ESP32 board support
3. Install ArduinoJson library
4. Open `esp32_firmware_template/esp32_firmware_template.ino`
5. Select your ESP32 board
6. Upload firmware

**Using PlatformIO:**
1. Install VS Code + PlatformIO
2. Create ESP32 project
3. Copy firmware template code
4. Build and upload

See `ESP32_FIRMWARE.md` for detailed instructions.

## API Usage

### Motor Control

```python
from hardware.motors import MotorController

motors = MotorController()  # Connects to ESP32 via serial
motors.move_forward(speed=70, duration=2.0)
motors.turn_left(speed=50, angle=45)
motors.stop()
```

### Sensor Reading

```python
from hardware.sensors import SensorArray

sensors = SensorArray()  # Connects to ESP32 via serial
distance = sensors.read_all()
front_distance = sensors.read_front()
```

## Testing

### 1. Test ESP32 Connection

```python
from hardware.esp32_serial import get_esp32

esp32 = get_esp32(port="/dev/ttyACM0")
if esp32.is_available():
    print("ESP32 connected!")
else:
    print("ESP32 not available")
```

### 2. Test Motor Control

```python
from hardware.motors import MotorController

motors = MotorController()
motors.move_forward(speed=50, duration=1.0)
motors.stop()
```

### 3. Test Sensor Reading

```python
from hardware.sensors import SensorArray

sensors = SensorArray()
distances = sensors.read_all()
print(f"Front: {distances['front']} cm")
```

## Troubleshooting

### ESP32 Not Detected

**Linux:**
```bash
ls /dev/ttyACM*  # Should show /dev/ttyACM0
ls /dev/ttyUSB*  # Or /dev/ttyUSB0
```

**Windows:**
- Check Device Manager → Ports (COM & LPT)
- Install CH340/CP210x drivers if needed

**Solution:**
- Try different USB cable (must support data)
- Check `dmesg` output on Linux
- Verify ESP32 firmware is uploaded

### Serial Communication Issues

**Symptoms:**
- `[ESP32] Cannot send command - not connected`
- Timeout errors

**Solutions:**
1. Check baud rate matches (115200)
2. Verify ESP32 firmware is running
3. Test with Arduino Serial Monitor first
4. Check USB cable quality

### Motors Not Responding

**Symptoms:**
- Commands sent but motors don't move
- `[WARNING] ESP32 not available`

**Solutions:**
1. Verify ESP32 firmware uploaded correctly
2. Check motor driver power supply
3. Test motors directly with ESP32 GPIO
4. Verify wiring matches pin configuration

### Sensor Readings Invalid

**Symptoms:**
- Distance returns -1 or None
- Inconsistent readings

**Solutions:**
1. Check sensor wiring (TRIG/ECHO correct?)
2. Ensure sensors have 5V power
3. Test sensors individually with ESP32
4. Verify clear path for ultrasonic waves

## Communication Protocol

### Example Commands

**Move Forward:**
```json
{"cmd": "motor", "action": "forward", "speed": 70, "duration": 1.5}
```

**Read Front Sensor:**
```json
{"cmd": "sensor", "type": "ultrasonic", "id": "front"}
```

### Example Responses

**Acknowledgment:**
```json
{"type": "ack", "status": "ok"}
```

**Sensor Data:**
```json
{"type": "sensor", "id": "front", "distance": 45.2}
```

See `ESP32_FIRMWARE.md` for complete protocol specification.

## Next Steps

1. **Hardware Assembly**: Connect ESP32 to motors and sensors
2. **Firmware Upload**: Flash ESP32 with the provided firmware
3. **Testing**: Verify each component works individually
4. **Integration**: Test full system with Raspberry Pi
5. **Calibration**: Fine-tune motor speeds and sensor readings

## Additional Resources

- `ESP32_FIRMWARE.md` - Complete firmware documentation
- `esp32_firmware_template/esp32_firmware_template.ino` - Arduino firmware template
- `ARCHITECTURE.md` - System architecture details
- `hardware/esp32_serial.py` - Serial communication implementation

## Support

For issues or questions:
1. Check `ESP32_FIRMWARE.md` troubleshooting section
2. Review `ARCHITECTURE.md` for system design
3. Test components individually before integration
4. Use Serial Monitor to debug ESP32 communication

---

**Setup Complete!** Your LangRover ESP32-based hardware control is ready for deployment.

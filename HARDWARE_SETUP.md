# Hardware Setup Guide - Raspberry Pi 5

Complete wiring guide for LangRover robot on Raspberry Pi 5 with real hardware.

## Hardware Components

### Required Components

1. **Raspberry Pi 5** (4GB or 8GB RAM)
2. **Raspberry Pi AI HAT+** or **AI HAT+ 2** (for local AI inference)
   - **AI HAT+ 2 Recommended** (40 TOPS, local LLM support, includes heatsink)
   - AI HAT+ also supported (13-26 TOPS, vision only)
3. **Pi Camera 3** (for computer vision)
4. **2× L293D Motor Driver ICs** (for 4 DC motors)
5. **4× DC Motors** (6-12V geared motors recommended)
6. **4× HC-SR04 Ultrasonic Sensors** (distance measurement)
7. **Power Supply**:
   - 5V/3A for Raspberry Pi
   - 6-12V battery pack for motors (separate from Pi power)
8. **Breadboard** or **PCB** for connections
9. **Jumper Wires** (male-to-female, male-to-male)
10. **Robot Chassis** with 4 wheels

### Optional Components (Highly Recommended)
- **Raspberry Pi Active Cooler** (fan heatsink for Pi - especially for AI HAT+ 2)
- **AI HAT+ 2 Heatsink** (included with AI HAT+ 2, additional for thermal management)
- Battery level monitor
- Servo for camera pan/tilt
- LED indicators
- Emergency stop button

---

## GPIO Pin Assignments (BCM Numbering)

### Complete Pin Map

```
┌─────────────────────────────────────────────────────────────────┐
│                    RASPBERRY PI 5 GPIO PINOUT                   │
│                      (BCM Numbering Mode)                       │
└─────────────────────────────────────────────────────────────────┘

ULTRASONIC SENSORS (4 sensors):
  Front Sensor:   TRIG = GPIO 23  |  ECHO = GPIO 24
  Left Sensor:    TRIG = GPIO 17  |  ECHO = GPIO 27
  Right Sensor:   TRIG = GPIO 22  |  ECHO = GPIO 10
  Rear Sensor:    TRIG = GPIO 9   |  ECHO = GPIO 11

MOTOR CONTROLLER 1 (Front Motors - L293D #1):
  Front Left Motor:   IN1 = GPIO 5   |  IN2 = GPIO 6   |  EN = GPIO 12 (PWM)
  Front Right Motor:  IN1 = GPIO 13  |  IN2 = GPIO 19  |  EN = GPIO 12 (PWM)

MOTOR CONTROLLER 2 (Rear Motors - L293D #2):
  Rear Left Motor:    IN1 = GPIO 16  |  IN2 = GPIO 20  |  EN = GPIO 18 (PWM)
  Rear Right Motor:   IN1 = GPIO 21  |  IN2 = GPIO 26  |  EN = GPIO 18 (PWM)

CAMERA:
  Pi Camera 3: Uses dedicated CSI connector (not GPIO)

POWER PINS:
  5V:  Multiple pins available (use for sensor VCC)
  GND: Multiple pins available (common ground for all components)
```

---

## Wiring Diagrams

### 1. Ultrasonic Sensors (HC-SR04)

Each sensor needs 4 connections:

```
HC-SR04 Ultrasonic Sensor
┌────────────────────┐
│  VCC  TRIG ECHO GND│
└──┬────┬────┬────┬──┘
   │    │    │    │
   │    │    │    └─── Pi GND
   │    │    └──────── Pi GPIO (ECHO pin)
   │    └───────────── Pi GPIO (TRIG pin)
   └────────────────── Pi 5V

Front Sensor:  TRIG=GPIO23, ECHO=GPIO24
Left Sensor:   TRIG=GPIO17, ECHO=GPIO27
Right Sensor:  TRIG=GPIO22, ECHO=GPIO10
Rear Sensor:   TRIG=GPIO9,  ECHO=GPIO11
```

**Important Notes**:
- HC-SR04 outputs 5V on ECHO pin, but Pi GPIO is 3.3V tolerant
- Use voltage divider (1kΩ + 2kΩ resistors) on ECHO pin to protect Pi
- Or use 3.3V-compatible ultrasonic sensors (HC-SR04P)

**Voltage Divider for ECHO Pin** (if using 5V HC-SR04):
```
HC-SR04 ECHO ──┬── 1kΩ ──┬── Pi GPIO (ECHO)
               │         │
               └── 2kΩ ──┴── GND

Output: 5V × (2kΩ/(1kΩ+2kΩ)) = 3.3V
```

### 2. L293D Motor Controllers

Two L293D chips control 4 motors.

**L293D Pinout** (16-pin DIP):
```
        L293D Motor Driver IC
    ┌────────────────────────┐
 EN1│1                    16│VCC (5V from Pi)
IN1 │2                    15│IN4
OUT1│3                    14│OUT4
GND │4                    13│GND
GND │5                    12│GND
OUT2│6                    11│OUT3
IN2 │7                    10│IN3
VCC2│8                     9│EN2
    └────────────────────────┘
```

**Motor Controller 1 (Front Motors)**:
```
Pi GPIO Connections:
  GPIO 5  → IN1 (Front Left Motor direction)
  GPIO 6  → IN2 (Front Left Motor direction)
  GPIO 13 → IN3 (Front Right Motor direction)
  GPIO 19 → IN4 (Front Right Motor direction)
  GPIO 12 → EN1 & EN2 (PWM speed control for both motors)

Power Connections:
  Pin 16 (VCC)  → Pi 5V (logic power)
  Pin 8 (VCC2)  → Motor battery + (6-12V)
  Pin 4,5,12,13 → Common GND (Pi + Motor battery)

Motor Connections:
  OUT1 & OUT2 → Front Left Motor
  OUT3 & OUT4 → Front Right Motor
```

**Motor Controller 2 (Rear Motors)**:
```
Pi GPIO Connections:
  GPIO 16 → IN1 (Rear Left Motor direction)
  GPIO 20 → IN2 (Rear Left Motor direction)
  GPIO 21 → IN3 (Rear Right Motor direction)
  GPIO 26 → IN4 (Rear Right Motor direction)
  GPIO 18 → EN1 & EN2 (PWM speed control for both motors)

Power Connections:
  Pin 16 (VCC)  → Pi 5V (logic power)
  Pin 8 (VCC2)  → Motor battery + (6-12V)
  Pin 4,5,12,13 → Common GND (Pi + Motor battery)

Motor Connections:
  OUT1 & OUT2 → Rear Left Motor
  OUT3 & OUT4 → Rear Right Motor
```

### 3. Pi Camera 3

```
Pi Camera 3 → CSI Connector on Raspberry Pi 5

No GPIO pins used - uses dedicated camera interface.

Installation:
1. Power off Pi
2. Lift CSI connector latch
3. Insert camera ribbon cable (blue side facing away from board)
4. Close latch
5. Enable camera in raspi-config
```

### 4. AI HAT+ Connection

```
Raspberry Pi AI HAT+
└─── Connects via GPIO header (40-pin)

The HAT uses:
- I2C for communication
- Dedicated pins for AI accelerator
- Does NOT conflict with our GPIO assignments

Our pin assignments avoid AI HAT reserved pins.
```

---

## Physical Wiring Diagram

```
                    ┌──────────────────────┐
                    │   RASPBERRY PI 5     │
                    │    + AI HAT+         │
                    └──────────┬───────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
    ┌───────▼───────┐  ┌──────▼──────┐  ┌────────▼────────┐
    │  L293D #1     │  │  L293D #2   │  │  4× HC-SR04     │
    │  (Front)      │  │  (Rear)     │  │  Sensors        │
    └───┬───────┬───┘  └──┬──────┬───┘  └─────────────────┘
        │       │         │      │               │
    ┌───▼───┐ ┌─▼─────┐ ┌▼────┐ ┌▼──────┐      │
    │ FL    │ │ FR    │ │ RL  │ │ RR    │      │
    │ Motor │ │ Motor │ │Motor│ │ Motor │      │
    └───────┘ └───────┘ └─────┘ └───────┘      │
                                                 │
    ┌────────────────────────────────────────────┘
    │
    ▼
  Mounted on robot chassis pointing:
  - Front: Forward
  - Left/Right: Sideways
  - Rear: Backward
```

---

## Power Supply Recommendations

### Two Separate Power Sources

**1. Raspberry Pi Power** (5V/3A):
- Official Raspberry Pi 5 USB-C power supply
- Powers: Pi, AI HAT+, Camera, L293D logic (VCC)

**2. Motor Power** (6-12V, 2-4A):
- Rechargeable battery pack (Li-Ion, NiMH, or LiPo)
- Powers: DC motors only (L293D VCC2)
- **CRITICAL**: Share common ground with Pi

### Wiring Power

```
Pi 5V Power:
  USB-C → Raspberry Pi
       └→ Breadboard 5V rail
          ├→ L293D #1 Pin 16 (VCC)
          ├→ L293D #2 Pin 16 (VCC)
          └→ HC-SR04 sensors VCC

Motor Battery (6-12V):
  Battery + → L293D #1 Pin 8 (VCC2)
           → L293D #2 Pin 8 (VCC2)
  
  Battery - → Common GND rail
           → Pi GND
           → L293D GND pins
           → Sensor GND pins
```

**⚠️ WARNING**: 
- Never connect motor battery voltage to Pi GPIO pins
- Always use common ground between Pi and motor battery
- Add flyback diodes across motors to protect L293D from back-EMF

---

## Assembly Steps

### Step 0: Install AI HAT+ or AI HAT+ 2 (FIRST!)

**Install BEFORE connecting GPIO components** (AI HAT uses PCIe, not GPIO).

Follow official Raspberry Pi documentation:
1. **Update Pi OS first**:
   ```bash
   sudo apt update && sudo apt full-upgrade -y
   sudo rpi-eeprom-update -a
   sudo reboot
   ```

2. **Mount Active Cooler** (optional but recommended):
   - Attach to Pi 5 before AI HAT
   - Follow Raspberry Pi cooling guide

3. **Install AI HAT+ or AI HAT+ 2**:
   - Connect GPIO stacking header to Pi GPIO
   - Insert PCIe ribbon cable (metallic contacts face inward)
   - Secure HAT with spacers and screws
   - For AI HAT+ 2: Install included heatsink (two push pins, diagonal corners)

4. **Verify installation**:
   ```bash
   hailortcli fw-control identify
   # Should show: Board Name: Hailo-8L or Hailo-10H
   ```

**Important**: AI HAT+ uses **PCIe connector**, not GPIO pins. This does NOT conflict with GPIO-based sensors and motors.

---

### Step 1: Prepare Raspberry Pi
1. Install Raspberry Pi OS (64-bit)
2. **Install AI HAT+ or AI HAT+ 2** (see Step 0 above)
3. Connect Pi Camera 3 to CSI port
4. Update system: `sudo apt update && sudo apt upgrade`

### Step 2: Test GPIO Access
```bash
# Enable GPIO
sudo raspi-config
# Interface Options → Enable I2C, SPI, Camera

# Install Python GPIO library
pip install RPi.GPIO
```

### Step 3: Wire Ultrasonic Sensors
1. Mount sensors on robot chassis (front, left, right, rear)
2. Connect VCC to 5V rail
3. Connect GND to common ground
4. Connect TRIG pins to assigned GPIO
5. Connect ECHO pins through voltage dividers to GPIO

### Step 4: Wire Motor Controllers
1. Place L293D chips on breadboard or PCB
2. Connect Pi GPIO pins to IN1-IN4 and EN pins
3. Connect VCC (Pin 16) to Pi 5V
4. Connect VCC2 (Pin 8) to motor battery positive
5. Connect all GND pins to common ground
6. Connect motors to OUT pins

### Step 5: Connect Power
1. Connect Pi to 5V/3A power supply
2. Connect motor battery to L293D VCC2 inputs
3. **Verify common ground connection**
4. Add power switch to motor battery for easy shutoff

### Step 6: Test Hardware
```bash
# Test pin configuration display
python hardware/pins.py

# Test ultrasonic sensors
python hardware/sensors.py

# Test motors (robot on blocks!)
python hardware/motors.py

# Test robot actions
python actions/gpio_actions.py
```

---

## Safety Considerations

### Electrical Safety
- ✓ Use appropriate wire gauge (22-24 AWG for signals, 18-20 AWG for motors)
- ✓ Add fuse to motor battery circuit (3-5A fast-blow fuse)
- ✓ Use heatsinks on L293D chips if running at high current
- ✓ Ensure common ground between all power sources

### Mechanical Safety
- ✓ Secure all wiring with zip ties or wire clips
- ✓ Mount Pi and components to chassis securely
- ✓ Add emergency stop button (connects to GPIO, stops all motors)
- ✓ Test on blocks before floor operation
- ✓ Add bumpers or protective casing

### Software Safety
- ✓ Implement timeout on motor commands
- ✓ Emergency stop on camera-detected people (already implemented)
- ✓ Watchdog timer to stop motors if software crashes
- ✓ Limit maximum motor speed in code

---

## Troubleshooting

### Motors Don't Run
- Check motor battery voltage (should be 6-12V)
- Verify EN pins are connected and receiving PWM
- Test motors directly with battery to confirm they work
- Check L293D is not overheating

### Sensors Return No Data
- Verify 5V and GND connections
- Check voltage dividers on ECHO pins
- Test sensor with multimeter (ECHO should pulse 3.3V)
- Ensure TRIG and ECHO pins not swapped

### GPIO Errors
- Confirm BCM mode in code (`GPIO.setmode(GPIO.BCM)`)
- Check no pin conflicts with AI HAT+
- Run as root or add user to `gpio` group
- Verify pin numbers match physical connections

### AI HAT+ Not Detected
- Check HAT is seated firmly on GPIO header
- Update Raspberry Pi firmware
- Install AI HAT+ drivers from official source
- Verify I2C is enabled in raspi-config

---

## Next Steps

After hardware assembly:

1. **Calibrate Movement**: Run calibration tool
   ```bash
   python actions/gpio_actions.py
   ```

2. **Test Vision**: Verify camera and object detection
   ```bash
   python vision/camera.py
   ```

3. **Configure for Hardware**: Update `config.py`
   ```python
   USE_GPIO_ACTIONS = True
   USE_REAL_CAMERA = True
   USE_REAL_VISION = True
   ```

4. **Run Robot**: Execute main program
   ```bash
   python main.py
   ```

---

## Pin Reference Quick Guide

Print and keep handy during assembly:

```
FRONT SENSOR:  GPIO 23 (TRIG), GPIO 24 (ECHO)
LEFT SENSOR:   GPIO 17 (TRIG), GPIO 27 (ECHO)
RIGHT SENSOR:  GPIO 22 (TRIG), GPIO 10 (ECHO)
REAR SENSOR:   GPIO 9  (TRIG), GPIO 11 (ECHO)

FRONT LEFT:    GPIO 5, 6   (EN: GPIO 12)
FRONT RIGHT:   GPIO 13, 19 (EN: GPIO 12)
REAR LEFT:     GPIO 16, 20 (EN: GPIO 18)
REAR RIGHT:    GPIO 21, 26 (EN: GPIO 18)
```

---

**Need help?** See [HARDWARE_TROUBLESHOOTING.md](HARDWARE_TROUBLESHOOTING.md) for detailed debugging steps.

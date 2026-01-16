# 📋 Hardware Quick Reference Card

**Print this page and keep it handy during assembly!**

---

## GPIO Pin Assignments (BCM Mode)

### Ultrasonic Sensors (HC-SR04)

| Sensor | TRIG Pin | ECHO Pin | Mounting |
|--------|----------|----------|----------|
| **Front** | GPIO 23 | GPIO 24 | Forward-facing |
| **Left** | GPIO 17 | GPIO 27 | Left side |
| **Right** | GPIO 22 | GPIO 10 | Right side |
| **Rear** | GPIO 9 | GPIO 11 | Backward-facing |

**Each sensor needs**: VCC (5V), GND, TRIG, ECHO
**Important**: Use voltage divider on ECHO pins (1kΩ + 2kΩ resistors)

---

### Motor Controllers (L293D)

#### Controller #1 (Front Motors)

| Motor | IN1 | IN2 | EN (PWM) |
|-------|-----|-----|----------|
| **Front Left** | GPIO 5 | GPIO 6 | GPIO 12 |
| **Front Right** | GPIO 13 | GPIO 19 | GPIO 12 |

#### Controller #2 (Rear Motors)

| Motor | IN1 | IN2 | EN (PWM) |
|-------|-----|-----|----------|
| **Rear Left** | GPIO 16 | GPIO 20 | GPIO 18 |
| **Rear Right** | GPIO 21 | GPIO 26 | GPIO 18 |

**L293D Power**:
- Pin 16 (VCC) → Pi 5V
- Pin 8 (VCC2) → Motor Battery (6-12V)
- Pins 4,5,12,13 (GND) → Common Ground

---

## Power Connections

### Raspberry Pi
- **USB-C 5V/3A** power supply
- Powers: Pi, AI HAT+, Camera, L293D logic

### Motor Battery
- **6-12V, 2-4A** rechargeable battery
- Powers: DC motors only
- **⚠️ CRITICAL**: Share common ground with Pi!

---

## Quick Test Commands

```bash
# Display pin configuration
python hardware/pins.py

# Test ultrasonic sensors
python hardware/sensors.py

# Test motors (ROBOT ON BLOCKS!)
python hardware/motors.py

# Test camera
python vision/camera.py

# Calibrate movement
python actions/gpio_actions.py
```

---

## Environment Variables

### Laptop (Simulation)
```bash
# Default - no configuration needed
python main.py
```

### Pi 5 (Real Hardware)
```bash
export USE_GPIO_ACTIONS=true
export USE_REAL_SENSORS=true
export USE_REAL_CAMERA=true
export USE_REAL_VISION=true
python main.py
```

### Pi 5 + AI HAT+ (Autonomous)
```bash
export USE_GPIO_ACTIONS=true
export USE_REAL_SENSORS=true
export USE_REAL_CAMERA=true
export USE_REAL_VISION=true
export LLM_PROVIDER=hailo
export HAILO_MODEL_PATH=/home/pi/models/tinyllama-1.1b.Q4_K_M.gguf
python main.py
```

---

## Component Checklist

### Before Assembly

- [ ] Raspberry Pi 5 (4GB or 8GB)
- [ ] Raspberry Pi AI HAT+
- [ ] Pi Camera 3
- [ ] 4× HC-SR04 ultrasonic sensors
- [ ] 2× L293D motor driver ICs
- [ ] 4× DC geared motors (6-12V)
- [ ] Robot chassis with 4 wheels
- [ ] 5V/3A USB-C power supply
- [ ] 6-12V battery pack for motors
- [ ] Breadboard or PCB
- [ ] ~40 jumper wires
- [ ] 4× voltage dividers (1kΩ + 2kΩ resistors)
- [ ] Optional: Emergency stop button

### Wiring Checklist

- [ ] All ultrasonic sensors connected (VCC, GND, TRIG, ECHO)
- [ ] Voltage dividers on all ECHO pins
- [ ] L293D #1: Power, IN pins, motor connections
- [ ] L293D #2: Power, IN pins, motor connections
- [ ] Common ground between Pi and motor battery
- [ ] Pi Camera 3 connected to CSI port
- [ ] AI HAT+ seated on GPIO header
- [ ] Power supplies connected
- [ ] All connections secure with zip ties

---

## Safety Checklist

- [ ] Voltage dividers protect Pi GPIO (3.3V max)
- [ ] Common ground connected (Pi + motor battery)
- [ ] Motor power separate from Pi power
- [ ] Fuse added to motor battery circuit (3-5A)
- [ ] All wiring secured to chassis
- [ ] Emergency stop button accessible
- [ ] Tested on blocks before floor operation
- [ ] People detection safety protocol active

---

## Pin Reference Diagram

```
┌───────────────────────────────────────────┐
│  RASPBERRY PI 5 GPIO HEADER (40 pins)     │
│         (Top view, BCM numbering)         │
└───────────────────────────────────────────┘

Used GPIO Pins:
  5, 6, 9, 10, 11, 12, 13, 16, 17, 18,
  19, 20, 21, 22, 23, 24, 26, 27

PWM-Capable Pins Used:
  GPIO 12 (Front motors EN)
  GPIO 18 (Rear motors EN)

5V Pins: Multiple available
GND Pins: Multiple available
CSI: Camera connector (not GPIO)
```

---

## Troubleshooting Quick Guide

| Problem | Check |
|---------|-------|
| Motors don't run | Battery voltage, EN pins, L293D heat |
| Sensors return None | VCC/GND, voltage dividers, pin swap |
| GPIO errors | BCM mode, pin conflicts, permissions |
| Camera not found | CSI connection, raspi-config enable |
| AI HAT+ not detected | GPIO seating, I2C enable, firmware |

---

## Calibration Values

**Fill in after calibration** (`python actions/gpio_actions.py`):

Forward movement:
- Speed: _____ cm/s at 70% power
- Update: `distance / SPEED` in gpio_actions.py

Rotation:
- Speed: _____ deg/s at 70% power
- Update: `degrees / SPEED` in gpio_actions.py

---

## Documentation Links

- **Wiring Guide**: [HARDWARE_SETUP.md](HARDWARE_SETUP.md)
- **AI HAT+ Setup**: [AI_HAT_SETUP.md](AI_HAT_SETUP.md)
- **Complete Delivery**: [HARDWARE_DELIVERY.md](HARDWARE_DELIVERY.md)
- **Main README**: [README.md](README.md)

---

**🤖 Build Date**: __________________

**✅ Assembly Complete**: [ ]
**✅ Tests Passed**: [ ]
**✅ Calibrated**: [ ]
**✅ Ready to Run**: [ ]

---

**Need help?** See HARDWARE_SETUP.md troubleshooting section.

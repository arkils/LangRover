# LangRover - Hardware-Agnostic Autonomous Robot Framework

LangRover is a Python framework for building autonomous robots that run on laptops using simulated sensors and can be deployed to real hardware (Raspberry Pi + ESP32) without changing decision-making logic.

## 🎯 Overview

LangRover separates the robot's cognitive layer (LangChain agent) from the hardware layer (motors, sensors, actuators). This allows:

- **Development on laptops** using simulated sensors and CLI output
- **ESP32-based hardware control** for reliable, real-time motor and sensor operations
- **Easy transition to real hardware** via abstracted interfaces
- **LLM provider flexibility** (OpenAI, local models via Ollama, on-device with Hailo)
- **Vision capabilities** with YOLO object detection and people safety features

## 🏗️ Architecture

### New: ESP32-Based Hardware Architecture

```
┌──────────────────────────────────────────────────┐
│  Raspberry Pi 5 - High-Level Intelligence        │
│  - LangChain Agent (Decision Making)             │
│  - Vision Processing (YOLO)                      │
│  - LLM (Ollama/OpenAI/Hailo)                     │
└───────────────────┬──────────────────────────────┘
                    │ USB Serial (JSON)
┌───────────────────┴──────────────────────────────┐
│  ESP32 - Hardware Control Layer                  │
│  - Dual-Core Processing (Core 0/1)               │
│  - Motor Control (TB6612FNG drivers)             │
│  - Sensor Reading (Ultrasonic)                   │
│  - Real-time GPIO operations                     │
└───────────────────┬──────────────────────────────┘
                    │ GPIO
┌───────────────────┴──────────────────────────────┐
│  Robotic Hardware                                │
│  - 4x DC Motors                                  │
│  - 4x HC-SR04 Ultrasonic Sensors                 │
│  - L293D Motor Driver ICs                        │
└──────────────────────────────────────────────────┘
```

### Software Architecture

```
┌─────────────────────────────────────────────┐
│  brain/agent.py - LangChain Agent           │
│  (Structured Chat ReAct Zero Shot)          │
└─────────────────────────────────────────────┘
         ↓ (tools)           ↓ (sensors)
┌─────────────────────┐    ┌──────────────────┐
│ actions/            │    │ world/           │
│ - RobotActions      │    │ - WorldState     │
│   (abstract)        │    │ - read_world_    │
│ - CLIRobotActions   │    │   state()        │
│   (CLI impl)        │    │ - simulator      │
│ - GPIORobotActions  │    │                  │
│   (ESP32 impl)      │    │                  │
└─────────────────────┘    └──────────────────┘
         ↓                       ↓
┌─────────────────────┐    ┌──────────────────┐
│ hardware/           │    │ vision/          │
│ - esp32_serial.py   │    │ - camera.py      │
│ - motors.py         │    │ - detector.py    │
│ - sensors.py        │    │ - vision.py      │
└─────────────────────┘    └──────────────────┘
```

### Modules

- **`brain/`** - LangChain agent and prompts
  - `agent.py` - Agent creation and execution loop
  - `prompts.py` - System prompts with constraints and strategy
  
- **`world/`** - Environment simulation and state management
  - `state.py` - `WorldState` Pydantic model (sensor readings + vision)
  - `simulator.py` - Simulated sensor data generator
  
- **`actions/`** - Robot control interface
  - `base.py` - Abstract `RobotActions` interface
  - `cli_actions.py` - CLI implementation (prints actions)
  - `gpio_actions.py` - Hardware implementation (ESP32 control)
  
- **`hardware/`** - ESP32 communication and hardware abstraction
  - `esp32_serial.py` - USB serial communication with ESP32
  - `motors.py` - Motor control via ESP32
  - `sensors.py` - Sensor reading via ESP32
  - `pins.py` - ESP32 GPIO pin configuration
  
- **`vision/`** - Computer vision and object detection
  - `camera.py` - Camera interface (PiCamera3/Mock)
  - `detector.py` - Vision detection (YOLO/Mock)
  - `vision.py` - Vision system integration
  
- **`models/`** - LLM provider factory
  - `llm.py` - Centralized LLM instantiation (supports OpenAI, Ollama, Hailo)
  
- **`config.py`** - Configuration from environment variables
- **`main.py`** - Main control loop

## Installation

### Prerequisites

- Python 3.10+
- Ollama (for local models) - Download from [ollama.ai](https://ollama.ai)
- gemma3:270m model installed locally

### Quick Start (Recommended)

One command to set up everything:

**On Windows (PowerShell):**
```powershell
.\setup.ps1
```

This will:
- ✓ Create isolated virtual environment in `./venv/`
- ✓ Install all dependencies locally
- ✓ Check Ollama installation
- ✓ Pull gemma3:270m model (if not already installed)

**On Linux/macOS (bash):**
```bash
chmod +x setup.sh
./setup.sh
```

### Run the Project

After setup, start the project with:

**Windows:**
```powershell
.\run.ps1
```

**Linux/macOS:**
```bash
chmod +x run.sh
./run.sh
```

The `run` script will:
1. ✓ Activate the virtual environment
2. ✓ Check if Ollama is running (start it if needed)
3. ✓ Verify gemma3:270m model exists
4. ✓ Run the robot simulation

**Everything happens automatically!** No manual setup needed.

### Manual Setup (Optional)

If you prefer manual control:

1. Navigate to project:
```bash
cd /path/to/LangRover
```

2. Create isolated virtual environment in project directory:
```bash
python -m venv venv
```

3. Activate the environment:
```bash
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Linux/macOS
source venv/bin/activate
```

4. Install dependencies locally (only in venv/):
```bash
pip install -r requirements.txt
```

5. Start Ollama (in separate terminal):
```bash
ollama serve
```

6. Run the project:
```bash
python main.py
```

### Deactivate Virtual Environment

When done, deactivate the environment to return to system Python:
```bash
deactivate
```

**All dependencies are installed exclusively in `./venv/` and never globally.**

## Usage

### Default: Local Ollama with gemma3:270m

The project is configured to use your local Ollama instance by default. No API keys needed!

**Start everything in one command:**

```powershell
# Windows
.\run.ps1
```

```bash
# Linux/macOS
./run.sh
```

This will:
- ✓ Activate virtual environment
- ✓ Check Ollama is running (start if needed)
- ✓ Pull gemma3:270m model if missing
- ✓ Run the agent

### Using Different Ollama Models

Run with a different model:

```powershell
# Windows
.\run.ps1 -Model "mistral"
```

```bash
# Linux/macOS
./run.sh --model mistral
```

List available models:
```bash
ollama list
```

### Using OpenAI Instead of Ollama

Set environment variable:

**Windows:**
```powershell
$env:LLM_PROVIDER = "openai"
$env:OPENAI_API_KEY = "sk-..."
python main.py
```

**Linux/macOS:**
```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...
python main.py
```

### Skip Ollama Checks

If Ollama is already running and you just want to run the project:

**Windows:**
```powershell
.\run.ps1 -NoOllama
```

**Linux/macOS:**
```bash
./run.sh --no-ollama
```

### Example output

```
============================================================
🤖 LangRover - Autonomous Robot Framework
============================================================
LLM Provider: openai
Simulation Steps: 10
============================================================

--- Decision Cycle 1 ---
📡 Sensors: Front: 156.34cm | Left: 89.42cm | Right: 234.56cm | Target visible: False

> Entering new AgentExecutor...
> Invoking: `turn_left` with `{'degrees': 45}`
🤖 Turning left 45 degrees
✓ Agent decision executed

--- Decision Cycle 2 ---
...
```

## Configuration

### Default Configuration

LangRover is configured to use **Ollama with gemma3:270m** by default.

```
LLM_PROVIDER = "ollama"      # Default: Local Ollama
OLLAMA_MODEL = "gemma3:270m" # Your model
OLLAMA_BASE_URL = "http://localhost:11434"
```

**No environment variables needed** - it just works!

### Customize with Environment Variables

**Windows (PowerShell):**

```powershell
# Use different Ollama model
$env:OLLAMA_MODEL = "mistral"

# Use remote Ollama instance
$env:OLLAMA_BASE_URL = "http://192.168.1.100:11434"

# Switch to OpenAI
$env:LLM_PROVIDER = "openai"
$env:OPENAI_API_KEY = "sk-..."

# Simulation settings
$env:SIMULATION_STEPS = "20"
$env:DECISION_CYCLE_DELAY = "2"
$env:VERBOSE = "true"

python main.py
```

**Linux/macOS (bash):**

```bash
# Use different Ollama model
export OLLAMA_MODEL=mistral

# Use remote Ollama instance
export OLLAMA_BASE_URL=http://192.168.1.100:11434

# Switch to OpenAI
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...

# Simulation settings
export SIMULATION_STEPS=20
export DECISION_CYCLE_DELAY=2
export VERBOSE=true

python main.py
```

### Using .env File

1. Copy the example:
```bash
cp .env.example .env
```

2. Edit `.env` and configure:
```env
# Ollama settings
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:270m

# Or switch to OpenAI
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-...

SIMULATION_STEPS=10
DECISION_CYCLE_DELAY=1
VERBOSE=true
```

3. Run the project (settings auto-loaded):
```bash
python main.py
```

### Configuration Defaults

| Setting | Default | Purpose |
|---------|---------|---------|
| `LLM_PROVIDER` | `ollama` | Which LLM to use |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `gemma3:270m` | Which model to use |
| `SIMULATION_STEPS` | `10` | Number of decision cycles |
| `DECISION_CYCLE_DELAY` | `1` | Seconds between cycles |
| `VERBOSE` | `true` | Show agent reasoning |
| `USE_REAL_CAMERA` | `false` | Use Pi Camera 3 vs mock |
| `USE_REAL_VISION` | `false` | Use YOLO detection vs mock |
| `YOLO_MODEL` | `nano` | YOLO model size (nano/small/medium/large) |

## Vision System

LangRover includes **computer vision capabilities** with object and person detection:

### Features

- **Object Detection**: Identify cups, chairs, people, etc.
- **Person Detection**: Count people in view with safety protocols
- **Motion Detection**: Detect movement in the environment
- **Confidence Scoring**: Each detection includes confidence level
- **Safety First**: Robot automatically stops if people detected

### Quick Start

```powershell
# Just run it - uses mock vision by default
.\run.ps1
```

Output shows detected objects:
```
[SENSORS] Front: 360cm | Objects: chair(82%), person(95%) | People: 1
[SAFETY] People detected! Stopping immediately.
```

### Using Real Vision (Raspberry Pi)

Install real vision detection:
```bash
pip install ultralytics opencv-python picamera2
```

Enable in environment:
```powershell
$env:USE_REAL_CAMERA = "true"
$env:USE_REAL_VISION = "true"
python main.py
```

### Vision Architecture

- **Mock Detector** (Laptop): Simulates realistic detections
- **YOLO Detector** (Real): Uses YOLOv8 for real object detection  
- **Pi Camera 3**: Official Raspberry Pi camera support
- **Mock Camera** (Laptop): Simulates camera without hardware

### Learn More

See [VISION.md](VISION.md) for comprehensive documentation and [VISION_QUICKSTART.md](VISION_QUICKSTART.md) for quick examples.

## Hardware Deployment (Raspberry Pi 5 + ESP32)

LangRover supports **real hardware deployment** with ESP32-based motor and sensor control.

### Hardware Architecture

```
Raspberry Pi 5 (Brain)
    ↓ USB Serial
ESP32 (Hardware Controller)
    ↓ GPIO
Motors & Sensors
```

The ESP32 provides:
- ✅ Dual-core processing (Core 0: motors, Core 1: sensors)
- ✅ Real-time motor control with instant response
- ✅ Continuous sensor monitoring at 10Hz
- ✅ Reliable sensor readings with auto-broadcast
- ✅ Electrical isolation from Pi
- ✅ Hardware safety features
- ✅ Simple JSON communication over USB serial

### Required Hardware

**Computing:**
- **Raspberry Pi 5** (4GB or 8GB RAM) - High-level intelligence
- **ESP32 Development Board** - Hardware controller
- **Raspberry Pi AI HAT+** (optional - for local AI inference)
- **Pi Camera 3** (optional - for computer vision)

**Motors & Drivers:**
- **4× DC Motors** (6-12V geared motors)
- **2× TB6612FNG Motor Driver Boards** (dual motor drivers, 1.2A per channel)
- **Robot Chassis** with 4 wheels

**Sensors:**
- **4× HC-SR04 Ultrasonic Sensors** (distance measurement)

**Power & Connectivity:**
- **USB Cable** (Pi to ESP32 - must support data)
- **Power supplies** (5V for Pi/ESP32, 6-12V for motors)

### ESP32 GPIO Pin Assignments

**IMPORTANT**: These are ESP32 GPIO pins, NOT Raspberry Pi pins!

```
ULTRASONIC SENSORS (ESP32):
  Front:  TRIG=GPIO23, ECHO=GPIO34 (input-only)
  Left:   TRIG=GPIO18, ECHO=GPIO35 (input-only)
  Right:  TRIG=GPIO17, ECHO=GPIO36 (input-only)
  Rear:   TRIG=GPIO16, ECHO=GPIO39 (input-only)

TB6612FNG DRIVER 1 (Front Motors):
  Front Left:   AIN1=GPIO25, AIN2=GPIO26, PWMA=GPIO27
  Front Right:  BIN1=GPIO14, BIN2=GPIO12, PWMB=GPIO13
  Standby:      STBY=GPIO21 (must be HIGH)

TB6612FNG DRIVER 2 (Rear Motors):
  Rear Left:    AIN1=GPIO33, AIN2=GPIO32, PWMA=GPIO15
  Rear Right:   BIN1=GPIO5,  BIN2=GPIO4,  PWMB=GPIO2
  Standby:      STBY=GPIO22 (must be HIGH)
```

### Hardware Setup Guide

**Quick Start:**
1. **[TB6612FNG_SETUP.md](TB6612FNG_SETUP.md)** - TB6612FNG motor driver setup and configuration
2. **[ESP32_FIRMWARE.md](ESP32_FIRMWARE.md)** - Complete ESP32 firmware guide
3. **[esp32_firmware_template.ino](esp32_firmware_template.ino)** - Ready-to-upload Arduino code

**Detailed Documentation:**
- **[HARDWARE_SETUP.md](HARDWARE_SETUP.md)** - Full wiring guide with diagrams
- **[AI_HAT_SETUP.md](AI_HAT_SETUP.md)** - AI HAT+ configuration for local models
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and communication protocol

### Quick Hardware Start

**1. Upload ESP32 Firmware**
```bash
# Using Arduino IDE
# 1. Install Arduino IDE 2.x
# 2. Add ESP32 board support
# 3. Install ArduinoJson library
# 4. Open esp32_firmware_template.ino
# 5. Upload to ESP32

# Or use PlatformIO (recommended)
# See ESP32_FIRMWARE.md for complete instructions
```

**2. Connect Hardware** (see [ESP32_FIRMWARE.md](ESP32_FIRMWARE.md))
- Connect ESP32 to Raspberry Pi via USB
- Wire motors to ESP32 GPIO
- Wire sensors to ESP32 GPIO

**3. Install Python Dependencies**
```bash
pip install pyserial  # Required for ESP32 communication
# Optional: pip install picamera2 ultralytics opencv-python
```

**4. Configure for Hardware Mode**
```bash
export USE_GPIO_ACTIONS=true
export USE_REAL_SENSORS=true
export ESP32_SERIAL_PORT=/dev/ttyACM0  # or COM3 on Windows
python main.py
```

**5. Test Components**
```bash
# Test ESP32 connection
python -c "from hardware.esp32_serial import get_esp32; print('Connected!' if get_esp32().is_available() else 'Not connected')"

# Test motors (robot on blocks!)
python hardware/motors.py

# Test sensors
python hardware/sensors.py

# Test camera (optional)
python vision/camera.py
```

### AI HAT+ / AI HAT+ 2 for Local Inference

Run AI models locally on Raspberry Pi 5 with hardware acceleration:

**AI HAT+ (13-26 TOPS)**: Vision and object detection
```bash
# Install Hailo drivers
sudo apt install hailo-all

# Configure for vision tasks
export LLM_PROVIDER=openai      # Use cloud LLM for decisions
python main.py
```

**AI HAT+ 2 (40 TOPS, Recommended)**: Vision + Local LLMs
```bash
# Install Hailo SDK
sudo apt install hailo-all

# Download local model
ollama pull tinyllama

# Run fully autonomous (no cloud needed!)
export LLM_PROVIDER=hailo
export HAILO_DEVICE=hailo10h
export HAILO_MODEL_PATH=/home/pi/models/tinyllama-1.1b.Q4_K_M.gguf
python main.py
```

| Feature | AI HAT+ | AI HAT+ 2 |
|---------|---------|-----------|
| **TOPS** | 13-26 | 40 |
| **Vision/Detection** | ✅ | ✅ |
| **Local LLM Support** | ❌ | ✅ |
| **Onboard Memory** | None | 8GB SDRAM |
| **Heatsink Included** | Optional | ✅ Required |

See [AI_HAT_SETUP.md](AI_HAT_SETUP.md) for complete setup and model recommendations.

### Configuration for Hardware

Environment variables for hardware deployment:

```bash
# Hardware Control
USE_GPIO_ACTIONS=true           # Use real motors via GPIO
USE_REAL_SENSORS=true           # Use real ultrasonic sensors
USE_REAL_CAMERA=true            # Use Pi Camera 3
USE_REAL_VISION=true            # Use YOLO detection

# Motor Settings
DEFAULT_MOTOR_SPEED=70          # Speed percentage (0-100)

# AI Settings (choose your HAT)
HAILO_DEVICE=hailo10h           # AI HAT+ 2 (recommended: 40 TOPS)
LLM_PROVIDER=hailo              # Use local LLM on AI HAT+ 2
HAILO_MODEL_PATH=/path/to/tinyllama-1.1b.Q4_K_M.gguf

# Alternative: AI HAT+ (vision only)
# HAILO_DEVICE=hailo8l          # AI HAT+ (13 TOPS)
# LLM_PROVIDER=openai           # Use cloud LLM
```

### Hardware Safety Features

Built-in safety protocols:
- ✓ People detection → immediate motor stop
- ✓ Obstacle avoidance via ultrasonic sensors
- ✓ Motor timeout protection
- ✓ GPIO cleanup on shutdown
- ✓ Emergency stop on keyboard interrupt

## Extending to Real Hardware

The hardware abstraction is already implemented! The system automatically:

1. **Detects hardware availability** - Falls back to simulation if GPIO unavailable
2. **Uses real sensors** when `USE_REAL_SENSORS=true`
3. **Controls motors via GPIO** when `USE_GPIO_ACTIONS=true`
4. **Integrates vision** with Pi Camera 3 and YOLO detection

**No code changes needed** to `brain/agent.py` or decision-making logic—the abstraction keeps intelligence hardware-agnostic.

## Switching LLM Providers

Change provider without touching agent logic:

```python
# main.py - just change this line
agent = create_agent(robot_actions, llm_provider="ollama")
```

Supported:
- **"openai"** - Uses gpt-4o-mini (requires `OPENAI_API_KEY`)
- **"ollama"** - Uses llama3 locally (requires Ollama installed and running)

Add new providers in `models/llm.py` without modifying the agent.

## Safety Constraints

The agent is configured with safety rules via `brain/prompts.py`:

- **Minimum safe distance**: 30 cm before obstacles
- **Critical distance**: 25 cm triggers stop
- **Max forward movement**: 100 cm per action
- **One action per cycle**: Enforced by `AgentExecutor(max_iterations=1)`

## Development

### Project structure verified

```
LangRover/
├── main.py                   # Entry point
├── config.py                 # Configuration
├── requirements.txt          # Dependencies
├── README.md                 # This file
├── .gitignore                # Git exclusions
│
├── brain/
│   ├── __init__.py
│   ├── agent.py              # LangChain agent + executor
│   └── prompts.py            # System prompt with constraints
│
├── world/
│   ├── __init__.py
│   ├── state.py              # WorldState Pydantic model
│   └── simulator.py          # read_world_state() function
│
├── actions/
│   ├── __init__.py
│   ├── base.py               # RobotActions abstract class
│   └── cli_actions.py        # CLIRobotActions implementation
│
└── models/
    ├── __init__.py
    └── llm.py                # get_llm() factory function
```

### Testing

Run the simulation:
```bash
python main.py
```

Test with Ollama:
```bash
LLM_PROVIDER=ollama python main.py
```

## Limitations (Intentional)

- No real GPIO or hardware dependencies
- Sensors return random but realistic values in CLI mode
- Agent decisions based on simulation—not validated against real physics
- Single robot instance (can be extended to multi-robot swarms)

## Future Enhancements

- [ ] Multi-agent coordination
- [ ] Persistent memory/learning
- [ ] Visual perception system (mock camera data)
- [ ] Path planning module
- [ ] Real hardware implementations (ROS integration)
- [ ] Logging and replay system
- [ ] Web UI for monitoring

## License

MIT

## Contributing

This is a starter framework. Extend as needed for your robotics experiments!

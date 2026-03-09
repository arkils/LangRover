# LangRover System Architecture

## Hardware Architecture Overview

**NEW: ESP32-Based Architecture**

The system now uses a 3-tier architecture:

1. **Raspberry Pi 5** - High-level intelligence (LLM, vision processing, decision making)
2. **ESP32 Microcontroller** - Low-level hardware control (motors, sensors)
3. **Robotic Hardware** - Motors (L293D drivers) and Sensors (HC-SR04 ultrasonic)

**Communication Flow:**
```
Raspberry Pi 5 ←→ USB Serial (CDC) ←→ ESP32 ←→ GPIO ←→ Motors/Sensors
```

**Why ESP32?**
- **Real-time control**: ESP32 handles time-critical sensor readings and motor control
- **Isolation**: Protects Raspberry Pi from electrical noise and hardware failures
- **Reliability**: ESP32 can continue safety operations even if Pi crashes
- **Simplicity**: Clean serial protocol reduces Pi GPIO complexity

## System Overview Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    LANGROVER AUTONOMOUS ROBOT                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    DECISION-MAKING LAYER                        │
│                        (brain/)                                 │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  LLM Agent (LangChain tool calling)                      │  │
│  │  - Reads: WorldState (sensors + vision)                 │  │
│  │  - Consults: gemma3:270m / OpenAI via bind_tools()      │  │
│  │  - Navigation tools: move_forward | turn_left |         │  │
│  │    turn_right | stop                                     │  │
│  │  - Skill tools: greet_cat | greet_dog |                 │  │
│  │    person_safety_stop | <your custom skills>            │  │
│  │  - Safety Check: People detected → STOP immediately    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Skill Registry (skills/)                                │  │
│  │  - Registered skills exposed as LangChain tools         │  │
│  │  - Triggered by YOLO-detected object classes            │  │
│  │  - Extensible: subclass Skill, call registry.register() │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  System Prompts (prompts.py)                             │  │
│  │  - Robot constraints & safety rules                      │  │
│  │  - Vision-aware behavior strategy                        │  │
│  │  - RELEVANT SKILLS hint injected per cycle              │  │
│  │  - PEOPLE DETECTION = HIGHEST PRIORITY                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    SENSOR INPUT LAYER                           │
│                        (world/)                                 │
│                                                                 │
│  ┌──────────────────────────┐  ┌──────────────────────────┐   │
│  │  Distance Sensors        │  │  Vision System (NEW!)    │   │
│  │  ├─ Front distance       │  │  ├─ Objects detected    │   │
│  │  ├─ Left distance        │  │  ├─ People count        │   │
│  │  └─ Right distance       │  │  ├─ Faces detected      │   │
│  │                          │  │  ├─ Motion detected     │   │
│  │  ┌──────────────────┐    │  │  └─ Frame quality       │   │
│  │  │ Target Visible?  │    │  └──────────────────────────┘   │
│  │  └──────────────────┘    │                                 │
│  └──────────────────────────┘                                 │
│                 ↓                           ↓                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  WorldState (state.py)                                   │  │
│  │  ├─ front_distance_cm: float                             │  │
│  │  ├─ left_distance_cm: float                              │  │
│  │  ├─ right_distance_cm: float                             │  │
│  │  ├─ target_visible: bool                                 │  │
│  │  └─ vision: VisionData (NEW!)                            │  │
│  │      ├─ objects: List[DetectedObject]                    │  │
│  │      ├─ people_count: int                                │  │
│  │      ├─ has_faces: bool                                  │  │
│  │      ├─ motion_detected: bool                            │  │
│  │      └─ frame_quality: float                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    VISION PROCESSING LAYER                      │
│                         (vision/)                               │
│                                                                 │
│  ┌──────────────────────────┐  ┌──────────────────────────┐   │
│  │  Camera Input            │  │  Vision Detector         │   │
│  │  ├─ PiCamera3 (real)    │  │  ├─ MockVisionDetector  │   │
│  │  └─ MockCamera (test)   │  │  │   (laptop testing)    │   │
│  │                          │  │  └─ YOLOVisionDetector  │   │
│  │  get_camera() factory    │  │     (real detection)    │   │
│  └──────────────────────────┘  └──────────────────────────┘   │
│                 ↓                           ↓                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  VisionData                                              │  │
│  │  Objects detected with:                                  │  │
│  │  - Name (person, dog, cat, cup, etc.)                   │  │
│  │  - Confidence (0.0-1.0)                                 │  │
│  │  - Position (x, y normalized 0-1)                       │  │
│  │  - Size (width, height normalized 0-1)                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTION LAYER                              │
│                        (actions/)                               │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  RobotActions Interface (base.py)                        │  │
│  │  - Abstract interface for all robot actions             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CLIRobotActions (cli_actions.py)                        │  │
│  │  ├─ move_forward(distance)   → "[ACTION] Moving..."     │  │
│  │  ├─ turn_left(degrees)        → "[ACTION] Turning..."   │  │
│  │  ├─ turn_right(degrees)       → "[ACTION] Turning..."   │  │
│  │  └─ stop()                    → "[ACTION] Stopping..."  │  │
│  │                                                           │  │
│  │  GPIORobotActions (gpio_actions.py)                      │  │
│  │  └─ Same interface → real ESP32 motor commands          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Output                                                  │  │
│  │  └─ Terminal / GPIO / Motor Control                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Control Flow Diagram

```
START
  ↓
[main.py] - Main control loop
  ↓
REPEAT (10 cycles):
  ├─ [world/simulator.py] read_world_state()
  │   ├─ Generate/read distance sensors
  │   ├─ [vision/vision.py] get_vision_detector().detect()
  │   │   ├─ If USE_REAL_VISION: YOLOVisionDetector (Pi Camera frame)
  │   │   └─ Else: MockVisionDetector
  │   └─ Return WorldState with vision data
  │
  ├─ [brain/agent.py] decide_and_act(world_state)
  │   ├─ SAFETY: people_count > 0? → robot_actions.stop(); return
  │   │
  │   ├─ Build nav tools   (move_forward, turn_left, turn_right, stop)
  │   ├─ Build skill tools (greet_cat, greet_dog, person_safety_stop, ...)
  │   ├─ Inject RELEVANT SKILLS hint for detected objects
  │   ├─ Call llm.bind_tools(nav_tools + skill_tools).invoke(messages)
  │   ├─ If tool_calls in response → execute each tool in order
  │   └─ Else (plain text fallback) → parse and execute action
  │
  └─ Display results
     [SENSORS]  Front: 360cm | Objects: cat(88%) | People: 0
     [TOOL]     greet_cat({})
     [SKILL]    Hello, cat! =^.^=
     [ACTION]   Turning left 20 degrees
     [ACTION]   Turning right 40 degrees
     [ACTION]   Turning left 20 degrees
     [SKILL]    greet_cat complete: Cat greeted with a friendly wiggle

END
```

## Data Flow Diagram

```
┌──────────────┐
│ WORLD STATE  │ Contains:
└──────────────┘ - Distance: front, left, right (cm)
       │         - Target: visible (bool)
       │         - Vision: Objects, People, Motion, Faces
       ↓
┌──────────────┐
│ AGENT        │ Process:
└──────────────┘ 1. Hard safety check (people → stop, skip LLM)
       │         2. Build nav tools + skill tools
       │         3. Inject RELEVANT SKILLS hint into prompt
       │         4. Call LLM with bind_tools()
       │         5. Execute returned tool calls
       ↓
┌──────────────┐
│ ACTION /     │ Either a navigation primitive:
│ SKILL        │   move_forward(cm) | turn_left(°) | turn_right(°) | stop()
└──────────────┘ Or a skill sequence:
                   e.g. greet_cat → turn_left(20) + turn_right(40) + turn_left(20)
```

## Skill System

```
skills/
├── base.py       Skill ABC + SkillContext dataclass
├── registry.py   SkillRegistry — register, lookup, convert to LangChain tools
├── builtin.py    CatGreetingSkill, DogGreetingSkill, PersonSafetySkill
└── __init__.py   Public API
```

Adding a new skill requires only subclassing `Skill` and registering it in `main.py`:

```python
class WaveSkill(Skill):
    name = "wave"
    description = "Wave at a detected bottle"
    trigger_objects = ["bottle"]
    def execute(self, ctx): ...

skill_registry.register(WaveSkill())
```

## Vision Pipeline

```
Camera Frame
     ↓
┌─────────────────────────┐
│ Capture Frame           │ (PiCamera3 or MockCamera)
└─────────────────────────┘
     ↓
┌─────────────────────────┐
│ Vision Detector         │
├─────────────────────────┤
│ Option 1: Mock          │ (Laptop - instant, no dependencies)
│ ├─ Random objects       │
│ ├─ Random people        │
│ └─ Random motion        │
│                         │
│ Option 2: YOLO          │ (Pi - real detection)
│ ├─ Load YOLOv8 model    │
│ ├─ Run inference        │
│ ├─ Extract detections   │
│ └─ Calculate motion     │
└─────────────────────────┘
     ↓
┌─────────────────────────┐
│ VisionData Output       │
├─────────────────────────┤
│ objects: [              │
│   {name, confidence,    │
│    x, y, width, height} │
│ ]                       │
│ people_count: int       │
│ has_faces: bool         │
│ motion_detected: bool   │
│ frame_quality: float    │
└─────────────────────────┘
```

## Safety Protocol Flow

```
worldState received with vision data
         ↓
Check: people_count > 0?
         ↓
    ┌─YES──┴──NO──┐
    ↓             ↓
STOP      Continue to LLM
(Immediate)
    ↓
Return
(no further decision)
    ↓
    ├──────────────┐
    ↓              ↓
Execute     Consult LLM
STOP        for decision
```

## ESP32 Communication Protocol

The Raspberry Pi and ESP32 communicate via USB CDC serial using a JSON-based protocol:

### Commands (Pi → ESP32)

**Motor Control:**
```json
{"cmd": "motor", "action": "forward", "speed": 70, "duration": 1.5}
{"cmd": "motor", "action": "backward", "speed": 70, "duration": 1.5}
{"cmd": "motor", "action": "turn_left", "speed": 70, "duration": 0.5}
{"cmd": "motor", "action": "turn_right", "speed": 70, "duration": 0.5}
{"cmd": "motor", "action": "stop"}
```

**Sensor Reading:**
```json
{"cmd": "sensor", "type": "ultrasonic", "id": "front"}
{"cmd": "sensor", "type": "ultrasonic", "id": "left"}
{"cmd": "sensor", "type": "ultrasonic", "id": "right"}
{"cmd": "sensor", "type": "ultrasonic", "id": "rear"}
```

**Ping:**
```json
{"cmd": "ping"}
```

### Responses (ESP32 → Pi)

**Acknowledgment:**
```json
{"type": "ack", "status": "ok"}
{"type": "ack", "status": "error", "message": "Motor timeout"}
```

**Sensor Data:**
```json
{"type": "sensor", "id": "front", "distance": 45.2}
```

**Pong:**
```json
{"type": "pong"}
```

**Error:**
```json
{"type": "error", "message": "Invalid command"}
```

### Serial Connection Details

- **Port**: `/dev/ttyACM0` (Linux/Pi), `COM3` (Windows)
- **Baud Rate**: 115200
- **Protocol**: USB CDC (Virtual COM Port)
- **Format**: JSON strings terminated with `\n`
- **Timeout**: 1-2 seconds for responses

## Configuration Cascade

```
Environment Variables (highest priority)
         ↓
.env file (if present)
         ↓
config.py defaults (lowest priority)
         ↓
Final Configuration
├─ LLM_PROVIDER (ollama/openai)
├─ OLLAMA_MODEL (gemma3:270m)
├─ USE_REAL_CAMERA (false = mock)
├─ USE_REAL_VISION (false = mock)
└─ YOLO_MODEL (nano/small/medium/large)
```

## Deployment Architecture

```
Development (Laptop)
├─ Mock Camera
├─ Mock Vision Detector
├─ Mock ESP32 (serial not available)
├─ Local Ollama
└─ CLI output

         ↓ (same code!)

Production (Raspberry Pi + ESP32)
├─ Pi Camera 3
├─ YOLO Vision Detector
├─ ESP32 via USB Serial
│  ├─ L293D Motor Drivers
│  ├─ 4x DC Motors
│  └─ 4x HC-SR04 Ultrasonic Sensors
├─ Local Ollama (or cloud LLM)
└─ Motor control via ESP32

Hardware Stack:
┌─────────────────────┐
│  Raspberry Pi 5     │ (Brain, Vision, LLM)
│  - Python app       │
│  - Camera module    │
│  - Ollama           │
└─────────┬───────────┘
          │ USB Serial
┌─────────┴───────────┐
│  ESP32              │ (Hardware Controller)
│  - Arduino code     │
│  - GPIO control     │
└─────────┬───────────┘
          │ GPIO
┌─────────┴───────────┐
│  Motor Drivers      │ (L293D x2)
└─────────┬───────────┘
          │
┌─────────┴───────────┐
│  Motors + Sensors   │
│  - 4x DC Motors     │
│  - 4x Ultrasonic    │
└─────────────────────┘
```

## Module Dependencies

```
main.py
├─ config.py
├─ brain/
│  ├─ agent.py
│  │  ├─ brain/prompts.py
│  │  ├─ models/llm.py
│  │  └─ actions/cli_actions.py
│  └─ prompts.py
│
├─ world/
│  ├─ state.py (Pydantic models)
│  └─ simulator.py
│      └─ vision/vision.py
│
├─ vision/
│  ├─ camera.py
│  ├─ detector.py
│  ├─ vision.py
│  └─ __init__.py
│
└─ models/
   └─ llm.py
```

---

**Visual diagrams created for system understanding and documentation.**

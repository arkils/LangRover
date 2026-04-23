# LangRover System Architecture

## Hardware Architecture Overview

**NEW: ESP32-Based Architecture**

The system now uses a 3-tier architecture:

1. **Raspberry Pi 5** - High-level intelligence (LLM, vision processing, decision making)
2. **ESP32 Microcontroller** - Low-level hardware control (motors, sensors)
3. **Robotic Hardware** - Motors (TB6612FNG drivers) and Sensors (HC-SR04 ultrasonic)

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
│  │  - Consults: qwen2.5:0.5b / OpenAI via bind_tools()      │  │
│  │  - Navigation tools: move_forward | turn_left |         │  │
│  │    turn_right | stop                                     │  │
│  │  - Skill tools: greet_person | greet_cat | greet_dog |          │  │
│  │    <your custom skills>                                   │  │
│  │  - Safety Check: Obstacle distance → avoid               │  │
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
│  │  - People detected → greet_person skill                  │  │
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
     │   ├─ Include rear distance sensor
  │   ├─ [vision/vision.py] get_vision_detector().detect()
  │   │   ├─ If USE_REAL_VISION: YOLOVisionDetector (Pi Camera frame)
  │   │   └─ Else: MockVisionDetector
  │   └─ Return WorldState with vision data
  │
  ├─ [brain/agent.py] decide_and_act(world_state)
     │   ├─ Apply hard rules first (e.g. greet_person / greet_cat / greet_dog)
     │   ├─ Build nav tools   (move_forward, turn_left, turn_right, stop)
     │   ├─ Build skill tools (greet_cat, greet_dog, greet_person, ...)
     │   ├─ Read DECISION_MODE
     │   │   ├─ agent  → single LLM invoke, no retrieval
     │   │   ├─ rag    → retrieve KB rules first, inject them, then LLM invoke
     │   │   └─ hybrid → expose query_knowledge_base tool, LLM decides whether to retrieve
     │   ├─ Inject short-term memory in all modes
     │   ├─ Inject long-term memory in rag / hybrid when enabled
     │   ├─ Execute returned tool call(s)
     │   └─ If plain text fallback is returned → parse and execute action
  │
  └─ Display results
           [SENSORS]  Front: 360cm | Left: 97cm | Right: 372cm | Rear: 184cm
           [VISION]   cat(88%) | People: 0 | Motion: no
           [BRAIN]    Mode: HYBRID | STM: 3 cycles | LTM: off | RAG KB: ready
           [CONTEXT]  Source: STM (3 cycles) | LTM: off | RAG: not injected yet (LLM decides)
           [LLM]      Invoke 1/2 — tools incl. query_knowledge_base
           [RAG]      LLM called query_knowledge_base
           [LLM]      Invoke 2/2 — final action selection
           [ACTION]   >> greet_cat()
           [RESULT]   Action: greet_cat | Heading: 0°

END
```

## Data Flow Diagram

```
┌──────────────┐
│ WORLD STATE  │ Contains:
└──────────────┘ - Distance: front, left, right, rear (cm)
       │         - Target: visible (bool)
       │         - Vision: Objects, People, Motion, Faces
       ↓
┌──────────────┐
│ AGENT        │ Process:
└──────────────┘ 1. Apply hard-rule skills when required
                │         2. Build nav tools + skill tools
                │         3. Inject RELEVANT SKILLS hint into prompt
                │         4. Depending on DECISION_MODE:
                │            - agent  → LLM only
                │            - rag    → retrieve then LLM
                │            - hybrid → LLM may call query_knowledge_base
                │         5. Execute returned tool calls
       ↓
┌──────────────┐
│ ACTION /     │ Either a navigation primitive:
│ SKILL        │   move_forward(cm) | turn_left(°) | turn_right(°) | stop()
└──────────────┘ Or a skill sequence:
                   e.g. greet_cat → turn_left(20) + turn_right(40) + turn_left(20)
```

## Decision Modes

```
DECISION_MODE=agent
     Sensors + vision + STM
               ↓
     LLM chooses action/skill tool

DECISION_MODE=rag
     Sensors + vision
               ↓
     Retrieve relevant KB rules
               ↓
     LLM chooses action/skill tool with rules injected

DECISION_MODE=hybrid
     Sensors + vision + query_knowledge_base tool
               ↓
     LLM decides whether retrieval is necessary
               ↓
     Optional second invoke with retrieved rules injected
               ↓
     Final action/skill tool
```

## Skill System

```
skills/
├── base.py       Skill ABC + SkillContext dataclass
├── registry.py   SkillRegistry — register, lookup, convert to LangChain tools
├── builtin.py    CatGreetingSkill, DogGreetingSkill, PersonGreetingSkill
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
Check: front_distance_cm < 30?
         ↓
    ┌─YES──┬──NO──┐
    ↓             ↓
Block         Continue to LLM
move_forward
    ↓
    ├──────────────┐
    ↓              ↓
Turn/Stop    Consult LLM
             for decision
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
├─ OLLAMA_MODEL (qwen2.5:0.5b)
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
│  ├─ TB6612FNG Motor Drivers
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
│  Motor Drivers      │ (TB6612FNG x2)
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

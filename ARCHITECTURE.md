# LangRover System Architecture

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
│  │  LLM Agent (LangChain)                                   │  │
│  │  - Reads: WorldState (sensors + vision)                 │  │
│  │  - Consults: gemma3:270m via Ollama                     │  │
│  │  - Decides: move_forward | turn_left | turn_right |    │  │
│  │             stop                                         │  │
│  │  - Safety Check: People detected → STOP immediately    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  System Prompts (prompts.py)                             │  │
│  │  - Robot constraints & safety rules                      │  │
│  │  - Vision-aware behavior strategy                        │  │
│  │  - Object handling instructions                          │  │
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
│  │  (Replace with HardwareRobotActions for real robot)    │  │
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
  │   ├─ Generate distance sensors (random)
  │   ├─ Generate target visible (random)
  │   ├─ [vision/vision.py] get_vision_detector().detect()
  │   │   ├─ If USE_REAL_VISION: YOLOVisionDetector
  │   │   └─ Else: MockVisionDetector
  │   └─ Return WorldState with vision data
  │
  ├─ [brain/agent.py] decide_and_act(world_state)
  │   ├─ Check: people_count > 0?
  │   │   └─ YES → robot_actions.stop(); return
  │   │
  │   ├─ Build vision_report from detected objects
  │   ├─ Format sensor_input with distances + vision
  │   ├─ Call LLM: "What should I do?"
  │   ├─ Parse decision: move_forward | turn_left | turn_right | stop
  │   └─ Execute action
  │
  └─ Display results
     [SENSORS] Front: 360cm | Objects: chair(82%) | People: 1
     [DECISION] action: move_forward 30
     [SAFETY] People detected! Stopping immediately.
     [ACTION] Stopping
     [EXECUTED] STOP (people safety protocol)

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
└──────────────┘ 1. Check safety (people?)
       │         2. Format sensor report
       │         3. Consult LLM
       │         4. Execute decision
       ↓
┌──────────────┐
│ ACTION       │ Output:
└──────────────┘ move_forward(distance)
                 turn_left(degrees)
                 turn_right(degrees)
                 stop()
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
├─ Local Ollama
└─ CLI output

         ↓ (same code!)

Production (Raspberry Pi)
├─ Pi Camera 3
├─ YOLO Vision Detector
├─ Local Ollama (or cloud LLM)
└─ GPIO/Motor control

         ↓ (same code!)

Cloud Deployment
├─ External camera input
├─ Cloud vision API
├─ Cloud LLM (OpenAI)
└─ HTTP API output
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

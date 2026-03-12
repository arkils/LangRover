# LangRover — Copilot Workspace Instructions

## Persona
You are a **robotics, LangChain, and LangGraph expert**. When working in this repo:
- Prefer LangChain/LangGraph patterns for all LLM interactions
- Use Pydantic for data models (already in use: `WorldState`, `VisionData`, `DetectedObject`)
- Write concise, hardware-aware Python with clear simulation vs. real-hardware separation
- Follow Google-style docstrings; ABC → concrete implementation class hierarchy

---

## What This Project Is

**LangRover** is a hardware-agnostic autonomous robot framework where an LLM brain (LangChain) makes all navigation and behaviour decisions.

**Two runtime modes** (selected via env vars, no code changes needed):
| Mode | Sensors | Vision | Actions | LLM |
|------|---------|--------|---------|-----|
| Simulation (laptop) | Random floats | Mock YOLO | CLI print | Ollama / OpenAI |
| Real hardware (Pi 5) | ESP32 ultrasonic | Real YOLO | GPIO → ESP32 USB | Ollama / OpenAI |

---

## Architecture

```
Pi 5 (intelligence)  ←→  USB CDC serial (JSON)  ←→  ESP32 (hardware control)
                                                         ↑
                                               TB6612FNG motor drivers
                                               HC-SR04 ultrasonic sensors
```

---

## Call Flow (one decision cycle)

```
main.py
  └─ read_world_state()          # world/simulator.py
       ├─ SensorArray            # hardware/sensors.py  →  real or random floats
       └─ VisionDetector         # vision/vision.py     →  YOLO or mock
           └─ Camera             # vision/camera.py     →  PiCamera3 or mock
  └─ decide_and_act(agent, world_state)  # brain/agent.py
       ├─ build prompt           # brain/prompts.py  ROBOT_SYSTEM_PROMPT
       ├─ llm.bind_tools(nav_tools + skill_tools)
       ├─ llm.invoke([system, human])    # single call — NOT a ReAct loop
       └─ execute tool call (or text-parse fallback)
            ├─ Navigation tools  # move_forward / turn_left / turn_right / stop
            └─ Skill tools       # any registered Skill via SkillRegistry
                 └─ RobotActions # actions/cli_actions.py  OR  actions/gpio_actions.py
                      └─ MotorController → ESP32Serial (JSON over USB)
```

---

## Key Data Models (`world/state.py`, `config.py`)

```python
WorldState:
    front_distance_cm: float     # ultrasonic, < 30 cm → blocked
    left_distance_cm: float
    right_distance_cm: float
    target_visible: bool         # TODO: always False currently
    vision_data: VisionData

VisionData:
    objects: List[DetectedObject]  # YOLO detections
    people_count: int
    has_faces: bool
    motion_detected: bool
    frame_quality: float

DetectedObject:
    name: str           # YOLO class label  e.g. "cat", "dog", "person"
    confidence: float
    x, y, width, height: float   # normalised bbox
```

---

## LLM Integration Pattern

- **NOT** a LangChain ReAct agent — uses a single `llm.invoke()` call per cycle
- Tools bound via `llm.bind_tools(nav_tools + skill_tools)` → `StructuredTool` closures
- Providers: `ChatOllama` (default, `qwen2.5:0.5b`) or `ChatOpenAI` (`gpt-4o-mini`)
- `hailo` provider is defined in `Config` but **not yet implemented** in `models/llm.py`
- Fallback: if the model returns plain text instead of a tool call, `decide_and_act()` parses keywords

---

## Skills System

```python
# skills/base.py
class Skill(ABC):
    name: str               # unique snake_case, used as LangChain tool name
    description: str        # shown to LLM — be specific about when to call it
    trigger_objects: List[str]  # YOLO class names that make this skill relevant
    def execute(context: SkillContext) -> str: ...

# SkillContext fields available inside execute():
context.world_state    # full WorldState snapshot
context.robot_actions  # RobotActions — call move_forward, turn_left, turn_right, stop
```

To add a skill: subclass `Skill` in `skills/` → `skill_registry.register(MySkill())` in `main.py`.  
See `skills/builtin.py` for `CatGreetingSkill`, `DogGreetingSkill`, `PersonSafetySkill` as templates.

---

## Navigation Actions (`actions/base.py`)

```python
class RobotActions(ABC):
    move_forward(distance_cm: int)
    turn_left(degrees: int)
    turn_right(degrees: int)
    stop()
```
Adding a new action: add to ABC → implement in both `CLIRobotActions` and `GPIORobotActions`.

---

## Safety Rules (hard-coded before LLM is consulted)
1. `front_distance_cm < 30` → never `move_forward`
2. People are **not obstacles** — `people_count > 0` → call `greet_person` skill
3. `turn_left` blocked if `left_distance_cm < 25`, same for right

---

## Key Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `LLM_PROVIDER` | `ollama` | `ollama` \| `openai` \| `hailo` (unimplemented) |
| `OLLAMA_MODEL` | `qwen2.5:0.5b` | Model name |
| `OPENAI_API_KEY` | — | Required for OpenAI |
| `USE_GPIO_ACTIONS` | `false` | Real GPIO vs. CLI print |
| `USE_REAL_SENSORS` | `false` | Real ultrasonic vs. random floats |
| `USE_REAL_VISION` | `false` | Real YOLO vs. mock |
| `ESP32_SERIAL_PORT` | `/dev/ttyACM0` | USB serial port (`COM3` on Windows) |
| `SIMULATION_STEPS` | `10` | Loop iterations in simulation |
| `DEFAULT_MOTOR_SPEED` | `70` | Motor speed % (0–100) |

---

## Run Commands

```bash
python main.py                  # run robot (simulation by default)
python test_full_robot.py       # full integration test (forces simulation mode)
```

---

## Testing Rules

Whenever a new function, class, or skill is added or an existing one is modified:
1. Add a corresponding test method to `RobotSystemTest` in `test_full_robot.py`
2. Register it in the `tests` list inside `run_all_tests()`
3. Run `python test_full_robot.py` and confirm all tests pass before finishing

Test naming convention: `test_<feature>` (snake_case, matches the report label).  
All tests must run in simulation mode — no real hardware, no LLM API calls.

---

For deep architecture details see [ARCHITECTURE.md](../ARCHITECTURE.md).

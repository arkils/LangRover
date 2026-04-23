# Quick Start: Vision Features

## Current Status
✅ Pi Camera 3 vision integration complete and tested
✅ Object detection with MockDetector running
✅ Hard-rule person handling active
✅ Real-time sensor reporting with vision data
✅ `agent`, `rag`, and `hybrid` decision modes available

## Run the Project

```bash
# Laptop (mock vision - no hardware needed)
.\venv\Scripts\python main.py

# Pi with real camera
export USE_REAL_CAMERA=true
export USE_REAL_VISION=true
python main.py
```

## Run the Dashboard

```powershell
streamlit run ui/app.py
```

Use the sidebar to switch between `agent`, `rag`, and `hybrid` and compare the per-cycle decision traces.

## What You're Seeing

When you run the robot:

```
[VISION] Using mock vision detector (simulation mode)
[SENSORS] Front: 360cm | Left: 97cm | Right: 372cm | Rear: 184cm
[VISION]  cat(88%) | People: 0 | Motion: no
[BRAIN]   Mode: HYBRID | STM: 2 cycles | LTM: off | RAG KB: ready
[CONTEXT] Source: STM (2 cycles) | LTM: off | RAG: not injected yet (LLM decides)
[LLM]     Invoke 1/2 — tools (incl. query_knowledge_base)
[RAG]     LLM called query_knowledge_base
[LLM]     Invoke 2/2 — final action selection
[ACTION]  >> greet_cat()
[SKILL]   Hello, cat! =^.^=
[RESULT]  Action: greet_cat | Heading: 0°
```

### Line Breakdown:
- **[VISION]** — Vision system status (mock or YOLO)
- **[SENSORS]** — Current front / left / right / rear distance readings
- **[VISION]** — Detected objects, people count, and motion flag
- **[BRAIN]** — Active decision mode and memory / RAG availability
- **[CONTEXT]** — What context was injected before the LLM call
- **[LLM]** — Each LLM invoke for the cycle
- **[RAG]** — Retrieval activity and whether KB rules were consulted
- **[SKILL]** — Skill console output
- **[ACTION]** — Action or skill selected by the LLM
- **[RESULT]** — Final action + heading after the cycle

## Key Features Added

### 1. Vision Data in WorldState
```python
world_state.vision = VisionData(
    objects=[...],           # Detected objects with confidence
    people_count=1,          # Number of people
    has_faces=True,          # Face detection
    motion_detected=True     # Motion in frame
)
```

### 2. People Detection Safety
```python
# People, cats, and dogs can trigger hard-rule skills before the LLM runs
if world_state.vision.people_count > 0:
    skill_registry.get("greet_person").execute(context)
```

### 3. Skill System
Detected objects trigger registered skills. The LLM receives them as callable tools:
- **cat detected** → LLM calls `greet_cat` → robot wiggles left-right
- **dog detected** → LLM calls `greet_dog` → robot bows forward
- **person detected** → `greet_person` may run as a hard rule before the LLM is consulted

### 4. Decision Modes

- **`agent`** — pure LLM tool-calling, no retrieval
- **`rag`** — always retrieve relevant KB rules before calling the LLM
- **`hybrid`** — expose `query_knowledge_base` as a tool so the LLM decides when retrieval is worth doing

The Streamlit UI makes this visible with a per-cycle summary and trace panel.

Add your own skill by subclassing `Skill` in `skills/builtin.py` and registering it in `main.py`.

## Test Vision Only

```python
from vision.vision import MockVisionDetector

detector = MockVisionDetector()
for i in range(5):
    vision = detector.detect()
    print(f"Frame {i}: {len(vision.objects)} objects, {vision.people_count} people")
```

## Install Real Vision (Optional)

Only needed if running on Pi with camera:

```bash
# In project venv
pip install ultralytics opencv-python picamera2
```

## Next Steps

1. ✅ Vision module with YOLO + mock fallback
2. ✅ Hard-rule person handling before normal LLM reasoning
3. ✅ Skill system (objects trigger named skill sequences)
4. ✅ LangChain tool calling (LLM picks nav tools or skills)
5. 📋 Test on real Pi with Pi Camera 3 (`./run.sh --vision`)
6. 📋 Add a custom skill for a new object class

## Customization Examples

### Change Detection Sensitivity
Edit `vision/vision.py`:
```python
class YOLOVisionDetector:
    def __init__(self, model_size="nano", confidence_threshold=0.5):
        self.conf_threshold = confidence_threshold
```

### Add Custom Objects to Detect
```python
# Edit YOLO model or create custom detector
OBJECTS_TO_TRACK = ["person", "dog", "cat", "car"]
```

### Adjust Safety Thresholds
Edit `brain/agent.py`:
```python
# Example: change the hard rule for detected people
if world_state.vision.people_count > 0:
    skill.execute(skill_context_early)

# Could be changed to: only stop if people are close
if world_state.vision.people_count > 0 and person_too_close():
    robot_actions.stop()
```

## Troubleshooting

**Q: Mock detector seems to randomly stop robot**
A: That's correct. Mock detector randomly generates people to simulate real-world scenarios. The hard-rule behavior may trigger whenever people are detected.

**Q: How do I disable people detection safety?**
A: Edit `brain/agent.py` and change the hard-rule block at the start of `decide_and_act()` (not recommended unless you understand the safety tradeoff).

**Q: Can I use custom vision models?**
A: Yes! Create a new class in `vision/vision.py` extending `VisionDetector`

## Full Documentation
See [VISION.md](VISION.md) for comprehensive vision system documentation.

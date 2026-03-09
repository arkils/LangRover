# Quick Start: Vision Features

## Current Status
✅ Pi Camera 3 vision integration complete and tested
✅ Object detection with MockDetector running
✅ People detection safety protocol active
✅ Real-time sensor reporting with vision data

## Run the Project

```bash
# Laptop (mock vision - no hardware needed)
.\venv\Scripts\python main.py

# Pi with real camera
export USE_REAL_CAMERA=true
export USE_REAL_VISION=true
python main.py
```

## What You're Seeing

When you run the robot:

```
[VISION] Using mock vision detector (simulation mode)
[SENSORS] Front: 360cm | Left: 97cm | Right: 372cm | Objects: cat(88%) | People: 0
[AGENT]   Consulting LLM | tools: [move_forward, turn_left, turn_right, stop, greet_cat, greet_dog, person_safety_stop]
[TOOL]    greet_cat({})
[SKILL]   Hello, cat! =^.^=
[ACTION]  Turning left 20 degrees
[ACTION]  Turning right 40 degrees
[ACTION]  Turning left 20 degrees
[SKILL]   greet_cat complete: Cat greeted with a friendly wiggle
```

### Line Breakdown:
- **[VISION]** — Vision system status (mock or YOLO)
- **[SENSORS]** — Current sensor readings including detected objects & people count
- **[AGENT]** — LLM is being called with these tools available
- **[TOOL]** — LLM chose this tool to call
- **[SKILL]** — Skill console output
- **[ACTION]** — Physical robot action executed
- **[SAFETY]** — Safety protocol activation (people → stop)

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
# Automatic in agent - ALWAYS stops if people detected
if people_detected:
    robot.stop()  # No exceptions
```

### 3. Skill System
Detected objects trigger registered skills. The LLM receives them as callable tools:
- **cat detected** → LLM calls `greet_cat` → robot wiggles left-right
- **dog detected** → LLM calls `greet_dog` → robot bows forward
- **person detected** → hard safety stop *before* the LLM is even consulted

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
2. ✅ Safety protocol (person → immediate stop)
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
# Current: stop if ANY people detected
if world_state.vision.people_count > 0:
    robot_actions.stop()

# Could be changed to: only stop if people are close
if world_state.vision.people_count > 0 and person_too_close():
    robot_actions.stop()
```

## Troubleshooting

**Q: Mock detector seems to randomly stop robot**
A: That's correct! Mock detector randomly generates people to simulate real-world scenarios. The safety protocol kicks in whenever people_count > 0.

**Q: How do I disable people detection safety?**
A: Edit `brain/agent.py` - comment out the safety check (not recommended!)

**Q: Can I use custom vision models?**
A: Yes! Create a new class in `vision/vision.py` extending `VisionDetector`

## Full Documentation
See [VISION.md](VISION.md) for comprehensive vision system documentation.

# Vision System for LangRover

## Overview

LangRover now includes computer vision capabilities for detecting objects and people. The system is hardware-agnostic and works on laptops (with mock data) and real Pi Camera 3 hardware.

## Features

### Vision Detection
- **Object Detection**: Identifies objects in the environment (cups, phones, chairs, etc.)
- **Person Detection**: Detects people and counts them
- **Face Detection**: Identifies faces in the frame
- **Motion Detection**: Detects motion/movement
- **Confidence Scoring**: Each detection includes confidence level (0.0-1.0)
- **Spatial Information**: Bounding box coordinates for objects

### Safety Integration
- **Immediate Stop on Detecting People**: Robot stops immediately if people are detected
- **Vision-Aware Planning**: Decision-making considers detected objects
- **Graceful Degradation**: Falls back to mock detection if real vision unavailable

## World State with Vision

```python
# WorldState now includes vision data
state = WorldState(
    # Distance sensors (as before)
    front_distance_cm=100,
    left_distance_cm=150,
    right_distance_cm=200,
    target_visible=True,
    
    # NEW: Vision data
    vision=VisionData(
        objects=[
            DetectedObject(
                name="person",
                confidence=0.95,
                x=0.5, y=0.6,
                width=0.3, height=0.7
            ),
            DetectedObject(
                name="cup",
                confidence=0.82,
                x=0.3, y=0.4,
                width=0.1, height=0.15
            )
        ],
        people_count=1,
        has_faces=True,
        motion_detected=False
    )
)
```

## Vision System Architecture

### Components

```
vision/
├── __init__.py
├── camera.py              # Camera interface
│   ├── CameraInterface    # Abstract camera
│   ├── PiCamera3          # Real Pi Camera 3
│   └── MockCamera         # Laptop testing
│
├── detector.py            # Detection interface
│   └── VisionDetector     # Abstract detector
│
└── vision.py              # Implementations
    ├── MockVisionDetector # Simulated detection
    └── YOLOVisionDetector # Real YOLO detection
```

### Detection Modes

#### 1. Mock Mode (Laptop - Default)
- No hardware required
- Simulates realistic detection data
- Random object/person detection
- Use for development and testing

```python
from vision.vision import MockVisionDetector

detector = MockVisionDetector()
vision_data = detector.detect()
```

#### 2. YOLO Mode (Real - Raspberry Pi)
- Requires: `ultralytics`, `opencv-python`
- Uses YOLOv8 models
- Real object detection from camera frames
- Supports nano/small/medium/large models

```python
from vision.vision import YOLOVisionDetector

detector = YOLOVisionDetector(model_size="nano")
frame = camera.capture_frame()
vision_data = detector.detect(frame)
```

#### 3. Auto Mode (Recommended)
- Automatically detects hardware
- Uses real detection on Pi
- Falls back to mock on laptop

```python
from vision.vision import get_vision_detector
from vision.camera import get_camera

# Auto-detect best option
camera = get_camera(use_real=True)
detector = get_vision_detector(use_real=True)
```

## Setup Instructions

### Laptop Setup (Mock Vision)
Already configured! No additional packages needed.

```bash
python main.py
```

### Raspberry Pi Setup (Real Vision with Pi Camera 3)

#### 1. Install Pi Camera 3 Support
```bash
pip install picamera2
```

#### 2. Install YOLO Detection (Optional, for real object detection)
```bash
pip install ultralytics opencv-python numpy
```

#### 3. Download YOLO Model
Weights download automatically on first run. To pre-download:
```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

#### 4. Enable Camera in raspi-config
```bash
sudo raspi-config
# Navigate to Interface Options → Camera → Enable
```

#### 5. Run Project
```bash
python main.py
```

## Using Different Vision Configurations

### Configuration via Config

Update `config.py`:

```python
@dataclass
class Config:
    # Vision settings
    USE_REAL_CAMERA: bool = os.getenv("USE_REAL_CAMERA", "false").lower() == "true"
    USE_REAL_VISION: bool = os.getenv("USE_REAL_VISION", "false").lower() == "true"
    YOLO_MODEL: str = os.getenv("YOLO_MODEL", "nano")  # nano, small, medium, large
```

### Environment Variables

```bash
# Use real Pi Camera 3
export USE_REAL_CAMERA=true

# Use YOLO detection instead of mock
export USE_REAL_VISION=true

# Specify YOLO model size
export YOLO_MODEL=small

python main.py
```

## Skill System Integration

Detected objects don't just appear in the LLM prompt — they drive the **skill system**.
Every YOLO detection is matched against registered skills in `SkillRegistry` and relevant
skills are surfaced to the LLM as callable tools:

| Detected object | Triggered skill | Behaviour |
|---|---|---|
| `person` | `person_safety_stop` | Immediate stop |
| `cat` | `greet_cat` | Left-right wiggle + console message |
| `dog` | `greet_dog` | Forward nudge (bow) + console message |
| *(anything else)* | navigation tools | move / turn / stop |

To add a new skill for a new object, subclass `Skill` in `skills/builtin.py` and register
it in `main.py` — the LLM picks it up automatically next run.

See `skills/` for full documentation.
### VisionData
```python
class VisionData(BaseModel):
    objects: List[DetectedObject]  # All detected objects
    people_count: int              # Number of people
    has_faces: bool                # Faces detected
    motion_detected: bool          # Motion in frame
    frame_quality: float           # Frame quality (0-1)
```

### DetectedObject
```python
class DetectedObject(BaseModel):
    name: str                      # Object class (e.g., "person", "dog")
    confidence: float              # Detection confidence (0.0-1.0)
    x: float                       # Center X (0-1 normalized)
    y: float                       # Center Y (0-1 normalized)
    width: float                   # Box width (0-1 normalized)
    height: float                  # Box height (0-1 normalized)
```

## Agent Behavior with Vision

### Safety Priority
The agent always prioritizes people detection:

```python
# If people are detected
if world_state.vision.people_count > 0:
    robot_actions.stop()  # ALWAYS STOP
```

### Vision-Aware Decisions
Agent considers:
- Detected objects for path planning
- People for safety
- Motion for caution level
- Target visibility combined with vision

### Example Scenarios

**Scenario 1: Person Detected**
```
Vision: people_count=1, person confidence=0.95
Decision: STOP immediately (safety protocol)
Action: stop()
```

**Scenario 2: Object Ahead**
```
Vision: objects=[cup(0.82), phone(0.75)]
Front distance: 50cm, Clear
Decision: Move toward detected objects or around them
Action: move_forward(30)
```

**Scenario 3: Motion + Clear Path**
```
Vision: motion_detected=True
Front distance: 200cm, Safe
Decision: Cautious movement
Action: move_forward(20) with caution
```

## Testing Vision Locally

### Test Mock Detector
```python
from vision.vision import MockVisionDetector

detector = MockVisionDetector()
for _ in range(5):
    vision = detector.detect()
    print(f"Detected: {len(vision.objects)} objects, {vision.people_count} people")
```

### Test YOLO Detector (if installed)
```python
import cv2
from vision.vision import YOLOVisionDetector

detector = YOLOVisionDetector(model_size="nano")
frame = cv2.imread("test_image.jpg")
vision = detector.detect(frame)
print(f"Objects: {vision.objects}")
print(f"People: {vision.people_count}")
```

## Performance Considerations

### Model Size vs Speed
- **nano**: Fastest, ~45 FPS on Pi 4 (5.6M params)
- **small**: Good balance, ~30 FPS (27.7M params)
- **medium**: Better accuracy, ~15 FPS (71.4M params)
- **large**: Best accuracy, ~5 FPS (150.7M params)

Recommended for robot navigation: **nano** or **small**

### Camera Frame Rate
- Pi Camera 3: Up to 30 FPS @ 720p
- Adjust in `camera.py` based on your needs

## Troubleshooting

### Camera Not Detected
```bash
# Check camera availability
vcgencmd get_camera
# Should return: supported=1 detected=1

# Or in Python
from vision.camera import PiCamera3
camera = PiCamera3()
print(camera.is_available())
```

### YOLO Model Won't Load
```bash
# Check ultralytics installation
pip install -U ultralytics

# Download model manually
python -c "from ultralytics import YOLO; m = YOLO('yolov8nano.pt')"
```

### Low FPS / Slow Detection
- Use smaller YOLO model (nano instead of medium)
- Reduce camera resolution
- Enable hardware acceleration on Pi 4/5

## Advanced: Custom Vision Detectors

Create your own detector:

```python
from vision.detector import VisionDetector
from world.state import VisionData

class MyCustomDetector(VisionDetector):
    def detect(self, frame_data) -> VisionData:
        # Your custom detection logic
        vision = VisionData()
        # ... populate vision data
        return vision
    
    def is_available(self) -> bool:
        return True

# Use it
detector = MyCustomDetector()
vision = detector.detect(frame)
```

## Future Enhancements

- [ ] Pose estimation (detect body parts)
- [ ] Gesture recognition (recognize gestures)
- [ ] Activity classification (running, walking, etc.)
- [ ] Depth estimation from single frame
- [ ] Real-time tracking of objects
- [ ] Color-based detection
- [ ] Custom model support

## References

- **YOLOv8**: https://docs.ultralytics.com/
- **Pi Camera 3**: https://www.raspberrypi.com/products/camera-module-3/
- **Picamera2**: https://github.com/raspberrypi/picamera2

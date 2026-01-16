"""Mock and real vision detectors for object/person detection."""

import random
from typing import Optional, List
from world.state import VisionData, DetectedObject
from vision.detector import VisionDetector


class MockVisionDetector(VisionDetector):
    """Mock vision detector for laptop testing (no model required)."""

    def __init__(self):
        """Initialize mock detector."""
        self.available = True
        print("[VISION] Using mock vision detector (simulation mode)")

    def detect(self, frame_data=None) -> VisionData:
        """
        Return simulated vision data.

        Randomly detects objects and people for testing.
        """
        vision = VisionData()

        # 50% chance to detect people
        if random.random() < 0.5:
            vision.people_count = random.randint(1, 3)
            vision.has_faces = vision.people_count > 0

        # 40% chance to detect motion
        if random.random() < 0.4:
            vision.motion_detected = True

        # Randomly detect objects
        possible_objects = [
            ("person", 0.92),
            ("dog", 0.85),
            ("cat", 0.88),
            ("cup", 0.75),
            ("phone", 0.80),
            ("bottle", 0.82),
            ("chair", 0.78),
        ]

        if random.random() < 0.6:
            # Detect 1-2 random objects
            num_objects = random.randint(1, 2)
            for _ in range(num_objects):
                obj_name, base_conf = random.choice(possible_objects)
                confidence = base_conf + random.uniform(-0.1, 0.05)
                confidence = max(0.5, min(1.0, confidence))

                detected_obj = DetectedObject(
                    name=obj_name,
                    confidence=round(confidence, 2),
                    x=round(random.uniform(0.2, 0.8), 2),
                    y=round(random.uniform(0.2, 0.8), 2),
                    width=round(random.uniform(0.1, 0.4), 2),
                    height=round(random.uniform(0.1, 0.4), 2),
                )
                vision.objects.append(detected_obj)

        return vision

    def is_available(self) -> bool:
        """Mock detector is always available."""
        return self.available


class YOLOVisionDetector(VisionDetector):
    """YOLO-based vision detector for real object/person detection."""

    def __init__(self, model_size: str = "nano"):
        """
        Initialize YOLO detector.

        Args:
            model_size: YOLO model size ('nano', 'small', 'medium', 'large')
        """
        self.available = False
        self.model = None
        self.model_size = model_size
        self._initialize()

    def _initialize(self):
        """Initialize YOLO model."""
        try:
            from ultralytics import YOLO  # type: ignore

            model_name = f"yolov8{self.model_size}.pt"
            print(f"[VISION] Loading YOLO model: {model_name}")
            self.model = YOLO(model_name)
            self.available = True
            print("[VISION] YOLO model loaded successfully")
        except ImportError:
            print("[WARNING] ultralytics not installed. Install with: pip install ultralytics opencv-python")
            self.available = False
        except Exception as e:
            print(f"[ERROR] Failed to load YOLO model: {e}")
            self.available = False

    def detect(self, frame_data) -> VisionData:
        """
        Detect objects and people using YOLO.

        Args:
            frame_data: Numpy array (H, W, 3) in RGB format.

        Returns:
            VisionData with detected objects.
        """
        vision = VisionData()

        if not self.is_available() or frame_data is None:
            return vision

        try:
            # Run YOLO inference
            results = self.model(frame_data, verbose=False)
            result = results[0]

            # Frame dimensions for normalization
            h, w = frame_data.shape[:2]

            # Process detections
            people_count = 0
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = result.names[class_id]
                confidence = float(box.conf[0])

                # Extract bounding box coordinates
                x1, y1, x2, y2 = box.xyxy[0]

                # Normalize coordinates (0-1)
                x_norm = float((x1 + x2) / 2 / w)
                y_norm = float((y1 + y2) / 2 / h)
                width_norm = float((x2 - x1) / w)
                height_norm = float((y2 - y1) / h)

                detected_obj = DetectedObject(
                    name=class_name,
                    confidence=round(confidence, 2),
                    x=round(x_norm, 2),
                    y=round(y_norm, 2),
                    width=round(width_norm, 2),
                    height=round(height_norm, 2),
                )
                vision.objects.append(detected_obj)

                # Count people
                if class_name.lower() == "person":
                    people_count += 1

            vision.people_count = people_count
            vision.has_faces = people_count > 0

            # Detect motion by comparing frame brightness (simple heuristic)
            import numpy as np
            brightness = np.mean(frame_data)
            # Brightness between 50-200 indicates normal scene, extreme values suggest motion blur
            vision.motion_detected = brightness < 50 or brightness > 200

        except Exception as e:
            print(f"[ERROR] YOLO detection failed: {e}")

        return vision

    def is_available(self) -> bool:
        """Check if YOLO detector is available."""
        return self.available


def get_vision_detector(use_real: bool = True, yolo_model: str = "nano") -> VisionDetector:
    """
    Get vision detector instance.

    Args:
        use_real: If True, try YOLO. If False, use mock.
        yolo_model: YOLO model size if using real detection.

    Returns:
        VisionDetector instance.
    """
    if use_real:
        detector = YOLOVisionDetector(model_size=yolo_model)
        if detector.is_available():
            return detector
        else:
            print("[WARNING] YOLO not available, falling back to mock detector")

    return MockVisionDetector()

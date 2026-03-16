"""Simulator for robot environment and sensor data."""

import random
import os
from world.state import WorldState, VisionData, DetectedObject
from vision.vision import get_vision_detector


# Initialize sensors, camera, and vision detector once
_vision_detector = None
_camera = None
_sensor_array = None


def _use_real_camera() -> bool:
    return os.getenv("USE_REAL_CAMERA", "false").lower() == "true"


def _use_real_sensors() -> bool:
    return os.getenv("USE_REAL_SENSORS", "false").lower() == "true"


def _use_real_vision() -> bool:
    return os.getenv("USE_REAL_VISION", "false").lower() == "true"


def _yolo_model() -> str:
    return os.getenv("YOLO_MODEL", "nano")


def get_camera():
    """Get or initialize camera (real PiCamera3 or mock)."""
    global _camera
    if _camera is None:
        if _use_real_camera():
            try:
                from vision.camera import PiCamera3
                cam = PiCamera3()
                if cam.is_available():
                    _camera = cam
                else:
                    print("[CAMERA] PiCamera3 unavailable, falling back to mock camera")
            except Exception as e:
                print(f"[CAMERA] Failed to initialize PiCamera3: {e}, falling back to mock camera")
        if _camera is None:
            from vision.camera import MockCamera
            _camera = MockCamera()
    return _camera


def get_detector():
    """Get or initialize vision detector (real YOLO or mock)."""
    global _vision_detector
    if _vision_detector is None:
        from vision.vision import get_vision_detector
        _vision_detector = get_vision_detector(
            use_real=_use_real_vision(),
            yolo_model=_yolo_model(),
        )
    return _vision_detector


def get_sensors():
    """Get or initialize sensor array (real or simulated)."""
    global _sensor_array
    
    if _sensor_array is None and _use_real_sensors():
        try:
            from hardware.sensors import SensorArray
            _sensor_array = SensorArray()
            if _sensor_array.is_available():
                print("[SENSORS] Using real ultrasonic sensors")
            else:
                print("[SENSORS] Real sensors unavailable, using simulation")
                _sensor_array = None
        except Exception as e:
            print(f"[SENSORS] Failed to initialize real sensors: {e}")
            print("[SENSORS] Falling back to simulation")
            _sensor_array = None
    
    return _sensor_array


def read_world_state() -> WorldState:
    """
    Read the current world state from sensors and camera.

    On Raspberry Pi with real hardware (USE_REAL_SENSORS=true):
    - Reads actual ultrasonic sensor values
    - Uses real camera for vision
    
    On laptop (default):
    - Returns realistic randomized sensor values
    - Uses mock vision detector

    Returns:
        WorldState: Current sensory state of the robot.
    """
    sensors = get_sensors()
    
    if sensors and sensors.is_available():
        # Read real sensor data
        distances = sensors.read_all()
        front_distance = distances.get('front', 200.0) or 200.0
        left_distance = distances.get('left', 200.0) or 200.0
        right_distance = distances.get('right', 200.0) or 200.0
        # Rear sensor available but not used in current WorldState model
        
        # Target detection would need additional sensor/camera logic
        target_visible = False  # TODO: Implement target detection
    else:
        # Simulate realistic distance sensor readings (20-400 cm)
        front_distance = random.uniform(20, 400)
        left_distance = random.uniform(20, 400)
        right_distance = random.uniform(20, 400)
        
        # Randomly make target visible 30% of the time
        target_visible = random.random() < 0.3

    # Get vision data from detector
    camera = get_camera()
    frame = camera.capture_frame()
    detector = get_detector()
    vision_data = detector.detect(frame)

    return WorldState(
        front_distance_cm=round(front_distance, 2),
        left_distance_cm=round(left_distance, 2),
        right_distance_cm=round(right_distance, 2),
        target_visible=target_visible,
        vision=vision_data,
    )

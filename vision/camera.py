"""Pi Camera 3 interface for LangRover."""

import os
from abc import ABC, abstractmethod
from typing import Optional, Any
from world.state import VisionData


class CameraInterface(ABC):
    """Abstract interface for robot camera hardware."""

    @abstractmethod
    def capture_frame(self) -> Optional[Any]:
        """
        Capture a frame from the camera.

        Returns:
            Frame data (numpy array, PIL Image, etc.) or None if unavailable.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if camera is available."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Clean up camera resources."""
        pass


class PiCamera3(CameraInterface):
    """Pi Camera Module 3 implementation (Sony IMX708, autofocus, libcamera)."""

    # Capture resolution — 1280×720 is a good balance of speed and detail for YOLO
    CAPTURE_WIDTH = 1280
    CAPTURE_HEIGHT = 720

    def __init__(self):
        """Initialize Pi Camera Module 3."""
        self.camera = None
        self.available = False
        self._initialize()

    def _initialize(self):
        """Configure and start the camera with RGB888 format for YOLO compatibility."""
        try:
            from picamera2 import Picamera2  # type: ignore

            self.camera = Picamera2()

            # Configure for video capture: RGB888 gives a 3-channel (H, W, 3) numpy
            # array directly usable by YOLO / OpenCV without channel conversion.
            config = self.camera.create_video_configuration(
                main={"size": (self.CAPTURE_WIDTH, self.CAPTURE_HEIGHT), "format": "RGB888"},
            )
            self.camera.configure(config)

            # Enable continuous autofocus (Camera Module 3 supports it)
            try:
                self.camera.set_controls({"AfMode": 2})  # 2 = AfModeContinuous
            except Exception:
                pass  # Older libcamera versions may not expose AfMode

            self.camera.start()
            self.available = True
            print(
                f"[CAMERA] Pi Camera Module 3 initialized "
                f"({self.CAPTURE_WIDTH}×{self.CAPTURE_HEIGHT} RGB888, autofocus)"
            )
        except ImportError:
            print("[WARNING] picamera2 not installed. Install with: pip install picamera2")
            self.available = False
        except Exception as e:
            print(f"[WARNING] Could not initialize Pi Camera Module 3: {e}")
            self.available = False

    def capture_frame(self) -> Optional[Any]:
        """
        Capture a frame from the Pi Camera Module 3.

        Returns:
            Numpy array of shape (H, W, 3) in RGB order, or None if unavailable.
        """
        if not self.is_available():
            return None

        try:
            frame = self.camera.capture_array()
            return frame
        except Exception as e:
            print(f"[ERROR] Failed to capture frame: {e}")
            return None

    def is_available(self) -> bool:
        """Check if camera is available."""
        return self.available and self.camera is not None

    def close(self) -> None:
        """Close camera and release resources."""
        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
            except Exception:
                pass


class MockCamera(CameraInterface):
    """Mock camera for laptop testing (no hardware required)."""

    def __init__(self):
        """Initialize mock camera."""
        self.available = True
        print("[CAMERA] Using mock camera (laptop simulation)")

    def capture_frame(self) -> Optional[Any]:
        """
        Return a dummy frame.

        In real usage, this would contain actual image data.
        """
        # Return None for mock - vision detector will handle it
        return None

    def is_available(self) -> bool:
        """Mock camera is always available."""
        return True

    def close(self) -> None:
        """No-op for mock camera."""
        pass


def get_camera(use_real: bool = True) -> CameraInterface:
    """
    Get camera instance.

    Args:
        use_real: If True, try to use Pi Camera 3. If False, use mock.

    Returns:
        CameraInterface instance.
    """
    # Auto-detect if Pi Camera is available
    if use_real:
        try:
            import RPi.GPIO  # type: ignore
            # We're on a Pi
            return PiCamera3()
        except ImportError:
            # Not on a Pi, use mock
            return MockCamera()
    else:
        return MockCamera()

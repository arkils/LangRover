"""Abstract vision detection interface."""

from abc import ABC, abstractmethod
from typing import List
from world.state import VisionData, DetectedObject


class VisionDetector(ABC):
    """Abstract interface for vision-based object/person detection."""

    @abstractmethod
    def detect(self, frame_data=None) -> VisionData:
        """
        Detect objects and people in the frame.

        Args:
            frame_data: Raw frame data (image array, etc.)

        Returns:
            VisionData with detected objects, people, etc.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if detector is available (model loaded, etc.)."""
        pass

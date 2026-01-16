"""World state representation for LangRover."""

from typing import Optional, List
from pydantic import BaseModel, Field


class DetectedObject(BaseModel):
    """Represents a detected object with position and confidence."""

    name: str = Field(..., description="Object class name (e.g., 'person', 'dog', 'cup')")
    confidence: float = Field(..., description="Detection confidence (0.0-1.0)", ge=0.0, le=1.0)
    x: float = Field(..., description="Bounding box center X (0-1 normalized)", ge=0.0, le=1.0)
    y: float = Field(..., description="Bounding box center Y (0-1 normalized)", ge=0.0, le=1.0)
    width: float = Field(..., description="Bounding box width (0-1 normalized)", ge=0.0, le=1.0)
    height: float = Field(..., description="Bounding box height (0-1 normalized)", ge=0.0, le=1.0)


class VisionData(BaseModel):
    """Computer vision sensor data from camera."""

    objects: List[DetectedObject] = Field(
        default_factory=list,
        description="List of detected objects with positions"
    )
    people_count: int = Field(
        default=0,
        description="Number of people detected",
        ge=0
    )
    has_faces: bool = Field(
        default=False,
        description="Whether faces were detected"
    )
    motion_detected: bool = Field(
        default=False,
        description="Whether motion is detected in frame"
    )
    frame_quality: float = Field(
        default=1.0,
        description="Frame quality (0.0=bad, 1.0=perfect)",
        ge=0.0,
        le=1.0
    )


class WorldState(BaseModel):
    """Represents the sensory state of the robot's environment."""

    # Distance sensors
    front_distance_cm: float = Field(
        ..., description="Distance to obstacle in front (cm)", ge=0, le=500
    )
    left_distance_cm: float = Field(
        ..., description="Distance to obstacle on left (cm)", ge=0, le=500
    )
    right_distance_cm: float = Field(
        ..., description="Distance to obstacle on right (cm)", ge=0, le=500
    )
    
    # Legacy simple target detection
    target_visible: bool = Field(..., description="Whether target is visible to robot")
    
    # Vision data from camera
    vision: VisionData = Field(
        default_factory=VisionData,
        description="Computer vision sensor data"
    )

    def __str__(self) -> str:
        """Human-readable representation of the world state."""
        vision_info = ""
        if self.vision.objects:
            object_names = [f"{obj.name}({obj.confidence:.1%})" for obj in self.vision.objects]
            vision_info = f" | Objects: {', '.join(object_names)}"
        if self.vision.people_count > 0:
            vision_info += f" | People: {self.vision.people_count}"
        if self.vision.motion_detected:
            vision_info += " | Motion detected"
        
        return (
            f"Front: {self.front_distance_cm}cm | "
            f"Left: {self.left_distance_cm}cm | "
            f"Right: {self.right_distance_cm}cm | "
            f"Target: {self.target_visible}{vision_info}"
        )

"""Abstract base class for robot actions."""

from abc import ABC, abstractmethod


class RobotActions(ABC):
    """Abstract interface for robot hardware actions."""

    @abstractmethod
    def move_forward(self, distance_cm: int) -> None:
        """
        Move the robot forward.

        Args:
            distance_cm: Distance to move in centimeters.
        """
        pass

    @abstractmethod
    def turn_left(self, degrees: int) -> None:
        """
        Turn the robot left.

        Args:
            degrees: Degrees to turn (positive = counterclockwise).
        """
        pass

    @abstractmethod
    def turn_right(self, degrees: int) -> None:
        """
        Turn the robot right.

        Args:
            degrees: Degrees to turn (positive = clockwise).
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop all robot movement."""
        pass

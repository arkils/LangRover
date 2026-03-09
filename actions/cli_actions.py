"""CLI-based implementation of robot actions for simulation."""

from actions.base import RobotActions


class CLIRobotActions(RobotActions):
    """Robot actions that output to CLI instead of controlling real hardware."""

    def move_forward(self, distance_cm: int) -> None:
        """
        Simulate moving forward by printing to terminal.

        Args:
            distance_cm: Distance to move in centimeters.
        """
        print(f"[ACTION] Moving forward {distance_cm} cm")

    def turn_left(self, degrees: int) -> None:
        """
        Simulate turning left by printing to terminal.

        Args:
            degrees: Degrees to turn counterclockwise.
        """
        print(f"[ACTION] Turning left {degrees} degrees")

    def turn_right(self, degrees: int) -> None:
        """
        Simulate turning right by printing to terminal.

        Args:
            degrees: Degrees to turn clockwise.
        """
        print(f"[ACTION] Turning right {degrees} degrees")

    def stop(self) -> None:
        """Simulate stopping by printing to terminal."""
        print("[ACTION] Stopping")

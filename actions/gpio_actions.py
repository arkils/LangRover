"""
GPIO-based RobotActions implementation for real hardware.

This module implements the RobotActions interface using real GPIO-controlled
motors on Raspberry Pi 5, replacing CLI output with actual motor commands.
"""

from actions.base import RobotActions
from hardware.motors import MotorController


class GPIORobotActions(RobotActions):
    """
    Real hardware implementation of RobotActions using GPIO motors.
    
    Controls 4-wheel robot with 2 L293D motor controllers via GPIO pins.
    """
    
    def __init__(self, default_speed: int = 70):
        """
        Initialize GPIO robot actions.
        
        Args:
            default_speed: Default motor speed percentage (0-100)
        """
        self.motors = MotorController()
        self.default_speed = default_speed
        
        if not self.motors.is_available():
            print("[WARNING] Motors not available - hardware may not be connected")
        else:
            print(f"[ACTIONS] GPIO robot actions initialized (default speed: {default_speed}%)")
    
    def move_forward(self, distance_cm: int):
        """
        Move robot forward by specified distance.
        
        Args:
            distance_cm: Distance to move in centimeters
            
        Note:
            Duration is calculated based on distance and speed.
            Calibration may be needed for accurate distance control.
        """
        # Estimate duration: assuming ~10 cm/second at default speed
        # This will need calibration based on actual robot
        duration = distance_cm / 10.0
        duration = max(0.1, min(10.0, duration))  # Clamp to reasonable range
        
        print(f"[ACTION] Moving forward {distance_cm} cm (~{duration:.1f}s)")
        self.motors.move_forward(speed=self.default_speed, duration=duration)
    
    def turn_left(self, degrees: int):
        """
        Turn robot left by specified degrees.
        
        Args:
            degrees: Angle to turn in degrees (0-360)
            
        Note:
            Duration is calculated based on degrees.
            Calibration may be needed for accurate angle control.
        """
        # Estimate duration: assuming ~90 degrees per second
        # This will need calibration based on actual robot
        duration = degrees / 90.0
        duration = max(0.1, min(5.0, duration))  # Clamp to reasonable range
        
        print(f"[ACTION] Turning left {degrees} degrees (~{duration:.1f}s)")
        self.motors.turn_left(speed=self.default_speed, duration=duration)
    
    def turn_right(self, degrees: int):
        """
        Turn robot right by specified degrees.
        
        Args:
            degrees: Angle to turn in degrees (0-360)
            
        Note:
            Duration is calculated based on degrees.
            Calibration may be needed for accurate angle control.
        """
        # Estimate duration: assuming ~90 degrees per second
        # This will need calibration based on actual robot
        duration = degrees / 90.0
        duration = max(0.1, min(5.0, duration))  # Clamp to reasonable range
        
        print(f"[ACTION] Turning right {degrees} degrees (~{duration:.1f}s)")
        self.motors.turn_right(speed=self.default_speed, duration=duration)
    
    def stop(self):
        """Stop all robot motors immediately."""
        print("[ACTION] Stopping")
        self.motors.stop()
    
    def cleanup(self):
        """Cleanup GPIO resources when shutting down."""
        print("[ACTIONS] Cleaning up GPIO actions...")
        self.motors.cleanup()


def calibrate_movement():
    """
    Interactive calibration tool for movement timing.
    
    Helps determine accurate duration-to-distance and duration-to-angle mappings.
    """
    print("=" * 70)
    print("MOVEMENT CALIBRATION TOOL")
    print("=" * 70)
    print()
    print("This tool helps calibrate movement timing for accurate control.")
    print()
    
    actions = GPIORobotActions(default_speed=70)
    
    if not actions.motors.is_available():
        print("[ERROR] Motors not available. Check hardware connection.")
        return
    
    try:
        print("=== FORWARD MOVEMENT CALIBRATION ===")
        print("Place robot on the floor with measuring tape.")
        print()
        
        # Test different durations
        test_durations = [0.5, 1.0, 2.0, 3.0]
        
        for duration in test_durations:
            input(f"Press ENTER to move forward for {duration}s...")
            actions.motors.move_forward(speed=70, duration=duration)
            distance = input(f"How many cm did it move? ")
            
            try:
                cm = float(distance)
                speed_cm_per_sec = cm / duration
                print(f"  → Speed: {speed_cm_per_sec:.2f} cm/s")
                print()
            except ValueError:
                print("  → Invalid input, skipping calculation")
                print()
        
        print()
        print("=== ROTATION CALIBRATION ===")
        print("Mark robot's starting orientation.")
        print()
        
        # Test rotation
        test_durations = [0.5, 1.0, 1.5, 2.0]
        
        for duration in test_durations:
            input(f"Press ENTER to turn left for {duration}s...")
            actions.motors.turn_left(speed=70, duration=duration)
            degrees = input(f"How many degrees did it rotate? ")
            
            try:
                deg = float(degrees)
                rotation_deg_per_sec = deg / duration
                print(f"  → Rotation speed: {rotation_deg_per_sec:.2f} deg/s")
                print()
            except ValueError:
                print("  → Invalid input, skipping calculation")
                print()
        
        print()
        print("=== CALIBRATION COMPLETE ===")
        print()
        print("Use the calculated speeds to update GPIORobotActions:")
        print("  - Update move_forward() duration calculation")
        print("  - Update turn_left/right() duration calculation")
        print()
        
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Calibration stopped")
    finally:
        actions.cleanup()
        print("[DONE] Calibration complete")


if __name__ == "__main__":
    calibrate_movement()

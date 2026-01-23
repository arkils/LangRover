"""
Motor Controller for LangRover - ESP32 Communication Interface

The Raspberry Pi communicates with an ESP32 microcontroller via USB CDC serial.
The ESP32 controls the actual motor hardware (TB6612FNG drivers and DC motors).

Architecture:
    Raspberry Pi → USB Serial → ESP32 → TB6612FNG Motor Drivers → DC Motors
"""

import time
from hardware.esp32_serial import get_esp32


class MotorController:
    """
    4-wheel robot motor controller communicating via ESP32.
    
    Provides high-level movement commands: forward, backward, turn left, turn right, stop.
    Commands are sent to ESP32 via USB serial, which controls the actual motor hardware.
    """
    
    def __init__(self, serial_port: str = "/dev/ttyACM0", baudrate: int = 115200):
        """
        Initialize motor controller with ESP32 connection.
        
        Args:
            serial_port: USB serial port for ESP32 (e.g., /dev/ttyACM0, COM3)
            baudrate: Serial communication speed (default 115200)
        """
        self.esp32 = get_esp32(port=serial_port, baudrate=baudrate)
        
        if self.esp32.is_available():
            print("[MOTORS] Motor controller initialized via ESP32")
        else:
            print("[WARNING] ESP32 not available - motor commands will be ignored")
    
    def move_forward(self, speed: int = 70, duration: float = 0):
        """
        Move robot forward.
        
        Args:
            speed: Speed percentage (0-100)
            duration: Duration in seconds (0 = continuous)
        """
        print(f"[MOTORS] Moving forward at {speed}% speed")
        
        if duration > 0:
            self.esp32.motor_forward(speed=speed, duration=duration)
        else:
            self.esp32.motor_forward(speed=speed)
    
    def move_backward(self, speed: int = 70, duration: float = 0):
        """
        Move robot backward.
        
        Args:
            speed: Speed percentage (0-100)
            duration: Duration in seconds (0 = continuous)
        """
        print(f"[MOTORS] Moving backward at {speed}% speed")
        
        if duration > 0:
            self.esp32.motor_backward(speed=speed, duration=duration)
        else:
            self.esp32.motor_backward(speed=speed)
    
    def turn_left(self, speed: int = 70, duration: float = 0):
        """
        Turn robot left.
        
        Args:
            speed: Speed percentage (0-100)
            duration: Duration in seconds (0 = continuous)
        """
        print(f"[MOTORS] Turning left at {speed}% speed")
        
        if duration > 0:
            self.esp32.motor_turn_left(speed=speed, duration=duration)
        else:
            self.esp32.motor_turn_left(speed=speed)
    
    def turn_right(self, speed: int = 70, duration: float = 0):
        """
        Turn robot right.
        
        Args:
            speed: Speed percentage (0-100)
            duration: Duration in seconds (0 = continuous)
        """
        print(f"[MOTORS] Turning right at {speed}% speed")
        
        if duration > 0:
            self.esp32.motor_turn_right(speed=speed, duration=duration)
        else:
            self.esp32.motor_turn_right(speed=speed)
    
    def stop(self):
        """Stop all motors."""
        print("[MOTORS] Stopping all motors")
        self.esp32.motor_stop()
    
    def is_available(self) -> bool:
        """Check if ESP32 connection is available."""
        return self.esp32.is_available()
    
    def cleanup(self):
        """Cleanup ESP32 connection."""
        print("[MOTORS] Cleaning up motor controller...")
        self.stop()
        self.esp32.cleanup()


def test_motors():
    """Test function to verify motor operation."""
    print("=" * 70)
    print("MOTOR CONTROLLER TEST")
    print("=" * 70)
    print()
    print("WARNING: Make sure robot is on blocks or wheels are off the ground!")
    print("Press Ctrl+C to stop at any time")
    print()
    input("Press ENTER to continue...")
    print()
    
    motors = MotorController()
    
    if not motors.is_available():
        print("[ERROR] No motors available. Check GPIO initialization.")
        return
    
    try:
        # Test sequence
        print("Test 1: Forward for 2 seconds at 50% speed")
        motors.move_forward(speed=50, duration=2)
        time.sleep(1)
        
        print("Test 2: Backward for 2 seconds at 50% speed")
        motors.move_backward(speed=50, duration=2)
        time.sleep(1)
        
        print("Test 3: Turn left for 1 second at 60% speed")
        motors.turn_left(speed=60, duration=1)
        time.sleep(1)
        
        print("Test 4: Turn right for 1 second at 60% speed")
        motors.turn_right(speed=60, duration=1)
        time.sleep(1)
        
        print("Test 5: Speed ramp (30% to 100%)")
        for speed in range(30, 101, 10):
            print(f"  Speed: {speed}%")
            motors.move_forward(speed=speed, duration=0.5)
        motors.stop()
        
        print()
        print("[SUCCESS] All motor tests completed!")
        
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Test stopped by user")
    finally:
        motors.cleanup()
        print("[DONE] Motor test complete")


if __name__ == "__main__":
    test_motors()

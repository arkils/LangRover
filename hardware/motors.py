"""
L293D Motor Controller Driver for 4-wheel robot on Raspberry Pi 5

Controls 4 DC motors using 2 L293D motor driver chips:
- Motor Controller 1: Front left and front right motors
- Motor Controller 2: Rear left and rear right motors
"""

import time
from typing import Literal

try:
    import RPi.GPIO as GPIO  # type: ignore
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("[WARNING] RPi.GPIO not available. Using simulated motors.")

from hardware.pins import PINS, MotorPins


class Motor:
    """
    Single DC motor controlled by L293D motor driver.
    
    Controls direction (forward/backward) and speed (PWM).
    """
    
    def __init__(self, in1: int, in2: int, enable: int, name: str = "Motor"):
        """
        Initialize motor.
        
        Args:
            in1: GPIO pin for IN1 (direction control)
            in2: GPIO pin for IN2 (direction control)
            enable: GPIO pin for EN (PWM speed control)
            name: Human-readable name for the motor
        """
        self.in1 = in1
        self.in2 = in2
        self.enable = enable
        self.name = name
        self.pwm = None
        self.available = False
        
        if GPIO_AVAILABLE:
            self._initialize_gpio()
    
    def _initialize_gpio(self):
        """Initialize GPIO pins for motor control."""
        try:
            # Set direction pins as outputs
            GPIO.setup(self.in1, GPIO.OUT)
            GPIO.setup(self.in2, GPIO.OUT)
            GPIO.setup(self.enable, GPIO.OUT)
            
            # Initialize PWM on enable pin (1000 Hz frequency)
            self.pwm = GPIO.PWM(self.enable, 1000)
            self.pwm.start(0)  # Start with 0% duty cycle (stopped)
            
            self.available = True
            print(f"[MOTOR] {self.name} initialized (IN1: GPIO{self.in1}, IN2: GPIO{self.in2}, EN: GPIO{self.enable})")
        except Exception as e:
            print(f"[ERROR] Failed to initialize {self.name}: {e}")
            self.available = False
    
    def forward(self, speed: int = 100):
        """
        Rotate motor forward.
        
        Args:
            speed: Speed percentage (0-100)
        """
        if not self.available:
            return
        
        speed = max(0, min(100, speed))  # Clamp to 0-100
        
        try:
            GPIO.output(self.in1, GPIO.HIGH)
            GPIO.output(self.in2, GPIO.LOW)
            self.pwm.ChangeDutyCycle(speed)
        except Exception as e:
            print(f"[ERROR] {self.name} forward failed: {e}")
    
    def backward(self, speed: int = 100):
        """
        Rotate motor backward.
        
        Args:
            speed: Speed percentage (0-100)
        """
        if not self.available:
            return
        
        speed = max(0, min(100, speed))  # Clamp to 0-100
        
        try:
            GPIO.output(self.in1, GPIO.LOW)
            GPIO.output(self.in2, GPIO.HIGH)
            self.pwm.ChangeDutyCycle(speed)
        except Exception as e:
            print(f"[ERROR] {self.name} backward failed: {e}")
    
    def stop(self):
        """Stop the motor."""
        if not self.available:
            return
        
        try:
            GPIO.output(self.in1, GPIO.LOW)
            GPIO.output(self.in2, GPIO.LOW)
            self.pwm.ChangeDutyCycle(0)
        except Exception as e:
            print(f"[ERROR] {self.name} stop failed: {e}")
    
    def cleanup(self):
        """Cleanup GPIO resources."""
        if self.available and GPIO_AVAILABLE:
            self.stop()
            if self.pwm:
                self.pwm.stop()
            GPIO.cleanup([self.in1, self.in2, self.enable])


class MotorController:
    """
    4-wheel robot motor controller using 2 L293D chips.
    
    Provides high-level movement commands: forward, backward, turn left, turn right, stop.
    """
    
    def __init__(self):
        """Initialize all 4 motors."""
        if GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
        
        # Initialize motors with configured pins
        self.front_left = Motor(
            PINS.motor_front_left.in1,
            PINS.motor_front_left.in2,
            PINS.motor_front_left.enable,
            "Front Left Motor"
        )
        
        self.front_right = Motor(
            PINS.motor_front_right.in1,
            PINS.motor_front_right.in2,
            PINS.motor_front_right.enable,
            "Front Right Motor"
        )
        
        self.rear_left = Motor(
            PINS.motor_rear_left.in1,
            PINS.motor_rear_left.in2,
            PINS.motor_rear_left.enable,
            "Rear Left Motor"
        )
        
        self.rear_right = Motor(
            PINS.motor_rear_right.in1,
            PINS.motor_rear_right.in2,
            PINS.motor_rear_right.enable,
            "Rear Right Motor"
        )
        
        print("[MOTORS] Motor controller initialized")
    
    def move_forward(self, speed: int = 70, duration: float = 0):
        """
        Move robot forward.
        
        Args:
            speed: Speed percentage (0-100)
            duration: Duration in seconds (0 = continuous)
        """
        print(f"[MOTORS] Moving forward at {speed}% speed")
        self.front_left.forward(speed)
        self.front_right.forward(speed)
        self.rear_left.forward(speed)
        self.rear_right.forward(speed)
        
        if duration > 0:
            time.sleep(duration)
            self.stop()
    
    def move_backward(self, speed: int = 70, duration: float = 0):
        """
        Move robot backward.
        
        Args:
            speed: Speed percentage (0-100)
            duration: Duration in seconds (0 = continuous)
        """
        print(f"[MOTORS] Moving backward at {speed}% speed")
        self.front_left.backward(speed)
        self.front_right.backward(speed)
        self.rear_left.backward(speed)
        self.rear_right.backward(speed)
        
        if duration > 0:
            time.sleep(duration)
            self.stop()
    
    def turn_left(self, speed: int = 70, duration: float = 0):
        """
        Turn robot left (left motors backward, right motors forward).
        
        Args:
            speed: Speed percentage (0-100)
            duration: Duration in seconds (0 = continuous)
        """
        print(f"[MOTORS] Turning left at {speed}% speed")
        self.front_left.backward(speed)
        self.front_right.forward(speed)
        self.rear_left.backward(speed)
        self.rear_right.forward(speed)
        
        if duration > 0:
            time.sleep(duration)
            self.stop()
    
    def turn_right(self, speed: int = 70, duration: float = 0):
        """
        Turn robot right (right motors backward, left motors forward).
        
        Args:
            speed: Speed percentage (0-100)
            duration: Duration in seconds (0 = continuous)
        """
        print(f"[MOTORS] Turning right at {speed}% speed")
        self.front_left.forward(speed)
        self.front_right.backward(speed)
        self.rear_left.forward(speed)
        self.rear_right.backward(speed)
        
        if duration > 0:
            time.sleep(duration)
            self.stop()
    
    def stop(self):
        """Stop all motors."""
        print("[MOTORS] Stopping all motors")
        self.front_left.stop()
        self.front_right.stop()
        self.rear_left.stop()
        self.rear_right.stop()
    
    def is_available(self) -> bool:
        """Check if motors are available."""
        return (self.front_left.available or self.front_right.available or
                self.rear_left.available or self.rear_right.available)
    
    def cleanup(self):
        """Cleanup all motor GPIO resources."""
        print("[MOTORS] Cleaning up motor controller...")
        self.stop()
        self.front_left.cleanup()
        self.front_right.cleanup()
        self.rear_left.cleanup()
        self.rear_right.cleanup()
        
        if GPIO_AVAILABLE:
            GPIO.cleanup()


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

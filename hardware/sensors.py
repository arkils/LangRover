"""
Ultrasonic Sensor Driver for HC-SR04 sensors on Raspberry Pi 5

Supports 4 ultrasonic sensors for distance measurement:
- Front sensor
- Left sensor
- Right sensor
- Rear sensor
"""

import time
from typing import Optional

try:
    import RPi.GPIO as GPIO  # type: ignore
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("[WARNING] RPi.GPIO not available. Using simulated sensors.")

from hardware.pins import PINS, UltrasonicPins


class UltrasonicSensor:
    """
    HC-SR04 Ultrasonic Distance Sensor driver.
    
    Measures distance by sending ultrasonic pulse and measuring echo time.
    """
    
    def __init__(self, trigger_pin: int, echo_pin: int, name: str = "Sensor"):
        """
        Initialize ultrasonic sensor.
        
        Args:
            trigger_pin: GPIO pin for trigger signal
            echo_pin: GPIO pin for echo signal
            name: Human-readable name for the sensor
        """
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.name = name
        self.available = False
        
        if GPIO_AVAILABLE:
            self._initialize_gpio()
    
    def _initialize_gpio(self):
        """Initialize GPIO pins for sensor."""
        try:
            # Set trigger as output, echo as input
            GPIO.setup(self.trigger_pin, GPIO.OUT)
            GPIO.setup(self.echo_pin, GPIO.IN)
            
            # Ensure trigger is low initially
            GPIO.output(self.trigger_pin, GPIO.LOW)
            time.sleep(0.1)
            
            self.available = True
            print(f"[SENSOR] {self.name} initialized (TRIG: GPIO{self.trigger_pin}, ECHO: GPIO{self.echo_pin})")
        except Exception as e:
            print(f"[ERROR] Failed to initialize {self.name}: {e}")
            self.available = False
    
    def measure_distance(self, timeout: float = 0.5) -> Optional[float]:
        """
        Measure distance in centimeters.
        
        Args:
            timeout: Maximum time to wait for echo (seconds)
            
        Returns:
            Distance in centimeters, or None if measurement failed
        """
        if not self.available:
            return None
        
        try:
            # Send 10us pulse on trigger
            GPIO.output(self.trigger_pin, GPIO.HIGH)
            time.sleep(0.00001)  # 10 microseconds
            GPIO.output(self.trigger_pin, GPIO.LOW)
            
            # Wait for echo to start
            pulse_start = time.time()
            timeout_start = pulse_start
            while GPIO.input(self.echo_pin) == GPIO.LOW:
                pulse_start = time.time()
                if pulse_start - timeout_start > timeout:
                    return None  # Timeout
            
            # Wait for echo to end
            pulse_end = time.time()
            timeout_start = pulse_end
            while GPIO.input(self.echo_pin) == GPIO.HIGH:
                pulse_end = time.time()
                if pulse_end - timeout_start > timeout:
                    return None  # Timeout
            
            # Calculate distance
            # Speed of sound: 343 m/s = 34300 cm/s
            # Distance = (Time × Speed) / 2 (round trip)
            pulse_duration = pulse_end - pulse_start
            distance = (pulse_duration * 34300) / 2
            
            # Filter unrealistic values (0-400cm for HC-SR04)
            if 2 <= distance <= 400:
                return round(distance, 2)
            else:
                return None
                
        except Exception as e:
            print(f"[ERROR] {self.name} measurement failed: {e}")
            return None
    
    def cleanup(self):
        """Cleanup GPIO resources."""
        if self.available and GPIO_AVAILABLE:
            GPIO.cleanup([self.trigger_pin, self.echo_pin])


class SensorArray:
    """
    Manages all 4 ultrasonic sensors for the robot.
    
    Provides easy access to front, left, right, and rear distance measurements.
    """
    
    def __init__(self):
        """Initialize all 4 ultrasonic sensors."""
        if GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
        
        # Initialize sensors with configured pins
        self.front = UltrasonicSensor(
            PINS.ultrasonic_front.trigger,
            PINS.ultrasonic_front.echo,
            "Front Sensor"
        )
        
        self.left = UltrasonicSensor(
            PINS.ultrasonic_left.trigger,
            PINS.ultrasonic_left.echo,
            "Left Sensor"
        )
        
        self.right = UltrasonicSensor(
            PINS.ultrasonic_right.trigger,
            PINS.ultrasonic_right.echo,
            "Right Sensor"
        )
        
        self.rear = UltrasonicSensor(
            PINS.ultrasonic_rear.trigger,
            PINS.ultrasonic_rear.echo,
            "Rear Sensor"
        )
        
        print("[SENSORS] Sensor array initialized")
    
    def read_all(self) -> dict:
        """
        Read all sensors and return distances.
        
        Returns:
            Dictionary with keys: front, left, right, rear
            Values are distances in cm, or None if unavailable
        """
        return {
            "front": self.front.measure_distance(),
            "left": self.left.measure_distance(),
            "right": self.right.measure_distance(),
            "rear": self.rear.measure_distance(),
        }
    
    def is_available(self) -> bool:
        """Check if any sensors are available."""
        return (self.front.available or self.left.available or 
                self.right.available or self.rear.available)
    
    def cleanup(self):
        """Cleanup all sensor GPIO resources."""
        print("[SENSORS] Cleaning up sensor array...")
        self.front.cleanup()
        self.left.cleanup()
        self.right.cleanup()
        self.rear.cleanup()
        
        if GPIO_AVAILABLE:
            GPIO.cleanup()


def test_sensors():
    """Test function to verify sensor operation."""
    print("=" * 70)
    print("ULTRASONIC SENSOR TEST")
    print("=" * 70)
    print()
    
    sensors = SensorArray()
    
    if not sensors.is_available():
        print("[ERROR] No sensors available. Check GPIO initialization.")
        return
    
    try:
        print("Reading sensors for 10 cycles...")
        print()
        
        for i in range(10):
            distances = sensors.read_all()
            print(f"Cycle {i+1}:")
            print(f"  Front: {distances['front']} cm" if distances['front'] else "  Front: N/A")
            print(f"  Left:  {distances['left']} cm" if distances['left'] else "  Left:  N/A")
            print(f"  Right: {distances['right']} cm" if distances['right'] else "  Right: N/A")
            print(f"  Rear:  {distances['rear']} cm" if distances['rear'] else "  Rear:  N/A")
            print()
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Test stopped by user")
    finally:
        sensors.cleanup()
        print("[DONE] Sensor test complete")


if __name__ == "__main__":
    test_sensors()

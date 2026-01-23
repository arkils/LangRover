"""
Ultrasonic Sensor Interface for LangRover - ESP32 Communication

The Raspberry Pi requests sensor readings from an ESP32 microcontroller via USB CDC serial.
The ESP32 reads the actual ultrasonic sensors (HC-SR04) and returns distance values.

Architecture:
    Raspberry Pi → USB Serial → ESP32 → HC-SR04 Ultrasonic Sensors
"""

import time
from typing import Optional, Dict
from hardware.esp32_serial import get_esp32


class SensorArray:
    """
    Manages all 4 ultrasonic sensors via ESP32 communication.
    
    Provides easy access to front, left, right, and rear distance measurements.
    Sensors are physically connected to ESP32, which handles the low-level reading.
    """
    
    def __init__(self, serial_port: str = "/dev/ttyACM0", baudrate: int = 115200):
        """
        Initialize sensor array with ESP32 connection.
        
        Args:
            serial_port: USB serial port for ESP32 (e.g., /dev/ttyACM0, COM3)
            baudrate: Serial communication speed (default 115200)
        """
        self.esp32 = get_esp32(port=serial_port, baudrate=baudrate)
        
        if self.esp32.is_available():
            print("[SENSORS] Sensor array initialized via ESP32")
        else:
            print("[WARNING] ESP32 not available - sensor readings will return None")
    
    def read_front(self) -> Optional[float]:
        """
        Read front ultrasonic sensor.
        
        Returns:
            Distance in centimeters, or None if unavailable
        """
        return self.esp32.read_ultrasonic("front")
    
    def read_left(self) -> Optional[float]:
        """
        Read left ultrasonic sensor.
        
        Returns:
            Distance in centimeters, or None if unavailable
        """
        return self.esp32.read_ultrasonic("left")
    
    def read_right(self) -> Optional[float]:
        """
        Read right ultrasonic sensor.
        
        Returns:
            Distance in centimeters, or None if unavailable
        """
        return self.esp32.read_ultrasonic("right")
    
    def read_rear(self) -> Optional[float]:
        """
        Read rear ultrasonic sensor.
        
        Returns:
            Distance in centimeters, or None if unavailable
        """
        return self.esp32.read_ultrasonic("rear")
    
    def read_all(self) -> Dict[str, Optional[float]]:
        """
        Read all sensors and return distances.
        
        Returns:
            Dictionary with keys: front, left, right, rear
            Values are distances in cm, or None if unavailable
        """
        return {
            "front": self.read_front(),
            "left": self.read_left(),
            "right": self.read_right(),
            "rear": self.read_rear(),
        }
    
    def is_available(self) -> bool:
        """Check if ESP32 connection is available."""
        return self.esp32.is_available()
    
    def cleanup(self):
        """Cleanup ESP32 connection."""
        print("[SENSORS] Cleaning up sensor array...")
        self.esp32.cleanup()


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

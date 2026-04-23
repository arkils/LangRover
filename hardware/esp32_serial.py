"""
ESP32 Serial Communication Module for LangRover

This module handles USB CDC serial communication between Raspberry Pi and ESP32.
The ESP32 acts as an intermediary, controlling motors and reading sensors.

Communication Protocol (JSON-based):
    Pi → ESP32: {"cmd": "motor", "action": "forward", "speed": 70, "duration": 1.5}
    Pi → ESP32: {"cmd": "motor", "action": "stop"}
    Pi → ESP32: {"cmd": "sensor", "type": "ultrasonic", "id": "front"}
    ESP32 → Pi: {"type": "sensor", "id": "front", "distance": 45.2}
    ESP32 → Pi: {"type": "ack", "status": "ok"}
    ESP32 → Pi: {"type": "error", "message": "Invalid command"}
"""

import json
import time
from typing import Optional, Dict, Any
import threading
import queue

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("[WARNING] pyserial not available. Install with: pip install pyserial")


class ESP32Serial:
    """
    Serial communication handler for ESP32 microcontroller.
    
    Manages USB CDC serial connection and provides high-level commands
    for motor control and sensor reading.
    """
    
    def __init__(self, port: str = "/dev/ttyACM0", baudrate: int = 115200, timeout: float = 1.0):
        """
        Initialize ESP32 serial connection.
        
        Args:
            port: Serial port path (e.g., /dev/ttyACM0 on Linux, COM3 on Windows)
            baudrate: Communication speed (115200 recommended for ESP32)
            timeout: Read timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.available = False
        self.response_queue = queue.Queue()
        self.read_thread = None
        self.running = False
        
        if SERIAL_AVAILABLE:
            self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize serial connection to ESP32."""
        try:
            # Open port WITHOUT asserting DTR/RTS — asserting DTR resets the ESP32
            # via its auto-reset circuit (DTR→EN pin), so we connect without touching it.
            self.serial_conn = serial.Serial()
            self.serial_conn.port = self.port
            self.serial_conn.baudrate = self.baudrate
            self.serial_conn.timeout = self.timeout
            self.serial_conn.write_timeout = self.timeout
            self.serial_conn.dtr = False
            self.serial_conn.rts = False
            self.serial_conn.open()
            
            # Brief pause then clear any accumulated messages
            time.sleep(0.3)
            self.serial_conn.reset_input_buffer()
            self.serial_conn.reset_output_buffer()
            
            # Start read thread
            self.running = True
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
            time.sleep(0.1)  # Give read thread time to start before ping
            if self._ping():
                self.available = True
                print(f"[ESP32] Connected on {self.port} at {self.baudrate} baud")
            else:
                print(f"[WARNING] ESP32 connected but not responding to ping")
                self.available = False
                
        except serial.SerialException as e:
            print(f"[ERROR] Failed to connect to ESP32 on {self.port}: {e}")
            self.available = False
        except Exception as e:
            print(f"[ERROR] Unexpected error connecting to ESP32: {e}")
            self.available = False
    
    def _read_loop(self):
        """Background thread for reading serial responses."""
        while self.running and self.serial_conn and self.serial_conn.is_open:
            try:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('utf-8').strip()
                    if line:
                        try:
                            response = json.loads(line)
                            self.response_queue.put(response)
                        except json.JSONDecodeError:
                            print(f"[ESP32] Invalid JSON received: {line}")
                else:
                    time.sleep(0.01)  # Small delay to prevent busy waiting
            except Exception as e:
                if self.running:  # Only log if not shutting down
                    print(f"[ESP32] Read error: {e}")
                    time.sleep(0.1)
    
    def _send_command(self, command: Dict[str, Any]) -> bool:
        """
        Send JSON command to ESP32.
        
        Args:
            command: Dictionary representing the command
            
        Returns:
            True if command was sent successfully
        """
        if not self.serial_conn:
            print(f"[ESP32] Cannot send command - not connected")
            return False
        
        try:
            json_str = json.dumps(command) + '\n'
            self.serial_conn.write(json_str.encode('utf-8'))
            return True
        except Exception as e:
            print(f"[ESP32] Error sending command: {e}")
            return False
    
    def _wait_for_response(self, timeout: float = 2.0, response_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Wait for response from ESP32.
        
        Args:
            timeout: Maximum time to wait for response
            response_type: Optional filter for specific response type
            
        Returns:
            Response dictionary or None if timeout
        """
        start_time = time.time()
        discarded = []
        result = None
        try:
            while time.time() - start_time < timeout:
                try:
                    response = self.response_queue.get(timeout=0.1)
                    if response_type is None or response.get("type") == response_type:
                        result = response
                        break
                    else:
                        discarded.append(response)
                except queue.Empty:
                    continue
        finally:
            # Restore non-matching messages so other callers can see them
            for item in discarded:
                self.response_queue.put(item)
        return result
    
    def _ping(self) -> bool:
        """
        Send ping to ESP32 to verify connection.
        
        Returns:
            True if ESP32 responds
        """
        cmd = {"cmd": "ping"}
        if self._send_command(cmd):
            response = self._wait_for_response(timeout=2.0, response_type="pong")
            return response is not None
        return False
    
    # ==================== Motor Commands ====================
    
    def motor_forward(self, speed: int = 100, duration: Optional[float] = None) -> bool:
        """
        Command ESP32 to move motors forward.
        
        Args:
            speed: Motor speed percentage (0-100)
            duration: Optional duration in seconds (None = continuous)
            
        Returns:
            True if command acknowledged
        """
        cmd = {
            "cmd": "motor",
            "action": "forward",
            "speed": speed
        }
        if duration is not None:
            cmd["duration"] = duration
        
        if self._send_command(cmd):
            # Ack arrives after the motor finishes running, so timeout = duration + margin
            ack_timeout = (duration if duration is not None else 0) + 2.0
            response = self._wait_for_response(timeout=ack_timeout, response_type="ack")
            return response is not None and response.get("status") == "ok"
        return False
    
    def motor_backward(self, speed: int = 100, duration: Optional[float] = None) -> bool:
        """
        Command ESP32 to move motors backward.
        
        Args:
            speed: Motor speed percentage (0-100)
            duration: Optional duration in seconds (None = continuous)
            
        Returns:
            True if command acknowledged
        """
        cmd = {
            "cmd": "motor",
            "action": "backward",
            "speed": speed
        }
        if duration is not None:
            cmd["duration"] = duration
        
        if self._send_command(cmd):
            ack_timeout = (duration if duration is not None else 0) + 2.0
            response = self._wait_for_response(timeout=ack_timeout, response_type="ack")
            return response is not None and response.get("status") == "ok"
        return False
    
    def motor_turn_left(self, speed: int = 100, duration: Optional[float] = None) -> bool:
        """
        Command ESP32 to turn left.
        
        Args:
            speed: Motor speed percentage (0-100)
            duration: Optional duration in seconds (None = continuous)
            
        Returns:
            True if command acknowledged
        """
        cmd = {
            "cmd": "motor",
            "action": "turn_left",
            "speed": speed
        }
        if duration is not None:
            cmd["duration"] = duration
        
        if self._send_command(cmd):
            ack_timeout = (duration if duration is not None else 0) + 2.0
            response = self._wait_for_response(timeout=ack_timeout, response_type="ack")
            return response is not None and response.get("status") == "ok"
        return False
    
    def motor_turn_right(self, speed: int = 100, duration: Optional[float] = None) -> bool:
        """
        Command ESP32 to turn right.
        
        Args:
            speed: Motor speed percentage (0-100)
            duration: Optional duration in seconds (None = continuous)
            
        Returns:
            True if command acknowledged
        """
        cmd = {
            "cmd": "motor",
            "action": "turn_right",
            "speed": speed
        }
        if duration is not None:
            cmd["duration"] = duration
        
        if self._send_command(cmd):
            ack_timeout = (duration if duration is not None else 0) + 2.0
            response = self._wait_for_response(timeout=ack_timeout, response_type="ack")
            return response is not None and response.get("status") == "ok"
        return False
    
    def motor_stop(self) -> bool:
        """
        Command ESP32 to stop all motors.
        
        Returns:
            True if command acknowledged
        """
        cmd = {
            "cmd": "motor",
            "action": "stop"
        }
        
        if self._send_command(cmd):
            response = self._wait_for_response(timeout=0.5, response_type="ack")
            return response is not None and response.get("status") == "ok"
        return False
    
    # ==================== Sensor Commands ====================
    
    def read_ultrasonic(self, sensor_id: str) -> Optional[float]:
        """
        Read ultrasonic sensor distance.
        
        Args:
            sensor_id: Sensor identifier ("front", "left", "right", "rear")
            
        Returns:
            Distance in centimeters or None if failed
        """
        cmd = {
            "cmd": "sensor",
            "type": "ultrasonic",
            "id": sensor_id
        }
        
        if self._send_command(cmd):
            response = self._wait_for_response(timeout=1.0, response_type="sensor")
            if response and response.get("id") == sensor_id:
                return response.get("distance")
        return None
    
    # ==================== Lifecycle ====================
    
    def is_available(self) -> bool:
        """Check if ESP32 connection is available."""
        return self.available and self.serial_conn is not None and self.serial_conn.is_open
    
    def cleanup(self):
        """Close serial connection and cleanup resources."""
        print("[ESP32] Cleaning up serial connection...")
        self.running = False
        
        # Wait for read thread to finish
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=1.0)
        
        # Close serial connection
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
            except Exception as e:
                print(f"[ESP32] Error closing serial: {e}")
        
        print("[ESP32] Cleanup complete")


# Global ESP32 instance (singleton pattern)
_esp32_instance: Optional[ESP32Serial] = None


def get_esp32(port: str = None, baudrate: int = None) -> ESP32Serial:
    """
    Get or create global ESP32 serial instance.
    
    Args:
        port: Serial port path (defaults to ESP32_SERIAL_PORT env var or /dev/ttyACM0)
        baudrate: Communication speed (defaults to ESP32_BAUDRATE env var or 115200)
        
    Returns:
        ESP32Serial instance
    """
    import os
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    global _esp32_instance
    if _esp32_instance is None:
        resolved_port = port or os.getenv("ESP32_SERIAL_PORT", "/dev/ttyUSB0")
        resolved_baudrate = baudrate or int(os.getenv("ESP32_BAUDRATE", "115200"))
        _esp32_instance = ESP32Serial(port=resolved_port, baudrate=resolved_baudrate)
    return _esp32_instance

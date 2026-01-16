"""
GPIO Pin Configuration for Raspberry Pi 5

This module defines all GPIO pin assignments for the LangRover robot hardware.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class UltrasonicPins:
    """Pin configuration for an ultrasonic sensor."""
    trigger: int  # GPIO pin for trigger
    echo: int     # GPIO pin for echo


@dataclass
class MotorPins:
    """Pin configuration for a motor controlled by L293D."""
    in1: int      # GPIO pin for IN1 (direction control)
    in2: int      # GPIO pin for IN2 (direction control)
    enable: int   # GPIO pin for EN (PWM speed control)


@dataclass
class PinConfiguration:
    """Complete GPIO pin configuration for LangRover on Raspberry Pi 5."""
    
    # Ultrasonic Sensors (4 sensors: front, left, right, rear)
    ultrasonic_front: UltrasonicPins = field(default_factory=lambda: UltrasonicPins(trigger=23, echo=24))
    ultrasonic_left: UltrasonicPins = field(default_factory=lambda: UltrasonicPins(trigger=17, echo=27))
    ultrasonic_right: UltrasonicPins = field(default_factory=lambda: UltrasonicPins(trigger=22, echo=10))
    ultrasonic_rear: UltrasonicPins = field(default_factory=lambda: UltrasonicPins(trigger=9, echo=11))
    
    # Motor Controller 1 (Front Motors) - L293D #1
    motor_front_left: MotorPins = field(default_factory=lambda: MotorPins(in1=5, in2=6, enable=12))
    motor_front_right: MotorPins = field(default_factory=lambda: MotorPins(in1=13, in2=19, enable=12))  # Shares EN with FL
    
    # Motor Controller 2 (Rear Motors) - L293D #2
    motor_rear_left: MotorPins = field(default_factory=lambda: MotorPins(in1=16, in2=20, enable=18))
    motor_rear_right: MotorPins = field(default_factory=lambda: MotorPins(in1=21, in2=26, enable=18))  # Shares EN with RL


# Global pin configuration instance
PINS = PinConfiguration()


def get_pin_summary() -> Dict[str, Dict[str, int]]:
    """
    Get a summary of all pin assignments.
    
    Returns:
        Dictionary with component names and their pin assignments
    """
    return {
        "Ultrasonic Sensors": {
            "Front (TRIG)": PINS.ultrasonic_front.trigger,
            "Front (ECHO)": PINS.ultrasonic_front.echo,
            "Left (TRIG)": PINS.ultrasonic_left.trigger,
            "Left (ECHO)": PINS.ultrasonic_left.echo,
            "Right (TRIG)": PINS.ultrasonic_right.trigger,
            "Right (ECHO)": PINS.ultrasonic_right.echo,
            "Rear (TRIG)": PINS.ultrasonic_rear.trigger,
            "Rear (ECHO)": PINS.ultrasonic_rear.echo,
        },
        "Motor Controller 1 (Front)": {
            "Front Left IN1": PINS.motor_front_left.in1,
            "Front Left IN2": PINS.motor_front_left.in2,
            "Front Right IN1": PINS.motor_front_right.in1,
            "Front Right IN2": PINS.motor_front_right.in2,
            "Enable (PWM)": PINS.motor_front_left.enable,
        },
        "Motor Controller 2 (Rear)": {
            "Rear Left IN1": PINS.motor_rear_left.in1,
            "Rear Left IN2": PINS.motor_rear_left.in2,
            "Rear Right IN1": PINS.motor_rear_right.in1,
            "Rear Right IN2": PINS.motor_rear_right.in2,
            "Enable (PWM)": PINS.motor_rear_left.enable,
        },
    }


def print_pin_configuration():
    """Print the complete pin configuration in a readable format."""
    print("=" * 70)
    print("LANGROVER GPIO PIN CONFIGURATION - RASPBERRY PI 5")
    print("=" * 70)
    print()
    
    summary = get_pin_summary()
    for component, pins in summary.items():
        print(f"{component}:")
        for name, pin in pins.items():
            print(f"  {name:25} GPIO {pin:2d}")
        print()
    
    print("=" * 70)
    print("IMPORTANT NOTES:")
    print("  - Use BCM pin numbering (GPIO numbers, not physical pin numbers)")
    print("  - Each motor controller enables (EN) are shared between two motors")
    print("  - PWM pins (12, 18) control motor speed via pulse width modulation")
    print("  - All ultrasonic sensors need 5V power and GND connections")
    print("  - L293D controllers need external power supply for motors (6-12V)")
    print("=" * 70)


if __name__ == "__main__":
    # Test/display the configuration
    print_pin_configuration()

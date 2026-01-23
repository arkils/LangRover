"""
ESP32 Pin Configuration for LangRover

This module defines GPIO pin assignments on the ESP32 microcontroller.
The ESP32 handles direct hardware control (motors and sensors).

Architecture:
    Raspberry Pi → USB Serial → ESP32 → Motors/Sensors

Note: These pin numbers are for the ESP32, NOT Raspberry Pi.
The Raspberry Pi communicates via USB CDC serial only.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class UltrasonicPins:
    """Pin configuration for an ultrasonic sensor on ESP32."""
    trigger: int  # ESP32 GPIO pin for trigger
    echo: int     # ESP32 GPIO pin for echo


@dataclass
class MotorPins:
    """Pin configuration for a motor controlled by TB6612FNG on ESP32."""
    in1: int      # ESP32 GPIO pin for IN1 (direction control)
    in2: int      # ESP32 GPIO pin for IN2 (direction control)
    pwm: int      # ESP32 GPIO pin for PWM (speed control)


@dataclass
class ESP32PinConfiguration:
    """Complete GPIO pin configuration for ESP32 controlling LangRover hardware."""
    
    # Ultrasonic Sensors (4 sensors: front, left, right, rear)
    # ESP32 GPIO pins
    ultrasonic_front: UltrasonicPins = field(default_factory=lambda: UltrasonicPins(trigger=23, echo=22))
    ultrasonic_left: UltrasonicPins = field(default_factory=lambda: UltrasonicPins(trigger=19, echo=18))
    ultrasonic_right: UltrasonicPins = field(default_factory=lambda: UltrasonicPins(trigger=17, echo=16))
    ultrasonic_rear: UltrasonicPins = field(default_factory=lambda: UltrasonicPins(trigger=4, echo=2))
    
    # TB6612FNG Motor Driver Channels (2 drivers, each controls 2 motors)
    # ESP32 GPIO pins
    motor_front_left: MotorPins = field(default_factory=lambda: MotorPins(in1=25, in2=26, pwm=27))
    motor_front_right: MotorPins = field(default_factory=lambda: MotorPins(in1=14, in2=12, pwm=13))
    motor_rear_left: MotorPins = field(default_factory=lambda: MotorPins(in1=33, in2=32, pwm=15))
    motor_rear_right: MotorPins = field(default_factory=lambda: MotorPins(in1=5, in2=4, pwm=2))
    
    # TB6612FNG Standby Pins (one per driver board)
    motor_driver_1_stby: int = 21  # Controls front left + front right motors
    motor_driver_2_stby: int = 19  # Controls rear left + rear right motors


# Global ESP32 pin configuration instance
ESP32_PINS = ESP32PinConfiguration()


def get_esp32_pin_summary() -> Dict[str, Dict[str, int]]:
    """
    Get a summary of all ESP32 pin assignments.
    
    Returns:
        Dictionary with component names and their pin assignments
    """
    return {
        "Ultrasonic Sensors (ESP32)": {
            "Front (TRIG)": ESP32_PINS.ultrasonic_front.trigger,
            "Front (ECHO)": ESP32_PINS.ultrasonic_front.echo,
            "Left (TRIG)": ESP32_PINS.ultrasonic_left.trigger,
            "Left (ECHO)": ESP32_PINS.ultrasonic_left.echo,
            "Right (TRIG)": ESP32_PINS.ultrasonic_right.trigger,
            "Right (ECHO)": ESP32_PINS.ultrasonic_right.echo,
            "Rear (TRIG)": ESP32_PINS.ultrasonic_rear.trigger,
            "Rear (ECHO)": ESP32_PINS.ultrasonic_rear.echo,
        },
        "TB6612FNG Driver 1 (Front Motors) - ESP32": {
            "Front Left IN1": ESP32_PINS.motor_front_left.in1,
            "Front Left IN2": ESP32_PINS.motor_front_left.in2,
            "Front Left PWM": ESP32_PINS.motor_front_left.pwm,
            "Front Right IN1": ESP32_PINS.motor_front_right.in1,
            "Front Right IN2": ESP32_PINS.motor_front_right.in2,
            "Front Right PWM": ESP32_PINS.motor_front_right.pwm,
            "Standby (STBY)": ESP32_PINS.motor_driver_1_stby,
        },
        "TB6612FNG Driver 2 (Rear Motors) - ESP32": {
            "Rear Left IN1": ESP32_PINS.motor_rear_left.in1,
            "Rear Left IN2": ESP32_PINS.motor_rear_left.in2,
            "Rear Left PWM": ESP32_PINS.motor_rear_left.pwm,
            "Rear Right IN1": ESP32_PINS.motor_rear_right.in1,
            "Rear Right IN2": ESP32_PINS.motor_rear_right.in2,
            "Rear Right PWM": ESP32_PINS.motor_rear_right.pwm,
            "Standby (STBY)": ESP32_PINS.motor_driver_2_stby,
        },
    }


def print_esp32_pin_configuration():
    """Print the complete ESP32 pin configuration in a readable format."""
    print("=" * 70)
    print("LANGROVER ESP32 PIN CONFIGURATION")
    print("=" * 70)
    print()
    print("NOTE: These are ESP32 GPIO pins, NOT Raspberry Pi pins!")
    print("The Raspberry Pi communicates with ESP32 via USB serial.")
    print()
    
    summary = get_esp32_pin_summary()
    for component, pins in summary.items():
        print(f"{component}:")
        for name, pin in pins.items():
            print(f"  {name:25} ESP32 GPIO {pin:2d}")
        print()
    
    print("=" * 70)
    print("IMPORTANT NOTES:")
    print("  - These pin numbers are for ESP32 microcontroller")
    print("  - Using TB6612FNG motor drivers (NOT L293D)")
    print("  - Each TB6612FNG controls 2 motors (A and B channels)")
    print("  - STBY pin must be HIGH to enable motors")
    print("  - Each motor has its own PWM pin for independent speed control")
    print("  - TB6612FNG provides higher current (1.2A) and better efficiency")
    print("=" * 70)


if __name__ == "__main__":
    # Test/display the configuration
    print_esp32_pin_configuration()

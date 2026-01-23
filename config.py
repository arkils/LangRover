"""Configuration settings for LangRover."""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Robot configuration parameters."""

    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")  # ollama, openai, or hailo
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Ollama Settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma3:270m")  # Default model
    
    # Hailo AI HAT+ / AI HAT+ 2 Settings (for Raspberry Pi 5)
    # Supported HAILO_DEVICE: "hailo8l" (13 TOPS), "hailo8" (26 TOPS), "hailo10h" (40 TOPS, AI HAT+ 2)
    HAILO_DEVICE: str = os.getenv("HAILO_DEVICE", "hailo10h")  # AI HAT+ 2 recommended
    HAILO_MODEL_PATH: str = os.getenv("HAILO_MODEL_PATH", "/home/pi/models/tinyllama-1.1b.Q4_K_M.gguf")
    HAILO_CONTEXT_LENGTH: int = int(os.getenv("HAILO_CONTEXT_LENGTH", "1024"))
    HAILO_MAX_TOKENS: int = int(os.getenv("HAILO_MAX_TOKENS", "100"))
    HAILO_TEMPERATURE: float = float(os.getenv("HAILO_TEMPERATURE", "0.7"))

    # Hardware Settings (Raspberry Pi 5 + ESP32)
    USE_GPIO_ACTIONS: bool = os.getenv("USE_GPIO_ACTIONS", "false").lower() == "true"
    USE_REAL_SENSORS: bool = os.getenv("USE_REAL_SENSORS", "false").lower() == "true"
    USE_REAL_CAMERA: bool = os.getenv("USE_REAL_CAMERA", "false").lower() == "true"
    USE_REAL_VISION: bool = os.getenv("USE_REAL_VISION", "false").lower() == "true"
    YOLO_MODEL: str = os.getenv("YOLO_MODEL", "nano")  # nano, small, medium, large
    
    # ESP32 Serial Communication Settings
    ESP32_SERIAL_PORT: str = os.getenv("ESP32_SERIAL_PORT", "/dev/ttyACM0")  # COM3 on Windows
    ESP32_BAUDRATE: int = int(os.getenv("ESP32_BAUDRATE", "115200"))
    
    # Motor Settings
    DEFAULT_MOTOR_SPEED: int = int(os.getenv("DEFAULT_MOTOR_SPEED", "70"))  # 0-100%

    # Agent Settings
    VERBOSE: bool = os.getenv("VERBOSE", "true").lower() == "true"
    DECISION_CYCLE_DELAY_SECONDS: int = int(os.getenv("DECISION_CYCLE_DELAY", "1"))

    # Safety Settings
    MIN_SAFE_DISTANCE_CM: int = 30
    CRITICAL_DISTANCE_CM: int = 25
    MAX_FORWARD_DISTANCE_CM: int = 100
    MAX_TURN_DEGREES: int = 90

    # Simulation Settings
    SIMULATION_STEPS: int = int(os.getenv("SIMULATION_STEPS", "10"))

    def validate(self) -> None:
        """Validate configuration."""
        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI provider")

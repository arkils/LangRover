/**
 * LangRover ESP32 Firmware
 * 
 * This firmware enables the ESP32 to act as a hardware controller for the LangRover robot.
 * It receives JSON commands via USB Serial from a Raspberry Pi and controls motors and sensors.
 * 
 * Hardware:
 * - ESP32 Development Board
 * - 2x TB6612FNG Motor Driver Boards (4 DC motors total)
 * - 4x HC-SR04 Ultrasonic Sensors
 * 
 * Communication: USB CDC Serial at 115200 baud
 * Protocol: JSON commands/responses
 * 
 * Author: LangRover Project
 * License: MIT
 */

#include <Arduino.h>
#include <ArduinoJson.h>

// ==================== PIN DEFINITIONS ====================

// TB6612FNG Driver 1 (Front Motors)
#define MOTOR_FL_IN1  25
#define MOTOR_FL_IN2  26
#define MOTOR_FL_PWM  27

#define MOTOR_FR_IN1  14
#define MOTOR_FR_IN2  12
#define MOTOR_FR_PWM  13

#define MOTOR_DRIVER_1_STBY  21  // Standby for Driver 1 (Front motors)

// TB6612FNG Driver 2 (Rear Motors)
#define MOTOR_RL_IN1  33
#define MOTOR_RL_IN2  32
#define MOTOR_RL_PWM  15

#define MOTOR_RR_IN1  5
#define MOTOR_RR_IN2  4
#define MOTOR_RR_PWM  2

#define MOTOR_DRIVER_2_STBY  19  // Standby for Driver 2 (Rear motors)

// Ultrasonic Sensors
#define ULTRASONIC_FRONT_TRIG  23
#define ULTRASONIC_FRONT_ECHO  22

#define ULTRASONIC_LEFT_TRIG   19
#define ULTRASONIC_LEFT_ECHO   18

#define ULTRASONIC_RIGHT_TRIG  17
#define ULTRASONIC_RIGHT_ECHO  16

#define ULTRASONIC_REAR_TRIG   4
#define ULTRASONIC_REAR_ECHO   2

// PWM Configuration
#define PWM_FREQ      20000   // 20kHz PWM frequency (recommended for TB6612FNG)
#define PWM_RESOLUTION 8      // 8-bit resolution (0-255)
#define PWM_CHANNEL_FL 0      // PWM channel for front left motor
#define PWM_CHANNEL_FR 1      // PWM channel for front right motor
#define PWM_CHANNEL_RL 2      // PWM channel for rear left motor
#define PWM_CHANNEL_RR 3      // PWM channel for rear right motor

// ==================== FUNCTION PROTOTYPES ====================

void setupMotors();
void setupSensors();
void processCommand(JsonDocument& doc);
void sendAck(bool success, const char* message = "");
void sendSensorData(const char* id, float distance);
void sendError(const char* message);

void motorForward(int speed, float duration = 0);
void motorBackward(int speed, float duration = 0);
void motorTurnLeft(int speed, float duration = 0);
void motorTurnRight(int speed, float duration = 0);
void motorStop();

float readUltrasonicDistance(int trigPin, int echoPin);

// ==================== SETUP ====================

void setup() {
  // Initialize Serial communication
  Serial.begin(115200);
  
  // Wait for serial connection
  delay(1000);
  
  // Setup hardware
  setupMotors();
  setupSensors();
  
  // Send startup message
  Serial.println("{\"type\":\"ready\",\"message\":\"ESP32 initialized\"}");
}

// ==================== MAIN LOOP ====================

void loop() {
  // Check for incoming serial data
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    if (input.length() > 0) {
      // Parse JSON command
      JsonDocument doc;
      DeserializationError error = deserializeJson(doc, input);
      
      if (error) {
        sendError("JSON parse error");
        return;
      }
      
      // Process the command
      processCommand(doc);
    }
  }
  
  delay(10);  // Small delay to prevent busy waiting
}

// ==================== MOTOR SETUP ====================

void setupMotors() {
  // Configure motor control pins as outputs
  pinMode(MOTOR_FL_IN1, OUTPUT);
  pinMode(MOTOR_FL_IN2, OUTPUT);
  pinMode(MOTOR_FR_IN1, OUTPUT);
  pinMode(MOTOR_FR_IN2, OUTPUT);
  pinMode(MOTOR_RL_IN1, OUTPUT);
  pinMode(MOTOR_RL_IN2, OUTPUT);
  pinMode(MOTOR_RR_IN1, OUTPUT);
  pinMode(MOTOR_RR_IN2, OUTPUT);
  
  // Configure standby pins as outputs
  pinMode(MOTOR_DRIVER_1_STBY, OUTPUT);
  pinMode(MOTOR_DRIVER_2_STBY, OUTPUT);
  
  // Configure PWM for each motor independently
  ledcSetup(PWM_CHANNEL_FL, PWM_FREQ, PWM_RESOLUTION);
  ledcSetup(PWM_CHANNEL_FR, PWM_FREQ, PWM_RESOLUTION);
  ledcSetup(PWM_CHANNEL_RL, PWM_FREQ, PWM_RESOLUTION);
  ledcSetup(PWM_CHANNEL_RR, PWM_FREQ, PWM_RESOLUTION);
  
  ledcAttachPin(MOTOR_FL_PWM, PWM_CHANNEL_FL);
  ledcAttachPin(MOTOR_FR_PWM, PWM_CHANNEL_FR);
  ledcAttachPin(MOTOR_RL_PWM, PWM_CHANNEL_RL);
  ledcAttachPin(MOTOR_RR_PWM, PWM_CHANNEL_RR);
  
  // Enable both drivers (STBY HIGH)
  digitalWrite(MOTOR_DRIVER_1_STBY, HIGH);
  digitalWrite(MOTOR_DRIVER_2_STBY, HIGH);
  
  // Initialize motors in stopped state
  motorStop();
}

// ==================== SENSOR SETUP ====================

void setupSensors() {
  // Configure ultrasonic sensor pins
  pinMode(ULTRASONIC_FRONT_TRIG, OUTPUT);
  pinMode(ULTRASONIC_FRONT_ECHO, INPUT);
  
  pinMode(ULTRASONIC_LEFT_TRIG, OUTPUT);
  pinMode(ULTRASONIC_LEFT_ECHO, INPUT);
  
  pinMode(ULTRASONIC_RIGHT_TRIG, OUTPUT);
  pinMode(ULTRASONIC_RIGHT_ECHO, INPUT);
  
  pinMode(ULTRASONIC_REAR_TRIG, OUTPUT);
  pinMode(ULTRASONIC_REAR_ECHO, INPUT);
  
  // Ensure all trigger pins are low
  digitalWrite(ULTRASONIC_FRONT_TRIG, LOW);
  digitalWrite(ULTRASONIC_LEFT_TRIG, LOW);
  digitalWrite(ULTRASONIC_RIGHT_TRIG, LOW);
  digitalWrite(ULTRASONIC_REAR_TRIG, LOW);
}

// ==================== COMMAND PROCESSING ====================

void processCommand(JsonDocument& doc) {
  const char* cmd = doc["cmd"];
  
  if (cmd == nullptr) {
    sendError("Missing 'cmd' field");
    return;
  }
  
  // Handle ping command
  if (strcmp(cmd, "ping") == 0) {
    Serial.println("{\"type\":\"pong\"}");
    return;
  }
  
  // Handle motor commands
  if (strcmp(cmd, "motor") == 0) {
    const char* action = doc["action"];
    int speed = doc["speed"] | 100;  // Default speed 100%
    float duration = doc["duration"] | 0.0;  // Default continuous
    
    if (action == nullptr) {
      sendError("Missing 'action' field");
      return;
    }
    
    // Clamp speed to 0-100
    speed = constrain(speed, 0, 100);
    
    // Execute motor action
    if (strcmp(action, "forward") == 0) {
      motorForward(speed, duration);
    } else if (strcmp(action, "backward") == 0) {
      motorBackward(speed, duration);
    } else if (strcmp(action, "turn_left") == 0) {
      motorTurnLeft(speed, duration);
    } else if (strcmp(action, "turn_right") == 0) {
      motorTurnRight(speed, duration);
    } else if (strcmp(action, "stop") == 0) {
      motorStop();
    } else {
      sendError("Invalid motor action");
      return;
    }
    
    sendAck(true);
    return;
  }
  
  // Handle sensor commands
  if (strcmp(cmd, "sensor") == 0) {
    const char* type = doc["type"];
    const char* id = doc["id"];
    
    if (type == nullptr || id == nullptr) {
      sendError("Missing 'type' or 'id' field");
      return;
    }
    
    if (strcmp(type, "ultrasonic") == 0) {
      float distance = -1.0;
      
      // Read the appropriate sensor
      if (strcmp(id, "front") == 0) {
        distance = readUltrasonicDistance(ULTRASONIC_FRONT_TRIG, ULTRASONIC_FRONT_ECHO);
      } else if (strcmp(id, "left") == 0) {
        distance = readUltrasonicDistance(ULTRASONIC_LEFT_TRIG, ULTRASONIC_LEFT_ECHO);
      } else if (strcmp(id, "right") == 0) {
        distance = readUltrasonicDistance(ULTRASONIC_RIGHT_TRIG, ULTRASONIC_RIGHT_ECHO);
      } else if (strcmp(id, "rear") == 0) {
        distance = readUltrasonicDistance(ULTRASONIC_REAR_TRIG, ULTRASONIC_REAR_ECHO);
      } else {
        sendError("Invalid sensor id");
        return;
      }
      
      sendSensorData(id, distance);
      return;
    }
    
    sendError("Invalid sensor type");
    return;
  }
  
  sendError("Unknown command");
}

// ==================== MOTOR CONTROL ====================

void motorForward(int speed, float duration) {
  // Convert speed percentage to PWM value (0-255)
  int pwm = map(speed, 0, 100, 0, 255);
  
  // Set all motors to forward
  digitalWrite(MOTOR_FL_IN1, HIGH);
  digitalWrite(MOTOR_FL_IN2, LOW);
  digitalWrite(MOTOR_FR_IN1, HIGH);
  digitalWrite(MOTOR_FR_IN2, LOW);
  digitalWrite(MOTOR_RL_IN1, HIGH);
  digitalWrite(MOTOR_RL_IN2, LOW);
  digitalWrite(MOTOR_RR_IN1, HIGH);
  digitalWrite(MOTOR_RR_IN2, LOW);
  
  // Set speed for each motor
  ledcWrite(PWM_CHANNEL_FL, pwm);
  ledcWrite(PWM_CHANNEL_FR, pwm);
  ledcWrite(PWM_CHANNEL_RL, pwm);
  ledcWrite(PWM_CHANNEL_RR, pwm);
  
  // If duration specified, run for that time then stop
  if (duration > 0) {
    delay((unsigned long)(duration * 1000));
    motorStop();
  }
}

void motorBackward(int speed, float duration) {
  // Convert speed percentage to PWM value (0-255)
  int pwm = map(speed, 0, 100, 0, 255);
  
  // Set all motors to backward
  digitalWrite(MOTOR_FL_IN1, LOW);
  digitalWrite(MOTOR_FL_IN2, HIGH);
  digitalWrite(MOTOR_FR_IN1, LOW);
  digitalWrite(MOTOR_FR_IN2, HIGH);
  digitalWrite(MOTOR_RL_IN1, LOW);
  digitalWrite(MOTOR_RL_IN2, HIGH);
  digitalWrite(MOTOR_RR_IN1, LOW);
  digitalWrite(MOTOR_RR_IN2, HIGH);
  
  // Set speed for each motor
  ledcWrite(PWM_CHANNEL_FL, pwm);
  ledcWrite(PWM_CHANNEL_FR, pwm);
  ledcWrite(PWM_CHANNEL_RL, pwm);
  ledcWrite(PWM_CHANNEL_RR, pwm);
  
  // If duration specified, run for that time then stop
  if (duration > 0) {
    delay((unsigned long)(duration * 1000));
    motorStop();
  }
}

void motorTurnLeft(int speed, float duration) {
  // Convert speed percentage to PWM value (0-255)
  int pwm = map(speed, 0, 100, 0, 255);
  
  // Left motors backward, right motors forward
  digitalWrite(MOTOR_FL_IN1, LOW);
  digitalWrite(MOTOR_FL_IN2, HIGH);
  digitalWrite(MOTOR_FR_IN1, HIGH);
  digitalWrite(MOTOR_FR_IN2, LOW);
  digitalWrite(MOTOR_RL_IN1, LOW);
  digitalWrite(MOTOR_RL_IN2, HIGH);
  digitalWrite(MOTOR_RR_IN1, HIGH);
  digitalWrite(MOTOR_RR_IN2, LOW);
  
  // Set speed for each motor
  ledcWrite(PWM_CHANNEL_FL, pwm);
  ledcWrite(PWM_CHANNEL_FR, pwm);
  ledcWrite(PWM_CHANNEL_RL, pwm);
  ledcWrite(PWM_CHANNEL_RR, pwm);
  
  // If duration specified, run for that time then stop
  if (duration > 0) {
    delay((unsigned long)(duration * 1000));
    motorStop();
  }
}

void motorTurnRight(int speed, float duration) {
  // Convert speed percentage to PWM value (0-255)
  int pwm = map(speed, 0, 100, 0, 255);
  
  // Left motors forward, right motors backward
  digitalWrite(MOTOR_FL_IN1, HIGH);
  digitalWrite(MOTOR_FL_IN2, LOW);
  digitalWrite(MOTOR_FR_IN1, LOW);
  digitalWrite(MOTOR_FR_IN2, HIGH);
  digitalWrite(MOTOR_RL_IN1, HIGH);
  digitalWrite(MOTOR_RL_IN2, LOW);
  digitalWrite(MOTOR_RR_IN1, LOW);
  digitalWrite(MOTOR_RR_IN2, HIGH);
  
  // Set speed for each motor
  ledcWrite(PWM_CHANNEL_FL, pwm);
  ledcWrite(PWM_CHANNEL_FR, pwm);
  ledcWrite(PWM_CHANNEL_RL, pwm);
  ledcWrite(PWM_CHANNEL_RR, pwm);
  
  // If duration specified, run for that time then stop
  if (duration > 0) {
    delay((unsigned long)(duration * 1000));
    motorStop();
  }
}

void motorStop() {
  // Set all direction pins low (short brake mode for TB6612FNG)
  digitalWrite(MOTOR_FL_IN1, LOW);
  digitalWrite(MOTOR_FL_IN2, LOW);
  digitalWrite(MOTOR_FR_IN1, LOW);
  digitalWrite(MOTOR_FR_IN2, LOW);
  digitalWrite(MOTOR_RL_IN1, LOW);
  digitalWrite(MOTOR_RL_IN2, LOW);
  digitalWrite(MOTOR_RR_IN1, LOW);
  digitalWrite(MOTOR_RR_IN2, LOW);
  
  // Set PWM to 0
  ledcWrite(PWM_CHANNEL_FL, 0);
  ledcWrite(PWM_CHANNEL_FR, 0);
  ledcWrite(PWM_CHANNEL_RL, 0);
  ledcWrite(PWM_CHANNEL_RR, 0);
}

// ==================== SENSOR READING ====================

float readUltrasonicDistance(int trigPin, int echoPin) {
  // Send 10us pulse
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  // Read echo pulse (with timeout)
  long duration = pulseIn(echoPin, HIGH, 30000);  // 30ms timeout
  
  // If timeout or invalid reading
  if (duration == 0) {
    return -1.0;
  }
  
  // Calculate distance in centimeters
  // Speed of sound: 343 m/s = 0.0343 cm/us
  // Distance = (duration * 0.0343) / 2
  float distance = (duration * 0.0343) / 2.0;
  
  // Filter unrealistic values (HC-SR04 range: 2-400cm)
  if (distance < 2.0 || distance > 400.0) {
    return -1.0;
  }
  
  return distance;
}

// ==================== SERIAL RESPONSES ====================

void sendAck(bool success, const char* message) {
  JsonDocument doc;
  doc["type"] = "ack";
  doc["status"] = success ? "ok" : "error";
  
  if (message != nullptr && strlen(message) > 0) {
    doc["message"] = message;
  }
  
  serializeJson(doc, Serial);
  Serial.println();
}

void sendSensorData(const char* id, float distance) {
  JsonDocument doc;
  doc["type"] = "sensor";
  doc["id"] = id;
  doc["distance"] = distance;
  
  serializeJson(doc, Serial);
  Serial.println();
}

void sendError(const char* message) {
  JsonDocument doc;
  doc["type"] = "error";
  doc["message"] = message;
  
  serializeJson(doc, Serial);
  Serial.println();
}

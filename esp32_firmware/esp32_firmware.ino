/**
 * LangRover ESP32 Firmware - Dual Core Edition
 * 
 * This firmware enables the ESP32 to act as a hardware controller for the LangRover robot.
 * It receives JSON commands via USB Serial from a Raspberry Pi and controls motors and sensors.
 * 
 * DUAL CORE ARCHITECTURE:
 * - Core 0: Serial communication and motor control (main loop)
 * - Core 1: Continuous sensor reading and world state updates (dedicated task)
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
#include <WiFi.h>
#include <ArduinoOTA.h>

// WiFi credentials — copy secrets.h.example → secrets.h and fill in your values.
// If secrets.h is absent (e.g. fresh clone), the sketch still compiles; OTA is simply disabled.
#if __has_include("secrets.h")
  #include "secrets.h"
#else
  #define WIFI_SSID      ""  // no secrets.h — OTA disabled
  #define WIFI_PASSWORD  ""
  #define OTA_PASSWORD   ""
#endif

// ==================== GLOBAL STATE & SYNCHRONIZATION ====================

// Sensor data structure for thread-safe access
struct SensorState {
  float frontDistance;
  float leftDistance;
  float rightDistance;
  float rearDistance;
  unsigned long lastUpdateTime;
};

// Global sensor state (shared between cores)
volatile SensorState sensorState = {-1.0, -1.0, -1.0, -1.0, 0};

// Mutex for thread-safe sensor data access
SemaphoreHandle_t sensorMutex;

// Mutex for thread-safe Serial writes (Core 0 responses vs Core 1 sensor reports)
SemaphoreHandle_t serialMutex;

// Task handle for sensor task (Core 1)
TaskHandle_t sensorTaskHandle = NULL;

// OTA enabled flag — set to true after a successful Wi-Fi + OTA initialisation
bool otaEnabled = false;

// Sensor update interval in milliseconds
#define SENSOR_UPDATE_INTERVAL 100  // 10Hz update rate
#define SENSOR_REPORT_INTERVAL 500  // Report to serial every 500ms

// ==================== OTA / WIFI CONFIGURATION ====================
// WIFI_SSID, WIFI_PASSWORD and OTA_PASSWORD come from secrets.h (gitignored).
// Leave WIFI_SSID as "" in secrets.h to skip Wi-Fi/OTA entirely (USB-only operation).
#define OTA_HOSTNAME             "langrover-esp32"
#define WIFI_CONNECT_TIMEOUT_MS  10000          // ms to wait for Wi-Fi before giving up

// ==================== PIN DEFINITIONS ====================
//
// GPIO conflict resolution summary:
//   The original design had three GPIO conflicts:
//     GPIO  2 → MOTOR_RR_PWM       vs ULTRASONIC_REAR_ECHO
//     GPIO  4 → MOTOR_RR_IN2       vs ULTRASONIC_REAR_TRIG
//     GPIO 19 → MOTOR_DRIVER_2_STBY vs ULTRASONIC_LEFT_TRIG
//
//   Fix: All four ECHO pins moved to input-only GPIOs (34/35/36/39),
//   which are read-only by hardware and therefore ideal for receive signals.
//   The freed output-capable pins are reused for TRIG/STBY:
//
//   ULTRASONIC_FRONT_ECHO  22 → 34  (input-only GPIO)
//   ULTRASONIC_LEFT_ECHO   18 → 35  (input-only GPIO)
//   ULTRASONIC_RIGHT_ECHO  16 → 36  (input-only GPIO)
//   ULTRASONIC_REAR_ECHO    2 → 39  (input-only GPIO)  fixes conflict #1
//   ULTRASONIC_LEFT_TRIG   19 → 18  (freed from LEFT_ECHO)  fixes conflict #3
//   MOTOR_DRIVER_2_STBY    19 → 22  (freed from FRONT_ECHO) fixes conflict #3
//   ULTRASONIC_REAR_TRIG    4 → 16  (freed from RIGHT_ECHO) fixes conflict #2

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

#define MOTOR_DRIVER_2_STBY  22  // Standby for Driver 2 (Rear motors) — moved from GPIO 19

// HC-SR04 Ultrasonic Sensors
// ECHO pins use input-only GPIOs (34, 35, 36, 39) — ideal for receive-only signals
#define ULTRASONIC_FRONT_TRIG  23
#define ULTRASONIC_FRONT_ECHO  34  // Input-only GPIO — moved from GPIO 22

#define ULTRASONIC_LEFT_TRIG   18  // Moved from GPIO 19 to free it for MOTOR_DRIVER_2_STBY
#define ULTRASONIC_LEFT_ECHO   35  // Input-only GPIO — moved from GPIO 18

#define ULTRASONIC_RIGHT_TRIG  17
#define ULTRASONIC_RIGHT_ECHO  36  // Input-only GPIO — moved from GPIO 16

#define ULTRASONIC_REAR_TRIG   16  // Moved from GPIO 4 to free it for MOTOR_RR_IN2
#define ULTRASONIC_REAR_ECHO   39  // Input-only GPIO — moved from GPIO 2

// PWM Configuration
#define PWM_FREQ      20000   // 20kHz PWM frequency (recommended for TB6612FNG)
#define PWM_RESOLUTION 8      // 8-bit resolution (0-255)

// ==================== FUNCTION PROTOTYPES ====================

void setupMotors();
void setupSensors();
void processCommand(JsonDocument& doc);
void sendAck(bool success, const char* message = "");
void sendSensorData(const char* id, float distance);
void sendAllSensorData();
void sendError(const char* message);

void motorForward(int speed, float duration = 0);
void motorBackward(int speed, float duration = 0);
void motorTurnLeft(int speed, float duration = 0);
void motorTurnRight(int speed, float duration = 0);
void motorStop();
void motorSingleRun(const char* motor, const char* direction, int speed, float duration);

float readUltrasonicDistance(int trigPin, int echoPin);
void updateSensorState(float front, float left, float right, float rear);
void getSensorState(float* front, float* left, float* right, float* rear);

// Core 1 task: Continuous sensor reading
void sensorTask(void* parameter);

// OTA / Wi-Fi initialisation
void setupOTA();

// ==================== SETUP ====================

void setup() {
  Serial.begin(115200);
  Serial.println("{\"type\":\"info\",\"message\":\"ESP32 Dual-Core Initialization...\"}");

  // Create mutex for sensor data synchronization
  sensorMutex = xSemaphoreCreateMutex();

  if (sensorMutex == NULL) {
    Serial.println("{\"type\":\"error\",\"message\":\"Failed to create mutex\"}");
    while (1);  // Halt if mutex creation fails
  }

  serialMutex = xSemaphoreCreateMutex();
  if (serialMutex == NULL) {
    Serial.println("{\"type\":\"error\",\"message\":\"Failed to create serial mutex\"}");
    while (1);
  }

  // Setup hardware
  setupMotors();
  setupSensors();
  setupOTA();

  // Create sensor reading task pinned to Core 1
  xTaskCreatePinnedToCore(
    sensorTask,         // Task function
    "SensorTask",       // Task name
    4096,               // Stack size in bytes
    NULL,               // Task parameter
    1,                  // Priority
    &sensorTaskHandle,  // Task handle
    1                   // Core 1
  );

  Serial.println("{\"type\":\"ready\",\"message\":\"ESP32 initialized\"}");
}

// ==================== MAIN LOOP (Core 0) ====================
// Handles serial communication and motor control

void loop() {
  // Service OTA when Wi-Fi is available (non-blocking)
  if (otaEnabled) ArduinoOTA.handle();

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

// ==================== SENSOR TASK (Core 1) ====================
// Continuously reads all sensors and updates shared world state

void sensorTask(void* parameter) {
  unsigned long lastUpdate = 0;
  unsigned long lastReport = 0;
  
  while(1) {
    unsigned long currentTime = millis();
    
    // Update sensors at defined interval
    if (currentTime - lastUpdate >= SENSOR_UPDATE_INTERVAL) {
      // Read all sensors (non-blocking for each sensor)
      float front = readUltrasonicDistance(ULTRASONIC_FRONT_TRIG, ULTRASONIC_FRONT_ECHO);
      delay(10); // Small delay between sensor readings to avoid interference
      
      float left = readUltrasonicDistance(ULTRASONIC_LEFT_TRIG, ULTRASONIC_LEFT_ECHO);
      delay(10);
      
      float right = readUltrasonicDistance(ULTRASONIC_RIGHT_TRIG, ULTRASONIC_RIGHT_ECHO);
      delay(10);
      
      float rear = readUltrasonicDistance(ULTRASONIC_REAR_TRIG, ULTRASONIC_REAR_ECHO);

      // Update shared sensor state (thread-safe)
      updateSensorState(front, left, right, rear);
      lastUpdate = currentTime;
    }
    
    // Periodically report sensor data to serial
    if (currentTime - lastReport >= SENSOR_REPORT_INTERVAL) {
      sendAllSensorData();
      lastReport = currentTime;
    }
    
    // Yield to other tasks
    vTaskDelay(10 / portTICK_PERIOD_MS);
  }
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
  
  // Configure PWM for each motor independently (ESP32 Arduino core v3 API)
  ledcAttach(MOTOR_FL_PWM, PWM_FREQ, PWM_RESOLUTION);
  ledcAttach(MOTOR_FR_PWM, PWM_FREQ, PWM_RESOLUTION);
  ledcAttach(MOTOR_RL_PWM, PWM_FREQ, PWM_RESOLUTION);
  ledcAttach(MOTOR_RR_PWM, PWM_FREQ, PWM_RESOLUTION);
  
  // Enable both drivers (STBY HIGH)
  digitalWrite(MOTOR_DRIVER_1_STBY, HIGH);
  digitalWrite(MOTOR_DRIVER_2_STBY, HIGH);
  
  // Initialize motors in stopped state
  motorStop();
}

// ==================== OTA SETUP ====================

void setupOTA() {
  if (strlen(WIFI_SSID) == 0) {
    Serial.println("{\"type\":\"info\",\"message\":\"OTA disabled — no WIFI_SSID configured\"}");
    return;
  }

  JsonDocument infoDoc;
  infoDoc["type"] = "info";
  infoDoc["message"] = "Connecting to Wi-Fi";
  infoDoc["ssid"] = WIFI_SSID;
  serializeJson(infoDoc, Serial);
  Serial.println();

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long startMs = millis();
  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - startMs > WIFI_CONNECT_TIMEOUT_MS) {
      Serial.println("{\"type\":\"error\",\"message\":\"Wi-Fi connection timed out — OTA unavailable\"}");
      return;
    }
    delay(200);
  }

  ArduinoOTA.setHostname(OTA_HOSTNAME);
  if (strlen(OTA_PASSWORD) > 0) {
    ArduinoOTA.setPassword(OTA_PASSWORD);
  }

  ArduinoOTA.onStart([]() {
    // Safety first: stop all motors before overwriting flash
    motorStop();
    String updateType = (ArduinoOTA.getCommand() == U_FLASH) ? "sketch" : "filesystem";
    JsonDocument doc;
    doc["type"] = "ota_start";
    doc["update_type"] = updateType;
    if (xSemaphoreTake(serialMutex, portMAX_DELAY) == pdTRUE) {
      serializeJson(doc, Serial);
      Serial.println();
      xSemaphoreGive(serialMutex);
    }
  });

  ArduinoOTA.onEnd([]() {
    if (xSemaphoreTake(serialMutex, portMAX_DELAY) == pdTRUE) {
      Serial.println("{\"type\":\"ota_end\",\"message\":\"Update complete — rebooting\"}");
      xSemaphoreGive(serialMutex);
    }
  });

  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    // Report only on each 10% boundary to avoid flooding Serial
    static unsigned int lastPct = 101;  // sentinel: force first report
    unsigned int pct = (progress * 100) / total;
    if (pct / 10 != lastPct / 10) {
      lastPct = pct;
      JsonDocument doc;
      doc["type"] = "ota_progress";
      doc["percent"] = pct;
      if (xSemaphoreTake(serialMutex, portMAX_DELAY) == pdTRUE) {
        serializeJson(doc, Serial);
        Serial.println();
        xSemaphoreGive(serialMutex);
      }
    }
  });

  ArduinoOTA.onError([](ota_error_t error) {
    const char* errStr = "Unknown error";
    if      (error == OTA_AUTH_ERROR)    errStr = "Auth failed";
    else if (error == OTA_BEGIN_ERROR)   errStr = "Begin failed";
    else if (error == OTA_CONNECT_ERROR) errStr = "Connect failed";
    else if (error == OTA_RECEIVE_ERROR) errStr = "Receive failed";
    else if (error == OTA_END_ERROR)     errStr = "End failed";
    JsonDocument doc;
    doc["type"] = "ota_error";
    doc["message"] = errStr;
    if (xSemaphoreTake(serialMutex, portMAX_DELAY) == pdTRUE) {
      serializeJson(doc, Serial);
      Serial.println();
      xSemaphoreGive(serialMutex);
    }
  });

  ArduinoOTA.begin();
  otaEnabled = true;

  JsonDocument readyDoc;
  readyDoc["type"] = "info";
  readyDoc["message"] = "OTA ready";
  readyDoc["hostname"] = OTA_HOSTNAME;
  readyDoc["ip"] = WiFi.localIP().toString();
  serializeJson(readyDoc, Serial);
  Serial.println();
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
    JsonDocument resp;
    resp["type"] = "pong";
    if (xSemaphoreTake(serialMutex, portMAX_DELAY) == pdTRUE) {
      serializeJson(resp, Serial);
      Serial.println();
      xSemaphoreGive(serialMutex);
    }
    return;
  }

  // Handle motor commands
  if (strcmp(cmd, "motor") == 0) {
    const char* action   = doc["action"];
    int         speed    = doc["speed"]    | 70;
    float       duration = doc["duration"] | 0.0f;

    if (action == nullptr) {
      sendError("Missing 'action' field");
      return;
    }

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
    const char* id   = doc["id"];

    if (type == nullptr) {
      sendError("Missing 'type' field");
      return;
    }

    if (strcmp(type, "ultrasonic") == 0) {
      // No id or "all" → return all sensor values
      if (id == nullptr || strcmp(id, "all") == 0) {
        sendAllSensorData();
        return;
      }

      // Return cached value for the requested sensor
      float front, left, right, rear;
      getSensorState(&front, &left, &right, &rear);

      float distance = -1.0;
      if (strcmp(id, "front") == 0) {
        distance = front;
      } else if (strcmp(id, "left") == 0) {
        distance = left;
      } else if (strcmp(id, "right") == 0) {
        distance = right;
      } else if (strcmp(id, "rear") == 0) {
        distance = rear;
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

  // Handle debug commands — individual motor control for hardware testing
  if (strcmp(cmd, "debug") == 0) {
    const char* subCmd = doc["subcmd"];

    if (subCmd == nullptr) {
      sendError("Missing 'subcmd' field");
      return;
    }

    if (strcmp(subCmd, "motor") == 0) {
      const char* motor     = doc["motor"];     // "fl" | "fr" | "rl" | "rr"
      const char* direction = doc["direction"]; // "forward" | "backward" | "stop"
      int         speed     = doc["speed"]    | 70;
      float       duration  = doc["duration"] | 0.0f;

      if (motor == nullptr) {
        sendError("Missing 'motor' field (fl/fr/rl/rr)");
        return;
      }
      if (direction == nullptr) {
        sendError("Missing 'direction' field (forward/backward/stop)");
        return;
      }

      motorSingleRun(motor, direction, speed, duration);
      sendAck(true);
      return;
    }

    sendError("Unknown debug subcmd");
    return;
  }

  // Handle OTA status query
  if (strcmp(cmd, "ota_status") == 0) {
    JsonDocument resp;
    resp["type"] = "ota_status";
    resp["enabled"] = otaEnabled;
    if (otaEnabled) {
      resp["hostname"] = OTA_HOSTNAME;
      resp["ip"] = WiFi.localIP().toString();
    }
    if (xSemaphoreTake(serialMutex, portMAX_DELAY) == pdTRUE) {
      serializeJson(resp, Serial);
      Serial.println();
      xSemaphoreGive(serialMutex);
    }
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
  ledcWrite(MOTOR_FL_PWM, pwm);
  ledcWrite(MOTOR_FR_PWM, pwm);
  ledcWrite(MOTOR_RL_PWM, pwm);
  ledcWrite(MOTOR_RR_PWM, pwm);
  
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
  ledcWrite(MOTOR_FL_PWM, pwm);
  ledcWrite(MOTOR_FR_PWM, pwm);
  ledcWrite(MOTOR_RL_PWM, pwm);
  ledcWrite(MOTOR_RR_PWM, pwm);
  
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
  ledcWrite(MOTOR_FL_PWM, pwm);
  ledcWrite(MOTOR_FR_PWM, pwm);
  ledcWrite(MOTOR_RL_PWM, pwm);
  ledcWrite(MOTOR_RR_PWM, pwm);
  
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
  ledcWrite(MOTOR_FL_PWM, pwm);
  ledcWrite(MOTOR_FR_PWM, pwm);
  ledcWrite(MOTOR_RL_PWM, pwm);
  ledcWrite(MOTOR_RR_PWM, pwm);
  
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
  ledcWrite(MOTOR_FL_PWM, 0);
  ledcWrite(MOTOR_FR_PWM, 0);
  ledcWrite(MOTOR_RL_PWM, 0);
  ledcWrite(MOTOR_RR_PWM, 0);
}

// ==================== DEBUG: SINGLE MOTOR CONTROL ====================
// Drives one motor independently — used for wiring/hardware verification.
// motor:     "fl" (front-left) | "fr" (front-right)
//            "rl" (rear-left)  | "rr" (rear-right)
// direction: "forward" | "backward" | "stop"
// speed:     0-100 (percentage)
// duration:  seconds to run, then auto-stop (0 = run until explicit stop)

void motorSingleRun(const char* motor, const char* direction, int speed, float duration) {
  // Resolve pin set for the requested motor
  int in1Pin, in2Pin, pwmPin;

  if (strcmp(motor, "fl") == 0) {
    in1Pin = MOTOR_FL_IN1; in2Pin = MOTOR_FL_IN2; pwmPin = MOTOR_FL_PWM;
  } else if (strcmp(motor, "fr") == 0) {
    in1Pin = MOTOR_FR_IN1; in2Pin = MOTOR_FR_IN2; pwmPin = MOTOR_FR_PWM;
  } else if (strcmp(motor, "rl") == 0) {
    in1Pin = MOTOR_RL_IN1; in2Pin = MOTOR_RL_IN2; pwmPin = MOTOR_RL_PWM;
  } else if (strcmp(motor, "rr") == 0) {
    in1Pin = MOTOR_RR_IN1; in2Pin = MOTOR_RR_IN2; pwmPin = MOTOR_RR_PWM;
  } else {
    sendError("Invalid motor id — use fl/fr/rl/rr");
    return;
  }

  if (strcmp(direction, "stop") == 0) {
    // Brake: both IN pins LOW, PWM 0
    digitalWrite(in1Pin, LOW);
    digitalWrite(in2Pin, LOW);
    ledcWrite(pwmPin, 0);
    return;
  }

  int pwm = map(speed, 0, 100, 0, 255);

  if (strcmp(direction, "forward") == 0) {
    digitalWrite(in1Pin, HIGH);
    digitalWrite(in2Pin, LOW);
  } else if (strcmp(direction, "backward") == 0) {
    digitalWrite(in1Pin, LOW);
    digitalWrite(in2Pin, HIGH);
  } else {
    sendError("Invalid direction — use forward/backward/stop");
    return;
  }

  ledcWrite(pwmPin, pwm);

  if (duration > 0) {
    delay((unsigned long)(duration * 1000));
    // Stop only this motor after the timed run
    digitalWrite(in1Pin, LOW);
    digitalWrite(in2Pin, LOW);
    ledcWrite(pwmPin, 0);
  }
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
  // Speed of sound: 343 m/s = 0.0343 cm/µs
  // Distance = (duration * 0.0343) / 2  (round trip)
  return (duration * 0.0343f) / 2.0f;
}

// ==================== SENSOR STATE MANAGEMENT ====================

// Thread-safe update of sensor state (called by Core 1)
void updateSensorState(float front, float left, float right, float rear) {
  if (xSemaphoreTake(sensorMutex, portMAX_DELAY) == pdTRUE) {
    sensorState.frontDistance = front;
    sensorState.leftDistance = left;
    sensorState.rightDistance = right;
    sensorState.rearDistance = rear;
    sensorState.lastUpdateTime = millis();
    xSemaphoreGive(sensorMutex);
  }
}

// Thread-safe read of sensor state (called by Core 0)
void getSensorState(float* front, float* left, float* right, float* rear) {
  if (xSemaphoreTake(sensorMutex, portMAX_DELAY) == pdTRUE) {
    *front = sensorState.frontDistance;
    *left = sensorState.leftDistance;
    *right = sensorState.rightDistance;
    *rear = sensorState.rearDistance;
    xSemaphoreGive(sensorMutex);
  }
}

// ==================== SERIAL RESPONSES ====================

void sendAck(bool success, const char* message) {
  JsonDocument doc;
  doc["type"] = "ack";
  doc["status"] = success ? "ok" : "error";
  
  if (message != nullptr && strlen(message) > 0) {
    doc["message"] = message;
  }
  
  if (xSemaphoreTake(serialMutex, portMAX_DELAY) == pdTRUE) {
    serializeJson(doc, Serial);
    Serial.println();
    xSemaphoreGive(serialMutex);
  }
}

void sendSensorData(const char* id, float distance) {
  JsonDocument doc;
  doc["type"] = "sensor";
  doc["id"] = id;
  doc["distance"] = distance;
  
  if (xSemaphoreTake(serialMutex, portMAX_DELAY) == pdTRUE) {
    serializeJson(doc, Serial);
    Serial.println();
    xSemaphoreGive(serialMutex);
  }
}

void sendAllSensorData() {
  float front, left, right, rear;
  getSensorState(&front, &left, &right, &rear);
  
  JsonDocument doc;
  doc["type"] = "sensor_state";
  doc["front"] = front;
  doc["left"] = left;
  doc["right"] = right;
  doc["rear"] = rear;
  doc["timestamp"] = millis();

  if (xSemaphoreTake(serialMutex, portMAX_DELAY) == pdTRUE) {
    serializeJson(doc, Serial);
    Serial.println();
    xSemaphoreGive(serialMutex);
  }
}

void sendError(const char* message) {
  JsonDocument doc;
  doc["type"] = "error";
  doc["message"] = message;
  
  if (xSemaphoreTake(serialMutex, portMAX_DELAY) == pdTRUE) {
    serializeJson(doc, Serial);
    Serial.println();
    xSemaphoreGive(serialMutex);
  }
}

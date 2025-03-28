#include <Arduino.h>

// ----- Hardware Definitions -----
#define STEP_PIN 26
#define DIR_PIN 25

// ----- Constants -----
#define STEPS_PER_REVOLUTION 200  // Change if your motor has a different specification

// ----- Global State Variables -----
volatile bool running = false;         // Indicates if motor stepping is active
volatile uint8_t currentMode = 0;        // 0: Idle, 1: Continuous, 2: Step Count, 3: Play Note
volatile unsigned long lastStepTime = 0; // microseconds
volatile unsigned long stepInterval = 1000000; // default 1 sec period between steps (in microseconds)
volatile int stepsRemaining = 0;         // For STEP mode
volatile unsigned long noteEndTime = 0;  // For PLAY_NOTE mode (millis)

void pulseStep() {
  // Generate a brief step pulse
  digitalWrite(STEP_PIN, HIGH);
  delayMicroseconds(10);  // 10 µs pulse width (adjust if needed)
  digitalWrite(STEP_PIN, LOW);
}

void parseCommand(String cmd);

void setup() {
  Serial.begin(115200);
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  Serial.println("Stepper Controller Ready");
}

void loop() {
  // Process incoming serial commands (nonblocking)
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    if (command.length() > 0) {
      parseCommand(command);
    }
  }
  
  // Process motor stepping based on current mode:
  unsigned long currentMicros = micros();
  if (running && (currentMicros - lastStepTime >= stepInterval)) {
    pulseStep();
    lastStepTime = currentMicros;
    
    if (currentMode == 2) {  // STEP count mode
      stepsRemaining--;
      if (stepsRemaining <= 0) {
        running = false;
        currentMode = 0;
      }
    } else if (currentMode == 3) {  // PLAY_NOTE mode
      if (millis() >= noteEndTime) {
        running = false;
        currentMode = 0;
      }
    }
    // For continuous mode (currentMode == 1) do nothing extra
  }
}

void parseCommand(String cmd) {
  // Examples of valid commands:
  // START
  // STOP
  // SET_SPEED 120 RPM
  // SET_SPEED 200 Steps/Sec
  // SET_DIRECTION CW
  // STEP 100
  // DECAY 50
  // PLAY_NOTE 440 500
  cmd.trim();
  if (cmd.startsWith("START")) {
    running = true;
    currentMode = 1; // continuous
    Serial.println("Continuous motion started.");
  } else if (cmd.startsWith("STOP")) {
    running = false;
    currentMode = 0;
    Serial.println("Motion stopped.");
  } else if (cmd.startsWith("SET_SPEED")) {
    // Format: SET_SPEED <value> <unit>
    int firstSpace = cmd.indexOf(' ');
    String rest = cmd.substring(firstSpace + 1);
    int secondSpace = rest.indexOf(' ');
    if (secondSpace == -1) {
      Serial.println("Error: Invalid SET_SPEED format.");
      return;
    }
    String speedStr = rest.substring(0, secondSpace);
    String unit = rest.substring(secondSpace + 1);
    float speedVal = speedStr.toFloat();
    if (unit == "RPM") {
      // Convert RPM to step interval:
      // steps/min = RPM * STEPS_PER_REVOLUTION, so steps/sec = RPM * STEPS_PER_REVOLUTION / 60.
      // Then period in microseconds = 1e6 / (steps/sec)
      if (speedVal > 0) {
        stepInterval = (unsigned long)(1e6 * 60 / (speedVal * STEPS_PER_REVOLUTION));
        Serial.print("Speed set to ");
        Serial.print(speedVal);
        Serial.println(" RPM");
      }
    } else if (unit == "Steps/Sec") {
      if (speedVal > 0) {
        stepInterval = (unsigned long)(1e6 / speedVal);
        Serial.print("Speed set to ");
        Serial.print(speedVal);
        Serial.println(" Steps/Sec");
      }
    } else {
      Serial.println("Error: Unknown speed unit.");
    }
  } else if (cmd.startsWith("SET_DIRECTION")) {
    // Format: SET_DIRECTION CW or CCW
    int spaceIndex = cmd.indexOf(' ');
    String direction = cmd.substring(spaceIndex + 1);
    direction.trim();
    if (direction == "CW") {
      digitalWrite(DIR_PIN, HIGH);
      Serial.println("Direction set to CW");
    } else if (direction == "CCW") {
      digitalWrite(DIR_PIN, LOW);
      Serial.println("Direction set to CCW");
    } else {
      Serial.println("Error: Unknown direction.");
    }
  } else if (cmd.startsWith("STEP")) {
    // Format: STEP <number>
    int spaceIndex = cmd.indexOf(' ');
    String stepsStr = cmd.substring(spaceIndex + 1);
    stepsRemaining = stepsStr.toInt();
    if (stepsRemaining > 0) {
      currentMode = 2;  // single-step mode
      running = true;
      Serial.print("Stepping ");
      Serial.print(stepsRemaining);
      Serial.println(" steps.");
    } else {
      Serial.println("Error: Invalid step count.");
    }
  } else if (cmd.startsWith("DECAY")) {
    // DECAY command: not implemented in this firmware (hardware parameter typically set externally)
    Serial.println("DECAY command received (not implemented).");
  } else if (cmd.startsWith("PLAY_NOTE")) {
    // Format: PLAY_NOTE <frequency> <duration_ms>
    int firstSpace = cmd.indexOf(' ');
    String rest = cmd.substring(firstSpace + 1);
    int secondSpace = rest.indexOf(' ');
    if (secondSpace == -1) {
      Serial.println("Error: Invalid PLAY_NOTE format.");
      return;
    }
    String freqStr = rest.substring(0, secondSpace);
    String durationStr = rest.substring(secondSpace + 1);
    float frequency = freqStr.toFloat();
    int duration = durationStr.toInt();
    if (frequency > 0 && duration > 0) {
      // Set the step interval to generate the desired frequency.
      stepInterval = (unsigned long)(1e6 / frequency);
      noteEndTime = millis() + duration;
      currentMode = 3;  // play note mode
      running = true;
      Serial.print("Playing note at ");
      Serial.print(frequency);
      Serial.print(" Hz for ");
      Serial.print(duration);
      Serial.println(" ms.");
    } else {
      Serial.println("Error: Invalid frequency or duration.");
    }
  } else {
    Serial.print("Unknown command: ");
    Serial.println(cmd);
  }
}

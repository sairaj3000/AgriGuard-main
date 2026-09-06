/*
 * Agriculture Surveillance - Arduino Defense Controller (4-Channel Relay)
 * Commands from Python:
 * 'M' - Motor Relay (birds)
 * 'L' - Lights Relay (human)
 * 'B' - Buzzer Relay (elephant)
 * 'E' - Extra Relay 4 (optional)
 * 'S' - Stop all
 */

// Relay Pin Definitions
#define RELAY_MOTOR 8       // Relay CH1
#define RELAY_BUZZER 9      // Relay CH2
#define RELAY_LIGHT 7       // Relay CH3
#define RELAY_EXTRA 6       // Relay CH4 (optional)
#define LED_INDICATOR 13    // Status LED

// Relay Active State (most relay boards are active LOW)
#define RELAY_ON  LOW
#define RELAY_OFF HIGH

// State Variables
bool motorActive = false;
bool buzzerActive = false;
bool lightActive = false;
bool extraActive = false;

unsigned long motorStart = 0;
unsigned long buzzerStart = 0;
unsigned long lightStart = 0;
unsigned long extraStart = 0;

// Duration settings (milliseconds)
#define MOTOR_DURATION 10000
#define BUZZER_DURATION 15000
#define LIGHT_DURATION 20000
#define EXTRA_DURATION 12000  // You can change this

void setup() {
  Serial.begin(9600);

  pinMode(RELAY_MOTOR, OUTPUT);
  pinMode(RELAY_BUZZER, OUTPUT);
  pinMode(RELAY_LIGHT, OUTPUT);
  pinMode(RELAY_EXTRA, OUTPUT);
  pinMode(LED_INDICATOR, OUTPUT);

  stopAll();

  Serial.println("4-Channel Relay Agriculture System Ready");
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    handleCommand(cmd);
  }

  checkAutoStop();
  updateStatusLED();
}

void handleCommand(char cmd) {
  switch(cmd) {
    case 'M':
      activateMotor();
      Serial.println("CMD: Motor Activated");
      break;

    case 'L':
      activateLight();
      Serial.println("CMD: Light Activated");
      break;

    case 'B':
      activateBuzzer();
      Serial.println("CMD: Buzzer Activated");
      break;

    case 'E':
      activateExtra();
      Serial.println("CMD: Extra Relay Activated");
      break;

    case 'S':
      stopAll();
      Serial.println("CMD: All Stopped");
      break;

    default:
      Serial.println("CMD: Unknown");
  }
}

/* ---------------- Relay Activation ---------------- */

void activateMotor() {
  digitalWrite(RELAY_MOTOR, RELAY_ON);
  motorActive = true;
  motorStart = millis();
}

void activateLight() {
  digitalWrite(RELAY_LIGHT, RELAY_ON);
  lightActive = true;
  lightStart = millis();
}

void activateBuzzer() {
  digitalWrite(RELAY_BUZZER, RELAY_ON);
  buzzerActive = true;
  buzzerStart = millis();
}

void activateExtra() {
  digitalWrite(RELAY_EXTRA, RELAY_ON);
  extraActive = true;
  extraStart = millis();
}

/* ---------------- Relay Stop ---------------- */

void stopMotor() {
  digitalWrite(RELAY_MOTOR, RELAY_OFF);
  motorActive = false;
}

void stopLight() {
  digitalWrite(RELAY_LIGHT, RELAY_OFF);
  lightActive = false;
}

void stopBuzzer() {
  digitalWrite(RELAY_BUZZER, RELAY_OFF);
  buzzerActive = false;
}

void stopExtra() {
  digitalWrite(RELAY_EXTRA, RELAY_OFF);
  extraActive = false;
}

void stopAll() {
  stopMotor();
  stopLight();
  stopBuzzer();
  stopExtra();
  Serial.println("All Systems: OFF");
}

/* ---------------- Auto-Stop Handling ---------------- */

void checkAutoStop() {
  unsigned long now = millis();

  if (motorActive && (now - motorStart >= MOTOR_DURATION)) stopMotor();
  if (buzzerActive && (now - buzzerStart >= BUZZER_DURATION)) stopBuzzer();
  if (lightActive && (now - lightStart >= LIGHT_DURATION)) stopLight();
  if (extraActive && (now - extraStart >= EXTRA_DURATION)) stopExtra();
}

/* ---------------- LED Indicator ---------------- */

void updateStatusLED() {
  if (motorActive || buzzerActive || lightActive || extraActive) {
    if (millis() % 500 < 250) digitalWrite(LED_INDICATOR, HIGH);
    else digitalWrite(LED_INDICATOR, LOW);
  } else {
    if (millis() % 2000 < 100) digitalWrite(LED_INDICATOR, HIGH);
    else digitalWrite(LED_INDICATOR, LOW);
  }
}

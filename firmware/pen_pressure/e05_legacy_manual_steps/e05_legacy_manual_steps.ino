/*
  E-05 legacy-map manual N20 step test

  Historical E-05 electrical roles are intentionally retained for A/B testing:
    GP4 -> DRV8833 IN1
    GP5 -> DRV8833 IN2
    GP6 <- EEP legacy fault input, INPUT_PULLUP
    GP7 -> ULT legacy sleep output, HIGH enables

  Service UART (3.3 V adapter, 115200 baud):
    Adapter GND -> TOOL_GND; RXD <- GP20; TXD -> GP21; VCC disconnected.

  Commands:
    u  first historical direction for the selected duration
    d  reverse historical direction for the selected duration
    [  decrease duration by 100 ms (minimum 100 ms)
    ]  increase duration by 100 ms (maximum 1000 ms)
    x  stop and sleep when no step is in progress
    ?  print help

  This sketch has no LIFT_HOME motion stop. Keep clear travel in the selected
  direction and send one manual pulse at a time.
*/

#include <Arduino.h>

constexpr uint8_t PIN_IN1 = 4;
constexpr uint8_t PIN_IN2 = 5;
constexpr uint8_t PIN_EEP_LEGACY_FAULT = 6;
constexpr uint8_t PIN_ULT_LEGACY_SLEEP = 7;
constexpr uint8_t PIN_UART_TX = 20;
constexpr uint8_t PIN_UART_RX = 21;

constexpr uint32_t SERIAL_BAUD = 115200;
constexpr uint16_t STEP_MIN_MS = 100;
constexpr uint16_t STEP_MAX_MS = 1000;
constexpr uint16_t STEP_INCREMENT_MS = 100;
constexpr bool LEGACY_FIRST_IN1_HIGH = true;
constexpr bool LEGACY_REVERSE_IN1_HIGH = false;

uint16_t stepMs = STEP_MIN_MS;

bool legacyFaultActive() {
  return digitalRead(PIN_EEP_LEGACY_FAULT) == LOW;
}

void stopAndSleep() {
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
  digitalWrite(PIN_ULT_LEGACY_SLEEP, LOW);
}

void printHelp() {
  Serial2.println(F("LEGACY E-05: u=first d=reverse [=shorter ]=longer x=idle-stop ?=help"));
  Serial2.print(F("Current duration: "));
  Serial2.print(stepMs);
  Serial2.println(F(" ms"));
}

void moveOneStep(bool in1High, const __FlashStringHelper *name) {
  stopAndSleep();
  if (legacyFaultActive()) {
    Serial2.println(F("LEGACY E-05 cancelled: GP6/EEP reads LOW."));
    return;
  }

  Serial2.print(name);
  Serial2.print(F(" legacy-map step: "));
  Serial2.print(stepMs);
  Serial2.println(F(" ms"));
  digitalWrite(PIN_ULT_LEGACY_SLEEP, HIGH);
  delay(5);
  digitalWrite(PIN_IN1, in1High ? HIGH : LOW);
  digitalWrite(PIN_IN2, in1High ? LOW : HIGH);
  delay(stepMs);
  stopAndSleep();
  Serial2.println(F("LEGACY E-05 stopped and asleep."));
}

void setup() {
  Serial2.setTX(PIN_UART_TX);
  Serial2.setRX(PIN_UART_RX);
  Serial2.begin(SERIAL_BAUD);
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_EEP_LEGACY_FAULT, INPUT_PULLUP);
  pinMode(PIN_ULT_LEGACY_SLEEP, OUTPUT);
  stopAndSleep();
  Serial2.println(F("LEGACY E-05 manual historical-role test ready."));
  printHelp();
}

void loop() {
  while (Serial2.available() > 0) {
    switch (static_cast<char>(Serial2.read())) {
      case 'u': case 'U': moveOneStep(LEGACY_FIRST_IN1_HIGH, F("UP/FIRST")); break;
      case 'd': case 'D': moveOneStep(LEGACY_REVERSE_IN1_HIGH, F("DOWN/REVERSE")); break;
      case '[':
        stepMs = stepMs > STEP_MIN_MS + STEP_INCREMENT_MS ?
            stepMs - STEP_INCREMENT_MS : STEP_MIN_MS;
        printHelp();
        break;
      case ']':
        stepMs = stepMs <= STEP_MAX_MS - STEP_INCREMENT_MS ?
            stepMs + STEP_INCREMENT_MS : STEP_MAX_MS;
        printHelp();
        break;
      case 'x': case 'X':
        stopAndSleep();
        Serial2.println(F("LEGACY E-05 stopped and asleep."));
        break;
      case '?': printHelp(); break;
      default: break;
    }
  }
}

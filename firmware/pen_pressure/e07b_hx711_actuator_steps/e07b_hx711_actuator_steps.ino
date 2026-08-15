/*
  E-07B: HX711 telemetry with safe N20 actuator steps

  This sketch uses an externally connected USB-to-TTL adapter for the serial
  console. It is intended for use while the toolhead runs from its normal 6 V
  supply, so the Pro Micro USB-C port MUST remain unplugged after upload.

  USB-to-TTL adapter wiring (adapter logic level set to 3.3 V):
    Adapter GND -> Pro Micro TOOL_GND
    Adapter RXD <- Pro Micro GP20 (UART1 TX)
    Adapter TXD -> Pro Micro GP21 (UART1 RX)
    Adapter VCC -> NOT CONNECTED

  Toolhead wiring:
    GP0 <- HX711 DT/DOUT                 GP4 -> DRV8833 IN1
    GP1 -> HX711 SCK                     GP5 -> DRV8833 IN2
    Pro Micro 3V3 -> HX711 VCC           GP6 <- DRV8833 EEP fault
    Pro Micro GND -> HX711 GND           GP7 -> DRV8833 ULT sleep

  Commands at 115200 baud:
    t  tare the unloaded, stationary mechanism (20 samples)
    p  print one HX711 reading now
    d  one 20 ms pen-DOWN step, then driver sleeps
    u  one 20 ms pen-UP step, then driver sleeps
    a  automatic approach: 50 ms DOWN pulses until load is detected
    [  reduce step time by 5 ms (minimum 5 ms)
    ]  increase step time by 5 ms (maximum 100 ms)
    x  stop and sleep driver immediately
    ?  print help

  Do not use continuous motor commands for E-07B. Place a digital scale under
  the pen, tare while clear of the scale, and use one short step at a time.
  Keep the first calibration below 1 N / 100 g and below the load cell's
  300 g rating.
*/

#include <Arduino.h>
#include "HX711.h"

constexpr uint8_t PIN_HX711_DT = 0;
constexpr uint8_t PIN_HX711_SCK = 1;
constexpr uint8_t PIN_IN1 = 4;
constexpr uint8_t PIN_IN2 = 5;
constexpr uint8_t PIN_EEP_FAULT = 6;
constexpr uint8_t PIN_ULT_SLEEP = 7;
constexpr uint8_t PIN_UART_TX = 20;
constexpr uint8_t PIN_UART_RX = 21;

constexpr uint32_t SERIAL_BAUD = 115200;
constexpr uint8_t TARE_SAMPLES = 20;
constexpr uint16_t STEP_MIN_MS = 5;
constexpr uint16_t STEP_MAX_MS = 100;
constexpr uint16_t STEP_INCREMENT_MS = 5;
constexpr uint16_t AUTO_APPROACH_STEP_MS = 50;
constexpr uint8_t AUTO_APPROACH_MAX_STEPS = 20;
constexpr uint8_t AUTO_APPROACH_LEARN_STEPS = 3;
// The installed load cell also sees normal lead-screw/mechanism force while
// traveling. Stop only when one pulse departs substantially from that learned
// no-contact behavior; this is roughly 10 g in the 57.2 g bench experiments.
constexpr long AUTO_CONTACT_RESIDUAL_COUNTS = 50000;
constexpr bool EEP_FAULT_ACTIVE_LOW = true;

// Verified E-05 direction mapping for the installed motor wires.
constexpr bool LIFT_IN1_HIGH = true;
constexpr bool LOWER_IN1_HIGH = false;

HX711 scale;
long tareRaw = 0;
long lastRaw = 0;
uint16_t stepMs = 20;

bool faultActive() {
  return digitalRead(PIN_EEP_FAULT) == (EEP_FAULT_ACTIVE_LOW ? LOW : HIGH);
}

void stopAndSleep() {
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
  digitalWrite(PIN_ULT_SLEEP, LOW);
}

bool readRaw(long &value) {
  if (!scale.is_ready()) return false;
  value = scale.read();
  lastRaw = value;
  return true;
}

void report() {
  long raw = lastRaw;
  const bool ready = readRaw(raw);
  Serial2.print(F("hx_ready="));
  Serial2.print(ready ? F("1") : F("0"));
  Serial2.print(F(" hx_raw="));
  Serial2.print(lastRaw);
  Serial2.print(F(" hx_tare="));
  Serial2.print(tareRaw);
  Serial2.print(F(" hx_delta="));
  Serial2.println(lastRaw - tareRaw);
}

void tare() {
  long total = 0;
  uint8_t count = 0;

  stopAndSleep();
  Serial2.println(F("Taring: leave pen clear of scale and mechanism still."));
  while (count < TARE_SAMPLES) {
    long sample = 0;
    if (readRaw(sample)) {
      total += sample;
      count++;
    }
    delay(10);
  }
  tareRaw = total / TARE_SAMPLES;
  Serial2.print(F("Tare raw="));
  Serial2.println(tareRaw);
}

void moveOneStep(bool in1High, const __FlashStringHelper *name) {
  stopAndSleep();
  if (faultActive()) {
    Serial2.println(F("EEP reports FAULT; motor command cancelled."));
    return;
  }

  Serial2.print(name);
  Serial2.print(F(" step: "));
  Serial2.print(stepMs);
  Serial2.println(F(" ms"));

  digitalWrite(PIN_ULT_SLEEP, HIGH);
  delay(5);
  digitalWrite(PIN_IN1, in1High ? HIGH : LOW);
  digitalWrite(PIN_IN2, in1High ? LOW : HIGH);
  delay(stepMs);
  stopAndSleep();
  Serial2.println(F("Motor stopped and asleep."));
}

bool readAveragedRaw(long &value) {
  long total = 0;
  uint8_t count = 0;
  const uint32_t timeoutAt = millis() + 750;

  while (count < 3 && static_cast<int32_t>(millis() - timeoutAt) < 0) {
    long sample = 0;
    if (readRaw(sample)) {
      total += sample;
      count++;
    } else {
      delay(5);
    }
  }
  if (count == 0) return false;
  value = total / count;
  lastRaw = value;
  return count == 3;
}

bool autoAbortRequested() {
  while (Serial2.available() > 0) {
    const char command = static_cast<char>(Serial2.read());
    if (command == 'x' || command == 'X') return true;
  }
  return false;
}

void automaticApproach() {
  stopAndSleep();
  if (faultActive()) {
    Serial2.println(F("EEP reports FAULT; automatic approach cancelled."));
    return;
  }

  Serial2.println(F("AUTO: three no-contact learning pulses, then 50 ms DOWN pulses."));
  Serial2.println(F("Keep at least 2 mm clearance for the learning pulses; x aborts."));
  long previousDelta = 0;
  long learnedDeltaPerStep = 0;
  for (uint8_t step = 1; step <= AUTO_APPROACH_MAX_STEPS; ++step) {
    if (autoAbortRequested()) {
      stopAndSleep();
      Serial2.println(F("AUTO aborted; motor stopped and asleep."));
      return;
    }
    if (faultActive()) {
      stopAndSleep();
      Serial2.println(F("EEP reports FAULT; AUTO cancelled."));
      return;
    }

    digitalWrite(PIN_ULT_SLEEP, HIGH);
    delay(5);
    digitalWrite(PIN_IN1, LOWER_IN1_HIGH ? HIGH : LOW);
    digitalWrite(PIN_IN2, LOWER_IN1_HIGH ? LOW : HIGH);
    delay(AUTO_APPROACH_STEP_MS);
    stopAndSleep();
    delay(150);

    long raw = lastRaw;
    if (!readAveragedRaw(raw)) {
      stopAndSleep();
      Serial2.println(F("AUTO stopped: HX711 did not provide three samples."));
      return;
    }
    const long delta = raw - tareRaw;
    const long observedStepDelta = step == 1 ? 0 : delta - previousDelta;
    Serial2.print(F("AUTO step="));
    Serial2.print(step);
    Serial2.print(F(" hx_delta="));
    Serial2.print(delta);

    if (step == 1) {
      Serial2.println(F(" (learning)"));
    } else if (step <= AUTO_APPROACH_LEARN_STEPS) {
      learnedDeltaPerStep = step == 2 ? observedStepDelta :
          (learnedDeltaPerStep + observedStepDelta) / 2;
      Serial2.print(F(" learned_step_delta="));
      Serial2.println(learnedDeltaPerStep);
    } else {
      const long residual = observedStepDelta - learnedDeltaPerStep;
      Serial2.print(F(" residual="));
      Serial2.println(residual);
      if (labs(residual) >= AUTO_CONTACT_RESIDUAL_COUNTS) {
        Serial2.println(F("AUTO contact detected; motor stopped and asleep."));
        return;
      }
    }
    previousDelta = delta;
  }
  stopAndSleep();
  Serial2.println(F("AUTO stopped: 20-pulse travel limit reached."));
}

void printHelp() {
  Serial2.println(F("E-07B: t=tare p=print d=down u=up a=auto [=shorter ]=longer x=stop ?=help"));
  Serial2.print(F("Current step duration: "));
  Serial2.print(stepMs);
  Serial2.println(F(" ms"));
}

void handleCommand(char command) {
  switch (command) {
    case 't': case 'T': tare(); break;
    case 'p': case 'P': report(); break;
    case 'd': case 'D': moveOneStep(LOWER_IN1_HIGH, F("DOWN")); break;
    case 'u': case 'U': moveOneStep(LIFT_IN1_HIGH, F("UP")); break;
    case 'a': case 'A': automaticApproach(); break;
    case '[':
      stepMs = stepMs > STEP_MIN_MS ? stepMs - STEP_INCREMENT_MS : STEP_MIN_MS;
      printHelp();
      break;
    case ']':
      stepMs = stepMs + STEP_INCREMENT_MS < STEP_MAX_MS ?
          stepMs + STEP_INCREMENT_MS : STEP_MAX_MS;
      printHelp();
      break;
    case 'x': case 'X':
      stopAndSleep();
      Serial2.println(F("Motor stopped and asleep."));
      break;
    case '?': printHelp(); break;
    default: break;
  }
}

void setup() {
  Serial2.setTX(PIN_UART_TX);
  Serial2.setRX(PIN_UART_RX);
  Serial2.begin(SERIAL_BAUD);

  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_ULT_SLEEP, OUTPUT);
  pinMode(PIN_EEP_FAULT, INPUT_PULLUP);
  stopAndSleep();

  scale.begin(PIN_HX711_DT, PIN_HX711_SCK);
  delay(500);
  Serial2.println(F("E-07B HX711 + safe actuator-step test"));
  printHelp();
  if (!scale.is_ready()) {
    Serial2.println(F("HX711 not ready: check VCC, GND, GP0, and GP1."));
  }
}

void loop() {
  while (Serial2.available() > 0) {
    handleCommand(static_cast<char>(Serial2.read()));
  }
}

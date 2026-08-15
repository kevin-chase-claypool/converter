/*
  Theta plotter toolhead prototype firmware

  Target: SparkFun Pro Micro RP2350 using the Arduino-Pico board package.

  Wiring matches docs/hardware/WIRING_TABLE.md prototype assignments:
    GP29 <- PC817 U1 M3/M5 output; external 10k pullup, opto assertion = LOW
    GP27 -> RP23CNC A_HOME input through selected switch-like interface
    GP28 <- PC817 U2 HOME_ARM output; external 10k pullup, opto assertion = LOW
    GP4  -> DRV8833 IN1
    GP5  -> DRV8833 IN2
    GP6  <- ACEIRMC DRV8833 EEP / protection-fault output
    GP7  -> ACEIRMC DRV8833 ULT / low-true nSLEEP input
    GP0  <- HX711 DT / DOUT
    GP1  -> HX711 SCK
    Qwiic SDA/SCL -> TMAG5273 SDA/SCL

  Required Arduino libraries:
    SparkFun TMAG5273 Arduino Library
    HX711 Arduino Library by Bogdan Necula / bogde

  Bench defaults are intentionally conservative. Confirm motor direction,
  load-cell polarity, and M3/M5 polarity before installing a pen.
*/

#include <Arduino.h>
#include <Wire.h>
#include "HX711.h"
#include "SparkFun_TMAG5273_Arduino_Library.h"

// ---------------- Pin assignments ----------------
static const uint8_t PIN_CMD_M3M5 = 29;    // GP29 / A3, protected digital input
static const uint8_t PIN_A_HOME_OUT = 27;  // GP27 / A1, conditioned A_HOME output
static const uint8_t PIN_HOME_ARM_IN = 28; // GP28 / A2, exposed homing-arm input
static const uint8_t PIN_DRV_IN1 = 4;      // GP4
static const uint8_t PIN_DRV_IN2 = 5;      // GP5
// These match the installed, continuity-checked harness. Do not rewire it.
static const uint8_t PIN_DRV_SLEEP = 7;    // GP7, ULT / low-true nSLEEP
static const uint8_t PIN_DRV_FAULT = 6;    // GP6, EEP / protection fault
static const uint8_t PIN_HX711_DT = 0;     // GP0
static const uint8_t PIN_HX711_SCK = 1;    // GP1

// ---------------- Configuration ----------------
// U1/U2 are common-emitter PC817 outputs: asserted opto = GPIO pulled LOW.
// E-18/F-05 must still confirm that ENA/Aux0 sink current in the intended
// M3/M5 and M64/M65 states before the controller harness is connected.
static const bool CMD_ACTIVE_HIGH_IS_M3 = false;
static const bool HOME_ARM_ACTIVE_LOW = true;
static const bool DRV_FAULT_ACTIVE_LOW = true;

// Flip these after the first motor-only bench test if direction is backward.
static const bool LIFT_USES_IN1_PWM = true;
static const bool SEEK_USES_IN1_PWM = false;

static const uint8_t PWM_STOP = 0;
static const uint8_t PWM_LIFT = 70;        // 0-255, conservative open-loop lift
static const uint8_t PWM_SEEK = 55;        // 0-255, slow downward seek
static const uint8_t PWM_HOLD_MIN = 0;
static const uint8_t PWM_HOLD_MAX = 85;

static const uint32_t SERIAL_BAUD = 115200;
static const uint32_t CONTROL_PERIOD_MS = 20;
static const uint32_t TELEMETRY_PERIOD_MS = 250;
static const uint32_t LIFT_TIME_MS = 700;
static const uint32_t SEEK_TIMEOUT_MS = 1500;
static const uint32_t COMMAND_TIMEOUT_MS = 2000;

// Raw HX711 placeholder thresholds. Use serial telemetry to tune.
static const long CONTACT_RAW_DELTA = 500;
static const long TARGET_FORCE_RAW_DELTA = 1200;
static const long HARD_FORCE_RAW_DELTA = 6000;
static const int16_t HOLD_KP_NUM = 1;
static const int16_t HOLD_KP_DEN = 60;

// ---------------- Devices ----------------
HX711 scale;
TMAG5273 tmag;
static const uint8_t TMAG_ADDR = TMAG5273_I2C_ADDRESS_INITIAL;

// ---------------- State ----------------
enum class ToolState : uint8_t {
  BOOT,
  LIFTING,
  LIFTED,
  SEEK_CONTACT,
  HOLD_FORCE,
  FAULT
};

ToolState state = ToolState::BOOT;
ToolState previousState = ToolState::BOOT;

bool tmagOnline = false;
bool hxOnline = false;
bool manualOverride = false;
bool manualEngage = false;
bool lastCommandEngage = false;

uint32_t stateStartMs = 0;
uint32_t lastControlMs = 0;
uint32_t lastTelemetryMs = 0;
uint32_t lastCommandChangeMs = 0;

long hxRaw = 0;
long hxTare = 0;
float magX = 0.0f;
float magY = 0.0f;
float magZ = 0.0f;
float magTemp = 0.0f;

// ---------------- Helpers ----------------
const char *stateName(ToolState value) {
  switch (value) {
    case ToolState::BOOT: return "BOOT";
    case ToolState::LIFTING: return "LIFTING";
    case ToolState::LIFTED: return "LIFTED";
    case ToolState::SEEK_CONTACT: return "SEEK_CONTACT";
    case ToolState::HOLD_FORCE: return "HOLD_FORCE";
    case ToolState::FAULT: return "FAULT";
  }
  return "UNKNOWN";
}

long forceDeltaRaw() {
  return hxRaw - hxTare;
}

void setState(ToolState next) {
  if (next == state) {
    return;
  }
  previousState = state;
  state = next;
  stateStartMs = millis();
  Serial.print(F("STATE "));
  Serial.print(stateName(previousState));
  Serial.print(F(" -> "));
  Serial.println(stateName(state));
}

void driverEnable(bool enable) {
  digitalWrite(PIN_DRV_SLEEP, enable ? HIGH : LOW);
}

void motorStop() {
  analogWrite(PIN_DRV_IN1, PWM_STOP);
  analogWrite(PIN_DRV_IN2, PWM_STOP);
}

void motorCoastAndSleep() {
  motorStop();
  driverEnable(false);
}

void motorDriveDirectional(bool useIn1Pwm, uint8_t pwm) {
  driverEnable(true);
  if (useIn1Pwm) {
    analogWrite(PIN_DRV_IN1, pwm);
    analogWrite(PIN_DRV_IN2, 0);
  } else {
    analogWrite(PIN_DRV_IN1, 0);
    analogWrite(PIN_DRV_IN2, pwm);
  }
}

void motorLift() {
  motorDriveDirectional(LIFT_USES_IN1_PWM, PWM_LIFT);
}

void motorSeekDown() {
  motorDriveDirectional(SEEK_USES_IN1_PWM, PWM_SEEK);
}

bool driverFaulted() {
  int raw = digitalRead(PIN_DRV_FAULT);
  return DRV_FAULT_ACTIVE_LOW ? (raw == LOW) : (raw == HIGH);
}

bool commandRequestsEngage() {
  if (manualOverride) {
    return manualEngage;
  }
  int raw = digitalRead(PIN_CMD_M3M5);
  return CMD_ACTIVE_HIGH_IS_M3 ? (raw == HIGH) : (raw == LOW);
}

bool homingArmActive() {
  int raw = digitalRead(PIN_HOME_ARM_IN);
  return HOME_ARM_ACTIVE_LOW ? (raw == LOW) : (raw == HIGH);
}

void updateAHomeOutput() {
  // Magnetic threshold and hysteresis are intentionally not guessed here.
  // Until calibrated, GP27 remains inactive even when HOME_ARM is active.
  const bool magnetDetected = false;
  digitalWrite(PIN_A_HOME_OUT, (homingArmActive() && magnetDetected) ? HIGH : LOW);
}

void readHx711() {
  if (!scale.is_ready()) {
    return;
  }
  hxOnline = true;
  hxRaw = scale.read();
}

void readTmag() {
  if (!tmagOnline) {
    return;
  }
  magX = tmag.getXData();
  magY = tmag.getYData();
  magZ = tmag.getZData();
  magTemp = tmag.getTemp();
}

void tareHx711(uint8_t samples = 10) {
  if (!scale.is_ready()) {
    Serial.println(F("HX711 not ready; tare skipped"));
    return;
  }
  long sum = 0;
  uint8_t count = 0;
  while (count < samples) {
    if (scale.is_ready()) {
      sum += scale.read();
      count++;
    }
    delay(10);
  }
  hxTare = sum / samples;
  hxRaw = hxTare;
  hxOnline = true;
  Serial.print(F("HX711 tare raw="));
  Serial.println(hxTare);
}

void printTelemetry() {
  Serial.print(F("state="));
  Serial.print(stateName(state));
  Serial.print(F(" cmd="));
  Serial.print(commandRequestsEngage() ? F("M3") : F("M5"));
  Serial.print(F(" manual="));
  Serial.print(manualOverride ? F("1") : F("0"));
  Serial.print(F(" fault="));
  Serial.print(driverFaulted() ? F("1") : F("0"));
  Serial.print(F(" hx_raw="));
  Serial.print(hxRaw);
  Serial.print(F(" hx_delta="));
  Serial.print(forceDeltaRaw());
  Serial.print(F(" hx_online="));
  Serial.print(hxOnline ? F("1") : F("0"));
  Serial.print(F(" tmag_online="));
  Serial.print(tmagOnline ? F("1") : F("0"));
  Serial.print(F(" mag_mT=["));
  Serial.print(magX, 2);
  Serial.print(F(","));
  Serial.print(magY, 2);
  Serial.print(F(","));
  Serial.print(magZ, 2);
  Serial.print(F("] tempC="));
  Serial.println(magTemp, 1);
}

void enterFault(const __FlashStringHelper *reason) {
  Serial.print(F("FAULT: "));
  Serial.println(reason);
  motorStop();
  setState(ToolState::FAULT);
}

void serviceStateMachine() {
  const uint32_t now = millis();

  readHx711();
  readTmag();

  const bool engage = commandRequestsEngage();
  if (engage != lastCommandEngage) {
    lastCommandEngage = engage;
    lastCommandChangeMs = now;
    Serial.print(F("COMMAND "));
    Serial.println(engage ? F("M3/ENGAGE") : F("M5/LIFT"));
  }

  if (state != ToolState::FAULT && driverFaulted()) {
    enterFault(F("DRV8833 fault input active"));
    return;
  }

  if (state != ToolState::FAULT && forceDeltaRaw() > HARD_FORCE_RAW_DELTA) {
    motorLift();
    enterFault(F("hard force limit exceeded"));
    return;
  }

  switch (state) {
    case ToolState::BOOT:
      motorStop();
      driverEnable(true);
      setState(ToolState::LIFTING);
      break;

    case ToolState::LIFTING:
      motorLift();
      if (now - stateStartMs >= LIFT_TIME_MS) {
        motorStop();
        setState(ToolState::LIFTED);
      }
      break;

    case ToolState::LIFTED:
      motorStop();
      if (engage) {
        if (!hxOnline && now - lastCommandChangeMs > COMMAND_TIMEOUT_MS) {
          enterFault(F("M3 requested but HX711 has no readings"));
        } else {
          setState(ToolState::SEEK_CONTACT);
        }
      }
      break;

    case ToolState::SEEK_CONTACT:
      if (!engage) {
        setState(ToolState::LIFTING);
        break;
      }
      motorSeekDown();
      if (forceDeltaRaw() >= CONTACT_RAW_DELTA) {
        motorStop();
        setState(ToolState::HOLD_FORCE);
      } else if (now - stateStartMs >= SEEK_TIMEOUT_MS) {
        motorStop();
        enterFault(F("seek timeout; no contact found"));
      }
      break;

    case ToolState::HOLD_FORCE: {
      if (!engage) {
        setState(ToolState::LIFTING);
        break;
      }

      long error = TARGET_FORCE_RAW_DELTA - forceDeltaRaw();
      int command = static_cast<int>(error / HOLD_KP_DEN * HOLD_KP_NUM);

      if (command > 0) {
        command = constrain(command, PWM_HOLD_MIN, PWM_HOLD_MAX);
        motorDriveDirectional(SEEK_USES_IN1_PWM, static_cast<uint8_t>(command));
      } else if (command < -20) {
        command = constrain(-command, PWM_HOLD_MIN, PWM_HOLD_MAX);
        motorDriveDirectional(LIFT_USES_IN1_PWM, static_cast<uint8_t>(command));
      } else {
        motorStop();
      }
      break;
    }

    case ToolState::FAULT:
      motorStop();
      if (!engage && Serial) {
        // Remain faulted until the operator sends 'c' over serial.
      }
      break;
  }
}

void printHelp() {
  Serial.println();
  Serial.println(F("Theta toolhead prototype commands:"));
  Serial.println(F("  ?  print this help"));
  Serial.println(F("  p  print telemetry now"));
  Serial.println(F("  t  tare HX711"));
  Serial.println(F("  e  manual ENGAGE/M3"));
  Serial.println(F("  l  manual LIFT/M5"));
  Serial.println(F("  a  automatic GP29 command input"));
  Serial.println(F("  u  jog lift for 250 ms"));
  Serial.println(F("  d  jog down for 250 ms"));
  Serial.println(F("  s  stop motor"));
  Serial.println(F("  c  clear FAULT to LIFTING"));
  Serial.println(F("Bench with motor mechanically unloaded until direction is verified."));
  Serial.println();
}

void serviceSerial() {
  while (Serial.available() > 0) {
    char c = static_cast<char>(Serial.read());
    switch (c) {
      case '?':
        printHelp();
        break;
      case 'p':
        printTelemetry();
        break;
      case 't':
        tareHx711();
        break;
      case 'e':
        manualOverride = true;
        manualEngage = true;
        Serial.println(F("Manual command: ENGAGE"));
        break;
      case 'l':
        manualOverride = true;
        manualEngage = false;
        Serial.println(F("Manual command: LIFT"));
        break;
      case 'a':
        manualOverride = false;
        Serial.println(F("Manual override off; using GP29 command input"));
        break;
      case 'u':
        Serial.println(F("Jog lift 250 ms"));
        motorLift();
        delay(250);
        motorStop();
        break;
      case 'd':
        Serial.println(F("Jog down 250 ms"));
        motorSeekDown();
        delay(250);
        motorStop();
        break;
      case 's':
        Serial.println(F("Motor stop"));
        motorStop();
        break;
      case 'c':
        if (state == ToolState::FAULT) {
          Serial.println(F("Clearing fault"));
          setState(ToolState::LIFTING);
        }
        break;
      default:
        break;
    }
  }
}

void setup() {
  // R3/R4 on the PC817 module supply the defined 3.3 V pullups. Using INPUT
  // avoids an internal pull-down fighting that external, isolated signal path.
  pinMode(PIN_CMD_M3M5, INPUT);
  pinMode(PIN_A_HOME_OUT, OUTPUT);
  pinMode(PIN_HOME_ARM_IN, INPUT);
  pinMode(PIN_DRV_IN1, OUTPUT);
  pinMode(PIN_DRV_IN2, OUTPUT);
  pinMode(PIN_DRV_SLEEP, OUTPUT);
  pinMode(PIN_DRV_FAULT, INPUT_PULLUP);

  digitalWrite(PIN_A_HOME_OUT, LOW);
  motorCoastAndSleep();

  Serial.begin(SERIAL_BAUD);
  delay(500);
  Serial.println();
  Serial.println(F("Theta toolhead prototype firmware"));

  Wire.begin();
  if (tmag.begin(TMAG_ADDR, Wire) == 1) {
    tmagOnline = true;
    tmag.setTemperatureEn(true);
    Serial.println(F("TMAG5273 online"));
  } else {
    tmagOnline = false;
    Serial.println(F("TMAG5273 not found; continuing without it"));
  }

  scale.begin(PIN_HX711_DT, PIN_HX711_SCK);
  if (scale.is_ready()) {
    tareHx711();
  } else {
    hxOnline = false;
    Serial.println(F("HX711 not ready; continuing until readings appear"));
  }

  lastCommandEngage = commandRequestsEngage();
  lastCommandChangeMs = millis();
  stateStartMs = millis();
  printHelp();
  setState(ToolState::LIFTING);
}

void loop() {
  const uint32_t now = millis();

  serviceSerial();

  if (now - lastControlMs >= CONTROL_PERIOD_MS) {
    lastControlMs = now;
    updateAHomeOutput();
    serviceStateMachine();
  }

  if (now - lastTelemetryMs >= TELEMETRY_PERIOD_MS) {
    lastTelemetryMs = now;
    printTelemetry();
  }
}

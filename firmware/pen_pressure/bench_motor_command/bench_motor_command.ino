/*
  Theta plotter toolhead motor and command bench sketch

  Target: SparkFun Pro Micro RP2350 using the Arduino-Pico board package.

  Purpose:
    Test only the RP23CNC M3/M5 command input and DRV8833 motor wiring.
    This sketch does not use HX711 or TMAG5273 libraries.

  Prototype wiring:
    GP29 <- RP23CNC M3/M5 spindle-enable signal after PC817C isolation
    GP4  -> DRV8833 IN1
    GP5  -> DRV8833 IN2
    GP6  <- ACEIRMC DRV8833 EEP / protection-fault output
    GP7  -> ACEIRMC DRV8833 ULT / low-true nSLEEP input

  Bench with the motor mechanically unloaded until direction is verified.
*/

#include <Arduino.h>

static const uint8_t PIN_CMD_M3M5 = 29;    // GP29 / A3, protected digital input
static const uint8_t PIN_DRV_IN1 = 4;      // GP4
static const uint8_t PIN_DRV_IN2 = 5;      // GP5
// These match the installed, continuity-checked harness. Do not rewire it.
static const uint8_t PIN_DRV_SLEEP = 7;    // GP7, ULT / low-true nSLEEP
static const uint8_t PIN_DRV_FAULT = 6;    // GP6, EEP / protection fault

static const bool CMD_ACTIVE_HIGH_IS_M3 = true;
static const bool DRV_FAULT_ACTIVE_LOW = true;

// Flip these after the first motor-only bench test if direction is backward.
static const bool LIFT_USES_IN1_PWM = true;
static const bool DOWN_USES_IN1_PWM = false;

static const uint8_t PWM_STOP = 0;
static const uint8_t PWM_LIFT = 70;
static const uint8_t PWM_DOWN = 55;
static const uint32_t SERIAL_BAUD = 115200;
static const uint32_t TELEMETRY_PERIOD_MS = 250;
static const uint32_t AUTO_PULSE_MS = 300;

enum class BenchMode : uint8_t {
  AUTO_FROM_COMMAND,
  MANUAL_LIFT,
  MANUAL_DOWN,
  MANUAL_STOP
};

BenchMode mode = BenchMode::AUTO_FROM_COMMAND;
bool lastCommandEngage = false;
uint32_t autoPulseStartMs = 0;
uint32_t lastTelemetryMs = 0;

const char *modeName(BenchMode value) {
  switch (value) {
    case BenchMode::AUTO_FROM_COMMAND: return "AUTO_FROM_COMMAND";
    case BenchMode::MANUAL_LIFT: return "MANUAL_LIFT";
    case BenchMode::MANUAL_DOWN: return "MANUAL_DOWN";
    case BenchMode::MANUAL_STOP: return "MANUAL_STOP";
  }
  return "UNKNOWN";
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

void motorDown() {
  motorDriveDirectional(DOWN_USES_IN1_PWM, PWM_DOWN);
}

bool driverFaulted() {
  int raw = digitalRead(PIN_DRV_FAULT);
  return DRV_FAULT_ACTIVE_LOW ? (raw == LOW) : (raw == HIGH);
}

bool commandRequestsEngage() {
  int raw = digitalRead(PIN_CMD_M3M5);
  return CMD_ACTIVE_HIGH_IS_M3 ? (raw == HIGH) : (raw == LOW);
}

void printTelemetry() {
  Serial.print(F("mode="));
  Serial.print(modeName(mode));
  Serial.print(F(" gp29_cmd="));
  Serial.print(commandRequestsEngage() ? F("M3/ENGAGE") : F("M5/LIFT"));
  Serial.print(F(" fault="));
  Serial.print(driverFaulted() ? F("1") : F("0"));
  Serial.print(F(" in1="));
  Serial.print(digitalRead(PIN_DRV_IN1));
  Serial.print(F(" in2="));
  Serial.print(digitalRead(PIN_DRV_IN2));
  Serial.print(F(" sleep="));
  Serial.println(digitalRead(PIN_DRV_SLEEP));
}

void printHelp() {
  Serial.println();
  Serial.println(F("Theta motor/command bench commands:"));
  Serial.println(F("  ?  print this help"));
  Serial.println(F("  p  print telemetry now"));
  Serial.println(F("  a  automatic GP29 command input"));
  Serial.println(F("  u  run lift direction"));
  Serial.println(F("  d  run down direction"));
  Serial.println(F("  s  stop motor"));
  Serial.println(F("In AUTO, a GP29 M3 transition gives a short down pulse; M5 gives a short lift pulse."));
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
      case 'a':
        mode = BenchMode::AUTO_FROM_COMMAND;
        autoPulseStartMs = millis();
        Serial.println(F("Mode: automatic GP29 input"));
        break;
      case 'u':
        mode = BenchMode::MANUAL_LIFT;
        Serial.println(F("Mode: manual lift"));
        break;
      case 'd':
        mode = BenchMode::MANUAL_DOWN;
        Serial.println(F("Mode: manual down"));
        break;
      case 's':
        mode = BenchMode::MANUAL_STOP;
        motorStop();
        Serial.println(F("Mode: manual stop"));
        break;
      default:
        break;
    }
  }
}

void serviceMotor() {
  if (driverFaulted()) {
    motorStop();
    return;
  }

  switch (mode) {
    case BenchMode::MANUAL_LIFT:
      motorLift();
      break;

    case BenchMode::MANUAL_DOWN:
      motorDown();
      break;

    case BenchMode::MANUAL_STOP:
      motorStop();
      break;

    case BenchMode::AUTO_FROM_COMMAND: {
      const bool engage = commandRequestsEngage();
      const uint32_t now = millis();
      if (engage != lastCommandEngage) {
        lastCommandEngage = engage;
        autoPulseStartMs = now;
        Serial.print(F("GP29 command changed: "));
        Serial.println(engage ? F("M3/ENGAGE") : F("M5/LIFT"));
      }

      if (now - autoPulseStartMs <= AUTO_PULSE_MS) {
        if (engage) {
          motorDown();
        } else {
          motorLift();
        }
      } else {
        motorStop();
      }
      break;
    }
  }
}

void setup() {
  pinMode(PIN_CMD_M3M5, INPUT_PULLDOWN);
  pinMode(PIN_DRV_IN1, OUTPUT);
  pinMode(PIN_DRV_IN2, OUTPUT);
  pinMode(PIN_DRV_SLEEP, OUTPUT);
  pinMode(PIN_DRV_FAULT, INPUT_PULLUP);

  motorCoastAndSleep();

  Serial.begin(SERIAL_BAUD);
  delay(500);
  Serial.println();
  Serial.println(F("Theta motor/command bench sketch"));
  lastCommandEngage = commandRequestsEngage();
  autoPulseStartMs = millis();
  printHelp();
}

void loop() {
  const uint32_t now = millis();

  serviceSerial();
  serviceMotor();

  if (now - lastTelemetryMs >= TELEMETRY_PERIOD_MS) {
    lastTelemetryMs = now;
    printTelemetry();
  }
}

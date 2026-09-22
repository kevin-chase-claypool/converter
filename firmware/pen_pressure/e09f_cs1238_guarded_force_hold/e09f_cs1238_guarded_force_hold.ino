/*
  E-09F: CS1238 guarded installed-pen force-hold test.

  Supervised bench firmware only. This is NOT the production M3/M5 controller:
  it never configures GP27 or GP29. It takes bounded 5 ms N20 corrections,
  sleeps the DRV8833 between corrections, and requires Arduino Serial Monitor
  commands over UART1 (GP20 TX / GP21 RX via a 3.3 V USB-to-TTL adapter).

  The force profile is from E-09C's cap-free precision-weight CS1238 fit:
    40 g lower band = 201551 raw delta
    50 g target     = 251938 raw delta
    60 g upper band = 302326 raw delta
    70 g hard limit = 352714 raw delta
    3 g clear band  =  15116 raw delta

  One-character Serial Monitor commands (line ending optional):
    ?  help + status       t  clear-state tare
    d  one guarded DOWN setup pulse
    a  arm one supervised automatic test
    s  seek and hold within the 40--60 g raw band for 5 s
    c  from contact, release to the 3 g band then issue one 100 ms UP air-gap pulse
       followed by a 500 ms telemetry-only sensor settle
    u  one guarded 5 ms manual UP/retract pulse; available after a fault
    r  report a 16-sample raw mean and tare delta
    x  immediately stop, sleep, disarm, and abort

  Keep the physical 6 V cutoff reachable. Start clear of the scale. This
  sketch cannot read the kitchen scale; it uses only the calibrated CS1238 raw
  values and remains a bench qualification, not authorization for drawing.
*/

#include <Arduino.h>
#include <CS123x.h>

// USB-C is flash-only while the externally powered toolhead rail is off.
// At runtime Serial2 is the existing data-only service adapter path.
#define Serial Serial2

constexpr uint8_t PIN_DT = 0;
constexpr uint8_t PIN_SCK = 1;
constexpr uint8_t PIN_LIFT_HOME = 2;
constexpr uint8_t PIN_IN1 = 4;
constexpr uint8_t PIN_IN2 = 5;
constexpr uint8_t PIN_DRV_SLEEP = 6;
constexpr uint8_t PIN_DRV_FAULT = 7;
constexpr uint8_t PIN_SERVICE_UART_TX = 20;
constexpr uint8_t PIN_SERVICE_UART_RX = 21;

constexpr uint32_t BAUD = 115200;
constexpr uint16_t TARE_SAMPLES = 64;
constexpr uint8_t READ_SAMPLES = 16;
constexpr uint16_t CORRECTION_PULSE_MS = 5;
constexpr uint16_t CLEARANCE_PULSE_MS = 100;
constexpr uint16_t CORRECTION_SETTLE_MS = 500;
constexpr uint16_t AIR_GAP_SETTLE_MS = 500;
constexpr uint32_t AUTO_TIMEOUT_MS = 30000;
constexpr uint32_t HOLD_DURATION_MS = 5000;
constexpr uint8_t AUTO_PULSE_BUDGET = 30;

constexpr long FORCE_BAND_LOW_RAW = 201551;     // 40 g
constexpr long TARGET_FORCE_RAW = 251938;       // 50 g
constexpr long FORCE_BAND_HIGH_RAW = 302326;    // 60 g
constexpr long HARD_FORCE_RAW = 352714;         // 70 g
constexpr long CLEAR_BAND_RAW = 15116;          // 3 g

constexpr bool FAULT_ACTIVE_LOW = true;
constexpr bool LIFT_HOME_ACTIVE_LOW = true;
constexpr CS123X_IntRef REFERENCE_MODE = CS123X_INT_REF_OFF;

CS123x scale(CS123X_TYPE_CS1238, PIN_DT, PIN_SCK, CS123X_CH_A,
             CS123X_GAIN_128, CS123X_RATE_640Hz, REFERENCE_MODE);

enum class TestState : uint8_t {
  IDLE, SEEK_HOLD, RELEASE_TO_CLEAR, AIR_GAP_SETTLE, COMPLETE, FAULT
};

bool configured = false;
bool tareValid = false;
bool armed = false;
int32_t tareRaw = 0;
long latestDelta = 0;
uint8_t downPulses = 0;
uint8_t upPulses = 0;
uint32_t startedMs = 0;
uint32_t lastCorrectionMs = 0;
uint32_t bandEnteredMs = 0;
TestState state = TestState::IDLE;

bool valid(int32_t raw) { return raw < CS123X_TIMEOUT_ERROR; }

bool driverFaulted() {
  return digitalRead(PIN_DRV_FAULT) == (FAULT_ACTIVE_LOW ? LOW : HIGH);
}

bool liftHomePressed() {
  return digitalRead(PIN_LIFT_HOME) == (LIFT_HOME_ACTIVE_LOW ? LOW : HIGH);
}

const __FlashStringHelper *stateName() {
  switch (state) {
    case TestState::IDLE: return F("IDLE");
    case TestState::SEEK_HOLD: return F("SEEK_HOLD");
    case TestState::RELEASE_TO_CLEAR: return F("RELEASE_TO_CLEAR");
    case TestState::AIR_GAP_SETTLE: return F("AIR_GAP_SETTLE");
    case TestState::COMPLETE: return F("COMPLETE");
    case TestState::FAULT: return F("FAULT");
  }
  return F("UNKNOWN");
}

void stopAndSleep() {
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
  digitalWrite(PIN_DRV_SLEEP, LOW);
}

bool readMean(uint8_t samples, int32_t &mean) {
  int64_t total = 0;
  for (uint8_t index = 0; index < samples; ++index) {
    const int32_t raw = scale.read();
    if (!valid(raw)) return false;
    total += raw;
  }
  mean = static_cast<int32_t>(total / samples);
  return true;
}

bool readForce(long &delta) {
  int32_t raw = 0;
  if (!readMean(READ_SAMPLES, raw)) {
    Serial.println(F("FAULT,reason=cs1238_timeout"));
    state = TestState::FAULT;
    stopAndSleep();
    return false;
  }
  delta = tareValid ? static_cast<long>(tareRaw) - raw : 0;
  latestDelta = delta;
  Serial.print(F("READING,time_us="));
  Serial.print(micros());
  Serial.print(F(",raw="));
  Serial.print(raw);
  Serial.print(F(",tare_delta="));
  Serial.print(delta);
  Serial.print(F(",tare_valid="));
  Serial.println(tareValid ? 1 : 0);
  return true;
}

void fail(const __FlashStringHelper *reason) {
  stopAndSleep();
  armed = false;
  state = TestState::FAULT;
  Serial.print(F("FAULT,reason="));
  Serial.println(reason);
}

bool drivePulse(bool down, uint16_t durationMs, const __FlashStringHelper *event) {
  stopAndSleep();
  if (driverFaulted()) {
    fail(F("drv_fault"));
    return false;
  }
  if (!down && liftHomePressed()) {
    fail(F("lift_home_pressed"));
    return false;
  }
  digitalWrite(PIN_DRV_SLEEP, HIGH);
  delay(5);
  if (driverFaulted()) {
    fail(F("drv_fault_after_enable"));
    return false;
  }
  // Bench-verified E-07B direction: IN1 HIGH lowers toward scale.
  digitalWrite(PIN_IN1, down ? HIGH : LOW);
  digitalWrite(PIN_IN2, down ? LOW : HIGH);
  delay(durationMs);
  const bool faultDuringDrive = driverFaulted();
  stopAndSleep();
  Serial.print(event);
  Serial.print(F(",direction="));
  Serial.print(down ? F("DOWN") : F("UP"));
  Serial.print(F(",ms="));
  Serial.print(durationMs);
  Serial.print(F(",fault_during_drive="));
  Serial.println(faultDuringDrive ? 1 : 0);
  if (faultDuringDrive) {
    fail(F("drv_fault_during_pulse"));
    return false;
  }
  return true;
}

void status() {
  Serial.print(F("STATUS,board=pro_micro_rp2350,mode=cs1238_guarded_force_hold,"));
  Serial.print(F("state="));
  Serial.print(stateName());
  Serial.print(F(",armed="));
  Serial.print(armed ? 1 : 0);
  Serial.print(F(",tare_valid="));
  Serial.print(tareValid ? 1 : 0);
  Serial.print(F(",latest_delta="));
  Serial.print(latestDelta);
  Serial.print(F(",down_pulses="));
  Serial.print(downPulses);
  Serial.print(F(",up_pulses="));
  Serial.print(upPulses);
  Serial.print(F(",fault="));
  Serial.print(driverFaulted() ? 1 : 0);
  Serial.print(F(",lift_home="));
  Serial.println(liftHomePressed() ? 1 : 0);
}

void help() {
  Serial.println(F("HELP,?=help,t=tare,d=down,a=arm,s=seek_hold,c=clear,u=up,r=read,x=abort"));
  Serial.println(F("HELP,force_band_raw=201551..302326,target=251938,hard=352714"));
  Serial.println(F("HELP,correction=5ms,settle=500ms,hold=5000ms,clearance=100ms"));
  status();
}

void tare() {
  stopAndSleep();
  int32_t mean = 0;
  if (!readMean(TARE_SAMPLES, mean)) {
    fail(F("tare_timeout"));
    return;
  }
  tareRaw = mean;
  tareValid = true;
  armed = false;
  state = TestState::IDLE;
  latestDelta = 0;
  Serial.print(F("TARE_MEAN_RAW,"));
  Serial.println(tareRaw);
}

void arm() {
  stopAndSleep();
  if (!configured || !tareValid || driverFaulted()) {
    Serial.println(F("ARM_REJECTED,reason=configuration_tare_or_fault"));
    return;
  }
  armed = true;
  state = TestState::IDLE;
  downPulses = 0;
  upPulses = 0;
  Serial.println(F("ARMED,max_down_pulses=30,max_up_pulses=30"));
}

void startSeekHold() {
  if (!armed || !tareValid || driverFaulted()) {
    Serial.println(F("START_REJECTED,reason=arm_tare_or_fault_required"));
    return;
  }
  state = TestState::SEEK_HOLD;
  startedMs = millis();
  lastCorrectionMs = 0;
  bandEnteredMs = 0;
  Serial.println(F("SEEK_HOLD_START,target_raw_delta=251938"));
}

void startClear() {
  if (!armed || !tareValid || driverFaulted()) {
    Serial.println(F("CLEAR_REJECTED,reason=arm_tare_or_fault_required"));
    return;
  }
  state = TestState::RELEASE_TO_CLEAR;
  startedMs = millis();
  lastCorrectionMs = 0;
  bandEnteredMs = 0;
  Serial.println(F("CLEAR_START,release_raw_delta=15116,air_gap_ms=100"));
}

void abortTest() {
  stopAndSleep();
  armed = false;
  state = TestState::IDLE;
  Serial.println(F("ABORTED,driver_asleep=1"));
}

void manualUp() {
  // Recovery operation: deliberately available after a fault so a failed
  // automatic sequence cannot leave the pen pressing on the fixture. It still
  // checks ULT and GP2, runs one 5 ms UP pulse only, then sleeps the driver.
  stopAndSleep();
  armed = false;
  state = TestState::IDLE;
  if (drivePulse(false, CORRECTION_PULSE_MS, F("MANUAL_UP"))) {
    Serial.println(F("MANUAL_UP_COMPLETE,driver_asleep=1"));
  }
}

void manualDown() {
  // Pen-install setup operation: one supervised 5 ms DOWN pulse only. It
  // deliberately does not infer contact from the CS1238 because installed
  // mechanical preload can change that signal before the tip reaches paper.
  stopAndSleep();
  armed = false;
  state = TestState::IDLE;
  if (drivePulse(true, CORRECTION_PULSE_MS, F("MANUAL_DOWN"))) {
    Serial.println(F("MANUAL_DOWN_COMPLETE,driver_asleep=1"));
  }
}

void serviceAutomaticTest() {
  if (state != TestState::SEEK_HOLD && state != TestState::RELEASE_TO_CLEAR &&
      state != TestState::AIR_GAP_SETTLE) return;
  const uint32_t now = millis();
  if (now - startedMs >= AUTO_TIMEOUT_MS) {
    fail(F("automatic_test_timeout"));
    return;
  }
  const uint16_t settleMs = state == TestState::AIR_GAP_SETTLE
                                ? AIR_GAP_SETTLE_MS
                                : CORRECTION_SETTLE_MS;
  if (now - lastCorrectionMs < settleMs) return;
  lastCorrectionMs = now;

  long delta = 0;
  if (!readForce(delta)) return;
  if (state == TestState::AIR_GAP_SETTLE) {
    // The clear band was proven before the known-duration UP pulse. This
    // delayed reading is telemetry only: a CS1238 sample taken directly after
    // motor motion is not evidence that the already-completed air gap failed.
    Serial.print(F("AIR_GAP_SETTLED,tare_delta="));
    Serial.println(delta);
    state = TestState::COMPLETE;
    Serial.println(F("CLEAR_COMPLETE,driver_asleep=1"));
    return;
  }
  if (state == TestState::SEEK_HOLD) {
    // Only downward seeking/holding can increase contact force. Confirm an
    // over-limit sample before faulting so a single CS1238 transient cannot
    // turn an otherwise safe, sleeping test into a false fault.
    if (delta > HARD_FORCE_RAW) {
      long confirmation = 0;
      if (!readForce(confirmation)) return;
      if (confirmation > HARD_FORCE_RAW) {
        fail(F("hard_force_limit"));
      } else {
        Serial.println(F("HARD_LIMIT_GLITCH_REJECTED"));
      }
      return;
    }
    if (delta < FORCE_BAND_LOW_RAW) {
      if (downPulses >= AUTO_PULSE_BUDGET) {
        fail(F("down_pulse_budget"));
        return;
      }
      if (drivePulse(true, CORRECTION_PULSE_MS, F("AUTO_PULSE"))) ++downPulses;
      return;
    }
    if (delta > FORCE_BAND_HIGH_RAW) {
      if (upPulses >= AUTO_PULSE_BUDGET) {
        fail(F("up_pulse_budget"));
        return;
      }
      if (drivePulse(false, CORRECTION_PULSE_MS, F("AUTO_PULSE"))) ++upPulses;
      return;
    }
    if (bandEnteredMs == 0) {
      bandEnteredMs = now;
      Serial.println(F("HOLD_BAND_ENTERED"));
    }
    if (now - bandEnteredMs >= HOLD_DURATION_MS) {
      stopAndSleep();
      state = TestState::COMPLETE;
      Serial.println(F("HOLD_COMPLETE,driver_asleep=1"));
    }
    return;
  }

  // RELEASE_TO_CLEAR: upward movement cannot increase pen contact force, so
  // it intentionally bypasses the downward hard-force gate above. Rise in 5
  // ms steps until clear, then issue one explicit 100 ms candidate air-gap
  // pulse and stop. GP2 is checked before each pulse.
  if (labs(delta) <= CLEAR_BAND_RAW) {
    if (!drivePulse(false, CLEARANCE_PULSE_MS, F("AIR_GAP_PULSE"))) return;
    state = TestState::AIR_GAP_SETTLE;
    lastCorrectionMs = millis();
    Serial.println(F("AIR_GAP_SETTLING,ms=500"));
    return;
  }
  if (upPulses >= AUTO_PULSE_BUDGET) {
    fail(F("clear_up_pulse_budget"));
    return;
  }
  if (drivePulse(false, CORRECTION_PULSE_MS, F("AUTO_RELEASE_PULSE"))) ++upPulses;
}

bool shortcut(char character);

void command(const char *line) {
  if (strlen(line) == 1 && shortcut(line[0])) return;
  if (!strcasecmp(line, "STATUS")) status();
  else if (!strcasecmp(line, "HELP")) help();
  else if (!strcasecmp(line, "TARE")) tare();
  else if (!strcasecmp(line, "ARM")) arm();
  else if (!strcasecmp(line, "SEEK")) startSeekHold();
  else if (!strcasecmp(line, "CLEAR")) startClear();
  else if (!strcasecmp(line, "UP")) manualUp();
  else if (!strcasecmp(line, "DOWN")) manualDown();
  else if (!strcasecmp(line, "READ")) { long delta = 0; readForce(delta); }
  else if (!strcasecmp(line, "STOP")) abortTest();
  else Serial.println(F("COMMAND_ERROR,send=? for help"));
}

bool shortcut(char character) {
  switch (tolower(static_cast<unsigned char>(character))) {
    case '?': help(); return true;
    case 't': tare(); return true;
    case 'a': arm(); return true;
    case 's': startSeekHold(); return true;
    case 'c': startClear(); return true;
    case 'u': manualUp(); return true;
    case 'd': manualDown(); return true;
    case 'r': { long delta = 0; readForce(delta); return true; }
    case 'x': abortTest(); return true;
    default: return false;
  }
}

void setup() {
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_DRV_SLEEP, OUTPUT);
  pinMode(PIN_DRV_FAULT, INPUT_PULLUP);
  pinMode(PIN_LIFT_HOME, INPUT_PULLUP);
  stopAndSleep();

  Serial2.setTX(PIN_SERVICE_UART_TX);
  Serial2.setRX(PIN_SERVICE_UART_RX);
  Serial.begin(BAUD);
  delay(300);
  configured = scale.begin() && scale.setConfig(CS123X_CH_A, CS123X_GAIN_128,
                                                  CS123X_RATE_640Hz, true);
  Serial.print(F("READY,configured="));
  Serial.println(configured ? 1 : 0);
  help();
}

void loop() {
  static char line[32];
  static uint8_t length = 0;
  while (Serial.available()) {
    const char character = static_cast<char>(Serial.read());
    if (character == '\r' || character == '\n') {
      if (length > 0) {
        line[length] = 0;
        length = 0;
        command(line);
      }
    } else if (length == 0 && Serial.available() == 0 && shortcut(character)) {
      continue;
    } else if (length + 1 < sizeof(line)) {
      line[length++] = character;
    } else {
      length = 0;
    }
  }
  serviceAutomaticTest();
}

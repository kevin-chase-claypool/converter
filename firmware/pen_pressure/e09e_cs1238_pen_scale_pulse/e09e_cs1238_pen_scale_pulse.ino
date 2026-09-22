/*
  E-09E: CS1238 installed-pen kitchen-scale pulse check.

  This is dedicated supervised bench firmware, not the production controller.
  It drives no GP29/M3/M5 or GP27 signal.  Native USB commands are intentionally
  bounded: ARM permits a limited number of individual 10 ms pulses; every
  pulse checks ULT/nFAULT and puts the DRV8833 to sleep before replying.

  Use only after E-09C known-mass calibration. Keep the physical 6 V cutoff
  reachable and begin with the pen clear of the scale. The kitchen scale is
  the reference; this firmware cannot read it and therefore cannot auto-stop
  at a selected scale force.

  Commands at 115200 native USB:
    STATUS             configuration and remaining downward-pulse budget
    TARE               64-sample clear-state diagnostic tare
    ARM                permit the next 30 individual DOWN pulses
    PULSE DOWN 10      one bounded toward-scale pulse (requires ARM)
    PULSE UP 10        one bounded away-from-scale pulse (blocked at GP2 home)
    READ               16-sample CS1238 mean and tare-relative delta
    CAPTURE <ms>       raw SAMPLE,time_us,raw records; 250..10000 ms
    STOP               sleep the driver immediately

  Known installed direction from E-07B evidence: IN1 HIGH lowers the pen
  toward the scale, IN1 LOW lifts it away. Reconfirm mechanically on the
  first guarded pulse. No command repeats and no command performs force
  control.
*/

#include <Arduino.h>
#include <CS123x.h>

constexpr uint8_t PIN_DT = 0;
constexpr uint8_t PIN_SCK = 1;
constexpr uint8_t PIN_IN1 = 4;
constexpr uint8_t PIN_IN2 = 5;
constexpr uint8_t PIN_DRV_SLEEP = 6;  // EEP / active-low nSLEEP.
constexpr uint8_t PIN_DRV_FAULT = 7;  // ULT / active-low nFAULT.
constexpr uint8_t PIN_LIFT_HOME = 2;  // Normally-open switch to TOOL_GND.

constexpr uint32_t BAUD = 115200;
constexpr uint16_t TARE_SAMPLES = 64;
constexpr uint8_t READ_SAMPLES = 16;
constexpr uint16_t PULSE_MS = 10;
constexpr uint8_t DOWN_PULSE_BUDGET = 30;
constexpr bool FAULT_ACTIVE_LOW = true;
constexpr bool LIFT_HOME_ACTIVE_LOW = true;
constexpr CS123X_IntRef REFERENCE_MODE = CS123X_INT_REF_OFF;

CS123x scale(CS123X_TYPE_CS1238, PIN_DT, PIN_SCK, CS123X_CH_A,
             CS123X_GAIN_128, CS123X_RATE_640Hz, REFERENCE_MODE);

bool configured = false;
bool tareValid = false;
int32_t tareRaw = 0;
uint8_t remainingDownPulses = 0;

bool valid(int32_t sample) { return sample < CS123X_TIMEOUT_ERROR; }

bool faultActive() {
  return digitalRead(PIN_DRV_FAULT) == (FAULT_ACTIVE_LOW ? LOW : HIGH);
}

bool liftHomePressed() {
  return digitalRead(PIN_LIFT_HOME) == (LIFT_HOME_ACTIVE_LOW ? LOW : HIGH);
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

void status() {
  Serial.print(F("STATUS,board=pro_micro_rp2350,mode=cs1238_pen_scale_pulse,"));
  Serial.print(F("channel=A,gain=128,rate_sps=640,pulse_ms="));
  Serial.print(PULSE_MS);
  Serial.print(F(",down_pulses_remaining="));
  Serial.print(remainingDownPulses);
  Serial.print(F(",tare_valid="));
  Serial.print(tareValid ? 1 : 0);
  Serial.print(F(",fault="));
  Serial.print(faultActive() ? 1 : 0);
  Serial.print(F(",lift_home="));
  Serial.println(liftHomePressed() ? 1 : 0);
}

void tare() {
  stopAndSleep();
  int32_t mean = 0;
  if (!readMean(TARE_SAMPLES, mean)) {
    Serial.println(F("TARE_FAILED,cs1238_timeout"));
    return;
  }
  tareRaw = mean;
  tareValid = true;
  remainingDownPulses = 0;
  Serial.print(F("TARE_MEAN_RAW,"));
  Serial.println(tareRaw);
}

void reportRead(const __FlashStringHelper *event) {
  int32_t mean = 0;
  if (!readMean(READ_SAMPLES, mean)) {
    Serial.print(event);
    Serial.println(F(",cs1238_timeout"));
    return;
  }
  Serial.print(event);
  Serial.print(F(",time_us="));
  Serial.print(micros());
  Serial.print(F(",raw="));
  Serial.print(mean);
  Serial.print(F(",tare_delta="));
  Serial.print(tareValid ? mean - tareRaw : 0);
  Serial.print(F(",tare_valid="));
  Serial.println(tareValid ? 1 : 0);
}

void arm() {
  stopAndSleep();
  if (!configured || !tareValid) {
    Serial.println(F("ARM_REJECTED,reason=tare_required"));
    return;
  }
  if (faultActive()) {
    Serial.println(F("ARM_REJECTED,reason=drv_fault"));
    return;
  }
  remainingDownPulses = DOWN_PULSE_BUDGET;
  Serial.print(F("ARMED,down_pulse_budget="));
  Serial.println(remainingDownPulses);
}

void pulse(bool down, uint16_t durationMs) {
  stopAndSleep();
  if (durationMs != PULSE_MS) {
    Serial.println(F("PULSE_REJECTED,reason=only_10ms_allowed"));
    return;
  }
  if (!configured || faultActive()) {
    Serial.println(F("PULSE_REJECTED,reason=drv_fault_or_adc_unconfigured"));
    return;
  }
  if (down && remainingDownPulses == 0) {
    Serial.println(F("PULSE_REJECTED,reason=arm_required"));
    return;
  }
  if (!down && liftHomePressed()) {
    Serial.println(F("PULSE_REJECTED,reason=lift_home_pressed"));
    return;
  }

  digitalWrite(PIN_DRV_SLEEP, HIGH);
  delay(5);
  if (faultActive()) {
    stopAndSleep();
    Serial.println(F("PULSE_REJECTED,reason=drv_fault_after_enable"));
    return;
  }

  // E-07B installed-direction evidence: HIGH lowers/toward scale.
  digitalWrite(PIN_IN1, down ? HIGH : LOW);
  digitalWrite(PIN_IN2, down ? LOW : HIGH);
  delay(durationMs);
  const bool faultDuringDrive = faultActive();
  stopAndSleep();
  if (down) --remainingDownPulses;

  Serial.print(F("PULSE_DONE,direction="));
  Serial.print(down ? F("DOWN") : F("UP"));
  Serial.print(F(",ms="));
  Serial.print(durationMs);
  Serial.print(F(",fault_during_drive="));
  Serial.print(faultDuringDrive ? 1 : 0);
  Serial.print(F(",down_pulses_remaining="));
  Serial.println(remainingDownPulses);
  if (faultDuringDrive) return;
  reportRead(F("PULSE_READING"));
}

void capture(uint32_t durationMs) {
  if (durationMs < 250 || durationMs > 10000) {
    Serial.println(F("CAPTURE_REJECTED,range_ms=250..10000"));
    return;
  }
  stopAndSleep();
  const uint32_t start = micros();
  uint32_t count = 0;
  Serial.print(F("CAPTURE_START,duration_ms="));
  Serial.println(durationMs);
  Serial.println(F("SAMPLES_HEADER,time_us,cs1238_raw"));
  while (static_cast<uint32_t>(micros() - start) < durationMs * 1000UL) {
    const int32_t raw = scale.read();
    if (!valid(raw)) {
      Serial.println(F("CAPTURE_STOP,reason=cs1238_timeout"));
      return;
    }
    Serial.print(F("SAMPLE,"));
    Serial.print(micros() - start);
    Serial.print(',');
    Serial.println(raw);
    ++count;
  }
  Serial.print(F("CAPTURE_STOP,reason=completed,samples="));
  Serial.println(count);
}

void command(const char *line) {
  if (!strcasecmp(line, "STATUS")) status();
  else if (!strcasecmp(line, "TARE")) tare();
  else if (!strcasecmp(line, "ARM")) arm();
  else if (!strcasecmp(line, "READ")) reportRead(F("READING"));
  else if (!strcasecmp(line, "STOP")) {
    stopAndSleep();
    remainingDownPulses = 0;
    Serial.println(F("STOPPED,driver_asleep=1"));
  } else if (!strcasecmp(line, "PULSE DOWN 10")) pulse(true, PULSE_MS);
  else if (!strcasecmp(line, "PULSE UP 10")) pulse(false, PULSE_MS);
  else if (!strncasecmp(line, "CAPTURE ", 8)) capture(strtoul(line + 8, nullptr, 10));
  else Serial.println(F("COMMAND_ERROR,expected=STATUS|TARE|ARM|PULSE DOWN 10|PULSE UP 10|READ|CAPTURE ms|STOP"));
}

void setup() {
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_DRV_SLEEP, OUTPUT);
  pinMode(PIN_DRV_FAULT, INPUT_PULLUP);
  pinMode(PIN_LIFT_HOME, INPUT_PULLUP);
  stopAndSleep();

  Serial.begin(BAUD);
  delay(300);
  configured = scale.begin() && scale.setConfig(CS123X_CH_A, CS123X_GAIN_128,
                                                  CS123X_RATE_640Hz, true);
  Serial.print(F("READY,configured="));
  Serial.println(configured ? 1 : 0);
  status();
}

void loop() {
  static char line[48];
  static uint8_t length = 0;
  while (Serial.available()) {
    const char character = static_cast<char>(Serial.read());
    if (character == '\r') continue;
    if (character == '\n') {
      line[length] = 0;
      length = 0;
      command(line);
    } else if (length + 1 < sizeof(line)) {
      line[length++] = character;
    } else {
      length = 0;
    }
  }
}

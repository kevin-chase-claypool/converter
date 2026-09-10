/*
  P100 magnetic-handshake diagnostic

  F-08/E-18 only. This sketch exercises the actual GP28 -> GP27 two-phase
  readiness/magnetic protocol used by P100, but deliberately never configures
  or writes any DRV8833, M3/M5, HX711, or LIFT_HOME pin. It is suitable for
  motorless controller/probe validation when the pen is physically clear and
  all motion is controlled by the staged F-08 procedure.

  It is not the production toolhead firmware and cannot authorize Q3/Q4 or
  normal printing. Reflash pro_micro_rp2350_toolhead before any actuator test.
*/

#include <Arduino.h>
#include <Wire.h>
#include "SparkFun_TMAG5273_Arduino_Library.h"

namespace {

constexpr uint8_t kAHomeOut = 27;
constexpr uint8_t kHomeArmIn = 28;
constexpr uint8_t kServiceUartTx = 20;
constexpr uint8_t kServiceUartRx = 21;
constexpr uint8_t kI2cSda = 16;
constexpr uint8_t kI2cScl = 17;

constexpr bool kHomeArmActiveLow = true;
constexpr uint32_t kReadyAckDelayMs = 20;
constexpr uint32_t kRearmWindowMs = 3000;
constexpr uint32_t kScanTimeoutMs = 300000;
constexpr uint32_t kSamplePeriodUs = 2000;
constexpr uint16_t kBaselineSamples = 64;
constexpr float kBaselineMaximumMt = 2.0f;
constexpr float kMagOnThresholdMt = 3.5f;
constexpr float kMagHysteresisMt = 1.0f;
constexpr uint8_t kRequiredSamples = 3;

enum class State : uint8_t { Disarmed, ReadyAck, WaitRearm, ScanActive, Fault };

TMAG5273 tmag;
State state = State::Fault;
bool tmagOnline = false;
bool baselineReady = false;
bool detected = false;
bool lastArmActive = false;
uint16_t baselineCount = 0;
double baselineSumX = 0.0;
double baselineSumY = 0.0;
double baselineSumZ = 0.0;
float baselineX = 0.0f;
float baselineY = 0.0f;
float baselineZ = 0.0f;
uint8_t onCount = 0;
uint8_t offCount = 0;
uint32_t stateStartedMs = 0;
uint32_t lastSampleUs = 0;
uint32_t lastTelemetryMs = 0;

bool armActive() {
  const int raw = digitalRead(kHomeArmIn);
  return kHomeArmActiveLow ? raw == LOW : raw == HIGH;
}

const char *stateName() {
  switch (state) {
    case State::Disarmed: return "DISARMED";
    case State::ReadyAck: return "READY_ACK";
    case State::WaitRearm: return "WAIT_REARM";
    case State::ScanActive: return "SCAN_ACTIVE";
    case State::Fault: return "FAULT";
  }
  return "UNKNOWN";
}

void setOutput(bool active) {
  digitalWrite(kAHomeOut, active ? HIGH : LOW);
}

void setState(State next) {
  state = next;
  stateStartedMs = millis();
}

void fault(const char *reason) {
  setOutput(false);
  setState(State::Fault);
  Serial2.print(F("P100 handshake FAULT: "));
  Serial2.println(reason);
}

void updateDetection(float delta) {
  const float offThreshold = kMagOnThresholdMt - kMagHysteresisMt;
  if (!detected) {
    if (delta >= kMagOnThresholdMt) {
      if (++onCount >= kRequiredSamples) {
        detected = true;
        onCount = 0;
      }
    } else {
      onCount = 0;
    }
    return;
  }
  if (delta <= offThreshold) {
    if (++offCount >= kRequiredSamples) {
      detected = false;
      offCount = 0;
    }
  } else {
    offCount = 0;
  }
}

void sampleMagnet() {
  const uint32_t nowUs = micros();
  if (nowUs - lastSampleUs < kSamplePeriodUs || !tmagOnline) {
    return;
  }
  lastSampleUs = nowUs;

  const float x = tmag.getXData();
  const float y = tmag.getYData();
  const float z = tmag.getZData();
  if (!isfinite(x) || !isfinite(y) || !isfinite(z)) {
    fault("TMAG5273 invalid sample");
    return;
  }

  if (!baselineReady && state == State::Disarmed && !armActive()) {
    const float magnitude = sqrtf(x * x + y * y + z * z);
    if (magnitude > kBaselineMaximumMt) {
      baselineCount = 0;
      baselineSumX = baselineSumY = baselineSumZ = 0.0;
      return;
    }
    baselineSumX += x;
    baselineSumY += y;
    baselineSumZ += z;
    if (++baselineCount == kBaselineSamples) {
      baselineX = static_cast<float>(baselineSumX / baselineCount);
      baselineY = static_cast<float>(baselineSumY / baselineCount);
      baselineZ = static_cast<float>(baselineSumZ / baselineCount);
      baselineReady = true;
      Serial2.println(F("P100 handshake baseline ready"));
    }
  }

  if (baselineReady) {
    const float dx = x - baselineX;
    const float dy = y - baselineY;
    const float dz = z - baselineZ;
    updateDetection(sqrtf(dx * dx + dy * dy + dz * dz));
  }
}

void emitTelemetry() {
  const uint32_t now = millis();
  if (now - lastTelemetryMs < 500) {
    return;
  }
  lastTelemetryMs = now;
  Serial2.print(F("p100_handshake state="));
  Serial2.print(stateName());
  Serial2.print(F(" baseline="));
  Serial2.print(baselineReady ? 1 : 0);
  Serial2.print(F(" detected="));
  Serial2.print(detected ? 1 : 0);
  Serial2.print(F(" arm="));
  Serial2.println(armActive() ? 1 : 0);
}

}  // namespace

void setup() {
  pinMode(kAHomeOut, OUTPUT);
  pinMode(kHomeArmIn, INPUT);
  setOutput(false);

  Serial.begin(115200);
  Serial2.setTX(kServiceUartTx);
  Serial2.setRX(kServiceUartRx);
  Serial2.begin(115200);
  Serial2.println(F("P100 handshake diagnostic: motor pins untouched"));

  Wire.setSDA(kI2cSda);
  Wire.setSCL(kI2cScl);
  Wire.begin();
  Wire.setClock(400000);
  tmagOnline = tmag.begin(TMAG5273_I2C_ADDRESS_INITIAL, Wire) == 1;
  if (!tmagOnline) {
    fault("TMAG5273 initialization failed");
    return;
  }
  tmag.setTemperatureEn(false);
  tmag.setConvAvg(TMAG5273_X8_CONVERSION);
  setState(State::Disarmed);
  lastArmActive = armActive();
}

void loop() {
  sampleMagnet();
  emitTelemetry();
  const uint32_t now = millis();
  const bool arm = armActive();
  const bool armRising = arm && !lastArmActive;
  const bool armFalling = !arm && lastArmActive;
  lastArmActive = arm;

  switch (state) {
    case State::Disarmed:
      setOutput(false);
      if (armRising) {
        if (!baselineReady) {
          fault("baseline is not ready; start away from a magnet");
        } else {
          setState(State::ReadyAck);
        }
      }
      break;
    case State::ReadyAck:
      if (armFalling) {
        setOutput(false);
        setState(State::WaitRearm);
      } else if (now - stateStartedMs >= kReadyAckDelayMs) {
        setOutput(true);
      }
      break;
    case State::WaitRearm:
      setOutput(false);
      if (now - stateStartedMs > kRearmWindowMs) {
        setState(State::Disarmed);
      } else if (armRising) {
        setState(State::ScanActive);
        setOutput(detected);
      }
      break;
    case State::ScanActive:
      setOutput(detected);
      if (armFalling) {
        setOutput(false);
        setState(State::Disarmed);
      } else if (now - stateStartedMs > kScanTimeoutMs) {
        fault("scan arm timeout");
      }
      break;
    case State::Fault:
      setOutput(false);
      if (!arm && tmagOnline) {
        baselineReady = false;
        baselineCount = 0;
        baselineSumX = baselineSumY = baselineSumZ = 0.0;
        detected = false;
        setState(State::Disarmed);
      }
      break;
  }
}

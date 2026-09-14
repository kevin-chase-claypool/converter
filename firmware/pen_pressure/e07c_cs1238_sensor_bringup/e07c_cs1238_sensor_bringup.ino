/*
  E-07C/E-08C: CS1238 motor-inert load-cell bring-up and rate/noise test

  Target: SparkFun Pro Micro RP2350, Arduino-Pico core.

  This is a SENSOR-ONLY sketch. It deliberately does not configure GP2 or
  GP4--GP7 and contains no DRV8833, N20, M3/M5, LIFT_HOME, or TMAG code.

  Safe physical precondition:
    - Toolhead 6 V actuator JST UNPLUGGED.
    - Pro Micro powered only by USB for this test.
    - Replace the HX711 with the received CS1238 only after its silkscreen,
      two-hole fit, and 3.3 V compatibility are inspected.

  Planned CS1238 channel-A wiring -- verify actual received labels first:
    Pro Micro 3V3 -> CS1238 VCC       Pro Micro GND -> CS1238 GND
    GP0 <-> CS1238 DT/DRDY-DOUT       GP1 -> CS1238 SCK
    Load cell red -> E+               black -> E-
    Load cell green -> A+             white -> A-

  Arduino Library Manager dependency: CS123x by FMazz97, version 1.1.0.
  The stock purple reference breakout uses an external TL431 reference when
  its R6 jumper is open; its actual board must be inspected before changing
  CS1238_REFERENCE_MODE below. Meter E+-to-E- with the actual load cell
  attached before trusting any readings.

  Commands at 115200 baud:
    ?  help
    p  one channel-A raw sample
    t  tare 64 settled channel-A samples
    1  select 40 SPS
    2  select 640 SPS
    3  select 1280 SPS
    w  one 60-second clear-state rate/noise window
    b  64-sample internal-short diagnostic, then restore channel A

  Do not run force/actuator traces from this sketch. E-09C requires a later
  bounded actuator sketch only after E-07C/E-08C pass.
*/

#include <Arduino.h>
#include <CS123x.h>

constexpr uint8_t PIN_CS1238_DT = 0;
constexpr uint8_t PIN_CS1238_SCK = 1;
constexpr uint32_t SERIAL_BAUD = 115200;
constexpr uint32_t WINDOW_MS = 60000;
constexpr uint8_t TARE_SAMPLES = 64;

// Set only after inspecting the received breakout. The common purple board
// with an onboard TL431 and its external-reference jumper OPEN uses OFF.
constexpr CS123X_IntRef CS1238_REFERENCE_MODE = CS123X_INT_REF_OFF;

CS123x scale(CS123X_TYPE_CS1238, PIN_CS1238_DT, PIN_CS1238_SCK,
             CS123X_CH_A, CS123X_GAIN_128, CS123X_RATE_40Hz,
             CS1238_REFERENCE_MODE);

int32_t tareRaw = 0;
bool tareValid = false;

const __FlashStringHelper *rateName(CS123X_Rate rate) {
  switch (rate) {
    case CS123X_RATE_10Hz: return F("10");
    case CS123X_RATE_40Hz: return F("40");
    case CS123X_RATE_640Hz: return F("640");
    case CS123X_RATE_1280Hz: return F("1280");
  }
  return F("unknown");
}

bool isError(int32_t value) {
  return value >= CS123X_TIMEOUT_ERROR;
}

void printHelp() {
  Serial.println(F("E-07C/E-08C CS1238 SENSOR-ONLY: ?=help p=sample t=tare 1=40SPS 2=640SPS 3=1280SPS w=60s-window b=internal-short"));
  Serial.print(F("rate_sps="));
  Serial.println(rateName(scale.getRate()));
}

void reportOne() {
  const int32_t raw = scale.read();
  if (isError(raw)) {
    Serial.println(F("CS1238 read timeout/error; check VCC/GND/DT/SCK, reference mode, and E+-E- excitation."));
    return;
  }
  Serial.print(F("cs1238_raw="));
  Serial.print(raw);
  Serial.print(F(" tare="));
  Serial.print(tareRaw);
  Serial.print(F(" delta="));
  Serial.println(raw - tareRaw);
}

void takeTare() {
  Serial.println(F("Taring: pen clear, mechanism still, and actuator JST unplugged."));
  const int32_t raw = scale.readAverage(TARE_SAMPLES);
  if (isError(raw)) {
    Serial.println(F("Tare failed: CS1238 did not provide samples."));
    return;
  }
  tareRaw = raw;
  tareValid = true;
  Serial.print(F("Tare raw="));
  Serial.println(tareRaw);
}

void selectRate(CS123X_Rate rate) {
  if (!scale.setConfig(CS123X_CH_A, CS123X_GAIN_128, rate, true)) {
    Serial.println(F("Rate change failed: configuration readback did not verify."));
    return;
  }
  tareValid = false;
  Serial.print(F("CS1238 configured rate_sps="));
  Serial.println(rateName(rate));
  Serial.println(F("Tare again before comparing deltas."));
}

void noiseWindow() {
  Serial.println(F("WINDOW: keep pen clear and mechanism still for 60 seconds."));
  const uint32_t start = millis();
  uint32_t samples = 0;
  uint32_t misses = 0;
  int32_t minimum = CS123X_MAX_VALUE;
  int32_t maximum = CS123X_MIN_VALUE;
  double mean = 0.0;
  double m2 = 0.0;

  while (millis() - start < WINDOW_MS) {
    const int32_t raw = scale.read();
    if (isError(raw)) {
      ++misses;
      continue;
    }
    ++samples;
    if (raw < minimum) minimum = raw;
    if (raw > maximum) maximum = raw;
    const double delta = static_cast<double>(raw) - mean;
    mean += delta / static_cast<double>(samples);
    m2 += delta * (static_cast<double>(raw) - mean);
  }

  const uint32_t elapsed = millis() - start;
  if (samples < 2) {
    Serial.println(F("WINDOW failed: fewer than two valid samples."));
    return;
  }
  const double variance = m2 / static_cast<double>(samples - 1);
  const double rms = sqrt(variance);
  Serial.print(F("E08C_WINDOW rate_sps="));
  Serial.print(rateName(scale.getRate()));
  Serial.print(F(" elapsed_ms="));
  Serial.print(elapsed);
  Serial.print(F(" samples="));
  Serial.print(samples);
  Serial.print(F(" actual_sps="));
  Serial.print(static_cast<double>(samples) * 1000.0 / static_cast<double>(elapsed), 2);
  Serial.print(F(" misses="));
  Serial.print(misses);
  Serial.print(F(" mean="));
  Serial.print(mean, 2);
  Serial.print(F(" rms_counts="));
  Serial.print(rms, 2);
  Serial.print(F(" min="));
  Serial.print(minimum);
  Serial.print(F(" max="));
  Serial.print(maximum);
  Serial.print(F(" p2p_counts="));
  Serial.println(maximum - minimum);
}

void internalShort() {
  const CS123X_Rate originalRate = scale.getRate();
  Serial.println(F("INTERNAL_SHORT: collecting 64 samples; this is ADC offset evidence, not load-cell calibration."));
  if (!scale.setConfig(CS123X_CH_SHORT, CS123X_GAIN_128, originalRate, true)) {
    Serial.println(F("Internal-short selection failed."));
    return;
  }
  const int32_t shortRaw = scale.readAverage(TARE_SAMPLES);
  const bool restored = scale.setConfig(CS123X_CH_A, CS123X_GAIN_128, originalRate, true);
  if (isError(shortRaw)) {
    Serial.println(F("Internal-short read failed."));
  } else {
    Serial.print(F("cs1238_internal_short_raw="));
    Serial.println(shortRaw);
  }
  if (!restored) {
    Serial.println(F("Channel-A restore failed; power-cycle before further testing."));
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(500);
  Serial.println(F("E-07C/E-08C CS1238 motor-inert bring-up"));
  Serial.println(F("Safety: 6 V actuator JST must be unplugged; this sketch has no motor commands."));
  if (!scale.begin()) {
    Serial.println(F("CS1238 begin failed: do not troubleshoot by changing motor wiring. Check sensor-board power, DT/SCK, reference mode, and bridge excitation."));
  } else {
    Serial.println(F("CS1238 configuration readback passed on channel A at 40 SPS."));
  }
  printHelp();
}

void loop() {
  while (Serial.available() > 0) {
    const char command = static_cast<char>(Serial.read());
    switch (command) {
      case '?': printHelp(); break;
      case 'p': case 'P': reportOne(); break;
      case 't': case 'T': takeTare(); break;
      case '1': selectRate(CS123X_RATE_40Hz); break;
      case '2': selectRate(CS123X_RATE_640Hz); break;
      case '3': selectRate(CS123X_RATE_1280Hz); break;
      case 'w': case 'W': noiseWindow(); break;
      case 'b': case 'B': internalShort(); break;
      case '\r': case '\n': break;
      default: Serial.println(F("Unknown command; send ?.")); break;
    }
  }
}

/*
  E-07D: Pro Micro RP2350-only CS1238 known-mass calibration.

  Hardware: Pro Micro 3V3/GND -> CS1238 VCC/GND; GP0 <- DT/DRDY; GP1 -> SCK.
  The 300 g load cell stays in its installed force path. No Pico, INA101, or
  actuator pin is configured. Keep the 6 V actuator supply disconnected.

  Native USB serial commands (115200):
    STATUS                  report configuration
    CAPTURE <milliseconds>  emit unfiltered SAMPLE,time_us,raw records
    TARE                    report a 64-sample unloaded mean (does not alter samples)
*/
#include <Arduino.h>
#include <CS123x.h>

constexpr uint8_t PIN_DT = 0, PIN_SCK = 1;
constexpr uint32_t BAUD = 115200;
constexpr uint16_t TARE_SAMPLES = 64;
constexpr CS123X_IntRef REFERENCE_MODE = CS123X_INT_REF_OFF; // Verify board before changing.

CS123x scale(CS123X_TYPE_CS1238, PIN_DT, PIN_SCK, CS123X_CH_A,
             CS123X_GAIN_128, CS123X_RATE_640Hz, REFERENCE_MODE);

bool valid(int32_t sample) { return sample < CS123X_TIMEOUT_ERROR; }

void status() {
  Serial.println(F("STATUS,board=pro_micro_rp2350,channel=A,gain=128,rate_sps=640,raw_only=1"));
}

void tare() {
  const int32_t mean = scale.readAverage(TARE_SAMPLES);
  if (!valid(mean)) { Serial.println(F("TARE_FAILED,cs1238_timeout")); return; }
  Serial.print(F("TARE_MEAN_RAW,")); Serial.println(mean);
}

void capture(uint32_t duration_ms) {
  if (duration_ms < 250 || duration_ms > 10000) {
    Serial.println(F("CAPTURE_REJECTED,range_ms=250..10000")); return;
  }
  const uint32_t start = micros();
  uint32_t count = 0;
  Serial.print(F("CAPTURE_START,duration_ms=")); Serial.println(duration_ms);
  Serial.println(F("SAMPLES_HEADER,time_us,cs1238_raw"));
  while (static_cast<uint32_t>(micros() - start) < duration_ms * 1000UL) {
    const int32_t raw = scale.read();
    if (!valid(raw)) { Serial.println(F("CAPTURE_STOP,reason=cs1238_timeout")); return; }
    Serial.print(F("SAMPLE,")); Serial.print(micros() - start); Serial.print(','); Serial.println(raw);
    ++count;
  }
  Serial.print(F("CAPTURE_STOP,reason=completed,samples=")); Serial.println(count);
}

void setup() {
  Serial.begin(BAUD); delay(300);
  if (!scale.begin() || !scale.setConfig(CS123X_CH_A, CS123X_GAIN_128, CS123X_RATE_640Hz, true)) {
    Serial.println(F("READY,configured=0")); return;
  }
  Serial.println(F("READY,configured=1,cs1238_known_mass_calibration")); status();
}

void loop() {
  static char line[40]; static uint8_t length = 0;
  while (Serial.available()) {
    const char c = static_cast<char>(Serial.read());
    if (c == '\r') continue;
    if (c == '\n') {
      line[length] = 0; length = 0;
      if (!strcasecmp(line, "STATUS")) status();
      else if (!strcasecmp(line, "TARE")) tare();
      else if (!strncasecmp(line, "CAPTURE ", 8)) capture(strtoul(line + 8, nullptr, 10));
      else Serial.println(F("COMMAND_ERROR,expected=STATUS|TARE|CAPTURE ms"));
    } else if (length + 1 < sizeof(line)) line[length++] = c;
    else length = 0;
  }
}

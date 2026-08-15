/*
  E-07: HX711 load-cell raw reading and calibration test

  Target: SparkFun Pro Micro RP2350 using the Arduino-Pico board package.

  Wiring:
    GP0 <- HX711 DT/DOUT
    GP1 -> HX711 SCK
    Pro Micro 3V3 -> HX711 VCC
    Pro Micro GND -> HX711 GND
    Load cell: red -> E+, black -> E-, green -> A+, white -> A-

  Keep the 6 V toolhead JST disconnected. USB powers this sensor-only test.
  Open Serial Monitor at 115200 baud and send:
    t  tare with the pen/load cell unloaded
    p  print the current reading immediately
    ?  print help

  Place a known mass on the pen/load cell after taring. Record the stable
  hx_delta value and whether it rises or falls. If it falls, the sign can be
  handled in later firmware; do not swap load-cell wires during E-07.
*/

#include <Arduino.h>
#include "HX711.h"

constexpr uint8_t PIN_HX711_DT = 0;
constexpr uint8_t PIN_HX711_SCK = 1;
constexpr uint32_t SERIAL_BAUD = 115200;
constexpr uint32_t REPORT_PERIOD_MS = 500;
constexpr uint8_t TARE_SAMPLES = 20;

HX711 scale;
long tareRaw = 0;
long lastRaw = 0;

bool readRaw(long &value) {
  if (!scale.is_ready()) return false;
  value = scale.read();
  lastRaw = value;
  return true;
}

void tare() {
  long total = 0;
  uint8_t count = 0;
  while (count < TARE_SAMPLES) {
    long sample = 0;
    if (readRaw(sample)) {
      total += sample;
      count++;
    }
    delay(10);
  }
  tareRaw = total / TARE_SAMPLES;
  Serial.print(F("Tare raw="));
  Serial.println(tareRaw);
}

void report() {
  long raw = lastRaw;
  const bool ready = readRaw(raw);
  Serial.print(F("hx_ready="));
  Serial.print(ready ? F("1") : F("0"));
  Serial.print(F(" hx_raw="));
  Serial.print(lastRaw);
  Serial.print(F(" hx_tare="));
  Serial.print(tareRaw);
  Serial.print(F(" hx_delta="));
  Serial.println(lastRaw - tareRaw);
}

void printHelp() {
  Serial.println(F("E-07 commands: t=tare, p=print, ?=help"));
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(500);
  scale.begin(PIN_HX711_DT, PIN_HX711_SCK);
  Serial.println(F("E-07 HX711 calibration test"));
  printHelp();
  if (!scale.is_ready()) {
    Serial.println(F("HX711 not ready: check VCC, GND, GP0, and GP1."));
  }
}

void loop() {
  static uint32_t lastReportMs = 0;
  while (Serial.available() > 0) {
    switch (static_cast<char>(Serial.read())) {
      case 't': case 'T': tare(); break;
      case 'p': case 'P': report(); break;
      case '?': printHelp(); break;
      default: break;
    }
  }

  if (millis() - lastReportMs >= REPORT_PERIOD_MS) {
    lastReportMs = millis();
    report();
  }
}

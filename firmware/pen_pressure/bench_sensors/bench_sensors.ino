/*
  Theta plotter toolhead sensor bench sketch

  Target: SparkFun Pro Micro RP2350 using the Arduino-Pico board package.

  Purpose:
    Test only the HX711 load-cell ADC and TMAG5273 Qwiic sensor.
    This sketch never drives the DRV8833 motor outputs.

  Prototype wiring:
    GP0 <- HX711 DT / DOUT
    GP1 -> HX711 SCK
    Qwiic SDA/SCL -> TMAG5273 SDA/SCL

  Required Arduino libraries:
    SparkFun TMAG5273 Arduino Library
    HX711 Arduino Library by Bogdan Necula / bogde
*/

#include <Arduino.h>
#include <Wire.h>
#include "HX711.h"
#include "SparkFun_TMAG5273_Arduino_Library.h"

static const uint8_t PIN_HX711_DT = 0;     // GP0
static const uint8_t PIN_HX711_SCK = 1;    // GP1

static const uint32_t SERIAL_BAUD = 115200;
static const uint32_t TELEMETRY_PERIOD_MS = 250;
static const uint8_t TMAG_ADDR = TMAG5273_I2C_ADDRESS_INITIAL;

HX711 scale;
TMAG5273 tmag;

bool hxOnline = false;
bool tmagOnline = false;
long hxRaw = 0;
long hxTare = 0;

long forceDeltaRaw() {
  return hxRaw - hxTare;
}

void readHx711() {
  if (!scale.is_ready()) {
    return;
  }
  hxOnline = true;
  hxRaw = scale.read();
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
  readHx711();

  Serial.print(F("hx_online="));
  Serial.print(hxOnline ? F("1") : F("0"));
  Serial.print(F(" hx_ready="));
  Serial.print(scale.is_ready() ? F("1") : F("0"));
  Serial.print(F(" hx_raw="));
  Serial.print(hxRaw);
  Serial.print(F(" hx_delta="));
  Serial.print(forceDeltaRaw());
  Serial.print(F(" tmag_online="));
  Serial.print(tmagOnline ? F("1") : F("0"));

  if (tmagOnline) {
    Serial.print(F(" mag_mT=["));
    Serial.print(tmag.getXData(), 2);
    Serial.print(F(","));
    Serial.print(tmag.getYData(), 2);
    Serial.print(F(","));
    Serial.print(tmag.getZData(), 2);
    Serial.print(F("] tempC="));
    Serial.print(tmag.getTemp(), 1);
  }

  Serial.println();
}

void printHelp() {
  Serial.println();
  Serial.println(F("Theta sensor bench commands:"));
  Serial.println(F("  ?  print this help"));
  Serial.println(F("  p  print telemetry now"));
  Serial.println(F("  t  tare HX711"));
  Serial.println(F("Move the load cell and magnet by hand and confirm signs and noise before motor tests."));
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
      default:
        break;
    }
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(500);
  Serial.println();
  Serial.println(F("Theta sensor bench sketch"));

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

  printHelp();
}

void loop() {
  static uint32_t lastTelemetryMs = 0;
  const uint32_t now = millis();

  serviceSerial();

  if (now - lastTelemetryMs >= TELEMETRY_PERIOD_MS) {
    lastTelemetryMs = now;
    printTelemetry();
  }
}

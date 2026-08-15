/*
  E-08: HX711 sample-rate and noise characterization

  Powered-toolhead serial wiring (adapter logic set to 3.3 V):
    Adapter GND -> Pro Micro TOOL_GND
    Adapter RXD <- Pro Micro GP20 (UART1 TX)
    Adapter TXD -> Pro Micro GP21 (UART1 RX)
    Adapter VCC -> NOT CONNECTED

  HX711 wiring:
    GP0 <- DT/DOUT
    GP1 -> SCK
    Pro Micro 3V3 -> VCC
    Pro Micro GND -> GND

  Commands at 115200 baud:
    r  collect a quiet 15-second stationary sample window
    ?  print help

  Upload while the local 6 V rail is off. Remove USB-C after upload, then use
  the USB-to-TTL adapter and local 6 V toolhead power. Keep the pen clear of
  the scale and mechanism stationary during each run. The motor is never driven.
*/

#include <Arduino.h>
#include "HX711.h"

constexpr uint8_t PIN_HX711_DT = 0;
constexpr uint8_t PIN_HX711_SCK = 1;
constexpr uint8_t PIN_UART_TX = 20;
constexpr uint8_t PIN_UART_RX = 21;
constexpr uint32_t SERIAL_BAUD = 115200;
constexpr uint32_t WINDOW_MS = 15000;

HX711 scale;

void printHelp() {
  Serial2.println(F("E-08: r=15-second HX711 stationary rate/noise run ?=help"));
}

void runWindow() {
  Serial2.println(F("E-08 running: keep pen clear and completely still for 15 s."));

  uint32_t count = 0;
  long minimum = 0;
  long maximum = 0;
  double mean = 0.0;
  double m2 = 0.0;
  const uint32_t startedAt = millis();

  while (millis() - startedAt < WINDOW_MS) {
    if (!scale.is_ready()) continue;

    const long raw = scale.read();
    count++;
    if (count == 1) {
      minimum = raw;
      maximum = raw;
      mean = static_cast<double>(raw);
      continue;
    }

    if (raw < minimum) minimum = raw;
    if (raw > maximum) maximum = raw;
    const double difference = static_cast<double>(raw) - mean;
    mean += difference / static_cast<double>(count);
    m2 += difference * (static_cast<double>(raw) - mean);
  }

  const double elapsedSeconds = static_cast<double>(millis() - startedAt) / 1000.0;
  const double sampleRate = elapsedSeconds > 0.0 ? count / elapsedSeconds : 0.0;
  const double standardDeviation = count > 1 ? sqrt(m2 / static_cast<double>(count - 1)) : 0.0;

  Serial2.println(F("E-08 result"));
  Serial2.print(F("samples="));
  Serial2.println(count);
  Serial2.print(F("window_s="));
  Serial2.println(elapsedSeconds, 3);
  Serial2.print(F("sample_rate_hz="));
  Serial2.println(sampleRate, 3);
  Serial2.print(F("mean_counts="));
  Serial2.println(mean, 1);
  Serial2.print(F("min_counts="));
  Serial2.println(minimum);
  Serial2.print(F("max_counts="));
  Serial2.println(maximum);
  Serial2.print(F("peak_to_peak_counts="));
  Serial2.println(maximum - minimum);
  Serial2.print(F("stddev_counts="));
  Serial2.println(standardDeviation, 1);
}

void setup() {
  Serial2.setTX(PIN_UART_TX);
  Serial2.setRX(PIN_UART_RX);
  Serial2.begin(SERIAL_BAUD);
  scale.begin(PIN_HX711_DT, PIN_HX711_SCK);
  delay(500);

  Serial2.println(F("E-08 HX711 rate/noise test"));
  printHelp();
  if (!scale.is_ready()) {
    Serial2.println(F("HX711 not ready: check 3V3, TOOL_GND, GP0, and GP1."));
  }
}

void loop() {
  while (Serial2.available() > 0) {
    const char command = static_cast<char>(Serial2.read());
    if (command == 'r' || command == 'R') runWindow();
    if (command == '?') printHelp();
  }
}

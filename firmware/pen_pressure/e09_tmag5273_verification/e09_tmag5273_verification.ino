/*
  E-09: TMAG5273 intended-wiring verification

  Powered-toolhead serial wiring (adapter logic set to 3.3 V):
    Adapter GND -> Pro Micro TOOL_GND
    Adapter RXD <- Pro Micro GP20 (UART1 TX)
    Adapter TXD -> Pro Micro GP21 (UART1 RX)
    Adapter VCC -> NOT CONNECTED

  TMAG5273 Qwiic wiring:
    Pro Micro Qwiic GPIO16 -> SDA
    Pro Micro Qwiic GPIO17 -> SCL
    Pro Micro Qwiic 3V3/GND -> TMAG5273 3V3/GND

  Commands at 115200 baud:
    i  initialize the Qwiic I2C bus and TMAG5273
    p  print one magnetic vector
    r  collect a 20-sample stationary stability window
    ?  print help

  Upload while the local 6 V rail is off. Remove USB-C after upload, then use
  the USB-to-TTL adapter and local 6 V toolhead power. The motor is never driven.
*/

#include <Arduino.h>
#include <Wire.h>
#include "SparkFun_TMAG5273_Arduino_Library.h"

constexpr uint8_t PIN_I2C_SDA = 16;
constexpr uint8_t PIN_I2C_SCL = 17;
constexpr uint8_t PIN_UART_TX = 20;
constexpr uint8_t PIN_UART_RX = 21;
constexpr uint32_t SERIAL_BAUD = 115200;
constexpr uint8_t TMAG_ADDR = TMAG5273_I2C_ADDRESS_INITIAL;
constexpr uint8_t STABILITY_SAMPLES = 20;

TMAG5273 tmag;
bool tmagOnline = false;
bool i2cInitialized = false;

struct VectorSample {
  float x;
  float y;
  float z;
  float temperature;
};

bool readVector(VectorSample &sample) {
  if (!tmagOnline) return false;
  sample.x = tmag.getXData();
  sample.y = tmag.getYData();
  sample.z = tmag.getZData();
  sample.temperature = tmag.getTemp();
  return true;
}

void initializeSensor() {
  if (i2cInitialized) {
    Serial2.println(tmagOnline ? F("TMAG5273 already online.") : F("TMAG5273 initialization already attempted."));
    return;
  }

  // UART intentionally starts before this command is allowed. If a Qwiic line
  // is shorted or held low, the user can still prove the GP20/GP21 service
  // path and identify I2C initialization as the blocking stage.
  Serial2.println(F("Initializing Qwiic I2C on SDA GPIO16 / SCL GPIO17..."));
  Wire.setSDA(PIN_I2C_SDA);
  Wire.setSCL(PIN_I2C_SCL);
  Wire.begin();
  i2cInitialized = true;

  if (tmag.begin(TMAG_ADDR, Wire) == 1) {
    tmagOnline = true;
    tmag.setTemperatureEn(true);
    Serial2.println(F("TMAG5273 online at I2C address 0x22."));
  } else {
    Serial2.println(F("TMAG5273 not found."));
  }
}

float magnitude(const VectorSample &sample) {
  return sqrt(sample.x * sample.x + sample.y * sample.y + sample.z * sample.z);
}

void printVector() {
  VectorSample sample{};
  if (!readVector(sample)) {
    Serial2.println(F("TMAG5273 offline; check Qwiic 3V3/GND, SDA GPIO16, and SCL GPIO17."));
    return;
  }
  Serial2.print(F("mag_mT=["));
  Serial2.print(sample.x, 2);
  Serial2.print(F(","));
  Serial2.print(sample.y, 2);
  Serial2.print(F(","));
  Serial2.print(sample.z, 2);
  Serial2.print(F("] magnitude_mT="));
  Serial2.print(magnitude(sample), 2);
  Serial2.print(F(" temp_C="));
  Serial2.println(sample.temperature, 1);
}

void runStabilityWindow() {
  if (!tmagOnline) {
    printVector();
    return;
  }

  Serial2.println(F("E-09 running: keep sensor and magnet position still."));
  float minMagnitude = 0.0F;
  float maxMagnitude = 0.0F;
  float totalMagnitude = 0.0F;

  for (uint8_t index = 0; index < STABILITY_SAMPLES; ++index) {
    VectorSample sample{};
    if (!readVector(sample)) {
      Serial2.println(F("TMAG5273 read failed."));
      return;
    }
    const float fieldMagnitude = magnitude(sample);
    if (index == 0 || fieldMagnitude < minMagnitude) minMagnitude = fieldMagnitude;
    if (index == 0 || fieldMagnitude > maxMagnitude) maxMagnitude = fieldMagnitude;
    totalMagnitude += fieldMagnitude;
    delay(50);
  }

  Serial2.println(F("E-09 stability result"));
  Serial2.print(F("samples="));
  Serial2.println(STABILITY_SAMPLES);
  Serial2.print(F("mean_magnitude_mT="));
  Serial2.println(totalMagnitude / STABILITY_SAMPLES, 2);
  Serial2.print(F("min_magnitude_mT="));
  Serial2.println(minMagnitude, 2);
  Serial2.print(F("max_magnitude_mT="));
  Serial2.println(maxMagnitude, 2);
  Serial2.print(F("peak_to_peak_mT="));
  Serial2.println(maxMagnitude - minMagnitude, 2);
}

void printHelp() {
  Serial2.println(F("E-09: i=initialize p=one vector r=20-sample stability ?=help"));
}

void setup() {
  Serial2.setTX(PIN_UART_TX);
  Serial2.setRX(PIN_UART_RX);
  Serial2.begin(SERIAL_BAUD);
  delay(500);

  Serial2.println(F("E-09 TMAG5273 intended-wiring test"));
  Serial2.println(F("UART ready. Send i to initialize Qwiic I2C/TMAG5273."));
  printHelp();
}

void loop() {
  while (Serial2.available() > 0) {
    const char command = static_cast<char>(Serial2.read());
    if (command == 'i' || command == 'I') initializeSensor();
    if (command == 'p' || command == 'P') printVector();
    if (command == 'r' || command == 'R') runStabilityWindow();
    if (command == '?') printHelp();
  }
}

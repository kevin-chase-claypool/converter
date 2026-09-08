/*
  T-01G LIFT_HOME UART diagnostic

  Motor-safe proof of the installed GP2 LIFT_HOME switch and the GP20/GP21
  service UART path. It does not initialize or drive the DRV8833, HX711,
  TMAG5273, PC817C, or any machine-control output.
*/

#include <Arduino.h>

constexpr uint8_t PIN_LIFT_HOME = 2;
constexpr uint8_t PIN_SERVICE_UART_TX = 20;
constexpr uint8_t PIN_SERVICE_UART_RX = 21;
constexpr uint32_t SERIAL_BAUD = 115200;

void setup() {
  pinMode(PIN_LIFT_HOME, INPUT_PULLUP);
  Serial1.setTX(PIN_SERVICE_UART_TX);
  Serial1.setRX(PIN_SERVICE_UART_RX);
  Serial1.begin(SERIAL_BAUD);
}

void loop() {
  const bool pressed = digitalRead(PIN_LIFT_HOME) == LOW;
  Serial1.print(F("T01G lift_home="));
  Serial1.println(pressed ? 1 : 0);
  delay(500);
}

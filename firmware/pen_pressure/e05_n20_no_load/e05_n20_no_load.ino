/*
  E-05: N20 unloaded CW/CCW direction test

  SparkFun Pro Micro RP2350 + ACEIRMC DRV8833 (B08RMWTDLM)

  Installed harness -- firmware mapping for this sketch:
    GP4 -> IN1
    GP5 -> IN2
    GP6 -> EEP  (low-true sleep input; HIGH enables the driver)
    GP7 <- ULT  (protection/fault output)

  This is intentionally self-running so USB is not required while the 6 V
  toolhead supply is present. After boot it waits 3 seconds, runs the first
  direction, pauses 2 seconds, runs the reverse direction, then stops/sleeps.

  USB is used only to upload this sketch. Serial Monitor remains optional if a
  data-only USB cable is available.

  Run with the pen mechanism unloaded or held safely clear. If the desired
  lift/lower direction is reversed, swap the definitions of FIRST_IN1_HIGH and
  SECOND_IN1_HIGH in code; do not swap motor wires during this test.
*/

#include <Arduino.h>

constexpr uint8_t PIN_IN1 = 4;
constexpr uint8_t PIN_IN2 = 5;
constexpr uint8_t PIN_DRV_SLEEP = 6;
constexpr uint8_t PIN_DRV_FAULT = 7;

constexpr bool DRV_FAULT_ACTIVE_LOW = true;
constexpr bool FIRST_IN1_HIGH = true;
constexpr bool SECOND_IN1_HIGH = false;
constexpr uint32_t BOOT_DELAY_MS = 3000;
constexpr uint32_t RUN_MS = 500;
constexpr uint32_t BETWEEN_DIRECTIONS_MS = 2000;

bool faultActive() {
  return digitalRead(PIN_DRV_FAULT) == (DRV_FAULT_ACTIVE_LOW ? LOW : HIGH);
}

void stopAndSleep() {
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
  digitalWrite(PIN_DRV_SLEEP, LOW);
}

void runDirection(bool in1High) {
  digitalWrite(PIN_DRV_SLEEP, HIGH); // EEP high: driver enabled
  delay(5);

  if (faultActive()) {
    Serial.println(F("ULT reports FAULT; motor command cancelled."));
    stopAndSleep();
    return;
  }

  digitalWrite(PIN_IN1, in1High ? HIGH : LOW);
  digitalWrite(PIN_IN2, in1High ? LOW : HIGH);
  delay(RUN_MS);
  stopAndSleep();
  Serial.println(F("Stopped."));
}

void printState() {
  Serial.print(F("EEP GP6 sleep="));
  Serial.print(digitalRead(PIN_DRV_SLEEP));
  Serial.print(F("; ULT GP7 fault="));
  Serial.print(digitalRead(PIN_DRV_FAULT));
  Serial.print(F("; fault="));
  Serial.println(faultActive() ? F("YES") : F("no"));
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_IN1, OUTPUT);
  pinMode(PIN_IN2, OUTPUT);
  pinMode(PIN_DRV_SLEEP, OUTPUT);
  pinMode(PIN_DRV_FAULT, INPUT_PULLUP);
  stopAndSleep();
  Serial.println(F("E-05: waiting 3 seconds, then testing both directions."));
  printState();

  delay(BOOT_DELAY_MS);
  Serial.println(F("E-05 first direction."));
  runDirection(FIRST_IN1_HIGH);
  delay(BETWEEN_DIRECTIONS_MS);
  Serial.println(F("E-05 reverse direction."));
  runDirection(SECOND_IN1_HIGH);
  stopAndSleep();
  Serial.println(F("E-05 complete: stopped and asleep."));
}

void loop() {
  // E-05 is a one-shot test. The driver remains asleep until reset/power-cycle.
}

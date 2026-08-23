#pragma once

#include <Arduino.h>

namespace toolhead_config {

// Installed pin map. Keep synchronized with docs/hardware/WIRING_TABLE.md.
constexpr uint8_t PIN_CMD_M3M5 = 29;
constexpr uint8_t PIN_A_HOME_OUT = 27;
constexpr uint8_t PIN_HOME_ARM_IN = 28;
constexpr uint8_t PIN_DRV_IN1 = 4;
constexpr uint8_t PIN_DRV_IN2 = 5;
constexpr uint8_t PIN_DRV_FAULT = 6;
constexpr uint8_t PIN_DRV_SLEEP = 7;
constexpr uint8_t PIN_HX711_DT = 0;
constexpr uint8_t PIN_HX711_SCK = 1;
constexpr uint8_t PIN_I2C_SDA = 16;
constexpr uint8_t PIN_I2C_SCL = 17;

constexpr bool CMD_ACTIVE_HIGH_IS_M3 = false;
constexpr bool HOME_ARM_ACTIVE_LOW = true;
constexpr bool DRV_FAULT_ACTIVE_LOW = true;
constexpr bool LIFT_USES_IN1_PWM = true;
constexpr bool SEEK_USES_IN1_PWM = false;

constexpr uint8_t PWM_LIFT = 70;
constexpr uint8_t PWM_SEEK = 55;
constexpr uint8_t PWM_HOLD_MAX = 85;

constexpr uint32_t SERIAL_BAUD = 115200;
constexpr uint32_t LIFT_TIME_MS = 700;
constexpr uint32_t LIFT_VERIFY_TIMEOUT_MS = 1800;
constexpr uint32_t SEEK_TIMEOUT_MS = 1500;
constexpr uint32_t HX_CORRECTION_PERIOD_MS = 250;
constexpr uint32_t TELEMETRY_PERIOD_MS = 1000;
constexpr uint32_t CORE_HEARTBEAT_PERIOD_MS = 10;
constexpr uint32_t CORE_STALE_TIMEOUT_MS = 500;
constexpr uint32_t HARDWARE_WATCHDOG_MS = 2000;

// Commissioning gates. The integrated firmware must remain motion-safe until
// the referenced hardware tests replace these placeholders with measured data.
constexpr bool ACTUATOR_DIRECTION_VALID = false;  // T-01
constexpr bool PRESSURE_CALIBRATION_VALID = false; // E-07/E-08
constexpr bool LIFT_REFERENCE_VALID = false;       // T-02
constexpr bool MAGNETIC_CALIBRATION_VALID = false; // E-18/M-08

constexpr long NO_CONTACT_RAW_REFERENCE = 0;
constexpr long LIFT_RELEASE_TOLERANCE_RAW = 500;
constexpr uint8_t LIFT_RELEASE_REQUIRED_WINDOWS = 3;

constexpr long CONTACT_RAW_DELTA = 500;
constexpr long TARGET_FORCE_RAW_DELTA = 1200;
constexpr long HARD_FORCE_RAW_DELTA = 6000;
constexpr int16_t HOLD_KP_NUM = 1;
constexpr int16_t HOLD_KP_DEN = 60;

// E-09 commissioning starting point. MAGNETIC_CALIBRATION_VALID deliberately
// remains false until installed-height scans validate these values.
constexpr float MAG_ON_THRESHOLD_MT = 3.5f;
constexpr float MAG_HYSTERESIS_MT = 1.0f;
constexpr uint8_t MAG_REQUIRED_CONSECUTIVE_SAMPLES = 3;
constexpr uint32_t MAG_SAMPLE_PERIOD_US = 2000;
constexpr uint32_t MAG_SENSOR_CHECK_PERIOD_MS = 500;
constexpr uint32_t MAG_MAX_ARM_TIME_MS = 300000;
constexpr uint32_t MAG_REARM_WINDOW_MS = 3000;
constexpr uint16_t MAG_BASELINE_SAMPLES = 64;
constexpr float MAG_BASELINE_MAX_MT = 2.0f;

} // namespace toolhead_config

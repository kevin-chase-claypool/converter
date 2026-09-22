#pragma once

#include <Arduino.h>

namespace toolhead_config {

// Installed pin map. Keep synchronized with docs/hardware/WIRING_TABLE.md.
constexpr uint8_t PIN_CMD_M3M5 = 29;
constexpr uint8_t PIN_A_HOME_OUT = 27;
constexpr uint8_t PIN_HOME_ARM_IN = 28;
constexpr uint8_t PIN_LIFT_HOME = 2;
constexpr uint8_t PIN_DRV_IN1 = 4;
constexpr uint8_t PIN_DRV_IN2 = 5;
// Confirmed installed module: EEP is nSLEEP and ULT is nFAULT.
constexpr uint8_t PIN_DRV_SLEEP = 6;
constexpr uint8_t PIN_DRV_FAULT = 7;
// CS1238 channel-A two-wire ADC interface. The physical GP0/GP1 harness is
// retained from the former HX711 path, but the ADC protocol is different.
constexpr uint8_t PIN_CS1238_DT = 0;
constexpr uint8_t PIN_CS1238_SCK = 1;
constexpr uint8_t PIN_I2C_SDA = 16;
constexpr uint8_t PIN_I2C_SCL = 17;
constexpr uint8_t PIN_SERVICE_UART_TX = 20;
constexpr uint8_t PIN_SERVICE_UART_RX = 21;

constexpr bool CMD_ACTIVE_HIGH_IS_M3 = false;
constexpr bool HOME_ARM_ACTIVE_LOW = true;
constexpr bool LIFT_HOME_ACTIVE_LOW = true;
constexpr bool DRV_FAULT_ACTIVE_LOW = true;
constexpr bool LIFT_USES_IN1_PWM = true;
constexpr bool SEEK_USES_IN1_PWM = false;

constexpr uint8_t PWM_LIFT = 70;
constexpr uint8_t PWM_SEEK = 55;
constexpr uint8_t PWM_HOLD_MAX = 85;

constexpr uint32_t SERIAL_BAUD = 115200;
// BOOT_LIFT_TIME_MS applies only to boot/fault recovery, where no preceding
// contact state is available. Normal M5 uses RELEASE_TO_CLEAR followed by the
// deliberately separate PEN_CLEAR_EXTRA_LIFT_MS air-gap pulse.
constexpr uint32_t BOOT_LIFT_TIME_MS = 700;
constexpr uint32_t LIFT_VERIFY_TIMEOUT_MS = 1800;
constexpr uint32_t PEN_CLEAR_RELEASE_TIMEOUT_MS = 1800;
// Temporary T-01H starting value requested for normal M5. Measure the actual
// resulting tip gap and replace this with an accepted per-tool value before
// PEN_CLEAR_VALID may be enabled.
constexpr uint32_t PEN_CLEAR_EXTRA_LIFT_MS = 500;
constexpr uint32_t SEEK_TIMEOUT_MS = 1500;
constexpr uint32_t CS1238_CORRECTION_PERIOD_MS = 250;
constexpr uint8_t CS1238_TARE_SAMPLES = 64;
// Candidate 25 ms moving-average window at the configured 640 SPS. E-08C
// must measure actual rate/noise before PRESSURE_CALIBRATION_VALID can be true.
constexpr uint8_t CS1238_MOVING_AVERAGE_SAMPLES = 16;
constexpr uint32_t TELEMETRY_PERIOD_MS = 1000;
constexpr uint32_t CORE_HEARTBEAT_PERIOD_MS = 10;
constexpr uint32_t CORE_STALE_TIMEOUT_MS = 500;
constexpr uint32_t HARDWARE_WATCHDOG_MS = 2000;

// Commissioning gates. The integrated firmware must remain motion-safe until
// the referenced hardware tests replace these placeholders with measured data.
constexpr bool ACTUATOR_DIRECTION_VALID = false;  // T-01
constexpr bool PRESSURE_CALIBRATION_VALID = false; // E-07C/E-08C/E-09C
constexpr bool LIFT_REFERENCE_VALID = false;       // T-02
constexpr bool MAGNETIC_CALIBRATION_VALID = false; // E-18/M-08
// Normal-print status shares GP27/U3 with the P100 magnetic protocol. Keep
// this false until F-08 proves the controller input polarity/endpoint and
// T-01H proves normal M5 clearance. It does not enable any controller wait.
constexpr bool GP27_NORMAL_STATUS_ENABLED = false;
constexpr bool PEN_CLEAR_VALID = false;             // T-01H

// These former HX711 raw-count values are intentionally reset. Populate the
// CS1238-specific values only from an accepted E-09C result and later actuator
// response evidence; the false calibration gate keeps them inactive.
constexpr long NO_CONTACT_RAW_REFERENCE = 0;
constexpr long LIFT_RELEASE_TOLERANCE_RAW = 0;
constexpr uint8_t LIFT_RELEASE_REQUIRED_WINDOWS = 3;

constexpr long CONTACT_RAW_DELTA = 0;
constexpr long TARGET_FORCE_RAW_DELTA = 0;
constexpr long HARD_FORCE_RAW_DELTA = 0;
// Set to +1 or -1 after E-09C establishes which raw direction is increasing
// downward pen force. A zero value deliberately blocks calibration enablement.
constexpr int8_t CS1238_CONTACT_FORCE_SIGN = 0;
constexpr int16_t HOLD_KP_NUM = 1;
constexpr int16_t HOLD_KP_DEN = 60;
// TBD until force calibration. These values are inactive while the above
// commissioning gates remain false.
constexpr long CONTACT_READY_TOLERANCE_RAW = 0;
constexpr uint8_t CONTACT_READY_REQUIRED_WINDOWS = 3;

static_assert(!PRESSURE_CALIBRATION_VALID ||
              (CS1238_CONTACT_FORCE_SIGN != 0 && CONTACT_RAW_DELTA > 0 &&
               TARGET_FORCE_RAW_DELTA > 0 && HARD_FORCE_RAW_DELTA > 0 &&
               CONTACT_READY_TOLERANCE_RAW > 0 && LIFT_RELEASE_TOLERANCE_RAW > 0),
              "E-09C and actuator-response values are required before enabling CS1238 force control");

// E-09 commissioning starting point. MAGNETIC_CALIBRATION_VALID deliberately
// remains false until installed-height scans validate these values.
constexpr float MAG_ON_THRESHOLD_MT = 3.5f;
constexpr float MAG_HYSTERESIS_MT = 1.0f;
constexpr uint8_t MAG_REQUIRED_CONSECUTIVE_SAMPLES = 3;
constexpr uint32_t MAG_SAMPLE_PERIOD_US = 2000;
constexpr uint32_t MAG_SENSOR_CHECK_PERIOD_MS = 500;
constexpr uint32_t MAG_MAX_ARM_TIME_MS = 300000;
constexpr uint32_t MAG_REARM_WINDOW_MS = 3000;
// Initial conservative value; F-08 must validate it against the controller
// input. Force GP27 inactive before emitting the magnetic readiness ACK so it
// is distinguishable from normal-print status.
constexpr uint32_t MAG_READY_ACK_DELAY_MS = 20;
constexpr uint16_t MAG_BASELINE_SAMPLES = 64;
constexpr float MAG_BASELINE_MAX_MT = 2.0f;

} // namespace toolhead_config

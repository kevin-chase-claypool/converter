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
// GP2 raw input is LOW when pressed; liftHomeActive() reports that semantic
// state as lift_home=1 (released reports 0).
constexpr bool LIFT_HOME_ACTIVE_LOW = true;
constexpr bool DRV_FAULT_ACTIVE_LOW = true;
// E-09E direction evidence: IN1 HIGH / IN2 LOW drives DOWN; IN1 LOW /
// IN2 HIGH drives UP. The booleans select which phase receives PWM.
constexpr bool LIFT_USES_IN1_PWM = false;
constexpr bool SEEK_USES_IN1_PWM = true;

// E-09E uses full phase drive for the validated 5–100 ms UP pulses. The
// integrated controller must overcome the installed mechanism's static
// friction before its GP2 maximum-retract guard can assert.
constexpr uint8_t PWM_LIFT = 255;
constexpr uint8_t PWM_SEEK = 55;

// The hard retract switch can preload the mechanism. After M3 first leaves
// GP2, stop and let it settle before sampling the clear-of-paper tare.
constexpr uint32_t HOME_RELEASE_TARE_SETTLE_MS = 1000;

constexpr uint32_t SERIAL_BAUD = 115200;
// Boot/fault recovery drives UP continuously and stops immediately when GP2
// reports the pressed/home state. This timeout is the independent runaway
// bound if GP2 never asserts; it is not the normal M5 air-gap duration.
constexpr uint32_t BOOT_LIFT_TIME_MS = 3000;
constexpr uint32_t LIFT_VERIFY_TIMEOUT_MS = 1800;
constexpr uint32_t PEN_CLEAR_RELEASE_TIMEOUT_MS = 1800;
// T-01H candidate: one E-09F installed-pen clear left about 1.75 mm of gap
// without approaching GP2 LIFT_HOME. It remains staged until 30 M3/M5
// clearance cycles prove repeatability before PEN_CLEAR_VALID may be enabled.
constexpr uint32_t PEN_CLEAR_EXTRA_LIFT_MS = 100;
// Supervised bench build: home to GP2 at startup, use a slow bounded seek when
// M3 begins at GP2, and retain the measured 100 ms M3/M5 pair between strokes.
// This is not the production commissioning gate.
constexpr bool MECHANICAL_PRELOAD_MODE = true; // supervised bench test build
constexpr uint32_t PEN_ENGAGE_TRAVEL_MS = 100;
constexpr uint32_t SEEK_TIMEOUT_MS = 1500;
// Use coarse pulses until the load cell first sees meaningful force, then
// switch to fine pulses before the 35 g contact threshold. The first 25 ms
// candidate reached target then transiently crossed the 60 g hard limit;
// keeping its speed only in the unloaded region avoids that final coarse step.
constexpr uint8_t HOME_SEEK_COARSE_PULSE_MS = 25;
constexpr uint8_t HOME_SEEK_FINE_PULSE_MS = 5;
constexpr uint8_t HOME_SEEK_FINE_THRESHOLD_DIVISOR = 5;
constexpr uint32_t HOME_SEEK_SETTLE_MS = 50;
constexpr uint16_t HOME_SEEK_MAX_PULSES = 100;
constexpr uint8_t HOME_SEEK_MAX_SWITCH_ACTIVE_PULSES = 30;
constexpr uint32_t HOME_SEEK_TIMEOUT_MS = 8000;
constexpr uint8_t HOME_SEEK_PWM = 255;
// First touch finds paper at a light calibrated force, then reverses enough
// to remove the first-touch preload before the fine drawing-force approach.
constexpr long HOME_SURFACE_TOUCH_RAW_DELTA = 25194; // approximately 5 g
constexpr uint8_t HOME_SURFACE_RETRACT_MS = 10;
constexpr uint8_t HOME_TUNE_PULSE_MS = 5;
constexpr uint32_t HOME_TUNE_SETTLE_MS = 50;
constexpr uint16_t HOME_TUNE_MAX_PULSES = 30;
constexpr uint32_t HOME_TUNE_TIMEOUT_MS = 3000;
// Existing post-contact force-hold cadence; home seeking has its own faster
// settle constant above and does not retune the moving-average control loop.
constexpr uint32_t CS1238_CORRECTION_PERIOD_MS = 250;
// The installed mechanism responds materially to a 5 ms full-drive pulse.
// Hold control therefore uses the same bounded pulse, never a continuous PWM
// command held for an entire correction interval.
constexpr uint8_t HOLD_CORRECTION_PULSE_MS = 5;
constexpr uint8_t HOLD_CORRECTION_PWM = 255;
constexpr uint8_t CS1238_TARE_SAMPLES = 64;
// Candidate 25 ms moving-average window at the configured 640 SPS. E-08C
// must measure actual rate/noise before PRESSURE_CALIBRATION_VALID can be true.
constexpr uint8_t CS1238_MOVING_AVERAGE_SAMPLES = 16;
constexpr uint32_t M3_FORCE_ACQUIRE_TIMEOUT_MS = 1500;
// Used only by the opt-in serial live stream; state and fault events are immediate.
constexpr uint32_t TELEMETRY_PERIOD_MS = 1000;
constexpr uint32_t CORE_HEARTBEAT_PERIOD_MS = 10;
constexpr uint32_t CORE_STALE_TIMEOUT_MS = 500;
constexpr uint32_t HARDWARE_WATCHDOG_MS = 2000;

// Commissioning gates. The integrated firmware must remain motion-safe until
// the referenced hardware tests replace these placeholders with measured data.
constexpr bool ACTUATOR_DIRECTION_VALID = true;   // E-09E direction check
constexpr bool PRESSURE_CALIBRATION_VALID = true;  // E-09C cap-free fit
constexpr bool LIFT_REFERENCE_VALID = false;       // T-02
constexpr bool MAGNETIC_CALIBRATION_VALID = false; // E-18/M-08
// Normal-print status shares GP27/U3 with the P100 magnetic protocol. Keep
// this false until F-08 proves the controller input polarity/endpoint and
// T-01H proves normal M5 clearance. It does not enable any controller wait.
constexpr bool GP27_NORMAL_STATUS_ENABLED = false;
constexpr bool PEN_CLEAR_VALID = false;             // T-01H

// 2026-09-22 E-09C cap-free repeat, converted using the explicitly chosen
// opposite upward pen-reaction assumption. The 20-point fit was
// 0.000198461271 g/raw (5,038.77 raw/g), 0.132 g RMS residual, R²=0.999978.
// This fixed zero is retained as a calibration record only; live clear checks
// use the fresh boot tare to reject drift and fixture offsets.
constexpr long NO_CONTACT_RAW_REFERENCE = 248497;
// Candidate clear band: 3 g = 15,116 raw. E-09C established ADC scale; T-01H
// must still prove normal-M5 release/air-gap behavior before its gate is true.
constexpr long LIFT_RELEASE_TOLERANCE_RAW = 15116;
constexpr uint8_t LIFT_RELEASE_REQUIRED_WINDOWS = 3;

// E-09C fit: 5,038.77 raw/g. Selected supervised bench profile:
// 35 g target = 176,357 raw; 60 g hard limit = 302,326 raw. The original
// 70 g candidate remains in the calibration record, not in this build.
// Force increases when raw decreases under the selected upward pen-reaction
// assumption, hence the negative sign.
constexpr long CONTACT_RAW_DELTA = 176357;
constexpr long TARGET_FORCE_RAW_DELTA = 176357;
constexpr long HARD_FORCE_RAW_DELTA = 302326;
constexpr int8_t CS1238_CONTACT_FORCE_SIGN = -1;
// Selected ±5 g target-ready band = 25,194 raw (approximately 30–40 g around
// the 35 g target).
constexpr long CONTACT_READY_TOLERANCE_RAW = 25194;
constexpr uint8_t CONTACT_READY_REQUIRED_WINDOWS = 3;

static_assert(HOME_SEEK_TIMEOUT_MS >
                  HOME_SEEK_MAX_PULSES *
                      (HOME_SEEK_COARSE_PULSE_MS + HOME_SEEK_SETTLE_MS),
              "Home contact-seek timeout must permit its bounded pulse sequence");

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

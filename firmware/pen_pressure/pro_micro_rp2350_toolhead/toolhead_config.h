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
// Clearance air gap. E-09F measured about 1.75 mm per 100 ms of UP drive, so
// 57 ms targets about 1 mm. The smaller gap shortens the next M3's travel and
// is folded into the warm-seek moving average; it must remain larger than
// paper/bed height variation or the pen drags during pen-up travel.
constexpr uint32_t PEN_CLEAR_EXTRA_LIFT_MS = 57;
// Normal M5 changes the mechanism's unloaded CS1238 baseline. Once the
// clearance motion has stopped, wait for the full sensing settle before
// taking the 64-sample clear-state tare. E-09F showed that a 50 ms read is
// still inside the post-drive mechanical transient.
// 2026-09-23 E-09E settle trace, three 5 ms DOWN pulses with the pen clear:
// the 16-sample filtered value reached within about +/-1,000 raw of its
// plateau at 218 / 220 / 294 ms, against a 300-692 raw tail noise floor.
// 300 ms covers that at roughly 1.5x the noise; 500 ms was a borrowed value.
constexpr uint32_t PEN_CLEAR_TARE_SETTLE_MS = 300;
// Supervised bench build: home to GP2 at startup, use a slow bounded seek when
// M3 begins at GP2, and retain the measured 100 ms M3/M5 pair between strokes.
// This is not the production commissioning gate.
constexpr bool MECHANICAL_PRELOAD_MODE = true; // supervised bench test build
constexpr uint32_t PEN_ENGAGE_TRAVEL_MS = 100;
constexpr uint32_t SEEK_TIMEOUT_MS = 1500;
// Use a bounded coarse pulse only while the pen is still clearly airborne, then
// switch to fine pulses before the 35 g contact threshold. A 25 ms pulse moved
// about 0.44 mm and the 2026-09-24 carriage-swap run reproduced the 60 g trip
// with 60.1 g two coarse pulses into a warm seek. A 10 ms pulse moves about
// 0.18 mm, so a worst-case placement lands near the 35 g target rather than
// through the 60 g limit, while still covering ~2x a fine pulse so the seek
// stays faster than fine-only.
constexpr uint8_t HOME_SEEK_COARSE_PULSE_MS = 10;
constexpr uint8_t HOME_SEEK_FINE_PULSE_MS = 5;
constexpr uint8_t HOME_SEEK_FINE_THRESHOLD_DIVISOR = 5;
// Force must be read only after the pulse has settled. E-09F's 500 ms settle
// produced repeatable 40.0 g / 40.4 g holds on this mechanism, where 50 ms
// reads were still settling transients. The 2026-09-23 E-09E settle trace
// measured the filtered value reaching +/-1,000 raw of its plateau by
// 218 / 220 / 294 ms, so 300 ms covers the measured settle.
constexpr uint32_t HOME_SEEK_SETTLE_MS = 300;
// Split settle. Pulses far below the contact threshold use this shorter wait
// because their only decision is "am I still far away", which does not need a
// fully settled reading. The full settle below still governs the contact
// decision itself.
constexpr uint32_t HOME_SEEK_SHORT_SETTLE_MS = 100;
// The full settle applies once the normalized force is within this margin of
// the contact threshold, so the final stage of the approach stays settled.
constexpr long HOME_SEEK_FULL_SETTLE_NEAR_RAW = 50388; // approximately 10 g
constexpr uint16_t HOME_SEEK_MAX_PULSES = 100;
constexpr uint8_t HOME_SEEK_MAX_SWITCH_ACTIVE_PULSES = 30;
// The settle dominates each bounded pulse. The timeout must allow the full
// coarse-plus-fine pulse sequence (100 x 325 ms worst case).
constexpr uint32_t HOME_SEEK_TIMEOUT_MS = 60000;
constexpr uint8_t HOME_SEEK_PWM = 255;
// Coarse-to-fine switch basis. The seek stays on 25 ms coarse pulses while the
// normalized force is below this divided by HOME_SEEK_FINE_THRESHOLD_DIVISOR
// (about 1 g), then switches to 5 ms fine pulses for the final approach.
constexpr long HOME_SURFACE_TOUCH_RAW_DELTA = 25194; // approximately 5 g
// Warm-seek travel learning. The first warm M3 after boot runs fine-only to
// measure the clearance distance; later warm M3s traverse most of that learned
// distance with bounded coarse pulses before the fine 5 ms approach. The 1 g
// force threshold still ends the coarse phase early if the pen reaches paper
// sooner than the learned distance.
//
// SEEK_WARM_COARSE_RATIO is the fine-pulse distance one coarse pulse covers.
// With HOME_SEEK_COARSE_PULSE_MS = 10 and the same full-drive PWM, travel is
// proportional to pulse width, so the ratio is the 10 ms / 5 ms time ratio
// (2). The old 13 came from the pre-swap stiction carriage, where a 25 ms
// pulse overcame static friction but a 5 ms pulse barely moved. Re-verify on
// the installed carriage before trusting the learned warm travel.
constexpr uint8_t SEEK_WARM_COARSE_RATIO = 2;
// Fine-pulse reserve left for the final approach after the coarse phase. With
// the ratio above (2), the coarse budget covers the learned travel minus this
// many fine pulses, so the last few pulses before contact are always the
// gentler 5 ms steps.
constexpr uint8_t SEEK_WARM_FINE_RESERVE = 4;
constexpr uint8_t SEEK_WARM_MAX_COARSE_PULSES = 8;
// The warm coarse phase also stops if force rises above this, meaning the pen
// met paper sooner than the learned distance predicted. It must sit above the
// M5 clear residual: on 2026-09-23 that residual ranged 4,340-6,516 raw and
// straddled the shared 1 g threshold, so cycles whose residual landed high
// skipped the coarse phase entirely (27 pulses instead of 13). Three grams
// clears the residual with margin while staying far below the 30 g target.
constexpr long SEEK_WARM_COARSE_FORCE_GATE_RAW = 15116; // approximately 3 g
// Existing post-contact force-hold cadence; home seeking has its own separate
// settle constant above and does not retune the moving-average control loop.
constexpr uint32_t CS1238_CORRECTION_PERIOD_MS = 250;
// Force hold ignores one-off rolling-average changes. A correction requires
// three same-direction out-of-band observations separated by one complete
// 16-sample window, then remains cadence-limited in both directions.
constexpr uint8_t HOLD_TREND_REQUIRED_WINDOWS = 3;
constexpr uint32_t HOLD_TREND_WINDOW_MS = 25;
// The installed mechanism responds materially to a 5 ms full-drive pulse.
// Hold control therefore uses the same bounded pulse, never a continuous PWM
// command held for an entire correction interval.
constexpr uint8_t HOLD_CORRECTION_PULSE_MS = 5;
constexpr uint8_t HOLD_CORRECTION_PWM = 255;
// One bounded 5 ms pulse per 325 ms cadence gives the hold loop only about
// 15 ms of drive authority per second. That is far too little when the
// mechanism releases stored energy after a long low-gain tune: on 2026-09-23 a
// cycle entered HOLD_FORCE in band, then rose 99,239 raw (about 20 g) to the
// 60 g trip. Above this much excess force, relieve with a bounded continuous
// UP move instead of waiting out the trend gate and cadence. Relief is
// retract-only, so it can only reduce force.
//
// The trigger must clear the band, and relief must stop at the band edge.
// The first form triggered exactly at the band top and retracted all the way
// to target, so every excursion beyond the band caused a full retract and the
// loop then rebuilt force with slow 5 ms pulses - a retract/rebuild limit
// cycle that reads as the pen poking and never holding. Trigger 15 g above
// target (5 g beyond the now ±10 g band top) and stop at the band top for 5 g
// of hysteresis, which still leaves 10 g before the 60 g hard limit.
constexpr long HOLD_URGENT_RELIEF_RAW = 75582; // approximately 15 g above target
constexpr uint32_t HOLD_URGENT_RELIEF_MAX_MS = 200;
// Bounded auto-recovery. A hard-limit trip (recoverable overshoot) and a
// CS1238 implausible-reading burst are each treated as recoverable: lift
// through the normal M5 clearance and re-seek rather than latching FAULT, up
// to this many consecutive recoveries without a successful contact. Exceeding
// it latches FAULT so a persistent fault cannot cycle retract/re-seek forever
// while the gantry keeps moving.
constexpr uint8_t HARD_LIMIT_RECOVERY_MAX = 3;
// How long the controller must hold the pen-up command (GP29 released) before a
// latched fault auto-clears. The controller's idle/M5 state is a deliberate
// "return to the safe lifted state" from the machine, so the toolhead can
// recover without the service console: it retracts to GP2 and hands control
// back to GP29. A persistent fault simply re-latches on the next M3, and the
// fault still drops the GP27 ready signal so the controller sees it.
constexpr uint32_t FAULT_AUTO_CLEAR_MS = 500;
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
// 2026-09-24: released so the INTEGRATED dual-core firmware can run the E-18/M-08
// verification. The magnetic interface already passed the motor-inert GP28->GP27
// handshake (E-18), F-08 PRB capture, and the 2026-09-11 P113/Q0 centroid raster
// plus A registration. Keep true only while the integrated path reproduces that
// behavior; revert if the production arm/scan faults. The remaining magnetic
// prerequisites still gate the arm at run time: TMAG online, a fresh baseline
// away from a magnet, LIFTED with the LIFT_HOME switch active, and no fault.
constexpr bool MAGNETIC_CALIBRATION_VALID = true; // E-18/M-08
// Normal-print status shares GP27/U3 with the P100 magnetic protocol. Enabled
// 2026-09-25: F-08's endpoint items are de-facto verified by the P113 runs,
// T-01H is accepted, and both ready bits (contact/clear) are available. It
// does not itself enable a controller wait; F-05A (P115 handshake) remains the
// final on-bench verification, and P115's timeout errors the program on a
// stuck signal.
constexpr bool GP27_NORMAL_STATUS_ENABLED = true;
// 2026-09-25: T-01H accepted. The 57 ms M5 clearance was measured at about
// 1.75 mm of pen-tip gap and cleared cleanly across production print runs and
// a four-cycle bench capture (contact ~40-47 g, release to ~0 g). This enables
// the clear-ready status reported to the GP27 handshake path; it does not
// itself enable the controller wait (that stays behind GP27_NORMAL_STATUS_ENABLED).
constexpr bool PEN_CLEAR_VALID = true;              // T-01H

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

// E-09C fit: 5,038.77 raw/g. Selected supervised bench profile. On 2026-09-24
// the target and contact reference were raised 5 g to keep the pen pressed
// during motion, and on 2026-09-25 they were raised another 5 g to a 45 g
// target (226,745 raw) with the hard limit at 75 g (377,908 raw). This stays
// inside the E-09C 0-90 g calibration range. Force increases when raw decreases
// under the selected upward pen-reaction assumption, hence the negative sign.
constexpr long CONTACT_RAW_DELTA = 226745;
constexpr long TARGET_FORCE_RAW_DELTA = 226745;
constexpr long HARD_FORCE_RAW_DELTA = 377908;
constexpr int8_t CS1238_CONTACT_FORCE_SIGN = -1;
// Selected ±10 g target-ready band = 50,388 raw (approximately 35–55 g around
// the 45 g target). 2026-09-23 first-print runs showed the ±5 g band was too
// tight for the mechanism's friction/noise: long strokes drifted out of band
// and triggered retract/re-approach cycles, while the wider band lets the
// hold tolerate that drift. This is a supervised bench choice, not a precision
// setting.
constexpr long CONTACT_READY_TOLERANCE_RAW = 50388;
constexpr uint8_t CONTACT_READY_REQUIRED_WINDOWS = 3;
// An accepted touch reference shifts the relative target upward, so the target
// is clamped to keep the top of the acceptance band this far below the
// absolute hard limit. On 2026-09-23 T-02 cycle 4 accepted a 78,727 raw
// (15.6 g) touch, leaving only 22,048 raw before the 60 g trip; post-hold
// creep then crossed the limit. Without the clamp the 20 g reference cap, the
// 35 g target, and the 5 g tolerance sum to exactly the 60 g hard limit, so a
// maximum-reference cycle would hold with its band top on the trip point.
constexpr long HOLD_BAND_HEADROOM_RAW = 50388; // approximately 10 g

static_assert(HARD_FORCE_RAW_DELTA >
                  CONTACT_READY_TOLERANCE_RAW + HOLD_BAND_HEADROOM_RAW,
              "Hard-force limit must leave room for the acceptance band and its headroom");

// Physical plausibility band for any single CS1238 conversion. The installed
// bridge reads roughly -1.5e5 to +3.2e5 raw across its whole force range, so a
// conversion outside this band is a communication or conversion fault.
constexpr long CS1238_SAMPLE_MIN_RAW = -500000;
constexpr long CS1238_SAMPLE_MAX_RAW = 500000;
// A conversion this far from the live tare cannot be force. Twice the
// hard-force delta is about 120 g, which leaves every real reading untouched
// while rejecting the -6,292,478 raw glitch that contaminated the 16-sample
// mean to -107,985 and tripped the hard-force guard on 2026-09-23.
constexpr long CS1238_SAMPLE_MAX_DELTA_RAW = 2 * HARD_FORCE_RAW_DELTA;
// Consecutive implausible conversions before the sensor is declared faulted.
// Isolated glitches are dropped; a persistent failure still stops the machine.
// 2026-09-23: a threshold of 3 is only ~4.7 ms of continuous garbage at 640
// SPS and still raised `CS1238 reading implausible` on a momentary bit-bang
// burst (2.9e6 / 4.2e6 raw) during an otherwise clean, in-band hold. Require
// one full 16-sample filter window (~25 ms) of continuous garbage instead. A
// genuinely dead or disconnected sensor returns the read timeout and faults
// through the CS1238-online/lost path, so this streak is only the secondary
// net for a sensor that still toggles DRDY but returns garbage.
constexpr uint8_t CS1238_IMPLAUSIBLE_FAULT_STREAK = 16;

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

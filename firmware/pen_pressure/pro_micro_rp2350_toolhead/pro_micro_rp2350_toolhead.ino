/*
  Theta plotter dual-core toolhead firmware

  Target: SparkFun Pro Micro RP2350, Arduino-Pico core.

  Core 0 owns pen-pressure safety, HX711, DRV8833, GP29 M3/M5, USB
  diagnostics, and the hardware watchdog. Core 1 owns Qwiic/TMAG5273, GP28
  HOME_ARM, and GP27 READY/magnetic output. The two control loops exchange only
  atomic status and heartbeat words.

  Production motion is deliberately commissioning-locked in toolhead_config.h.
  Do not enable a validity flag until its named bench test has passed.
*/

#include <Arduino.h>
#include <atomic>
#include <cstdio>
#include "hardware/watchdog.h"

#include "magnetic_homing.h"
#include "pressure_controller.h"
#include "toolhead_config.h"
#include "toolhead_shared.h"

using namespace toolhead_config;

// Arduino-Pico otherwise divides one 8 KB stack between the two cores.
bool core1_separate_stack = true;

std::atomic<uint32_t> g_status{0};
std::atomic<uint32_t> g_core0_heartbeat{0};
std::atomic<uint32_t> g_core1_heartbeat{0};
std::atomic<int32_t> g_mag_x_millimt{0};
std::atomic<int32_t> g_mag_y_millimt{0};
std::atomic<int32_t> g_mag_z_millimt{0};
std::atomic<int32_t> g_mag_delta_millimt{0};
std::atomic<uint32_t> g_mag_sample_count{0};
std::atomic<uint32_t> g_mag_state{static_cast<uint32_t>(MagneticState::BOOT)};

PressureController pressure;
MagneticHomingController magnetic;

uint32_t last_core0_heartbeat_ms = 0;
uint32_t last_core1_observed_ms = 0;
uint32_t last_core1_heartbeat = 0;
uint32_t last_core0_observed_ms_core1 = 0;
uint32_t last_core0_heartbeat_core1 = 0;
uint32_t last_telemetry_ms = 0;
bool watchdog_started = false;

void printHelp() {
  Serial.println(F("Theta RP2350 dual-core toolhead commands:"));
  Serial.println(F("  ?  help"));
  Serial.println(F("  p  telemetry snapshot"));
  Serial.println(F("  t  asynchronous HX711 tare"));
  Serial.println(F("  e  manual ENGAGE/M3 request"));
  Serial.println(F("  l  manual LIFT/M5 request"));
  Serial.println(F("  a  return to automatic GP29 input"));
  Serial.println(F("  c  clear pressure fault when commissioning permits"));
  Serial.println(F("Integrated motion remains locked until config validity flags are true."));
}

const char *publishedMagneticStateName() {
  switch (static_cast<MagneticState>(g_mag_state.load(std::memory_order_acquire))) {
    case MagneticState::BOOT: return "BOOT";
    case MagneticState::DISARMED: return "DISARMED";
    case MagneticState::READY_ACK: return "READY_ACK";
    case MagneticState::WAIT_REARM: return "WAIT_REARM";
    case MagneticState::SCAN_ACTIVE: return "SCAN_ACTIVE";
    case MagneticState::FAULT: return "FAULT";
  }
  return "UNKNOWN";
}

void emitTelemetry() {
  char line[420];
  const uint32_t status = g_status.load(std::memory_order_acquire);
  const int32_t mx = g_mag_x_millimt.load(std::memory_order_relaxed);
  const int32_t my = g_mag_y_millimt.load(std::memory_order_relaxed);
  const int32_t mz = g_mag_z_millimt.load(std::memory_order_relaxed);
  const int32_t md = g_mag_delta_millimt.load(std::memory_order_relaxed);
  const int length = snprintf(
      line, sizeof(line),
      "pressure=%s cmd=%s fault=%s hx_raw=%ld hx_filtered=%ld hx_delta=%ld "
      "mag=%s mT=[%ld.%03ld,%ld.%03ld,%ld.%03ld] delta=%ld.%03ld "
      "samples=%lu status=0x%08lx commission=[dir:%d pressure:%d lift:%d mag:%d]\r\n",
      pressure.stateName(), pressure.commandEngage() ? "M3" : "M5",
      pressure.faultReason(), pressure.raw(), pressure.filtered(), pressure.forceDelta(),
      publishedMagneticStateName(),
      static_cast<long>(mx / 1000), static_cast<long>(std::abs(mx % 1000)),
      static_cast<long>(my / 1000), static_cast<long>(std::abs(my % 1000)),
      static_cast<long>(mz / 1000), static_cast<long>(std::abs(mz % 1000)),
      static_cast<long>(md / 1000), static_cast<long>(std::abs(md % 1000)),
      static_cast<unsigned long>(g_mag_sample_count.load(std::memory_order_relaxed)),
      static_cast<unsigned long>(status), ACTUATOR_DIRECTION_VALID,
      PRESSURE_CALIBRATION_VALID, LIFT_REFERENCE_VALID, MAGNETIC_CALIBRATION_VALID);

  if (length > 0 && length < static_cast<int>(sizeof(line)) && Serial &&
      Serial.availableForWrite() >= length) {
    Serial.write(reinterpret_cast<const uint8_t *>(line), static_cast<size_t>(length));
  }
}

void serviceSerial() {
  while (Serial.available() > 0) {
    const char command = static_cast<char>(Serial.read());
    switch (command) {
      case '?': printHelp(); break;
      case 'p': emitTelemetry(); break;
      case 't': pressure.requestTare(); break;
      case 'e': pressure.setManualCommand(true, true); break;
      case 'l': pressure.setManualCommand(true, false); break;
      case 'a': pressure.setManualCommand(false, false); break;
      case 'c': pressure.clearFault(); break;
      default: break;
    }
  }
}

void serviceCore1Watchdog() {
  const uint32_t now = millis();
  const uint32_t heartbeat = g_core1_heartbeat.load(std::memory_order_acquire);
  if (heartbeat != last_core1_heartbeat) {
    last_core1_heartbeat = heartbeat;
    last_core1_observed_ms = now;
  }

  const bool both_ready = statusFlag(STATUS_CORE0_READY) && statusFlag(STATUS_CORE1_READY);
  const bool core1_fresh = now - last_core1_observed_ms <= CORE_STALE_TIMEOUT_MS;
  if (both_ready && !watchdog_started) {
    watchdog_enable(HARDWARE_WATCHDOG_MS, true);
    watchdog_started = true;
  }

  if (watchdog_started) {
    if (core1_fresh) {
      watchdog_update();
    } else {
      pressure.forceFault("core 1 heartbeat stale");
      // Deliberately stop feeding the hardware watchdog.
    }
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(250); // Startup-only USB enumeration; automatic control has not begun.
  Serial.println();
  Serial.println(F("Theta RP2350 dual-core toolhead firmware"));
  if (watchdog_caused_reboot()) {
    Serial.println(F("Previous reset was caused by the hardware watchdog."));
  }
  pressure.begin();
  last_core0_heartbeat_ms = millis();
  last_core1_observed_ms = millis();
  printHelp();
}

void loop() {
  const uint32_t now = millis();
  if (now - last_core0_heartbeat_ms >= CORE_HEARTBEAT_PERIOD_MS) {
    last_core0_heartbeat_ms = now;
    g_core0_heartbeat.fetch_add(1, std::memory_order_release);
  }

  pressure.service();
  serviceSerial();
  serviceCore1Watchdog();

  if (now - last_telemetry_ms >= TELEMETRY_PERIOD_MS) {
    last_telemetry_ms = now;
    emitTelemetry();
  }
  tight_loop_contents();
}

void setup1() {
  magnetic.begin();
  last_core0_heartbeat_core1 = g_core0_heartbeat.load(std::memory_order_acquire);
  last_core0_observed_ms_core1 = millis();
}

void loop1() {
  static uint32_t last_heartbeat_ms = 0;
  const uint32_t now = millis();
  if (now - last_heartbeat_ms >= CORE_HEARTBEAT_PERIOD_MS) {
    last_heartbeat_ms = now;
    g_core1_heartbeat.fetch_add(1, std::memory_order_release);
  }

  const uint32_t core0_heartbeat = g_core0_heartbeat.load(std::memory_order_acquire);
  if (core0_heartbeat != last_core0_heartbeat_core1) {
    last_core0_heartbeat_core1 = core0_heartbeat;
    last_core0_observed_ms_core1 = now;
  }
  if (now - last_core0_observed_ms_core1 > CORE_STALE_TIMEOUT_MS) {
    setStatusFlag(STATUS_SAFE_FOR_HOMING, false);
  }

  magnetic.service();
  tight_loop_contents();
}

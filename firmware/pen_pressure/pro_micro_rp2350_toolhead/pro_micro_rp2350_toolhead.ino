/*
  Theta plotter dual-core toolhead firmware

  Target: SparkFun Pro Micro RP2350, Arduino-Pico core.

  Core 0 owns pen-pressure safety, CS1238, DRV8833, GP29 M3/M5, USB
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
bool telemetry_stream_enabled = false;
bool pressure_state_reported = false;
PressureState last_reported_pressure_state = PressureState::BOOT;

void printConsoleLine(const char *line) {
  if (Serial) {
    Serial.println(line);
  }
  Serial2.println(line);
}

void printHelp() {
  printConsoleLine("Toolhead commands: ? help | p one status snapshot | v toggle 1 s live stream");
  printConsoleLine("t tare | e engage/M3 | l lift/M5 | a automatic GP29 | c clear fault");
  printConsoleLine("Default output is quiet except startup, state changes, and one fault record.");
  printConsoleLine("FAULT stops/disables the motor; inspect the cause before sending c.");
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

void emitTelemetry(const char *event) {
  char line[512];
  const uint32_t status = g_status.load(std::memory_order_acquire);
  const int32_t mx = g_mag_x_millimt.load(std::memory_order_relaxed);
  const int32_t my = g_mag_y_millimt.load(std::memory_order_relaxed);
  const int32_t mz = g_mag_z_millimt.load(std::memory_order_relaxed);
  const int32_t md = g_mag_delta_millimt.load(std::memory_order_relaxed);
  const int length = snprintf(
      line, sizeof(line),
      "event=%s pressure=%s cmd=%s fault=%s "
      "cs1238_raw=%ld cs1238_filtered=%ld cs1238_tare=%ld tare_valid=%d "
      "cs1238_delta=%ld force_norm_raw=%ld hard_limit_raw=%ld "
      "lift_home=%d home_seek_pulses=%u/%u home_tune_pulses=%u/%u "
      "mag=%s mT=[%ld.%03ld,%ld.%03ld,%ld.%03ld] delta=%ld.%03ld "
      "mag_samples=%lu status=0x%08lx ready=[contact:%d clear:%d gp27:%d] "
      "commission=[dir:%d pressure:%d lift:%d mag:%d]\r\n",
      event, pressure.stateName(), pressure.commandEngage() ? "M3" : "M5",
      pressure.faultReason(), pressure.raw(), pressure.filtered(), pressure.tare(),
      pressure.tareValid(), pressure.forceDelta(), pressure.normalizedForceDelta(),
      static_cast<long>(HARD_FORCE_RAW_DELTA),
      pressure.liftHomeActive(), pressure.homeSeekPulseCount(),
      static_cast<unsigned int>(HOME_SEEK_MAX_PULSES),
      pressure.homeTunePulseCount(),
      static_cast<unsigned int>(HOME_TUNE_MAX_PULSES),
      publishedMagneticStateName(),
      static_cast<long>(mx / 1000), static_cast<long>(std::abs(mx % 1000)),
      static_cast<long>(my / 1000), static_cast<long>(std::abs(my % 1000)),
      static_cast<long>(mz / 1000), static_cast<long>(std::abs(mz % 1000)),
      static_cast<long>(md / 1000), static_cast<long>(std::abs(md % 1000)),
      static_cast<unsigned long>(g_mag_sample_count.load(std::memory_order_relaxed)),
      static_cast<unsigned long>(status),
      statusFlag(STATUS_CONTACT_READY), statusFlag(STATUS_CLEAR_READY),
      GP27_NORMAL_STATUS_ENABLED,
      ACTUATOR_DIRECTION_VALID,
      PRESSURE_CALIBRATION_VALID, LIFT_REFERENCE_VALID, MAGNETIC_CALIBRATION_VALID);

  if (length > 0 && length < static_cast<int>(sizeof(line)) && Serial &&
      Serial.availableForWrite() >= length) {
    Serial.write(reinterpret_cast<const uint8_t *>(line), static_cast<size_t>(length));
  }
  // UART's transmit FIFO can be smaller than this complete telemetry record.
  // Do not require the whole record to fit before starting the write: that
  // condition permanently suppressed service-UART telemetry on GP20/GP21.
  // This is used for one-shot snapshots, rare state/fault events, and the
  // optional one-second stream; do not add periodic output to the default path.
  if (length > 0 && length < static_cast<int>(sizeof(line))) {
    Serial2.write(reinterpret_cast<const uint8_t *>(line), static_cast<size_t>(length));
  }
}

void reportPressureStateChange() {
  const PressureState current = pressure.state();
  if (pressure_state_reported && current == last_reported_pressure_state) {
    return;
  }
  last_reported_pressure_state = current;
  pressure_state_reported = true;
  if (current == PressureState::FAULT) {
    emitTelemetry("FAULT_EVENT");
    return;
  }

  char line[128];
  snprintf(line, sizeof(line),
           "STATE_EVENT pressure=%s cmd=%s lift_home=%d tare_valid=%d force_norm_raw=%ld",
           pressure.stateName(), pressure.commandEngage() ? "M3" : "M5",
           pressure.liftHomeActive(), pressure.tareValid(),
           pressure.normalizedForceDelta());
  printConsoleLine(line);
}

void toggleTelemetryStream() {
  telemetry_stream_enabled = !telemetry_stream_enabled;
  last_telemetry_ms = millis();
  emitTelemetry(telemetry_stream_enabled ? "STREAM_ON" : "STREAM_OFF");
}

void dispatchServiceCommand(char command) {
  switch (command) {
    case '?': printHelp(); break;
    case 'p': emitTelemetry("SNAPSHOT"); break;
    case 'v': toggleTelemetryStream(); break;
    case 't': pressure.requestTare(); break;
    case 'e': pressure.setManualCommand(true, true); break;
    case 'l': pressure.setManualCommand(true, false); break;
    case 'a': pressure.setManualCommand(false, false); break;
    case 'c': pressure.clearFault(); break;
    default: break;
  }
}

void serviceSerial() {
  while (Serial.available() > 0) {
    dispatchServiceCommand(static_cast<char>(Serial.read()));
  }
  while (Serial2.available() > 0) {
    dispatchServiceCommand(static_cast<char>(Serial2.read()));
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
  Serial2.setTX(PIN_SERVICE_UART_TX);
  Serial2.setRX(PIN_SERVICE_UART_RX);
  Serial2.begin(SERIAL_BAUD);
  Serial2.println(F("Theta toolhead service UART ready"));
  delay(250); // Startup-only USB enumeration; automatic control has not begun.
  Serial.println();
  Serial.println(F("Theta RP2350 dual-core toolhead firmware"));
  if (watchdog_caused_reboot()) {
    Serial.println(F("Previous reset was caused by the hardware watchdog."));
  }
  pressure.begin();
  last_core0_heartbeat_ms = millis();
  last_core1_observed_ms = millis();
  printConsoleLine("READY,quiet=state-events,p=snapshot,v=toggle-1s-stream,?=help");
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
  reportPressureStateChange();

  const uint32_t telemetry_now = millis();
  if (telemetry_stream_enabled &&
      telemetry_now - last_telemetry_ms >= TELEMETRY_PERIOD_MS) {
    last_telemetry_ms = telemetry_now;
    emitTelemetry("LIVE");
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

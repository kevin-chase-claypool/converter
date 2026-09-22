#pragma once

#include <stdint.h>

namespace toolhead {

enum class ContactSeekAction : uint8_t {
  WAIT,
  START_PULSE,
  STOP_PULSE,
  CONTACT_FOUND,
  CANCELLED,
  LIMIT_REACHED,
};

struct ContactSeekStatus {
  bool engage_requested;
  bool fresh_sample;
  long normalized_force_raw;
  long contact_threshold_raw;
  uint32_t now_ms;
  uint32_t seek_started_ms;
  bool pulse_active;
  uint32_t pulse_started_ms;
  uint32_t last_pulse_ended_ms;
  uint16_t completed_pulses;
};

struct ContactSeekLimits {
  uint32_t pulse_ms;
  uint32_t settle_ms;
  uint16_t max_pulses;
  uint32_t timeout_ms;
};

constexpr bool elapsed(uint32_t now_ms, uint32_t start_ms,
                       uint32_t duration_ms) {
  return static_cast<uint32_t>(now_ms - start_ms) >= duration_ms;
}

constexpr ContactSeekAction decideContactSeekAction(
    const ContactSeekStatus &status, const ContactSeekLimits &limits) {
  if (!status.engage_requested) {
    return ContactSeekAction::CANCELLED;
  }
  if (status.fresh_sample &&
      status.normalized_force_raw >= status.contact_threshold_raw) {
    return ContactSeekAction::CONTACT_FOUND;
  }
  if (elapsed(status.now_ms, status.seek_started_ms, limits.timeout_ms)) {
    return ContactSeekAction::LIMIT_REACHED;
  }
  if (status.pulse_active) {
    return elapsed(status.now_ms, status.pulse_started_ms, limits.pulse_ms)
               ? ContactSeekAction::STOP_PULSE
               : ContactSeekAction::WAIT;
  }
  if (!status.fresh_sample) {
    return ContactSeekAction::WAIT;
  }
  if (status.completed_pulses > 0 &&
      !elapsed(status.now_ms, status.last_pulse_ended_ms, limits.settle_ms)) {
    return ContactSeekAction::WAIT;
  }
  if (status.completed_pulses >= limits.max_pulses) {
    return ContactSeekAction::LIMIT_REACHED;
  }
  return ContactSeekAction::START_PULSE;
}

// Compile-time regression cases exercise the same decision function used by
// the live state machine without energizing hardware.
constexpr ContactSeekLimits kTestLimits{25, 50, 80, 8000};
static_assert(decideContactSeekAction(
                  {true, true, 0, 100, 100, 100, false, 0, 0, 0},
                  kTestLimits) == ContactSeekAction::START_PULSE);
static_assert(decideContactSeekAction(
                  {true, false, 0, 100, 100, 100, false, 0, 0, 0},
                  kTestLimits) == ContactSeekAction::WAIT);
static_assert(decideContactSeekAction(
                  {true, false, 0, 100, 124, 100, true, 100, 0, 0},
                  kTestLimits) == ContactSeekAction::WAIT);
static_assert(decideContactSeekAction(
                  {true, false, 0, 100, 125, 100, true, 100, 0, 0},
                  kTestLimits) == ContactSeekAction::STOP_PULSE);
static_assert(decideContactSeekAction(
                  {true, true, 100, 100, 101, 100, true, 100, 0, 0},
                  kTestLimits) == ContactSeekAction::CONTACT_FOUND);
static_assert(decideContactSeekAction(
                  {false, true, 0, 100, 101, 100, true, 100, 0, 0},
                  kTestLimits) == ContactSeekAction::CANCELLED);
static_assert(decideContactSeekAction(
                  {true, true, 0, 100, 149, 100, false, 0, 100, 1},
                  kTestLimits) == ContactSeekAction::WAIT);
static_assert(decideContactSeekAction(
                  {true, true, 0, 100, 150, 100, false, 0, 100, 1},
                  kTestLimits) == ContactSeekAction::START_PULSE);
static_assert(decideContactSeekAction(
                  {true, true, 0, 100, 150, 100, false, 0, 100, 80},
                  kTestLimits) == ContactSeekAction::LIMIT_REACHED);
static_assert(decideContactSeekAction(
                  {true, false, 0, 100, 8100, 100, false, 0, 0, 0},
                  kTestLimits) == ContactSeekAction::LIMIT_REACHED);

}  // namespace toolhead

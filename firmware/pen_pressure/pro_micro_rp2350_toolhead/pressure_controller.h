#pragma once

#include <Arduino.h>
#include <CS123x.h>

#include "toolhead_config.h"

enum class PressureState : uint8_t {
  BOOT,
  LIFTING,
  HOME_RELEASE_TARE_SETTLING,
  VERIFY_LIFTED,
  LIFTED,
  MECHANICAL_ENGAGE,
  HOME_SEEK_CONTACT,
  HOME_RETRACT_AFTER_TOUCH,
  HOME_TUNE_FORCE,
  SEEK_CONTACT,
  HOLD_FORCE,
  RELEASE_TO_CLEAR,
  CLEARANCE_LIFT,
  FAULT,
};

class PressureController {
 public:
  void begin();
  void service();
  void requestTare();
  void setManualCommand(bool enabled, bool engage);
  void clearFault();
  void forceFault(const char *reason);

  PressureState state() const { return state_; }
  const char *stateName() const;
  const char *faultReason() const { return fault_reason_; }
  long raw() const { return cs1238_raw_; }
  long filtered() const { return cs1238_filtered_; }
  long tare() const { return cs1238_tare_; }
  bool tareValid() const { return tare_valid_; }
  long forceDelta() const { return cs1238_filtered_ - cs1238_tare_; }
  long normalizedForceDelta() const;
  bool commandEngage() const;
  bool driverFaulted() const;
  bool liftHomeActive() const;
  uint16_t homeSeekPulseCount() const { return home_seek_pulse_count_; }
  uint16_t homeTunePulseCount() const { return home_tune_pulse_count_; }
  bool manualOverride() const { return manual_override_; }

 private:
  void setState(PressureState next);
  void setDriverEnabled(bool enabled);
  void motorStop();
  void motorDrive(bool use_in1_pwm, uint8_t pwm);
  void motorLift();
  void motorSeek();
  void serviceCs1238();
  void serviceTare(long sample);
  void updateFilteredSample(long sample);
  void updateReadyState();
  void publishSafetyState();
  void enterFault(const char *reason);
  long noContactResidual() const;
  CS123x scale_{CS123X_TYPE_CS1238, toolhead_config::PIN_CS1238_DT,
                toolhead_config::PIN_CS1238_SCK, CS123X_CH_A,
                CS123X_GAIN_128, CS123X_RATE_640Hz, CS123X_INT_REF_OFF};
  PressureState state_ = PressureState::BOOT;
  uint32_t state_started_ms_ = 0;
  uint32_t last_force_correction_ms_ = 0;
  uint32_t m3_started_ms_ = 0;
  uint32_t home_seek_pulse_started_ms_ = 0;
  uint32_t home_seek_last_pulse_ended_ms_ = 0;
  uint32_t home_surface_retract_started_ms_ = 0;
  uint32_t hold_correction_pulse_started_ms_ = 0;

  bool manual_override_ = false;
  bool manual_engage_ = false;
  bool cs1238_powered_down_ = false;
  bool new_filtered_sample_ = false;
  bool tare_valid_ = false;
  bool m3_force_acquired_ = false;
  bool home_seek_pulse_active_ = false;
  bool hold_correction_pulse_active_ = false;
  bool home_tare_sampling_started_ = false;
  bool home_wait_for_release_tare_ = false;
  uint8_t home_seek_active_pulse_ms_ = 0;

  long cs1238_raw_ = 0;
  long cs1238_tare_ = 0;
  long cs1238_filtered_ = 0;
  long sample_window_[toolhead_config::CS1238_MOVING_AVERAGE_SAMPLES] = {};
  uint8_t sample_window_count_ = 0;
  uint8_t sample_window_index_ = 0;
  int64_t sample_window_sum_ = 0;

  bool tare_requested_ = false;
  int64_t tare_sum_ = 0;
  uint8_t tare_count_ = 0;
  uint8_t lift_release_windows_ = 0;
  uint8_t contact_ready_windows_ = 0;
  uint16_t home_seek_pulse_count_ = 0;
  uint16_t home_tune_pulse_count_ = 0;
  uint8_t home_seek_pulses_while_switch_active_ = 0;

  const char *fault_reason_ = "none";
};

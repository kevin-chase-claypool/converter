#pragma once

#include <Arduino.h>
#include "HX711.h"

enum class PressureState : uint8_t {
  BOOT,
  LIFTING,
  VERIFY_LIFTED,
  LIFTED,
  SEEK_CONTACT,
  HOLD_FORCE,
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
  long raw() const { return hx_raw_; }
  long filtered() const { return hx_filtered_; }
  long tare() const { return hx_tare_; }
  long forceDelta() const { return hx_filtered_ - hx_tare_; }
  bool commandEngage() const;
  bool driverFaulted() const;
  bool manualOverride() const { return manual_override_; }

 private:
  void setState(PressureState next);
  void setDriverEnabled(bool enabled);
  void motorStop();
  void motorDrive(bool use_in1_pwm, uint8_t pwm);
  void motorLift();
  void motorSeek();
  void serviceHx711();
  void serviceTare(long sample);
  void updateFilteredSample(long sample);
  void publishSafetyState();
  void enterFault(const char *reason);
  static long median3(long a, long b, long c);

  HX711 scale_;
  PressureState state_ = PressureState::BOOT;
  uint32_t state_started_ms_ = 0;
  uint32_t last_force_correction_ms_ = 0;

  bool manual_override_ = false;
  bool manual_engage_ = false;
  bool hx_powered_down_ = false;
  bool new_filtered_sample_ = false;

  long hx_raw_ = 0;
  long hx_tare_ = 0;
  long hx_filtered_ = 0;
  long sample_window_[3] = {0, 0, 0};
  uint8_t sample_window_count_ = 0;
  uint8_t sample_window_index_ = 0;
  bool ema_initialized_ = false;

  bool tare_requested_ = false;
  int64_t tare_sum_ = 0;
  uint8_t tare_count_ = 0;
  uint8_t lift_release_windows_ = 0;

  const char *fault_reason_ = "none";
};

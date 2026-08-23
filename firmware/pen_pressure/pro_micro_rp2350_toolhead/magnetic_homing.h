#pragma once

#include <Arduino.h>
#include <Wire.h>
#include "SparkFun_TMAG5273_Arduino_Library.h"

enum class MagneticState : uint8_t {
  BOOT,
  DISARMED,
  READY_ACK,
  WAIT_REARM,
  SCAN_ACTIVE,
  FAULT,
};

class MagneticHomingController {
 public:
  void begin();
  void service();
  MagneticState state() const { return state_; }
  const char *stateName() const;
  const char *faultReason() const { return fault_reason_; }

 private:
  bool armActive() const;
  bool prerequisitesReady() const;
  void setState(MagneticState next);
  void setOutput(bool active);
  void readSensor();
  void updateBaseline(float x, float y, float z);
  void updateDetection(float delta_magnitude);
  void enterFault(const char *reason);
  void clearPublishedState();

  TMAG5273 tmag_;
  MagneticState state_ = MagneticState::BOOT;
  const char *fault_reason_ = "none";

  bool tmag_online_ = false;
  bool baseline_ready_ = false;
  bool detected_ = false;
  bool output_active_ = false;
  bool last_arm_active_ = false;

  uint32_t state_started_ms_ = 0;
  uint32_t scan_started_ms_ = 0;
  uint32_t last_sample_us_ = 0;
  uint32_t last_sensor_check_ms_ = 0;

  uint16_t baseline_count_ = 0;
  double baseline_sum_x_ = 0.0;
  double baseline_sum_y_ = 0.0;
  double baseline_sum_z_ = 0.0;
  float baseline_x_ = 0.0f;
  float baseline_y_ = 0.0f;
  float baseline_z_ = 0.0f;
  uint8_t on_count_ = 0;
  uint8_t off_count_ = 0;
};

#include "magnetic_homing.h"

#include <cmath>

#include "toolhead_config.h"
#include "toolhead_shared.h"

using namespace toolhead_config;

void MagneticHomingController::begin() {
  pinMode(PIN_A_HOME_OUT, OUTPUT);
  pinMode(PIN_HOME_ARM_IN, INPUT);
  setOutput(false);

  Wire.setSDA(PIN_I2C_SDA);
  Wire.setSCL(PIN_I2C_SCL);
  Wire.begin();
  Wire.setClock(400000);

  tmag_online_ = tmag_.begin(TMAG5273_I2C_ADDRESS_INITIAL, Wire) == 1;
  if (tmag_online_) {
    tmag_.setTemperatureEn(false);
    tmag_.setConvAvg(TMAG5273_X8_CONVERSION);
  }

  setStatusFlag(STATUS_TMAG_ONLINE, tmag_online_);
  setStatusFlag(STATUS_CORE1_READY, true);
  setState(tmag_online_ ? MagneticState::DISARMED : MagneticState::FAULT);
  if (!tmag_online_) {
    fault_reason_ = "TMAG5273 initialization failed";
  }
  last_arm_active_ = armActive();
}

const char *MagneticHomingController::stateName() const {
  switch (state_) {
    case MagneticState::BOOT: return "BOOT";
    case MagneticState::DISARMED: return "DISARMED";
    case MagneticState::READY_ACK: return "READY_ACK";
    case MagneticState::WAIT_REARM: return "WAIT_REARM";
    case MagneticState::SCAN_ACTIVE: return "SCAN_ACTIVE";
    case MagneticState::FAULT: return "FAULT";
  }
  return "UNKNOWN";
}

bool MagneticHomingController::armActive() const {
  const int raw = digitalRead(PIN_HOME_ARM_IN);
  return HOME_ARM_ACTIVE_LOW ? raw == LOW : raw == HIGH;
}

bool MagneticHomingController::prerequisitesReady() const {
  return MAGNETIC_CALIBRATION_VALID && tmag_online_ && baseline_ready_ &&
         statusFlag(STATUS_SAFE_FOR_HOMING) &&
         !statusFlag(STATUS_PRESSURE_FAULT);
}

void MagneticHomingController::setOutput(bool active) {
  output_active_ = active;
  digitalWrite(PIN_A_HOME_OUT, active ? HIGH : LOW);
}

void MagneticHomingController::clearPublishedState() {
  setStatusFlag(STATUS_MAG_SCAN_ACTIVE, false);
  setStatusFlag(STATUS_MAG_DETECTED, false);
  setOutput(false);
}

void MagneticHomingController::setState(MagneticState next) {
  state_ = next;
  g_mag_state.store(static_cast<uint32_t>(next), std::memory_order_release);
  state_started_ms_ = millis();
  if (next != MagneticState::SCAN_ACTIVE) {
    setStatusFlag(STATUS_MAG_SCAN_ACTIVE, false);
  }
  setStatusFlag(STATUS_MAG_FAULT, next == MagneticState::FAULT);
}

void MagneticHomingController::enterFault(const char *reason) {
  fault_reason_ = reason;
  clearPublishedState();
  setState(MagneticState::FAULT);
}

void MagneticHomingController::updateBaseline(float x, float y, float z) {
  if (state_ != MagneticState::DISARMED || armActive() || baseline_ready_) {
    return;
  }

  const float magnitude = std::sqrt(x * x + y * y + z * z);
  if (!std::isfinite(magnitude) || magnitude > MAG_BASELINE_MAX_MT) {
    baseline_count_ = 0;
    baseline_sum_x_ = baseline_sum_y_ = baseline_sum_z_ = 0.0;
    return;
  }

  baseline_sum_x_ += x;
  baseline_sum_y_ += y;
  baseline_sum_z_ += z;
  baseline_count_++;
  if (baseline_count_ >= MAG_BASELINE_SAMPLES) {
    baseline_x_ = static_cast<float>(baseline_sum_x_ / baseline_count_);
    baseline_y_ = static_cast<float>(baseline_sum_y_ / baseline_count_);
    baseline_z_ = static_cast<float>(baseline_sum_z_ / baseline_count_);
    baseline_ready_ = true;
    setStatusFlag(STATUS_TMAG_BASELINE_READY, true);
  }
}

void MagneticHomingController::updateDetection(float delta_magnitude) {
  const float off_threshold = MAG_ON_THRESHOLD_MT - MAG_HYSTERESIS_MT;
  if (!detected_) {
    off_count_ = 0;
    if (delta_magnitude >= MAG_ON_THRESHOLD_MT) {
      if (++on_count_ >= MAG_REQUIRED_CONSECUTIVE_SAMPLES) {
        detected_ = true;
        on_count_ = 0;
      }
    } else {
      on_count_ = 0;
    }
  } else {
    on_count_ = 0;
    if (delta_magnitude <= off_threshold) {
      if (++off_count_ >= MAG_REQUIRED_CONSECUTIVE_SAMPLES) {
        detected_ = false;
        off_count_ = 0;
      }
    } else {
      off_count_ = 0;
    }
  }
  setStatusFlag(STATUS_MAG_DETECTED, detected_);
}

void MagneticHomingController::readSensor() {
  if (!tmag_online_) {
    return;
  }

  const uint32_t now_us = micros();
  if (now_us - last_sample_us_ < MAG_SAMPLE_PERIOD_US) {
    return;
  }
  last_sample_us_ = now_us;

  const float x = tmag_.getXData();
  const float y = tmag_.getYData();
  const float z = tmag_.getZData();
  if (!std::isfinite(x) || !std::isfinite(y) || !std::isfinite(z)) {
    enterFault("TMAG5273 returned invalid data");
    return;
  }

  updateBaseline(x, y, z);
  const float dx = x - baseline_x_;
  const float dy = y - baseline_y_;
  const float dz = z - baseline_z_;
  const float delta = std::sqrt(dx * dx + dy * dy + dz * dz);
  updateDetection(delta);

  g_mag_x_millimt.store(static_cast<int32_t>(x * 1000.0f), std::memory_order_relaxed);
  g_mag_y_millimt.store(static_cast<int32_t>(y * 1000.0f), std::memory_order_relaxed);
  g_mag_z_millimt.store(static_cast<int32_t>(z * 1000.0f), std::memory_order_relaxed);
  g_mag_delta_millimt.store(static_cast<int32_t>(delta * 1000.0f), std::memory_order_relaxed);
  g_mag_sample_count.fetch_add(1, std::memory_order_relaxed);
}

void MagneticHomingController::service() {
  const uint32_t now = millis();
  readSensor();

  if (tmag_online_ && now - last_sensor_check_ms_ >= MAG_SENSOR_CHECK_PERIOD_MS) {
    last_sensor_check_ms_ = now;
    if (tmag_.isConnected() != 0) {
      tmag_online_ = false;
      setStatusFlag(STATUS_TMAG_ONLINE, false);
      enterFault("TMAG5273 communication lost");
    }
  }

  const bool arm = armActive();
  const bool arm_rising = arm && !last_arm_active_;
  const bool arm_falling = !arm && last_arm_active_;
  last_arm_active_ = arm;

  if (!statusFlag(STATUS_SAFE_FOR_HOMING) &&
      (state_ == MagneticState::READY_ACK || state_ == MagneticState::WAIT_REARM ||
       state_ == MagneticState::SCAN_ACTIVE)) {
    enterFault("toolhead lost safe-for-homing state");
  }

  switch (state_) {
    case MagneticState::BOOT:
      clearPublishedState();
      break;

    case MagneticState::DISARMED:
      clearPublishedState();
      if (arm_rising) {
        if (prerequisitesReady()) {
          fault_reason_ = "none";
          setState(MagneticState::READY_ACK);
          setOutput(true);
        } else {
          enterFault("magnetic readiness prerequisites not met");
        }
      }
      break;

    case MagneticState::READY_ACK:
      setOutput(true);
      if (arm_falling) {
        setOutput(false);
        setState(MagneticState::WAIT_REARM);
      }
      break;

    case MagneticState::WAIT_REARM:
      setOutput(false);
      if (now - state_started_ms_ > MAG_REARM_WINDOW_MS) {
        setState(MagneticState::DISARMED);
      } else if (arm_rising) {
        if (prerequisitesReady()) {
          scan_started_ms_ = now;
          setState(MagneticState::SCAN_ACTIVE);
          setStatusFlag(STATUS_MAG_SCAN_ACTIVE, true);
          setOutput(detected_);
        } else {
          enterFault("readiness lost before scan re-arm");
        }
      }
      break;

    case MagneticState::SCAN_ACTIVE:
      setStatusFlag(STATUS_MAG_SCAN_ACTIVE, true);
      setOutput(detected_ && prerequisitesReady());
      if (arm_falling) {
        clearPublishedState();
        setState(MagneticState::DISARMED);
      } else if (now - scan_started_ms_ > MAG_MAX_ARM_TIME_MS) {
        enterFault("magnetic arm timeout");
      }
      break;

    case MagneticState::FAULT:
      clearPublishedState();
      if (!arm && tmag_online_ && statusFlag(STATUS_SAFE_FOR_HOMING)) {
        fault_reason_ = "none";
        setState(MagneticState::DISARMED);
      }
      break;
  }
}

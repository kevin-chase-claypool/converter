#include "pressure_controller.h"

#include <cstdlib>

#include "toolhead_config.h"
#include "toolhead_shared.h"

using namespace toolhead_config;

void PressureController::begin() {
  pinMode(PIN_CMD_M3M5, INPUT);
  pinMode(PIN_DRV_IN1, OUTPUT);
  pinMode(PIN_DRV_IN2, OUTPUT);
  pinMode(PIN_DRV_SLEEP, OUTPUT);
  pinMode(PIN_DRV_FAULT, INPUT_PULLUP);

  motorStop();
  setDriverEnabled(false);

  scale_.begin(PIN_HX711_DT, PIN_HX711_SCK);
  requestTare();

  state_started_ms_ = millis();
  setStatusFlag(STATUS_CORE0_READY, true);

  if (!ACTUATOR_DIRECTION_VALID) {
    enterFault("T-01 actuator direction is not commissioned");
    return;
  }

  setState(PressureState::LIFTING);
}

const char *PressureController::stateName() const {
  switch (state_) {
    case PressureState::BOOT: return "BOOT";
    case PressureState::LIFTING: return "LIFTING";
    case PressureState::VERIFY_LIFTED: return "VERIFY_LIFTED";
    case PressureState::LIFTED: return "LIFTED";
    case PressureState::SEEK_CONTACT: return "SEEK_CONTACT";
    case PressureState::HOLD_FORCE: return "HOLD_FORCE";
    case PressureState::FAULT: return "FAULT";
  }
  return "UNKNOWN";
}

void PressureController::setState(PressureState next) {
  state_ = next;
  state_started_ms_ = millis();
  if (next != PressureState::VERIFY_LIFTED) {
    lift_release_windows_ = 0;
  }
  publishSafetyState();
}

void PressureController::setDriverEnabled(bool enabled) {
  digitalWrite(PIN_DRV_SLEEP, enabled ? HIGH : LOW);
}

void PressureController::motorStop() {
  analogWrite(PIN_DRV_IN1, 0);
  analogWrite(PIN_DRV_IN2, 0);
}

void PressureController::motorDrive(bool use_in1_pwm, uint8_t pwm) {
  setDriverEnabled(true);
  if (use_in1_pwm) {
    analogWrite(PIN_DRV_IN1, pwm);
    analogWrite(PIN_DRV_IN2, 0);
  } else {
    analogWrite(PIN_DRV_IN1, 0);
    analogWrite(PIN_DRV_IN2, pwm);
  }
}

void PressureController::motorLift() {
  motorDrive(LIFT_USES_IN1_PWM, PWM_LIFT);
}

void PressureController::motorSeek() {
  motorDrive(SEEK_USES_IN1_PWM, PWM_SEEK);
}

bool PressureController::driverFaulted() const {
  const int raw = digitalRead(PIN_DRV_FAULT);
  return DRV_FAULT_ACTIVE_LOW ? raw == LOW : raw == HIGH;
}

bool PressureController::commandEngage() const {
  if (manual_override_) {
    return manual_engage_;
  }
  const int raw = digitalRead(PIN_CMD_M3M5);
  return CMD_ACTIVE_HIGH_IS_M3 ? raw == HIGH : raw == LOW;
}

long PressureController::median3(long a, long b, long c) {
  if (a > b) {
    const long t = a; a = b; b = t;
  }
  if (b > c) {
    const long t = b; b = c; c = t;
  }
  if (a > b) {
    const long t = a; a = b; b = t;
  }
  return b;
}

void PressureController::updateFilteredSample(long sample) {
  sample_window_[sample_window_index_] = sample;
  sample_window_index_ = (sample_window_index_ + 1) % 3;
  if (sample_window_count_ < 3) {
    sample_window_count_++;
  }
  if (sample_window_count_ < 3) {
    return;
  }

  const long median = median3(sample_window_[0], sample_window_[1], sample_window_[2]);
  if (!ema_initialized_) {
    hx_filtered_ = median;
    ema_initialized_ = true;
  } else {
    hx_filtered_ = (3L * hx_filtered_ + median) / 4L;
  }
  new_filtered_sample_ = true;
}

void PressureController::serviceTare(long sample) {
  if (!tare_requested_) {
    return;
  }
  tare_sum_ += sample;
  tare_count_++;
  if (tare_count_ >= 10) {
    hx_tare_ = static_cast<long>(tare_sum_ / tare_count_);
    tare_requested_ = false;
    tare_sum_ = 0;
    tare_count_ = 0;
  }
}

void PressureController::serviceHx711() {
  if (hx_powered_down_ || !scale_.is_ready()) {
    return;
  }
  hx_raw_ = scale_.read();
  setStatusFlag(STATUS_HX_ONLINE, true);
  serviceTare(hx_raw_);
  updateFilteredSample(hx_raw_);
}

void PressureController::requestTare() {
  tare_requested_ = true;
  tare_sum_ = 0;
  tare_count_ = 0;
}

void PressureController::setManualCommand(bool enabled, bool engage) {
  manual_override_ = enabled;
  manual_engage_ = engage;
}

void PressureController::publishSafetyState() {
  const bool lifted = state_ == PressureState::LIFTED;
  const bool safe = lifted && LIFT_REFERENCE_VALID && !driverFaulted() &&
                    state_ != PressureState::FAULT;
  setStatusFlag(STATUS_TOOL_LIFTED, lifted);
  setStatusFlag(STATUS_SAFE_FOR_HOMING, safe);
  setStatusFlag(STATUS_PRESSURE_FAULT, state_ == PressureState::FAULT);
}

void PressureController::enterFault(const char *reason) {
  fault_reason_ = reason;
  motorStop();
  setDriverEnabled(false);
  setState(PressureState::FAULT);
}

void PressureController::forceFault(const char *reason) {
  if (state_ != PressureState::FAULT) {
    enterFault(reason);
  }
}

void PressureController::clearFault() {
  if (state_ != PressureState::FAULT) {
    return;
  }
  if (!ACTUATOR_DIRECTION_VALID) {
    fault_reason_ = "T-01 actuator direction is not commissioned";
    return;
  }
  fault_reason_ = "none";
  setState(PressureState::LIFTING);
}

void PressureController::service() {
  const uint32_t now = millis();
  const bool magnetic_scan = statusFlag(STATUS_MAG_SCAN_ACTIVE);

  if (magnetic_scan && !hx_powered_down_) {
    scale_.power_down();
    hx_powered_down_ = true;
    setStatusFlag(STATUS_HX_ONLINE, false);
  } else if (!magnetic_scan && hx_powered_down_) {
    scale_.power_up();
    hx_powered_down_ = false;
    sample_window_count_ = 0;
    ema_initialized_ = false;
  }

  if (!magnetic_scan) {
    serviceHx711();
  }

  if (state_ != PressureState::FAULT && driverFaulted()) {
    enterFault("DRV8833 fault input active");
    return;
  }

  if (state_ != PressureState::FAULT && new_filtered_sample_ &&
      forceDelta() > HARD_FORCE_RAW_DELTA) {
    enterFault("hard force limit exceeded");
    return;
  }

  const bool engage = commandEngage();
  if (magnetic_scan && engage) {
    enterFault("M3 requested during magnetic homing");
    return;
  }

  switch (state_) {
    case PressureState::BOOT:
      motorStop();
      break;

    case PressureState::LIFTING:
      motorLift();
      if (now - state_started_ms_ >= LIFT_TIME_MS) {
        motorStop();
        setDriverEnabled(false);
        setState(PressureState::VERIFY_LIFTED);
      }
      break;

    case PressureState::VERIFY_LIFTED:
      motorStop();
      setDriverEnabled(false);
      if (!LIFT_REFERENCE_VALID) {
        enterFault("T-02 no-contact lift reference is not commissioned");
        break;
      }
      if (new_filtered_sample_) {
        const long residual = std::labs(hx_filtered_ - NO_CONTACT_RAW_REFERENCE);
        if (residual <= LIFT_RELEASE_TOLERANCE_RAW) {
          lift_release_windows_++;
        } else {
          lift_release_windows_ = 0;
        }
        if (lift_release_windows_ >= LIFT_RELEASE_REQUIRED_WINDOWS) {
          setState(PressureState::LIFTED);
        }
      }
      if (state_ == PressureState::VERIFY_LIFTED &&
          now - state_started_ms_ >= LIFT_VERIFY_TIMEOUT_MS) {
        enterFault("HX711 did not verify pen release");
      }
      break;

    case PressureState::LIFTED:
      motorStop();
      setDriverEnabled(false);
      if (engage) {
        if (!PRESSURE_CALIBRATION_VALID) {
          enterFault("E-07/E-08 pressure calibration is incomplete");
        } else if (!statusFlag(STATUS_HX_ONLINE)) {
          enterFault("M3 requested without HX711 data");
        } else {
          setState(PressureState::SEEK_CONTACT);
        }
      }
      break;

    case PressureState::SEEK_CONTACT:
      if (!engage) {
        setState(PressureState::LIFTING);
        break;
      }
      motorSeek();
      if (new_filtered_sample_ && forceDelta() >= CONTACT_RAW_DELTA) {
        motorStop();
        setState(PressureState::HOLD_FORCE);
      } else if (now - state_started_ms_ >= SEEK_TIMEOUT_MS) {
        enterFault("seek timeout; no contact found");
      }
      break;

    case PressureState::HOLD_FORCE:
      if (!engage) {
        setState(PressureState::LIFTING);
        break;
      }
      if (new_filtered_sample_ && now - last_force_correction_ms_ >= HX_CORRECTION_PERIOD_MS) {
        last_force_correction_ms_ = now;
        const long error = TARGET_FORCE_RAW_DELTA - forceDelta();
        int command = static_cast<int>((error * HOLD_KP_NUM) / HOLD_KP_DEN);
        if (command > 0) {
          command = constrain(command, 0, PWM_HOLD_MAX);
          motorDrive(SEEK_USES_IN1_PWM, static_cast<uint8_t>(command));
        } else if (command < -20) {
          command = constrain(-command, 0, PWM_HOLD_MAX);
          motorDrive(LIFT_USES_IN1_PWM, static_cast<uint8_t>(command));
        } else {
          motorStop();
        }
      }
      break;

    case PressureState::FAULT:
      motorStop();
      setDriverEnabled(false);
      break;
  }

  new_filtered_sample_ = false;
  publishSafetyState();
}

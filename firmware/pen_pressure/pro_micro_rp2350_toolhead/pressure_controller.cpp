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
  pinMode(PIN_LIFT_HOME, INPUT_PULLUP);

  motorStop();
  setDriverEnabled(false);

  if (!scale_.begin() ||
      !scale_.setConfig(CS123X_CH_A, CS123X_GAIN_128, CS123X_RATE_640Hz, true)) {
    enterFault("CS1238 initialization/configuration failed");
    return;
  }
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
    case PressureState::MECHANICAL_ENGAGE: return "MECHANICAL_ENGAGE";
    case PressureState::SEEK_CONTACT: return "SEEK_CONTACT";
    case PressureState::HOLD_FORCE: return "HOLD_FORCE";
    case PressureState::RELEASE_TO_CLEAR: return "RELEASE_TO_CLEAR";
    case PressureState::CLEARANCE_LIFT: return "CLEARANCE_LIFT";
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
  if (next != PressureState::HOLD_FORCE) {
    contact_ready_windows_ = 0;
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

bool PressureController::liftHomeActive() const {
  const int raw = digitalRead(PIN_LIFT_HOME);
  return LIFT_HOME_ACTIVE_LOW ? raw == LOW : raw == HIGH;
}

bool PressureController::commandEngage() const {
  if (manual_override_) {
    return manual_engage_;
  }
  const int raw = digitalRead(PIN_CMD_M3M5);
  return CMD_ACTIVE_HIGH_IS_M3 ? raw == HIGH : raw == LOW;
}

long PressureController::normalizedForceDelta() const {
  return static_cast<long>(CS1238_CONTACT_FORCE_SIGN) * forceDelta();
}

long PressureController::noContactResidual() const {
  // The E-09C zero is retained in configuration as calibration evidence, but
  // every boot takes a fresh unloaded tare. Clear detection must use that live
  // reference so an otherwise valid profile is not defeated by ADC drift or a
  // small fixture-zero change.
  return cs1238_filtered_ - cs1238_tare_;
}

void PressureController::updateFilteredSample(long sample) {
  if (sample_window_count_ == CS1238_MOVING_AVERAGE_SAMPLES) {
    sample_window_sum_ -= sample_window_[sample_window_index_];
  } else {
    sample_window_count_++;
  }
  sample_window_[sample_window_index_] = sample;
  sample_window_sum_ += sample;
  sample_window_index_ = (sample_window_index_ + 1) % CS1238_MOVING_AVERAGE_SAMPLES;
  if (sample_window_count_ < CS1238_MOVING_AVERAGE_SAMPLES) {
    return;
  }
  cs1238_filtered_ = static_cast<long>(sample_window_sum_ / CS1238_MOVING_AVERAGE_SAMPLES);
  new_filtered_sample_ = true;
}

void PressureController::serviceTare(long sample) {
  if (!tare_requested_) {
    return;
  }
  tare_sum_ += sample;
  tare_count_++;
  if (tare_count_ >= CS1238_TARE_SAMPLES) {
    cs1238_tare_ = static_cast<long>(tare_sum_ / tare_count_);
    tare_requested_ = false;
    tare_sum_ = 0;
    tare_count_ = 0;
  }
}

void PressureController::serviceCs1238() {
  if (cs1238_powered_down_ || !scale_.isReady()) {
    return;
  }
  const int32_t sample = scale_.forceRead();
  if (sample >= CS123X_TIMEOUT_ERROR) {
    setStatusFlag(STATUS_CS1238_ONLINE, false);
    return;
  }
  cs1238_raw_ = sample;
  setStatusFlag(STATUS_CS1238_ONLINE, true);
  serviceTare(cs1238_raw_);
  updateFilteredSample(cs1238_raw_);
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
  const bool pressure_healthy = PRESSURE_CALIBRATION_VALID &&
                                statusFlag(STATUS_CS1238_ONLINE) &&
                                !driverFaulted() && state_ != PressureState::FAULT;
  const bool contact_ready = pressure_healthy && state_ == PressureState::HOLD_FORCE &&
                             contact_ready_windows_ >= CONTACT_READY_REQUIRED_WINDOWS;
  // This firmware's present LIFTED state is only published as a normal M5
  // completion after T-01H has proven the calibrated PEN_CLEAR behavior.
  const bool clear_ready = PEN_CLEAR_VALID && lifted && !commandEngage() &&
                           !driverFaulted() && state_ != PressureState::FAULT;
  setStatusFlag(STATUS_TOOL_LIFTED, lifted);
  setStatusFlag(STATUS_SAFE_FOR_HOMING, safe);
  setStatusFlag(STATUS_PRESSURE_FAULT, state_ == PressureState::FAULT);
  setStatusFlag(STATUS_CONTACT_READY, contact_ready);
  setStatusFlag(STATUS_CLEAR_READY, clear_ready);
}

void PressureController::updateReadyState() {
  if (state_ != PressureState::HOLD_FORCE || !PRESSURE_CALIBRATION_VALID ||
      !statusFlag(STATUS_CS1238_ONLINE) || driverFaulted()) {
    contact_ready_windows_ = 0;
    return;
  }
  if (!new_filtered_sample_) {
    return;
  }

  const long target_error = std::labs(normalizedForceDelta() - TARGET_FORCE_RAW_DELTA);
  if (target_error <= CONTACT_READY_TOLERANCE_RAW) {
    if (contact_ready_windows_ < CONTACT_READY_REQUIRED_WINDOWS) {
      contact_ready_windows_++;
    }
  } else {
    contact_ready_windows_ = 0;
  }
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

  if (magnetic_scan && !cs1238_powered_down_) {
    scale_.powerDown();
    cs1238_powered_down_ = true;
    setStatusFlag(STATUS_CS1238_ONLINE, false);
  } else if (!magnetic_scan && cs1238_powered_down_) {
    scale_.powerUp();
    cs1238_powered_down_ = false;
    sample_window_count_ = 0;
    sample_window_index_ = 0;
    sample_window_sum_ = 0;
  }

  if (!magnetic_scan) {
    serviceCs1238();
  }

  if (state_ != PressureState::FAULT && driverFaulted()) {
    enterFault("DRV8833 fault input active");
    return;
  }

  if (state_ != PressureState::FAULT && PRESSURE_CALIBRATION_VALID && new_filtered_sample_ &&
      normalizedForceDelta() > HARD_FORCE_RAW_DELTA) {
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
      if (now - state_started_ms_ >= BOOT_LIFT_TIME_MS) {
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
        const long residual = std::labs(noContactResidual());
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
        enterFault("CS1238 did not verify pen release");
      }
      break;

    case PressureState::LIFTED:
      motorStop();
      setDriverEnabled(false);
      if (engage) {
        if (MECHANICAL_PRELOAD_MODE) {
          if (!ACTUATOR_DIRECTION_VALID) {
            enterFault("M3 requested before actuator direction commissioning");
          } else {
            setState(PressureState::MECHANICAL_ENGAGE);
          }
        } else if (!PRESSURE_CALIBRATION_VALID) {
          enterFault("E-07/E-08 pressure calibration is incomplete");
        } else if (!statusFlag(STATUS_CS1238_ONLINE)) {
          enterFault("M3 requested without CS1238 data");
        } else {
          setState(PressureState::SEEK_CONTACT);
        }
      }
      break;

    case PressureState::MECHANICAL_ENGAGE:
      if (!engage) {
        setState(PressureState::CLEARANCE_LIFT);
        break;
      }
      // The pen is mechanically installed at the desired drawing preload.
      // This timed move returns from the verified 100 ms clear position; the
      // CS1238 remains telemetry/guarding and does not seek paper.
      motorSeek();
      if (now - state_started_ms_ >= PEN_ENGAGE_TRAVEL_MS) {
        motorStop();
        setDriverEnabled(false);
        setState(PressureState::HOLD_FORCE);
      }
      break;

    case PressureState::SEEK_CONTACT:
      if (!engage) {
        // Normal M5 first proves the no-contact release band, then adds an
        // explicit air-gap pulse. Do not treat a timed boot lift as proof of
        // normal pen clearance.
        setState(PressureState::RELEASE_TO_CLEAR);
        break;
      }
      motorSeek();
      if (new_filtered_sample_ && normalizedForceDelta() >= CONTACT_RAW_DELTA) {
        motorStop();
        setState(PressureState::HOLD_FORCE);
      } else if (now - state_started_ms_ >= SEEK_TIMEOUT_MS) {
        enterFault("seek timeout; no contact found");
      }
      break;

    case PressureState::HOLD_FORCE:
      if (!engage) {
        setState(PressureState::CLEARANCE_LIFT);
        break;
      }
      if (MECHANICAL_PRELOAD_MODE) {
        motorStop();
        setDriverEnabled(false);
        break;
      }
      if (new_filtered_sample_ && now - last_force_correction_ms_ >= CS1238_CORRECTION_PERIOD_MS) {
        last_force_correction_ms_ = now;
        const long error = TARGET_FORCE_RAW_DELTA - normalizedForceDelta();
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

    case PressureState::RELEASE_TO_CLEAR:
      motorLift();
      if (new_filtered_sample_) {
        const long residual = std::labs(noContactResidual());
        if (residual <= LIFT_RELEASE_TOLERANCE_RAW) {
          lift_release_windows_++;
        } else {
          lift_release_windows_ = 0;
        }
        if (lift_release_windows_ >= LIFT_RELEASE_REQUIRED_WINDOWS) {
          // The candidate 100 ms is deliberately *after* the CS1238 has
          // confirmed release, providing a real physical air-gap margin for
          // between-line travel rather than merely an unloaded pen state.
          setState(PressureState::CLEARANCE_LIFT);
          break;
        }
      }
      if (now - state_started_ms_ >= PEN_CLEAR_RELEASE_TIMEOUT_MS) {
        enterFault("CS1238 did not verify pen release before clearance lift");
      }
      break;

    case PressureState::CLEARANCE_LIFT:
      motorLift();
      if (now - state_started_ms_ >= PEN_CLEAR_EXTRA_LIFT_MS) {
        motorStop();
        setDriverEnabled(false);
        if (MECHANICAL_PRELOAD_MODE) {
          // The 100 ms motion is the verified mechanical clear operation. A
          // CS1238 value immediately after motor travel is telemetry only.
          setState(PressureState::LIFTED);
        } else {
          // Recheck after the added air-gap motion before declaring M5 complete.
          setState(PressureState::VERIFY_LIFTED);
        }
      }
      break;

    case PressureState::FAULT:
      motorStop();
      setDriverEnabled(false);
      break;
  }

  updateReadyState();
  new_filtered_sample_ = false;
  publishSafetyState();
}

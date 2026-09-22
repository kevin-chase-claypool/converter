#include "pressure_controller.h"

#include <cstdlib>

#include "contact_seek_policy.h"
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
    case PressureState::HOME_RELEASE_TARE_SETTLING:
      return "HOME_RELEASE_TARE_SETTLING";
    case PressureState::VERIFY_LIFTED: return "VERIFY_LIFTED";
    case PressureState::LIFTED: return "LIFTED";
    case PressureState::MECHANICAL_ENGAGE: return "MECHANICAL_ENGAGE";
    case PressureState::HOME_SEEK_CONTACT: return "HOME_SEEK_CONTACT";
    case PressureState::HOME_RETRACT_AFTER_TOUCH: return "HOME_RETRACT_AFTER_TOUCH";
    case PressureState::HOME_TUNE_FORCE: return "HOME_TUNE_FORCE";
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
    hold_correction_pulse_active_ = false;
  }
  if (next != PressureState::HOME_SEEK_CONTACT &&
      next != PressureState::HOME_TUNE_FORCE) {
    home_seek_pulse_active_ = false;
    home_seek_active_pulse_ms_ = 0;
  }
  if (next != PressureState::HOME_RELEASE_TARE_SETTLING) {
    home_tare_sampling_started_ = false;
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
    tare_valid_ = true;
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
  tare_valid_ = false;
  tare_sum_ = 0;
  tare_count_ = 0;
}

void PressureController::setManualCommand(bool enabled, bool engage) {
  manual_override_ = enabled;
  manual_engage_ = engage;
}

void PressureController::publishSafetyState() {
  const bool lifted = state_ == PressureState::LIFTED;
  const bool lift_reference_ok = MECHANICAL_PRELOAD_MODE ? liftHomeActive()
                                                         : LIFT_REFERENCE_VALID;
  const bool safe = lifted && lift_reference_ok && !driverFaulted() &&
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
  // Fault clearing is retract-only. Hold the command low so an asserted GP29
  // or stale manual M3 cannot restart contact seeking as soon as GP2 is hit.
  manual_override_ = true;
  manual_engage_ = false;
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

  const bool retracting_to_home = state_ == PressureState::LIFTING ||
                                  state_ == PressureState::RELEASE_TO_CLEAR ||
                                  state_ == PressureState::CLEARANCE_LIFT;
  if (state_ != PressureState::FAULT && !retracting_to_home && tare_valid_ &&
      PRESSURE_CALIBRATION_VALID && new_filtered_sample_ &&
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
      if (MECHANICAL_PRELOAD_MODE && liftHomeActive()) {
        motorStop();
        setDriverEnabled(false);
        // GP2 itself can preload this mechanism. The relevant no-paper tare
        // is collected after an M3 seek first releases GP2, not at the switch.
        tare_valid_ = false;
        home_wait_for_release_tare_ = false;
        setState(PressureState::LIFTED);
      } else {
        motorLift();
        if (now - state_started_ms_ >= BOOT_LIFT_TIME_MS) {
          motorStop();
          setDriverEnabled(false);
          if (MECHANICAL_PRELOAD_MODE) {
            enterFault("GP2 lift-home not reached during retract");
          } else {
            setState(PressureState::VERIFY_LIFTED);
          }
        }
      }
      break;

    case PressureState::HOME_RELEASE_TARE_SETTLING:
      motorStop();
      setDriverEnabled(false);
      if (liftHomeActive()) {
        // The transition was not stable. Resume the switch-release phase
        // rather than accepting a switch-preloaded tare.
        home_wait_for_release_tare_ = true;
        setState(PressureState::HOME_SEEK_CONTACT);
        break;
      }
      if (now - state_started_ms_ < HOME_RELEASE_TARE_SETTLE_MS) {
        break;
      }
      if (!home_tare_sampling_started_) {
        requestTare();
        home_tare_sampling_started_ = true;
        break;
      }
      if (!tare_valid_) {
        break;
      }
      home_wait_for_release_tare_ = false;
      setState(PressureState::HOME_SEEK_CONTACT);
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
          } else if (!liftHomeActive() && !tare_valid_) {
            enterFault("M3 requested before clear-home tare completed");
          } else if (!PRESSURE_CALIBRATION_VALID) {
            enterFault("M3 requested without CS1238 force calibration");
          } else if (!statusFlag(STATUS_CS1238_ONLINE)) {
            enterFault("M3 requested without CS1238 data");
          } else {
            m3_started_ms_ = now;
            m3_force_acquired_ = false;
            if (liftHomeActive()) {
              home_seek_pulse_count_ = 0;
              home_tune_pulse_count_ = 0;
              home_seek_pulses_while_switch_active_ = 0;
              home_seek_pulse_active_ = false;
              home_seek_active_pulse_ms_ = 0;
              home_seek_pulse_started_ms_ = 0;
              home_seek_last_pulse_ended_ms_ = 0;
              tare_valid_ = false;
              home_wait_for_release_tare_ = true;
              setState(PressureState::HOME_SEEK_CONTACT);
            } else {
              setState(PressureState::MECHANICAL_ENGAGE);
            }
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
        motorStop();
        setDriverEnabled(false);
        setState(PressureState::CLEARANCE_LIFT);
        break;
      }
      // A normal M5 leaves only the measured 100 ms clearance gap. Restore
      // that short travel quickly; HOLD_FORCE must still acquire force within
      // M3_FORCE_ACQUIRE_TIMEOUT_MS.
      motorSeek();
      if (now - state_started_ms_ >= PEN_ENGAGE_TRAVEL_MS) {
        motorStop();
        setDriverEnabled(false);
        setState(PressureState::HOLD_FORCE);
      }
      break;

    case PressureState::HOME_SEEK_CONTACT: {
      if (!statusFlag(STATUS_CS1238_ONLINE)) {
        enterFault("CS1238 lost during home contact seek");
        break;
      }

      const long fine_threshold = HOME_SURFACE_TOUCH_RAW_DELTA /
                                  HOME_SEEK_FINE_THRESHOLD_DIVISOR;
      const uint32_t next_pulse_ms = home_wait_for_release_tare_
                                         ? HOME_SEEK_COARSE_PULSE_MS
                                         : normalizedForceDelta() >= fine_threshold
                                               ? HOME_SEEK_FINE_PULSE_MS
                                               : HOME_SEEK_COARSE_PULSE_MS;
      const uint32_t active_pulse_ms = home_seek_pulse_active_
                                           ? home_seek_active_pulse_ms_
                                           : next_pulse_ms;
      const toolhead::ContactSeekLimits limits{
          active_pulse_ms, HOME_SEEK_SETTLE_MS,
          HOME_SEEK_MAX_PULSES, HOME_SEEK_TIMEOUT_MS};
      const toolhead::ContactSeekStatus seek_status{
          engage,
          new_filtered_sample_,
          normalizedForceDelta(),
          home_wait_for_release_tare_ ? 0x7fffffffL
                                      : HOME_SURFACE_TOUCH_RAW_DELTA,
          now,
          state_started_ms_,
          home_seek_pulse_active_,
          home_seek_pulse_started_ms_,
          home_seek_last_pulse_ended_ms_,
          home_seek_pulse_count_};

      switch (toolhead::decideContactSeekAction(seek_status, limits)) {
        case toolhead::ContactSeekAction::WAIT:
          break;
        case toolhead::ContactSeekAction::START_PULSE:
          motorDrive(SEEK_USES_IN1_PWM, HOME_SEEK_PWM);
          home_seek_pulse_started_ms_ = now;
          home_seek_active_pulse_ms_ = static_cast<uint8_t>(limits.pulse_ms);
          home_seek_pulse_active_ = true;
          break;
        case toolhead::ContactSeekAction::STOP_PULSE:
          motorStop();
          setDriverEnabled(false);
          home_seek_pulse_active_ = false;
          home_seek_active_pulse_ms_ = 0;
          home_seek_pulse_count_++;
          home_seek_last_pulse_ended_ms_ = now;
          if (liftHomeActive()) {
            if (home_seek_pulses_while_switch_active_ <
                HOME_SEEK_MAX_SWITCH_ACTIVE_PULSES) {
              home_seek_pulses_while_switch_active_++;
            }
            if (home_seek_pulses_while_switch_active_ >=
                HOME_SEEK_MAX_SWITCH_ACTIVE_PULSES) {
              enterFault("GP2 home switch stayed active during M3 seek");
            }
          } else {
            home_seek_pulses_while_switch_active_ = 0;
            if (home_wait_for_release_tare_) {
              setState(PressureState::HOME_RELEASE_TARE_SETTLING);
            }
          }
          break;
        case toolhead::ContactSeekAction::CONTACT_FOUND:
          motorStop();
          setDriverEnabled(false);
          home_seek_pulse_active_ = false;
          home_seek_active_pulse_ms_ = 0;
          home_surface_retract_started_ms_ = now;
          setState(PressureState::HOME_RETRACT_AFTER_TOUCH);
          break;
        case toolhead::ContactSeekAction::CANCELLED:
          motorStop();
          setDriverEnabled(false);
          home_seek_pulse_active_ = false;
          home_seek_active_pulse_ms_ = 0;
          // The 3 g release detector is for force-controlled M5. A cancelled
          // home seek may still be far above contact, so do only the normal
          // bounded up-clearance move (or stop sooner at GP2).
          setState(PressureState::CLEARANCE_LIFT);
          break;
        case toolhead::ContactSeekAction::LIMIT_REACHED:
          motorStop();
          setDriverEnabled(false);
          home_seek_pulse_active_ = false;
          home_seek_active_pulse_ms_ = 0;
          if (home_seek_pulse_count_ >= HOME_SEEK_MAX_PULSES) {
            enterFault("M3 home contact seek pulse budget exhausted");
          } else {
            enterFault("M3 home contact seek timed out");
          }
          break;
      }
      break;
    }

    case PressureState::HOME_RETRACT_AFTER_TOUCH:
      motorLift();
      if (now - home_surface_retract_started_ms_ >= HOME_SURFACE_RETRACT_MS ||
          liftHomeActive()) {
        motorStop();
        setDriverEnabled(false);
        home_tune_pulse_count_ = 0;
        home_seek_pulse_active_ = false;
        home_seek_active_pulse_ms_ = 0;
        home_seek_pulse_started_ms_ = 0;
        home_seek_last_pulse_ended_ms_ = now;
        setState(PressureState::HOME_TUNE_FORCE);
      }
      break;

    case PressureState::HOME_TUNE_FORCE: {
      if (!statusFlag(STATUS_CS1238_ONLINE)) {
        enterFault("CS1238 lost during home force tune");
        break;
      }

      // Stop at the lower edge of the 30–40 g hold band. The filtered hold
      // controller can then settle/release from inside its no-drive band.
      const long tune_threshold =
          TARGET_FORCE_RAW_DELTA - CONTACT_READY_TOLERANCE_RAW;
      const toolhead::ContactSeekLimits limits{
          HOME_TUNE_PULSE_MS, HOME_TUNE_SETTLE_MS,
          HOME_TUNE_MAX_PULSES, HOME_TUNE_TIMEOUT_MS};
      const toolhead::ContactSeekStatus tune_status{
          engage,
          new_filtered_sample_,
          normalizedForceDelta(),
          tune_threshold,
          now,
          state_started_ms_,
          home_seek_pulse_active_,
          home_seek_pulse_started_ms_,
          home_seek_last_pulse_ended_ms_,
          home_tune_pulse_count_};

      switch (toolhead::decideContactSeekAction(tune_status, limits)) {
        case toolhead::ContactSeekAction::WAIT:
          break;
        case toolhead::ContactSeekAction::START_PULSE:
          motorDrive(SEEK_USES_IN1_PWM, HOME_SEEK_PWM);
          home_seek_pulse_started_ms_ = now;
          home_seek_active_pulse_ms_ = HOME_TUNE_PULSE_MS;
          home_seek_pulse_active_ = true;
          break;
        case toolhead::ContactSeekAction::STOP_PULSE:
          motorStop();
          setDriverEnabled(false);
          home_seek_pulse_active_ = false;
          home_seek_active_pulse_ms_ = 0;
          home_tune_pulse_count_++;
          home_seek_pulse_count_++;
          home_seek_last_pulse_ended_ms_ = now;
          break;
        case toolhead::ContactSeekAction::CONTACT_FOUND:
          motorStop();
          setDriverEnabled(false);
          home_seek_pulse_active_ = false;
          home_seek_active_pulse_ms_ = 0;
          m3_force_acquired_ = true;
          last_force_correction_ms_ = now;
          setState(PressureState::HOLD_FORCE);
          break;
        case toolhead::ContactSeekAction::CANCELLED:
          motorStop();
          setDriverEnabled(false);
          home_seek_pulse_active_ = false;
          home_seek_active_pulse_ms_ = 0;
          setState(PressureState::CLEARANCE_LIFT);
          break;
        case toolhead::ContactSeekAction::LIMIT_REACHED:
          motorStop();
          setDriverEnabled(false);
          home_seek_pulse_active_ = false;
          home_seek_active_pulse_ms_ = 0;
          if (home_tune_pulse_count_ >= HOME_TUNE_MAX_PULSES) {
            enterFault("M3 home force-tune pulse budget exhausted");
          } else {
            enterFault("M3 home force-tune timed out");
          }
          break;
      }
      break;
    }

    case PressureState::SEEK_CONTACT:
      if (!engage) {
        // Normal M5 first proves the no-contact release band, then adds an
        // explicit air-gap pulse. Do not treat a timed boot lift as proof of
        // normal pen clearance.
        motorStop();
        setDriverEnabled(false);
        setState(PressureState::RELEASE_TO_CLEAR);
        break;
      }
      motorSeek();
      if (new_filtered_sample_ && normalizedForceDelta() >= CONTACT_RAW_DELTA) {
        motorStop();
        setDriverEnabled(false);
        m3_force_acquired_ = true;
        setState(PressureState::HOLD_FORCE);
      } else if (now - state_started_ms_ >= SEEK_TIMEOUT_MS) {
        enterFault("seek timeout; no contact found");
      }
      break;

    case PressureState::HOLD_FORCE: {
      if (!engage) {
        motorStop();
        setDriverEnabled(false);
        setState(PressureState::CLEARANCE_LIFT);
        break;
      }
      if (!statusFlag(STATUS_CS1238_ONLINE)) {
        enterFault("CS1238 lost during M3 force acquisition");
        break;
      }
      if (!m3_force_acquired_) {
        if (new_filtered_sample_ &&
            normalizedForceDelta() >=
                TARGET_FORCE_RAW_DELTA - CONTACT_READY_TOLERANCE_RAW) {
          m3_force_acquired_ = true;
        } else if (now - m3_started_ms_ >= M3_FORCE_ACQUIRE_TIMEOUT_MS) {
          enterFault("M3 force acquisition timed out");
          break;
        }
      }
      if (hold_correction_pulse_active_) {
        if (now - hold_correction_pulse_started_ms_ >=
            HOLD_CORRECTION_PULSE_MS) {
          motorStop();
          setDriverEnabled(false);
          hold_correction_pulse_active_ = false;
          last_force_correction_ms_ = now;
        }
        break;
      }

      if (!new_filtered_sample_) {
        break;
      }

      const long force = normalizedForceDelta();
      const long error = TARGET_FORCE_RAW_DELTA - force;
      const bool above_hold_band = error < -CONTACT_READY_TOLERANCE_RAW;
      const bool below_hold_band = error > CONTACT_READY_TOLERANCE_RAW;
      // Correct an over-force reading immediately, rather than waiting up to
      // the normal cadence and risking the 60 g guard while the mechanics
      // settle. Low force uses the slower cadence to avoid hunting.
      const bool correction_due = above_hold_band ||
                                  (below_hold_band &&
                                   now - last_force_correction_ms_ >=
                                       CS1238_CORRECTION_PERIOD_MS);
      if (!correction_due) {
        motorStop();
        setDriverEnabled(false);
        break;
      }

      if (above_hold_band) {
        motorDrive(LIFT_USES_IN1_PWM, HOLD_CORRECTION_PWM);
      } else {
        motorDrive(SEEK_USES_IN1_PWM, HOLD_CORRECTION_PWM);
      }
      hold_correction_pulse_started_ms_ = now;
      hold_correction_pulse_active_ = true;
      break;
    }

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
      if (MECHANICAL_PRELOAD_MODE && liftHomeActive()) {
        motorStop();
        setDriverEnabled(false);
        setState(PressureState::LIFTED);
        break;
      }
      motorLift();
      if (now - state_started_ms_ >= PEN_CLEAR_EXTRA_LIFT_MS) {
        motorStop();
        setDriverEnabled(false);
        if (MECHANICAL_PRELOAD_MODE) {
          // The 100 ms motion is the mechanical air-gap operation. The
          // moving-average force loop is used only after the next M3 preload.
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

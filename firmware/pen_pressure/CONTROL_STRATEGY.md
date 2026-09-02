# Toolhead Control Strategy

## Inputs

- `ENGAGE`: derived from grblHAL M3/M5 output.
- Load-cell force through HX711.
- Position/reference data through TMAG5273.
- Planned `GP2` LIFT-home switch for an occasional absolute lift reference.

## Output

Bidirectional PWM or phase/enable command to the DRV8833 driving the 6 V N20
threaded gearmotor.

## Planned state machine

This is the commissioning-gated target behavior. The current firmware must not
claim these thresholds or positions until T-01G and T-01H provide their measured
inputs.

1. `BOOT`: initialize outputs in a safe state and validate sensors.
2. `LIFT_HOME`: on boot, recovery, or an explicit service request only, retract
   to the `GP2` switch reference; ignore force-control demand.
3. `PEN_CLEAR`: the normal `M5` state. Retract until the filtered force returns
   to the measured no-contact release band, then apply one bounded, calibrated
   extra lift pulse to create clearance above the paper.
4. `SEEK_CONTACT`: descend with bounded command until force threshold.
5. `HOLD_FORCE`: regulate contact force.
6. `FAULT`: stop or retract according to the verified safest mechanical response.

`PEN_CLEAR` is not an absolute actuator position. Its load-cell transition
proves that the pen has released the paper; the measured clearance pulse then
creates the required travel gap. `LIFT_HOME` is the absolute position reference
used at startup and recovery. Do not make normal high-cycle `M5` motions travel
to the home switch.

## Interchangeable writing tools and preflight

The intended toolhead accepts pens, markers, and pencils with different tip
heights. It therefore does **not** depend on one shared vertical pen-tip datum
for normal contact and release control. The load cell distinguishes only the
two operational conditions: `CONTACT` when the filtered residual crosses
`F_contact_on`, and `CLEAR` when it remains below `F_release_off`.

It cannot measure an absolute air gap while the tip is unloaded. After each
tool change, a planned P100 toolhead preflight must: run `LIFT_HOME`, take the
RAM-only no-contact baseline, seek the actual paper at limited force, perform
normal `PEN_CLEAR`, and verify that the result returns to the clear band. It
must fault rather than permit plotting if contact, release, or the allowed
travel/force bounds are not achieved. The preflight proves this installed tool
can contact and release the current paper; it does not establish an exact tip
height or clearance distance.

The saved force conversion and safety limits may be shared only after they
pass scale checks. `F_target` and the accepted clearance-pulse bounds must be
validated for each pen/pencil type; they are not inferred automatically from
the no-contact reading.

## M3/M5 force transitions

The M3/M5 input requests a mode; it does not directly set N20 polarity or a
fixed motor duration.

- `M3` requests `SEEK_CONTACT`. Start from `PEN_CLEAR`, descend slowly, and
  declare contact only after the filtered force crosses `F_contact_on`.
- `M5` requests `PEN_CLEAR`. Retract until the filtered force stays below
  `F_release_off` for the configured debounce interval, then issue the bounded
  `t_clear`/pulse command and stop the actuator.
- `F_contact_on` and `F_release_off` are distinct hysteresis thresholds. Both
  must be derived from the installed, signed load-cell force units and current
  no-contact residual; raw HX711 zero is not a valid threshold.

The T-01H characterization test must establish `F_contact_on`,
`F_release_off`, debounce, the clearance-pulse bound, and the resulting pen-tip
clearance. If release is not observed before the configured command/travel
limit, enter `FAULT`; do not continue retracting toward the home switch during
an ordinary M5.

## Calibration profile and boot baseline

After E-07, T-01E, and T-01H pass, commit one versioned, checksummed
nonvolatile calibration profile through an explicit local service action. The
profile includes the accepted force conversion/slope, signed direction,
`F_contact_on`, `F_release_off`, `F_target`, `F_max`, debounce, correction-pulse
bounds, and M5 clearance-pulse bounds. Never write it as a side effect of a
normal M3/M5 cycle or boot.

After each verified `LIFT_HOME`, collect a short no-contact HX711 baseline in
RAM. Use that temporary residual only to compensate startup drift. It must not
replace the stored calibration profile. Reject force control and report a fault
if the stored profile is absent, has a bad checksum/version, or the startup
baseline is implausible/noisy under the T-01I acceptance limits.

## Controller development order

1. Open-loop motor direction and travel limits.
2. Sensor acquisition and calibration.
3. State transitions and timeouts.
4. Contact-seek profile.
5. P/PI force controller.
6. Disturbance and bed-rotation tests.
7. Only then consider more complex PID terms or feed-forward.

## Provisional force-filter and speed policy

The N20/lead-screw mechanism is a coarse actuator, so the toolhead must not
continuously chase individual HX711 readings during normal X/Y drawing. That
would add vibration and limit drawing speed without improving the line.

Use a two-stage engage profile instead:

1. Use bounded coarse down pulses while the pen is clear of the surface.
2. Near contact, use smaller 10-20 ms pulses and a filtered force residual.
3. After the force enters the target band, stop the N20 and draw with the
   lead screw mechanically holding position.
4. While drawing, sample force at the measured HX711 rate but correct only
   after the filtered value has left a deliberately wide deadband for multiple
   samples. Do not make a motor correction for ordinary sample noise.

The filter should reject a transient without adding unnecessary delay: take
three consecutive ready samples after an actuator pulse, use their median to
reject a spike, then apply a light exponential moving average to successive
median values. "Mean" and "average" are equivalent; the median-before-average
combination is more robust than a plain mean when the motor injects a single
mechanical/electrical transient.

E-08 measured 179 samples in each 15-second stationary window, or about
11.93 Hz. Raw stationary peak-to-peak noise was 300-484 counts and standard
deviation was 69-121 counts. Therefore use a three-ready-sample median (about
0.25 s) followed by light smoothing, and do not issue force corrections faster
than approximately 4 Hz after actuator settling. Initial E-07B evidence shows
that raw HX711 values include position-dependent lead-screw preload, so force
decisions must use the learned no-contact residual rather than a global raw
tare.

The control update rate must be based on measured HX711 data-ready timing. Do
not select gains using an assumed sample rate.

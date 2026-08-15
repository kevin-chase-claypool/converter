# Toolhead Control Strategy

## Inputs

- `ENGAGE`: derived from grblHAL M3/M5 output.
- Load-cell force through HX711.
- Position/reference data through TMAG5273.
- Optional hard limit switches.

## Output

Bidirectional PWM or phase/enable command to the DRV8833 driving the 6 V N20
threaded gearmotor.

## State machine

1. `BOOT`: initialize outputs in a safe state and validate sensors.
2. `LIFT`: retract to a verified safe position; ignore force-control demand.
3. `SEEK_CONTACT`: descend with bounded command until force threshold.
4. `HOLD_FORCE`: regulate contact force.
5. `FAULT`: stop or retract according to the verified safest mechanical response.

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

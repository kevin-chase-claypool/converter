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

The control update rate must be based on measured HX711 data-ready timing. Do
not select gains using an assumed sample rate.

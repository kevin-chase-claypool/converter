# grblHAL — motion control (Pi Pico 2 / RP2350)

Motion firmware for the X/Y gantry + A (theta/bed) axis. Uses **grblHAL** rather
than custom code.

## To do

1. Build/flash a **4-axis** grblHAL for the RP2350 port (X/Y/Z/A enabled — the
   default build is 3-axis).
2. `$` calibration:
   - X/Y steps-per-mm from belt pitch + microstepping.
   - **A steps-per-unit = motor steps per degree** (host emits `A` in motor
     degrees — see the integration note in `../README.md`).
   - per-axis max rate and acceleration.
3. Map the **spindle-enable output** to the pen-pressure MCU's engage/lift input
   (`M3` = engage, `M5` = lift).
4. Confirm `G4` dwell handling (host emits `G4 P<seconds>` after M3/M5 — note
   grbl/grblHAL `P` is in **seconds**).
5. Verify feed-rate scaling on a combined X/Y/**A** move vs the host's
   `sqrt(xy² + motor_deg²)/F` pacing (affects speed/timing only, not path shape).

## Contents (to be added)

- board map / pin assignments for the Pico 2 carrier
- saved `$` settings (steps/mm, steps/deg, rates, accel)
- build notes / flashing instructions

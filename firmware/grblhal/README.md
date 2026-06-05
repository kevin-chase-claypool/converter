# grblHAL - motion control on RP23CNC / RP23U5XBB

Motion firmware for the X/Y gantry plus A/theta rotating bed axis. The selected
controller is the Brookwood Design RP23CNC / RP23U5XBB 5-axis grblHAL controller
based on the RP2350, with the Ethernet adapter installed.

Use grblHAL rather than custom motion firmware. The board provides the needed
step-dir outputs, opto-isolated limit inputs, probe/control inputs, spindle and
digital outputs, USB, and Ethernet.

## To do

1. Build/flash RP23CNC-compatible grblHAL with Ethernet enabled and X/Y/Z/A
   available.
2. `$` calibration:
   - X/Y steps-per-mm from GT2 belt pitch, pulley tooth count, motor steps, and
     microstepping.
   - **A steps-per-unit = motor steps per degree** because the host emits `A` in
     motor degrees. Do not reapply the 12:1 bed pulley ratio in firmware unless
     the host `Theta ratio` is changed to `1`.
   - Per-axis max rate and acceleration.
3. Wire X/Y home switches to opto-isolated limit inputs.
4. Wire the theta index/probe sensor to a suitable input once the final homing
   scheme is chosen.
5. Map the **spindle-enable output** to the pen-pressure MCU's engage/lift input:
   `M3` = engage, `M5` = lift.
6. Confirm `G4` dwell handling. The host emits `G4 P<seconds>` after M3/M5, and
   grbl/grblHAL `P` is in seconds.
7. Verify feed-rate scaling on a combined X/Y/**A** move vs the host's
   `sqrt(xy^2 + motor_deg^2)/F` pacing. This affects speed/timing only, not path
   shape.

## Contents to add

- RP23CNC board map and pin assignments used by this build.
- Saved `$` settings: steps/mm, steps/deg, rates, acceleration, homing, and
  Ethernet settings.
- Build, flashing, and Ethernet setup notes.

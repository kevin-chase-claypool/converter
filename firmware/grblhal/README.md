# grblHAL - motion control on RP23CNC / RP23U5XBB

Motion firmware for the X/Y gantry plus A/theta rotating bed axis. The selected
controller is the Brookwood Design RP23CNC / RP23U5XBB 5-axis grblHAL controller
based on the RP2350B. The received PCB is photographically confirmed as
**RP23U5XBB V1.01**. The purchased Shopify variant is **With Assembly and
Ethernet Kits** (`48493912129751`). The basic terminal strips and headers are
installed. The W5500 module is separate and must still be seated in the
installed Wiz850io sockets after the remaining solder and continuity inspection.

Canonical board reference:
[`phil-barrett/RP23CNC`](https://github.com/phil-barrett/RP23CNC).
Check its current documentation and schematics against the received board
revision before assigning pins or applying power.

The reviewed board-specific coding and bring-up sequence is
[`UPCOMING_CODING_STEPS.md`](UPCOMING_CODING_STEPS.md).

Purchased configuration:
[Brookwood Design RP23CNC with Assembly and Ethernet Kits](https://brookwood-design-77.myshopify.com/products/ro?variant=48493912129751).

Use grblHAL rather than custom motion firmware. The board provides the needed
step-dir outputs, opto-isolated limit inputs, probe/control inputs, spindle and
digital outputs, USB, and Ethernet.

## To do

1. Complete the remaining kit inventory, magnified inspection, and continuity
   checks for the installed connectors; then seat the W5500 module in its
   sockets and pass tests E-16 and E-17.
2. Follow [`UPCOMING_CODING_STEPS.md`](UPCOMING_CODING_STEPS.md) to create a
   reproducible four-axis RP23U5XBB build with W5500 Ethernet, flash it, and
   verify USB recovery plus DHCP/Telnet operation.
3. `$` calibration:
   - X/Y steps-per-mm from GT2 belt pitch, pulley tooth count, motor steps, and
     microstepping.
   - **A steps-per-unit = motor steps per degree** because the host emits `A` in
     motor degrees. Do not reapply the 12:1 bed pulley ratio in firmware unless
     the host `Theta ratio` is changed to `1`.
   - Per-axis max rate and acceleration.
4. Wire X/Y home switches to opto-isolated limit inputs.
5. Follow
   [`HOMING_AND_MAGNETIC_CALIBRATION.md`](HOMING_AND_MAGNETIC_CALIBRATION.md)
   for the planned two-stage homing/calibration scheme: physical X/Y switches
   first, then TMAG5273/RP2040 magnetic bed-center and theta-index scans.
6. Map the **spindle-enable output** to the pen-pressure MCU's engage/lift input:
   `M3` = engage, `M5` = lift.
7. Confirm `G4` dwell handling. The host emits `G4 P<seconds>` after M3/M5, and
   grbl/grblHAL `P` is in seconds.
8. Verify feed-rate scaling on a combined X/Y/**A** move vs the host's
   `sqrt(xy^2 + motor_deg^2)/F` pacing. This affects speed/timing only, not path
   shape.

## Contents to add

- RP23CNC board map and pin assignments used by this build.
- Saved `$` settings: steps/mm, steps/deg, rates, acceleration, homing, and
  Ethernet settings.
- Build, flashing, and Ethernet setup notes.

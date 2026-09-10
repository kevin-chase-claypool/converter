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

The June bring-up sequence is preserved only as an
[archived historical plan](UPCOMING_CODING_STEPS.md). Active work belongs in
[`../../docs/project/ROADMAP.md`](../../docs/project/ROADMAP.md).

Purchased configuration:
[Brookwood Design RP23CNC with Assembly and Ethernet Kits](https://brookwood-design-77.myshopify.com/products/ro?variant=48493912129751).

Use grblHAL rather than custom motion firmware. The board provides the needed
step-dir outputs, opto-isolated limit inputs, probe/control inputs, spindle and
digital outputs, USB, and Ethernet.

## Current status and next work

The four-axis XYZA USB baseline passed F-01, and installed A/Y motion evidence
is recorded in the roadmap and test plan. The remaining controller work is not
duplicated here: use the roadmap for task status and the test plan for pass
conditions. The active priorities are F-02 revalidation with a default
converter file, F-05 M3/M5 behavior, F-08 PRB/G38 feasibility, X calibration,
and M-06 combined X/Y/A motion.

**A convention:** A is motor-shaft degrees; the converter applies the 12:1
ratio. Controller steps-per-unit must not apply that ratio a second time.

## Magnetic registration candidate

- Candidate build options: [`config/homing-candidate.md`](config/homing-candidate.md)
- Controller macro and ioSender setup: [`macros/README.md`](macros/README.md)
- Full design and commissioning gates:
  [`HOMING_AND_MAGNETIC_CALIBRATION.md`](HOMING_AND_MAGNETIC_CALIBRATION.md)

The baseline UF2 is unchanged. The 2026-09-10 candidate passed direct and
actual GP27/U3 motor-inert PRB/G38 transition checks, so the blue return is now
at `PRB`. It does not authorize P100 motion: macro/parameter semantics, the
normal-status interval, and all Q3/Q4 commissioning gates remain open.

## Current records

- [`config/build-record.md`](config/build-record.md): build provenance and
  installed baseline configuration.
- [`HOMING_AND_MAGNETIC_CALIBRATION.md`](HOMING_AND_MAGNETIC_CALIBRATION.md):
  P100 design and commissioning gates.
- [`../../docs/testing/TEST_PLAN.md`](../../docs/testing/TEST_PLAN.md): formal
  controller and motion acceptance conditions.
- [`../../docs/hardware/WIRING_TABLE.md`](../../docs/hardware/WIRING_TABLE.md):
  verified signal assignments and wiring status.

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
converter file, F-08 PRB/G38 feasibility, X calibration, and M-06 combined
X/Y/A motion.

F-05 M3/M5 behavior is now demonstrated. The RP23CNC spindle `ENA` output is
active-high by default, which drove the toolhead's active-low optocoupler input
on at idle and made the pen dive at power-up. The controller sets `$16=1`
(invert spindle enable) to correct it, so `M3` engages and `M5` lifts, with the
pen-up fail-safe preserved. See [`config/machine-settings.md`](config/machine-settings.md)
and the 2026-09-23 F-05 lab note. `F-05A`, the `P115`/`PRB` acknowledgement,
passed on 2026-09-29.

**A convention:** A is motor-shaft degrees; the converter applies the measured 12.0332:1
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

`macros/P115.macro` is the normal-print GP27 acknowledgement and is installed on
the controller; F-05A ran its `Q0`/`Q1` paths against the installed build on
2026-09-29. It performs bounded `PRB` polling only; its strict, `Q7`, and `W1`
warn-only modes never command an axis, Aux0, M3, or M5, while the opt-in `W2`
recover mode may issue one `M5` fail-safe lift on timeout. The converter still
ships the handshake off by default.

`macros/P116.macro` is the manual **PEN UP + PARK** command for an ioSender
button: `M5` plus `G65 P115 Q0`, the `M65 P0` full-retract request to the GP2
lift-home switch, `G65 P111` for physical X/Y home, and the
`G53 G0 X-10 Y-436` off-bed park. The home is mandatory: the first version
parked without one and drove the gantry into the `-Y` end on 2026-09-30, because
an unhomed controller has no machine frame and no soft-limit envelope, so its
`G53` move travelled the full commanded distance from an unknown position. See
[`macros/README.md`](macros/README.md).

## Current records

- [`config/build-record.md`](config/build-record.md): build provenance and
  installed baseline configuration.
- [`config/machine-settings.md`](config/machine-settings.md): verified `$`
  settings, including `$16=1` for the spindle-enable invert.
- [`HOMING_AND_MAGNETIC_CALIBRATION.md`](HOMING_AND_MAGNETIC_CALIBRATION.md):
  P100 design and commissioning gates.
- [`../../docs/testing/TEST_PLAN.md`](../../docs/testing/TEST_PLAN.md): formal
  controller and motion acceptance conditions.
- [`../../docs/hardware/WIRING_TABLE.md`](../../docs/hardware/WIRING_TABLE.md):
  verified signal assignments and wiring status.

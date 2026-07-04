# Test Plan

## Rules

- Start with current-limited bench supplies.
- Test one subsystem at a time.
- Keep the pen and mechanics disconnected during initial motor tests.
- Record actual settings, instruments, firmware commit, result, and evidence.
- A failed test is a result; do not tune around it without documenting the change.
- Promote connection status in `docs/hardware/WIRING_TABLE.md` only after the
  corresponding test passes.

## Phase 1 bench worksheet

| ID | Test | Expected result | Actual result | Evidence |
|---|---|---|---|---|
| E-01 | Confirm each stepper coil pair with ohmmeter | Black/green and red/blue pairs | TBD | TBD |
| E-02 | Record TB6600 labels and switch tables | Three identical, readable units | TBD | TBD |
| E-03 | Check STEP/DIR input behavior | Compatible with RP23CNC outputs | TBD | TBD |
| E-04 | Set driver current conservatively | At or below 1.5 A/phase convention | TBD | TBD |
| E-05 | Measure N20 no-load current at 6 V | Stable and within supply/module range | TBD | TBD |
| E-06 | Measure current-limited actuator stall current | Below verified DRV8833 safe limit | TBD | TBD |
| E-07 | Calibrate load cell with known masses | Repeatable slope and zero | TBD | TBD |
| E-08 | Measure HX711 samples/s and noise | Sufficient for chosen loop bandwidth | TBD | TBD |
| E-09 | Read TMAG5273 through intended wiring | Stable field/position signal | TBD | TBD |
| E-18 | Verify RP2040/TMAG5273 magnetic adapter | Qwiic readings are stable; USB diagnostics are readable; the `A_HOME` output driver is electrically compatible with the selected RP23CNC input before connection | TBD | TBD |
| E-10 | Verify all rails and common references | No overvoltage or unintended backfeed | TBD | TBD |
| E-11 | Inspect and bench-test MEISHILE S-120-12 supply | Rating label photographed; terminals 1-7 match L, N, earth, -V, -V, +V, +V; approximately 12 V no-load output; +V ADJ range and protective-earth bonding documented | TBD | TBD |
| E-12 | Measure system 12 V current and supply temperature under motion load | Adequate current/thermal margin below the supply's 10 A, 120 W listing rating | TBD | TBD |
| E-13 | Verify supply protection and certification claims from markings/manual | Only protections and certifications printed on the unit or supported by manufacturer documentation are accepted | TBD | TBD |
| E-14 | Configure B085T73CSD buck before load connection | Input/output labels and polarity verified; output adjusted to 6.0 V using a calibrated multimeter; onboard display error recorded | TBD | TBD |
| E-15 | Characterize B085T73CSD buck with the actuator | 6 V remains stable; peak current stays below tested capacity with margin; ripple and temperature are acceptable during seek, hold, lift, and current-limited stall | TBD | TBD |
| E-16 | Inventory RP23CNC Assembly and Ethernet Kits | Purchased variant, PCB revision, connectors, Ethernet components, and missing/damaged parts recorded | TBD | TBD |
| E-17 | Inspect completed RP23CNC soldering | Correct orientation, complete joints, no bridges, no opens, and continuity/power-rail checks pass before board power | TBD | TBD |

## Firmware tests

| ID | Test | Pass condition |
|---|---|---|
| F-01 | Boot and identify firmware | Correct board/driver and recorded build |
| F-02 | Parser dry run | Converter subset accepted; invalid words error clearly |
| F-03 | Output pulse check | Correct STEP/DIR pins and polarity without drivers |
| F-04 | Limit input test | Each input reports and alarms correctly |
| F-05 | Spindle/tool output test | Deterministic output pin state: M3 = ENGAGE, M5 = LIFT, fail-safe to LIFT/OFF |
| F-06 | Settings persistence | Reboot preserves calibrated settings |
| F-07 | Four-axis configuration sanity check | X/Y/A are enabled, A is available for homing/motion, and the Z axis slot remains unused/unwired |

## Motion tests

| ID | Test | Pass condition |
|---|---|---|
| M-01 | One-axis low-speed jog | Correct direction, no stalls, acceptable heating |
| M-02 | One-axis rate ramp | Documented stable max; configured below margin |
| M-03 | X/Y dimensional calibration | Error inside project tolerance |
| M-04 | A-axis one motor revolution | 360 commanded motor degrees gives one motor revolution |
| M-05 | Bed ratio check | 4320 motor degrees gives one bed revolution for 12:1 |
| M-06 | Coordinated X/Y/A sample | Smooth motion and no lost steps |
| M-07 | Homing and limits | Repeatable X/Y home from physical switches, repeatable A home from validated `A_HOME`, and safe stop |
| M-08 | Magnetic bed-center scan | After X/Y homing, a bounded 4 in x 4 in scan locates the center magnet from opposing saturated or thresholded edges with documented repeatability |
| M-09 | Magnetic theta-index setup scan | At the measured outer radius, two full bed revolutions (`8640` A motor degrees) find two outer-magnet entry/exit pairs, validate pair spacing near `4320` A motor degrees, and compute a repeatable theta index |
| M-10 | Normal startup homing macro | ioSender sends `M5`, waits the lift dwell, sends `$H`, and grblHAL exits homed/idle with X/Y/A referenced and the pen still lifted |
| M-11 | Homing abort/fault path | Missing/inconsistent magnetic edges, sensor fault, grblHAL alarm, or unknown lift state stops the current attempt, preserves diagnostics, reports status to ioSender, and requires manual recovery before retry |

## Toolhead tests

| ID | Test | Pass condition |
|---|---|---|
| T-01 | LIFT state | Retracts reliably and stops safely |
| T-02 | Contact seek | Finds paper before timeout without excessive force |
| T-03 | Force hold | Stable force within defined error band |
| T-04 | Missing-paper fault | Seek timeout enters FAULT |
| T-05 | Overforce fault | Immediate safe response |
| T-06 | Sensor disconnect | Safe response and visible fault |

## Integrated tests

- M3 seeks contact and reaches stable force before drawing.
- M5 sets the spindle/tool output pin to the LIFT state before any travel,
  homing, or magnetic scan move.
- E-stop and reset leave the toolhead safe.
- Toolhead workload does not create measurable lost steps or unacceptable jitter.
- Normal startup homing uses X/Y switches plus the validated RP2040 `A_HOME`
  input; the setup calibration script is not required for daily homing.
- Calibration pattern dimensions, force traces, and magnetic diagnostics are
  saved for the report.

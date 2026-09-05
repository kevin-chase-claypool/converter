# Test Plan

For the recommended dependency and safety order for these tests, see
[`RECOMMENDED_TEST_SEQUENCE.md`](RECOMMENDED_TEST_SEQUENCE.md). This plan
remains the authoritative source for individual test pass conditions and
completion status.

## Rules

- Start with current-limited bench supplies.
- Test one subsystem at a time.
- Keep the pen and mechanics disconnected during initial motor tests.
- For every `E-*` test attempt, create or update a dated lab note using
  [`../report/LAB_NOTE_TEMPLATE.md`](../report/LAB_NOTE_TEMPLATE.md). Record
  the setup, procedure, readings, observed behavior, pass/fail disposition,
  and evidence.
- If code, a command sequence, or a machine configuration is used, include the
  exact version used in a fenced code block in that lab note. A file path or
  verbal description alone is not sufficient test evidence.
- Record every difficulty, failed attempt, unexpected behavior, and corrective
  action that enabled a retry or pass. A failed test is a result; do not tune
  around it without documenting the change.
- Record actual settings, instruments, firmware commit, result, and evidence.
- Promote connection status in `docs/hardware/WIRING_TABLE.md` only after the
  corresponding test passes.

## Phase 1 bench worksheet

| ID | Test | Expected result | Actual result | Evidence |
|---|---|---|---|---|
| E-01 | Confirm each stepper coil pair with ohmmeter | Black/green and red/blue motor-lead pairs | Partial | Owner hand-turn generated-voltage test confirmed all three 17HS15 motors have black/green and red/blue coil pairs on 2026-08-19. Latest wiring plan: X is the sole shielded motor run, with driver-side `A+`/`A-` black/green and `B+`/`B-` red/white (white -> motor blue); Y/A retain black/green and red/blue. Winding-resistance measurement and final X shield-bond continuity remain open. See `2026-08-19-e-01-y-stepper-coil-pair-test.md`. |
| E-02 | Record TB6600 labels and switch tables | Three identical, readable units | Partial | The B0FQ5GBNZ1 product-label image maps 8× = SW1/SW2/SW3 OFF/ON/OFF, 16× = OFF/OFF/ON, and 1.5 A = SW4/SW5/SW6 ON/OFF/ON. Initial per-axis settings: X/Y 16×, A 8×; all axes 1.5 A. Photograph/confirm all three received labels and switch numbering before treating it as verified. See 2026-08-15 E-02 lab note. |
| E-03 | Check STEP/DIR/EN input behavior | The documented common-cathode pattern (`G` to `PUL-`/`DIR-`/`ENA-`; `Stp`/`Dir`/`En` to `PUL+`/`DIR+`/`ENA+`) works without excessive input loading | Passed | Installed X/Y/A TB6600 signal test passed 2026-09-05. `ENA+` was about 5 V idle and 0 V moving; `DIR+` held opposite states for positive/negative motion; `PUL+` reached about 5.22 V during motion. See `2026-09-05-e-03-tb6600-installed-signal-response.md`. |
| E-04 | Set driver current and microstep configuration conservatively | With all drivers unpowered: X/Y 16× (`SW1 OFF`, `SW2 OFF`, `SW3 ON`); A 8× (`SW1 OFF`, `SW2 ON`, `SW3 OFF`); all 1.5 A/phase (`SW4 ON`, `SW5 OFF`, `SW6 ON`) | TBD | X/Y's 20T GT2 pulleys yield 80 steps/mm at 16×. The 12:1 A reduction produces 19,200 pulses/bed revolution at 8×; do not increase A to 16/32× unless testing demonstrates a need. |
| E-05 | Measure N20 no-load current at 6 V | Stable and within supply/module range | Passed | Owner correction: aligned unloaded N20 motion current is 0.009 A. The earlier 0.043 A toolhead reading included extra mechanical load from a lead screw that was not straight against the heat-set insert; it is retained as a historical misalignment result, not the normal unloaded baseline. The repaired DRV8833 output solder joint remained reliable. No manual stall test was performed during the original E-05 run. |
| E-06 | Measure current-limited actuator stall current | Below verified DRV8833 safe limit | Passed (bounded endpoint-stall only) | With the then-installed spring (identity and compression not recorded), the N20 was commanded to retract until it could travel no farther and pressed the LIFT_HOME switch. At 6.0 V with a 0.20 A bench-supply limit it read 0.18 A at that endpoint for approximately 30 s, repeated 10 times. This is bounded endpoint-stall evidence only; it does not measure current required to hold a selected operating preload, and it does not qualify the current 0.4 mm x 7 mm x 25 mm spring. Repeat the loaded current/hold check at a known safe compression. Temperature, rail-voltage, and long-duration endurance remain outside this test scope. |
| E-07 | Calibrate load cell with known masses | Repeatable slope and zero | Partial | USB-only HX711 testing passed communication (`hx_ready=1`). E-07B GP20/GP21 service UART and two automatic pen-tip/digital-scale contacts passed (49.4 g and 65 g). Normal Z-mechanism preload changes raw readings, so the residual approach is safe for contact detection but the coarse 50 ms final increment has not produced a repeatable force slope. Refine final approach increments before production calibration. See 2026-08-14 E-07 lab note. |
| E-08 | Measure HX711 samples/s and noise | Sufficient for chosen loop bandwidth | Passed | Two stationary 15-second GP0/GP1 HX711 windows returned 179 samples each: 11.933 Hz. Peak-to-peak noise was 300 and 484 counts; standard deviation was 69.1 and 120.5 counts. Use a three-ready-sample median (about 0.25 s) and no faster than ~4 Hz force corrections after settling. See 2026-08-14 E-08 lab note. |
| E-09 | Read TMAG5273 through intended wiring | Stable field/position signal | Passed | Corrected GP16/SDA and GP17/SCL I2C mapping passed. Far/near/return magnitudes were 0.24/7.51/7.44 mT; stationary spans were 0.25/0.28 mT. A conservative initial magnitude threshold is 3.5 mT with 1.0 mT hysteresis, pending final scan geometry. See 2026-08-14 E-09 lab note. |
| E-18 | Verify Pro Micro RP2350/TMAG5273 magnetic interface | Qwiic readings are stable; service diagnostics are readable; the `A_HOME` output driver is electrically compatible with the selected RP23CNC input before connection | Partial | PC817 circuit bench stage passed on the prior GP8/GP20/GP9 map. Repeat U1/U2/U3 and isolation tests on the current GP29/GP28/GP27 harness; actual RP23CNC terminal behavior, Qwiic readings, and installed-system test remain. The Pro Micro RP2350 is also the pen-pressure controller; there is no separate RP2040 magnetic adapter. See `docs/report/lab-notes/2026-08-10-e-18-pc817-interface-bench-test.md`. |
| E-19 | Verify E-stop/Halt input | SW1 NC-A is continuous released/open pressed; RP23CNC enters Halt and needs deliberate Reset/Unlock; no automatic movement occurs after release; NC-B remains insulated | TBD | Planned topology: `docs/hardware/ESTOP_TOPOLOGY.md` |
| E-10 | Verify all rails and common references | No overvoltage or unintended backfeed | TBD | TBD |
| E-11 | Inspect and bench-test MEISHILE S-120-12 supply | Rating label photographed; terminals 1-7 match L, N, earth, -V, -V, +V, +V; approximately 12 V no-load output; +V ADJ range and protective-earth bonding documented | Partial | With the supply feeding the HD064RT fuse block and no downstream loads reported, the block input measured 12.05 VDC and an output pair also measured 12.05 VDC. Positive/negative polarity agrees with the block markings. Meter model/accuracy, supply-terminal reading, +V ADJ range, protective-earth bonding, label photo, and loaded test remain open. See 2026-08-20 E-11 lab note. |
| E-12 | Measure system 12 V current and supply temperature under motion load | Adequate current/thermal margin below the supply's 10 A, 120 W listing rating | TBD | TBD |
| E-13 | Verify supply protection and certification claims from markings/manual | Only protections and certifications printed on the unit or supported by manufacturer documentation are accepted | TBD | TBD |
| E-14 | Verify Pololu D36V50F6 6 V regulator before load connection | Input/output labels and polarity verified; fixed output measured near 6.0 V using a calibrated multimeter; enable and power-good behavior documented if used | TBD | TBD |
| E-14B | Inspect the completed toolhead perfboard before its first 6 V connection | With no supply connected: continuity confirms GP4→IN1, GP5→IN2, GP6←`EEP` fault output, and GP7→`ULT` sleep input; no short exists across the incoming 6 V JST or the 5 V/3.3 V rails to ground; `OUT1`/`OUT2` remain isolated until the motor pair is fitted; `CTRL_GND` remains isolated from tool ground | Partial | Power and every currently wired Pro Micro logic conductor passed continuity. A 6 V bench supply at the JST powered both the DRV8833 and S7V8F5, and the Pro Micro received the correct voltage. Firmware now matches the installed ACEIRMC label mapping; E-14C is its functional check. See 2026-08-12 toolhead-power lab note. |
| E-14C | Inspect and function-check ACEIRMC DRV8833 control labels | Retain GP7→`ULT` (sleep input) and GP6←`EEP` (protection/fault output); firmware maps those physical endpoints; J2 sleep-control bridge is inspected and its state recorded; no motor attached | Partial | Functional evidence: GP7 pulsed `ULT` to about 3.3 V, GP6/`EEP` stayed about 2.98 V (no asserted fault), and the driver moved the N20 in both directions. Inspect/record J2 before calling this complete. |
| E-15 | Characterize Pololu D36V50F6 with the actuator | 6 V remains stable; peak current stays below tested capacity with margin; ripple and temperature are acceptable during seek, hold, lift, and current-limited stall | TBD | TBD |
| E-15A | Characterize toolhead-mounted Pololu S7V8F5 logic regulator | With the regulator fed from the 6 V toolhead rail, output remains 5.0 V within tolerance while RP2350, HX711, and TMAG5273 are active and while the DRV8833/N20 actuator starts, seeks, holds, and lifts; RP2350 does not reset | Passed for current motor-only configuration | With a 6.0 V bench input and the E-05 N20 motion test, DRV8833 `VM` remained near 6 V, the S7V8F5 output remained near 5 V, and the Pro Micro did not reset. HX711/TMAG loads, ripple, thermal behavior, and the upstream D36V50F6 remain separate tests. |
| E-16 | Inventory RP23CNC Assembly and Ethernet Kits | Purchased variant, PCB revision, connectors, Ethernet components, and missing/damaged parts recorded | TBD | TBD |
| E-17 | Inspect completed RP23CNC soldering | Correct orientation, complete joints, no bridges, no opens, and continuity/power-rail checks pass before board power | Passed | Magnified visual inspection found good joints and no visible bridges. With all power disconnected, both main 12 V positive-to-negative and labeled 5 V rail-to-ground checks had no continuity beep. See 2026-08-14 E-17 lab note. |

## Firmware tests

| ID | Test | Pass condition |
|---|---|---|
| F-01 | Boot and identify firmware | Correct board/driver and recorded build |
| F-02 | Parser dry run | Passed — `G21`, `G90`, zero-distance XYZA `G0`/`G1`, `M3`, `G4 P0.1`, `M5`, and `M2` each accepted. `M2` reported program end and final modal state included safe `M5`. See 2026-08-14 F-02 lab note. |
| F-03 | Output pulse check | Passed — X/Y/A each had held 0/5 V direction logic, STEP activity only during motion (about 50 mV DC-meter average), and active-low enable (5 V idle, 0 V moving). No driver, motor, or PC817 controller-side wire attached. See 2026-08-14 F-03 lab note. |
| F-04 | Limit input test | Partial — X and Y each report active only when its own NC switch is pressed, with both released inactive, in ioSender on 2026-08-22. `$5=0`; hard limits remain disabled (`$21=0`). Hard-limit alarm behavior, broken-wire response, and the unused Z/A/A-index inputs remain open. See 2026-08-22 F-04 lab note. |
| F-05 | Spindle/tool output test | Deterministic output pin state: M3 = ENGAGE, M5 = PEN_CLEAR, fail-safe to PEN_CLEAR/OFF |
| F-06 | Settings persistence | Reboot preserves calibrated settings |
| F-07 | Four-axis configuration sanity check | X/Y/A are enabled, A is available for homing/motion, and the Z axis slot remains unused/unwired |
| F-08 | Motorless RP23CNC `PRB`/G38/macro feasibility | With TB6600 signal leads and motors disconnected, the candidate build reports `PRB`, captures X entry/release with `G38.3`/`G38.5`, proves or rejects equivalent A capture and `#5064`, executes filesystem `G65 P100`, and verifies the coordinate/parameter semantics used by P100. Keep GP27 on `LIMA` until the direct-input and GP27/U3 stages pass. |

### F-08 motorless PRB/G38 procedure

This is a controller-input and firmware-feasibility test, not a motion test.
Disconnect the TB6600 `STEP`/`DIR`/`EN` signal leads and all motors. grblHAL may
then advance only its internal position counters while the RP23CNC step outputs
remain unloaded.

1. Power the RP23CNC and its isolated 12 V input section. Use a temporary dry
   contact or the already validated optocoupler-style sink between `PRB` and
   its isolated input ground. Do not drive the 12 V probe terminal from a
   3.3 V or 5 V logic output.
2. With no motion command active, verify the intended idle and asserted states
   in ioSender. `Pn:P` must appear only for the asserted probe state. Record
   the starting and final `$6` probe-inversion value; change it only if the
   observed state is reversed.
3. Confirm hard and soft limits are disabled for this bench test, unlock the
   controller if required, and select millimeters plus incremental motion:

   ```gcode
   G21
   G91
   ```

4. Start with `PRB` inactive. Send `G38.3 X10 F60`, assert `PRB` before the
   logical target is reached, and verify that the cycle ends with a successful
   `[PRB:...]` report.
5. Leave `PRB` asserted. Send `G38.5 X10 F60`, release `PRB` before the logical
   target is reached, and verify a second successful probe-coordinate report.
6. Repeat bounded inactive-to-active and active-to-inactive checks with an A
   target. Record whether the installed XYZA firmware accepts `G38.x A...`,
   stops on both transitions, and reports an A coordinate. Source-level support
   is not accepted as a substitute for this installed-build result.
7. After the direct `PRB` test passes, repeat the state and G38 checks through
   the actual Pro Micro GP27 -> PC817C U3 -> controller input path while
   preserving `CTRL_GND`/`TOOL_GND` isolation.
8. Copy the locked `P100.macro` to the controller filesystem. Verify `G65 P100
   Q1`, the expected commissioning abort for Q0/Q3/Q4, `$H` behavior in Q2,
   G53/G54 and `G10 L20` parameter semantics, and that every abort releases
   Aux0. Do not bypass either commissioning lock.
9. Send `G90`, reset the controller, and do not use the motorless test's
   internal coordinates as machine references.

Pass requires deterministic polarity, successful X transition captures,
an explicit pass/fail result for A probing, readable probe coordinates, and a
successful GP27/U3 path check. Only a later documented wiring change may move
the routed U3 return conductor from `LIMA` to `PRB`.

## Motion tests

| ID | Test | Pass condition |
|---|---|---|
| M-01 | One-axis low-speed jog | Correct direction, no stalls, acceptable heating |
| M-02 | One-axis rate ramp | Documented stable max; configured below margin |
| M-03 | X/Y dimensional calibration | Initial `$100/$101 = 80.000000` steps/mm for GT2 20T pulleys at 16 microsteps; measured error is inside project tolerance after correction |
| M-04 | A-axis one motor revolution | With 8 microsteps and `$103 = 4.444444` steps per motor-degree, 360 commanded A motor-degrees gives one motor revolution |
| M-05 | Bed ratio check | 4320 commanded A motor-degrees (19,200 pulses) gives one bed revolution for 12:1 |
| M-06 | Coordinated X/Y/A sample | Smooth motion and no lost steps |
| M-07 | Homing and limits | Repeatable X/Y machine home from physical switches, safe limit behavior, and homing configuration that excludes unused Z and magnetic A registration |
| M-08 | Magnetic bed-center centroid raster | After X/Y physical homing, P100 produces multiple valid equal-pitch X chords, rejects malformed footprints, calculates the chord-width-weighted area centroid, performs the Centroid Approach and Registration Pass, and repeatably sets G54 X0/Y0 |
| M-09 | Magnetic theta-index registration | At the measured outer radius, P100 finds two outer-magnet entry/exit pairs from one direction, validates spacing near `4320` A motor degrees, approaches the equivalent averaged index, and repeatably sets G54 A0 |
| M-10 | Full startup home and registration | One ioSender `G65 P100 Q0` command lifts, homes physical X/Y, registers center and A, returns to G54 X0 Y0 A0, and leaves the pen lifted |
| M-11 | Homing abort/fault path | Missing/inconsistent magnetic edges, sensor fault, grblHAL alarm, or unknown lift state stops the current attempt, preserves diagnostics, reports status to ioSender, and requires manual recovery before retry |

M-01 current evidence: on 2026-09-05 the A-axis motor completed an initial
bidirectional jog at `F120`; `A10` was counterclockwise, `A-10` was clockwise,
and supply current was approximately `0.44 A` with a 2 A limit. The Y axis then
moved north for `Y1` and south for `Y-1` at `F60`, with approximately `0.43 A`
reported for both moves. The X axis moved east for `X1` and west for `X-1` at
`F60`, with approximately `0.42 A` reported for both moves. After ten X
`+5`/`-5` cycles at `F60`, the physical carriage mark returned exactly to its
starting reference. After ten Y `+5`/`-5` cycles at `F60`, the physical Y
carriage mark also returned exactly to its starting reference. The A motor
pulley likewise returned to its starting position relative to the motor after
the repeat cycle set. No noticeable heating was reported at any X, Y, or A
motor or driver; all remained cold to the touch. **M-01 passed for the
conducted low-speed jog and return checks**, with the thermal observation
qualitative rather than instrumented. See
[`2026-09-05-m-01-a-axis-direction-jog.md`](../report/lab-notes/2026-09-05-m-01-a-axis-direction-jog.md).

M-02 current evidence: on 2026-09-05 the A-axis rate ramp completed cleanly at
`F180`, `F240`, `F300`, `F360`, `F420`, `F480`, `F540`, and `F600`. The
mechanism returned exactly to its physical reference mark at both `F480` and
`F540` and remained cool to the touch. The measured supply current at `F480`
was approximately `0.465 A`, at `F540` approximately `0.476 A`, and at `F600`
approximately `0.485 A`. An apparent `0.5 mm` offset was later traced to the
operator moving the pulley during inspection, not to a machine repeatability
failure. The operator reported an audible speed plateau near `F500` and could
distinguish `F495` from the identical-sounding `F500`, `F540`, and `F600`
commands. The initial ioSender configuration confirmed `$113 = 500.000 deg/min`,
so commands above `F500` were planner-limited by that earlier value. The operator corrected
`$103` to `4.44444`, and a later `$$` report confirms it. M-04 then passed the
one-motor-revolution check with `A360 F300` in both directions. With `$113=5000`
and `$123=10 deg/sec^2`, follow-up `A720 F5000` and `A1440 F5000` moves were
smooth but dominated by ramp-up/ramp-down; they do not select a final plotting
acceleration. The same forward/reverse check passed at `$123=25` and `$123=50`
without reported stalls or return-position errors; current and temperature were
not recorded for those steps. A later test at `$113=15000`, `F15000`, and
`$123=300` was also reported smooth in both directions, but exact travel,
current, temperature, and return position were not recorded. A later
`$113=40000` / `F40000` forward-reverse test reportedly returned exactly to the
mark in both directions; it was an acceleration-profile result, not sustained
`40000 deg/min` validation. M-02 remains in progress for quantitative evidence,
a pen-loaded check, M-05 bed-ratio
verification, and then the X/Y rate checks. See
[`2026-09-05-m-02-a-axis-rate-ramp.md`](../report/lab-notes/2026-09-05-m-02-a-axis-rate-ramp.md).

## Toolhead tests

| ID | Test | Pass condition |
|---|---|---|
| T-01 | Toolhead lift/clear and motor/preload physical capability | Every applicable T-01A through T-01J sub-test below is recorded. The full `LIFT_HOME` and normal `PEN_CLEAR` motions stay inside the measured mechanical and electrical envelope; retracts repeatably without a fault, hard-stop contact, unacceptable drift, or an uncommanded pen contact. |
| T-02 | Contact seek | Finds paper before timeout without excessive force |
| T-03 | Force hold | After E-06, E-07, E-08, T-01, and T-02: a bounded pulse-based P/PI trim loop holds a calibrated target force through (a) stationary contact, (b) X/Y translation, and (c) progressively faster constant A rotation. Define the measured error band before the test; log mean, 95th-percentile absolute error, peak force, pulse count/reversals, and faults. No sustained limit cycle, hard-force trip, or uncommanded contact loss is allowed. Demonstrate that the dominant bed-rotation disturbance is within the measured loop bandwidth; otherwise reduce speed or add mechanical compliance before considering feed-forward. |
| T-04 | Missing-paper fault | Seek timeout enters FAULT |
| T-05 | Overforce fault | Immediate safe response |
| T-06 | Sensor disconnect | Safe response and visible fault |

### T-01 motor/preload physical-capability sub-tests

**Purpose:** establish the measured mechanical, force, motor, and electrical
limits that the pressure controller must obey. This is a commissioning test,
not permission to change a firmware constant from a nominal spring dimension.
The previously documented spring candidate was nominally 0.027 in wire x
0.295 in outside diameter x 1.19 in free length. It was replaced on
2026-09-04. The currently installed candidate is owner-reported as 0.4 mm
wire diameter x 7 mm outside diameter x 25 mm free length. Measure the
installed part rather than assuming either catalogue/owner-reported set of
dimensions is exact.

**Safety gates:** T-01A may be performed unpowered. E-05 and the basic
open-loop direction portion of T-01 must pass before powered motion. E-06
(current-limited loaded-actuator test), E-15 (loaded 6 V rail), and E-07
(repeatable force calibration) must pass before endurance, force-envelope, or
force-control conclusions are accepted. Use a guarded travel range that stops
short of both the spring's solid height and the mechanism's hard stops. Keep a
digital scale or equivalent calibrated force fixture under the pen for every
loaded test; never hand-stall the actuator.

**Previous LIFT datum superseded (2026-09-04):** the prior spring candidate
had `L_free = 1.190 in` and a proposed `x_lift = 0.535 in`, yielding
`L_lift = 0.655 in`; the then-installed pen tip was measured 0.1885 in above
the bed. Those values are historical to the removed spring and are not
approved for the current assembly. The new 0.4 mm x 7 mm x 25 mm candidate has
no approved LIFT compression, clearance, or safe travel endpoint yet. Re-run
T-01A before powered motion into preload. Interchangeable pens and pencils
may still sit at different clamp heights.

**Force-path terminology (2026-09-04):** in the current geometry, the spring
is not assumed to be compressed while the pen is floating clear of the paper.
When the pen contacts the paper, the paper reaction drives the pen carriage
upward and the carriage compresses/loads the spring against the N20-side cup or
housing. Use `x_contact` and `F_contact` (the writing-force condition) for this
case. Use `F_preload` only if an intentional off-paper assembly compression is
actually measured. If the M4 heat-set/leadscrew carries the axial load without
the spring length changing, the spring is being bypassed and the mechanism is
not acting as a series-compliant force path; correct that before claiming
spring-based force control.

| Sub-test | Procedure and values to record | Pass condition / resulting control input |
|---|---|---|
| **T-01A — geometry and preload reference** | With power off, measure actual free spring length `L_free`, installed spring length at LIFT `L_lift`, at first pen contact `L_contact`, and at the greatest intended compression `L_min`. Record spring solid length `L_solid` from a manufacturer specification or a cautious dedicated compression measurement. Record the direction of compression as the motor retracts. Calculate `x = L_free - L`, `x_lift`, `x_contact`, `x_max`, and the remaining solid-height margin `L_min - L_solid`. Photograph/mark the repeatable LIFT reference. | Every length, force direction, and safe travel endpoint is known; `L_min` remains above `L_solid` with a documented mechanical margin. These values set the firmware travel soft limits and identify whether retract increases or decreases preload. |
| **T-01B — installed spring force curve and hysteresis** | At no fewer than five evenly spaced compression points from the least to greatest intended compression, measure force with the spring installed in its real force path. Include the paper/scale contact condition if the spring is only loaded when the carriage is pushed upward by paper. Run at least three increasing/decreasing cycles, returning to the verified LIFT reference between cycles. Record applied force, length/position, load-cell raw reading, and any guide or linkage motion. Fit or tabulate the local force curve; do not assume a single linear rate if the mechanism is nonlinear. | Determine `F_contact = F(x_contact)` and, only if off-paper compression is intentionally present, `F_preload = F(x_lift)`, plus `F_min`, `F_max`, effective spring rate or lookup table, and increasing/decreasing-path hysteresis. The intended writing-force range is inside the measured range without coil bind, force-path bypass, or linkage slip. |
| **T-01C — static motor hold at contact force** | After E-06 and E-15, place the pen on a paper or digital-scale fixture and slowly move into contact until the selected `F_contact` is reached. Do not press the LIFT_HOME switch. Record carriage/spring position, pen force, rail voltage, motor/driver current, and motor/driver/regulator temperature at the start and after a defined hold dwell. Repeat once with the driver disabled only if the mechanism is guarded, to determine whether the leadscrew is self-locking and whether the carriage back-drives. The prior 0.18 A result was measured while pressing the LIFT_HOME switch at the travel endpoint and is not a T-01C contact-force measurement. | T-01C remains open until the selected contact force is held for the defined dwell with position/force/rail/current/temperature and drift recorded. If force remains stable with the motor disabled, the leadscrew is mechanically holding the load and active motor hold current may be near zero; if force decays, record the enabled hold current required to prevent back-drive. The endpoint-stall result remains separate bounded E-06 evidence. |
| **T-01D — retract motion reserve** | Starting from the greatest intended opposing-spring force, increase retract pulse width/PWM or speed in small documented steps. At each setting record retract time, current peak, position reached, force/clearance, and any driver fault. At the selected setting, perform at least 30 full `PEN_CLEAR`-to-work-range-to-`PEN_CLEAR` cycles with the normal payload. | Select a retract command below the first unreliable setting, with documented force/current/thermal margin. All 30 cycles reach `PEN_CLEAR` without a fault, hard-stop contact, lost reference, or uncommanded pen contact. This sets maximum retract effort and the minimum M5 dwell; it does not validate `LIFT_HOME`. |
| **T-01E — command-to-force and pulse response map** | Characterize the actuator's global motion limits with a representative pen or guarded force fixture: small up/down pulses at the intended preload and low/nominal/high force regions. Record command direction, PWM, pulse width, initial/final position, initial/final force, response delay, settle time, overshoot, and reversal/backlash. Do not assume the force change per pulse is universal across tools. Each new pen, marker, or pencil receives a short bounded response check during T-01J rather than repeating the full map unless it falls outside the established range. | Establish global minimum repeatable pulse, maximum safe pulse, directional backlash, and settle delay for the actuator. Record any per-tool force-response correction needed by T-01J. The load cell remains the force authority; these measurements bound pulse duration, correction rate, deadband, and anti-windup behavior for T-03. |
| **T-01F — control-envelope record** | Consolidate global actuator values and per-tool settings in the lab note: `L_free`, `L_solid`, `L_lift`, `L_contact`, `x_lift`, `x_max`, solid-height margin, force curve/rate, `F_preload`, global friction/stiction threshold, backlash, global minimum/maximum pulse, retract time, maximum tested current, rail-voltage minimum, temperatures, hold drift, selected dwell, and each tool's `F_target`, contact/release thresholds, and any bounded pulse override. State the source/test date for each value. | The table supplies every non-TBD physical value needed to configure force limits, travel limits, seek timeout, pulse bounds, correction cadence, LIFT dwell, and the T-03 acceptance band without pretending that one pen's pulse-to-force curve applies to every tool. Any unknown or failed value remains a commissioning gate rather than a firmware assumption. |
| **T-01G — LIFT-home switch** | Before connecting to the Pro Micro, meter-check the selected terminals: open when released and closed when the actuator flag presses the switch. Then wire the dry contact only between `GP2` and `TOOL_GND`, enable `INPUT_PULLUP`, and record at least ten slow retract cycles. Record trigger/release position relative to the **current measured LIFT compression**, repeatability, debounce behavior, and timeout behavior if no trigger occurs. | All ten cycles report `GP2` LOW only when the moving-carriage flag presses the fixed switch, at a repeatable LIFT position before the separate mechanical backstop. A missing or implausible transition faults/stops retraction. This input is a position reference, not a hard stop; do not use it until the current spring's solid-height and backstop margins are verified. |
| **T-01H — M5 release and clearance pulse** | With E-07 force calibration active and a scale/paper fixture under the pen, start from stable contact and command normal M5. Record the signed filtered force trace, `F_contact_on`, `F_release_off`, release debounce, retract command, extra clearance-pulse PWM/duration, pen-tip gap after stopping, and any mark/drag during a representative pen-up travel move. Repeat at least 30 M3-contact/M5-clear cycles. `LIFT_HOME` switch contact is not expected during this test. | `F_contact_on` and `F_release_off` have a measured hysteresis margin; release is detected repeatably before the pulse; the calibrated pulse leaves the pen clear throughout the representative travel without contacting the distant switch; all 30 cycles complete without fault, drag, or uncommanded paper contact. These values authorize normal high-cycle M5 `PEN_CLEAR` behavior. |
| **T-01I — saved force profile and startup baseline** | After E-07, T-01E, and T-01H produce accepted values, record a versioned calibration profile containing the load-cell slope/direction, `F_contact_on`, `F_release_off`, `F_target`, `F_max`, debounce, pulse bounds, and clearance-pulse command. Commit it only through an explicit local service action and record its identifier/checksum. Perform at least five complete power cycles. On each boot, run `LIFT_HOME`, verify the profile identifier/checksum before force control is enabled, collect a fresh no-contact baseline in RAM, and then use the scale fixture to check one low and one nominal commanded force. Query the stored profile again after every cycle. | All five boots reload the identical valid profile; each RAM baseline is within the documented no-contact/noise acceptance band; the low and nominal scale checks stay within their documented force tolerance; invalid/missing profile or implausible baseline leaves force control disabled/faulted; and the stored identifier/checksum remains unchanged until another explicit service calibration commit. This authorizes the profile for normal operation, not an automatic re-calibration. |
| **T-01J — interchangeable-tool contact and clear preflight** | For each intended pen, marker, or pencil type and its allowed clamp-height range, run: `LIFT_HOME`; no-contact baseline; guarded low-force seek to the current paper/scale fixture; a short bounded response check using the global T-01E pulse limits; normal M5 release plus clearance pulse; then a representative pen-up travel move. Record tool identity, clamp setting, first-contact force, seek travel/time, selected `F_target`, `F_contact_on`, `F_release_off`, any per-tool pulse override, clearance-pulse command, post-clear force band, mark quality, and any drag. Repeat enough M3/M5 cycles to expose stiction or missed release; never use normal M5 to reach the home switch. | Every tested tool reaches contact before its seek limit, stays below `F_max`, releases into the clear band, and completes representative pen-up travel without drag or switch contact. The load cell closes the force loop; no universal pulse-to-force curve is required. Record a separate approved target-force/clearance setting for each tool type, with a per-tool pulse override only when the bounded response check requires it. A failure leaves that tool/profile combination disabled pending correction. |

For every T-01 sub-test, use the lab-note template and include the exact test
sketch/build, supply current limit, PWM/pulse settings, instruments, raw
readings, photos, and unsuccessful attempts. Do not start T-02 or tune T-03
until T-01F identifies a safe working envelope, T-01G establishes a repeatable
`LIFT_HOME` reference, T-01H establishes normal M5 `PEN_CLEAR` behavior,
T-01I verifies the saved profile plus RAM-only startup baseline, and T-01J
establishes the selected interchangeable-tool settings.

**Historical endpoint-stall observation (2026-08-30; owner clarification
2026-09-04):** with a spring installed, the owner reported approximately
0.019-0.050 A during retraction. The 0.18 A reading occurred only after the
motor retracted until it could travel no farther and pressed the LIFT_HOME
switch. It is an endpoint-stall current, not the current required to hold a
selected operating preload; no T-01C preload hold was measured. The spring
identity and compression at that test were not recorded. These observations do
not qualify the current 0.4 mm x 7 mm x 25 mm spring; repeat T-01A and the
loaded E-06/T-01C/T-01D checks after establishing its safe compression range.
Do not use a fully compressed spring or a switch-pressed stall as a normal
operating point. The normal operating measurement is the paper-contact force,
not this switch-pressed endpoint current. See
[`2026-08-30-t-01-preload-current-observation.md`](../report/lab-notes/2026-08-30-t-01-preload-current-observation.md).

## Integrated tests

- M3 seeks contact and reaches stable force before drawing.
- Normal M5 establishes `PEN_CLEAR` from the load-cell release threshold plus
  its calibrated clearance pulse before travel. Boot/recovery invokes the
  separate `LIFT_HOME` switch reference before machine homing or a magnetic
  scan move.
- E-stop and reset leave the toolhead safe.
- Toolhead workload does not create measurable lost steps or unacceptable jitter.
- Normal startup uses X/Y switches plus the full controller-resident center
  raster and A registration; no Windows converter or separate host script is
  in the real-time sequence.
- Calibration pattern dimensions, force traces, and magnetic diagnostics are
  saved for the report.

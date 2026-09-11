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
| E-07 | Calibrate load cell with a scale-force transfer test | A repeatable signed conversion from settled filtered HX711 delta to grams-force, with zero, residual, and hysteresis bounds | Partial | USB-only HX711 testing passed communication (`hx_ready=1`). E-07B GP20/GP21 service UART and two automatic pen-tip/digital-scale contacts passed (49.4 g and 65 g). Normal Z-mechanism preload changes raw readings, so the residual approach is safe for contact detection but the coarse 50 ms final increment has not produced a repeatable force slope. Refine final approach increments before production calibration. See 2026-08-14 E-07 lab note. |
| E-08 | Measure HX711 samples/s and noise | Sufficient for chosen loop bandwidth | Passed | Two stationary 15-second GP0/GP1 HX711 windows returned 179 samples each: 11.933 Hz. Peak-to-peak noise was 300 and 484 counts; standard deviation was 69.1 and 120.5 counts. Use a three-ready-sample median (about 0.25 s) and no faster than ~4 Hz force corrections after settling. See 2026-08-14 E-08 lab note. |
| E-09 | Read TMAG5273 through intended wiring | Stable field/position signal | Passed | Corrected GP16/SDA and GP17/SCL I2C mapping passed. Far/near/return magnitudes were 0.24/7.51/7.44 mT; stationary spans were 0.25/0.28 mT. A conservative initial magnitude threshold is 3.5 mT with 1.0 mT hysteresis, pending final scan geometry. The fully wired installed toolhead recheck on 2026-09-08 again identified the device at `0x22`, read a 0.29 mT far-field vector at 28.9 C, and produced a 20-sample far-field span of 0.29 mT. See 2026-08-14 E-09 lab note. |
| E-18 | Verify Pro Micro RP2350/TMAG5273 magnetic interface | Installed active-low Aux0/U2/GP28 and GP27/U3-to-PRB transitions with real-magnet A capture | Partial | The 2026-09-10 motor-inert diagnostic passed arm/release/re-arm, local TMAG `detected=0→1→0`, and the actual GP27/U3-to-PRB state path. Real-magnet A `G38.3`/`.5` captures each returned `:1`; the blue return is at `PROBE SIG`. J1.4 measured 9.33 V released and 0.15 mV asserted relative to `CTRL_GND`. P100 macro, coordinate, and production/actuator gates remain open. See `docs/report/lab-notes/2026-09-10-e-18-motor-inert-p100-handshake.md`. |
| E-19 | Verify E-stop/Halt input | With power removed, upper NC-A `1`–`2` is continuous released/open pressed and lower NC-B is isolated/insulated. With NC-A across RP23CNC `ESTOP SIG`/`GND` and NC-compatible `$14=6` verified live, pressing SW1 enters Halt; deliberate Reset/Unlock is required after release and no automatic movement occurs. Motor/tool 12 V remains powered. | Passed | On 2026-09-08, power-off NC-A meter check beeped/continuous released and did not beep/open pressed. ioSender 2.0.47 showed `$14=6`; press produced `ALARM:10`, then twist-release → Reset → Unlock returned it to `IDLE` with no motion reported. The unused NC-B pair remains insulated; see `2026-09-08-e-19-estop-iosender-configuration.md`. |
| E-10 | Verify all rails and common references | No overvoltage or unintended backfeed | TBD | TBD |
| E-11 | Inspect and bench-test MEISHILE S-120-12 supply | Rating label photographed; terminals 1-7 match L, N, earth, -V, -V, +V, +V; approximately 12 V no-load output; +V ADJ range and protective-earth bonding documented | Partial | With the supply feeding the HD064RT fuse block and no downstream loads reported, the block input measured 12.05 VDC and an output pair also measured 12.05 VDC. Positive/negative polarity agrees with the block markings. Meter model/accuracy, supply-terminal reading, +V ADJ range, protective-earth bonding, label photo, and loaded test remain open. See 2026-08-20 E-11 lab note. |
| E-12 | Measure system 12 V current and supply temperature under motion load | Adequate current/thermal margin below the supply's 10 A, 120 W listing rating | TBD | TBD |
| E-13 | Verify supply protection and certification claims from markings/manual | Only protections and certifications printed on the unit or supported by manufacturer documentation are accepted | TBD | TBD |
| E-14 | Verify Pololu D36V50F6 6 V regulator before load connection | Input/output labels and polarity verified; fixed output measured near 6.0 V using a calibrated multimeter; enable and power-good behavior documented if used | Passed | Owner reported constant 6.05 V output with E-14 passed on 2026-09-08. |
| E-14B | Inspect the completed toolhead perfboard before its first 6 V connection | With no supply connected: continuity confirms GP4→IN1, GP5→IN2, GP6←`EEP` fault output, and GP7→`ULT` sleep input; no short exists across the incoming 6 V JST or the 5 V/3.3 V rails to ground; `OUT1`/`OUT2` remain isolated until the motor pair is fitted; `CTRL_GND` remains isolated from tool ground | Passed | Owner reported E-14B passed on 2026-09-08, closing the prior partial continuity/inspection record. See 2026-08-12 toolhead-power and 2026-09-08 toolhead-power-path lab notes. |
| E-14C | Inspect and function-check ACEIRMC DRV8833 control labels | Retain GP7→`ULT` (sleep input) and GP6←`EEP` (protection/fault output); firmware maps those physical endpoints; J2 sleep-control bridge is inspected and its state recorded; no motor attached | Passed | Owner reported E-14C passed on 2026-09-08, closing the prior J2 inspection record. Prior functional evidence: GP7 pulsed `ULT` about 3.3 V, GP6/`EEP` remained about 2.98 V, and N20 moved both directions. |
| E-15 | Characterize Pololu D36V50F6 with the actuator | 6 V remains stable; peak current stays below tested capacity with margin; ripple and temperature are acceptable during seek, hold, lift, and current-limited stall | TBD | TBD |
| E-15A | Characterize toolhead-mounted Pololu S7V8F5 logic regulator | With the regulator fed from the 6 V toolhead rail, output remains 5.0 V within tolerance while RP2350, HX711, and TMAG5273 are active and while the DRV8833/N20 actuator starts, seeks, holds, and lifts; RP2350 does not reset | Passed | The current motor-only result was supplemented by owner-reported TMAG test evidence; owner reported E-15A passed on 2026-09-08. E-15 remains the separate upstream-regulator load/ripple/current/temperature characterization. |
| E-16 | Inventory RP23CNC Assembly and Ethernet Kits | Purchased variant, PCB revision, connectors, Ethernet components, and missing/damaged parts recorded | TBD | TBD |
| E-17 | Inspect completed RP23CNC soldering | Correct orientation, complete joints, no bridges, no opens, and continuity/power-rail checks pass before board power | Passed | Magnified visual inspection found good joints and no visible bridges. With all power disconnected, both main 12 V positive-to-negative and labeled 5 V rail-to-ground checks had no continuity beep. See 2026-08-14 E-17 lab note. |

### E-07 required scale-force transfer calibration

Clamp a capped pen or other rigid non-marking dummy tool exactly as a writing
pen will be clamped. With a digital scale under the tip, gather settled
**filtered** HX711 deltas at no fewer than five gentle, known force points
covering the intended writing range. At every point record the external scale
reading in grams-force, raw HX711 value, filtered HX711 value, no-contact
baseline, and tool/clamp identity. Repeat at least three loading and unloading
cycles without side-loading the pen.

Fit and record the signed scale-force conversion, its residual error across
the intended range, and loading/unloading hysteresis. This is the required
mapping used to select contact, target, release, and hard-force thresholds; it
is not a claim that motor PWM, actuator travel, or spring compression is
linear. Reject force control if the conversion is not repeatable enough to
separate the intended writing band from contact/release noise and the hard
limit. A physical scale is required for this calibration and periodic
verification, but not for each print after an approved tool profile exists.

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
| F-08 | Motorless RP23CNC `PRB`/G38/macro feasibility | Partial pass 2026-09-10: the candidate reports `PRB`; direct and actual GP27/U3 paths captured A entry/release with `G38.3`/`G38.5`; the blue return was moved from `LIMA` to `PRB` after those stages passed. Still required: `#5064`, filesystem `G65 P100`, coordinate/parameter semantics, and the proposed 20 ms GP27 inactive interval after normal-status assertion. |

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
   Before the replacement actuator is qualified, use only
   `firmware/pen_pressure/p100_handshake_test/p100_handshake_test.ino` for
   this stage. It drives the real two-phase GP28/GP27 protocol, including the
   20 ms inactive interval before its ACK and threshold state during the second
   arm, but never configures or writes DRV8833, M3/M5, HX711, or LIFT_HOME
   pins. Verify `G65 P100 Q1` reports the ACK/release result and use the
   controlled dry-contact checks for every G38 transition. Do not run Q3/Q4
   with this diagnostic firmware.
8. Copy `P100.macro` to the controller filesystem. `G65 P100 Q1` passed on
   2026-09-11 and direct X/Y `$H` passed with the installed switches and fuses.
   Next verify `G65 P100 Q2`, the expected commissioning abort for Q0/Q3/Q4,
   G53/G54 and `G10 L20` parameter semantics, and that every abort releases
   Aux0. Do not bypass the Q0/Q3/Q4 commissioning locks.
9. Send `G90`, reset the controller, and do not use the motorless test's
   internal coordinates as machine references.

Pass requires deterministic polarity, successful X transition captures,
an explicit pass/fail result for A probing, readable probe coordinates, and a
successful GP27/U3 path check. The documented 2026-09-10 direct and
actual-path result moved the routed U3 return conductor from `LIMA` to `PRB`.
Preserve `$6=1` unless a future measured idle/asserted observation proves the
physical input polarity changed.

### F-08 result: 2026-09-10 PRB and real-magnet GP27/U3 path

The candidate build (`grblHAL 1.1f.20260908`) reported `PRB` and accepted A-axis
G38. Direct dry-contact testing established normally-open polarity with `$6=1`.
The actual motor-inert `p100_handshake_test` path then synchronized toolhead
`detected=0 -> 1 -> 0` with controller `P` blank -> red -> blank and returned:

```text
G38.3 A30 F60 -> [PRB:0.000,0.000,0.000,11.475:1]
G38.5 A30 F60 -> [PRB:0.000,0.000,0.000,13.275:1]
```

The TB6600 branch fuses were removed and no axis moved. The initial `:0` result
was caused by the diagnostic's known five-minute scan timeout, then cleared by
disarming and reacquiring the baseline. F-08 remains open for macro/parameter
and coordinate semantics; Q3/Q4 remain prohibited.

## Motion tests

| ID | Test | Pass condition |
|---|---|---|
| M-01 | One-axis low-speed jog | Correct direction, no stalls, acceptable heating |
| M-02 | One-axis rate ramp | Documented stable max; configured below margin |
| M-03 | X/Y dimensional calibration | Initial `$100/$101 = 80.000000` steps/mm for GT2 20T pulleys at 16 microsteps; measured error is inside project tolerance after correction |
| M-04 | A-axis one motor revolution | With 8 microsteps and `$103 = 4.444444` steps per motor-degree, 360 commanded A motor-degrees gives one motor revolution |
| M-05 | Bed ratio check | 4320 commanded A motor-degrees (19,200 pulses) gives one bed revolution for 12:1 |
| M-06 | Coordinated X/Y/A sample | Smooth motion and no lost steps |
| M-07 | Homing and limits | X/Y physical home passed: repeatable machine home from physical switches with Z/A excluded. A conservative X/Y software envelope is enabled; explicit near-boundary rejection/recovery remains open. |
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
`$123=4000` was also reported smooth in both directions, but exact travel,
current, temperature, and return position were not recorded. A later
`$113=40000` / `F40000` forward-reverse test reportedly returned exactly to the
mark in both directions and included a sustained-speed section at `$123=4000`;
the motor remained cool to the touch afterward, but it still needs repeated
thermal evidence. A later `$113=80000` / `F80000` forward-reverse test also
reportedly returned perfectly. The operator then reported a smooth repeat at
`$123=6000`; repeated forward/reverse cycles remained non-problematic, and both
the motor and driver remained cool to the touch. Unloaded A-axis motion is
complete through the tested settings; the X-axis rate check remains. See
[`2026-09-05-m-02-a-axis-rate-ramp.md`](../report/lab-notes/2026-09-05-m-02-a-axis-rate-ramp.md).

M-05 current evidence: on 2026-09-05, with `$103 = 4.44444` and the 12:1
bed reduction, the operator marked the bed against a fixed frame reference and
commanded `G1 A4320 F10000`, followed by `G1 A-4320 F10000` in incremental mode.
`A4320` is 12 motor revolutions (19,200 pulses) and should equal one complete
bed revolution. The bed mark returned exactly to its starting position after
each forward/reverse check, with no reported lost-step or position error.
**M-05 passed for the unloaded geometric bed-ratio check.** Pen-engaged force,
magnetic index repeatability, final plotting rate, and instrumented thermal
limits remain separate tests. See
[`2026-09-05-m-05-bed-ratio-check.md`](../report/lab-notes/2026-09-05-m-05-bed-ratio-check.md).

M-02 Y-axis evidence: on 2026-09-05, the operator ran matched `Y5`/`Y-5`
unloaded moves at `F60`, `F120`, `F240`, `F360`, and `F500` after establishing
`G21` and `G94`. All stepped moves completed successfully with no reported
skipped steps, stalls, or jerking. The operator then raised `$111` to `1500`
mm/min and `$121` to `500` mm/sec^2 and reported the resulting motion as
smooth and acceptable. **M-02 passed for the conducted unloaded Y-axis check
and preliminary settings; the X-axis rate check remains.** See
[`2026-09-05-m-02-y-axis-rate-ramp.md`](../report/lab-notes/2026-09-05-m-02-y-axis-rate-ramp.md).

M-03 Y-axis evidence: on 2026-09-05, with `$101=80.000000`, a relative
`G1 Y100 F120` move measured exactly 100 mm with calipers. The matched
`G1 Y-100 F120` move returned exactly to the starting reference mark. **M-03
passed for the conducted Y-axis dimensional check.** See
[`2026-09-05-m-03-y-axis-dimensional-calibration.md`](../report/lab-notes/2026-09-05-m-03-y-axis-dimensional-calibration.md).

M-02 X-axis evidence: on 2026-09-06, the operator selected `$110=1500`
mm/min and `$120=500` mm/sec^2, then ran five matched `X50`/`X-50` unloaded
moves at `F1500`. Motion was reported smooth and returned exactly to the
reference mark with no skipped-step, stall, or jerk symptom. **M-02 passed for
the conducted unloaded X-axis check and preliminary settings.** No temperature
observation was recorded. See
[`2026-09-06-m-02-x-axis-rate-ramp.md`](../report/lab-notes/2026-09-06-m-02-x-axis-rate-ramp.md).

M-03 X-axis evidence: the initial 10 mm measurement was rejected after a
longer caliper check. With `$100=80.000000`, `G1 X100 F300` initially measured
`100.36 mm`; a calculated `79.71303` correction was tried and documented.
The operator later rechecked the axis by caliper, found `$100=80.000000`
accurate, and restored that value as the active setting. **M-03 passed for the
conducted X-axis dimensional check, with `$100=80.000000` as the current
operator-verified value.** See
[`2026-09-06-m-03-x-axis-dimensional-calibration.md`](../report/lab-notes/2026-09-06-m-03-x-axis-dimensional-calibration.md)
and [`2026-09-07-converter-house-sun-and-soft-limits.md`](../report/lab-notes/2026-09-07-converter-house-sun-and-soft-limits.md).

M-06 initial evidence: on 2026-09-06, pen-free matched diagonal X/Y/A moves
were reported perfect at `F15000` and `F20000`; the X/Y carriage and A-bed
marks returned exactly to their starts. **The coordinated-motion repeatability
smoke test passed.** Converter-generated inner/mid/outer-radius timing and
geometry validation remain required. See
[`2026-09-06-m-06-xya-coordinated-smoke.md`](../report/lab-notes/2026-09-06-m-06-xya-coordinated-smoke.md).
Use [`m06-radius-sweep.svg`](../../samples/svg/m06-radius-sweep.svg) for the
next pen-free converter-generated M-06 timing and geometry run. It uses
explicit inner/middle/outer-radius polylines and a reversed middle loop so the
current planner emits both positive and negative A drawing moves. For this
toolhead-disconnected run, leave **Use Z axis** unchecked and temporarily set
both pen commands and both pen delays to blank/zero before generating the
file. Confirm the G54 XY reference and a deliberate temporary A reference,
then inspect the generated first rapid and park target before Cycle Start.
On 2026-09-08, the owner reported that this radius-sweep run completed each
path perfectly and that the post-run `G90` / `G54` / `G0 X0 Y0 A0` command
returned X, Y, and A exactly to their reference marks. This passes the reported
geometry/repeatability portion. Actual bed movement measured 1:15.05 (75.05 s)
versus a 2:40.58 (160.58 s) preview, a 2.14× preview overestimate. Repeat the
timing with like-for-like scope or record inner/middle/outer times before
calibrating the estimator.

Use [`m06-xy-theta-lettering.svg`](../../samples/svg/m06-xy-theta-lettering.svg)
as a separate pen-free visual strategy check. With the current default r-theta
resolver, its generated command list must contain both `(x_theta)` and
`(y_theta)` draw labels. Those labels describe the selected coordinated
kinematic strategy; they do not denote distinct firmware modes.

[`kindergarten-house-sun.svg`](../../samples/svg/kindergarten-house-sun.svg)
is a larger pen-free visual smoke sample: house, sun, and explicit wavy ground
lines. It is parser-safe (polylines only) and is centered in G54 by the
converter. Its pen-free generated program completed on 2026-09-07 and the
explicit `G90 G54 G0 X0 Y0 A0` return landed exactly on both reference marks.
It does not replace the controlled radius, strategy, or preview-time checks;
see [`2026-09-07-converter-house-sun-and-soft-limits.md`](../report/lab-notes/2026-09-07-converter-house-sun-and-soft-limits.md).

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

**T-01A partial geometry result (2026-09-08):** the current spring measures
`L_free = 25.00 mm` outside its housing and `20.37 mm` installed and unloaded in its
housing, with a direct repeat of `20.29 mm` on 2026-09-09, giving approximately
`x_unloaded = 4.7 mm`. Its reported full-compression length is
`1.95 mm`. The photos confirm these are the two spring-seat separations within
the assembled mechanism: the motor-controlled compression span is therefore
`20.37 - 1.95 = 18.42 mm`. The 25.00 mm free length only establishes the
4.63 mm captured preload at the unloaded position; it is not the commanded
travel span. The 1.95 mm lower position is a hard housing endpoint, not a
normal `L_min` or a measurement of free-spring `L_solid`; it can coincide with
a housing hard stop, near coil bind, or both. Measure `L_lift`, `L_contact`, a
chosen working `L_min`, margins from the 1.95 mm endpoint, and compression
direction before powered preload motion. Obtain free-spring `L_solid` or its
specification before assigning final coil-bind margin or force limits.

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
| **T-01A — geometry and preload reference** | With power off, measure actual free spring length `L_free`, installed spring length at unloaded LIFT `L_lift`, at first pen contact `L_contact`, and at the greatest intended compression `L_min`. Record spring solid length `L_solid` from a manufacturer specification or a cautious dedicated compression measurement. Record the direction of compression under upward pen/paper force; do not infer it from lead-screw position alone. Calculate `x = L_free - L`, `x_lift`, `x_contact`, `x_max`, and the remaining solid-height margin `L_min - L_solid`. Photograph/mark the repeatable LIFT reference. | Every length, force direction, and safe travel endpoint is known; `L_min` remains above `L_solid` with a documented mechanical margin. These values set the firmware travel soft limits and distinguish unloaded lift from paper-contact compression. |
| **T-01B — installed spring force curve and hysteresis** | After E-07 establishes the scale-to-filtered-HX711 conversion, at no fewer than five evenly spaced compression points from the least to greatest intended compression, measure force with the spring installed in its real force path. Include the paper/scale contact condition if the spring is only loaded when the carriage is pushed upward by paper. Run at least three increasing/decreasing cycles, returning to the verified LIFT reference between cycles. Record applied force, length/position, load-cell raw reading, filtered force estimate, and any guide or linkage motion. Fit or tabulate the local force curve; do not assume a single linear rate if the mechanism is nonlinear. | Determine `F_contact = F(x_contact)` and, only if off-paper compression is intentionally present, `F_preload = F(x_lift)`, plus `F_min`, `F_max`, effective spring rate or lookup table, and increasing/decreasing-path hysteresis. The intended writing-force range is inside the measured range without coil bind, force-path bypass, or linkage slip. |
| **T-01C — static motor hold at contact force** | After E-06 and E-15, place the pen on a paper or digital-scale fixture and slowly move into contact until the selected `F_contact` is reached. Do not press the LIFT_HOME switch. Record carriage/spring position, pen force, rail voltage, motor/driver current, and motor/driver/regulator temperature at the start and after a defined hold dwell. Repeat once with the driver disabled only if the mechanism is guarded, to determine whether the leadscrew is self-locking and whether the carriage back-drives. The prior 0.18 A result was measured while pressing the LIFT_HOME switch at the travel endpoint and is not a T-01C contact-force measurement. | T-01C remains open until the selected contact force is held for the defined dwell with position/force/rail/current/temperature and drift recorded. If force remains stable with the motor disabled, the leadscrew is mechanically holding the load and active motor hold current may be near zero; if force decays, record the enabled hold current required to prevent back-drive. The endpoint-stall result remains separate bounded E-06 evidence. |
| **T-01D — retract motion reserve** | Starting from the greatest intended opposing-spring force, increase retract pulse width/PWM or speed in small documented steps. At each setting record retract time, current peak, position reached, force/clearance, and any driver fault. At the selected setting, perform at least 30 full `PEN_CLEAR`-to-work-range-to-`PEN_CLEAR` cycles with the normal payload. | Select a retract command below the first unreliable setting, with documented force/current/thermal margin. All 30 cycles reach `PEN_CLEAR` without a fault, hard-stop contact, lost reference, or uncommanded pen contact. This sets maximum retract effort and the minimum M5 dwell; it does not validate `LIFT_HOME`. |
| **T-01E — command-to-force and pulse response map** | Characterize the actuator's global motion limits with a representative pen or guarded force fixture: small up/down pulses at the intended preload and low/nominal/high force regions. Record command direction, PWM, pulse width, initial/final position, initial/final force, response delay, settle time, overshoot, and reversal/backlash. Do not assume the force change per pulse is universal across tools. Each new pen, marker, or pencil receives a short bounded response check during T-01J rather than repeating the full map unless it falls outside the established range. | Establish global minimum repeatable pulse, maximum safe pulse, directional backlash, and settle delay for the actuator. Record any per-tool force-response correction needed by T-01J. The load cell remains the force authority; these measurements bound pulse duration, correction rate, deadband, and anti-windup behavior for T-03. |
| **T-01F — control-envelope record** | Consolidate global actuator values and per-tool settings in the lab note: `L_free`, `L_solid`, `L_lift`, `L_contact`, `x_lift`, `x_max`, solid-height margin, force curve/rate, `F_preload`, global friction/stiction threshold, backlash, global minimum/maximum pulse, retract time, maximum tested current, rail-voltage minimum, temperatures, hold drift, selected dwell, and each tool's `F_target`, contact/release thresholds, and any bounded pulse override. State the source/test date for each value. | The table supplies every non-TBD physical value needed to configure force limits, travel limits, seek timeout, pulse bounds, correction cadence, LIFT dwell, and the T-03 acceptance band without pretending that one pen's pulse-to-force curve applies to every tool. Any unknown or failed value remains a commissioning gate rather than a firmware assumption. |
| **T-01G — LIFT-home switch** | Before connecting to the Pro Micro, meter-check the selected terminals: open when released and closed when the actuator flag presses the switch. Then wire the dry contact only between `GP2` and `TOOL_GND`, enable `INPUT_PULLUP`, and record at least ten slow retract cycles. Record trigger/release position relative to a documented mechanical LIFT datum, repeatability, debounce behavior, and timeout behavior if no trigger occurs. | All ten cycles report `GP2` LOW only when the moving-carriage flag presses the fixed switch, at a repeatable LIFT position before the separate mechanical backstop. A missing or implausible transition faults/stops retraction. This input is a position reference, not a hard stop; do not use it until the current spring's solid-height and backstop margins are verified. |

**T-01G partial installation result (2026-09-08):** the selected normally-open
contact meter-tested open released and continuous pressed. It is installed
between `GP2` and adjacent local `TOOL_GND`. Firmware configures GP2 with
`INPUT_PULLUP` and reports `lift_home=1` only when the switch is pressed; it
does not yet command or stop motor motion. The motor-safe UART1 diagnostic
passed at 115200 baud: `lift_home=1` pressed and `lift_home=0` released. Ten
slow powered retract cycles remain required.
Use `t01g_lift_home_uart` to isolate the GP2/GP20 path if the integrated sketch
does not produce readable service telemetry; it drives no motor-related pin.

**T-01G guarded-cycle result (2026-09-09):** With the 6.0 V supply limited to
0.20 A and the bounded E-07B service sketch at 20 ms per pulse, all ten
powered cycles released GP2 after six physical down pulses and first asserted
it after nine physical up/retract pulses. Manual `h` reads were stable at
`lift_home=1` at the pressed position. The actuator slept after every pulse.
This passes the observed switch polarity and repeatability portion only.
Trigger/release positions relative to measured spring length, the backstop
margin, stable released-state samples on every cycle, and missing-trigger
timeout/fault behavior remain open; GP2 must remain telemetry-only.

**T-01A/T-01G position result (2026-09-09):** lead-screw/heat-set-nut gap
measured `7.23 mm` at first `lift_home=1` assertion and `7.97 mm` at first
release, a `0.74 mm` observed switch window. These are not spring-seat lengths.
**Measured `L_solid` is 3.75 mm (2026-09-09):** the spring compresses only
under upward pen/paper contact force, making solid height a contact-force bound
instead of a retract-travel bound. Measure actual spring-seat lengths before
calculating preload or compression margin.
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

**Actuator replacement hold (2026-09-09):** 6 V 400 RPM and 1000 RPM N20
replacement candidates are ordered. Pause loaded contact, force, hold, retract,
and pulse-response characterization on the installed 200 RPM motor: speed and
gear ratio can alter torque reserve, current, self-locking, backlash, and every
command-to-force result. On receipt, first verify physical compatibility and
repeat E-05, guarded E-06/E-15, direction, GP2 travel, and the T-01 envelope
for the selected motor. Sensor-only work remains valid when it does not depend
on actuator motion.

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

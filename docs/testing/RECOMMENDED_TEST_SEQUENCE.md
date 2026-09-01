# Recommended Test Sequence

This is the recommended order for carrying out the existing tests in
[`TEST_PLAN.md`](TEST_PLAN.md). It is a dependency and safety guide with
explicit stop/go rules; it does not replace the formal measurements or pass
conditions in the test plan.

## Pass/fail rule

- **Pass / proceed** means the relevant `TEST_PLAN.md` pass condition is met,
  the exact setup and readings are in a dated lab note, and no safety fault or
  unresolved anomalous behavior remains. Advance only to the stated dependent
  test.
- **Fail or partial / stop** means leave dependent tests unstarted, command the
  actuator to its safe state or remove power as appropriate, and record the
  observation, settings, and corrective action in the lab note. A retry starts
  from the failed test after the cause is addressed; it is never an implicit
  pass.

## Order of operations

1. **E-01 through E-04 — Stepper and TB6600 characterization.** Identify coil
   pairs, record the physical driver settings, confirm input behavior, and set
   conservative current before connecting a controller.
2. **E-17 — RP23CNC pre-power inspection.** Inspect soldering, orientation,
   continuity, and rail isolation before applying normal power.
3. **E-11 and E-13 — 12 V supply by itself.** Verify terminal labels,
   protective earth, no-load output, adjustment range, and only documented
   protection/certification claims.
4. **E-14 — 6 V actuator regulator with no load.** Verify polarity and the
   fixed 6.0 V output before attaching the motor.
5. **E-14B — Completed toolhead perfboard, unpowered.** Before connecting the
   arriving 6 V twisted pair, verify the new Pro Micro-to-DRV8833 wiring by
   continuity, confirm the two-pin JST is not shorted, and confirm that
   `OUT1`/`OUT2` are still isolated because the motor pair is not fitted.
6. **E-14C — Exact DRV8833 control-label check.** For the installed ACEIRMC
   board, retain the continuity-checked GP7→`ULT` (sleep input) and
   GP6←`EEP` (fault output) harness, confirm the firmware mapping, and inspect
   its J2 bridge. This is a hard gate before the motor is fitted.
7. **E-15A — Toolhead 5 V regulator.** Connect the verified 6 V rail and
   verify stable logic power with the RP2350 and sensors active before the
   actuator is used.
8. **E-10 — System rails and references.** Confirm voltage rails, intended
   common references, and absence of unintended backfeed. Preserve galvanic
   isolation between `CTRL_GND` and `TOOL_GND` at the PC817 interface.
9. **F-01 — Controller baseline.** Boot and identify the RP23CNC firmware.
10. **F-03 and F-04 — Unpowered controller I/O.** Check STEP/DIR and limits
   before motor drivers or the toolhead are attached.
11. **F-08 — Motorless PRB/G38 feasibility.** With all TB6600 signal leads and
   motors disconnected, use a dry contact or validated optocoupler-style sink
   to prove probe state reporting, X `G38.3`/`G38.5` transition capture, probe
   coordinate reporting, and whether the installed XYZA build accepts A-axis
   probing. Keep the routed GP27 return assigned to `LIMA` until F-08 and its
   later GP27/U3 path check pass.
12. **F-05 — M3/M5 tool-output behavior.** Establish the actual controller
   ENA/AUX0 output states and fail-safe state.
13. **E-18 — Installed PC817/TMAG interface.** The assembled board has passed
    its simulated bench test; now verify it against the actual RP23CNC
    terminals and complete the TMAG5273 portion.
14. **E-05 — N20 no-load current.** After fitting the 22 AWG twisted
   `OUT1`/`OUT2` pair, run the motor mechanically unloaded at
    6 V in both directions. Do not restrain the shaft.
15. **T-01A — Toolhead geometry and preload reference.** With the toolhead
    unpowered, measure the installed spring, safe compression range, and LIFT
    reference before allowing the actuator to approach a hard stop. **Pass / proceed:**
    all T-01A lengths, force direction, and solid-height margin are recorded;
    proceed to the basic T-01 direction test. **Fail or partial / stop:** do
    not power the actuator into the unknown range; correct the geometry or add
    a guarded travel limit, then repeat T-01A.
16. **T-01G — LIFT-home switch.** With the actuator guarded, meter-check the
    planned terminals `1` and `3`, then verify the `GP2` input reads LOW only
    when the moving-carriage flag presses the fixed switch. Run ten slow
    full-retract `LIFT_HOME` motions and record the trigger/release positions.
    **Pass / proceed:** all ten transitions are repeatable and occur before the
    mechanical backstop; proceed to the basic T-01 direction test. **Fail or
    partial / stop:** keep the input out of firmware control, correct the
    switch/flag geometry or wiring, and repeat T-01G. This is a boot/recovery
    reference test, not a normal M5 cycle test.
17. **T-01 basic lift/open-loop direction.** Verify safe travel and record
    which motor polarity produces lift versus seek/down. If reversed, swap
    OUT1/OUT2 *or* reverse the firmware mapping, never both. **Pass / proceed:**
    lift direction and guarded travel are repeatable; proceed to E-06/E-15.
    **Fail or partial / stop:** de-energize before a hard stop, correct exactly
    one direction mapping, and repeat this test.
18. **E-06 and E-15 — Loaded actuator capability.** Perform the
    current-limited stall test and regulator load/ripple/temperature test only
    after no-load direction is known. **Pass / proceed:** measured current,
    driver response, regulator voltage/ripple, and thermal behavior establish a
    safe loaded electrical envelope; proceed to sensor characterization.
    **Fail or partial / stop:** do not attempt preload endurance or force-loop
    testing; resolve the electrical or thermal limit and repeat the failed test.
19. **E-07 through E-09 — Sensor characterization.** Calibrate the load cell,
    measure HX711 behavior, and validate the TMAG5273 with the intended
    magnet/geometry. **Pass / proceed:** E-07 provides repeatable force units
    and E-08/E-09 meet their recorded requirements; proceed to T-01B through
    T-01F. **Fail or partial / stop:** do not interpret raw counts as control
    force or tune gains; repair/recalibrate the affected sensor and repeat it.
20. **T-01B through T-01I — Motor/preload, M5-clear, and calibration-profile
    envelope.**
    Measure the installed force curve, motor hold and retract reserve, pulse
    response, normal M5 load-cell release hysteresis, clearance pulse, and the
    resulting controller limits. E-06, E-15, and E-07 are required gates; do
    not use nominal spring dimensions or unloaded N20 current as a force
    capability result. **Pass / proceed:** the T-01F envelope has every
    required value or a documented safe bound, T-01C/D prove the selected hold
    and retract commands, T-01H proves that normal M5 creates pen clearance
    without reaching the LIFT-home switch, and T-01I proves profile persistence
    plus a RAM-only startup baseline; proceed to contact seek. **Fail or
    partial / stop:** retain the relevant commissioning gate, reduce the
    claimed working range or correct the mechanism, then repeat the failed
    sub-test.
21. **T-02 through T-06 — Closed-loop toolhead and faults.** Add contact seek,
    force hold, and each safe-fault case one at a time. **Pass / proceed:**
    each test meets its formal pass condition and leaves the toolhead safe;
    proceed only to the next listed toolhead test. **Fail or partial / stop:**
    leave drawing/integration disabled and resolve the fault path before retry.
22. **M-01 through M-11 — Motion system.** Begin with one mechanically
    detached axis, then progress through calibration, coordinated motion,
    homing, magnetic scans, and homing fault paths.
23. **E-19 — Emergency stop input.** With the pen removed and motion disabled
    for the first pass, verify SW1 NC-A continuity, RP23CNC Halt/reset behavior,
    NC-compatible input inversion, and no automatic motion restart after release.
24. **Integrated tests — Full system.** Verify M3/M5 behavior, reset/E-stop
    safety, timing, jitter/lost-step effects, calibration patterns, and saved
    diagnostics.

## Critical gates

- Do not attach the RP23CNC to the optocoupler harness until **E-17**, power
  checks, and **F-05** are complete.
- Do not move the GP27/U3 return from `LIMA` to `PRB` until the direct-input
  portion of **F-08** proves the installed firmware behavior. Do not treat an
  A-axis source-code inference as a passed hardware/firmware test.
- Do not mechanically load or stall the N20 before **E-05** passes.
- Do not connect the motion mechanics until their driver settings and isolated
  I/O checks have passed.
- Record each result in the formal test plan and a dated lab note; a failed
  test pauses dependent tests until the cause and corrective action are
  documented.

## Current position

The PC817 bench portion of **E-18** is complete, but E-18 remains partial:
actual RP23CNC terminal behavior, TMAG readings, and installed-system
verification remain outstanding.

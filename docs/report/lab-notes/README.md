# Lab Notes

Store raw bench evidence and physical test results here. Use
[`../LAB_NOTE_TEMPLATE.md`](../LAB_NOTE_TEMPLATE.md).

Filename format:

```text
YYYY-MM-DD-test-id-short-title.md
```

Examples:

```text
2026-06-08-e-11-main-supply-check.md
2026-06-10-m-01-x-axis-jog.md
```

Each note should link to the relevant test in
[`../../testing/TEST_PLAN.md`](../../testing/TEST_PLAN.md), affected change note,
wiring-table rows, and engineering-log event. Keep measured values and failed
attempts here; summarize conclusions in the subsystem change note. For every
`E-*` test, the note must state the physical/software configuration, exact
procedure, measurements and outcome, difficulties encountered, corrective
action, and repeat evidence supporting a pass. If any code, commands, or
configuration were used, paste the exact version in a fenced code block in the
note; a source-file reference alone is insufficient.

## Index

Newest notes appear first.

| Date | Test ID | Result | Summary |
|---|---|---|---|
| 2026-09-08 | T-01G LIFT_HOME installation | Partial | Meter-verified normally-open contact installed between Pro Micro GP2 and local TOOL_GND. Input-only firmware telemetry is implemented; USB transition and guarded retract-cycle evidence remain. |
| 2026-09-08 | T-01A spring geometry | Partial | Current spring: 20.37 mm unloaded to 1.95 mm lower housing endpoint establishes an 18.42 mm in-housing compression span; 25.00 mm free length establishes 4.63 mm captured preload. LIFT/contact/safe-margin values remain. |
| 2026-09-08 | E-14 / E-14B / E-14C / E-15A | Passed | D36V50F6 output was reported constant at 6.05 V; perfboard, DRV8833/J2, and previously tested TMAG-related 5 V path gates passed. E-15 loaded characterization remains. |
| 2026-09-08 | M-06 radius sweep | Partial — geometry/repeatability passed | Pen-free converter-generated inner/middle/outer-radius sweep reportedly completed perfectly; explicit G54 return landed X/Y/A on all reference marks. Per-radius elapsed times remain. |
| 2026-09-07 | Converter X/Y/A and X/Y envelope | Passed (guarded pen-free scope) | `$100=80.00000` is the active caliper-verified X setting. The conservative X/Y software envelope is enabled at `$130=455`, `$131=446`, `$20=$40=1`; the house-and-sun program and `G90 G54 G0 X0 Y0 A0` return reached both reference marks. Boundary rejection, timing, and production registration remain open. |
| 2026-09-06 | Manual G54 XY | Verified (temporary) | Manual TMAG/pen-axis alignment measured a `(0,-30.1)` mm sensor-to-pen vector and set pen-centered G54 X/Y zero; A/P100 remain unregistered. |
| 2026-09-06 | M-07 X/Y homing | Passed (physical home) | X-east and Y-south NC switches passed single-axis and repeated combined `$H` cycles. Both logged repeats ended at `MPos:-10.000,-498.000` with `H:1,3`; limits and G54 registration remain open. |
| 2026-09-06 | M-06 X/Y/A | Passed (smoke) | Pen-free simultaneous diagonal X/Y/A moves were reported perfect at `F15000` and `F20000`; carriage and bed marks returned exactly. Converter radius/timing validation remains. |
| 2026-09-06 | M-03 X-axis | Passed | Historical run: `$100=79.71303` measured exactly 100 mm by caliper and `G1 X-100 F300` returned exactly to the starting mark. The active setting was later superseded to `$100=80.00000` after a separate 2026-09-07 caliper recheck. |
| 2026-09-06 | M-02 X-axis | Passed (unloaded) | Five `X50`/`X-50` pairs at `F1500` returned exactly to the reference mark with no reported motion problem; `$110=1500` and `$120=500` are preliminary unloaded settings. |
| 2026-09-05 | M-03 Y-axis | Passed | With `$101=80.000000`, a relative `G1 Y100 F120` move measured exactly 100 mm by caliper and `G1 Y-100 F120` returned exactly to the starting mark; X remains. |
| 2026-09-05 | M-02 Y-axis | Passed (unloaded) | Y stepped bidirectional moves at `F60` through `F500` completed without skipped steps, stalls, or jerking; `$111=1500` and `$121=500` were then reported smooth as preliminary settings. X rate remains; dimensional calibration is separate. |
| 2026-09-05 | M-05 | Passed | With `$103 = 4.44444`, `A4320` and `A-4320` at `F10000` produced the expected one-bed-revolution forward/reverse check; the bed mark returned exactly to its starting position each time. |
| 2026-09-05 | M-02 A-axis | Passed (unloaded) | A-axis acceleration tests through `$123=6000` / `F80000` were repeatedly smooth with exact mark returns; the F40000 test read `0.492 A` moving and `0.122 A` idle, and both motor and driver remained cool by touch. X rate remains; pen-force testing is separate. |
| 2026-09-05 | M-01 | Passed | A moved counterclockwise/clockwise at `F120`, Y north/south at `F60`, and X east/west at `F60`; supply current was approximately 0.44/0.43/0.42 A. X, Y, and A returned exactly to their physical marks with no noticeable heating by touch. |
| 2026-09-05 | E-03 | Passed | Installed X/Y/A TB6600 signal response passed: active-low enable, opposite DIR states, and approximately 5 V STEP pulses through the common-cathode harnesses. |
| 2026-08-19 | E-01 partial | Pass/partial | All 17HS15 coil pairs were identified by hand-turn generated voltage; Y's shielded cable continues black/green and red/white, with white spliced to motor blue. |
| 2026-08-12 | E-14B partial | Pass/partial | Local 6 V branch and S7V8F5-to-Pro-Micro power path passed continuity and bench-power checks; no motor or upstream regulator test. |
| 2026-08-10 | E-18 partial | Mixed | U1/U2/U3 and ground isolation passed after repairing missing wires; actual RP23CNC terminal behavior and magnetic-adapter work remain. |

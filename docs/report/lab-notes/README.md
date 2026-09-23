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
| 2026-09-23 | T-01H clearance, no-drag | Passed — behavioral (measured record open) | About 10-20 `M3`/`M5` cycles with X/Y jogs between strokes: the pen cleared on every `M5`, the jog left no mark, every `M3` re-contacted, and nothing faulted. Validates the staged 57 ms clearance for the supervised bench build; the measured pen-tip gap and 30-cycle formal record remain open. |
| 2026-09-23 | F-05 spindle-enable polarity | Passed — direction and fail-safe | Powering the RP23CNC drove the pen down with no M3 issued: the controller's spindle `ENA` is active-high by default, holding the toolhead's active-low optocoupler on at idle. Setting `$16=1` (invert spindle enable) fixed it — M3 is pen down, M5 is pen up, and the pen-up fail-safe holds. No optocoupler change. |
| 2026-09-23 | T-02 one-millimetre clearance run | Passed — 8/8 cycles | Reducing the M5 gap to about 1 mm cut the steady-state warm seek from 13-16 to 7-9 pulses, and `warm_ema` converged to about 13. Warm M3 is now about 2.2-2.8 s. |
| 2026-09-23 | T-02 learned travel after reseat + gate fix | Passed — 6/6 cycles | Reseating the CS1238 header dropped rejects from 1,578 to 0-1, confirming the flood was a connection. With the 3 g gate, every warm M3 now uses the learned coarse travel (13-16 pulses vs 24-27 fine-only). |
| 2026-09-23 | T-02 learned-travel first run | Partial — learning works, gate too tight | Six cycles, no faults. The first warm M3 measured 24 fine pulses and later cycles dropped to 13-14 using learned coarse travel. One cycle entered at a 6,516 raw clear residual, above the shared 1 g gate, and skipped coarse travel entirely (27 pulses). The warm gate is now 3 g. |
| 2026-09-23 | T-02 single-descend ten-cycle run | Passed — 10/10 cycles | Single-descend seek works with no faults. Cold start dropped 74 to 56 pulses; warm cycles stayed 22-26 because the M5 clearance gap dominates. Seek overshoots its threshold and the relief corrects it, so held spread widened to 5.4 g from 2.7 g. |
| 2026-09-23 | T-02 ten-cycle run (300 ms + rejection build) | Passed — 10/10 cycles | Ten M3/M5 cycles, no faults. Held force for warm cycles spanned 13,738 raw (2.7 g); references 38,108-80,032 raw (8.3 g) but clamped; three CS1238 conversions rejected with no fault and no recurrence of the false hard-force trip. |
| 2026-09-23 | T-02 at 300 ms settle, CS1238 glitch | Partial — false hard-force fault | Two M3/M5 cycles passed on the 300 ms build (references 24,236 and 48,557 raw, relief never engaged), then the controller faulted while idle: one -6,292,478 raw conversion pulled the 16-sample mean to -107,985 and tripped the hard-force guard. Implausible conversions are now rejected. |
| 2026-09-23 | E-09E post-pulse settle trace | Measured — 300 ms adopted | Three 5 ms DOWN pulses with the pen clear: the 16-sample filtered value reached within ±1,000 raw (about 0.2 g) of its plateau at 218 / 220 / 294 ms against a 299-692 raw tail noise floor, so the integrated settle dropped from 500 ms to 300 ms. |
| 2026-09-23 | T-02 hysteresis-relief nine-cycle run | Passed — relief engaged and recovered | Nine M3/M5 cycles, no faults. Cycle 1 entered hold 13.3 g above target; the relief engaged nine bounded times (199 ms total) and settled it in band, then stayed flat for cycles 2-9. Reference spread 21,403 raw, held spread 21,962 raw, smallest hard-limit margin 16 g. |
| 2026-09-23 | T-02 five-cycle clean pass | Passed (supervised cycle set) | Five M3/M5 cycles on the clamped + relief build reached `HOLD_FORCE` with no faults: reference spread 12,290 raw (about 2.4 g), held-force spread 12,943 raw (about 2.6 g), smallest hard-limit margin 18.7 g. The target clamp engaged on one cycle. |
| 2026-09-23 | T-02 settled-seek four-cycle run | Partial — 3 of 4 cycles reached hold, follow-up faulted | Four M3/M5 cycles with the 500 ms settle: first-touch reference came in at 38,886 / 46,551 / 42,697 raw, but a 78,727 raw touch left only 4.4 g below the hard limit and post-hold creep tripped it. A further cycle on the clamped build also faulted, with the force rising about 20 g after hold from a 49,314 raw reference. |
| 2026-09-22 | T-02 home-origin seek setup | Partial — two-stage candidate pending | The first 160 × 5 ms seek stopped safely 4.5 mm short; the next 25 ms-only seek reached the 35 g target then briefly crossed the 60 g limit. The new candidate uses 25 ms pulses far from contact and 5 ms pulses after force appears. |
| 2026-09-22 | Integrated GP2 boot retract | Passed (supervised bench) | Latest boot transitioned from `LIFTING, lift_home=0` to `LIFTED, lift_home=1, fault=none` after the 3000 ms timeout change; formal lift-reference gate remains unset. |
| 2026-09-22 | Integrated lift drive | Failed safely — PWM corrected | Corrected phase polarity still timed out at GP2 with no DRV fault; integrated lift PWM 70/255 was lower than E-09E's validated full-drive pulses, so it was raised to 255. |
| 2026-09-22 | Integrated direction polarity | Failed safely — corrected | The first supervised integrated boot timed out before GP2 because IN1/IN2 lift/seek phase selections were reversed relative to E-09E; the controller entered a bounded fault and the constants were corrected. |
| 2026-09-22 | T-01G lift-home switch transition | Partial | GP2 changed 0→1→0 repeatedly in the motor-safe UART diagnostic; ten powered retract cycles, positions, and backstop margin remain open. |
| 2026-09-22 | E-09F guarded force hold | Partial — band hold passed | Two `t`/`a`/`s` runs using the precision-weight raw profile settled and held at reported 40.0 g and 40.4 g. The separate 100 ms air-gap clear test remains. |
| 2026-09-22 | E-09E installed-pen scale direction | Partial | At a settled 40.7 g kitchen-scale reading, CS1238 raw was -59,087 and tare delta -312,723: the installed upward pen reaction is confirmed as opposite to downward calibration loading. One point does not establish an installed-pen transfer fit. |
| 2026-09-16 | USB/CDC research | Planned | Lowest-change calibration uses Pico native USB for raw force data and the existing USB-to-TTL Pro Micro service link for commands; direct externally powered Pro Micro USB needs a voltage check. |
| 2026-09-10 | E-18 / F-08 staged handshake | Partial — motor-inert local path passed | Installed `M64`/`M65` drove active-low Aux0/U2/GP28 through `READY_ACK`, `WAIT_REARM`, and `SCAN_ACTIVE`; TMAG detection changed 0→1→0. J1.6 sank during readiness, but ioSender did not expose `LIMA` input state; PRB/G38 remains open. |
| 2026-09-09 | T-01G guarded retract cycles | Partial — repeatability passed | All ten 6.0 V / 0.20 A guarded cycles released GP2 after six down pulses and re-triggered after nine up/retract pulses; backstop margin and timeout remain open. |
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

# RP23CNC filesystem macros

`P100.macro` is the commissioning-gated home and magnetic registration macro.
It is intended for the grblHAL filesystem macro plugin and is invoked with
`G65 P100 Q<mode>`.

| Mode | Behavior |
|---:|---|
| 0 | Full magnetic registration after standalone P111: center raster, two-pass A index, G54 writes, pen-center park |
| 1 | Toolhead readiness handshake only |
| 2 | Compatibility stop; directs the operator to P111 |
| 3 | Center raster and `G54 X0 Y0` registration |
| 4 | Outer-magnet scan and `G54 A0` registration |
| 5 | Automatic center-magnet survey; stops at TMAG centroid without writing G54 or A |

Q0 is enabled for a supervised first combined run only after `G65 P111`
completes successfully. Its measured values are the verified Q5 rectangle,
the P112 inboard `G53 X-10.5` index position, two 10,000 motor-degree/min A
searches, and the `4332 +/- 10` A-spacing gate. It defers every G54 write until
both magnetic surveys pass, writes A0 at the second observed index center,
returns TMAG to the calculated center, writes the installed pen-minus-TMAG
offset, and parks with the pen at `G54 X0 Y0 A0`. Q3/Q4 remain locked and return
error 39 before motion. Mode 1 requires commissioned toolhead firmware because
the Pro Micro will not acknowledge readiness otherwise.

P100's executable entry points now permit **Q0**, **Q1**, and **Q5**. Q1 performs the
proven motor-inert READY/release handshake. `Q2` now returns error 39 with an
explicit instruction to run `G65 P111`, because grblHAL processes `$H` system
commands while streaming a macro even when an enclosing O-word condition is
false. P100 therefore contains **no** `$H` text. Q0, Q2, Q3, and Q4 return
before the magnetic body.

`P111.macro` owns physical X/Y homing for isolated commissioning stages such
as Q5. It contains the one intentional, unconditional `$H`, preceded by `M5`
and a three-second settle; the X/Y homing configuration must omit A/Z.

`P113.macro` is the hardware-verified one-command `HOME + REGISTER` production
wrapper. It performs `M5`, the three-second dwell, the one unconditional `$H`,
and `G65 P100 Q0`; P100 remains free of `$H`. The motor-inert `G65 P114`
diagnostic printed both P101 and P114 PASS messages before the verified P113
run, proving that this grblHAL filesystem build returns correctly from a
nested macro invocation.

`P115.macro` is the normal-print toolhead acknowledgement wait. The converter
can optionally emit `G65 P115 Q0` after its opening M5 and `G65 P115 Q1` after
each later M3/M5 transition. Q1 first waits for GP27/`PRB` to clear so an old
ready level cannot satisfy a new command, then waits for the new assertion. Q0
accepts an already-proven-clear opening state. Both paths default to finite
0.50 s release and 5.00 s completion bounds and raise error 39 before following
motion on failure. `P115` observes GP27/`PRB` and dwells only in its strict,
`Q7`, and `W1` modes; the opt-in `W2` recover mode may issue one `M5` fail-safe
lift on timeout. It must not be used during P100. The separate normal-print
commissioning gates are now satisfied - F-05A passed on 2026-09-29 - so the
macro may be installed and selected in the converter, which still ships the
option off by default.

`P115` accepts optional arguments, each defaulting to the commissioned value:
`B<seconds>` completion bound (5.00), `C<seconds>` release bound (0.50),
`D<seconds>` poll interval (0.02), `A<seconds>` fallback dwell, `W1` warn-only,
and `W2` recover. The converter passes a `B` bound derived from
`pen_down_first_ms` on the program's first M3 only, because that one travels
the whole GP2 retract distance (measured at about 7 s) and would otherwise
exceed the 5.00 s default and abort a healthy program. Keep `D` at its default
unless `Q7` shows the release phase missing an edge; the 2026-09-25
`GP27_TRANSITION_LOW_MS` firmware floor is the real fix for an unterminated low
window.

With `W1` a timeout prints `P115 WARNING ...`, dwells `A` seconds - the fixed
`G4` dwell the converter would otherwise have emitted - and returns without
error. `W1` is the end-of-print full-retract fallback: the pen is already up
there and the Aux0/GP28 arm drives that retract, so no extra lift is issued.

With `W2` a timeout prints `P115 WARNING ...`, issues `M5` to lift the pen to
the fail-safe state, dwells `A` seconds (the converter passes the pen-up
clearance dwell), and returns without error. Recover mode is for a long print
where one missed handshake should cost a stroke or a travel, not the whole
sheet. It still masks a genuinely stuck toolhead signal and can draw the
following stroke in the air when the missed transition was an `M3`, so it stays
an explicit opt-in and the strict paths remain the default.

`Q7` is the measure-only mode. It reports `release observed|missing` and
`completion observed|missing` without raising error 39, so the operator can see
which phase fails on the installed hardware before choosing bounds or turning
on recover mode.

`P116.macro` is the manual **PEN UP + PARK** operator command. It performs, in
order: `M5` plus the verified `G65 P115 Q0` clear check; the `M65 P0`
full-retract request to the GP2 lift-home switch inside the toolhead's own
`BOOT_LIFT_TIME_MS` bound; `M64 P0` to release the arm; `G65 P111` for the one
physical X/Y home; and `G53 G0 X-10 Y-436` to park off the bed at the homed rest
position.

The X/Y home is not decoration. **An absolute park needs a machine frame.** An
unhomed controller has neither a machine position nor a soft-limit envelope for
X and Y, so a `G53` park pressed from it travels the whole commanded distance
from wherever the gantry happens to be. The park commands a little over 436 mm
in -Y while only about 246 mm of travel exists below the registered bed centre,
so an unhomed press runs the gantry into the end of travel. That is the
2026-09-30 failure this revision fixes, and it is why `P116` now homes first:
the home establishes the frame, and the controller then either allows `Y-436`
(5 mm inside the enforced Y end) or refuses it with a soft-limit alarm instead
of moving.

The arm handling also changed in that revision. The first version released
`Aux0`, waited 0.20 s, and asserted it again. When the pen is already parked at
GP2 the toolhead's readiness prerequisites are met, so that pair is exactly the
two-phase magnetic arm: the first assertion is a READY_ACK and the second,
inside the 3.0 s `MAG_REARM_WINDOW_MS`, moves the magnetic state into
`SCAN_ACTIVE`. The macro now releases the arm and waits `G4 P3.5` - longer than
the rearm window - before asserting it once, so a pen already at GP2 gets no
spurious magnetic arm and a pen off GP2 still gets its clean rising-edge
full-retract request.

The ioSender button is named `PEN UP + PARK`, has confirmation enabled, and
issues `G65 P116`. An operator who does not want a controller-side macro file can
put the same sequence directly in an ioSender macro:

```gcode
G21
G90
G94
G17
G54
M5
G65 P115 Q0
M64 P0
G4 P3.5
M65 P0
G4 P3.0
M64 P0
G65 P111
G53 G0 X-10 Y-436
```

`G65 P115 Q0` deliberately runs before any gantry movement. An already-clear
level or a proved clear-ready edge lets the sequence proceed; a stuck or faulted
toolhead raises `error[39]` while the gantry is still over the bed, instead of
moving a pen that never left the paper. On a controller without `P115.macro`,
substitute the converter's `G4 P0.8` pen-up dwell, which bounds rather than
proves the clearance. The retract's `G4 P3.0` is a bound as well, but the
toolhead raises `GP2 lift-home not reached during retract` inside it, so a missed
switch cannot become an unlimited retract.

`P116.macro` deliberately contains no `$` text at all, so no grblHAL system
command - the `$H` home that P100 must avoid - can execute while it streams.
The one home is `G65 P111`, which owns that system command.

The park target is the converter's `park_x_machine` / `park_y_machine` default
and it is tight: the enforced envelope is about X `-445..-10` and Y `-441..-10`,
so `Y-436` is 5 mm from the Y end and `X-10` is on the X pull-off edge. Any
drift in `$27`, `$130`, or `$131` turns the program-end park into a soft-limit
alarm. Re-derive the target from a fresh `$$` readout before assuming it is
still safe.

`P116` has been pressed on the machine exactly once and failed as described
above. The sequence has not completed a clean run yet; its retract half was also
exercised during the 2026-09-29 F-05A session.

`P112.macro` is the next **survey-only** A-index stage. After fresh P111 and a
successful Q5, run `G65 P112` without jogging X/Y/A between them. P112 moves
the TMAG along +X to G53 X `-10.5` mm: the measured `223.675804` mm radius
would exceed the X `-10` mm home pull-off limit, so this is roughly 2.2 mm
inboard while preserving the A phase. It captures two A entry/exit pairs,
requires their centers to differ by `4332 +/- 10` motor degrees, and stops at
the second-pass index center. It does not home or write G54. Its two bounded
searches run at 10,000 motor-degrees/min: at 12.0332:1,
that is 2.31 bed RPM and no more than 54 seconds for the 9,000 motor-degree
search allowance. The final move trims backward from the second exit to that
second observed center; it does not add a third rotation. Q4 remains locked
for a separate registration review. The installed revised survey completed at
`MPos:-10.500,-218.363,A8610.084` without a G54 write, and the operator
visually confirmed the index magnet centered beneath TMAG. The operator then
manually set the verified stationary position to G54 A0 with `G10 L20 P1 A0`;
`$#` reported G54 A offset `17281.142`. This is a verified commissioning
reference, not authorization to run P100 Q4/Q0.

The final center reference has also been physically verified. A subsequent Q5
returned TMAG to `MPos:-232.125,-218.325,A17281.142`; at that stationary point,
`G10 L20 P1 X0 Y-29.4892` set the installed pen-minus-TMAG offset. `$#` then
reported `G54:-232.126,-188.835,0.000,17281.142`. `G54 G0 X0 Y0` was visually
confirmed to place the **pen tip** exactly at the center magnet. This replaces
the historical temporary XY reference, but it does not authorize P100 Q0/Q3/Q4:
the production path must first be rebuilt around P111, Q5, and P112.

Q5 is a verified controlled motion stage. Run P111 first, then Q5. Q5 contains
no `$H` command and does not home. It uses the
candidate G53 rectangle and P100 probe/chord validation to calculate the
center-magnet centroid, approaches that centroid in G53, releases Aux0, and
returns. It does not execute `G10`, change G54, or move A.
Its successful 2026-09-11 hardware run completed at TMAG machine position
`X=-232.325`, `Y=-217.950` mm; visual placement of a magnet beneath that
point agreed with the calculated centroid. The active Q5 settings are 5 mm
row pitch and requested `F2000` magnetic crossings. With the existing 1500
mm/min X/Y maximum rate, that requested feed must not be treated as a measured
physical 2000 mm/min rate until a separate loaded-rate test passes.
The staged Q1 path waits two seconds for READY_ACK, based on the observed
controller-to-toolhead response timing. Before asserting READY it forces Aux0
released and waits two seconds for the toolhead to reacquire its inactive
magnetic baseline; the P104 evidence showed that an assertion during
`baseline=0` is deliberately ignored. Q1 then verifies the released state
after an additional 0.10-second settle.
Modes 0 and 3 also require the independent `#<sensor_to_pen_offset_valid> = 1`
gate and installed `pen - TMAG` X/Y values; this ensures G54 X0/Y0 is the pen
tip at bed center.

The ioSender production button is named `HOME + REGISTER`, has confirmation
enabled, and issues `G65 P113`. P113 is the verified unified registration
sequence; do not substitute Q3 or Q4.

The macro expects:

- grblHAL probe input and NGC expression/flow-control support;
- the filesystem macro plugin;
- `Aux 0` mapped as immediate digital output `P0` for `M64`/`M65`;
- GP27/U3 connected to `PRB`, with probe protection disabled;
- grblHAL homing cycles configured for X/Y only, excluding A; and
- G54 selected for the plotter's bed-local X/Y/A coordinate frame.

On the installed active-low U2/GP28 path, `M65 P0` asserts the arm and `M64
P0` releases it. The macro therefore uses `M65` -> `M64` -> `M65` for the
two-phase protocol and uses `M64` for every cleanup/abort path.

Do not upload or run the production macro until the candidate build and macro
syntax have passed the controller-side simulator/motorless validation described
in `docs/testing/TEST_PLAN.md`.

`P101.macro` is a temporary, non-motion diagnostic. `G65 P101 Q1` reports
whether grblHAL delivered the call's `Q1` argument to parameter `#17`; it does
not command any output, spindle, probe, or axis motion.

`P102.macro` is a second non-motion diagnostic. It copies `#17` to `#31`,
performs P100's initial named-variable assignments, and reports whether `#31`
preserved `Q1`. It likewise commands no output, spindle, probe, or axis motion.
P100 uses this same early `#31 = #17` preservation step because the tested
controller macro runtime does not retain `#17` reliably after named-variable
initialization.

`P103.macro` is an inert diagnostic for the complete P100 initialization
section. It reports whether `#31` still contains `Q1` after every current
commissioning, scan, timing, and saved-G54 assignment. It commands no output,
spindle, probe, or axis motion.

`P104.macro` is the output-context diagnostic. It asserts Aux0 through the
filesystem macro, waits two seconds, and returns with Aux0 intentionally still
asserted. Verify `READY_ACK` on the toolhead, then release it manually with
`M64 P0`. It contains no axis motion, spindle, or probe command.

`P105.macro` is the timed GP27 voltage diagnostic. It forces Aux0 released for
five seconds, holds READY_ACK for 30 seconds to permit a safe meter reading,
and then releases Aux0 automatically. It contains no axis motion, spindle, or
probe command.

`P106.macro` is the timed manual magnetic field-survey diagnostic. Starting
from a magnetically clear TMAG position, it performs the actual P100
`M65 -> M64 -> M65` READY/release/re-arm sequence, holds `SCAN_ACTIVE` for
180 seconds, then releases automatically. During the hold, manual jogging is
allowed: P blank means clear and P red means a detected magnetic field. It
contains no axis motion, spindle, or probe move of its own.

`P107.macro` is the Q5 preposition diagnostic. After a successful Q2, it makes
only the bounded G53 rapid from the X/Y-home position to Q5's southwest scan
corner `X=-280`, `Y=-266` mm and stops. It contains no `$H`, probe, Aux0,
A-axis, or G54-write command. Use it to distinguish the first Q5 travel move
from an unexpected additional physical homing cycle.

`P108.macro` is the Q5 readiness-handshake diagnostic. It reproduces Q5's
`M64 -> M65 -> M64 -> M65 -> M64` Aux0 sequence and probe-state checks, but
contains no axis-motion command. A `Home` state or any X/Y movement during
P108 is therefore an unexpected controller/external action rather than Q5
preposition or raster motion.

`P109.macro` combines the two verified pieces in their Q5 order: the bounded
G53 preposition to `X=-280`, `Y=-266` followed by the complete Aux0 handshake.
It stops before every `G38` command, so it contains no raster or centroid
motion. Run it only after a fresh Q2; a `Home` state during P109 isolates the
interaction to this combined sequence, while a clean pass shifts attention to
the first raster/probe command.

`P110.macro` is the first Q5 G38-row diagnostic. After a fresh Q2, it reaches
the southwest corner, runs the full Q5 arm/release/re-arm sequence, and issues
only the first clear-row `G38.3 X100` at G53 Y `-266` mm. It releases Aux0
before returning. It performs no centroid, G54, or A operation. A `Home`
state during P110 isolates the behavior to G38 probing rather than homing.

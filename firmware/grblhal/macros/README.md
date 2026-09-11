# RP23CNC filesystem macros

`P100.macro` is the commissioning-gated home and magnetic registration macro.
It is intended for the grblHAL filesystem macro plugin and is invoked with
`G65 P100 Q<mode>`.

| Mode | Behavior |
|---:|---|
| 0 | Full X/Y home, center raster, centroid approach/registration, and A registration |
| 1 | Toolhead readiness handshake only |
| 2 | Compatibility stop; directs the operator to P111 |
| 3 | Center raster and `G54 X0 Y0` registration |
| 4 | Outer-magnet scan and `G54 A0` registration |
| 5 | Automatic center-magnet survey; stops at TMAG centroid without writing G54 or A |

The file intentionally sets `#<commissioned> = 0`. Modes 0, 3, and 4 return
grblHAL error 39 before they can command `M5`, motion, or Aux0; they remain
locked until F-08/E-18 pass and every scan constant at the top of the macro is
replaced with measured, documented values. Mode 1 requires commissioned
toolhead firmware because the Pro Micro will not acknowledge readiness
otherwise.

P100's executable entry points now permit **Q1** and **Q5**. Q1 performs the
proven motor-inert READY/release handshake. `Q2` now returns error 39 with an
explicit instruction to run `G65 P111`, because grblHAL processes `$H` system
commands while streaming a macro even when an enclosing O-word condition is
false. P100 therefore contains **no** `$H` text. Q0, Q2, Q3, and Q4 return
before the magnetic body.

`P111.macro` owns physical X/Y homing. It contains the one intentional,
unconditional `$H`, preceded by `M5` and a three-second settle. Run `G65 P111`
before Q5; the X/Y homing configuration must omit A/Z.

`P112.macro` is the next **survey-only** A-index stage. After fresh P111 and a
successful Q5, run `G65 P112` without jogging X/Y/A between them. P112 moves
the TMAG +X by the measured center-to-index radius of `223.675804` mm, captures
two A entry/exit pairs, requires their centers to differ by `4320 +/- 10`
motor degrees, and stops at the second-pass index center. It does not home or
write G54. Its two bounded searches run at 10,000 motor-degrees/min: at 12:1,
that is 2.31 bed RPM and no more than 54 seconds for the 9,000 motor-degree
search allowance. The final move trims backward from the second exit to that
second observed center; it does not add a third rotation. Q4 remains locked
until this survey is physically verified.

Q5 is a verified controlled motion stage. Run P111 first, then Q5. Q5 contains
no `$H` command and does not home. It uses the
candidate G53 rectangle and P100 probe/chord validation to calculate the
center-magnet centroid, approaches that centroid in G53, releases Aux0, and
returns. It does not execute `G10`, change G54, or move A.
Its successful 2026-09-11 hardware run completed at TMAG machine position
`X=-232.325`, `Y=-217.950` mm; visual placement of a magnet beneath that
point agreed with the calculated centroid.
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
enabled, and is not yet authorized because Q0 remains locked. During staged
testing, invoke Q1/Q5 from P100 and physical X/Y home through P111 only.

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

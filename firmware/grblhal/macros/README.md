# RP23CNC filesystem macros

`P100.macro` is the commissioning-gated home and magnetic registration macro.
It is intended for the grblHAL filesystem macro plugin and is invoked with
`G65 P100 Q<mode>`.

| Mode | Behavior |
|---:|---|
| 0 | Full X/Y home, center raster, centroid approach/registration, and A registration |
| 1 | Toolhead readiness handshake only |
| 2 | Physical X/Y homing only |
| 3 | Center raster and `G54 X0 Y0` registration |
| 4 | Outer-magnet scan and `G54 A0` registration |

The file intentionally sets `#<commissioned> = 0`. Modes 0, 3, and 4 return
grblHAL error 39 before they can command `M5`, motion, or Aux0; they remain
locked until F-08/E-18 pass and every scan constant at the top of the macro is
replaced with measured, documented values. Mode 1 requires commissioned
toolhead firmware because the Pro Micro will not acknowledge readiness
otherwise.

P100's executable entry points now permit **Q1** and **Q2** only. Q1 performs
the proven motor-inert READY/release handshake. Q2 performs only `M5`, a
three-second settle, and the controller's configured X/Y `$H` cycle, then
returns; it never reaches the readiness, raster, or A-index code. Q0, Q3, and
Q4 immediately return error 39 before the macro's legacy registration body.
The Q2 branch passed direct installed `$H` and filesystem `G65 P100 Q2`
execution on 2026-09-11.
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
enabled, and sends `G65 P100 Q0`. During staged testing, invoke Q1 through Q4
individually from the MDI only after satisfying each mode's prerequisites.

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

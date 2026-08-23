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

The file intentionally sets `#<commissioned> = 0`. Modes 0, 3, and 4 abort
until F-08/E-18 pass and every scan constant at the top of the macro is replaced
with measured, documented values. Mode 1 requires commissioned toolhead
firmware because the Pro Micro will not acknowledge readiness otherwise.

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

Do not upload or run the production macro until the candidate build and macro
syntax have passed the controller-side simulator/motorless validation described
in `docs/testing/TEST_PLAN.md`.

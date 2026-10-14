---
id: RPSW-20261014-001
date: 2026-10-14
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/grblhal/macros/P100.macro
  - tools/validate_homing_macro.py
tags:
  - grblhal
  - macro
  - p100
  - registration
  - calibration
  - drift
related:
  - RPSW-20261001-002
  - WSW-20261013-014
  - WSW-20261013-015
---

# Axis-centre correction re-measured by registered jog: X 2.45, Y 0.9

## Summary

`P100.macro`'s `#<axis_center_correction_x>` and `_y` move from `1.25 / 0.0`
to `2.45 / 0.9`. The update comes from a registered jog on 2026-10-14: after
`G65 P113` parked at `G54 X0 Y0`, the operator jogged the pen tip exactly onto
the centre magnet, reading `X-0.005 Y0.004` at the park and `X1.195 Y0.904` at
the centred position - a delta of +1.200 mm X and +0.900 mm Y that is *added*
to the correction because the registration write subtracts it from
`sensor_to_pen`. The operator identified these two DRO readings as the
authoritative basis for the update.

The correction stays in the axis-centre constants because the jog measures
where the registered origin must sit, not the pen/TMAG geometry. The pen-offset
equivalent would be `sensor_to_pen = (-1.200, -30.3892)`, within 0.3 mm of the
historical `-30.100` Y measurement. Attribution of the error remains pending
(Q5 at A0 and A180). The operator confirmed the parked pen lands centred after
the update was applied on 2026-10-14; the rotation acceptance check remains
open.

## Reason

The operator asked to make the registration offset durable: "i want to modify
my pen offset. where does this pen offset occur? p100?" and "after registration
can i jog it to the exact center, give you the number of the DRO and you
adjust our pen offset based on the difference between the jog number and the
pen offset number?" A jog plus `G10 L20 P1 X0 Y0` does not survive the next
registration - `G65 P113` -> `P100 Q0` rewrites G54 X/Y/A from the P100
constants (recorded 2026-10-13). The durable place is those constants.

## Implementation

- `firmware/grblhal/macros/P100.macro`: the two constants carry the
  2026-10-14 dated evidence in their comment block; the registration write is
  unchanged in form and now writes `X-2.45 Y-30.3892` at the centroid.
- `tools/validate_homing_macro.py`: the required-token expectations pin the new
  values, so a future edit cannot drop the update silently.
- Documentation: the macros README axis-centre section, `firmware/README.md`,
  this note, the lab note, and the engineering log.

## Verification

- `python tools\check_macros.py` - all macros parse-safe.
- `python tools\validate_homing_macro.py` - P100/P115 validation passed.
- `python tools\docs_index.py --write` / `--check` - indexes regenerated and
  valid.
- **Park confirmed on the machine (2026-10-14):** with the revised macro
  uploaded and `G65 P113` re-run, the operator reports the parked pen lands
  centred on the centre magnet ("it looks perfect now").
- **Remaining acceptance:** the rotation check - a magnet under the lifted pen
  must stay centred through a bed rotation - or the a-center-test tick bundle
  collapsing, or the `center-registration-check.gcode` crosses coinciding.

## Struggles and rejected approaches

- The first instinct is to subtract the jog from the correction. The
  validator's model (`origin = centroid - written`) shows the jog *adds* to
  the correction, because the registered origin must move with the jog delta;
  the 2026-10-01 `+1.25` update reproduces the same direction.
- Considered folding the delta into `sensor_to_pen`, matching the operator's
  phrase "pen offset". Rejected for bookkeeping: the jog measures the
  registered frame at the bed centre, which the repo records as the
  axis-centre quantity, and the pen/TMAG value stays the measured geometry
  until the Q5 A0/A180 test attributes the cause. The machine behaviour is
  identical either way.
- Known conflict: the 2026-10-13/14 centre-test session measured 2.0/1.44 mm
  and found that a G54 form of that correction did not collapse the eight-angle
  tick bundle. This new jog disagrees by about 1 mm; both readings are
  operator-visual.

## Risks and follow-up

- Operator-visual measurement; roughly 1 mm of run-to-run scatter is visible
  between the 2026-10-13 (2.0/1.44) and 2026-10-14 (1.200/0.900) readings.
- If the residual is rotation-angle-dependent (off-axis centre magnet) or a
  scale error, the constant update alone will not collapse the plots. The next
  evidence is the X/Y scale-sheet reading and, if needed, the Q5 A0/A180
  attribution test.
- Re-seating the centre magnet invalidates the correction.

## Files

- `firmware/grblhal/macros/P100.macro`: constants and comment block.
- `tools/validate_homing_macro.py`: pinned expectations.
- `firmware/grblhal/macros/README.md`, `firmware/README.md`: current-state
  documentation.
- `docs/report/lab-notes/2026-10-14-registered-pen-centre-jog.md`: bench note.
- `docs/project/ENGINEERING_LOG.md`: log entry.

---
id: WSW-20260929-003
date: 2026-09-29
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
status: implemented
components:
  - software/converter_core/settings.py
tags:
  - converter
  - clipping
  - soft-limit
  - reachable-area
  - g54
  - alarm-2
related:
  - WSW-20260926-002
  - HW-20260907-002
---

# Re-derive the reach radius and give it a registration-drift margin

## Summary

The default **Gantry reach radius mm** moves from `191.4` to `185.0`. The new
value is the binding directional margin from the currently registered bed
center (195.27 mm to the machine's +Y home edge) less a 10 mm margin for
registration drift.

## Reason

The old default was a literal derived once from a bed center at machine
`Y = -191.4`. HOME + REGISTER moves that center every session: the recorded G54
`Y` offset has been `-189.980` (2026-09-24) and `-195.270` (2026-09-29), a
spread of more than 5 mm. Because the +Y edge is the machine's home position,
the margin to it *is* the drawable radius, so a few millimetres of drift eats
the whole allowance.

That is what a `samples/gcode/mom.gcode` run hit on 2026-09-29: the program
measured 189.81 mm maximum radius against the 191.4 cap - inside the model -
but `Alarm:2 - Soft limit` stopped it partway through contour 8713 reversed,
leaving the pen down. The file itself contains no target outside the
controller's configured envelope, so the disagreement has to be between the
model's assumed bed center and the registered one.

Margins from the 2026-09-29 registration (`$130=455`, `$131=451`, bed center
machine `-232.449, -195.270`):

| Direction | Margin |
|---|---|
| +X | 232.449 |
| -X | 222.551 |
| **+Y (home end)** | **195.270** |
| -Y | 255.730 |

`195.270 - 10 = 185.27`, entered as `185.0`.

## Implementation

- `settings.py`: `machine_reach_radius_mm` default `191.4 -> 185.0`, and the
  derivation and drift evidence recorded in the comment above it, including the
  instruction to re-derive after every HOME + REGISTER.
- `settings.py`: the field default string updated so the Qt field seeds `185.0`.
- `software/README.md`: the setting description now names the binding
  direction, gives the four margins, and states that the value must be
  re-derived after each registration.

No planning or emission logic changed: the clip radius is still
`min(bed_diameter/2 - bed_margin, machine_reach_radius_mm)`.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes, 72
  tests.
- Re-derivation checked against the controller snapshot: `$130=455`,
  `$131=451`, G54 `-232.449, -195.270`, giving +Y = 195.270 as the minimum of
  the four margins.

**Not verified:** no plot has been generated and run from the new default yet.
The immediate evidence is that `mom.gcode` reaches 189.81 mm, which the new cap
now clips.

## Struggles and rejected approaches

- Leaving the value at 191.4 and only documenting the re-derivation was
  rejected: the previous default was already "correct" for the registration it
  was derived from, and that is exactly how it went stale.
- Deriving the cap in the converter from `$130`/`$131` and the bed center was
  considered but not implemented here: the controller registers G54 at run
  time, so the converter would still need the operator to supply the current
  bed-center machine coordinates. Recorded as the proper follow-up rather than
  guessed at in this change.

## Risks and follow-up

- The cap is still a literal. A registration that moves the bed center further
  toward +Y than 10 mm will silently invalidate it again. Exposing the travel
  limits and the registered bed center, computing the cap from them, naming the
  binding direction in the UI, and warning when the artwork radius comes within
  a few millimetres of the cap is the durable fix and should be scheduled.
- The 10 mm margin is a judgement, not a measurement: it covers the 5.3 mm
  registration spread observed so far with room to spare. Tighten or widen it
  only against recorded registration data.

## Files

- `software/converter_core/settings.py`: default and derivation comment.
- `software/README.md`: setting description and the over-scale example text.

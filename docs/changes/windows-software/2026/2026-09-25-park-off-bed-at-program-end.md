---
id: WSW-20260925-003
date: 2026-09-25
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/gcode.py
  - software/converter_core/settings.py
tags:
  - converter
  - parking
  - g53
  - program-end
---

# Park the toolhead off the bed at program end

## Summary

The generated program now ends with a `G53 G0` machine-coordinate move to a
configured park position (defaults to the homed rest position `-10,-436`)
instead of parking at the northeast edge of the drawable bed. The pen clears
the rotating bed so the paper can be removed without the gantry in the way.

## Reason

The previous end-of-print park stayed on the drawable circle, so the pen ended
up over the paper and the operator could not remove it without jogging the
machine by hand.

## Implementation

- `settings.py`: new `park_x_machine`/`park_y_machine` floats exposed in the
  Pen group, defaulting to the installed machine's homed rest position.
- `gcode.py`: `park_home_command()` emits the `G53` move; `contours_to_gcode`
  appends it after the final M5/pen-up, and `build_preview_moves` accounts for
  a nominal off-bed travel time (the G53 target has no fixed G54 equivalent
  because the work offset is registered at run time).
- `kinematics.py`: removed the now-unused `ne_park_position`.

## Verification

- `python -m unittest discover -s software/tests` passes (24 tests).
- Generated sample program ends `M5` / `G65 P115 Q1` / `G53 G0 X-10 Y-436
  (park home)` / `M2`.

## Struggles and rejected approaches

A G54 off-bed target was rejected because the controller's work offset is
registered at run time, so the converter cannot compute the bed edge relative
to the machine envelope. `G53` machine coordinates target the fixed home
position regardless of the work offset.

## Risks and follow-up

- The park coordinates must stay inside the controller software envelope
  (`$130/$131`); the defaults are the verified homed rest position. Entering a
  value outside the envelope would raise a controller soft-limit alarm at the
  end of the run.

## Files

- `software/converter_core/settings.py`
- `software/converter_core/gcode.py`
- `software/converter_core/kinematics.py`
- `software/tests/test_theta_feed.py`
- `software/README.md`
- `docs/integration/INTERFACES.md`

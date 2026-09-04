---
id: WSW-20260904-001
date: 2026-09-04
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
status: implemented
components:
  - software/converter_core/settings.py
  - software/converter_core/kinematics.py
  - software/converter_core/gcode.py
  - software/qt_svg_to_gcode.pyw
tags:
  - coordinate-frames
  - tool-offset
  - p100
  - g54
related:
  - docs/integration/INTERFACES.md
  - firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md
---

# Move pen/TMAG XY offset ownership to P100

## Summary

Removed the converter's configurable pen/TMAG XY offset. Generated XY G-code
and preview positions now use one direct machine/work-coordinate frame, while
P100 owns magnetic registration, the measured `pen - TMAG` offset, and G54 zero.

## Reason

The controller must register the actual bed center at startup. Applying the
same offset in the offline converter and P100 would double-compensate the pen
position and would make saved G-code dependent on a stale toolhead geometry.

## Implementation

- Removed `tool_offset_x_mm` and `tool_offset_y_mm` from converter settings and
  the Qt Pen settings group.
- Removed the `tool_to_command`/`command_to_tool` translation helpers; G-code
  formatting now emits the calculated XY point directly.
- Simplified preview move data and overlays to one XY position frame; theta
  offset and pen-width compensation remain separate settings.
- Updated the host README and handoff to state that P100 owns the runtime
  sensor-to-pen transformation.

## Verification

- `python -m py_compile software\qt_svg_to_gcode.pyw software\svg_to_gcode.pyw software\converter_core\settings.py software\converter_core\geometry.py software\converter_core\kinematics.py software\converter_core\gcode.py software\converter_core\__init__.py` passed.
- `python -m unittest discover -s software\tests -p "test_*.py" -v` passed all
  three coordinate-frame regression tests: the removed settings are absent,
  direct XY formatting is unshifted, and preview moves no longer contain the
  duplicate command frame.
- `python tools\docs_index.py --write` and `python tools\docs_index.py --check`
  passed after the documentation updates.

## Struggles and rejected approaches

The initial implementation kept separate preview `tool` and `command` points
after removing the numerical offset. That preserved a misleading two-frame
model, so the preview/status data was simplified to one position frame.

## Risks and follow-up

P100's measured `pen - TMAG` values and `sensor_to_pen_offset_valid` gate remain
commissioning requirements. A physical plotting test must confirm that G54
registration places the pen tip correctly before production use.

## Files

- `software/converter_core/settings.py`: removed the converter offset fields and UI metadata.
- `software/converter_core/kinematics.py`: removed the XY translation helpers.
- `software/converter_core/gcode.py`: emits direct XY points and simplified preview move records.
- `software/qt_svg_to_gcode.pyw`: removed the duplicate command/tool preview frame.
- `software/tests/test_coordinate_frames.py`: guards the single-frame offset ownership contract.
- `software/README.md`: documents direct XY output and P100 ownership.
- `docs/HANDOFF.md`: corrected the current converter coordinate model.

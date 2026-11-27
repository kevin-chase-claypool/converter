---
id: WSW-20261127-002
date: 2026-11-27
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/gcode.py
  - software/tests/test_generator_tabs.py
tags:
  - cmyk
  - preview
  - registration
  - fiducial
  - auto-fit
  - clipping
  - bug-fix
related:
  - WSW-20261127-001
  - ADR-013
---

# Keep CMYK registration crosses visible after automatic fit

## Summary

CMYK previews now retain all four named registration crosses when **Fill bed**
or **Fit inside** scales the page. The crosses remain control geometry outside
the artwork clipping pass. When their rectangular page-corner layout would
leave the circular planning envelope, the planner pulls the four centres
inward, caps the printed arm length at `5 mm`, and emits the same layout in
preview and G-code.

## Reason

Selecting **Corner crosses (all inks)** and pressing Preview could show no
crosses. A direct preview-worker reproduction found zero registration contours
after planning, although manual 1:1 planning retained all 32 cross arms.

The cause was automatic page scaling: a rectangular page fitted to the round
bed put its four corners outside the circular reach. The general artwork clip
then removed every cross before the preview and G-code could receive it.

## Implementation

- Split tagged registration contours from ordinary artwork before
  `clip_contours_to_bed`.
- Recenter registration geometry into the same bed frame as artwork without
  clipping it.
- Leave already-fitting manual page-margin crosses unchanged.
- If any arm would exceed `98 %` of the effective planning radius, preserve the
  four quadrant positions but pull their centres onto a safe inscribed
  rectangle. Arm half-length is capped at `5 mm`.
- Normalize arm midpoints against the declared pen offset so bed-fit scaling
  cannot multiply that absolute paper-space correction.
- Append the prepared crosses to the planned contour set so preview and all
  four exact G-code programs share the visible control geometry.

## Verification

- The new regression uses a blank `32 x 32` image, a `60 x 60 mm` CMYK page,
  automatic fit, and crosses enabled.
- Before the fix, planning returned no registration arms.
- After the fix, all four IDs (`CORNER-NW/NE/SW/SE`) survive for cyan,
  magenta, yellow, and black.
- The regression also confirms the furthest mark remains inside the effective
  planning radius, remains in the outer half of the drawable field, and every
  arm is at least `1 mm` long.
- Focused generator, CMYK, overlay, set-identity, and Wave rotating-row suites
  pass `195` tests with one expected OpenGL-context skip.
- Complete converter discovery passes `682` tests with one expected
  OpenGL-context skip.

## Struggles and rejected approaches

- A manual-scale comparison proved that SVG serialization, per-ink tagging, and
  the preview renderer retained the crosses; automatic fit plus circular
  clipping was the specific boundary.
- Exempting crosses from reach checks would have left out-of-envelope machine
  moves. The selected fix relocates only the control layout when necessary.
- Drawing preview-only crosses would have produced an image the saved G-code
  could not reproduce, so the placement is done in shared planning.

## Risks and follow-up

- Auto-fit may move the visible cross rectangle away from the extreme
  rectangular page corners because those corners are outside the round stock.
  The cross IDs, quadrant arrangement, and cross-ink alignment are preserved.
- Automatic placement is software geometry. A small fresh print after one
  HOME + REGISTER remains the physical verification.
- Use a sparse `60-100 mm` diagnostic page for preview and the first paper
  check rather than consuming a full-photo plot.

## Files

- `software/converter_core/gcode.py`: registration/artwork clip separation,
  safe placement, arm cap, and absolute pen-offset normalization.
- `software/tests/test_generator_tabs.py`: automatic-fit preview regression
  across all four inks and visibility/radius assertions.
- `software/README.md`, `docs/decisions/ADR-013-gcode-registration-gate.md`,
  `docs/project/ENGINEERING_LOG.md`, and generated change indexes: current
  behavior, rationale, verification, and remaining physical check.

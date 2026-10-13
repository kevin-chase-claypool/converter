---
id: WSW-20261013-002
date: 2026-10-13
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/settings.py
  - tools/check_cmyk_set.py
tags:
  - reach-radius
  - soft-limits
  - cmyk
  - preflight
  - registration
related:
  - docs/HANDOFF.md
  - tools/check_gcode_motion.py
---

# Reach radius 180, and a CMYK set preflight against the travel window

## Summary

Two changes after a mid-plot Alarm 2 on the CMYK yellow layer:

1. The default `machine_reach_radius_mm` drops from **185.0 to 180.0**, with
   the re-derivation recorded in the settings comment.
2. `tools/check_cmyk_set.py` computes each layer file's machine-coordinate
   bounding box from the live G54 offset and fails any file whose targets
   leave the grblHAL work envelope - the check that would have caught this
   set before the first move.

## Reason

The CMYK set auto-fitted to the 185 mm reach radius. That value was derived
from the 2026-09-29 registration (bed centre at machine -232.449, -195.270,
+Y reach 185.270). The registration moved: tonight's live dump shows G54 at
machine -231.214, -193.629, making the +Y work limit 183.629. The layers'
top edges therefore sat 0.35-1.37 mm past the soft limit; grblHAL stopped the
plot mid-column (the machine looks fine because the alarm triggers on the
target ahead), and the layer was completed with a resume file
(`IMG_0514-cmyk-yellow_resume.gcode`, clipped at work Y 183.13).

## Implementation

- `settings.py`: default and UI default string 185.0 -> 180.0; the comment now
  records both registrations, the derived work envelope for the live one, and
  the standing rule to re-derive after every registration.
- `tools/check_cmyk_set.py`: takes glob patterns plus `--g54` (the live work
  offset) and optional `--machine-x/--machine-y` window overrides; prints per
  file the machine bbox, move count, and any overshoot; exits non-zero if any
  file is outside.

## Verification

- Preflight against tonight's G54: black/magenta/yellow fail by ~1.37 mm,
  cyan by 0.35 mm, and the resume file passes (machine Y max -10.50).
- The resume file passes `tools/check_gcode_motion.py` (bed step 14.7 deg < 15
  cap, A rate at cap, worst bow 0.072 mm).

## Struggles and rejected approaches

The first resume generator emitted strokes out of order (travel, moves, then
M3) because the block splitter reassembled lines instead of preserving the
file's order; caught by inspecting the output before use and rewritten to
preserve original order while clamping travels and truncating out-of-window
strokes.

## Risks and follow-up

- An open app session may hold the old 185 value; set "Gantry reach radius mm"
  to 180 (or re-derive) in the UI before the next auto-fit.
- The machine window used by the preflight follows $130=455, $131=451,
  $27=10 with hard limits on; pass explicit windows if any of those change.

## Files

- `software/converter_core/settings.py`: default and comment.
- `tools/check_cmyk_set.py`: new preflight.
- `docs/project/ENGINEERING_LOG.md`: session entry.

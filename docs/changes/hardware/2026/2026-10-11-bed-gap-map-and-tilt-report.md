---
id: HW-20261011-001
date: 2026-10-11
category: hardware
affected_categories:
  - hardware
  - windows-software
status: implemented
components:
  - tools/bed_tilt_map.py
  - tools/make_bed_gap_maps.py
tags:
  - bed
  - flatness
  - tilt
  - runout
  - diagnosis
  - tooling
related:
  - docs/report/lab-notes/2026-10-01-theta-a-rate-limit-lowering.md
  - docs/testing/RECOMMENDED_TEST_SEQUENCE.md
---

# Bed gap map and Klipper-style tilt report

## Summary

Added the measurement loop the bed accuracy investigation needs: a generator
for pen-up measurement programs that walk the carriage (and index the bed) and
pause for a mechanical gauge reading, and an analysis tool that turns those
readings into a plane fit, a per-mount "raise by shim mm / screw turns" report,
and a one-page PNG with the 3D surface, top-down map, residual map, and
per-radius ring profiles - so a tilt adjustment can be made and re-scanned and
the two maps compared directly.

No sensors or wiring are required: the controller only positions and pauses;
the operator reads a dial indicator or feeler gauges.

## Reason

The 2026-10-11 heraldic imprecision investigation verified that the commanded
path is faithful to the source artwork (mean 0.14 mm, p90 0.26 mm against the
SVG) and that the printed error is consistent with a pen-to-surface gap that
varies with position: the force-controlled toolhead extends further where the
surface is lower, and any lateral runout in the pen carriage turns that
extension change into a drawn-line position error. Machine settings were
changed (feed, tolerance, tangential speed, 24 V Y/A rails, new Y motor) without
removing the defect, so the next step is mechanical: measure the bed-to-gantry
gap map, level what can be leveled, and re-measure.

The operator asked for a Klipper `screws_tilt_adjust`-style workflow with a 3D
visual instead of ad-hoc measurements.

## Implementation

- `tools/make_bed_gap_maps.py` emits four programs: a 5x5 grid over the used
  area (G54 X/Y +/-100 mm, bed parked) and a rotation sweep at r = 60/120/180 mm
  with 30 deg bed indexing, each in an `M0` pause variant and a `G4 P25` dwell
  variant for builds without program pause.
- `tools/bed_tilt_map.py --template` writes the CSV those programs fill in
  (`type, x, y, radius_mm, angle_deg, gap_mm`; `grid` rows use machine G54 XY,
  `ring` rows use bed-frame radius/angle, and the grid rows can be rotated to
  bed frame with `--bed-angle`).
- The analysis fits `gap = c + bx*x + by*y` (optionally `+ d*r^2`), prints the
  tilt in mm per 100 mm and its bed-frame direction, reports the residual rms
  and max, and produces the per-mount report from `--mounts "angle,radius;..."`
  or `--mounts-xy "x,y;x,y;..."` (the four gantry-rail end supports are known in
  G54 machine coordinates from the frame CAD, so Cartesian input is the normal
  case) with the required shim thickness and equivalent screw turns at the
  given thread pitch.
- The PNG shows the 3D gap surface, a top-down map with mount points marked,
  the residual after the plane fit (the warp/runout signature), and the ring
  profiles per radius.

## Verification

- Synthetic demo (0.45 mm tilt + 0.10 mm two-lobe warp + 0.01 mm noise, 61
  readings; `tmp/heraldic_diag/bed_map_demo.csv`): the tool recovered a plane of
  0.247 mm per 100 mm at 26 deg, residual rms 0.070 mm, and mount corrections
  of +0.220 / -0.493 / +0.273 mm (+0.31 / -0.70 / +0.39 M4 turns) for mounts at
  90/210/330 deg, r = 200 mm; PNG output inspected.
- `python tools\docs_index.py --check` passes (401 change notes).
- No machine motion was run; the physical measurement is the follow-up.

## Struggles and rejected approaches

- Automated sensing was rejected for this step: a data-logging sensor would
  need wiring and a carriage mount, and the operator explicitly wanted a
  workflow that requires no rewiring. The toolhead's own force sensor was also
  considered as a touch probe and deferred: the actuator has no commanded Z
  axis, and thread backlash puts it in the +/-0.1 mm class.
- Program pause (`M0`) support in the installed grblHAL build is unverified, so
  every measurement program is emitted in both pause and dwell variants.
- The first draft of the (scratch) witness-mark program lowered the pen before
  travelling to the mark and would have drawn a stray line to reach it; the
  block now always lifts, travels, then lowers.

## Risks and follow-up

- The measurement reference is wherever the indicator is mounted: keep the
  fixture identical between scans or the before/after maps are not comparable.
- Mount count, positions, and thread pitch must be entered for the actual bed
  hub before the shim numbers are actionable.
- If the residual after the plane fit stays above ~0.15 mm, leveling will not
  fix the bed and the next suspect is disc warp or bearing axial runout; the
  ring panel of the map is the evidence for that call.
- Open question carried from the diagnosis: whether a slip witness (first/last
  mark re-draw) should become part of the standard bed test set.

## Files

- `tools/bed_tilt_map.py`: new analysis tool (template, fit, mount report, PNG).
- `tools/make_bed_gap_maps.py`: new generator for the pen-up measurement
  programs.
- `docs/project/ENGINEERING_LOG.md`: session entry.

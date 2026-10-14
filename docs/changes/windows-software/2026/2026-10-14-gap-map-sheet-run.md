---
id: WSW-20261014-002
date: 2026-10-14
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - tools/make_bed_gap_maps.py
  - samples/gcode/gap_map_rot.gcode
  - samples/gcode/gap_map_rot_dwell.gcode
  - samples/gcode/gap_map_rot.csv
tags:
  - bed
  - tilt
  - gap-map
  - diagnostic
  - calibration
related:
  - HW-20261011-001
  - RPSW-20261014-002
---

# Gap-map generator: configurable radii and step, matching readings CSV, sheet-fit run

## Summary

`tools/make_bed_gap_maps.py` gains `--radii`, `--bed-step`, and `--dwell`,
and now writes a `gap_map_rot.csv` readings template that matches the
rotation program one-for-one. The committed set was regenerated for the
letter sheet already on the bed: rings at r = 60 / 90 mm, 30 deg steps,
12 stops per ring (24 readings).

The ring size shrank from 60/120/180 because the measurement runs on the
sheet on the bed: a 120 mm ring leaves a letter sheet (inscribed radius
about 105 mm) and would read the bed or corner tape instead of the paper.

## Reason

Operator decision: the toolhead touch probe is not trusted for this
measurement - "im using a dc motor attached to a motor driver so i wont get
a consistent measurement like i would with a stepper." The pulse-timed DC
lift gives a relative signal at best (the repository's own note puts that
probing in the +/-0.1 mm class), so the mechanical gauge route - dial
indicator or feeler gauges - is the measurement of record. As a bonus it
never touches the paper, so the sheet already on the bed survives every
adjustment iteration unchanged.

## Implementation

- Generator options: `--radii` (default 60,120,180), `--bed-step` (default
  30 deg), `--dwell` seconds for the `_dwell` variants (default 25).
- `rotation_csv()` writes `gap_map_rot.csv` with one row per stop, so the
  radius/angle bookkeeping cannot drift from the program.
- Programs remain pen-up only: the controller positions and pauses; no M3,
  no probing, no mark of any kind. The operator reads the gap at each stop.

## Verification

- Regenerated into `samples/gcode` with `--radii 60,90`: rotation programs
  (M0 and `_dwell` variants) and the 24-row CSV; program headers state the
  radii and the step.
- Generator self-checks: radii positive, bed step divides 360 into at least
  three steps, dwell positive.
- `python tools\docs_index.py --write` / `--check` - indexes valid.
- **Pending:** read the 24 stops and feed the filled CSV to
  `bed_tilt_map.py` with the four rail-end mounts and `--rail-mounts`.

## Struggles and rejected approaches

- The touch-probe route (`bed_mesh_probe.py`) is deferred for the final
  numbers per the operator's DC-lift objection; it stays available for
  quick, clearly-relative checks.
- The generic `bed_tilt_map.py --template` writes all three default radii;
  having the generator emit its own matching CSV removes that mismatch.

## Risks and follow-up

- Reading resolution is the instrument's: 0.01 mm class for a dial
  indicator, about 0.05 mm for feeler gauges.
- Check the tip-to-paper clearance at the first stop before starting the
  ring; the program pauses before every index so it can be eyeballed.
- If the post-plane residual stays above ~0.15 mm, the next suspect remains
  disc warp or bearing axial runout (`HW-20261011-001`).

## Files

- `tools/make_bed_gap_maps.py`: options and CSV emission.
- `samples/gcode/gap_map_rot.gcode`, `gap_map_rot_dwell.gcode`,
  `gap_map_rot.csv`: the sheet-fit rotation set.
- `docs/project/ENGINEERING_LOG.md`: log entry.

---
id: WSW-20260922-002
date: 2026-09-22
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
  - hardware
status: implemented
components:
  - samples
  - docs/report
  - docs/testing/gcode
  - firmware/pen_pressure/e07d_cs1238_known_mass_calibration/pc_logger
tags:
  - repository-hygiene
  - evidence
  - samples
related:
  - WSW-20260922-001
  - RPSW-20260922-033
---

# File outstanding working-tree artifacts into the repository

## Summary

Every artifact that had been left loose in the working tree was filed into the
repository. Nothing was discarded, and the tracked documents that cite these
files now point at content that exists in a fresh clone.

## Reason

An audit of the working tree found three separate gaps. Tracked files were
modified but never committed, so those edits existed only on one machine.
Generated sample programs, report renders, and a test program sat untracked.
Most seriously, the E-09C lab note already cited raw calibration captures by
path, but those captures were not in the repository — so the cloud backup was
missing evidence its own documents reference.

## Implementation

- Committed the outstanding tracked edits: the summer-progress presentation and
  two PC817 KiCad project files.
- Moved both generated sample programs into the documented `samples/gcode/`
  location: `kindergarten-house-sun.gcode` and `m06-radius-sweep.gcode`. The one
  document that cited the old `samples/svg/` path was updated.
- Committed the thirteen presentation slide renders under
  `docs/report/Theta_Pen_Plotter_Summer_Progress_Update/` and referenced them
  from `docs/report/README.md` so they are discoverable.
- Committed `docs/testing/gcode/x-rate-repeat.nc`.
- Committed the three `pc_logger/results/run_*` capture sets for the
  2026-09-22 E-09C known-mass calibration, and corrected the lab note's "is
  local at" wording now that the run is retained in the repository.

## Verification

- `git status --short` no longer lists any of these paths as modified or
  untracked.
- `python tools\docs_index.py --write` and `python tools\docs_index.py --check`
  pass, so the moved sample reference is still valid.
- The E-09C lab-note path
  `firmware/pen_pressure/e07d_cs1238_known_mass_calibration/pc_logger/results/run_2026-09-22_08-29-03/`
  now exists in the repository.

## Struggles and rejected approaches

Adding ignore rules for the sample, render, and capture files was rejected. It
would have made `git status` look clean while keeping cited evidence out of the
repository, which inverts the purpose of the backup. Deleting them was also
rejected. The only deletions in this pass were the two root-level script-bug
files and the abandoned `force_calibration_test/` skeleton, both explicitly
authorized by the project owner.

## Risks and follow-up

`x-rate-repeat.nc` repeats most of the tracked `x-axis-rate-repeat.gcode`
without its header comments or `G94`. It is retained because it may be the
exact program streamed during the M-02 X-axis rate check; consolidate the two
only after confirming which file the controller received. The two `.kicad_pro`
files will keep showing incidental churn whenever KiCad is opened.

The repository `.gitattributes` applies `* text=auto eol=lf`, so the committed
capture CSVs are stored with LF line endings rather than the CRLF the logger
wrote. Sample values and record counts are unchanged, but the stored files are
not byte-identical to the bench originals.

## Files

- `samples/gcode/kindergarten-house-sun.gcode`: moved from `samples/svg/`.
- `samples/gcode/m06-radius-sweep.gcode`: moved from `samples/svg/`.
- `docs/report/lab-notes/2026-09-07-converter-house-sun-and-soft-limits.md`: update the sample program path.
- `docs/report/Theta_Pen_Plotter_Summer_Progress_Update/`: add the thirteen slide renders.
- `docs/report/README.md`: note where the rendered slide set is kept.
- `docs/testing/gcode/x-rate-repeat.nc`: retain the streamed test program.
- `firmware/pen_pressure/e07d_cs1238_known_mass_calibration/pc_logger/results/`: retain the E-09C raw captures.
- `docs/report/lab-notes/2026-09-22-e-09c-cs1238-known-mass-calibration.md`: state that the run is retained in the repository.
- `docs/report/Theta_Pen_Plotter_Summer_Progress_Update.pptx`: commit the outstanding presentation edit.
- `hardware/pc817-interface/pc817-interface.kicad_pro`: commit the KiCad format migration.
- `hardware/pc817-interface/pc817-perfboard-v2-minwire.kicad_pro`: commit the corrected internal filename reference.

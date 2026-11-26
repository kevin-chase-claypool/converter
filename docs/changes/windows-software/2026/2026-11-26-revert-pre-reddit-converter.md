---
id: WSW-20261126-005
date: 2026-11-26
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/
  - tools/cmyk_calibrate.py
tags:
  - rollback
  - cmyk
  - reddit-reference
  - edge-flow
  - app-stability
  - regression
related:
  - WSW-20261122-002
  - RPSW-20261124-001
  - HW-20261126-001
---

# Revert the converter to its pre-Reddit baseline

## Summary

The Windows converter and its CMYK calibration CLI are restored to commit
`2a52202`, the last state before the Reddit-inspired Edge-flow work began in
`4c44fc5`. The app again exposes the original CMYK tool without the later
Edge-flow, guided CMYK Photo, coherent-flow, stage-workspace, headless-export,
or embedded Plotterfun Extended additions.

The rollback is limited to converter code and converter-facing documentation.
Independent machine calibration, P100 firmware changes, lab notes, meshes, and
unrelated working-tree files remain untouched.

## Reason

The project owner reported that the converter had been unstable ever since the
attempt to reproduce the Reddit user's CMYK image. Restoring the last known
pre-reference tree is the clearest recovery boundary and avoids carrying a
large, interconnected set of experimental screening and workflow changes
forward while the app is being stabilized.

## Implementation

- Restored `software/` in full to `2a52202`, the parent of
  `4c44fc5` (`Add edge-flow CMYK streamlines`).
- Restored `tools/cmyk_calibrate.py` and removed
  `tools/export_cmyk_headless.py`, which belonged to the later CMYK workflow.
- Restored the converter-facing sections of `docs/HANDOFF.md`,
  `docs/integration/INTERFACES.md`, and
  `docs/testing/CMYK_CALIBRATION.md` to the same baseline.
- Kept the separate P100 registration change, hardware calibration evidence,
  bed meshes, and unrelated dirty-worktree changes.
- Marked the Reddit-era software roadmap and decision material as historical
  so it cannot be mistaken for current app behavior.

## Verification

- `py -3.13 -m unittest -q` across `test_cmyk_tab`, `test_cmyk_sheet`,
  `test_generator_tabs`, `test_plotterfun_tab`, and `test_preview_view`
  passed `186` tests with one expected OpenGL-context skip.
- `py -3.13 -m unittest discover -q -s software\tests -p "test_*.py"` passed
  all `623` restored converter tests with one expected OpenGL-context skip.
- `py -3.13 tools\docs_index.py --write` rebuilt five indexes from `556`
  change notes. The first `--check` exposed one link in a historical note to
  the removed headless exporter; after changing that reference to plain code,
  the final check passed all documentation links.
- The repository's `python` command resolves to the Microsoft Store stub on
  this host; verification used the installed Python 3.13 launcher directly.

## Struggles and rejected approaches

The first Reddit change added a separate screen style, but the following four
days repeatedly replaced its renderer, tone handling, path joining, UI
registration, export contract, and tests. Disabling only the first option
would leave those interdependent changes active, so it was not a reliable
return to the owner's requested state.

Reverting the entire repository would also remove unrelated P100 and hardware
calibration work, so only the converter and matching current-state documents
were restored.

## Risks and follow-up

This broad rollback intentionally removes later converter improvements that
were committed during the same period, including post-compensation reach
guarding, post-planner screen chaining, the adaptive CMYK workspace, and the
vendored Plotterfun Extended tool. They remain recoverable from Git history
and should be reintroduced one at a time only after the restored app is
confirmed stable.

Saved recipes or generated CMYK sets that depend on the removed screen styles
will no longer load identically. Begin from the restored CMYK tool's supported
settings and create a fresh baseline before evaluating each later feature.

## Files

- `software/`: restored the complete converter application and test tree.
- `tools/cmyk_calibrate.py`: restored pre-Edge-flow calibration behavior.
- `tools/export_cmyk_headless.py`: removed with the superseded export workflow.
- `docs/HANDOFF.md`: restored converter architecture description.
- `docs/integration/INTERFACES.md`: restored the pre-rollback host contract.
- `docs/testing/CMYK_CALIBRATION.md`: restored supported screen descriptors.
- `docs/project/ROADMAP.md`: marks the Reddit-era converter work as historical.
- `docs/decisions/ADR-011-cmyk-stage-workspace.md`: marked superseded.
- `docs/decisions/ADR-012-bed-stock-and-tape-margin.md`: records deferred
  converter implementation while retaining the physical geometry decision.
- `docs/project/ENGINEERING_LOG.md`: records the rollback and verification.

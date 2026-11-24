---
id: WSW-20261124-003
date: 2026-11-24
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/gcode.py
  - software/converter_core/motion_check.py
  - software/tests/test_reach_guard.py
tags:
  - reach
  - soft-limits
  - bed-compensation
  - preflight
  - cmyk
  - magenta
related:
  - WSW-20261124-001
  - ADR-009
---

# Guard machine reach after bed compensation

## Summary

The converter now reserves the bed-compensation profile's maximum correction
before clipping artwork to the reachable circle. G-code preflight also rejects
any final G54 point beyond the configured machine-reach radius.

## Reason

The magenta pass around blocks 145,000-155,000 had no runaway G-code jump, but
132 final machine points exceeded the nominal `180 mm` radius. The maximum was
`180.547 mm` at block `154,593`, with X `180.5312 mm` against the controller's
displayed X maximum of `179.434 mm`.

P100 still owns centering, and bed compensation still owns its measured
correction. The defect was ordering: clipping to `180 mm` happened before the
profile's correction was added, and preflight did not inspect final XY radius.

## Implementation

- `plan_program()` loads the compensation profile before clipping.
- The planning radius becomes:

  ```text
  min(bed radius, machine reach) - profile maximum correction
  ```

- With default reach `180 mm` and profile maximum `1.142 mm`, the planning
  radius is `178.858 mm`.
- G-code headers record `(reach guard 180.000 mm, planning radius 178.858 mm)`.
- `analyse_gcode()` records the largest emitted G54 XY radius and its source
  line.
- Preflight blocks any program whose final radius exceeds the configured reach
  by more than `0.001 mm`.

## Verification

- `test_reach_guard.py` generates compensated edge lines that previously
  reached `180.431 mm`; they now remain at or below `180 mm`.
- A second regression supplies a synthetic `X180.5 Y2.0` move and requires a
  machine-reach preflight failure.
- The full converter suite passes 684 tests with one expected OpenGL-context
  skip.
- The current pre-guard magenta file is rejected at `180.568 mm`, proving the
  detector catches the physical run that prompted this change.

## Struggles and rejected approaches

- Checking only base artwork radius was rejected because compensation happens
  later in the machine transform.
- Post-emission point deletion was rejected because it can break path
  continuity. Reserving the profile maximum before clipping keeps paths intact.
- Treating the issue as an A-axis rate problem was rejected; the angular step
  and rate checks were already passing.

## Risks and follow-up

- The safety inset sacrifices up to the profile's maximum correction at the
  extreme edge. This is deliberate until the extrapolated edge field is
  physically verified.
- The final low-level safety bound is still grblHAL and its soft limits; the
  converter guard uses the declared machine-reach radius.
- Cyan and black must be regenerated and their preflight must pass before those
  plates are printed.

## Files

- `software/converter_core/gcode.py`: compensation-aware planning radius and
  header record.
- `software/converter_core/motion_check.py`: final-radius measurement and hard
  preflight failure.
- `software/tests/test_reach_guard.py`: edge-generation and preflight
  regressions.
- `software/README.md`: current reach behavior.
- `docs/project/ROADMAP.md`: implementation and remaining edge-verification
  status.

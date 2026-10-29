---
id: WSW-20261029-007
date: 2026-10-29
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/settings.py
  - software/tests/test_bed_compensation.py
  - software/tests/test_cmyk_tab.py
  - samples/gcode/bed-error-compensation-2026-10-29-dense-v3-centered.json
tags:
  - bed-compensation
  - dense-mesh
  - default-profile
  - owner-override
  - coverage
related:
  - WSW-20261029-006
---

# Promote the centered dense v3 bed profile

## Summary

The project owner selected candidate `18bfb4ed1c33` as the default bed
compensation profile despite its independent verification missing the formal
M-12 maximum and improvement thresholds. The default measured coverage is now
`165.100 mm` radius (`13.0 in` diameter) instead of the previous extrapolated
`171.450 mm` radius (`13.5 in` diameter).

This is an explicit owner override, not a claim that the candidate passed the
standard promotion gates.

## Reason

The centered dense-v3 profile reduced aggregate RMS from `0.550` to
`0.486 mm` and improved every per-angle RMS. The owner judged the result better
for the current machine despite the maximum moving from `1.163` to `1.171 mm`
and the improvement being `11.6%`, below the required `30%`.

The measured correction remains safe: its maximum is `1.142 mm`, below the
`5 mm` profile bound.

## Implementation

- Add the promoted profile as
  `samples/gcode/bed-error-compensation-2026-10-29-dense-v3-centered.json`.
- Set `DEFAULT_BED_COMPENSATION_PATH` to that profile.
- Set the default bed margin and compensation diameter to the measured
  `165.100 mm` radius service envelope.
- Keep the prior `4bad792e35ad` 13.5-inch profile available for explicit
  selection.
- Update planner and CMYK defaults tests to require fingerprint
  `18bfb4ed1c33`.

## Verification

- The promoted file loads with fingerprint `18bfb4ed1c33`, coverage
  `165.100 mm`, and maximum correction `1.142 mm`.
- The default planner emits the compensated profile header and accepts paths
  within the measured 13-inch field.
- Explicit selection of the older 13.5-inch profile remains supported with an
  explicit 6.35 mm margin.
- Focused planner and CMYK tests pass.

## Struggles and rejected approaches

The normal gate-qualified decision remains to retain `4bad792e35ad`: the
centered dense-v3 candidate missed both the `0.90 mm` maximum and `30%`
improvement requirements. That failed result is preserved rather than
rewritten as a pass.

The prior 13.5-inch coverage cannot be retained as the default because the new
measured profile only covers 13.0 inches.

## Risks and follow-up

The promoted profile is selected by owner judgment despite an objective
verification failure. The outer 6.35 mm annulus is no longer compensated by
default. Revisit candidate refinement or mechanical diagnosis before expanding
the field again.

## Files

- `software/converter_core/settings.py`: default profile and 13-inch field.
- `software/tests/test_bed_compensation.py`: default profile and coverage
  expectations.
- `software/tests/test_cmyk_tab.py`: CMYK inheritance expectations.
- `samples/gcode/bed-error-compensation-2026-10-29-dense-v3-centered.json`:
  promoted profile, byte-identical to candidate `18bfb4ed1c33`.
- `software/README.md`, `docs/integration/INTERFACES.md`,
  `docs/decisions/ADR-009-post-registration-bed-compensation.md`, and
  `docs/testing/TEST_PLAN.md`: current-state and override records.

---
id: WSW-20261126-009
date: 2026-11-26
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/gcode.py
  - software/converter_core/motion_check.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_reach_guard.py
  - software/tests/test_program_set_identity.py
  - software/tests/test_cmyk_tab.py
  - software/tests/test_theta_feed.py
  - software/README.md
  - docs/integration/INTERFACES.md
  - docs/decisions/ADR-009-post-registration-bed-compensation.md
  - docs/project/ROADMAP.md
related:
  - WSW-20261124-003
  - WSW-20261126-007
  - WSW-20261126-008
tags:
  - cmyk
  - bed-compensation
  - machine-reach
  - pen-envelope
  - preflight
  - set-identity
  - g54
  - row-lock
  - safety
---

# Harden CMYK reach and set identity

## Summary

CMYK planning now reserves both the active profile's maximum compensation
vector and half the physical pen width before clipping. The finished `G0/G1`
program is re-read before release and rejected if the path plus ink envelope
exceeds the configured machine reach. Multi-ink sets are also rejected unless
every file declares the same G54 frame center, compensation profile, reach,
planning radius, and expected Wave row angle.

## Reason

Pre-compensation clipping alone allowed the profile to move a boundary point
outward after the radius check. The active default profile can produce a final
machine point around `180.64 mm` from a nominal `180 mm` boundary. Existing
preflight checked A-axis limits but not final X/Y or the physical ink edge.

The CMYK worker used one shared frame and profile by construction, but no
cross-file gate independently parsed the generated headers. A reporting or
plumbing defect could therefore leave a mismatch undetected until paper.

## Implementation

- `plan_program()` loads compensation before clipping and computes:

  ```text
  planning radius =
      min(bed radius, machine reach)
      - profile maximum correction
      - pen diameter / 2
  ```

- G-code headers record reach, compensation reserve, pen-radius reserve, and
  effective planning radius.
- Preview fit actions and the over-scale warning use the same effective
  planning radius, so the conservative safety inset is visible rather than
  appearing as unexplained clipping.
- `contours_to_gcode()` re-reads the completed program and raises if the
  largest emitted `G0/G1` point plus pen radius exceeds the configured reach.
  G53 park moves remain excluded because they intentionally use the machine
  frame outside the bed envelope.
- `gcode_program_identity()` parses G54, frame center, compensation
  fingerprint, reach reserves, planning radius, and Wave row angle.
- `validate_program_set_identity()` rejects a CMYK set with any mismatch.
  `ProgramAnalysisWorker` runs this gate before emitting results, so a failed
  set never reaches Save.
- The set manifest records the parsed program identity per ink in addition to
  output hashes.

## Verification

- Reach regressions cover compensated edge artwork, uncompensated pen-envelope
  reservation, and rejection of a program whose ink envelope exceeds reach.
- Set-identity regressions accept matching raw and row-locked sets and reject
  mismatched frame centers, profile fingerprints, and row angles.
- A CMYK worker regression confirms a mismatched layer frame fails the whole
  set before results are released.
- The complete affected CMYK, generator, compensation, placement, reach, and
  identity modules pass `211` tests with one expected OpenGL-context skip.
  Complete converter discovery passes `639` tests with one expected
  OpenGL-context skip. Python compilation passes for all changed Python files.

## Struggles and rejected approaches

Checking only the uncompensated artwork radius was rejected because
compensation is applied afterward. Post-emission deletion was rejected because
it can break path continuity. Comparing only manifests was rejected because
the manifest is created after files are already written; the actual generated
G-code headers must pass before publication.

## Risks and follow-up

The pen-radius reserve is conservative and reduces the tool-centreline planning
radius by `pen_diameter / 2`. It protects the physical ink edge, not only the
pen-tip center. The planner guard uses the configured reach; grblHAL soft
limits and live HOME + REGISTER verification remain the final controller and
hardware authority. The outer compensation annulus remains extrapolated until
its separate physical verification.

## Files

- `software/converter_core/gcode.py`: compensation and pen-envelope reserve,
  identity headers, and post-emission reach rejection.
- `software/converter_core/motion_check.py`: final path/ink radius analysis,
  reach preflight, G-code identity parsing, and set validation.
- `software/generator_tabs/cmyk_tab.py`: pre-release CMYK set identity gate and
  manifest identity records.
- `software/tests/`: reach, identity, and worker mismatch regressions.
- `software/tests/test_theta_feed.py`: emitted header contract.
- `software/README.md`: current planning, preflight, and set-identity behavior.
- `docs/integration/INTERFACES.md`: host/controller reach and multi-file
  identity contract.
- `docs/decisions/ADR-009-post-registration-bed-compensation.md`: lasting
  compensation safety consequences.
- `docs/project/ROADMAP.md`: restored hardening status and remaining physical
  validation boundary.

---
id: WSW-20261030-002
date: 2026-10-30
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: superseded
components:
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
  - tools/check_cmyk_wave_spacing.py
  - software/tests/test_check_cmyk_wave_spacing.py
  - samples/gcode/Ben2/PXL_20201128_211515508-cmyk-cyan.gcode
  - samples/gcode/Ben2/PXL_20201128_211515508-cmyk-magenta.gcode
  - samples/gcode/Ben2/PXL_20201128_211515508-cmyk-yellow.gcode
  - samples/gcode/Ben2/PXL_20201128_211515508-cmyk-black.gcode
  - samples/gcode/Ben2/PXL_20201128_211515508-cmyk-set.json
  - samples/gcode/Ben2/PXL_20201128_211515508-cmyk-cyan-compensated.gcode
  - samples/gcode/Ben2/PXL_20201128_211515508-cmyk-magenta-compensated.gcode
  - samples/gcode/Ben2/PXL_20201128_211515508-cmyk-yellow-compensated.gcode
  - samples/gcode/Ben2/PXL_20201128_211515508-cmyk-black-compensated.gcode
  - samples/gcode/Ben2/PXL_20201128_211515508-cmyk-compensated-set.json
tags:
  - cmyk
  - wave-screen
  - row-spacing
  - bed-compensation
  - final-machine-coordinates
  - ben2
related:
  - WSW-20261029-008
  - WSW-20261029-007
  - ADR-009
  - WSW-20261030-003
---

# Preserve exact Wave row pitch across final machine coordinates

## Summary

The normal CMYK Wave-screen path now removes bed compensation by default so
its equidistant source rows remain equidistant in the final machine `X/Y`
commands. The guard is disabled for non-Wave styles, can be explicitly turned
off for a positional-correction tradeoff, and is recorded in the set manifest.
The canonical Ben2 CMYK set has been regenerated without compensation and
audited across all four inks.

**Superseded:** the no-compensation workaround was replaced by the row-locked
projection in `WSW-20261030-003`, which keeps the measured profile active while
retaining exact row pitch.

## Reason

The previous audit decoded compensated G-code back into paper space. That
correctly showed a uniform source lattice, but removed the displacement field
from consideration before measuring the coordinates grblHAL would execute.
Direct final-machine-space sampling found that active profile `18bfb4ed1c33`
changed adjacent row gaps by `0.224-0.323 mm`. The yellow program ranged from
`1.731065` to `2.054542 mm` around a `1.91546 mm` source pitch.

An arbitrary non-uniform displacement field cannot preserve an exact uniform
row lattice. Exact spacing and positional residual correction therefore
cannot both be guaranteed by applying the current profile after planning.
The operator requirement is exact spacing, so Wave output must default to the
uncompensated displacement path.

## Implementation

- Added **Preserve exact row pitch (skip bed compensation)** to the CMYK
  Screen controls. It starts enabled and is enabled in the UI only for
  **Wave screen - equidistant rows**.
- `apply_tab_settings` clears `bed_compensation_path` when that style and guard
  are active. Other screen styles continue to inherit the Machine-tab profile.
- Unchecking the guard explicitly restores the selected profile and produces
  an `OFF - compensation may alter pitch` pass-summary warning.
- Version-3 set manifests record both the effective compensation path and
  `screen.preserve_exact_row_pitch`.
- Replaced the canonical Ben2 four-file set with XY-only, no-compensation
  `waves_even` programs. Preserved the former active profiles as the four
  `-compensated` files and matching set manifest for direct comparison.
- The canonical set keeps the same source image, page and frame centre,
  artwork scale, screen angles, pitch, masks, ink controls, and pen offsets as
  the prior Ben2 set. Only the compensation displacement path is removed.

## Verification

- A final-machine-space audit sampled 199 columns in each effective
  `-15/-75/0/-45 degree` screen frame:

| Ink | Minimum | Median | Maximum | Spread |
|---|---:|---:|---:|---:|
| Cyan | `1.914111 mm` | `1.915526 mm` | `1.916586 mm` | `0.002476 mm` |
| Magenta | `1.914135 mm` | `1.915554 mm` | `1.916323 mm` | `0.002188 mm` |
| Yellow | `1.915400 mm` | `1.915465 mm` | `1.915500 mm` | `0.000100 mm` |
| Black | `1.914421 mm` | `1.915529 mm` | `1.915977 mm` | `0.001555 mm` |

- All four canonical files pass `tools/check_macros.py`.
- All four pass `tools/check_gcode_motion.py --strict` with zero A velocity,
  zero bed rotation, zero bare `G0` rotations, and zero bed-path bow.
- `tools/check_cmyk_wave_spacing.py` verifies manifest hashes, the active
  spacing guard, empty compensation path, and all four final-machine row
  lattices in one command.
- A dedicated dark-tone regression compares full and 15 % tone at the same
  sine phase. The sampled common wave offset is `1.951 mm` at full tone versus
  `0.295 mm` at 15 %, while all 15 adjacent gaps remain exactly `4.000000 mm`
  and every row baseline remains fixed.
- Canonical SHA-256:
  cyan `5CC24D7DD32F8DA43167A0DBC803109D51DBA6394E92FE2CDBD21352EA274290`,
  magenta `718706CD5E275D1D883C4B265440ECE353C6123807448B69C6B3BEFB6F028DC4`,
  yellow `590E9B4C60965EDF33255A2A22885029023C382BE780D675A8DB03A9D1A49563`,
  black `2789596CB5BADC4A0026726CCA773A67BF88E8B1C251DCAA035FE672A5F7683B`.
- The focused CMYK tab suite passes `96` tests.
- The complete converter suite passes `582` tests with one expected
  OpenGL-context skip.

## Struggles and rejected approaches

The first red-dot investigation measured reconstructed paper paths and
concluded that only image-mask row omission remained. That was a false
negative because inverse compensation removed the machine-visible distortion.

The first spacing-guard regression also used a fake host with an already-empty
compensation path, so it could not detect a failure to clear a real profile.
The test now supplies `converter.default_settings()` and separately verifies
that Wave output clears it while another screen style retains it.

Refining the mesh cannot resolve the conflict: a denser arbitrary correction
field can improve positional reconstruction while still changing row spacing.
No-operator-input compensation was rejected for this Wave style because it
would silently violate the hard spacing requirement.

## Risks and follow-up

The canonical Wave set intentionally omits residual bed-position correction.
Its maximum physical placement error is not re-established by this software
audit and must be accepted or reduced mechanically. A fresh paper print is
still required to confirm that the machine follows the regular lattice and
that the remaining positional error is acceptable.

Future work that needs both exact spacing and positional correction must
measure a mechanical correction that preserves the lattice, or define a
constrained correction model whose differential X/Y displacement does not
change row normals. Applying the unmodified dense map after planning is not a
valid solution.

## Files

- `software/generator_tabs/cmyk_tab.py`: spacing guard, UI state, summary, and
  manifest metadata.
- `software/tests/test_cmyk_tab.py`: non-empty-profile regression and manifest
  coverage.
- `tools/check_cmyk_wave_spacing.py`: repeatable final-machine row-spacing
  verifier.
- `software/tests/test_check_cmyk_wave_spacing.py`: verifier geometry and
  guard-metadata regressions.
- `software/README.md`: current operator behavior and tradeoff.
- `docs/integration/INTERFACES.md`: effective compensation exception.
- `docs/decisions/ADR-009-post-registration-bed-compensation.md`: lasting
  incompatibility between arbitrary compensation and exact Wave pitch.
- `docs/testing/TEST_PLAN.md`: corrected M-13 acceptance evidence.
- `docs/project/ROADMAP.md`: current status and physical-print follow-up.
- `docs/project/ENGINEERING_LOG.md`: correction and superseded hypothesis.
- `docs/report/lab-notes/2026-10-30-ben2-yellow-row-end-boundary.md`: all-four
  final-machine measurements.
- `samples/gcode/Ben2/PXL_20201128_211515508-cmyk-{cyan,magenta,yellow,black}.gcode`:
  canonical no-compensation outputs.
- `samples/gcode/Ben2/PXL_20201128_211515508-cmyk-set.json`: canonical recipe,
  guard state, hashes, and final audit.
- `samples/gcode/Ben2/PXL_20201128_211515508-cmyk-{cyan,magenta,yellow,black}-compensated.gcode`:
  preserved failing-comparison outputs.
- `samples/gcode/Ben2/PXL_20201128_211515508-cmyk-compensated-set.json`:
  comparison recipe and hashes.

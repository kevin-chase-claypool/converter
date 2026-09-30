---
id: WSW-20260930-001
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
status: implemented
components:
  - software/converter_core/settings.py
  - firmware/grblhal/macros/P100.macro
  - firmware/grblhal/macros/P112.macro
  - firmware/grblhal/macros/P103.macro
tags:
  - theta
  - kinematics
  - a-axis
  - calibration
  - registration
  - drift
related:
  - docs/report/lab-notes/2026-09-30-p112-a-index-spacing-repeat.md
  - docs/integration/INTERFACES.md
---

# Calibrate the bed ratio from the measured A-index spacing

## Summary

The converter now emits A with the measured effective bed ratio `12.03324`
(4331.97 A motor-degrees per bed revolution) instead of the nominal `12.0`
(4320), and the P100/P112/P103 outer-index gate is re-derived from `4320 +/- 15`
to `4332 +/- 10`.

## Reason

The 2026-09-29-to-30 mandala print showed registration ghosting. Diagnosing it
against three independent P112/P100 outer-index surveys gave
`4331.818` (2026-09-11), `4331.930` (2026-09-24) and `4332.153` (2026-09-30)
motor-degrees per bed revolution, a total spread of 0.335. The old nominal
4320 made every commanded bed revolution land about 1 degree short, so the
converter's `theta_drive_ratio = 12.0` was wrong by +0.277%.

## Implementation

- `software/converter_core/settings.py`: `theta_drive_ratio` default `12.0` ->
  `12.03324`, with the measurement basis in the comment; the UI default string
  follows. Every A value, the radius-aware A feed
  (`360 * theta_drive_ratio = 4331.97` motor-degrees per bed revolution) and
  the preview derive from this one setting.
- `firmware/grblhal/macros/P100.macro`, `P112.macro`, `P103.macro`:
  `a_expected_spacing` `4320.0` -> `4332.0`, `a_spacing_tolerance` `15.0` ->
  `10.0`, with the three measurements recorded as the comment rationale.
- Current-state documents updated to the measured ratio: `software/README.md`,
  `docs/integration/INTERFACES.md`, `firmware/README.md`,
  `firmware/grblhal/README.md`,
  `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`,
  `firmware/grblhal/macros/README.md`, `docs/testing/TEST_PLAN.md`,
  `docs/HANDOFF.md`, `docs/architecture/SYSTEM_ARCHITECTURE.md` and the root
  `ONTOLY_PROMPT.md` contract. The nominal 60T:720T hardware description is
  retained as nominal; the effective ratio is stated alongside it.
- `docs/project/ROADMAP.md`: the "Re-derive the outer A index spacing budget"
  item is closed, and the coarse M-05 bed-ratio item is recorded as
  established by measurement.

## Verification

- All 72 unit tests in `software/tests/` pass with the new default.
- `python tools\docs_index.py --write` and `--check` pass.
- No print has been run with the new ratio yet; the pointer/dial check and a
  first test print remain open (below).

## Struggles and rejected approaches

- The P112 macro validates the spacing but never prints it; the value had to be
  reconstructed from the four `PRB` capture lines with the macro's own formula.
- A `$103`, microstep, or motor-step-angle error was considered and rejected as
  the cause: such an error would scale the pulse count by about 2x or 0.5x, not
  1.0028x. The measurement is an effective mechanical ratio.
- Tightening the gate rather than leaving the 81%-consumed `4320 +/- 15` band
  was chosen because the observed spread (0.335 across three sessions) supports
  `+/- 10` with a large margin.

## Risks and follow-up

- The root cause of the 0.277% mechanical discrepancy is not identified (belt
  pitch, effective pulley circumference, or compliance). The measured deviation
  is almost exactly two belt teeth per revolution (0.278% of the 1440 mm ring
  circumference, 1.27 mm of diameter), so the leading candidates are printed-ring
  scale/seams and the belt's own pitch tolerance; only the effective ratio is
  calibrated, and the 100-tooth span check that would identify the source is
  recorded in the lab note.
- Existing G-code files, including `samples/gcode/mom.gcode`, were emitted with
  the old ratio and must be regenerated before a reprint is expected to show
  the correction.
- Unverified: a magnet-independent pointer check (rim mark, `G91 G0 A4320`,
  expect about 1 degree of shortfall at the old setting) and a first print with
  the new ratio; both should be recorded before the ratio is treated as
  production-calibrated.

## Files

- `software/converter_core/settings.py`: measured ratio default and rationale.
- `firmware/grblhal/macros/P100.macro`, `P112.macro`, `P103.macro`: re-derived
  spacing gate.
- Current-state docs listed under Implementation.
- `docs/report/lab-notes/2026-09-30-p112-a-index-spacing-repeat.md`: raw
  evidence for the third survey.
- `docs/project/ENGINEERING_LOG.md`: dated entry for this session.

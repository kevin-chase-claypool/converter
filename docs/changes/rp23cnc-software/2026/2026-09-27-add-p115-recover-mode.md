---
id: RPSW-20260927-002
date: 2026-09-27
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - windows-software
status: implemented
components:
  - firmware/grblhal/macros/P115.macro
  - tools/validate_homing_macro.py
  - software/converter_core/gcode.py
  - software/converter_core/settings.py
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_theta_feed.py
tags:
  - p115
  - gp27
  - handshake
  - error-39
  - recover
  - f-05a
related:
  - RPSW-20260927-001
  - ADR-007
---

# Add a lift-and-continue recover mode to the P115 handshake

## Summary

The normal M3/M5 handshake wait now has a recover mode. On a timeout `P115`
prints a warning, issues `M5` to lift the pen to the fail-safe state, dwells
for the pen-up clearance, and returns without `error[39]`, so the program
continues on the next command instead of aborting the sheet.

## Reason

The operator wants complex prints to tolerate the occasional `error[39]` miss
that has been occurring: cancel the waiting call, lift the pen, and resume at
the next command. The existing warn-only fallback only dwelled and continued,
which still left a risk of dragging the pen when the missed transition was an
`M5` lift. Forcing `M5` on a miss removes that drag risk; the cost of a missed
`M3` is that one stroke is drawn in the air, which the operator accepts for a
long print.

## Implementation

- `firmware/grblhal/macros/P115.macro`: added a `W2` recover flag. Each timeout
  branch now has a recover path that prints `P115 WARNING ...`, issues `M5`,
  dwells `A` seconds, and returns `[0]`. The strict, `Q7`, and `W1` paths are
  unchanged; `W1` is now used only for the end-of-print full-retract fallback.
- `software/converter_core/settings.py`: renamed the `toolhead_handshake_warn_only`
  setting to `toolhead_handshake_recover` and updated its checkbox label.
- `software/converter_core/gcode.py`: `handshake_command()` emits
  `A<pen-up dwell> W2` around each normal M3/M5 transition; the first-down
  completion bound is unchanged. `append_full_retract()` emits `A3 W1` (warn +
  dwell, no lift) because the pen is already up and the Aux0/GP28 arm drives
  that retract.
- `software/qt_svg_to_gcode.pyw`: wired the recover checkbox into the Pen group
  and the settings collector. (The previous warn-only checkbox existed in
  `CHECKBOX_FIELDS` but was never exposed in the Qt UI.)
- `tools/validate_homing_macro.py`: the P115 contract now permits exactly two
  guarded `M5` recover lifts and still forbids axis motion, Aux0, M3, and `$H`.

## Verification

- `python tools\validate_homing_macro.py` passes with the new recover tokens,
  the two-guarded-`M5` count, and the unchanged forbidden-command scan.
- `python -m unittest discover -s software\tests -p "test_*.py"` passes. New
  coverage asserts the recover emission sequence `G65 P115 Q0 A0.8 W2` /
  `G65 P115 Q1 B12 A0.8 W2` / `G65 P115 Q1 A0.8 W2` / `G65 P115 Q0 A3 W1` and
  that the setting stays off by default.

**Not verified:** nothing in this change has run on the controller. `W2`
argument delivery through `G65`, the `M5`-inside-macro behaviour, and the
lift-then-continue path still need the motorless macro checks and the F-05A
bench session. The converter's emitted strings are the only half proven here.

## Struggles and rejected approaches

- Issuing `M5` during the end-of-print full-retract `Q0` was rejected: the pen
  is already up there and the Aux0/GP28 arm drives that retract, so a normal
  clear adds nothing and its interaction with the arm is unverified. That call
  stays `W1` (warn + dwell).
- Adding a third independent policy was rejected; recover folds into the
  existing opt-in slot, with the full-retract edge case kept as `W1`.

## Risks and follow-up

- `W2` masks a genuinely stuck toolhead signal, and a missed `M3` draws the
  following stroke in the air, so it remains an explicit opt-in and must not be
  used as the commissioning path.
- `M5` inside a macro is already proven by `P100`/`P111`, but `W2`'s
  lift-then-continue behaviour still needs bench confirmation.
- Bench sequence: upload the updated `P115.macro`, run `G65 P115 Q7` in each
  pen state, then run F-05A with the converter recover checkbox ticked.

## Files

- `firmware/grblhal/macros/P115.macro`: `W2` recover branches.
- `tools/validate_homing_macro.py`: updated P115 contract.
- `software/converter_core/gcode.py`: recover emission and full-retract `W1`.
- `software/converter_core/settings.py`: renamed setting and checkbox.
- `software/qt_svg_to_gcode.pyw`: recover checkbox wiring.
- `software/tests/test_theta_feed.py`: recover emission coverage.
- `software/README.md`, `firmware/README.md`, `firmware/grblhal/README.md`,
  `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`,
  `firmware/grblhal/macros/README.md`, `docs/integration/INTERFACES.md`,
  `docs/decisions/ADR-007-bounded-gp27-pen-ready-wait.md`: contract and
  operator documentation.

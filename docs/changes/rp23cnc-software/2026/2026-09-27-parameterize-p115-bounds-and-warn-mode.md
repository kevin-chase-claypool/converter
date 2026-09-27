---
id: RPSW-20260927-001
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
tags:
  - p115
  - gp27
  - handshake
  - error-39
  - f-05a
  - warn-only
related:
  - WSW-20260927-008
  - RPSW-20260925-007
  - RPSW-20260925-003
---

# Parameterize the P115 handshake bounds and add a warn-only mode

## Summary

`P115` keeps its fatal `error[39]` guard, but its bounds are now arguments
instead of constants, it can report each phase without erroring, and an opt-in
warn-only mode degrades to dwell timing instead of aborting the print. The
converter passes a longer completion bound on the program's first `M3`, the one
seek that legitimately exceeds the old fixed bound.

## Reason

The fatal guard aborted healthy programs for three reasons:

1. The program's first `M3` starts at the GP2 lift-home switch and is measured
   at about 7 s, while `P115` waited a fixed 5.00 s (`Settings.pen_down_first_ms`
   already encodes that seek at 10 s, and the firmware seek envelope allows far
   longer). The dwell path had a wide bound; the handshake path did not.
2. The release phase polls at 20 ms against a low window that the 2026-09-25
   `GP27_TRANSITION_LOW_MS` firmware floor guarantees at 50 ms. The floor is the
   real fix, and the poll interval is now tunable for the bench.
3. Any genuine miss is fatal, so a single stuck signal costs the whole sheet.
   The operator asked for a code path that keeps the handshake and tolerates a
   miss rather than removing the handshake.

## Implementation

- `P115.macro`: the `G65` argument registers are copied to numbered locals
  before anything else (`#32`-`#36`), because the tested controller runtime does
  not retain `#17` reliably after named-variable initialization. New optional
  arguments: `B<seconds>` completion bound (5.00 default), `C<seconds>` release
  bound (0.50), `D<seconds>` poll interval (0.02), `A<seconds>` fallback dwell,
  and `W1` warn-only. `Q7` measures both phases and prints
  `release observed|missing` and `completion observed|missing` without raising
  `error[39]`. With `W1`, a timeout prints `P115 WARNING ...`, executes `G4`
  for `A` seconds, and returns `[0]`; the strict paths still print their
  message and raise `error[39]`.
- `software/converter_core/gcode.py`: `handshake_command()` builds every call.
  The first `M3` emits a `B` bound derived from `pen_down_first_ms`
  (`max(5.0, first_dwell_s + 2.0)`), the end-of-print retract keeps its `Q0`,
  and warn-only mode appends the fixed-dwell equivalent as `A` plus `W1`.
  Older macros ignore the extra words, so a controller that has not been
  updated keeps its previous behaviour.
- `software/converter_core/settings.py`: new `toolhead_handshake_warn_only`
  setting (default off) and its Pen checkbox.
- `tools/validate_homing_macro.py`: the P115 checks now require the argument
  snapshots, the parameter overrides, the `Q7` mode, the warn-only warning and
  fallback dwell, and both return paths, while keeping the existing
  "observe GP27 only" forbidden-command scan.

## Verification

- `python tools\validate_homing_macro.py` passes for `P100.macro` and the new
  `P115.macro`.
- `python -m unittest discover -s software\tests -p "test_*.py"` passes, 51
  tests. New coverage: the first-down bound tracks `pen_down_first_ms`
  (`B7` for a 5 s first dwell, `B12` for the default 10 s), warn-only mode emits
  exactly `Q0 A0.8 W1` / `Q1 B12 A10 W1` / `Q1 A0.8 W1` / `Q0 A3 W1`, and the
  default program still emits no `G65 P115` at all.

**Not verified:** nothing in this change has run on the controller. The macro
dialect, argument delivery through `G65` (`A`/`B`/`D`/`W`), the `Q7` prints,
and the warn-only fallback all need the motorless macro checks and then the
F-05A bench session. The converter's emitted strings are the only half proven
here.

## Struggles and rejected approaches

- Removing the guard, or silently continuing with no message, was rejected:
  the operator wants the handshake kept, and a masked stuck signal must at least
  be visible on the console.
- Skipping the stale-state release phase was rejected earlier for the same
  reason (`RPSW-20260925-007`): without it a previous completion can satisfy the
  next command.
- Changing the macro's default poll interval to 5 ms was rejected for now. The
  firmware low floor is the real fix for a short edge, and `D` lets the bench
  tune the interval once `Q7` shows a miss, without shipping an unmeasured
  default.
- Making the converter emit a longer bound for every transition was rejected:
  later warm seeks measure about 1.2 s and clears about 0.46 s, so the default
  bound is already wide there and a longer bound would only delay a real fault.

## Risks and follow-up

- `W1` trades a mid-print abort for dwell timing plus a warning; it masks a
  genuinely stuck toolhead, so it stays off by default and must not be used as
  the commissioning path.
- The strict guard still needs the flashed `GP27_TRANSITION_LOW_MS` firmware
  and a passing `F-05A` before the converter checkbox can be re-defaulted on.
- The converter's time estimate still models pen time from the configured
  dwells, so it stays conservative while the handshake is enabled.
- Bench sequence: upload the updated `P115.macro`, run `G65 P115 Q7` in each
  pen state and record which phases report missing, then run F-05A with the
  converter checkbox ticked.

## Files

- `firmware/grblhal/macros/P115.macro`: arguments, `Q7`, warn-only paths.
- `tools/validate_homing_macro.py`: P115 contract checks.
- `software/converter_core/gcode.py`: bound derivation and optional arguments.
- `software/converter_core/settings.py`: warn-only setting and checkbox.
- `software/tests/test_theta_feed.py`: bound and warn-only coverage.
- `software/README.md`, `firmware/grblhal/macros/README.md`,
  `docs/integration/INTERFACES.md`: operator and interface documentation.

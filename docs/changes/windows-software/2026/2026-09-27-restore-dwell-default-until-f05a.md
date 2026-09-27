---
id: WSW-20260927-008
date: 2026-09-27
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
status: implemented
components:
  - software/converter_core/settings.py
  - software/tests/test_theta_feed.py
tags:
  - converter
  - gp27
  - p115
  - error-39
  - f-05a
  - pen-dwell
related:
  - WSW-20260925-001
  - RPSW-20260925-003
  - RPSW-20260925-007
---

# Restore the fixed-dwell default until F-05A passes

## Summary

The converter's **Wait for GP27 toolhead ready** option is off by default
again. Generated programs now use the fixed `G4` pen dwells unless the operator
deliberately enables the controller-side `G65 P115` acknowledgement.

## Reason

The option was flipped on by default on 2026-09-25 (`WSW-20260925-001`). That
put a fatal guard around every M3/M5 in every program: `P115` raises `error[39]`
when GP27/PRB does not show a fresh inactive-to-active completion edge inside
its 0.50 s release and 5.00 s completion bounds, and ioSender aborts the
streamed job when that happens. `F-05A`, the on-bench validation of that exact
handshake, is still open in `docs/testing/TEST_PLAN.md` and
`docs/project/ROADMAP.md`, and `docs/integration/INTERFACES.md` still requires
the fixed-dwell default until the force, clear, and GP27 tests pass.

The 2026-09-25 firmware fix (`RPSW-20260925-007`, guaranteed 50 ms GP27-inactive
window) removes one known trigger but is not bench-verified and requires the
toolhead to be reflashed with it.

Observed evidence: production jobs generated on 2026-09-27 carried 8,300-11,700
`G65 P115` lines (`samples/gcode/plane.gcode`,
`samples/gcode/plane_resume_21555.gcode`), and the abort/recover trail is
visible as `plane_resume.gcode`, `plane_resume_21555.gcode`, and finally the
hand-unticked `plane_resume_21555_dwell.gcode` that contains no P115 call.

## Implementation

- `software/converter_core/settings.py`: `toolhead_status_handshake` defaults to
  `False`, with a comment naming the fatal timeout and the F-05A gate. The
  `CHECKBOX_FIELDS` entry that seeds the Qt checkbox defaults to `False` as
  well, so a fresh app session matches the library default.
- The handshake code path is unchanged; `G65 P115 Q0`/`Q1` emission, the
  M3/M5-only validator, and the `include_z` exclusion all still apply when the
  option is enabled.

## Verification

- New regression test
  `test_default_program_avoids_the_uncommissioned_gp27_handshake` asserts
  `Settings().toolhead_status_handshake is False`, that a default program emits
  no `G65 P115` line, and that it still emits the `G4` dwells. It was run
  against the old default first and failed with `AssertionError: True is not
  false`, then passed after the change.
- `python -m unittest discover -s software\tests -p "test_*.py"` passes, 49
  tests.
- `python -m py_compile software\converter_core\settings.py` passes.

## Struggles and rejected approaches

- Keeping the option on and reducing the abort surface instead was rejected.
  The only in-program alternatives are to keep P115's stale-state protection
  (fatal by design) or to emit `Q0` everywhere, which would let a previous
  pen-state completion satisfy the next command - exactly the failure the
  `Q1` release phase exists to prevent.
- Emitting a host-side wait instead of the macro was rejected earlier for this
  machine; `P115` is the controller-resident design and the host cannot poll
  PRB while streaming.
- Coalescing redundant M3/M5 pairs was measured and dropped: a 8,344-command
  production file contains a single same-command pair, so there is nothing to
  coalesce.

## Risks and follow-up

- Until `F-05A` passes, pen timing depends on the configured `G4` dwells
  (`pen_down_first_ms` 10000, `pen_down_ms` 2500, `pen_up_ms` 800). If a future
  pen or clamp changes the seek/clear times, the dwells must be re-measured.
- Re-enabling the handshake for production still needs: `P115.macro` on the
  RP23CNC filesystem, verified GP27/U3-to-PRB polarity, the 2026-09-25
  `GP27_TRANSITION_LOW_MS` firmware flashed to the toolhead, and the `F-05A`
  bench record. Only then should the checkbox be re-defaulted on.
- A program that is resumed mid-file after an abort can start from an
  unproven pen state; the fixed-dwell default tolerates that, and the handshake
  path never did.

## Files

- `software/converter_core/settings.py`: dwell default and checkbox seed.
- `software/tests/test_theta_feed.py`: regression test for the default program.
- `software/README.md`: default, opt-in gate, and end-of-program wording.
- `docs/integration/INTERFACES.md`: dated record that the 2026-09-25 flip was
  reverted and why.

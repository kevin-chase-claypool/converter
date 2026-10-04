---
id: WSW-20261004-001
date: 2026-10-04
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
  - handshake
  - pen-dwell
  - defaults
related:
  - WSW-20260927-008
  - WSW-20260925-001
  - RPSW-20260927-002
  - RPSW-20260929-002
  - software/README.md
---

# Default the GP27 handshake and recover options on

## Summary

`toolhead_status_handshake` and `toolhead_handshake_recover` now default to
`true`, and both Qt checkboxes are checked when the converter opens. A default
program emits the bounded `G65 P115` acknowledgement around every M3/M5
transition, with the `W2` recover fallback on normal transitions and `W1` on
the end-of-print full retract, instead of the fixed `G4` pen dwells. Unchecking
**Wait for GP27 toolhead ready** still restores the fixed-dwell path.

## Reason

Request from the project owner, with the two Pen checkboxes shown ticked:
"i am always using these two. make them default checked." The operator runs
every job with the handshake and its recover mode armed, so the shipped default
now matches the as-operated configuration instead of making the same two clicks
part of every session.

This reverses the deliberate opt-in restored by `WSW-20260927-008`, which was
written while F-05A was still open. F-05A passed on 2026-09-29
(`RPSW-20260929-002`), and the owner has since decided the residual risk is
acceptable for this machine.

## Implementation

- `software/converter_core/settings.py`
  - `toolhead_status_handshake` default `false -> true`, with the comment
    recording the decision, the F-05A pass, the unexplained intermittent
    timeout, and the unchecked fallback.
  - `toolhead_handshake_recover` default `false -> true`; the failure mode is
    now a logged `P115 WARNING`, a pen lift to the fail-safe state, and a
    continued program rather than a mid-print abort.
  - `CHECKBOX_FIELDS` marks both checkboxes `True`, so the Qt sidebar opens with
    them checked, matching a headless `Settings()`.
- `software/tests/test_theta_feed.py`
  - The default-program test now asserts the exact four handshake lines and
    that both defaults are `True`.
  - A new test pins the unchecked fallback: no `G65 P115`, fixed `G4` dwells.
  - The strict-handshake tests pass `toolhead_handshake_recover=False`
    explicitly so they keep covering the fatal `Q0`/`Q1` path.

## Verification

- `python -m unittest software.tests.test_theta_feed`: 26 tests pass.
- Full suite: 190 tests pass
  (`python -m unittest discover -s software/tests -t software/tests`).
- A default `Settings()` program for a two-point contour emits, in order:
  `G65 P115 Q0 A0.8 W2`, `G65 P115 Q1 B12 A0.8 W2`,
  `G65 P115 Q1 A0.8 W2`, `G65 P115 Q0 A3 W1`, and no `G4 P0.3`/`G4 P0.6`
  dwells.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- None in the code change itself. The history is the interesting part: this is
  the second time the handshake default flips. The 2026-09-25 flip was reverted
  on 2026-09-27 because a single `error[39]` aborted a print mid-job while
  F-05A was open. This flip is safe to make now only because F-05A passed,
  `P115.macro` supports bounded warnings/recovery, and the recover option
  (default on) turns a timeout into a lift plus a warning instead of an abort.
- Considered defaulting only `toolhead_status_handshake` and leaving recover
  off. Rejected: the owner runs both, and the recover path is the whole reason
  the intermittent timeout is tolerable on a default configuration.

## Risks and follow-up

- A default program now depends on `P115.macro` being installed on the RP23CNC,
  the GP27/U3-to-`PRB` wiring being intact, and the flashed toolhead carrying
  `GP27_NORMAL_STATUS_ENABLED` plus `GP27_TRANSITION_LOW_MS`. If any is
  missing, a default program raises `error[39]`; unchecking **Wait for GP27
  toolhead ready** restores the fixed dwells.
- The roughly hourly `error[39]` seen in real printing is still unexplained.
  With recover on it degrades to a lifted pen and a console warning, but a
  missed `M3` draws that stroke in the air - watch the console and the sheet.
- No hardware test was run for this change; it only moves the defaults to the
  configuration the operator already uses on the bench.

## Files

- `software/converter_core/settings.py`: both defaults and the checkbox seeds.
- `software/tests/test_theta_feed.py`: default-program and fallback coverage.
- `software/README.md`: Pen documentation and this-machine notes.
- `docs/integration/INTERFACES.md`: default GP27/P115 contract wording.

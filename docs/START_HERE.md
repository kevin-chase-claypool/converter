# Start Here

This is the first file an AI or new contributor should read.

## Project goal

Build an XY + rotating-bed pen plotter:

```text
SVG -> host converter -> G-code -> RP23CNC/grblHAL -> X, Y, A motion
                                      |
                                      +-> engage/lift command -> force-controlled toolhead
```

The host converter is functional. Hardware integration and controller
configuration are the next phase.

Primary motion-controller reference:
[`phil-barrett/RP23CNC`](https://github.com/phil-barrett/RP23CNC).

## Read in this order

1. [`HANDOFF.md`](HANDOFF.md) - detailed implementation history and current behavior.
2. [`project/ENGINEERING_LOG.md`](project/ENGINEERING_LOG.md) - dated chronological record of work, evidence, and next actions.
3. [`architecture/SYSTEM_ARCHITECTURE.md`](architecture/SYSTEM_ARCHITECTURE.md) - subsystem ownership and dual-core strategy.
4. [`hardware/BOM.md`](hardware/BOM.md) - selected parts, known ratings, and unresolved electrical questions.
5. [`hardware/WIRING_TABLE.md`](hardware/WIRING_TABLE.md) - authoritative physical connection record.
6. [`integration/INTERFACES.md`](integration/INTERFACES.md) - contracts between host, motion controller, and toolhead.
7. [`project/ROADMAP.md`](project/ROADMAP.md) - phased work plan and acceptance criteria.
8. [`testing/TEST_PLAN.md`](testing/TEST_PLAN.md) - bring-up and integration test order.

## Current decisions

- Use grblHAL on RP23CNC for G-code parsing, planning, acceleration, and step generation.
- Do not write a second custom G-code parser unless a documented grblHAL limitation requires it.
- Use X, Y, and A for the three steppers.
- Treat converter `A` values as motor-shaft degrees unless the convention is deliberately changed at both ends.
- Use M3/M5 as the toolhead ENGAGE/LIFT contract.
- Start with fixed G4 settling delays. Add a feedback handshake only after basic motion and force control work independently.
- Keep motion timing isolated from toolhead sensor/control work.

## Session handoff procedure

At the end of every substantial AI session:

1. Add a timestamped entry to [`project/ENGINEERING_LOG.md`](project/ENGINEERING_LOG.md).
2. Update the status table in [`project/ROADMAP.md`](project/ROADMAP.md).
3. Record new measurements or tests in `docs/report/lab-notes/`.
4. Add decisions with lasting consequences under `docs/decisions/`.
5. Update `hardware/BOM.md` if a part or rating changes.
6. Update `hardware/WIRING_TABLE.md` for every physical wiring or pin-assignment change.
7. Update `integration/INTERFACES.md` if a signal, command, unit, or ownership boundary changes.
8. Summarize changed files, tests run, failures, and the next concrete task in `HANDOFF.md`.

Before starting an approach, search the single chronological engineering log.
Failed attempts must be interleaved with successes at the time they occurred
and include enough detail to prevent accidental repetition.

Do not put unverified assumptions into firmware constants. Mark them `TBD` and
link them to the test that will determine the value.

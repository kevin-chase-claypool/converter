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

## Read in this order

1. [`HANDOFF.md`](HANDOFF.md) - detailed implementation history and current behavior.
2. [`project/ENGINEERING_LOG.md`](project/ENGINEERING_LOG.md) - dated chronological record of work, evidence, and next actions.
3. [`project/STRUGGLES_AND_REJECTED_APPROACHES.md`](project/STRUGGLES_AND_REJECTED_APPROACHES.md) - topic-based failure and lessons register.
4. [`architecture/SYSTEM_ARCHITECTURE.md`](architecture/SYSTEM_ARCHITECTURE.md) - subsystem ownership and dual-core strategy.
5. [`hardware/BOM.md`](hardware/BOM.md) - selected parts, known ratings, and unresolved electrical questions.
6. [`hardware/WIRING_TABLE.md`](hardware/WIRING_TABLE.md) - authoritative physical connection record.
7. [`integration/INTERFACES.md`](integration/INTERFACES.md) - contracts between host, motion controller, and toolhead.
8. [`project/ROADMAP.md`](project/ROADMAP.md) - phased work plan and acceptance criteria.
9. [`testing/TEST_PLAN.md`](testing/TEST_PLAN.md) - bring-up and integration test order.

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
2. Update [`project/STRUGGLES_AND_REJECTED_APPROACHES.md`](project/STRUGGLES_AND_REJECTED_APPROACHES.md) when a failure or lesson is likely to recur.
3. Update the status table in [`project/ROADMAP.md`](project/ROADMAP.md).
4. Record new measurements or tests in `docs/report/lab-notes/`.
5. Add decisions with lasting consequences under `docs/decisions/`.
6. Update `hardware/BOM.md` if a part or rating changes.
7. Update `hardware/WIRING_TABLE.md` for every physical wiring or pin-assignment change.
8. Update `integration/INTERFACES.md` if a signal, command, unit, or ownership boundary changes.
9. Summarize changed files, tests run, failures, and the next concrete task in `HANDOFF.md`.

Before starting an approach, search
[`project/STRUGGLES_AND_REJECTED_APPROACHES.md`](project/STRUGGLES_AND_REJECTED_APPROACHES.md).
Failed attempts must be logged with enough detail to prevent accidental
repetition.

Do not put unverified assumptions into firmware constants. Mark them `TBD` and
link them to the test that will determine the value.

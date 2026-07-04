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

1. [`README.md`](README.md) - task-oriented documentation map and sources of truth.
2. [`../project_management_overview.html`](../project_management_overview.html)
   - at-a-glance project status dashboard.
3. [`project/ROADMAP.md`](project/ROADMAP.md) - current priorities and acceptance criteria.
4. Read only the subsystem documents relevant to the task.
5. Search [`changes/INDEX.md`](changes/INDEX.md) and
   [`project/ENGINEERING_LOG.md`](project/ENGINEERING_LOG.md) when history is
   needed.

[`HANDOFF.md`](HANDOFF.md) is a large technical and historical reference.
Search its relevant section instead of reading it front to back.

## Current decisions

- Use grblHAL on RP23CNC for G-code parsing, planning, acceleration, and step generation.
- Do not write a second custom G-code parser unless a documented grblHAL limitation requires it.
- Use X, Y, and A for the three steppers.
- Treat converter `A` values as motor-shaft degrees unless the convention is deliberately changed at both ends.
- Use M3/M5 as the toolhead ENGAGE/LIFT contract.
- Start with fixed G4 settling delays. Add a feedback handshake only after basic motion and force control work independently.
- Keep motion timing isolated from toolhead sensor/control work.

## Session handoff procedure

Documentation is part of implementation, not a later cleanup task. Follow
[`../AGENTS.md`](../AGENTS.md) for every change:

Use the documentation level defined in [`../AGENTS.md`](../AGENTS.md). Current
behavior must stay current, but minor edits do not need duplicate narratives in
both a change note and the engineering log.

The same working agreement requires continuous, evidence-based maintenance:
address local complexity when touching it, record larger technical debt in the
roadmap, and avoid speculative rewrites.

Before starting an approach, search the single chronological engineering log.
Failed attempts must be interleaved with successes at the time they occurred
and include enough detail to prevent accidental repetition.

Do not put unverified assumptions into firmware constants. Mark them `TBD` and
link them to the test that will determine the value.

# Repository Working Agreement

Before planning, editing, running project commands, committing, or pushing:

1. Read every Markdown file in the repository root, including this file.
2. Read `docs/START_HERE.md`.
3. Follow the linked project instructions relevant to the requested work.
4. Re-read the completion requirements in this file before finishing.

Do not treat a task as complete when these instruction files have not been
checked. If a referenced instruction file or required command is missing,
report that as a repository setup problem instead of silently skipping it.

## Documentation is part of every change

A task is not complete until its documentation is updated in the same working
session. Do not wait for the project owner to request documentation.

Use the lightest documentation level that preserves useful project knowledge:

1. Always update the subsystem's current-state document when behavior,
   configuration, wiring, or instructions changed.
2. Add or update a categorized change note for meaningful user-visible
   behavior, interfaces, design, configuration, hardware, or nontrivial fixes.
3. Add an engineering-log event for substantial sessions, milestones, failed
   approaches, measurements, and decisions. Do not duplicate every minor edit.
4. Use Git history for incidental formatting, typo fixes, and mechanical
   cleanup that does not change project behavior or understanding.
5. Update `docs/project/ROADMAP.md` only when task or phase status changed.
6. Record verification, failures, and unresolved risks at the appropriate
   level. Do not document only the successful result.

## Change categories

- `windows-software`: Windows host converter, Qt UI, conversion engine,
  launcher, desktop workflows, and converter samples.
- `rp23cnc-software`: RP23CNC/grblHAL builds, configuration, plugins, settings,
  machine-side embedded software, and pen-pressure controller firmware.
- `hardware`: Mechanical parts, electronics, power, wiring, pin assignments,
  enclosures, assembly, and physical measurements.

Cross-subsystem changes use one canonical note in the dominant category and
list all affected categories in its metadata. Category indexes are generated
from that metadata.

Use `docs/changes/_templates/CHANGE_NOTE.md`. Change-note filenames use:

```text
YYYY-MM-DD-short-kebab-case-title.md
```

Keep generated files, caches, logs, and incidental formatting churn out of
change notes unless they are relevant evidence.

## Required subsystem updates

- Windows converter behavior: update `software/README.md`.
- RP23CNC/grblHAL behavior: update `firmware/README.md` and the relevant
  `firmware/grblhal/` document.
- Wiring or pin assignment: update `docs/hardware/WIRING_TABLE.md`.
- Parts, ratings, or purchasing status: update `docs/hardware/BOM.md`.
- Interface, command, unit, or ownership change: update
  `docs/integration/INTERFACES.md`.
- Lasting architectural decision: add or supersede an ADR in `docs/decisions/`.
- Bench evidence: add a dated note under `docs/report/lab-notes/`.

Before finishing, run:

```powershell
python tools\docs_index.py --write
python tools\docs_index.py --check
```

These commands also rebuild and validate the engineering log's topic links and
stable entry anchors.

Report the documentation files changed alongside implementation files.

## Maintainability and continuous optimization

Treat long-term maintainability as part of every task:

1. Preserve existing architecture unless evidence supports changing it.
2. Avoid duplication, oversized modules, scattered configuration, and
   documentation that repeats the same source of truth.
3. When touched code has become difficult to understand or safely modify,
   include a focused cleanup if it can be verified within the task.
4. Do not perform broad speculative rewrites. Record larger improvements as
   concrete roadmap tasks with the problem, expected benefit, risk, and
   acceptance criteria.
5. Remove obsolete paths and documentation only after confirming they are no
   longer referenced or required.
6. Keep tests and verification proportional to the affected behavior.
7. Note newly discovered technical debt in the relevant change note and
   roadmap instead of allowing it to remain implicit.
8. Periodically review module size, duplicated logic, stale documents,
   generated artifacts, and unresolved TODOs when working in those areas.

Optimization means making the project easier to understand, verify, operate,
and extend. It does not mean changing working code merely to make it different.

## Documentation scaling triggers

Do not split documents merely because they are long. Split or archive when
navigation becomes measurably worse:

- If `docs/HANDOFF.md` exceeds roughly 700 lines or one topic exceeds roughly
  150 lines, move that topic into a focused current-state document and leave a
  short summary and link.
- If `docs/project/ENGINEERING_LOG.md` exceeds roughly 1,000 lines, archive
  completed calendar years under `docs/project/engineering-log/` and keep a
  chronological index.
- Keep change notes grouped by year. Do not create month folders unless a year
  contains enough notes that the year listing becomes difficult to scan.
- Prefer generated indexes over adding more hand-maintained navigation files.

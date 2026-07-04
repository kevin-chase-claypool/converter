# Change Documentation

This directory is the searchable record of what changed by subsystem. It
complements, rather than replaces, the single chronological
[`ENGINEERING_LOG.md`](../project/ENGINEERING_LOG.md).

## Find a change

| Area | Scope | Index |
|---|---|---|
| Windows software | Qt converter, conversion engine, launcher, desktop workflow | [`windows-software/README.md`](windows-software/README.md) |
| RP23CNC software | grblHAL, controller settings/plugins, machine-side firmware | [`rp23cnc-software/README.md`](rp23cnc-software/README.md) |
| Hardware | Mechanics, electronics, wiring, power, enclosure, physical tests | [`hardware/README.md`](hardware/README.md) |

The combined reverse-chronological index is [`INDEX.md`](INDEX.md).

## Record format

Each meaningful change gets one canonical Markdown note using
[`_templates/CHANGE_NOTE.md`](_templates/CHANGE_NOTE.md). Notes contain
searchable metadata, the reason for the change, implementation details,
verification, failures, risks, and links to affected files.

Use these stable category IDs:

- `WSW`: Windows software
- `RPSW`: RP23CNC and machine-side software
- `HW`: hardware, wiring, and mechanics

IDs use `<category>-YYYYMMDD-NNN`, for example `WSW-20260607-001`.

## Rules

1. Put the canonical note in the dominant subsystem directory.
2. List every affected category in the note metadata.
3. Run `python tools\docs_index.py --write`; indexes are generated from note
   metadata.
4. Keep one subject per note. Split unrelated work.
5. Update an existing note for follow-up evidence about the same change.
6. Create a new note when behavior, design intent, wiring, or configuration
   changes again.
7. Link detailed bench results to a lab note rather than copying raw data.

Lab notes are indexed in
[`../report/lab-notes/README.md`](../report/lab-notes/README.md).

Useful searches:

```powershell
rg -n "preview|grblHAL|wiring" docs\changes
rg -n "status: (planned|implemented|failed)" docs\changes
rg -n "tags:.*safety|tags:.*breaking-change" docs\changes
```

Validate metadata, generated indexes, duplicate IDs, and local links with:

```powershell
python tools\docs_index.py --check
```

---
id: WSW-20260922-001
date: 2026-09-22
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
  - hardware
status: implemented
components:
  - .gitignore
tags:
  - repository-hygiene
  - tooling
  - commit-workflow
related:
  - AGENTS.md
---

# Ignore local tooling and build-scratch directories

## Summary

`.gitignore` now covers the local tool and scratch trees that appear in every
working session: `node_modules/`, the pnpm store, the Ontoly graph cache and
output, Arduino compile trees under `work/`, KiCad `*-backups/` folders, and
Office lock files. None of them is project source, and none of them appears as
an untracked entry in `git status` after this change.

## Reason

`git status` listed `node_modules/`, `.pnpm-store/`, `.ontoly/`,
`ontoly-output/`, `work/`, two KiCad `-backups/` folders, and a `~$*.pptx`
Office lock file as untracked. `node_modules/` alone holds thousands of files,
and `work/` held roughly fifty `arduino-cli` build directories from the
2026-09-22 toolhead sessions. Under the scoped-commit rule in `AGENTS.md`, a
`git add .` or `git add -A` would have swept regenerable tool state into a
milestone commit.

## Implementation

Added ignore groups to `.gitignore`:

- `node_modules/`, `.pnpm-store/`, `.ontoly/`, `ontoly-output/` — the local
  Node/pnpm tool install and the Ontoly architecture-graph cache and output.
- `work/` — local `arduino-cli` compile trees. Verified by inspection that the
  contents are preprocessed copies of `firmware/pen_pressure/` sketches rather
  than original source.
- `~$*` — Microsoft Office lock files.
- `*-backups/` — KiCad automatic project backup archives.

The two stray root-level files `$pngBase` and `$pngPath`, written by a
root-level script bug on 2026-08-09, keep their existing ignore entries and now
carry a comment explaining their origin.

## Verification

- `git ls-files -i -c --exclude-standard` returns nothing, proving that no
  already-tracked file became ignored.
- `git status --short` no longer lists any of the directories named above, and
  still lists the pre-existing tracked modifications unchanged.
- `python tools\docs_index.py --write` and `python tools\docs_index.py --check`
  pass.

## Struggles and rejected approaches

A blanket `*.gcode` rule was rejected because `samples/gcode/` holds
intentional tracked output. Ignore rules were also deliberately not added for
files that may be real evidence — generated sample output sitting next to its
source SVG, raw CS1238 calibration captures, and presentation slide renders.
Those stay visible in `git status` so the owner can decide whether to track
them, rather than being silently hidden.

## Risks and follow-up

`work/` is now ignored wholesale. If a future workflow needs to commit
something under `work/`, add an explicit negation rule rather than removing the
directory rule. The stray `$pngBase` and `$pngPath` files are still on disk and
can be deleted once the project owner confirms they are not needed.

## Files

- `.gitignore`: added local tooling, build-scratch, backup, and lock-file rules.

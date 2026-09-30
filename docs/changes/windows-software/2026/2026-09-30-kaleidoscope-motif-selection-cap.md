---
id: WSW-20260930-017
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
status: implemented
tags:
  - kaleidoscope
  - motifs
  - interface
related:
  - WSW-20260930-016
  - software/README.md
---

# Kaleidoscope: use a random set of ten motifs, not the whole folder

## Summary

A motif folder is now a *pool*, not a worklist. `Motifs in use` (default **10**)
caps how many images a design may draw on: the app picks that many at random
from the folder, traces only those, and offers only those to the generator.
`New selection` draws a different random set. The limit and the exact selection
are remembered between launches, so the same ten come back.

## Reason

The operator asked to "keep the bat from attempting to render all of the pngs
simultaneously" and to "limit it to 10, randomized within the folders options".
With `motifs\nature` at 150 files and a folder of the operator's own images,
browsing seeds could trace and cache dozens of files, and a single design could
call on twenty or more.

## Implementation

- `qt_kaleidoscope.pyw`:
  - `load_motif_folder` now stores the folder's full list in `all_motif_paths`
    and calls `select_motifs()`, which keeps `motif_paths` at or below
    `Motifs in use`.
  - `select_motifs(wanted)`: when a saved selection is supplied it is reused
    (topped up randomly if files have been added or the limit raised);
    otherwise a `random.SystemRandom()` sample of the pool is taken. The
    selection is sorted for a stable label and the trace cache is cleared.
  - `refresh_motif_label` shows `using 10 of 150: a.png, b.png, ...` with the
    folder in the tooltip.
  - `roll_motif_selection` (the `New selection` button) re-draws the set,
    saves, rebuilds and logs `New motif selection: 10 of 150 images.`
  - `on_motif_limit_changed` re-selects when the spin box moves.
  - Settings gained `motif_limit` and `motif_selection`; `KaleidoscopeWindow`
    accepts an explicit `settings_file` so tests never touch the real one.
- `software/tests/test_preview_view.py`: the window is constructed with a
  temporary settings file everywhere, plus new tests for the cap, the limit
  control, re-rolling and selection persistence.

## Verification

- New tests: loading a 110-file folder uses exactly 10 files; `Motifs in use`
  of 3 uses 3 and 200 uses the whole folder; `New selection` changes the set;
  the selection and the limit survive a save/apply round trip; and every test
  window now uses an isolated settings file.
- Headless run against `samples\png` (40 files): startup 4.5 s, `using 10 of 40`,
  re-roll changes the set, limit 3 gives 3, and a reload restores the same set
  and limit.
- All eleven test modules pass; `python tools\docs_index.py --write` /
  `--check` pass.

## Struggles and rejected approaches

- Selecting per seed was rejected: browsing seeds would keep tracing new files
  and grow the cache, which is exactly what the operator wanted to stop.
- An unlimited default with a warning was rejected in favour of a hard default
  of 10, matching the request.
- The first test run failed because every `KaleidoscopeWindow` read the real
  settings file; the constructor now takes `settings_file`, and tests pass a
  temporary path.

## Risks and follow-up

- A small selection narrows the look: with 10 of 150 the same animals recur
  across seeds until `New selection` is pressed. That is the intended trade.
- The selection is stored per folder; switching folders re-draws it.

## Files

- `software/qt_kaleidoscope.pyw`: selection cap, re-roll button, settings keys,
  `settings_file` constructor argument.
- `software/tests/test_preview_view.py`: cap, limit, re-roll and persistence
  tests.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`: current state and
  session evidence.

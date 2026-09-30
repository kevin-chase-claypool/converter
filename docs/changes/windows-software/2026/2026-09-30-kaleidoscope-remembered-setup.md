---
id: WSW-20260930-016
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
status: implemented
tags:
  - kaleidoscope
  - interface
  - motifs
related:
  - WSW-20260930-015
  - software/README.md
---

# Kaleidoscope: remembered setup and a default motif folder

## Summary

The app now saves its setup to `software/kaleidoscope_settings.json` (git-ignored)
and restores it on launch: motif folder, source path, seed, intricacy,
divisions, mirror, rotation, source size, image offsets, threshold, trace
detail, every printable bound, tolerance, fill spacing, feed rates and the mode
checkboxes. With no settings file yet, the motif folder defaults to
`samples\png` when it exists (otherwise `motifs\nature`) and both **Use natural
motifs in patterns** and **Generate a random pattern** start ticked, so the app
opens on a pattern built from that folder.

Motif images that would trace into more than 200 contours or 4,000 points are
skipped with a log line: those are whole drawings, not shapes, and the affected
ring falls back to the drawn families instead of exploding into hundreds of
thousands of contours.

## Reason

The operator asked to make `C:\Users\jacks\Documents\Claude\converter\samples\png`
the motif folder, saying they were "tired of setting it up" on every launch.
The app had no persistence at all: no stored folder, mode or numbers.

## Implementation

- `qt_kaleidoscope.pyw`:
  - `settings_path()`, `apply_settings()`, `save_settings()` and `closeEvent`
    persist and restore the setup as JSON next to the script; `_settings_file`
    allows a different path (used by tests).
  - `default_motif_folder()` prefers `samples\png` in the repository, then
    `motifs\nature`.
  - `load_motif_folder(folder, announce)` centralises folder loading; the
    folder dialog now opens in the current folder, and choosing one saves the
    settings immediately so a crash cannot lose it.
  - Change handlers are guarded by `_loading` while settings are applied, and
    `__init__` performs exactly one build afterwards.
  - `_motif()` rejects artwork-sized traces (over 200 contours or 4,000 points)
    and says which file it skipped; motif tracing also runs at `max_side=512`
    instead of 700, which is plenty for a single shape and noticeably faster.
- `.gitignore` ignores `kaleidoscope_settings.json`; it is local state, not
  project source.

## Verification

- New `SettingsPersistenceTests` in `software/tests/test_preview_view.py`:
  the default folder resolves to `samples\png` when present; a save/load round
  trip restores seed, intricacy, divisions, source size, feed rate, fit radius,
  random mode and the motif folder; a chosen folder is remembered with its file
  list; a 24x24 grid drawing is rejected as a motif with a log line; and a
  single ellipse is accepted.
- Headless first run with no settings file: folder `...\samples\png`, motifs and
  random mode ticked, 40 files listed, 6 candidate motifs traced, all six - the
  old notebook renders in that folder - skipped as artwork, and the design built
  in 2.9 s with the drawn families as the fallback.
- All eleven test modules pass; `python tools\docs_index.py --write` /
  `--check` pass.

## Struggles and rejected approaches

- The first version stored nothing and relied on the dialog's last-used path,
  which Qt does not guarantee across processes.
- The first motif guard allowed 500 contours / 8,000 points; the folder's
  whole-design renders still got through and produced a 199,176-contour design.
  The limits are now 200 / 4,000, which a real single shape passes easily.
- Storing settings in the Windows registry (`QSettings`) was rejected in favour
  of a readable JSON file in the project, matching how the rest of the
  repository documents its state.

## Risks and follow-up

- Settings are per-user and per-checkout; two copies of the repository keep
  separate setups, which is intended but worth knowing.
- The default folder contains whatever the operator left there. Files that are
  not single shapes are skipped one by one, so a folder of artwork still costs a
  trace per used file before it is rejected.

## Files

- `software/qt_kaleidoscope.pyw`: settings persistence, default folder,
  folder-loading refactor, motif size guard.
- `software/tests/test_preview_view.py`: `SettingsPersistenceTests`.
- `.gitignore`: ignore the settings file.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`: current state and
  session evidence.

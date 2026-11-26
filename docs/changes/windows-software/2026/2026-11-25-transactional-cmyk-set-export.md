---
id: WSW-20261125-009
date: 2026-11-25
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/program_set_export.py
  - software/qt_svg_to_gcode.pyw
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_program_set_export.py
  - software/tests/test_cmyk_tab.py
  - software/tests/test_cmyk_photo_tab.py
  - software/tests/test_generator_tabs.py
  - software/README.md
  - docs/integration/INTERFACES.md
  - docs/decisions/ADR-010-transactional-multiprogram-export.md
  - docs/project/ROADMAP.md
tags:
  - cmyk
  - export
  - transaction
  - manifest
  - preflight
  - registration
  - reproducibility
related:
  - WSW-20261125-008
  - WSW-20261025-002
  - ADR-010
---

# Publish CMYK sets as one transactional export

## Summary

A CMYK save now stages all four numbered G-code programs and their version-5
set manifest before replacing any destination file. A write, flush, or commit
failure restores the previous complete set and reports that no new set was
published. Guided CMYK also requires all four inks, and program records are
checked for one common scale, placement, page frame, theta contract, feed
contract, and compensation identity.

The G-code text, machine coordinate contract, print order, manifest field
meanings, and firmware interface are unchanged.

## Reason

The prior exporter wrote `01-yellow`, `02-magenta`, `03-cyan`, and `04-black`
sequentially and wrote the manifest afterward. A disk or permission failure
could therefore leave a mixed old/new set or four programs without the manifest
that identifies their calibration and verification. The guided workflow also
kept prior **Write files** checkbox state, so a user who had unchecked an ink
in Advanced settings could reach the guided one-click path without four files.

## Implementation

- `program_set_export.py` validates unique filename-safe labels, writes every
  payload to a same-directory temporary file, flushes it to disk, and only then
  commits the set with atomic replacements.
- Existing destination files are moved to same-directory backups during the
  commit. Any failure removes newly installed targets and restores every backup
  before the error reaches the UI. Failed backups are retained rather than
  deleted if the operating system also rejects rollback.
- The main window resolves one destination base and passes it to the
  transactional writer. Companion manifests are part of the same transaction.
- The CMYK tab derives manifest hashes from the exact UTF-8 bytes supplied to
  the writer, so Windows newline conversion cannot invalidate recorded hashes.
- Guided defaults restore all four write checkboxes. Every analyzed ink records
  its final program settings and compensation identity; complete CMYK export is
  blocked if those records disagree.
- Set manifests move from version 4 to 5 and add a calibration-identity hash,
  a canonical set-identity hash, and explicit whole-set verification fields.

## Verification

- The focused CMYK suite, including transactional export, passed `168` tests
  in `29.397 s`.
- The expanded CMYK, exporter, and generator-shell subset passed `215` tests
  in `34.918 s` with one expected OpenGL-context skip.
- Complete converter discovery passed `724` tests in `137.386 s` with the one
  expected OpenGL-context skip.
- Regressions cover successful program-plus-manifest publication, staging
  failure with untouched old files, commit failure with complete rollback,
  duplicate/unsafe labels, guided four-ink restoration, and rejection of
  mismatched per-ink frame contracts.
- No physical printer, controller, or paper test was run; this change is
  host-side publication behavior and does not claim machine validation.

## Struggles and rejected approaches

Writing four files first and deleting them after a later failure was rejected
because it destroys a previously valid set. Deferring the manifest until after
all four replacements was rejected because the returned save could still be
incomplete. Comparing only filenames was rejected because four similarly named
files can still carry different scale, placement, kinematics, or compensation.

## Risks and follow-up

Atomic replacement is guaranteed per file, not as a single filesystem
primitive across four files. The implementation provides exception rollback
and never reports success before commit completes, but an operating-system
crash between individual replacements still requires recovery from the
retained backup files. A UI recovery action for orphaned `.backup` files is not
implemented.

The stage-owned adaptive-flow workspace described by the current development
objective remains a larger follow-up; this milestone closes the coordinated
export contract only.

## Files

- `software/program_set_export.py`: staged multi-file publication and rollback.
- `software/qt_svg_to_gcode.pyw`: destination resolution and transactional
  program-set API.
- `software/generator_tabs/cmyk_tab.py`: complete-set enforcement, common
  program identity, manifest hashing, and coordinated save.
- `software/tests/test_program_set_export.py`: transaction and rollback
  regressions.
- `software/tests/test_cmyk_tab.py`, `test_cmyk_photo_tab.py`,
  `test_generator_tabs.py`: set manifest, guided export, and host integration.
- `software/README.md`: current save behavior and manifest version.
- `docs/integration/INTERFACES.md`: host-side logical export contract.
- `docs/decisions/ADR-010-transactional-multiprogram-export.md`: lasting
  transaction decision.
- `docs/project/ROADMAP.md`: completed export task and remaining workspace
  milestone.

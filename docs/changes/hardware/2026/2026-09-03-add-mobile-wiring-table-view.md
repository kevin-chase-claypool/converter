---
id: HW-20260903-003
date: 2026-09-03
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - docs/hardware/WIRING_TABLE.md
  - docs/hardware/wiring-table-mobile.html
  - tools/generate_wiring_table_mobile.py
tags:
  - wiring
  - mobile
  - documentation
related:
  - HW-20260903-001
  - HW-20260903-002
---

# Add mobile wiring-table view

## Summary

Added a responsive card view of the master wiring table for tablet and phone
reading, with a client-side filter for connection IDs, pins, axes, and status.

## Reason

The authoritative Markdown table contains many columns and is difficult to
scan on a narrow screen. The mobile view preserves the Markdown file as the
only source of truth and derives its cards from every Markdown table.

## Implementation

`tools/generate_wiring_table_mobile.py` parses the tables in
`docs/hardware/WIRING_TABLE.md` and writes
`docs/hardware/wiring-table-mobile.html`. The generated page uses a
mobile-first card layout, expands to two columns on wider screens, and filters
cards without changing the underlying data.

## Verification

The generator completed successfully from the current wiring table. The
resulting HTML contains the table sections and responsive CSS; the Markdown
table links to the generated view and includes the regeneration command.

## Struggles and rejected approaches

Duplicating the wiring data in a hand-authored mobile Markdown document was
rejected because it could drift from the authoritative table.

## Risks and follow-up

Regenerate the HTML after any wiring-table edit. The generated file is a view,
not a second authority, and its browser rendering should be checked on the
target tablet when practical.

## Files

- `tools/generate_wiring_table_mobile.py`: derived-view generator.
- `docs/hardware/wiring-table-mobile.html`: responsive generated view.
- `docs/hardware/WIRING_TABLE.md`: mobile-view link and regeneration command.
